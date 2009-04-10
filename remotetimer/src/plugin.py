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

from Components.ActionMap import NumberActionMap
from Components.Button import Button

from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import getConfigListEntry, config, \
	ConfigSubsection, ConfigText, ConfigIP, ConfigYesNo, \
	ConfigPassword, ConfigNumber, KEY_LEFT, KEY_RIGHT, KEY_0

from Screens.TimerEntry import TimerEntry
from Screens.MessageBox import MessageBox
from Screens.MovieSelection import getPreferredTagEditor
from RecordTimer import AFTEREVENT
from enigma import eEPGCache

from Tools.BoundFunction import boundFunction

import time
from twisted.web.client import getPage 
from xml.dom.minidom import parseString
from base64 import encodestring

import urllib
#------------------------------------------------------------------------------------------

config.plugins.remoteTimer = ConfigSubsection()
config.plugins.remoteTimer.httphost = ConfigText(default = "" , fixed_size = False)
config.plugins.remoteTimer.httpip = ConfigIP(default = [0, 0, 0, 0])
config.plugins.remoteTimer.httpport = ConfigNumber(default = "0")
config.plugins.remoteTimer.username = ConfigText(default = "root", fixed_size = False)
config.plugins.remoteTimer.password = ConfigPassword(default = "", fixed_size = False)

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

		ConfigListScreen.__init__(self, [
			getConfigListEntry(_("Remote Timer - Hostname"), config.plugins.remoteTimer.httphost),
			getConfigListEntry(_("Remote Timer - Network IP"), config.plugins.remoteTimer.httpip),
			getConfigListEntry(_("Remote Timer - WebIf Port"), config.plugins.remoteTimer.httpport),
			getConfigListEntry(_("Remote Timer - Username"), config.plugins.remoteTimer.username),
			getConfigListEntry(_("Remote Timer - Password"), config.plugins.remoteTimer.password),
		], session)
		

	def keyLeft(self):
		self["config"].handleKey(KEY_LEFT)

	def keyRight(self):
		self["config"].handleKey(KEY_RIGHT)
		
	def keyNumber(self, number):
		self["config"].handleKey(KEY_0 + number)

	def keySave(self):
		#print "################################"
		#print config.plugins.remoteTimer.httphost.value
		#print "################################"
		config.plugins.remoteTimer.save()
		timerInit()
		self.close()
		
	def Exit(self):
		self.close()

baseTimerEntrySetup = None
baseTimerEntryGo = None

def timerInit():
	global baseTimerEntrySetup, baseTimerEntryGo
	if baseTimerEntrySetup is None:
		baseTimerEntrySetup = TimerEntry.createSetup
	if baseTimerEntryGo is None:
		baseTimerEntryGo = TimerEntry.keyGo
	TimerEntry.createSetup = createNewnigma2Setup
	TimerEntry.keyGo = newnigma2KeyGo

def createNewnigma2Setup(self, widget):
	baseTimerEntrySetup(self, widget)
	self.timerentry_remote = ConfigYesNo()
	self.list.insert(0, getConfigListEntry(_("Remote Timer"), self.timerentry_remote))

	# force re-reading the list
	self[widget].list = self.list

def newnigma2SubserviceSelected(self, service):
	if service is not None:
		# ouch, this hurts a little
		service_ref = timerentry_service_ref
		self.timerentry_service_ref = ServiceReference(service[1])
		eit = self.timer.eit
		self.timer.eit = None

		newnigma2KeyGo(self)

		self.timerentry_service_ref = service_ref
		self.timer.eit = eit

