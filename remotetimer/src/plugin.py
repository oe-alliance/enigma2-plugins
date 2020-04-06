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
#===============================================================================

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.TimerList import TimerList

from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import getConfigListEntry, config, \
	ConfigSubsection, ConfigText, ConfigIP, ConfigYesNo, \
	ConfigPassword, ConfigNumber, KEY_LEFT, KEY_RIGHT, KEY_0

from Screens.TimerEntry import TimerEntry
from Screens.MessageBox import MessageBox
from RecordTimer import AFTEREVENT

from enigma import eEPGCache
from boxbranding import getImageDistro

from Tools.BoundFunction import boundFunction

from twisted.web.client import getPage
from xml.etree.cElementTree import fromstring as cElementTree_fromstring
from base64 import encodestring

import urllib

#------------------------------------------------------------------------------------------

config.plugins.remoteTimer = ConfigSubsection()
config.plugins.remoteTimer.httphost = ConfigText(default = "" , fixed_size = False)
config.plugins.remoteTimer.httpip = ConfigIP(default = [0, 0, 0, 0])
config.plugins.remoteTimer.httpport = ConfigNumber(default = 80)
config.plugins.remoteTimer.username = ConfigText(default = "root", fixed_size = False)
config.plugins.remoteTimer.password = ConfigPassword(default = "", fixed_size = False)
config.plugins.remoteTimer.default = ConfigYesNo(default = False)
config.plugins.remoteTimer.remotedir = ConfigYesNo(default = False)

def localGetPage(url):
	username = config.plugins.remoteTimer.username.value
	password = config.plugins.remoteTimer.password.value
	if username and password:
		basicAuth = encodestring(username + ':' + password)
		authHeader = "Basic " + basicAuth.strip()
		headers = {"Authorization": authHeader}
	else:
		headers = {}

	return getPage(url, headers = headers)

class RemoteService:
	def __init__(self, sref, sname):
		self.sref = sref
		self.sname = sname

	getServiceName = lambda self: self.sname

