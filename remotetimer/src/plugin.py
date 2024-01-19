# -*- coding: utf-8 -*-
# ===============================================================================
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
# Copyright (C) 2020 by Mr.Servo, jbleyel
#
# License: GPL
#
# $Id$
# ===============================================================================

# PYTHON IMPORTS
from __future__ import print_function
from base64 import b64encode
from requests import get
from six import PY2, PY3
from six.moves.urllib.parse import quote
from xml.etree.cElementTree import fromstring
import inspect
__getargs = inspect.getfullargspec if PY3 else inspect.getargspec

# ENIGMA IMPORTS
from enigma import eEPGCache
from boxbranding import getImageDistro
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import getConfigListEntry, config, ConfigSubsection, ConfigText, ConfigIP, ConfigYesNo, ConfigPassword, ConfigNumber
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.TimerList import TimerList
from Plugins.Plugin import PluginDescriptor
from RecordTimer import AFTEREVENT
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.TimerEntry import TimerEntry
from Screens.ChoiceBox import ChoiceBox
from ServiceReference import ServiceReference
from Tools.BoundFunction import boundFunction

config.plugins.remoteTimer = ConfigSubsection()
config.plugins.remoteTimer.httphost = ConfigText(default="", fixed_size=False)
config.plugins.remoteTimer.httpip = ConfigIP(default=[0, 0, 0, 0])
config.plugins.remoteTimer.httpport = ConfigNumber(default=80)
config.plugins.remoteTimer.username = ConfigText(default="root", fixed_size=False)
config.plugins.remoteTimer.password = ConfigPassword(default="", fixed_size=False)
config.plugins.remoteTimer.default = ConfigYesNo(default=False)
config.plugins.remoteTimer.remotedir = ConfigYesNo(default=False)


def getPage(url, callback, errback):
	if PY3:
		url = url.encode('utf-8')
	username = config.plugins.remoteTimer.username.value
	password = config.plugins.remoteTimer.password.value
	print("[remotetimer] username=%s password=%s" % (username, password))
	if username and password:
		base64string = "%s:%s" % (username, password)
		if PY3:
			base64string = base64string.encode('utf-8')
		base64string = b64encode(base64string)
		authheader = {b"Authorization": b"Basic %s" % base64string}
		print("[remotetimer] Headers=%s" % (authheader))
		try:
			r = get(url, headers=authheader, timeout=5)
			print("[remotetimer] statuscode=%s" % (r.status_code))
			if r.status_code == 200:
				data = r.content.decode('utf-8') if PY3 else r.content
				callback(data)
			else:
				errback("[remotetimer][getPage] incorrect response: %d" % r.status_code)
		except Exception as err:
			print("[remotetimer][getPage] %s: '%s'" % (type(err).__name__, err))
			import traceback
			traceback.print_exc()


class RemoteService:
	def __init__(self, sref, sname):
		self.sref = sref
		self.sname = sname

	def getServiceName(self):
		return self.sname


