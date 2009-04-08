# -*- coding: utf-8 -*-
#===============================================================================
# Remote Timer Setup by Homey
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#
# Copyright (C) 2009 by nixkoenner@newnigma2.to
# http://newnigma2.to
#
# License: GPL
#
# $Id$
#
#===============================================================================

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen

from Components.ActionMap import ActionMap, NumberActionMap
from Components.Label import Label
from Components.Button import Button

from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import getConfigListEntry, config, ConfigSubsection, ConfigSelection, ConfigText, ConfigIP, ConfigYesNo, ConfigNumber, KEY_LEFT, KEY_RIGHT, KEY_0

from Screens.TimerEntry import TimerEntry
from Screens.MessageBox import MessageBox
from Screens.MovieSelection import getPreferredTagEditor
from RecordTimer import AFTEREVENT
from Tools.Directories import resolveFilename, SCOPE_HDD
from enigma import eEPGCache
from time import localtime, mktime, time, strftime
from datetime import datetime

from twisted.web.client import getPage 
from xml.dom.minidom import *

import urllib
#------------------------------------------------------------------------------------------

my_global_session = None

config.plugins.remoteTimer = ConfigSubsection()
config.plugins.remoteTimer.httphost = ConfigText(default="" , fixed_size = False)
config.plugins.remoteTimer.httpip = ConfigIP(default=[0, 0, 0, 0])
config.plugins.remoteTimer.httpport = ConfigNumber(default="0")