class RemoteTimerScreen(Screen):
	skin = """
		<screen position="center,center" size="585,410" title="Remote-Timer digest" >
			<widget name="text" position="0,10" zPosition="1" size="585,20" font="Regular;20" halign="center" valign="center" />
			<widget name="timerlist" position="5,40" size="560,275" scrollbarMode="showOnDemand" />
			<ePixmap name="key_red" position="5,365" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="5,365" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<ePixmap name="key_green" position="150,365" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<widget name="key_green" position="150,365" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<ePixmap name="key_yellow" position="295,365" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<widget name="key_yellow" position="295,365" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<ePixmap name="key_blue" position="440,365" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_blue" position="440,365" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self.setTitle(_("Remote-Timer digest"))

		# XXX: any reason not to use the skin from the local screen?
		# is the info line really that much of a gain to lose a skinned screen...

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.settings,
			"blue": self.clean,
			"yellow": self.delete,
			"cancel": self.close,
		}, -1)

		self["timerlist"] = TimerList([])
		self["key_green"] = Button(_("Settings"))
		self["key_blue"] = Button(_("Cleanup"))
		self["key_yellow"] = Button(_("Delete"))
		self["key_red"] = Button(_("Cancel"))
		self["text"] = Label("")

		remoteip = "%d.%d.%d.%d" % tuple(config.plugins.remoteTimer.httpip.value)
		self.remoteurl = "%s:%s" % ( remoteip, str(config.plugins.remoteTimer.httpport.value))

		self.onLayoutFinish.append(self.getInfo)

	def getInfo(self, *args):
		try:
			info = _("fetching remote data...")
			url = "http://%s/web/timerlist" % (self.remoteurl)
			localGetPage(url).addCallback(self._gotPageLoad).addErrback(self.errorLoad)
		except:
			info = _("not configured yet. please do so in the settings.")
		self["text"].setText(info)

	def _gotPageLoad(self, data):
		# XXX: this call is not optimized away so it is easier to extend this functionality to support other kinds of receiver
		self["timerlist"].l.setList(self.generateTimerE2(data))
		info = _("finish fetching remote data...")
		self["text"].setText(info)

	def errorLoad(self, error):
		print "[RemoteTimer] errorLoad ERROR:", error.getErrorMessage()

	def clean(self):
		try:
			url = "http://%s/web/timercleanup?cleanup=true" % (self.remoteurl)
			localGetPage(url).addCallback(self.getInfo).addErrback(self.errorLoad)
		except:
			print "[RemoteTimer] ERROR Cleanup"

	def delete(self):
		sel = self["timerlist"].getCurrent()
		if not sel:
			return
		self.session.openWithCallback(
			self.deleteTimerConfirmed,
			MessageBox,
			_("Do you really want to delete the timer \n%s ?") % sel.name
		)

	def deleteTimerConfirmed(self, val):
		if val:
			sel = self["timerlist"].getCurrent()
			if not sel:
				return
			url = "http://%s/web/timerdelete?sRef=%s&begin=%s&end=%s" % (self.remoteurl, sel.service_ref.sref, sel.begin, sel.end)
			localGetPage(url).addCallback(self.getInfo).addErrback(self.errorLoad)

	def settings(self):
		self.session.open(RemoteTimerSetup)

	def generateTimerE2(self, data):
		try:
			root = cElementTree_fromstring(data)
		except Exception, e:
			print "[RemoteTimer] error: %s", e
			self["text"].setText(_("error parsing incoming data."))
		else:
			return [
				(
					E2Timer(
						sref = str(timer.findtext("e2servicereference", '').encode("utf-8", 'ignore')),
						sname = str(timer.findtext("e2servicename", 'n/a').encode("utf-8", 'ignore')),
						name = str(timer.findtext("e2name", '').encode("utf-8", 'ignore')),
						disabled = int(timer.findtext("e2disabled", 0)),
						failed = int(timer.findtext("e2failed", 0)),
						timebegin = int(timer.findtext("e2timebegin", 0)),
						timeend = int(timer.findtext("e2timeend", 0)),
						duration = int(timer.findtext("e2duration", 0)),
						startprepare = int(timer.findtext("e2startprepare", 0)),
						state = int(timer.findtext("e2state", 0)),
						repeated = int(timer.findtext("e2repeated", 0)),
						justplay = int(timer.findtext("e2justplay", 0)),
						eventId = int(timer.findtext("e2eit", -1)),
						afterevent = int(timer.findtext("e2afterevent", 0)),
						dirname = str(timer.findtext("e2dirname", '').encode("utf-8", 'ignore')),
						description = str(timer.findtext("e2description", '').encode("utf-8", 'ignore'))
					),
					False
				)
				for timer in root.findall("e2timer")
			]

class E2Timer:
	def __init__(self, sref = "", sname = "", name = "", disabled = 0, failed = 0, \
			timebegin = 0, timeend = 0, duration = 0, startprepare = 0, \
			state = 0, repeated = 0, justplay = 0, eventId = 0, afterevent = 0, \
			dirname = "", description = "", isAutoTimer = 0, ice_timer_id = None):
		self.service_ref = RemoteService(sref, sname)
		self.name = name
		self.disabled = disabled
		self.failed = failed
		self.begin = timebegin
		self.end = timeend
		self.duration = duration
		self.startprepare = startprepare
		self.state = state
		self.repeated = repeated
		self.justplay = justplay
		self.eventId = eventId
		self.afterevent = afterevent
		self.dirname = dirname
		self.description = description
		self.isAutoTimer = isAutoTimer
		self.ice_timer_id = ice_timer_id

class RemoteTimerSetup(Screen, ConfigListScreen):
	skin = """
		<screen position="center,center" size="560,410" title="Settings" >
			<widget name="config" position="5,40" size="480,335" scrollbarMode="showOnDemand" />
			<ePixmap name="key_red" position="120,280" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="key_green" position="320,280" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="120,280" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="320,280" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self.setTitle(_("Remote-Timer settings"))
		
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()

 		self["SetupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keySave,
			"cancel": self.Exit,
			"green": self.keySave,
		}, -1)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))

		ConfigListScreen.__init__(self, [
			getConfigListEntry(_("Remote Timer - Hostname"), config.plugins.remoteTimer.httphost),
			getConfigListEntry(_("Remote Timer - Network IP"), config.plugins.remoteTimer.httpip),
			getConfigListEntry(_("Remote Timer - WebIf Port"), config.plugins.remoteTimer.httpport),
			getConfigListEntry(_("Remote Timer - Username"), config.plugins.remoteTimer.username),
			getConfigListEntry(_("Remote Timer - Password"), config.plugins.remoteTimer.password),
			getConfigListEntry(_("Remote Timer - Default"), config.plugins.remoteTimer.default),
			getConfigListEntry(_("Remote Timer - Remotedir"), config.plugins.remoteTimer.remotedir),
		], session)

	def keySave(self):
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
	self.timerentry_remote = ConfigYesNo(default = config.plugins.remoteTimer.default.value)
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

		# unify the service ref
		service_ref = str(service_ref)
		clean_ref = ""
		colon_counter = 0

		for char in service_ref:
			if char == ':':
				colon_counter += 1
			if colon_counter < 10:
				clean_ref += char

		service_ref = clean_ref;

		# XXX: this will - without any hassle - ignore the value of repeated
		begin, end = self.getBeginEnd()

		# when a timer end is set before the start, add 1 day
		if end < begin:
			end += 86400

		rt_name = urllib.quote(self.timerentry_name.value.decode('utf8').encode('utf8','ignore'))
		rt_description = urllib.quote(self.timerentry_description.value.decode('utf8').encode('utf8','ignore'))
		rt_disabled = 0 # XXX: do we really want to hardcode this? why do we offer this option then?
		rt_repeated = 0 # XXX: same here

		if config.plugins.remoteTimer.remotedir.value:
			rt_dirname = urllib.quote(self.timerentry_dirname.value.decode('utf8').encode('utf8','ignore'))
		else:
			rt_dirname = "None"

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
		remoteurl = "http://%s:%s/web/timeradd?sRef=%s&begin=%s&end=%s&name=%s&description=%s&disabled=%s&justplay=%s&afterevent=%s&repeated=%s&dirname=%s" % (
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
			rt_repeated,
			rt_dirname
		)
		print "[RemoteTimer] debug remote", remoteurl

		defer = localGetPage(remoteurl)
		defer.addCallback(boundFunction(_gotPageLoad, self.session, self))
		defer.addErrback(boundFunction(errorLoad, self.session))