class RemoteTimerScreen(Screen):
	skin = """
		<screen position="center,center" size="585,410" title="Remote-Timer" >
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
		self.setTitle(_("Remote-Timer"))
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
		self.remoteurl = "%s:%s" % (remoteip, str(config.plugins.remoteTimer.httpport.value))
		self.onLayoutFinish.append(self.getInfo)

	def getInfo(self, *args):
		print("[remotetimer] remoteurl=%s" % self.remoteurl)
		if self.remoteurl != "0.0.0.0:80":
			url = "http://%s/web/timerlist" % (self.remoteurl)
			print("[remotetimer] url=%s" % (url))
			info = _("fetched remote data...")
			self["text"].setText(info)
			getPage(url, self._gotPageLoad, self.errorLoad)
		else:
			info = _("not configured yet. please do so in the settings.")
			self["text"].setText(info)

	def _gotPageLoad(self, data):
		print("[remotetimer] data=%s" % (data))
		# this call is not optimized so it is easier to extend this functionality to support other kinds of receiver
		self["timerlist"].l.setList(self.generateTimerE2(data))
		# info = _("finish fetching remote data...")
		self["text"].setText("")

	def errorLoad(self, error):
		print("[RemoteTimer][errorLoad] ERROR:", error)

	def clean(self):
		try:
			url = "http://%s/web/timercleanup?cleanup=true" % (self.remoteurl)
			getPage(url, self.getInfo, self.errorLoad)
		except Exception:
			print("[RemoteTimer][clean] ERROR Cleanup")

	def delete(self):
		sel = self["timerlist"].getCurrent()
		if sel:
			self.session.openWithCallback(self.deleteTimerConfirmed, MessageBox, _("Do you really want to delete the timer \n%s ?") % sel.name)

	def deleteTimerConfirmed(self, val):
		if val:
			sel = self["timerlist"].getCurrent()
			if not sel:
				return
			url = "http://%s/web/timerdelete?sRef=%s&begin=%s&end=%s" % (self.remoteurl, sel.service_ref.sref, sel.begin, sel.end)
			getPage(url, self.getInfo, self.errorLoad)

	def settings(self):
		self.session.open(RemoteTimerSetup)

	def generateTimerE2(self, data):
		try:
			root = fromstring(data)
		except Exception as e:
			print("[RemoteTimer][generateTimerE2] ERROR: %s", e)
			self["text"].setText(_("error parsing incoming data."))
		else:
			return [
				(
					E2Timer(
						sref=str(timer.findtext("e2servicereference", '').encode("utf-8", 'ignore')) if PY2 else str(timer.findtext("e2servicereference", '')),
						sname=str(timer.findtext("e2servicename", 'n/a').encode("utf-8", 'ignore')) if PY2 else str(timer.findtext("e2servicename", 'n/a')),
						name=str(timer.findtext("e2name", '').encode("utf-8", 'ignore')) if PY2 else str(timer.findtext("e2name", '')),
						disabled=int(timer.findtext("e2disabled", 0)),
						failed=int(timer.findtext("e2failed", 0)),
						timebegin=int(timer.findtext("e2timebegin", 0)),
						timeend=int(timer.findtext("e2timeend", 0)),
						duration=int(timer.findtext("e2duration", 0)),
						startprepare=int(timer.findtext("e2startprepare", 0)),
						state=int(timer.findtext("e2state", 0)),
						repeated=int(timer.findtext("e2repeated", 0)),
						justplay=int(timer.findtext("e2justplay", 0)),
						eventId=int(timer.findtext("e2eit", -1)) if timer.findtext("e2eit", -1) != '' else int(-1),
						afterevent=int(timer.findtext("e2afterevent", 0)),
						dirname=str(timer.findtext("e2dirname", '').encode("utf-8", 'ignore')) if PY2 else str(timer.findtext("e2dirname", '')),
						description=str(timer.findtext("e2description", '').encode("utf-8", 'ignore')) if PY2 else str(timer.findtext("e2description", ''))
					),
					False
				)
				for timer in root.findall("e2timer")
			]


class E2Timer:
	def __init__(self, sref="", sname="", name="", disabled=0, failed=0, timebegin=0, timeend=0, duration=0, startprepare=0,
		  		state=0, repeated=0, justplay=0, eventId=0, afterevent=0, dirname="", description="", isAutoTimer=0, ice_timer_id=None):
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
		self.marginBefore = 0
		self.marginAfter = 0
		self.eventEnd = timeend
		self.eventBegin = timebegin
		self.hasEndTime = timeend != 0


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
	print("[RemoteTimer] timerInit")
	global baseTimerEntrySetup, baseTimerEntryGo
	if baseTimerEntrySetup is None:
		baseTimerEntrySetup = TimerEntry.createSetup
	if baseTimerEntryGo is None:
		baseTimerEntryGo = TimerEntry.keySave
	TimerEntry.createSetup = createNewnigma2Setup
	TimerEntry.keySave = newnigma2KeyGo


def createNewnigma2Setup(self, widget="config"):
	print("[RemoteTimer] createNewnigma2Setup widget: %s" % widget)
	args = __getargs(baseTimerEntrySetup).args
	print("[RemoteTimer] createNewnigma2Setup setup args:" % args)
	if not hasattr(self, "timerentry_remote"):  # sometimes this is set outside this plugin
		self.timerentry_remote = ConfigYesNo(default=config.plugins.remoteTimer.default.value)
	timerEntryRemote = getConfigListEntry(_("Remote Timer"), self.timerentry_remote)
	if baseTimerEntrySetup:
		# if/elif/else clauses are a workaround for different kwargs in TimerEntry.createSetup in different distros
		if "widget" in args:
			baseTimerEntrySetup(self, widget)
		elif "prependItems" in args:
			baseTimerEntrySetup(self, prependItems=[timerEntryRemote])
		else:
			baseTimerEntrySetup(self)
		if "prependItems" not in args:
			self.list.insert(0, timerEntryRemote)
			# force re-reading the list
			self[widget].list = self.list


def newnigma2SubserviceSelected(self, service):
	print("[RemoteTimer] newnigma2SubserviceSelected entered service: %s" % service)
	if service is not None:
		# ouch, this hurts a little
		service_ref = self.timerentry_service_ref
		self.timerentry_service_ref = ServiceReference(service[1])
		eit = self.timer.eit
		self.timer.eit = None
		newnigma2KeyGo(self)
		self.timerentry_service_ref = service_ref
		self.timer.eit = eit


def newnigma2KeyGo(self):
	print("[RemoteTimer] newnigma2KeyGo entered self.timerentry_remote.value: %s" % self.timerentry_remote.value)
	if not self.timerentry_remote.value and baseTimerEntryGo:
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
					self.session.openWithCallback(boundFunction(newnigma2SubserviceSelected, self), ChoiceBox, title=_("Please select a subservice to record..."), list=tlist, selection=selection)
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
		service_ref = clean_ref

		# start: workaround for variables that are only available in some distros
		if not hasattr(self, "getTimeStamp"):
			self.getTimeStamp = self.getTimestamp
		if not hasattr(self, "timerStartDate"):
			self.timerStartDate = self.timerentry_date
		if not hasattr(self, "timerEndTime"):
			self.timerStartTime = self.timerentry_starttime
		if not hasattr(self, "timerEndTime"):
			self.timerEndTime = self.timerentry_endtime
		if not hasattr(self, "timerMarginBefore"):
			self.timerMarginBefore = config.recording.margin_before
		if not hasattr(self, "timerMarginAfter"):
			self.timerMarginAfter = config.recording.margin_after
		# end: workaround for variables that are only available in some distros

		# XXX: this will - without any hassle - ignore the value of repeated
		begin = self.getTimeStamp(self.timerStartDate.value, self.timerStartTime.value) - self.timerMarginBefore.value * 60
		end = self.getTimeStamp(self.timerStartDate.value, self.timerEndTime.value) + self.timerMarginAfter.value * 60
		# when a timer end is set before the start, add 1 day
		if end < begin:
			end += 86400
		if PY2:
			rt_name = quote(self.timerentry_name.value.decode('utf8').encode('utf8', 'ignore'))
			rt_description = quote(self.timerentry_description.value.decode('utf8').encode('utf8', 'ignore'))
		else:
			rt_name = quote(self.timerentry_name.value.encode('utf8', 'ignore'))
			rt_description = self.timerentry_description.value if self.timerentry_description.default != self.timerentry_description.value else self.timer.description
			rt_description = quote(rt_description.encode('utf8', 'ignore'))
		rt_disabled = 0  # XXX: do we really want to hardcode this? why do we offer this option then?
		rt_repeated = 0  # XXX: same here
		if config.plugins.remoteTimer.remotedir.value:
			rt_dirname = quote(self.timerentry_dirname.value.decode('utf8').encode('utf8', 'ignore')) if PY2 else quote(self.timerLocation.value.encode('utf8', 'ignore'))
		else:
			rt_dirname = "None"
		rt_justplay = 1 if self.timerentry_justplay.value == "zap" else 0
		# XXX: this one is tricky since we do not know if the remote box offers afterEventAuto so lets just keep it simple for now
		rt_afterEvent = {"deepstandby": AFTEREVENT.DEEPSTANDBY, "standby": AFTEREVENT.STANDBY, }.get(self.timerentry_afterevent.value, AFTEREVENT.NONE)
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
		getPage(remoteurl, boundFunction(_gotPageLoad, self.session, self), boundFunction(errorLoad, self.session))


def _gotPageLoadCb(timerEntry, doClose, *args):
	print("[RemoteTimer] _gotPageLoadCb: %s" % doClose)
	if doClose:
		timerEntry.keyCancel()


def _gotPageLoad(session, timerEntry, html):
	remoteresponse = parseXml(html)
	print("[RemoteTimer] _gotPageLoad remoteresponse: %s" % remoteresponse)
	session.openWithCallback(boundFunction(_gotPageLoadCb, timerEntry, True), MessageBox, _("Set Timer on Remote Receiver via WebIf:\n%s") % (remoteresponse), MessageBox.TYPE_INFO)


def errorLoad(session, error):
	print("[RemoteTimer] errorLoad ERROR: %s" % error)
	session.open(MessageBox, _("ERROR - Set Timer on Remote Receiver via WebIf:\n%s") % (error), MessageBox.TYPE_INFO)


def parseXml(string):
	print("[RemoteTimer] parseXML:%s" % string)
	try:
		dom = fromstring(string)
		entry = dom.findtext('e2statetext')
		if entry:
			return entry.encode("utf-8", 'ignore') if PY2 else entry
		return "No entry in XML from the webserver"
	except Exception:
		return "ERROR XML PARSE"


def autostart(reason, **kwargs):
	if "session" in kwargs:
		try:
			if config.plugins.remoteTimer.httpip.value:
				timerInit()
		except Exception:
			print("[RemoteTimer][autostart] NO remoteTimer.httpIP.value")


def timermenu(menuid, **kwargs):
	return [("Remote Timers", main, "remotetimer", None)] if menuid == "timermenu" else []


def main(session, **kwargs):
	session.open(RemoteTimerScreen)


def Plugins(**kwargs):
	plugin = []
	if getImageDistro() in ("openvix", "openatv", "openxta"):
		plugin.append(PluginDescriptor(name=_("Remote Timer"), description=_("Remote Timer Setup"), where=PluginDescriptor.WHERE_MENU, fnc=timermenu))
	else:
		plugin.append(PluginDescriptor(name="Remote Timer", description="Remote Timer Setup", where=[PluginDescriptor.WHERE_PLUGINMENU], icon="remotetimer.png", fnc=main))
	plugin.append(PluginDescriptor(name="Remote Timer", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main))
	plugin.append(PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=autostart))
	return plugin
