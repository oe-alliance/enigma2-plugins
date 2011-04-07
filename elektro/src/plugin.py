#
# Power Save Plugin by gutemine
# Rewritten by Morty (morty@gmx.net)
# HDD Mod by joergm6
#
# Deep standby will be called sleep. Normal standby will be named standby!
# All calculations are in the local timezone, or in the relative Timezone.
# In the relative timezone the day starts at "nextday". If it is before nextday the last day will be used.
#
#


#from enigma import *
from __init__ import _

from Screens.InfoBarGenerics import *
# from RecordTimer import *


import calendar 
#################

# Plugin
from Plugins.Plugin import PluginDescriptor

# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Screens.MessageBox import MessageBox
from Screens.Console import Console
from Screens import Standby 

# GUI (Summary)
# from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Button import Button

from Components.Harddisk import harddiskmanager

# Configuration
from Components.config import getConfigListEntry, ConfigEnableDisable, \
	ConfigYesNo, ConfigText, ConfigClock, ConfigNumber, ConfigSelection, \
	config, ConfigSubsection, ConfigSubList, ConfigSubDict

# Startup/shutdown notification
from Tools import Notifications

import os
# Timer, etc

#import time
from time import localtime, asctime, time, gmtime
# import datetime
# import codecs


# Enigma system functions
from enigma import quitMainloop, eTimer


# import Wakeup?!
from Tools.DreamboxHardware import getFPWasTimerWakeup

#############

# Globals
session = None
ElektroWakeUpTime = -1
elektro_pluginversion = "3.4.1"
elektro_readme = "/usr/lib/enigma2/python/Plugins/Extensions/Elektro/readme.txt"
elektrostarttime = 60 
elektrosleeptime = 5
elektroShutdownThreshold = 60 * 20


#Configuration
config.plugins.elektro = ConfigSubsection()
config.plugins.elektro.nextday = ConfigClock(default = ((6 * 60 + 0) * 60) )

config.plugins.elektro.sleep = ConfigSubDict()
for i in range(7):
	config.plugins.elektro.sleep[i] = ConfigClock(default = ((1 * 60 + 0) * 60) )

config.plugins.elektro.wakeup = ConfigSubDict()
for i in range(7):
	config.plugins.elektro.wakeup[i] = ConfigClock(default = ((9 * 60 + 0) * 60) )

config.plugins.elektro.standbyOnBoot = ConfigEnableDisable(default = False)
config.plugins.elektro.standbyOnManualBoot =  ConfigEnableDisable(default = True)
config.plugins.elektro.standbyOnBootTimeout = ConfigNumber(default = 60)
config.plugins.elektro.enable = ConfigEnableDisable(default = False)
config.plugins.elektro.nextwakeup = ConfigNumber(default = 0)
config.plugins.elektro.force = ConfigEnableDisable(default = False)
config.plugins.elektro.dontwakeup = ConfigEnableDisable(default = False)
config.plugins.elektro.holiday =  ConfigEnableDisable(default = False)
config.plugins.elektro.hddsleep =  ConfigEnableDisable(default = False)



weekdays = [
	_("Monday"),
	_("Tuesday"),
	_("Wednesday"),
	_("Thursday"),
	_("Friday"),
	_("Saturday"),
	_("Sunday"),
]


#global ElektroWakeUpTime
ElektroWakeUpTime = -1

def autostart(reason, **kwargs):
	global session  
	if reason == 0 and kwargs.has_key("session"):
		session = kwargs["session"]
		session.open(DoElektro)

def getNextWakeup():
	global ElektroWakeUpTime
	
	#it might happen, that session does not exist. I don't know why. :-(
	if session is None:
		return ElektroWakeUpTime;
	
	nextTimer = session.nav.RecordTimer.getNextRecordingTime()
	print "[Elektro] Now: " + strftime("%a:%H:%M:%S",  gmtime(time()))
	if (nextTimer < 1) or (nextTimer > ElektroWakeUpTime):
		print "[Elektro] will wake up " + strftime("%a:%H:%M:%S",  gmtime(ElektroWakeUpTime))
		return ElektroWakeUpTime
	
	#We have to make sure, that the Box will wake up because of us
	# and not because of the timer
	print "[Elektro] will wake up due to the next timer" + strftime("%a:%H:%M:%S",  gmtime(nextTimer))
	return nextTimer - 1
	   
	
	
	