def _gotPageLoadCb(timerEntry, doClose, *args):
	if doClose:
		timerEntry.keyCancel()

def _gotPageLoad(session, timerEntry, html):
	remoteresponse = parseXml( html)
	#print "print _gotPageLoad remoteresponse:", remoteresponse
	# XXX: should be improved...
	doClose = remoteresponse == "Timer added successfully!"
	session.openWithCallback(
		boundFunction(_gotPageLoadCb, timerEntry, doClose),
		MessageBox,
		_("Set Timer on Remote Receiver via WebIf:\n%s") % (remoteresponse),
		MessageBox.TYPE_INFO
	)

def errorLoad(session, error):
	#print "[RemoteTimer] errorLoad ERROR:", error
	session.open(
		MessageBox,
		_("ERROR - Set Timer on Remote Receiver via WebIf:\n%s") % (error),
		MessageBox.TYPE_INFO
	)

def parseXml(string):
	try:
		dom = cElementTree_fromstring(string)
		entry = dom.findtext('e2statetext')
		if entry:
			return entry.encode("utf-8", 'ignore')
		return "No entry in XML from the webserver"
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
			print "[RemoteTimer] NO remoteTimer.httpip.value"


def timermenu(menuid, **kwargs):
	if menuid == "timermenu":
		return [("Remote Timers", main, "remotetimer", None)]
	else:
		return []

def main(session, **kwargs):
	session.open(RemoteTimerScreen)

def Plugins(**kwargs):
	plugin = []
	if getImageDistro() in ("openvix", "openatv", "openxta"):
		plugin.append(PluginDescriptor(name=_("Remote Timer"), description = _("Remote Timer Setup"), where=PluginDescriptor.WHERE_MENU, fnc=timermenu))
	else:
		plugin.append(PluginDescriptor(name="Remote Timer",description="Remote Timer Setup", where = [ PluginDescriptor.WHERE_PLUGINMENU ], icon="remotetimer.png", fnc = main))
	plugin.append(PluginDescriptor(name="Remote Timer", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main))
	plugin.append(PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart))
	return plugin