def newnigma2KeyGo(self):
	if not self.timerentry_remote.value:
		baseTimerEntryGo(self)
	else:
		service_ref = self.timerentry_service_ref
		if self.timer.eit is not None:
			event = eEPGCache.getInstance().lookupEventId(service_ref.ref, self.timer.eit)
			if event:
				n = event.getNumOfLinkageServices()
				if n > 1:
					tlist = []
					ref = self.session.nav.getCurrentlyPlayingServiceReference()
					parent = service_ref.ref
					selection = 0
					for x in range(n):
						i = event.getLinkageService(parent, x)
						if i.toString() == ref.toString():
							selection = x
						tlist.append((i.getName(), i))
					self.session.openWithCallback(boundFunction(newnigma2SubserviceSelected, self), ChoiceBox, title=_("Please select a subservice to record..."), list = tlist, selection = selection)
					return
				elif n > 0:
					parent = service_ref.ref
					service_ref = ServiceReference(event.getLinkageService(parent, 0))

		# XXX: this will - without any hassle - ignore the value of repeated
		begin, end = self.getBeginEnd()

		# when a timer end is set before the start, add 1 day
		if end < begin:
			end += 86400
	
		rt_name = urllib.quote(self.timerentry_name.value.decode('utf8').encode('utf8','ignore'))
		rt_description = urllib.quote(self.timerentry_description.value.decode('utf8').encode('utf8','ignore'))
		rt_disabled = 0 # XXX: do we really want to hardcode this? why do we offer this option then?
		rt_repeated = 0 # XXX: same here
	
		if self.timerentry_justplay.value == "zap":
			rt_justplay = 1
		else:
			rt_justplay = 0

		# XXX: this one is tricky since we do not know if the remote box offers afterEventAuto so lets just keep it simple for now
		rt_afterEvent = {
			"deepstandby": AFTEREVENT.DEEPSTANDBY,
			"standby": AFTEREVENT.STANDBY,
		}.get(self.timerentry_afterevent.value, AFTEREVENT.NONE)

		# Add Timer on RemoteBox via WebIf Command
		# http://192.168.178.20/web/timeradd?sRef=&begin=&end=&name=&description=&disabled=&justplay=&afterevent=&repeated=
		remoteip = "%d.%d.%d.%d" % tuple(config.plugins.remoteTimer.httpip.value)
		remoteurl = "http://%s:%s/web/timeradd?sRef=%s&begin=%s&end=%s&name=%s&description=%s&disabled=%s&justplay=%s&afterevent=%s&repeated=%s" % (
			remoteip,
			config.plugins.remoteTimer.httpport.value,
			service_ref,
			begin,
			end,
			rt_name,
			rt_description,
			rt_disabled,
			rt_justplay,
			rt_afterEvent,
			rt_repeated
		)
		print "######### debug remote", remoteurl

		username = config.plugins.remoteTimer.username.value
		password = config.plugins.remoteTimer.password.value
		if username and password:
			basicAuth = encodestring("%s:%s" % (username, password))
			authHeader = "Basic " + basicAuth.strip()
			headers = {"Authorization": authHeader}
		else:
			headers = {}

		defer = getPage(remoteurl, headers = headers)
		defer.addCallback(boundFunction(_gotPageLoad, self.session, self))
		defer.addErrback(boundFunction(errorLoad, self.session))

def _gotPageLoadCb(timerEntry, doClose, *args):
	if doClose:
		timerEntry.keyCancel()

def _gotPageLoad(session, timerEntry, html):
	remoteresponse = parseXml( html)
	#print "_gotPageLoad remoteresponse:", remoteresponse
	# XXX: should be improved...
	doClose = remoteresponse == "Timer added successfully!"
	session.openWithCallback(
		boundFunction(_gotPageLoadCb, timerEntry, doClose),
		MessageBox,
		_("Set Timer on Remote DreamBox via WebIf:\n%s") % (remoteresponse),
		MessageBox.TYPE_INFO
	)

def errorLoad(session, error):
	#print "errorLoad ERROR:", error
	session.open(
		MessageBox,
		_("ERROR - Set Timer on Remote DreamBox via WebIf:\n%s") % (error),
		MessageBox.TYPE_INFO
	)

def parseXml(string):
	try:
		dom = parseString(string)
		for entry in dom.firstChild.childNodes:
			if entry.nodeName == 'e2statetext':
				result = entry.firstChild.data.encode("utf-8")
		#print "parseXml debug result:", result
		return result
	except:
		return "ERROR XML PARSE"

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
 	return [
		PluginDescriptor(name="Remote Timer",description="Remote Timer Setup", where = [ PluginDescriptor.WHERE_PLUGINMENU ], fnc = main),
		PluginDescriptor(name="Remote Timer", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main),
		PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart)
	]