def Plugins(**kwargs):
	return [
		PluginDescriptor(
			name="Elektro", 
			description="Elektro Power Save Plugin Ver. " + elektro_pluginversion, 
			where = [
				PluginDescriptor.WHERE_SESSIONSTART, 
				PluginDescriptor.WHERE_AUTOSTART
			], 
			fnc = autostart, 
			wakeupfnc=getNextWakeup
		),
		PluginDescriptor(
			name="Elektro", 
			description="Elektro Power Save Plugin Ver. " + elektro_pluginversion, 
			where = PluginDescriptor.WHERE_PLUGINMENU, 
			icon="elektro.png", 
			fnc=main
		)
	]

	
def main(session,**kwargs):
	try:	
	 	session.open(Elektro)
	except:
		print "[Elektro] Pluginexecution failed"

class Elektro(ConfigListScreen,Screen):
	skin = """
			<screen position="center,center" size="600,400" title="Elektro Power Save Ver. """ + elektro_pluginversion + """" >
			<widget name="config" position="0,0" size="600,360" scrollbarMode="showOnDemand" />
			
			<widget name="key_red" position="0,360" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;18" transparent="1"/> 
			<widget name="key_green" position="140,360" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;18" transparent="1"/> 
			<widget name="key_yellow" position="280,360" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;18" transparent="1"/>
			
			<ePixmap name="red"    position="0,360"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green"  position="140,360" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,360" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" /> 
		</screen>"""
		
	def __init__(self, session, args = 0):
		self.session = session
		Screen.__init__(self, session)
	
		
		self.list = []
		
		
		self.list.append(getConfigListEntry(_("Enable Elektro Power Save"),config.plugins.elektro.enable))
		self.list.append(getConfigListEntry(_("Standby on boot"), config.plugins.elektro.standbyOnBoot ))
		self.list.append(getConfigListEntry(_("Standby on manual boot"), config.plugins.elektro.standbyOnManualBoot ))
		self.list.append(getConfigListEntry(_("Standby on boot screen timeout"), config.plugins.elektro.standbyOnBootTimeout))
		self.list.append(getConfigListEntry(_("Force sleep (even when not in standby)"), config.plugins.elektro.force ))
		self.list.append(getConfigListEntry(_("Don't sleep while hdd is active (e.g. ftp)"), config.plugins.elektro.hddsleep ))
		self.list.append(getConfigListEntry(_("Dont wake up"), config.plugins.elektro.dontwakeup ))
		self.list.append(getConfigListEntry(_("Holiday mode (experimental)"), config.plugins.elektro.holiday ))
		
		self.list.append(getConfigListEntry(_("Next day starts at"), config.plugins.elektro.nextday))

		for i in range(7):
			self.list.append(getConfigListEntry(weekdays[i] + ": "  + _("Wakeup"), config.plugins.elektro.wakeup[i]))
			self.list.append(getConfigListEntry(weekdays[i] + ": "  + _("Sleep"), config.plugins.elektro.sleep[i]))
			
		ConfigListScreen.__init__(self, self.list)
		
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Ok"))
		self["key_yellow"] = Button(_("Help"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"green": self.save,
			"yellow": self.help,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
		}, -2)
	
	def save(self):
		#print "saving"
		for x in self["config"].list:
			x[1].save()
		self.close(True,self.session)

	def cancel(self):
		#print "cancel"
		for x in self["config"].list:
			x[1].cancel()
		self.close(False,self.session)
		
	def help(self):
		self.session.open(Console,_("Showing Elektro readme.txt"),["cat %s" % elektro_readme])