class RemoteTimerSetup(Screen, ConfigListScreen):
	skin = """
		<screen position="80,160" size="560,330" title="Settings" >
			<widget name="config" position="5,40" size="480,335" scrollbarMode="showOnDemand" />
			<ePixmap name="red" position="120,280" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="320,280" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="120,280" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="320,280" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""
	
	def __init__(self, session):
		Screen.__init__(self, session)

		self["actions"] = NumberActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keySave,
			"green": self.keySave,
			"red": self.Exit,
			"cancel": self.Exit,
			"left": self.keyLeft,
			"right": self.keyRight,
			"0": self.keyNumber,
			"1": self.keyNumber,
			"2": self.keyNumber,
			"3": self.keyNumber,
			"4": self.keyNumber,
			"5": self.keyNumber,
			"6": self.keyNumber,
			"7": self.keyNumber,
			"8": self.keyNumber,
			"9": self.keyNumber
		}, -1)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))

		self.list = []
		self.list.append(getConfigListEntry(_("Remote Timer - Hostname"), config.plugins.remoteTimer.httphost))
		self.list.append(getConfigListEntry(_("Remote Timer - Netwerk-IP"), config.plugins.remoteTimer.httpip))
		self.list.append(getConfigListEntry(_("Remote Timer - WebIf Port"), config.plugins.remoteTimer.httpport))
		ConfigListScreen.__init__(self, self.list, session)

	def keyLeft(self):
		self["config"].handleKey(KEY_LEFT)

	def keyRight(self):
		self["config"].handleKey(KEY_RIGHT)
		
	def keyNumber(self, number):
		self["config"].handleKey(KEY_0 + number)

	def keySave(self):
		print "################################"
		print config.plugins.remoteTimer.httphost.value
		print "################################"
		config.plugins.remoteTimer.save()
		timerInit()
		self.close()
		
	def Exit(self):
		self.close()

def timerInit():
		TimerEntry.createSetup = createNewnigma2Setup
		TimerEntry.keyGo = newnigma2KeyGo

def createNewnigma2Setup(self, widget):
	self.timerentry_remote = ConfigYesNo()
	self.list = []
	self.list.append(getConfigListEntry(_("Remote Timer"), self.timerentry_remote))
	self.list.append(getConfigListEntry(_("Name"), self.timerentry_name))
	self.list.append(getConfigListEntry(_("Description"), self.timerentry_description))
	self.timerJustplayEntry = getConfigListEntry(_("Timer Type"), self.timerentry_justplay)
	self.list.append(self.timerJustplayEntry)
	self.timerTypeEntry = getConfigListEntry(_("Repeat Type"), self.timerentry_type)
	self.list.append(self.timerTypeEntry)

	if self.timerentry_type.value == "once":
		self.frequencyEntry = None
	else: # repeated
		self.frequencyEntry = getConfigListEntry(_("Repeats"), self.timerentry_repeated)
		self.list.append(self.frequencyEntry)
		self.repeatedbegindateEntry = getConfigListEntry(_("Starting on"), self.timerentry_repeatedbegindate)
		self.list.append(self.repeatedbegindateEntry)
		if self.timerentry_repeated.value == "daily":
			pass
		if self.timerentry_repeated.value == "weekdays":
			pass
		if self.timerentry_repeated.value == "weekly":
			self.list.append(getConfigListEntry(_("Weekday"), self.timerentry_weekday))

		if self.timerentry_repeated.value == "user":
			self.list.append(getConfigListEntry(_("Monday"), self.timerentry_day[0]))
			self.list.append(getConfigListEntry(_("Tuesday"), self.timerentry_day[1]))
			self.list.append(getConfigListEntry(_("Wednesday"), self.timerentry_day[2]))
			self.list.append(getConfigListEntry(_("Thursday"), self.timerentry_day[3]))
			self.list.append(getConfigListEntry(_("Friday"), self.timerentry_day[4]))
			self.list.append(getConfigListEntry(_("Saturday"), self.timerentry_day[5]))
			self.list.append(getConfigListEntry(_("Sunday"), self.timerentry_day[6]))
	self.entryDate = getConfigListEntry(_("Date"), self.timerentry_date)
	if self.timerentry_type.value == "once":
		self.list.append(self.entryDate)
		
	self.entryStartTime = getConfigListEntry(_("StartTime"), self.timerentry_starttime)
	self.list.append(self.entryStartTime)
	if self.timerentry_justplay.value != "zap":
		self.entryEndTime = getConfigListEntry(_("EndTime"), self.timerentry_endtime)
		self.list.append(self.entryEndTime)
	else:
		self.entryEndTime = None
	self.channelEntry = getConfigListEntry(_("Channel"), self.timerentry_service)
	self.list.append(self.channelEntry)

	self.dirname = getConfigListEntry(_("Location"), self.timerentry_dirname)
	self.tagsSet = getConfigListEntry(_("Tags"), self.timerentry_tagsset)
	if self.timerentry_justplay.value != "zap":
		if config.usage.setup_level.index >= 2: # expert+
			self.list.append(self.dirname)
		if getPreferredTagEditor():
			self.list.append(self.tagsSet)
		self.list.append(getConfigListEntry(_("After event"), self.timerentry_afterevent))

	self[widget].list = self.list
	self[widget].l.setList(self.list)

def newnigma2KeyGo(self):
		self.timer.name = self.timerentry_name.value
		self.timer.description = self.timerentry_description.value
		self.timer.justplay = self.timerentry_justplay.value == "zap"
		self.timer.resetRepeated()
		self.timer.afterEvent = {
			"nothing": AFTEREVENT.NONE,
			"deepstandby": AFTEREVENT.DEEPSTANDBY,
			"standby": AFTEREVENT.STANDBY,
			"auto": AFTEREVENT.AUTO
			}[self.timerentry_afterevent.value]
		self.timer.service_ref = self.timerentry_service_ref
		self.timer.tags = self.timerentry_tags

		self.timer.dirname = self.timerentry_dirname.value
		config.movielist.last_timer_videodir.value = self.timer.dirname
		config.movielist.last_timer_videodir.save()

		if self.timerentry_type.value == "once":
			self.timer.begin, self.timer.end = self.getBeginEnd()
		if self.timerentry_type.value == "repeated":
			if self.timerentry_repeated.value == "daily":
				for x in (0, 1, 2, 3, 4, 5, 6):
					self.timer.setRepeated(x)

			if self.timerentry_repeated.value == "weekly":
				self.timer.setRepeated(self.timerentry_weekday.index)

			if self.timerentry_repeated.value == "weekdays":
				for x in (0, 1, 2, 3, 4):
					self.timer.setRepeated(x)

			if self.timerentry_repeated.value == "user":
				for x in (0, 1, 2, 3, 4, 5, 6):
					if self.timerentry_day[x].value:
						self.timer.setRepeated(x)

			self.timer.repeatedbegindate = self.getTimestamp(self.timerentry_repeatedbegindate.value, self.timerentry_starttime.value)
			if self.timer.repeated:
				self.timer.begin = self.getTimestamp(self.timerentry_repeatedbegindate.value, self.timerentry_starttime.value)
				self.timer.end = self.getTimestamp(self.timerentry_repeatedbegindate.value, self.timerentry_endtime.value)
			else:
				self.timer.begin = self.getTimestamp(time.time(), self.timerentry_starttime.value)
				self.timer.end = self.getTimestamp(time.time(), self.timerentry_endtime.value)

			# when a timer end is set before the start, add 1 day
			if self.timer.end < self.timer.begin:
				self.timer.end += 86400

		if self.timer.eit is not None:
			event = eEPGCache.getInstance().lookupEventId(self.timer.service_ref.ref, self.timer.eit)
			if event:
				n = event.getNumOfLinkageServices()
				if n > 1:
					tlist = []
					ref = self.session.nav.getCurrentlyPlayingServiceReference()
					parent = self.timer.service_ref.ref
					selection = 0
					for x in range(n):
						i = event.getLinkageService(parent, x)
						if i.toString() == ref.toString():
							selection = x
						tlist.append((i.getName(), i))
					self.session.openWithCallback(self.subserviceSelected, ChoiceBox, title=_("Please select a subservice to record..."), list = tlist, selection = selection)
					return
				elif n > 0:
					parent = self.timer.service_ref.ref
					self.timer.service_ref = ServiceReference(event.getLinkageService(parent, 0))

		if self.timerentry_remote.value:
			self.rt_name = urllib.quote(self.timer.name.decode('utf8').encode('utf8','ignore'))
			self.rt_description = urllib.quote(self.timer.description.decode('utf8').encode('utf8','ignore'))
			self.rt_disabled = 0
			self.rt_repeated = 0
			self.rt_afterEvent = 0
		
			if self.timer.justplay:
				self.rt_justplay = 1
			else:
				self.rt_justplay = 0
	
			if self.timer.afterEvent == "standby":
				self.rt_afterEvent = 1
			if self.timer.afterEvent == "deepstandby":
				self.rt_afterEvent = 2

			# Add Timer on RemoteBox via WebIf Command
			# http://192.168.178.20/web/timeradd?sRef=&begin=&end=&name=&description=&disabled=&justplay=&afterevent=&repeated=
			self.remoteip = "%d.%d.%d.%d" % tuple(config.plugins.remoteTimer.httpip.value)
			self.remoteurl = "http://%s:%s/web/timeradd?sRef=%s&begin=%s&end=%s&name=%s&description=%s&disabled=%s&justplay=%s&afterevent=%s&repeated=%s" % (
				self.remoteip,
				config.plugins.remoteTimer.httpport.value,
				self.timer.service_ref,
				self.timer.begin,
				self.timer.end,
				self.rt_name,
				self.rt_description,
				self.rt_disabled,
				self.rt_justplay,
				self.rt_afterEvent,
				self.rt_repeated
			)
			print "######### debug remote " + self.remoteurl
			global my_global_session
			my_global_session = self.session
			getPage(self.remoteurl).addCallback(_gotPageLoad).addErrback(errorLoad)
		else:
			self.saveTimer()
			self.close((True, self.timer))

def _gotPageLoad(html):
	remoteresponse = parseXml( html)
	print "_gotPageLoad remoteresponse:" + remoteresponse
	my_global_session.open(MessageBox,("Set Timer on Remote DreamBox via WebIf:\n%s") % (remoteresponse),  MessageBox.TYPE_INFO)

def errorLoad(error):
	print "errorLoad ERROR:" + error
	my_global_session.open(MessageBox,("ERROR - Set Timer on Remote DreamBox via WebIf:\n%s") % (error),  MessageBox.TYPE_INFO)


def parseXml(string):
	try:
		dom = xml.dom.minidom.parseString(string)
		for entry in dom.firstChild.childNodes:
			if entry.nodeName == 'e2statetext':
				result = entry.firstChild.data.encode("utf-8")
		#print "parseXml debug result:" + result
		return result
	except:
		return "ERROR XML PARS"

#------------------------------------------------------------------------------------------

def autostart(reason, **kwargs):
	if "session" in kwargs:
		session = kwargs["session"]
		try:
			if config.plugins.remoteTimer.httpip.value:
				timerInit()
		except:
			print "####### NO remoteTimer.httpip.value"

def main(session, **kwargs):
		session.open(RemoteTimerSetup)

def Plugins(**kwargs):
 	return [PluginDescriptor(name="Remote Timer",description="Remote Timer Setup", where = [ PluginDescriptor.WHERE_PLUGINMENU ],fnc = main),
  PluginDescriptor(name="Remote Timer", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main), PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart)]


