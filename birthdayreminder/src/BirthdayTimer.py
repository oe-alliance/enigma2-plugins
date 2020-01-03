# -*- coding: utf-8 -*-
#
#  Birthday Reminder E2 Plugin
#
#  $Id: BirthdayTimer.py,v 1.0 2011-08-29 00:00:00 Shaderman Exp $
#
#  Coded by Shaderman (c) 2011
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#


# OWN IMPORTS
from BirthdayNetworking import BroadcastProtocol, TransferServerFactory, TransferClientFactory
from BirthdayReminder import BirthdayStore, getAge

# PYTHON IMPORTS
from datetime import datetime, date, timedelta, time as dt_time
from time import mktime, time, strftime, strptime
from timer import Timer, TimerEntry
from twisted.internet import reactor

# ENIGMA IMPORTS
from Components.config import config
from enigma import eDVBLocalTimeHandler
from Screens.MessageBox import MessageBox
from Tools import Notifications

# for localized messages
from . import _


class BirthdayTimerEntry(TimerEntry):
	def __init__(self, begin, end, preremind):
		TimerEntry.__init__(self, int(begin), int(end))
		self.preremind = preremind
		self.state = self.StatePrepared
		
	def getNextActivation(self):
		return self.begin
		
	def activate(self):
		if self.preremind:
			when = config.plugins.birthdayreminder.preremind.getText()
			print "[Birthday Reminder] %s will turn %s in %s!" % (self.bDay[0], getAge(self.bDay[1]) + 1, when)
			text = _("%s will turn %s in %s!") % (self.bDay[0], getAge(self.bDay[1]) + 1, when)
		else:
			print "[Birthday Reminder] It's %s's birthday today!" % self.bDay[0]
			
			if config.plugins.birthdayreminder.dateFormat.value == "mmddyyyy":
				format = "%m/%d/%Y"
			else:
				format = "%d.%m.%Y"
			birthday = self.bDay[1].strftime(format)
			
			text = _("Today is %s's birthday!\n\nShe/he was born on %s and is now %s year(s) old.") % (self.bDay[0], birthday, getAge(self.bDay[1]))
			
		Notifications.AddNotification(MessageBox, text, type = MessageBox.TYPE_INFO)
		
		# activate the timer for next year
		now = date.today()
		bDay = self.bDay[1]
		
		# set timer to feb 28th for birthdays on feb 29th
		try:
			bDayNextYear = date(now.year + 1, bDay.month, bDay.day)
		except ValueError: # raised on feb 29th
			bDayNextYear = date(now.year + 1, bDay.month, bDay.day - 1)
		
		self.begin = int(mktime(bDayNextYear.timetuple()))
		self.end = self.begin -1
		self.state = self.StatePrepared
		
		return True
						
	def shouldSkip(self):
		return False
		
	def timeChanged(self):
		self.state = self.StatePrepared
		