class DoElektro(Screen):
	skin = """ <screen position="center,center" size="300,300" title="Elektro Plugin Menu" > </screen>"""
	
	def __init__(self,session):
		Screen.__init__(self,session)
		
		print "[Elektro] Starting up Version " + elektro_pluginversion
		
		self.session = session
		
		# Make sure wakeup time is set.
		self.setNextWakeuptime()
		
		# If we didn't wake up by a timer we don't want to go to sleep any more.
		# Unforturnately it is not possible to use getFPWasTimerWakeup()
		# Therfore we're checking wheter there is a recording starting within
		# the next five min		
		self.dontsleep = False
		
		#Let's assume we got woken up manually
		timerWakeup = False
		
		#Is a recording already runniong ->woken up by a timer
		if self.session.nav.RecordTimer.isRecording():
			timerWakeup = True
		# Is the next timer within 5 min -> woken up by a timer	
		if abs(self.session.nav.RecordTimer.getNextRecordingTime() - time()) <= 360:
			timerWakeup = True
			
		# Did we wake up by Elektro?
		# Let's hope this get's run early enaugh, and this get's run
		# before the requested wakeup-time (should be the case)
		#
		if abs(ElektroWakeUpTime - time()) <= 360:
			timerWakeup = True	
			
		# If the was a manual wakeup: Don't go to sleep	
		if timerWakeup == False:
			self.dontsleep = True
		
		
		#Check whether we should try to sleep:
		trysleep = config.plugins.elektro.standbyOnBoot.value
		
		#Don't go to sleep when this was a manual wakeup and the box shouldn't go to standby
		if timerWakeup == False and	config.plugins.elektro.standbyOnManualBoot.value == False:
			trysleep = False
			
	
		#if waken up by timer and configured ask whether to go to sleep.
		if trysleep:
			self.TimerStandby = eTimer()
			self.TimerStandby.callback.append(self.CheckStandby)
			self.TimerStandby.startLongTimer(elektrosleeptime)
			print "[Elektro] Set up standby timer"

		self.TimerSleep = eTimer()
		self.TimerSleep.callback.append(self.CheckElektro)
		self.TimerSleep.startLongTimer(elektrostarttime)
		print "[Elektro] Set up sleep timer"
		print "[Elektro] Translation test: " + _("Standby on boot")
		
	def clkToTime(self, clock):
		return ( (clock.value[0]) * 60 + (int)(clock.value[1]) )  * 60
		
	def getTime(self):
		ltime = localtime();
		return ( (int)(ltime.tm_hour) * 60 + (int)(ltime.tm_min) ) * 60
	
	def getPrintTime(self, secs):
		return strftime("%H:%M:%S", gmtime(secs))

	
	# This function converts the time into the relative Timezone where the day starts at "nextday"
	# This is done by substracting nextday from the current time. Negative times are corrected using the mod-operator
	def getReltime(self, time):
		nextday = self.clkToTime(config.plugins.elektro.nextday)
		return (time - nextday) %  (24 * 60 * 60)
		
	
	def CheckStandby(self):
		print "[Elektro] Showing Standby Sceen "
		try:
			self.session.openWithCallback(self.DoElektroStandby,MessageBox,_("Go to Standby now?"),type = MessageBox.TYPE_YESNO,
					timeout = config.plugins.elektro.standbyOnBootTimeout.value)		
		except:
			# Couldn't be shown. Restart timer.
			print "[Elektro] Failed Showing Standby Sceen "
			self.TimerStandby.startLongTimer(elektrostarttime)


	def DoElektroStandby(self,retval):
		if (retval):
			#Yes, go to sleep
			Notifications.AddNotification(Standby.Standby)
		

			
	def setNextWakeuptime(self):
		# Do not set a wakeup time if
		#  - Elektro isn't enabled
		#  - Elektro shouldn't wake up
		#  - Holiday mode is turned on
		if ((config.plugins.elektro.enable.value == False) 
		      or (config.plugins.elektro.dontwakeup.value == True)
		      or config.plugins.elektro.holiday.value == True): 
			global ElektroWakeUpTime
			ElektroWakeUpTime = -1
			return
			
		time_s = self.getTime()
		ltime = localtime()
		
		#print "Nextday:" + time.ctime(self.clkToTime(config.plugins.elektro.nextday))
		# If it isn't past next-day time we need yesterdays settings
		if time_s < self.clkToTime(config.plugins.elektro.nextday):
			day = (ltime.tm_wday - 1) % 7
		else:
			day = ltime.tm_wday
		
		#Check whether we wake up today or tomorrow
		# Relative Time is needed for this
		time_s = self.getReltime(time_s)
		wakeuptime = self.getReltime(self.clkToTime(config.plugins.elektro.wakeup[day]))
		
		# Lets see if we already woke up today
		if wakeuptime < time_s:
			#yes we did -> Next wakeup is tomorrow
			#print "Elektro: Wakeup tomorrow"
			day = (day + 1) % 7
			wakeuptime = self.getReltime(self.clkToTime(config.plugins.elektro.wakeup[day]))
		
		# Tomorrow we'll wake up erly-> Add a full day.
		if wakeuptime < time_s:
			wakeuptime = wakeuptime + 24 * 60 * 60
		
		# The next wakeup will be in wakupin seconds
		wakeupin = wakeuptime - time_s
		
		# Now add this to the current time to get the wakeuptime
		wakeuptime = (int)(time()) + wakeupin
		
		#Write everything to the global variable
		ElektroWakeUpTime = wakeuptime
			
			
	def CheckElektro(self):
		# first set the next wakeuptime - it would be much better to call that function on sleep. This will be a todo!
		self.setNextWakeuptime()
	
		#convert to seconds
		time_s = self.getTime()
		ltime = localtime()
		
		print "[Elektro] Testtime; " + self.getPrintTime(2 * 60 * 60)
		
		#Which day is it? The next day starts at nextday
		print "[Elektro] wday 1: " + str(ltime.tm_wday)
		if time_s < self.clkToTime(config.plugins.elektro.nextday):
			day = (ltime.tm_wday - 1) % 7
		else:
			day = ltime.tm_wday
			
		print "[Elektro] wday 2: " + str(day)
		
		#Let's get the day
		wakeuptime = self.clkToTime(config.plugins.elektro.wakeup[day])
		sleeptime = self.clkToTime(config.plugins.elektro.sleep[day])
		print "[Elektro] Current time: " + self.getPrintTime(time_s)
		print "[Elektro] Wakeup time: " + self.getPrintTime(wakeuptime)
		print "[Elektro] Sleep time: " + self.getPrintTime(sleeptime)
		
		#convert into relative Times
		time_s = self.getReltime(time_s)
		wakeuptime  = self.getReltime(wakeuptime)
		sleeptime = self.getReltime(sleeptime)
		
		print "[Elektro] Current Rel-time: " + self.getPrintTime(time_s)
		print "[Elektro] Wakeup Rel-time: " + self.getPrintTime(wakeuptime)
		print "[Elektro] Sleep Rel-time: " + self.getPrintTime(sleeptime)
		
		
		#let's see if we should be sleeping
		trysleep = False
		if time_s < (wakeuptime - elektroShutdownThreshold): # Wakeup is in the future -> sleep!
			trysleep = True
			print "[Elektro] Wakeup!" + str(time_s) + " < " + str(wakeuptime)
		if sleeptime < time_s : #Sleep is in the past -> sleep!
			trysleep = True
			print "[Elektro] Sleep: " + str(sleeptime) + " < " + str(time_s)
		
		#We are not tying to go to sleep anymore -> maybe go to sleep again the next time
		if trysleep == False:
			self.dontsleep = False
		
		#The User aborted to got to sleep -> Don't go to sleep.
		if self.dontsleep:
			trysleep = False
			
		# If we are in holydaymode we should try to got to sleep anyway
		# This should be set after self.dontsleep has been handled
		if config.plugins.elektro.holiday.value:
			trysleep = True
		
		# We are not enabled -> Dont go to sleep (This could have been catched earlier!)
		if config.plugins.elektro.enable.value == False:
			trysleep = False
		
		# Only go to sleep if we are in standby or sleep is forced by settings
		if  not ((Standby.inStandby) or (config.plugins.elektro.force.value == True) ):
			trysleep = False
		
		# No Sleep while recording
		if self.session.nav.RecordTimer.isRecording():
			trysleep = False
		
		# No Sleep on HDD running - joergm6
		if (config.plugins.elektro.hddsleep.value == True) and (harddiskmanager.HDDCount() > 0):
			hddlist = harddiskmanager.HDDList()
			if not hddlist[0][1].isSleeping():
				trysleep = False
		
		# Will there be a recording in a short while?
		nextRecTime = self.session.nav.RecordTimer.getNextRecordingTime()
		if  (nextRecTime > 0) and (nextRecTime - (int)(time()) <  elektroShutdownThreshold):
			trysleep = False
			
		# Looks like there really is a reason to go to sleep -> Lets try it!
		if trysleep:
			#self.();
			try:
				self.session.openWithCallback(self.DoElektroSleep, MessageBox, _("Go to sleep now?"),type = MessageBox.TYPE_YESNO,timeout = 60)	
			except:
				#reset the timer and try again
				self.TimerSleep.startLongTimer(elektrostarttime) 
				
		#set Timer, which calls this function again.
		self.TimerSleep.startLongTimer(elektrostarttime) 
		
		


	def DoElektroSleep(self,retval):
		if (retval):
			# os.system("wall 'Powermanagent does Deepsleep now'")
			#  Notifications.AddNotification(TryQuitMainloop,1)
			# 1 = Deep Standby -> enigma2:/doc/RETURNCODES
			
			global inTryQuitMainloop
			if Standby.inTryQuitMainloop == False:
				self.session.open(Standby.TryQuitMainloop, 1) # <- This might not work reliably
				#quitMainloop(1)
		else:
			# Dont try to sleep until next wakeup
			self.dontsleep = True
			#Start the timer again
			self.TimerSleep.startLongTimer(elektrostarttime) 
			