class BirthdayTimer(Timer, BirthdayStore):
	def __init__(self):
		BirthdayStore.__init__(self)
		Timer.__init__(self)
		
		# this is used to detect settings changes, because we only want to change preremind timers if a different value was saved by the user
		config.plugins.birthdayreminder.preremindChanged.addNotifier(self.cbPreremindChanged, initial_call = False)
		config.plugins.birthdayreminder.notificationTimeChanged.addNotifier(self.cbNotificationTimeChanged, initial_call = False)
		
		# let's wait for the system time being up to date before starting the timers. needed when the box was powered off
		if not eDVBLocalTimeHandler.getInstance().ready():
			eDVBLocalTimeHandler.getInstance().m_timeUpdated.get().append(self.startTimer)
		else:
			self.start()
			self.startNetworking()
		self.broadcastPort = None
		self.transferServerPort = None
		
	def startTimer(self):
		eDVBLocalTimeHandler.getInstance().m_timeUpdated.get().remove(self.startTimer)
		self.start()
		self.startNetworking()
		
	def start(self):
		if not self.getSize():
			print "[Birthday Reminder] Got no birthdays, no timers to add."
			return
			
		self.addAllTimers()
		
	def stop(self):
		self.stopNetworking()
		
		print "[Birthday Reminder] stopping timer..."
		
		self.timer.stop()
		self.timer_list = []
		self.timer.callback.remove(self.calcNextActivation)
		self.timer = None
		
		config.plugins.birthdayreminder.preremindChanged.notifiers.remove(self.cbPreremindChanged)
		config.plugins.birthdayreminder.notificationTimeChanged.notifiers.remove(self.cbNotificationTimeChanged)
		
	def startNetworking(self):
		print "[Birthday Reminder] starting network communication..."
		
		port = config.plugins.birthdayreminder.broadcastPort.value
		self.transferServerProtocol = TransferServerFactory(self)
		self.broadcastProtocol = BroadcastProtocol(self)
		try:
			self.transferServerPort = reactor.listenTCP(port, self.transferServerProtocol)
			self.broadcastPort = reactor.listenUDP(port, self.broadcastProtocol)
		except:
			print "[Birthday Reminder] can't listen on port", port
			
	def stopNetworking(self):
		print "[Birthday Reminder] stopping network communication..."
		self.broadcastPort and self.broadcastPort.stopListening()
		self.transferServerPort and self.transferServerPort.stopListening()
		
	def requestBirthdayList(self, addr):
		print "[Birthday Reminder] requesting birthday list from", addr[0]
		reactor.connectTCP(addr[0], 7374, TransferClientFactory(self, "requestingList"))
		
	def sendPingResponse(self, addr):
		print "[Birthday Reminder] sending ping response to", addr[0]
		reactor.connectTCP(addr[0], 7374, TransferClientFactory(self, "pong"))
		
	def updateTimer(self, oldBirthday, newBirthday):
		print "[Birthday Reminder] updating timer for", oldBirthday[0]
		
		self.removeTimersForEntry(oldBirthday)
		self.addTimer(newBirthday)
		
		# add a preremind timer also?
		if config.plugins.birthdayreminder.preremind.getValue() != "-1":
			self.addTimer(newBirthday, preremind = True)
			
	def addTimer(self, entry, preremind = False):
		if preremind:
			print "[Birthday Reminder] Adding preremind timer for", entry[0]
		else:
			print "[Birthday Reminder] Adding birthday timer for", entry[0]
		
		timeList = config.plugins.birthdayreminder.notificationTime.value
		notifyTime = dt_time(timeList[0], timeList[1])
		now = date.today()
		bDay = entry[1]
		
		if preremind:
			numDays = int(config.plugins.birthdayreminder.preremind.getValue())
			# set timer to feb 28th for birthdays on feb 29th
			try:
				dateThisYear = date(now.year, bDay.month, bDay.day) - timedelta(numDays)
			except ValueError: # raised on feb 29th
				dateThisYear = date(now.year, bDay.month, bDay.day -1) - timedelta(numDays)
		else:
			# set timer to feb 28th for birthdays on feb 29th
			try:
				dateThisYear = date(now.year, bDay.month, bDay.day)
			except ValueError: # raised on feb 29th
				dateThisYear = date(now.year, bDay.month, bDay.day -1)
			
		dateTimeThisYear = datetime.combine(dateThisYear, notifyTime)
		
		if dateThisYear >= now: # check if the birthday is in this year
			begin = int(mktime(dateTimeThisYear.timetuple()))
		else: # birthday is in the past, we need a timer for the next year
			# set timer to feb 28th for birthdays on feb 29th
			try:
				bDayNextYear = dateTimeThisYear.replace(year = dateThisYear.year +1)
			except ValueError: # raised on feb 29th
				bDayNextYear = dateTimeThisYear.replace(year = dateThisYear.year +1, day = dateThisYear.day -1)
				
			begin = int(mktime(bDayNextYear.timetuple()))
			
		end = begin -1
		timerEntry = BirthdayTimerEntry(begin, end, preremind)
		timerEntry.bDay = entry
		self.addTimerEntry(timerEntry)
		
	def removeTimersForEntry(self, entry):
		for timer in self.timer_list[:]:
			if timer.bDay == entry:
				if timer.preremind:
					print "[Birthday Reminder] Removing preremind timer for", entry[0]
				else:
					print "[Birthday Reminder] Removing birthday timer for", entry[0]
				self.timer_list.remove(timer)
				
		self.calcNextActivation()
		
	def removePreremindTimers(self):
		print "[Birthday Reminder] Removing all preremind timers..."
		for timer in self.timer_list[:]:
			if timer.preremind:
				self.timer_list.remove(timer)
				
		self.calcNextActivation()
			
	def addAllTimers(self):
		print "[Birthday Reminder] Adding timers for all birthdays..."
		bDayList = self.getBirthdayList()
		for entry in bDayList:
			self.addTimer(entry)
			
			# add a preremind timer also?
			if config.plugins.birthdayreminder.preremind.getValue() != "-1":
				self.addTimer(entry, preremind = True)
				
	def showReceivedMessage(self, numReceived, peer):
		text = _("Birthday Reminder received %s birthdays from %s.") % (numReceived, peer)
		Notifications.AddNotification(MessageBox, text, type = MessageBox.TYPE_INFO)
		
	def cbPreremindChanged(self, configElement = None):
		if config.plugins.birthdayreminder.preremind.value == "-1": # remove all preremind timers
			self.removePreremindTimers()
		else: # we need to add or change timers
			if config.plugins.birthdayreminder.preremindChanged.value: # there are no preremind timers, add new timers
				print "[Birthday Reminder] Adding new preremind timers..."
				for timer in self.timer_list[:]:
					self.addTimer(timer.bDay, preremind = True)
			else: # change existing preremind timers
				print "[Birthday Reminder] Changing date of preremind timers..."
				self.removePreremindTimers()
				
				for timer in self.timer_list[:]:
					self.addTimer(timer.bDay, preremind = True)
					
	def cbNotificationTimeChanged(self, configElement = None):
		print "[Birthday Reminder] Changing timer times..."
		
		timeList = config.plugins.birthdayreminder.notificationTime.value
		notifyTime = dt_time(timeList[0], timeList[1])
		
		for timer in self.timer_list:
			day = date.fromtimestamp(timer.begin)
			newDateTime = datetime.combine(day, notifyTime)
			timer.begin = int(mktime(newDateTime.timetuple()))
			timer.end = timer.begin -1
			
		self.calcNextActivation()
		
