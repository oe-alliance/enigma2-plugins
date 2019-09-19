#
#  Partnerbox E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2009
#  Support: www.dreambox-tools.info
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import PinInput
from Components.config import config
from Components.ScrollLabel import ScrollLabel
from Components.ActionMap import ActionMap, NumberActionMap
from Components.MenuList import MenuList
from Components.Label import Label
from Components.Button import Button
from Components.EpgList import Rect
from Components.SystemInfo import SystemInfo
from Components.MultiContent import MultiContentEntryText
from enigma import eServiceReference
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, RT_VALIGN_TOP
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_SKIN_IMAGE
from Tools.FuzzyDate import FuzzyTime
from timer import TimerEntry
from enigma import eTimer, getDesktop
from time import localtime
import time
import xml.etree.cElementTree
import urllib
import SocketServer
ENIGMA_WEBSERVICE_ID = 0x1012
from Screens.InfoBarGenerics import InfoBarAudioSelection
from Screens.InfoBar import InfoBar
from RemoteTimerEntry import RemoteTimerEntry, RemoteTimerInit
from PartnerboxEPGSelection import Partnerbox_EPGSelectionInit

from PartnerboxFunctions import PlaylistEntry, FillE1TimerList, E2Timer, FillE2TimerList, SetPartnerboxTimerlist, sendPartnerBoxWebCommand, isInTimerList

from PartnerboxEPGList import Partnerbox_EPGListInit
from PartnerboxSetup import PartnerboxSetup, PartnerboxEntriesListConfigScreen, PartnerboxEntryList, PartnerboxEntryConfigScreen, initPartnerboxEntryConfig, initConfig
import time

from Services import Services, E2EPGListAllData, E2ServiceList
from Screens.ChannelSelection import service_types_tv

from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import ConfigSubsection, ConfigSubList, ConfigIP, ConfigInteger, ConfigSelection, ConfigText, ConfigYesNo, getConfigListEntry, configfile

from Components.GUIComponent import GUIComponent
import skin

# for localized messages
from . import _

config.plugins.Partnerbox = ConfigSubsection()
config.plugins.Partnerbox.showremotetvinextensionsmenu= ConfigYesNo(default = True)
config.plugins.Partnerbox.showcurrentstreaminextensionsmenu= ConfigYesNo(default = True)
config.plugins.Partnerbox.showremotetimerinextensionsmenu= ConfigYesNo(default = True)
config.plugins.Partnerbox.enablepartnerboxintimerevent = ConfigYesNo(default = False)
config.plugins.Partnerbox.enablepartnerboxepglist = ConfigYesNo(default = False)
config.plugins.Partnerbox.showremaingepglist = ConfigYesNo(default = False)
config.plugins.Partnerbox.enablepartnerboxzapbuton = ConfigYesNo(default = True)
config.plugins.Partnerbox.allicontype = ConfigYesNo(default = False)
config.plugins.Partnerbox.enablepartnerboxchannelselector = ConfigYesNo(default = True)
config.plugins.Partnerbox.enabledefaultpartnerboxintimeredit = ConfigYesNo(default = False)
config.plugins.Partnerbox.enablepartnerboxeventinfomenu = ConfigYesNo(default = True)
config.plugins.Partnerbox.enablepartnerboxeventinfocontextmenu = ConfigYesNo(default = True)
config.plugins.Partnerbox.entriescount = ConfigInteger(0)
config.plugins.Partnerbox.Entries = ConfigSubList()
config.plugins.Partnerbox.enablevpsintimerevent = ConfigYesNo(default = False)
initConfig()

def showPartnerboxIconsinEPGList():
	# for epgsearch
	return config.plugins.Partnerbox.enablepartnerboxepglist.value

def showPartnerboxZapRepIconsinEPGList():
	# for epgsearch_mod
	return True

def partnerboxpluginStart(session, what):
	count = config.plugins.Partnerbox.entriescount.value
	if count == 1:
		partnerboxplugin(session, what, config.plugins.Partnerbox.Entries[0])
	else:
		session.openWithCallback(partnerboxplugin, PartnerboxEntriesListConfigScreen, what)

def partnerboxplugin(session, what, partnerboxentry = None):
	if partnerboxentry is None:
		return
	if what == 0: # Current RemoteTV
		session.open(CurrentRemoteTV, partnerboxentry)
	elif what == 1: # RemoteTV
		session.open(RemoteTimerBouquetList, [], partnerboxentry, 1)
	elif what == 2: # RemoteTimer
		session.open(RemoteTimer, partnerboxentry)

def autostart_RemoteTimerInit(reason, **kwargs):
	if "session" in kwargs:
		session = kwargs["session"]
		try: RemoteTimerInit()
		except: pass

def autostart_Partnerbox_EPGList(reason, **kwargs):
	if "session" in kwargs:
		session = kwargs["session"]
		try:
			Partnerbox_EPGListInit()
			Partnerbox_EPGSelectionInit()
		except: pass

def setup(session,**kwargs):
	session.open(PartnerboxSetup)

def currentremotetv(session,**kwargs):
	partnerboxpluginStart(session, 0)

def remotetvplayer(session,**kwargs):
	partnerboxpluginStart(session, 1)

def main(session,**kwargs):
	partnerboxpluginStart(session, 2)

def eventinfo(session, servicelist, eventName="", **kwargs):
		partnerboxpluginStart(session, 2)

def eventinfoContextMenu(session, eventName="", **kwargs):
	partnerboxpluginStart(session, 2)

def Plugins(**kwargs):
	list = [PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart_ChannelContextMenu)]
	if config.plugins.Partnerbox.enablepartnerboxintimerevent.value:
		list.append(PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart_RemoteTimerInit))
	if config.plugins.Partnerbox.enablepartnerboxepglist.value:
		list.append(PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart_Partnerbox_EPGList))
	if config.plugins.Partnerbox.enablepartnerboxeventinfomenu.value and not config.plugins.Partnerbox.enablepartnerboxeventinfocontextmenu.value:
		list.append(PluginDescriptor(name= _("Partnerbox: RemoteTimer"), description=_("Manage timer for other dreamboxes in network"),  where = PluginDescriptor.WHERE_EVENTINFO, fnc = eventinfo))
	if config.plugins.Partnerbox.enablepartnerboxeventinfocontextmenu.value and config.plugins.Partnerbox.enablepartnerboxeventinfomenu.value:
		list.append(PluginDescriptor(name= _("Partnerbox: RemoteTimer"), where = PluginDescriptor.WHERE_EVENTINFO, fnc = eventinfoContextMenu))
	list.append(PluginDescriptor(name= _("Partnerbox"), description=_("setup for partnerbox"), where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "Setup_Partnerbox.png", fnc=setup))
	if config.plugins.Partnerbox.showremotetimerinextensionsmenu.value:
		list.append(PluginDescriptor(name= _("Partnerbox: RemoteTimer"), description=_("Manage timer for other dreamboxes in network"), where = [PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main))
	if config.plugins.Partnerbox.showremotetvinextensionsmenu.value:
		list.append(PluginDescriptor(name= _("Partnerbox: RemoteTV Player"), description=_("Stream TV from your Partnerbox"), where = [PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=remotetvplayer))
	if config.plugins.Partnerbox.showcurrentstreaminextensionsmenu.value:
		list.append(PluginDescriptor(name= _("Stream current Service from Partnerbox"), description=_("Stream current service from partnerbox"), where = [PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=currentremotetv))
	return list

def FillLocationList(xmlstring):
	Locations = []
	try: root = xml.etree.cElementTree.fromstring(xmlstring)
	except: Locations
	for location in root.findall("e2location"):
		Locations.append(location.text.encode("utf-8", 'ignore'))
	for location in root.findall("e2simplexmlitem"):  # vorerst Kompatibilitaet zum alten Webinterface-Api aufrecht erhalten (e2simplexmlitem)
		Locations.append(location.text.encode("utf-8", 'ignore'))
	return Locations

class CurrentRemoteTV(Screen):
	skin = """
		<screen name="CurrentRemoteTV" position="center,center" size="300,240" title="Remote Player">
		<widget name="text" position="10,10" zPosition="1" size="290,225" font="Regular;20" halign="center" valign="center" />
	</screen>"""

	def __init__(self, session, partnerboxentry):
		self.session = session
		Screen.__init__(self, session)
		self.setTitle(_("Remote Player"))
		self.CurrentService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.PartnerboxEntry = partnerboxentry
		self.password = partnerboxentry.password.value
		self.username = "root"
		self.ip = "%d.%d.%d.%d" % tuple(partnerboxentry.ip.value)
		port = partnerboxentry.port.value
		self.http = "http://%s:%d" % (self.ip,port)
		self.enigma_type = int(partnerboxentry.enigma.value)
		self.useinternal = int(partnerboxentry.useinternal.value)
		if self.enigma_type == 1:
			self.url = self.http + "/video.m3u"
		else:
			self.url = self.http + "/web/getcurrent"

		tt = _("Starting Remote Player (IP = %s)") % (self.ip)
		self["text"] = Label(tt)
		self.onLayoutFinish.append(self.startRun)

	def startRun(self):
		sendPartnerBoxWebCommand(self.url, None,10, self.username, self.password).addCallback(self.Callback).addErrback(self.Error)

	def Callback(self, xmlstring):
		url = ""
		servicereference = ""
		if self.enigma_type == 0:
			root = xml.etree.cElementTree.fromstring(xmlstring)
			for service in root.findall("e2service"):
				servicereference = str(service.findtext("e2servicereference", '').decode("utf-8").encode("utf-8", 'ignore'))
			if len(servicereference) > 0:
				url = "http://" + self.ip + ":8001/" + servicereference
			else:
				self.close()
		else:
			url = xmlstring
		if len(url) > 0:
			self.session.nav.stopService()
			sref = eServiceReference(ENIGMA_WEBSERVICE_ID, 0, url)
			self.session.nav.playService(sref, adjust=False)
			self.session.openWithCallback(self.RemotePlayerFinished, RemotePlayer,"" ,"", 0, 0, self.PartnerboxEntry, servicereference)
		else:
			self.close()

	def RemotePlayerFinished(self):
		if self.CurrentService:
			self.session.nav.playService(self.CurrentService)
		else:
			self.session.nav.stopService()
		self.close()

	def Error(self, error = None):
		self.close()

HD = False
try:
	sz_w = getDesktop(0).size().width()
	if sz_w >= 1280:
		HD = True
except:
	pass
class RemoteTimer(Screen):
	global CurrentParnerBoxName
	if HD:
		skin = """
			<screen name="RemoteTimer" position="center,center" size="560,455" title="RemoteTimer Timerlist">
				<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on"/>
				<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on"/>
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on"/>
				<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on"/>
				<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#9f1313" transparent="1"/>
				<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#1f771f" transparent="1"/>
				<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#a08500" transparent="1"/>
				<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#18188b" transparent="1"/>
				<widget name="text" position="0,60" zPosition="1" size="560,350" font="Regular;20" halign="center" valign="center" />
				<widget name="textok" position="0,430" zPosition="1" size="560,25" font="Regular;20" halign="center" valign="center" />
				<widget name="timerlist" position="0,60" zPosition="2" size="560,350" scrollbarMode="showOnDemand" foregroundColorSelected="#ffd700" />
			</screen>"""
	else:
		skin = """
			<screen name="RemoteTimer" position="center,center" size="560,455" title="RemoteTimer Timerlist">
				<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on"/>
				<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on"/>
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on"/>
				<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on"/>
				<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#9f1313" transparent="1"/>
				<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#1f771f" transparent="1"/>
				<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#a08500" transparent="1"/>
				<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#18188b" transparent="1"/>
				<widget name="text" position="0,60" zPosition="1" size="560,350" font="Regular;20" halign="center" valign="center" />
				<widget name="textok" position="0,430" zPosition="1" size="560,25" font="Regular;20" halign="center" valign="center" />
				<widget name="timerlist" position="0,60" zPosition="2" size="560,350" scrollbarMode="showOnDemand" />
			</screen>"""
	timerlist = []
	def __init__(self, session, partnerboxentry, not_epg=False):
		self.session = session
		Screen.__init__(self, session)
		self.not_epg = not_epg
		self["key_red"] = Label()
		self["key_green"] = Label()
		self["key_yellow"] = Label()
		self["key_blue"] = Label()
		self["text"] = Label(_("Getting Partnerbox Information..."))
		self["textok"] = Label()
		self.onLayoutFinish.append(self.startRun)
		self.E2TimerList = []
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EPGSelectActions"],
		{
			"ok": self.getLocations,
			"green": self.toggleTimer,
			"back": self.close,
			"yellow": self.EPGList,
			"blue": self.cleanupTimer,
			"red": self.deleteTimer,
		}, -1)

		self.setTitle(_("RemoteTimer Timerlist"))
		self.PartnerboxEntry = partnerboxentry
		self.password = partnerboxentry.password.value
		self.username = "root"
		self.ip = "%d.%d.%d.%d" % tuple(partnerboxentry.ip.value)
		self.port = partnerboxentry.port.value
		self.http = "http://%s:%d" % (self.ip,self.port)
		self.enigma_type = int(partnerboxentry.enigma.value)
		self.useinternal = int(partnerboxentry.useinternal.value)
		self.oldstart = 0
		self.oldend = 0
		self.oldtype = 0
		self.Locations = []
		self["timerlist"] = E2TimerMenu(self.enigma_type)
		self.toggleButtonState()

	def toggleButtonState(self):
		if self["timerlist"].currentSelection is not None:
			self["key_red"].setText(_("Delete timer"))
			self["key_green"].setText(_("Toggle status (on/off)"))
			if self.not_epg:
				self["key_yellow"].setText("")
			else:
				self["key_yellow"].setText(_("EPG Selection"))
			self["key_blue"].setText(_("Clean up"))
			self["textok"].setText(_("Press OK to edit timer..."))
		else:
			self["key_red"].setText("")
			self["key_green"].setText("")
			self["key_blue"].setText("")
			if self.not_epg:
				self["key_yellow"].setText("")
			else:
				self["key_yellow"].setText(_("EPG Selection"))
			self["textok"].setText("")

	def getLocations(self):
		if self["timerlist"].currentSelection is not None:
			if self.enigma_type == 0:
				sCommand = self.http + "/web/getlocations"
				sendPartnerBoxWebCommand(sCommand, None,3, self.username, self.password).addCallback(self.getLocationsCallback).addErrback(self.deleteTimerError)
			else:
				self.addTimer()

	def getLocationsCallback(self, xmlstring):
		self.Locations = []
		self.Locations = FillLocationList(xmlstring)
		self.addTimer()

	def addTimer(self):
		try:
			sel = self["timerlist"].l.getCurrentSelection()[0]
		except: return
		if sel is None:
			return
		if sel.repeated == 0:
			self.oldstart = sel.timebegin
			self.oldend = sel.timeend
			self.oldtype = sel.type
			self.session.openWithCallback(self.RemoteTimerEntryFinished, RemoteTimerEntry,sel, self.Locations)
		else:
			text = _("Repeated Timer are not supported!")
			self.session.open(MessageBox,text,  MessageBox.TYPE_INFO)

	def RemoteTimerEntryFinished(self, answer):
		if answer[0]:
			entry = answer[1]
			self["timerlist"].instance.hide()
			if self.enigma_type == 0:
				refstr = ':'.join(str(entry.servicereference).split(':')[:11])
				ref_old = "&channelOld=" + urllib.quote(refstr.decode('utf-8').encode('utf-8','ignore')) + "&beginOld=" + ("%s"%(self.oldstart)) + "&endOld=" + ("%s"%(self.oldend))  + "&deleteOldOnSave=1"
				ref = urllib.quote(refstr.decode('utf-8').encode('utf-8','ignore')) + "&begin=" + ("%s"%(entry.timebegin)) + "&end=" + ("%s"%(entry.timeend))  + "&name=" + urllib.quote(entry.name) + "&description=" + urllib.quote(entry.description) + "&dirname=" + urllib.quote(entry.dirname) + "&eit=" + ("%s"%(entry.eventId)) + "&justplay=" + ("%s"%(entry.justplay)) + "&afterevent=" + ("%s"%(entry.afterevent))
				sCommand = self.http + "/web/timerchange?sRef=" + ref + ref_old
				sendPartnerBoxWebCommand(sCommand, None,10, self.username, self.password).addCallback(self.deleteTimerCallback).addErrback(self.downloadError)
			else:
				if entry.justplay & PlaylistEntry.SwitchTimerEntry:
					action = "zap"
				elif entry.justplay & PlaylistEntry.recNgrab:
					action = "ngrab"
				else:
					action = ""
				tstart = time.localtime(entry.timebegin)
				tend = time.localtime(entry.timeend)
				ref_time_start = "&sday=" + ("%s"%(tstart.tm_mday)) + "&smonth=" + ("%s"%(tstart.tm_mon)) + "&syear=" + ("%s"%(tstart.tm_year)) + "&shour=" + ("%s"%(tstart.tm_hour)) + "&smin=" + ("%s"%(tstart.tm_min))
				ref_time_end = "&eday=" + ("%s"%(tend.tm_mday)) + "&emonth=" + ("%s"%(tend.tm_mon)) + "&eyear=" + ("%s"%(tend.tm_year)) + "&ehour=" + ("%s"%(tend.tm_hour)) + "&emin=" + ("%s"%(tend.tm_min))
				ref_old = "&old_type=" + ("%s"%(self.oldtype)) + "&old_stime=" + ("%s"%(self.oldstart)) + "&force=yes"
				ref = urllib.quote(entry.servicereference.decode('utf-8').encode('utf-8','ignore')) + "&descr=" + urllib.quote(entry.description) + "&channel=" + urllib.quote(entry.servicename) + "&after_event=" + ("%s"%(entry.afterevent)) + "&action=" + ("%s"%(action))
				sCommand = self.http + "/changeTimerEvent?ref=" + ref + ref_old + ref_time_start + ref_time_end
				sendPartnerBoxWebCommand(sCommand, None,10, self.username, self.password).addCallback(self.deleteTimerCallback).addErrback(self.downloadError)

	def startRun(self):
		self["timerlist"].instance.hide()
		self.action()

	def cleanupTimer(self):
		if self["timerlist"].currentSelection is not None:
			self["timerlist"].instance.hide()
			self["text"].setText(_("Cleaning up finished timer entries..."))
			if self.enigma_type == 0:
				sCommand = self.http + "/web/timercleanup?cleanup=true"
			else:
				sCommand = self.http + "/cleanupTimerList"
			sendPartnerBoxWebCommand(sCommand, None,3, self.username, self.password).addCallback(self.cleanupTimerlistCallback).addErrback(self.cleanupTimerlistCallback)

	def cleanupTimerlistCallback(self, answer):
		self.action()

	def deleteTimer(self):
		try:
			sel = self["timerlist"].l.getCurrentSelection()[0]
			if sel is None:
				return
			title_text = ""
			if self.enigma_type == 0:
				title_text = sel.repeated and _("Attention, this is repeated timer!\n") or ""
				name = sel.name
			else:
				name = sel.description
			self.session.openWithCallback(self.deleteTimerConfirmed, MessageBox, title_text + _("Do you really want to delete the timer \n%s ?") % name)
		except: return

	def deleteTimerConfirmed(self, val):
		if val:
			sel = self["timerlist"].l.getCurrentSelection()[0]
			if sel is None:
				return
			if self.enigma_type == 0:
				refstr = ':'.join(str(sel.servicereference).split(':')[:11])
				sCommand = self.http + "/web/timerdelete?sRef=" + refstr + "&begin=" + ("%s"%(sel.timebegin)) + "&end=" +("%s"%(sel.timeend))
			else:
				sCommand = self.http + "/deleteTimerEvent?ref=" + sel.servicereference + "&start=" + ("%s"%(sel.timebegin)) + "&type=" +("%s"%(sel.type)) + "&force=yes"
			sendPartnerBoxWebCommand(sCommand, None, 4, self.username, self.password).addCallback(self.deleteTimerCallback).addErrback(self.deleteTimerError)

	def deleteTimerCallback(self, callback = None):
		self.action()

	def deleteTimerError(self, error = None):
		if error is not None:
			self["timerlist"].instance.hide()
			self["text"].setText(str(_(error.getErrorMessage())))

	def downloadCallback(self, callback = None):
		self.readXML(callback)
		self["timerlist"].instance.show()
		self.toggleButtonState()

	def downloadError(self, error = None):
		if error is not None:
			self["text"].setText(str(_(error.getErrorMessage())))

	def action(self):
		if self.enigma_type == 0:
			url = self.http + "/web/timerlist"
		else:
			url = self.http + "/xml/timers"
		sendPartnerBoxWebCommand(url, None,10, self.username, self.password).addCallback(self.downloadCallback).addErrback(self.downloadError)

	def readXML(self, xmlstring):
		self.E2TimerList = []
		if self.enigma_type == 0:
			self.E2TimerList = FillE2TimerList(xmlstring)
		else:
			self.E2TimerList = FillE1TimerList(xmlstring)
		self["timerlist"].setList([ (x,) for x in self.E2TimerList])

	def toggleTimer(self):
		try:
			sel = self["timerlist"].l.getCurrentSelection()[0]
			if sel is None:
				return
			if self.enigma_type == 0:
				refstr = ':'.join(str(sel.servicereference).split(':')[:11])
				sCommand = self.http + "/web/timertogglestatus?sRef=" + refstr + "&begin=" + ("%s"%(sel.timebegin)) + "&end=" +("%s"%(sel.timeend))
				sendPartnerBoxWebCommand(sCommand, None, 3, self.username, self.password).addCallback(self.deleteTimerCallback).addErrback(self.deleteTimerError)
		except: pass

	def EPGList(self):
		if self.not_epg:
			return
		self.session.openWithCallback(self.CallbackEPGList, RemoteTimerBouquetList, self.E2TimerList, self.PartnerboxEntry, 0)

	def CallbackEPGList(self):
		self.startRun()

class RemoteTimerBouquetList(Screen):
	skin = """
		<screen name="RemoteTimerBouquetList" position="center,center" size="300,240" title="Choose bouquet">
		<widget name="text" position="10,10" zPosition="1" size="290,225" font="Regular;20" halign="center" valign="center" />
		<widget name="bouquetlist" position="10,10" zPosition="2" size="290,225" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session, E2Timerlist, partnerboxentry, playeronly):
		self.session = session
		Screen.__init__(self, session)
		self.setTitle(_("Choose bouquet"))
		self["bouquetlist"] = E2BouquetList([])
		self["text"] = Label(_("Getting Partnerbox Bouquet Information..."))
		self.onLayoutFinish.append(self.startRun)
		self.E2TimerList = E2Timerlist
		self["actions"] = ActionMap(["WizardActions", "DirectionActions"],
		{
			"ok": self.action,
			"back": self.close,
		}, -1)
		self.PartnerboxEntry = partnerboxentry
		self.password = partnerboxentry.password.value
		self.username = "root"
		ip = "%d.%d.%d.%d" % tuple(partnerboxentry.ip.value)
		port = partnerboxentry.port.value
		self.http = "http://%s:%d" % (ip,port)
		self.enigma_type = int(partnerboxentry.enigma.value)
		self.useinternal = int(partnerboxentry.useinternal.value)
		self.playeronly = playeronly
		if self.enigma_type == 0:
			self.url = self.http + "/web/getservices"
		else:
			self.url = self.http + "/xml/services?mode=0&submode=4"
		self.E1XMLString = ""

	def action(self):
		try:
			sel = self["bouquetlist"].l.getCurrentSelection()[0]
			if sel is None:
				return
			self.session.openWithCallback(self.CallbackEPGList, RemoteTimerChannelList, self.E2TimerList, sel.servicereference, sel.servicename, self.PartnerboxEntry, self.E1XMLString, self.playeronly)
		except: return

	def CallbackEPGList(self):
		pass

	def startRun(self):
		if self.useinternal == 1 :
			BouquetList = []
			a = Services(self.session)
			ref = eServiceReference( service_types_tv + ' FROM BOUQUET "bouquets.tv" ORDER BY bouquet')
			BouquetList = a.buildList(ref, False)
			self["bouquetlist"].buildList(BouquetList)
		else:
			self["bouquetlist"].instance.hide()
			self.getBouquetList()

	def getBouquetList(self):
		sendPartnerBoxWebCommand(self.url, None,10, self.username, self.password).addCallback(self.downloadCallback).addErrback(self.downloadError)

	def downloadCallback(self, callback = None):
		if self.enigma_type == 0:
			self.readXML(callback)
		else:
			self.readXMLE1(callback)
		self["bouquetlist"].instance.show()

	def downloadError(self, error = None):
		if error is not None:
			self["text"].setText(str(_(error.getErrorMessage())))

	def readXMLE1(self,xmlstring):
		self.E1XMLString = xmlstring
		BouquetList = []
		root = xml.etree.cElementTree.fromstring(xmlstring)
		for bouquets in root.findall("bouquet"):
			BouquetList.append(E2ServiceList(
			servicereference = str(bouquets.findtext("reference", '').encode("utf-8", 'ignore')),
			servicename = str(bouquets.findtext("name", 'n/a').encode("utf-8", 'ignore'))))
		self["bouquetlist"].buildList(BouquetList)

	def readXML(self, xmlstring):
		BouquetList = []
		root = xml.etree.cElementTree.fromstring(xmlstring)
		for servives in root.findall("e2service"):
			BouquetList.append(E2ServiceList(
			servicereference = str(servives.findtext("e2servicereference", '').decode("utf-8").encode("utf-8", 'ignore')),
			servicename = str(servives.findtext("e2servicename", 'n/a').decode("utf-8").encode("utf-8", 'ignore'))))
		self["bouquetlist"].buildList(BouquetList)

class RemoteTimerChannelList(Screen):
	EMPTY = 0
	ADD_TIMER = 1
	REMOVE_TIMER = 2
	REMOTE_TIMER_MODE = 0
	REMOTE_TV_MODE = 1

	if HD:
		skin = """
			<screen name="RemoteTimerChannelList" position="center,center" size="560,430" title ="Bouquet List">
				<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
				<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
				<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
				<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
				<widget name="text" position="0,40" zPosition="1" size="560,375" font="Regular;20" halign="center" valign="center" />
				<widget name="channellist" position="0,40" zPosition="2" size="560,375" scrollbarMode="showOnDemand" foregroundColorSelected="#ffd700" />
			</screen>"""
	else:
		skin = """
			<screen name="RemoteTimerChannelList" position="center,center" size="560,430" title ="Bouquet List">
				<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
				<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
				<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
				<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
				<widget name="text" position="0,40" zPosition="1" size="560,375" font="Regular;20" halign="center" valign="center" />
				<widget name="channellist" position="0,40" zPosition="2" size="560,375" scrollbarMode="showOnDemand" />
			</screen>"""

	def __init__(self, session, E2Timerlist, ServiceReference, ServiceName, partnerboxentry, E1XMLString,  playeronly):
		self.session = session
		Screen.__init__(self, session)
		self.setTitle(_("Bouquet List"))
		self["channellist"] = E2ChannelList([], selChangedCB = self.onSelectionChanged)
		self.playeronly = playeronly
		self["key_red"] = Label(_("Zap"))
		self["key_green"] = Label()
		if self.playeronly == 0:
				self["key_yellow"] = Label(_("EPG Selection"))
		else:
			self["key_yellow"] = Label()
		self["key_blue"] = Label(_("Info"))

		self["text"] = Label(_("Getting Channel Information..."))
		self.onLayoutFinish.append(self.startRun)
		self.E2TimerList = E2Timerlist
		self.E2ChannelList = []
		self.servicereference = ServiceReference
		self.E1XMLString = E1XMLString
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions"],
		{
			"ok": self.PlayRemoteStream,
			"back": self.close,
			"yellow": self.EPGSelection,
			"blue": self.EPGEvent,
			"red": self.Zap,
		}, -1)

		self.PartnerboxEntry = partnerboxentry
		self.password = partnerboxentry.password.value
		self.username = "root"
		self.ip = "%d.%d.%d.%d" % tuple(partnerboxentry.ip.value)
		self.port = partnerboxentry.port.value
		self.http = "http://%s:%d" % (self.ip,self.port)
		self.enigma_type = int(partnerboxentry.enigma.value)
		self.useinternal = int(partnerboxentry.useinternal.value)
		self.zaptoservicewhenstreaming = partnerboxentry.zaptoservicewhenstreaming.value
		self.key_green_choice = self.ADD_TIMER
		self.zapTimer = eTimer()
		self.zapTimer.timeout.get().append(self.zapTimerTimeout)
		self.onClose.append(self.__onClose)
		self.ChannelListCurrentIndex = 0
		self.mode = self.REMOTE_TIMER_MODE
		self.CurrentService = self.session.nav.getCurrentlyPlayingServiceReference()

	def __onClose(self):
		if self.zapTimer.isActive():
			self.zapTimer.stop()

	def startRun(self):
		if self.useinternal == 1 :
			ChannelList = []
			a = Services(self.session)
			Channelref = eServiceReference(self.servicereference)
			ChannelList = a.buildList(Channelref, True)
			self["channellist"].buildList(ChannelList)
			self["channellist"].instance.show()
			if self.ChannelListCurrentIndex !=0:
				sel = self["channellist"].moveSelectionTo(self.ChannelListCurrentIndex)
				self.ChannelListCurrentIndex = 0
		else:
			self["channellist"].instance.hide()
			self.getChannelList()

	def PlayRemoteStream(self):
		if self.playeronly == 1:
			if self.mode == self.REMOTE_TIMER_MODE:
				self.mode = self.REMOTE_TV_MODE
				if self.zaptoservicewhenstreaming == False and self.enigma_type == 0:
					self.GetStreamInfosCallback()
				else:
					self.Zap()
			else:
				if self.CurrentService:
					self.session.nav.playService(self.CurrentService)
				else:
					self.session.nav.stopService()
				self.mode = self.REMOTE_TIMER_MODE
				self["channellist"].instance.show()
		else:
			self.EPGSelection()

	def Zap(self):
		try:
			sel = self["channellist"].l.getCurrentSelection()[0]
		except:
			sel = None
		if sel is None:
			return
		self["channellist"].instance.hide()
		self.ChannelListCurrentIndex = self["channellist"].getCurrentIndex()
		self["text"].setText(_("Zapping to ") + sel.servicename)

		if self.useinternal == 1 and self.mode == self.REMOTE_TIMER_MODE:
			self.session.nav.playService(eServiceReference(sel.servicereference), adjust=False)
			self.ZapCallback(None)
		else:
			if self.enigma_type == 0:
				url = self.http + "/web/zap?sRef=" + urllib.quote(sel.servicereference.decode('utf-8').encode('utf-8','ignore'))
			else:
				url = self.http + "/cgi-bin/zapTo?path=" + urllib.quote(sel.servicereference.decode('utf-8').encode('utf-8','ignore'))
			sendPartnerBoxWebCommand(url, None,10, self.username, self.password).addCallback(self.ZapCallback).addErrback(self.DoNotCareError)

	def DoNotCareError(self, dnce = None):
		# Jesses, E1 sendet 204 nach umschalten, kommt hier also immer rein...
		self.ZapCallback(dnce)

	def ZapCallback(self, callback = None):
		if self.mode == self.REMOTE_TIMER_MODE:
			self["text"].setText(_("Give Enigma time to fill epg cache..."))
			self.zapTimer.start(10000) # 10 Sekunden
		else:
			self.zapTimer.start(3000) # 3 Sekunden REMOTE_TV

	def zapTimerTimeout(self):
		if self.zapTimer.isActive():
			self.zapTimer.stop()
		if self.mode == self.REMOTE_TIMER_MODE:
			self.startRun()
		else:
			self.GetStreamInfosCallback()

	def GetStreamInfosCallback(self):
		if self.enigma_type == 0:
			url = "http://" + self.ip + ":8001/" + self["channellist"].l.getCurrentSelection()[0].servicereference
			self.StreamTV(url)
		else:
			url = self.http + "/video.m3u"
			sendPartnerBoxWebCommand(url, None,10, self.username, self.password).addCallback(self.StreamTV).addErrback(self.ChannelListDownloadError)

	def MoveItem(self, next):
		self.mode = self.REMOTE_TIMER_MODE
		self.session.nav.stopService()
		if next:
			self["channellist"].moveSelection(eListbox.moveDown)
		else:
			self["channellist"].moveSelection(eListbox.moveUp)

	def StreamTV(self, connectstring):
			self.session.nav.stopService()
			sref = eServiceReference(ENIGMA_WEBSERVICE_ID, 0, connectstring)
			self.session.nav.playService(sref, adjust=False)
			self.session.openWithCallback(self.PlayRemoteStream, RemotePlayer, self["channellist"].l.getCurrentSelection()[0].servicename,self["channellist"].l.getCurrentSelection()[0].eventtitle, self["channellist"].l.getCurrentSelection()[0].eventstart, self["channellist"].l.getCurrentSelection()[0].eventduration, self.PartnerboxEntry, self["channellist"].l.getCurrentSelection()[0].servicereference, self.session.current_dialog)

	def EPGEvent(self):
		try:
			sel = self["channellist"].l.getCurrentSelection()[0]
		except:return
		if sel is None:
			return
		self.session.openWithCallback(self.CallbackEPGEvent, RemoteTimerEventView, self.E2TimerList, sel, self.PartnerboxEntry)

	def CallbackEPGEvent(self):
		pass

	def onSelectionChanged(self):
		cur = self["channellist"].getCurrent()
		if cur is None:
			self["key_green"].setText("")
			self.key_green_choice = self.EMPTY
			self["key_yellow"].setText("")
			self["key_blue"].setText("")
			return
		eventid = cur[0].eventid
		if eventid ==0:
			self["key_green"].setText("")
			self.key_green_choice = self.EMPTY
			self["key_yellow"].setText("")
			self["key_blue"].setText("")
			return
		if self.playeronly == 0:
			self["key_yellow"].setText(_("EPG Selection"))
		self["key_blue"].setText(_("Info"))
		serviceref = cur[0].servicereference

	def ChannelListDownloadCallback(self, callback = None):
		self.readXMLServiceList(callback)
		if self.ChannelListCurrentIndex !=0:
			sel = self["channellist"].moveSelectionTo(self.ChannelListCurrentIndex)
			self.ChannelListCurrentIndex = 0
		self["channellist"].instance.show()

	def ChannelListDownloadError(self, error = None):
		if error is not None:
			self["text"].setText(str(_(error.getErrorMessage())))
			self.mode = REMOTE_TIMER_MODE

	def getChannelList(self):
		if self.enigma_type == 0:
			ref = urllib.quote(self.servicereference.decode('utf-8').encode('utf-8','ignore'))
			url = self.http + "/web/epgnow?bRef=" + ref
			sendPartnerBoxWebCommand(url, None,10, self.username, self.password).addCallback(self.ChannelListDownloadCallback).addErrback(self.ChannelListDownloadError)
		else:
			self.readXMLServiceListE1()
			if self.ChannelListCurrentIndex !=0:
				sel = self["channellist"].moveSelectionTo(self.ChannelListCurrentIndex)
				self.ChannelListCurrentIndex = 0
			self["channellist"].instance.show()

	def readXMLServiceListE1(self):
		self.E2ChannelList = []
		root = xml.etree.cElementTree.fromstring(self.E1XMLString)
		for bouquets in root.findall("bouquet"):
			tempref = str(bouquets.findtext("reference", '').encode("utf-8", 'ignore'))
			if tempref == self.servicereference:
				for services in bouquets.findall("service"):
					servicereference = str(services.findtext("reference", '').encode("utf-8", 'ignore'))
					servicename = str(services.findtext("name", 'n/a').encode("utf-8", 'ignore'))
					http_ = "%s:%d" % (self.ip,self.port)
					url = "http://" + self.username + ":" + self.password + "@" + http_ + "/xml/serviceepg?ref=" + servicereference + "&entries=1"
					f = urllib.urlopen(url)
					sxml = f.read()
					eventstart, eventduration, eventtitle, eventdescriptionextended, eventdescription, eventid = self.XMLReadEPGDataE1(sxml)
					self.E2ChannelList.append(E2EPGListAllData(servicereference = servicereference, servicename = servicename, eventstart = eventstart, eventduration = eventduration, eventtitle = eventtitle, eventid = eventid , eventdescription= eventdescription, eventdescriptionextended = eventdescriptionextended))
		self["channellist"].buildList(self.E2ChannelList)

	def XMLReadEPGDataE1(self,xmlstring):
		eventstart = 0
		eventduration = 0
		eventtitle = ""
		eventdescriptionextended = ""
		eventdescription = ""
		eventid = 0
		xmlstring = xmlstring.replace("""<?xml-stylesheet type="text/xsl" href="/xml/serviceepg.xsl"?>""","")
		root = xml.etree.cElementTree.fromstring(xmlstring)
		for events in root.findall("event"):
			try:eventtitle = str(events.findtext("description", '').encode("utf-8", 'ignore'))
			except:eventtitle = ""
			try:eventdescriptionextended = str(events.findtext("details", '').encode("utf-8", 'ignore'))
			except:eventdescriptionextended = ""
			try:eventdescription = str(events.findtext("genre", '').encode("utf-8", 'ignore'))
			except:eventdescription = ""
			try:eventstart = int(events.findtext("start", 0))
			except:eventstart = 0
			try:eventduration = int(events.findtext("duration", 0))
			except:eventduration = 0
		if eventstart != 0:
			eventid = 1

		return eventstart, eventduration, eventtitle, eventdescriptionextended, eventdescription,eventid

	def readXMLServiceList(self, xmlstring):
		self.E2ChannelList = []
		root = xml.etree.cElementTree.fromstring(xmlstring)
		for events in root.findall("e2event"):
			servicereference = str(events.findtext("e2eventservicereference", '').encode("utf-8", 'ignore'))
			servicename = str(events.findtext("e2eventservicename", 'n/a').encode("utf-8", 'ignore'))
			try:eventstart = int(events.findtext("e2eventstart", 0))
			except:eventstart = 0
			try:eventduration = int(events.findtext("e2eventduration", 0))
			except:eventduration  = 0
			try:eventtitle = str(events.findtext("e2eventtitle", '').encode("utf-8", 'ignore'))
			except:eventtitle = ""
			try:eventid = int(events.findtext("e2eventid", 0))
			except:eventid = 0
			try:eventdescription = str(events.findtext("e2eventdescription", '').encode("utf-8", 'ignore'))
			except:eventdescription = ""
			try:eventdescriptionextended = str(events.findtext("e2eventdescriptionextended", '').encode("utf-8", 'ignore'))
			except:eventdescriptionextended = ""
			self.E2ChannelList.append(E2EPGListAllData(
					servicereference = servicereference, servicename = servicename, eventstart = eventstart,
					eventduration = eventduration, eventtitle = eventtitle, eventid = eventid, eventdescription= eventdescription,
					eventdescriptionextended = eventdescriptionextended))
		self["channellist"].buildList(self.E2ChannelList)

	def EPGSelection(self):
		if self.playeronly == 0:
			try:
				sel = self["channellist"].l.getCurrentSelection()[0]
				if sel is None:
					return
				if sel.eventid != 0:
					self.session.openWithCallback(self.CallbackEPGSelection, RemoteTimerEPGList, self.E2TimerList, sel.servicereference, sel.servicename, self.PartnerboxEntry)
			except: return

	def CallbackEPGSelection(self):
		pass

class RemotePlayer(Screen, InfoBarAudioSelection):
	if HD:
		skin="""
			<screen name="RemotePlayer" flags="wfNoBorder" position="283,102" size="720,576" title="Partnerbox - RemotePlayer" backgroundColor="#FFFFFFFF">
				<ePixmap position="41,388" zPosition="-1" size="630,130" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/ExPlayer.png" alphatest="off" transparent="1"/>
				<widget name="ServiceName" zPosition="1" position="50,404" size="610,59" valign="center" halign="center" font="Regular;21" foregroundColor="#F0F0F0" backgroundColor="#302C2C39" />
				<widget name="DateTime" zPosition="1" position="52,473" size="500,30" halign="left" font="Regular;16" foregroundColor="#F0F0F0" backgroundColor="#302C2C39" transparent="1" />
				<widget name="IP" zPosition="2" position="361,473" size="300,30" halign="right" font="Regular;16" foregroundColor="#F0F0F0" backgroundColor="#302C2C39" transparent="1" />
			</screen>"""
	else:
		skin="""
			<screen name="RemotePlayer" flags="wfNoBorder" position="3,30" size="720,576" title="Partnerbox - RemotePlayer" backgroundColor="#FFFFFFFF">
				<ePixmap position="41,388" zPosition="-1" size="630,130" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/ExPlayer.png" alphatest="off" transparent="1"/>
				<widget name="ServiceName" zPosition="1" position="50,404" size="610,59" valign="center" halign="center" font="Regular;21" foregroundColor="#F0F0F0" backgroundColor="#302C2C39" />
				<widget name="DateTime" zPosition="1" position="52,473" size="500,30" halign="left" font="Regular;16" foregroundColor="#F0F0F0" backgroundColor="#302C2C39" transparent="1" />
				<widget name="IP" zPosition="2" position="361,473" size="300,30" halign="right" font="Regular;16" foregroundColor="#F0F0F0" backgroundColor="#302C2C39" transparent="1" />
			</screen>"""

	def __init__(self, session, ServiceName, EventTitle, eventstart, eventduration, partnerboxentry, servicereference, parent = None):
		self.session = session
		Screen.__init__(self, session)
		self.setTitle(_("Partnerbox - RemotePlayer"))
		InfoBarAudioSelection.__init__(self)
		self.enigma_type = int(partnerboxentry.enigma.value)
		self.useinternal = int(partnerboxentry.useinternal.value)
		endtime = int(eventstart + eventduration)
		tt = ((" %s ... %s (+%d " + _("mins") + ")") % (FuzzyTime(eventstart)[1], FuzzyTime(endtime)[1], (endtime - time.time()) / 60))
		self["ServiceName"] = Label(EventTitle)
		self.ip = "%d.%d.%d.%d" % tuple(partnerboxentry.ip.value)
		port = partnerboxentry.port.value
		self.http = self.http = "http://%s:%d" % (self.ip,port)
		self["IP"] = Label(self.ip)
		if eventstart != 0:
			self["DateTime"] = Label(ServiceName + ": " + tt)
		else:
			self["DateTime"] = Label()
		self.isVisible = True
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions"],
		{
			"ok": self.Infobar,
			"back": self.close,
			"right": self.nextChannel,
			"left": self.previousChannel,
			"blue": self.showVCS,
			"up": self.nextPipService,
			"down": self.prevPipService,
			"red": self.activatePiP,
			"green": self.openServiceList,
		}, -1)
		self.password = partnerboxentry.password.value
		self.username = "root"
		self.servicereference = servicereference
		self.onLayoutFinish.append(self.startRun)
		self.onClose.append(self.__onClose)

		self.parent = parent
		self.Timer = eTimer()
		self.Timer.timeout.get().append(self.TimerTimeout)
		if InfoBar.instance is not None:
			self.servicelist = InfoBar.instance.servicelist
		else:
			self.servicelist = None
		slist = self.servicelist
		if slist:
			try:
				self.pipZapAvailable = slist.dopipzap
			except:
				self.pipZapAvailable = None

	def openServiceList(self):
		if self.pipZapAvailable is None:
			return
		if self.servicelist and self.servicelist.dopipzap:
			self.session.execDialog(self.servicelist)

	def activatePiP(self):
		if self.pipZapAvailable is None:
			return
		if SystemInfo.get("NumVideoDecoders", 1) > 1:
			if InfoBar.instance is not None:
				modeslist = [ ]
				keyslist = [ ]
				if InfoBar.pipShown(InfoBar.instance):
					slist = self.servicelist
					if slist:
						try:
							if slist.dopipzap:
								modeslist.append((_("Zap focus to main screen"), "pipzap"))
							else:
								modeslist.append((_("Zap focus to Picture in Picture"), "pipzap"))
							keyslist.append('red')
						except:
							pass
					modeslist.append((_("Move Picture in Picture"), "move"))
					keyslist.append('green')
					modeslist.append((_("Disable Picture in Picture"), "stop"))
					keyslist.append('blue')
				else:
					modeslist.append((_("Activate Picture in Picture"), "start"))
					keyslist.append('blue')
				dlg = self.session.openWithCallback(self.pipAnswerConfirmed, ChoiceBox, title=_("Choose action:"), list = modeslist, keys = keyslist)
				dlg.setTitle(_("Menu PiP"))

	def pipAnswerConfirmed(self, answer):
		answer = answer and answer[1]
		if answer is None:
			return
		if answer == "pipzap":
			try:
				InfoBar.togglePipzap(InfoBar.instance)
			except:
				pass
		elif answer == "move":
			if InfoBar.instance is not None:
				InfoBar.movePiP(InfoBar.instance)
		elif answer == "stop":
			if InfoBar.instance is not None:
				if InfoBar.pipShown(InfoBar.instance):
					slist = self.servicelist
					try:
						if slist and slist.dopipzap:
							slist.togglePipzap()
					except:
						pass
					if hasattr(self.session, 'pip'):
						del self.session.pip
					self.session.pipshown = False
		elif answer == "start":
			prev_playingref = self.session.nav.getCurrentlyPlayingServiceReference()
			if prev_playingref:
				self.session.nav.currentlyPlayingServiceReference = None
			InfoBar.showPiP(InfoBar.instance)
			if prev_playingref:
				self.session.nav.currentlyPlayingServiceReference = prev_playingref
			slist = self.servicelist
			if slist:
				try:
					if not slist.dopipzap and hasattr(self.session, 'pip'):
						InfoBar.togglePipzap(InfoBar.instance)
				except:
					pass

	def nextPipService(self):
		if self.pipZapAvailable is None:
			return
		try:
			slist = self.servicelist
			if slist and slist.dopipzap:
				if slist.inBouquet():
					prev = slist.getCurrentSelection()
					if prev:
						prev = prev.toString()
						while True:
							if config.usage.quickzap_bouquet_change.value and slist.atEnd():
								slist.nextBouquet()
							else:
								slist.moveDown()
							cur = slist.getCurrentSelection()
							if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
								break
				else:
					slist.moveDown()
				slist.zap(enable_pipzap = True)
		except:
			pass

	def prevPipService(self):
		if self.pipZapAvailable is None:
			return
		try:
			slist = self.servicelist
			if slist and slist.dopipzap:
				if slist.inBouquet():
					prev = slist.getCurrentSelection()
					if prev:
						prev = prev.toString()
						while True:
							if config.usage.quickzap_bouquet_change.value:
								if slist.atBegin():
									slist.prevBouquet()
							slist.moveUp()
							cur = slist.getCurrentSelection()
							if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
								break
				else:
					slist.moveUp()
				slist.zap(enable_pipzap = True)
		except:
			pass

	def showVCS(self):
		try:
			from Plugins.Extensions.VCS.plugin import show_choisebox
		except:
			pass
		else:
			try:
				show_choisebox(self.session)
			except:
				pass

	def nextChannel(self):
		if self.parent is not None:
			self.parent.MoveItem(True)
			self.close()

	def previousChannel(self):
		if self.parent is not None:
			self.parent.MoveItem(False)
			self.close()

	def TimerTimeout(self):
		if self.Timer.isActive():
			self.Timer.stop()
		self.Infobar()

	def startRun(self):
		idx = config.usage.infobar_timeout.index
		if idx:
			self.Timer.start(idx * 1000)
		else:
			self.Timer.start(6 * 1000)
		if self.enigma_type == 0:
			url = self.http + "/web/epgservicenow?sRef=" + self.servicereference
		else:
			url = self.http + "/xml/serviceepg?ref=" + self.servicereference + "&entries=1"
		sendPartnerBoxWebCommand(url, None,10, self.username, self.password).addCallback(self.CurrentEPGCallback).addErrback(self.CurrentEPGCallbackError)

	def CurrentEPGCallback(self, xmlstring):
		xmlstring = xmlstring.replace("""<?xml-stylesheet type="text/xsl" href="/xml/serviceepg.xsl"?>""","")
		root = xml.etree.cElementTree.fromstring(xmlstring)
		e2eventtitle = ""
		e2eventservicename = ""
		e2eventstart = 0
		e2eventduration = 0
		if self.enigma_type == 0:
			for events in root.findall("e2event"):
				try:e2eventservicename = str(events.findtext("e2eventservicename", 'n/a').encode("utf-8", 'ignore'))
				except:e2eventservicename = "n/a"
				try:e2eventstart = int(events.findtext("e2eventstart", 0))
				except:e2eventstart = 0
				try:e2eventduration = int(events.findtext("e2eventduration", 0))
				except:e2eventduration  = 0
				try:e2eventtitle = str(events.findtext("e2eventtitle", '').encode("utf-8", 'ignore'))
				except:e2eventtitle = ""
		else:
			for services in root.findall("service"):
				try:e2eventservicename = str(services.findtext("name", 'n/a').encode("utf-8", 'ignore'))
				except:e2eventservicename = "n/a"
			for events in root.findall("event"):
				try:e2eventstart = int(events.findtext("start", 0))
				except:e2eventstart = 0
				try:e2eventduration = int(events.findtext("duration", 0))
				except:e2eventduration  = 0
				try:e2eventtitle = str(events.findtext("description", '').encode("utf-8", 'ignore'))
				except:e2eventtitle = ""
		endtime = int(e2eventstart + e2eventduration)
		if endtime != 0:
			tt = ((": %s ... %s (+%d " + _("mins") + ")") % (FuzzyTime(e2eventstart)[1], FuzzyTime(endtime)[1], (endtime - time.time()) / 60))
		else:
			tt = ""
		self["ServiceName"].setText(e2eventtitle)
		self["DateTime"].setText(e2eventservicename + tt)

	def CurrentEPGCallbackError(self, error = None):
		print "[RemotePlayer] Error: ",error.getErrorMessage()

#	def readXMSubChanelList(self, xmlstring):
#		BouquetList = []
#		counter = 0
#		dom = xml.dom.minidom.parseString(xmlstring)
#		for node in dom.firstChild.childNodes:
#			servicereference = ""
#			servicename = ""
#			if node.nodeName == "e2service":
#				for node2 in node.childNodes:
#					if node2.nodeName == "e2servicereference": servicereference = str(node2.firstChild.data.strip().encode("utf-8"))
#					if node2.nodeName == "e2servicename":
#						try:servicename = str(node2.firstChild.data.strip().encode("utf-8"))
#						except:servicename = "n/a"
#						if counter != 0: # erster Eintrag ist der aktuelle Sedner, nicht aufnehmen
#							BouquetList.append(E2ServiceList(servicereference = servicereference, servicename = servicename))
#						counter += 1

	def Infobar(self):
		if self.isVisible:
			if self.Timer.isActive():
				self.Timer.stop()
			self.hide()
			self.isVisible = False
		else:
			self.startRun()
			self.show()
			self.isVisible = True

	def __onClose(self):
		if self.Timer.isActive():
			self.Timer.stop()

class RemoteTimerEPGList(Screen):
	EMPTY = 0
	ADD_TIMER = 1
	REMOVE_TIMER = 2
	if HD:
		skin = """
			<screen name="RemoteTimerEPGList" position="center,center" size="760,540" title ="EPG Selection">
				<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/green.png" position="190,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="370,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/blue.png" position="520,0" size="140,40" alphatest="on" />
				<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
				<widget name="key_green" position="190,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="key_yellow" position="370,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
				<widget name="key_blue" position="520,0" zPosition="1" size="140,40" font="Regular;18" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
				<widget name="text" position="0,40" zPosition="1" size="560,375" font="Regular;22" halign="center" valign="center" />
				<widget name="epglist" position="0,40" zPosition="2" size="760,480" foregroundColorSelected="#ffd700" scrollbarMode="showOnDemand" />
			</screen>"""
	else:
		skin = """
			<screen name="RemoteTimerEPGList" position="center,center" size="560,440" title ="EPG Selection">
				<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
				<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
				<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
				<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
				<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
				<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
				<widget name="text" position="0,40" zPosition="1" size="560,375" font="Regular;20" halign="center" valign="center" />
				<widget name="epglist" position="0,40" zPosition="2" size="560,380" scrollbarMode="showOnDemand" />
			</screen>"""
	def __init__(self, session, E2Timerlist, ServiceReference, ServiceName, partnerboxentry):
		self.session = session
		Screen.__init__(self, session)
		self.setTitle(_("EPG Selection"))
		self.E2TimerList = E2Timerlist
		self["epglist"] = E2EPGList([],selChangedCB = self.onSelectionChanged)
		self["key_red"] = Label()# Dummy, kommt eventuell noch was
		self["key_green"] = Label(_("Add timer"))
		self.key_green_choice = self.ADD_TIMER
		self["key_yellow"] = Label() # Dummy, kommt eventuell noch was
		self["key_blue"] = Label(_("Info"))
		self["text"] = Label(_("Getting EPG Information..."))
		self.onLayoutFinish.append(self.startRun)
		self.servicereference = ServiceReference
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions"],
		{
			"back": self.close,
			"green": self.GreenPressed,
			"blue": self.EPGEvent,
			"ok": self.EPGEvent,
		}, -1)

		self.PartnerboxEntry = partnerboxentry
		self.password = partnerboxentry.password.value
		self.username = "root"
		self.ip = "%d.%d.%d.%d" % tuple(partnerboxentry.ip.value)
		port = partnerboxentry.port.value
		self.http = "http://%s:%d" % (self.ip,port)
		self.enigma_type = int(partnerboxentry.enigma.value)
		self.useinternal = int(partnerboxentry.useinternal.value)

		if self.enigma_type == 0:
			self.url = self.http + "/web/epgservice?sRef=" + urllib.quote(self.servicereference.decode('utf-8').encode('utf-8','ignore'))
		else:
			self.url = self.http + "/xml/serviceepg?ref=" + urllib.quote(self.servicereference.decode('utf-8').encode('utf-8','ignore'))
		self.ListCurrentIndex = 0
		self.Locations = []

	def EPGEvent(self):
		try:
			sel = self["epglist"].l.getCurrentSelection()[0]
		except:return
		if sel is None:
			return
		self.session.openWithCallback(self.CallbackEPGEvent, RemoteTimerEventView, self.E2TimerList, sel, self.PartnerboxEntry)

	def CallbackEPGEvent(self):
		pass

	def onSelectionChanged(self):
		cur = self["epglist"].getCurrent()
		if cur is None:
			self["key_green"].setText("")
			self.key_green_choice = self.EMPTY
			self["key_blue"].setText("")
			return
		serviceref = cur[0].servicereference
		eventid = cur[0].eventid
		if eventid == 0:
			self["key_green"].setText("")
			self.key_green_choice = self.EMPTY
			self["key_blue"].setText("")
			return
		self["key_blue"].setText(_("Info"))

		timerentry = isInTimerList(cur[0].eventstart,cur[0].eventduration, cur[0].servicereference, cur[0].eventid, self.E2TimerList)
		if timerentry is None:
			if self.key_green_choice != self.ADD_TIMER:
				self["key_green"].setText(_("Add timer"))
				self.key_green_choice = self.ADD_TIMER
		else:
			if self.key_green_choice != self.REMOVE_TIMER:
				self["key_green"].setText(_("Remove timer"))
				self.key_green_choice = self.REMOVE_TIMER

	def startRun(self):
		if self.useinternal == 1:
			EPGList = []
			a = Services(self.session)
			EPGList = a.buildEPGList(self.servicereference)
			self["epglist"].buildList(EPGList, self.E2TimerList)
			if self.ListCurrentIndex != 0:
				sel = self["epglist"].moveSelectionTo(self.ListCurrentIndex)
				self.ListCurrentIndex = 0
		else:
			self["epglist"].instance.hide()
			self.getEPGList()

	def getEPGList(self):
			sendPartnerBoxWebCommand(self.url, None,10, self.username, self.password).addCallback(self.EPGListDownloadCallback).addErrback(self.EPGListDownloadError)

	def EPGListDownloadCallback(self, callback = None):
		if self.enigma_type == 0:
			self.readXMLEPGList(callback)
		else:
			self.readXMLEPGListE1(callback)
		self["epglist"].instance.show()

	def EPGListDownloadError(self, error = None):
		if error is not None:
			self["text"].setText(str(_(error.getErrorMessage())))

	def readXMLEPGListE1(self, xmlstring):
		E1ListEPG = []
		xmlstring = xmlstring.replace("""<?xml-stylesheet type="text/xsl" href="/xml/serviceepg.xsl"?>""","")
		root = xml.etree.cElementTree.fromstring(xmlstring)
		for services in root.findall("service"):
			servicereference = str(services.findtext("reference", 'n/a').decode("utf-8").encode("utf-8", 'ignore'))
			try:servicename = str(services.findtext("name", 'n/a').decode("utf-8").encode("utf-8", 'ignore'))
			except:servicename = "n/a"
		for events in root.findall("event"):
			try:eventstart = int(events.findtext("start", 0))
			except:eventstart = 0
			try:eventduration = int(events.findtext("duration", 0))
			except:eventduration  = 0
			try:eventtitle = str(events.findtext("description", '').decode("utf-8").encode("utf-8", 'ignore'))
			except:eventtitle = ""
			try:eventdescription = str(events.findtext("genre", '').decode("utf-8").encode("utf-8", 'ignore'))
			except:eventdescription = ""
			try:eventdescriptionextended = str(events.findtext("details", '').decode("utf-8").encode("utf-8", 'ignore'))
			except:eventdescriptionextended = ""
			E1ListEPG.append(E2EPGListAllData(servicereference = servicereference, servicename = servicename, eventid = 1, eventstart = eventstart, eventduration = eventduration, eventtitle = eventtitle, eventdescription = eventdescription, eventdescriptionextended = eventdescriptionextended  ))
		self["epglist"].buildList(E1ListEPG, self.E2TimerList)
		if self.ListCurrentIndex != 0:
			sel = self["epglist"].moveSelectionTo(self.ListCurrentIndex)
			self.ListCurrentIndex = 0

	def readXMLEPGList(self, xmlstring):
		E2ListEPG = []
		root = xml.etree.cElementTree.fromstring(xmlstring)
		for events in root.findall("e2event"):
			servicereference = str(events.findtext("e2eventservicereference", '').decode("utf-8").encode("utf-8", 'ignore'))
			servicename = str(events.findtext("e2eventservicename", 'n/a').decode("utf-8").encode("utf-8", 'ignore'))
			try:eventstart = int(events.findtext("e2eventstart", 0))
			except:eventstart = 0
			try:eventduration = int(events.findtext("e2eventduration", 0))
			except:eventduration  = 0
			try:eventtitle = str(events.findtext("e2eventtitle", '').decode("utf-8").encode("utf-8", 'ignore'))
			except:eventtitle = ""
			try:eventid = int(events.findtext("e2eventid", -1))
			except:eventid = -1
			try:eventdescription = str(events.findtext("e2eventdescription", '').decode("utf-8").encode("utf-8", 'ignore'))
			except:eventdescription = ""
			try:eventdescriptionextended = str(events.findtext("e2eventdescriptionextended", '').decode("utf-8").encode("utf-8", 'ignore'))
			except:eventdescriptionextended = ""
			E2ListEPG.append(E2EPGListAllData(servicereference = servicereference, servicename = servicename, eventid = eventid, eventstart = eventstart, eventduration = eventduration, eventtitle = eventtitle, eventdescription = eventdescription, eventdescriptionextended = eventdescriptionextended  ))
		self["epglist"].buildList(E2ListEPG, self.E2TimerList)
		if self.ListCurrentIndex != 0:
			sel = self["epglist"].moveSelectionTo(self.ListCurrentIndex)
			self.ListCurrentIndex = 0

	def GreenPressed(self):
		if self.key_green_choice == self.ADD_TIMER:
			if self.enigma_type == 0:
				self.getLocations()
			else:
				self.addTimerEvent()
		elif self.key_green_choice == self.REMOVE_TIMER:
			self.deleteTimer()

	def LocationsError(self, error = None):
		if error is not None:
			self["epglist"].instance.hide()
			self["text"].setText(str(_(error.getErrorMessage())))

	def getLocations(self):
		sCommand = self.http + "/web/getlocations"
		sendPartnerBoxWebCommand(sCommand, None,3, self.username, self.password).addCallback(self.getLocationsCallback).addErrback(self.LocationsError)

	def getLocationsCallback(self, xmlstring):
		self.Locations = []
		self.Locations = FillLocationList(xmlstring)
		self.addTimerEvent()

	def addTimerEvent(self):
		cur = self["epglist"].getCurrent()
		if cur is None:
			return
		cur_eventId = -1
		if self.enigma_type == 0:
			description = cur[0].eventdescription
			cur_eventId = cur[0].eventid
			type = 0
			dirname = "None"
		else:
			dirname = ""
			type = PlaylistEntry.RecTimerEntry|PlaylistEntry.recDVR
			description = cur[0].eventtitle
		timerentry = E2Timer(servicereference = cur[0].servicereference, servicename = cur[0].servicename, name = cur[0].eventtitle, disabled = 0, timebegin = cur[0].eventstart, timeend = cur[0].eventstart + cur[0].eventduration, duration = cur[0].eventduration, startprepare = 0, state = 0 , repeated = 0, justplay= 0, eventId = cur_eventId, afterevent = 3, dirname = dirname, description = description, type = type)
		self.session.openWithCallback(self.RemoteTimerEntryFinished, RemoteTimerEntry, timerentry, self.Locations)

	def RemoteTimerEntryFinished(self, answer):
		if answer[0]:
			self.ListCurrentIndex = self["epglist"].getCurrentIndex()
			entry = answer[1]
			self["epglist"].instance.hide()
			if self.enigma_type == 0:
				refstr = ':'.join(str(entry.servicereference).split(':')[:11])
				ref = urllib.quote(refstr.decode('utf-8').encode('utf-8','ignore')) + "&begin=" + ("%s"%(entry.timebegin)) + "&end=" + ("%s"%(entry.timeend))  + "&name=" + urllib.quote(entry.name) + "&description=" + urllib.quote(entry.description) + "&dirname=" + urllib.quote(entry.dirname) + "&eit=" + ("%s"%(entry.eventId)) +"&justplay=" + ("%s"%(entry.justplay)) + "&afterevent=" + ("%s"%(entry.afterevent))
				sCommand = self.http + "/web/timeradd?sRef=" + ref
				sendPartnerBoxWebCommand(sCommand, None,10, self.username, self.password).addCallback(self.deleteTimerCallback).addErrback(self.EPGListDownloadError)
			else:
				if entry.justplay & PlaylistEntry.SwitchTimerEntry:
					action = "zap"
				elif entry.justplay & PlaylistEntry.recNgrab:
					action = "ngrab"
				else:
					action = ""
				ref = urllib.quote(entry.servicereference.decode('utf-8').encode('utf-8','ignore')) + "&start=" + ("%s"%(entry.timebegin)) + "&duration=" + ("%s"%(entry.timeend - entry.timebegin))  + "&descr=" + urllib.quote(entry.description) + "&channel=" + urllib.quote(entry.servicename) + "&after_event=" + ("%s"%(entry.afterevent)) + "&action=" + ("%s"%(action))
				sCommand = self.http + "/addTimerEvent?ref=" + ref
				sendPartnerBoxWebCommand(sCommand, None,10, self.username, self.password).addCallback(self.deleteTimerCallback).addErrback(self.EPGListDownloadError)

	def deleteTimer(self):
		cur = self["epglist"].getCurrent()
		if cur is None:
			return
		timerentry = isInTimerList(cur[0].eventstart,cur[0].eventduration, cur[0].servicereference, cur[0].eventid, self.E2TimerList)
		if timerentry is None:
			return
		else:
			title_text = timerentry.repeated and _("Attention, this is repeated timer!\n") or ""
			self.session.openWithCallback(self.deleteTimerConfirmed, MessageBox, title_text + _("Do you really want to delete the timer \n%s ?") % timerentry.name)

	def deleteTimerConfirmed(self, val):
		if val:
			cur = self["epglist"].getCurrent()
			if cur is None:
				return
			self.ListCurrentIndex = self["epglist"].getCurrentIndex()
			timerentry = isInTimerList(cur[0].eventstart,cur[0].eventduration, cur[0].servicereference, cur[0].eventid, self.E2TimerList)
			if timerentry is None:
				return
			else:
				self["epglist"].instance.hide()
				if self.enigma_type == 0:
					refstr = ':'.join(str(timerentry.servicereference).split(':')[:11])
					sCommand = self.http + "/web/timerdelete?sRef=" + refstr + "&begin=" + ("%s"%(timerentry.timebegin)) + "&end=" +("%s"%(timerentry.timeend))
				else:
					sCommand = self.http + "/deleteTimerEvent?ref=" + timerentry.servicereference + "&start=" + ("%s"%(timerentry.timebegin)) + "&type=" +("%s"%(timerentry.type)) + "&force=yes"
				sendPartnerBoxWebCommand(sCommand, None,3, self.username, self.password).addCallback(self.deleteTimerCallback).addErrback(self.EPGListDownloadError)

	def deleteTimerCallback(self, callback = None):
		if self.enigma_type == 0:
			url = self.http + "/web/timerlist"
		else:
			if callback.find("Timer event deleted successfully.") != -1:
				msg = _("Timer event deleted successfully.")
			else:
				msg = callback
			self.session.open(MessageBox,msg,  MessageBox.TYPE_INFO, timeout = 3)
			url = self.http + "/xml/timers"
		sendPartnerBoxWebCommand(url, None,10, self.username, self.password).addCallback(self.readXML).addErrback(self.EPGListDownloadError)

	def readXML(self, xmlstring = None):
		if xmlstring is not None:
			self["text"].setText(_("Getting timerlist data..."))
			self.E2TimerList = []
			if self.enigma_type == 0:
				self.E2TimerList = FillE2TimerList(xmlstring)
			else:
				self.E2TimerList = FillE1TimerList(xmlstring)
			self["text"].setText(_("Getting EPG data..."))
			if self.useinternal == 1:
				EPGList = []
				a = Services(self.session)
				EPGList = a.buildEPGList(self.servicereference)
				self["epglist"].buildList(EPGList, self.E2TimerList)
				self["epglist"].instance.show()
				if self.ListCurrentIndex != 0:
					sel = self["epglist"].moveSelectionTo(self.ListCurrentIndex)
					self.ListCurrentIndex = 0
			else:
				self.getEPGList()

class E2TimerMenu(GUIComponent, object):
	def __init__(self, enigma_type):
		GUIComponent.__init__(self)
		self.l = eListboxPythonMultiContent()
		if enigma_type == 0:
			self.l.setBuildFunc(self.buildEntry)
		else:
			self.l.setBuildFunc(self.buildEntryE1)
		font = skin.fonts.get("PartnerBoxE2TimerMenu0", ("Regular", 20, 70))
		self.l.setFont(0, gFont(font[0], font[1]))
		self.l.setItemHeight(font[2])
		font = skin.fonts.get("PartnerBoxE2TimerMenu1", ("Regular", 18))
		self.l.setFont(1, gFont(font[0], font[1]))
		self.iconWait = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/timer_wait.png"))
		self.iconRecording = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/timer_rec.png"))
		self.iconPrepared = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/timer_prep.png"))
		self.iconDone = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/timer_done.png"))
		self.iconRepeat = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/timer_rep.png"))
		self.iconZapped = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/timer_zap.png"))
		self.iconDisabled = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/timer_off.png"))

	def buildEntry(self, timer):
		width = self.l.getItemSize().width()
		res = [ timer ]
		x, y, h = skin.parameters.get("PartnerBoxTimerServicename",(0, 0, 30))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, width, h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, timer.servicename + '      ' + self.getOrbitalPos(timer.servicereference)))
		x, y, h = skin.parameters.get("PartnerBoxTimerName",(0, 30, 20))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, width, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, timer.name))
		repeatedtext = ""
		days = [ _("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun") ]
		icon = None
		x, y, w, h = skin.parameters.get("PartnerBoxE2TimerTime",(0, 50, 150, 20))
		if timer.repeated:
			flags = timer.repeated
			count = 0
			for x in range(0, 7):
					if (flags & 1 == 1):
						if (count != 0):
							repeatedtext += ", "
						repeatedtext += days[x]
						count += 1
					flags = flags >> 1
			if self.iconRepeat:
				x1, y1, w1, h1 = skin.parameters.get("PartnerBoxE2TimerIconRepeat",(510, 30, 20, 20))
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x1, y1, w1, h1, self.iconRepeat))
			if timer.justplay:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, width-w, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + ((" %s "+ _("(ZAP)")) % (FuzzyTime(timer.timebegin)[1]))))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, width-w, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + ((" %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(timer.timebegin)[1], FuzzyTime(timer.timeend)[1], (timer.timeend - timer.timebegin) / 60))))
		else:
			if timer.justplay:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, width-w, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + (("%s, %s " + _("(ZAP)")) % (FuzzyTime(timer.timebegin)))))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, width-w, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + (("%s, %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(timer.timebegin) + FuzzyTime(timer.timeend)[1:] + ((timer.timeend - timer.timebegin) / 60,)))))

		if timer.state == TimerEntry.StateWaiting:
			state = _("waiting")
			icon = self.iconWait
		elif timer.state == TimerEntry.StatePrepared:
			state = _("about to start")
			icon = self.iconPrepared
		elif timer.state == TimerEntry.StateRunning:
			if timer.justplay:
				state = _("zapped")
				icon = self.iconZapped
			else:
				state = _("recording...")
				icon = self.iconRecording
		elif timer.state == TimerEntry.StateEnded:
			state = _("done!")
			icon = self.iconDone
		else:
			state = _("<unknown>")
			icon = None

		if timer.disabled:
			state = _("disabled")
			icon = self.iconDisabled

		x, y, w, h = skin.parameters.get("PartnerBoxE2TimerState",(150, 50, 150, 20))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width-x, y, w, h, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, state))

		#if timer.disabled:
		#	png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/redx.png"))
		#	x, y, w, h = skin.parameters.get("PartnerBoxE2TimerIcon",(490, 5, 40, 40))
		#	res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x, y, w, h, png))
		if icon:
			x, y, w, h = skin.parameters.get("PartnerBoxE2TimerIcon",(510, 5, 20, 20))
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, x, y, w, h, icon))

		return res

	def buildEntryE1(self,timer):
		width = self.l.getItemSize().width()
		res = [ timer ]
		x, y, h = skin.parameters.get("PartnerBoxTimerServicename",(0, 0, 30))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, width, h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, timer.servicename))
		x, y, h = skin.parameters.get("PartnerBoxTimerName",(0, 30, 20))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, width, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, timer.description))

		repeatedtext = ""
		days = [ _("Sun"), _("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat") ]
		x, y, w, h = skin.parameters.get("PartnerBoxE1TimerTime",(0, 50, 170, 20))
		if timer.type & PlaylistEntry.isRepeating :
			mask = PlaylistEntry.Su
			count = 0
			for x in range(0, 7):
				if timer.type & mask:
					if (count != 0):
						repeatedtext += ", "
					repeatedtext += days[x]
					count += 1
				mask *= 2
			if timer.type & PlaylistEntry.SwitchTimerEntry:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, width-w, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + ((" %s "+ _("(ZAP)")) % (FuzzyTime(timer.timebegin)[1]))))
			elif timer.type & PlaylistEntry.RecTimerEntry:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, width-w, h, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + ((" %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(timer.timebegin)[1], FuzzyTime(timer.timeend)[1], (timer.timeend - timer.timebegin) / 60))))
		else:
			if timer.type & PlaylistEntry.SwitchTimerEntry:
				res.append((eListboxPythonMultiContent.TYPE_TEXT,  x, y, width-w, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + (("%s, %s ... %s (%d " + _("mins") + ") ") % (FuzzyTime(timer.timebegin) + FuzzyTime(timer.timeend)[1:] + ((timer.timeend - timer.timebegin) / 60,))) + _("(ZAP)")))
			elif timer.type & PlaylistEntry.RecTimerEntry:
				res.append((eListboxPythonMultiContent.TYPE_TEXT,  x, y, width-w, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, repeatedtext + (("%s, %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(timer.timebegin) + FuzzyTime(timer.timeend)[1:] + ((timer.timeend - timer.timebegin) / 60,)))))

		if timer.type & PlaylistEntry.stateWaiting:
			state = _("waiting")
		elif timer.type & PlaylistEntry.stateRunning:
			if timer.type & PlaylistEntry.SwitchTimerEntry:
				state = _("zapped")
			elif timer.type & PlaylistEntry.RecTimerEntry:
				state = _("recording...")
		elif timer.type & PlaylistEntry.stateFinished:
			state = _("done!")
		elif timer.type & PlaylistEntry.stateError:
			if timer.type & PlaylistEntry.errorNoSpaceLeft:
				state = _("Error: No space left")
			elif timer.type & PlaylistEntry.errorUserAborted:
				state = _("Error: User aborted")
			elif timer.type & PlaylistEntry.errorZapFailed:
				state = _("Error: Zap failed")
			elif timer.type & PlaylistEntry.errorOutdated:
				state = _("Error: Outdated")
			else:
				state = _("Error: ") + _("<unknown>")
		else:
			state = _("<unknown>")
		x, y, w, h = skin.parameters.get("PartnerBoxE1TimerState",(170, 50, 170, 20))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, width-x, y, w, h, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, state))
		return res

	def getOrbitalPos(self, ref):
		try:
			refstr = ''
			if hasattr(ref, 'sref'):
				refstr = str(ref.sref)
			else:
				refstr = str(ref)
			refstr = ':'.join(refstr.split(':')[:11])
			if refstr.startswith('1:134:'):
				return "%s" % _("Alternative")
			if '%3a//' in refstr:
				return "%s" % _("Stream")
			op = int(refstr.split(':', 10)[6][:-4] or "0",16)
			if op == 0xeeee:
				return "%s" % _("DVB-T")
			if op == 0xffff:
				return "%s" % _("DVB-C")
			direction = 'E'
			if op > 1800:
				op = 3600 - op
				direction = 'W'
			return ("%d.%d\xc2\xb0%s") % (op // 10, op % 10, direction)
		except:
			return ''

	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)

	def preWidgetRemove(self, instance):
		instance.setContent(None)

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	currentIndex = property(getCurrentIndex, moveToIndex)
	currentSelection = property(getCurrent)

	def setList(self, list):
		self.l.setList(list)

class E2BouquetList(MenuList):
	def __init__(self, list, enableWrapAround = True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		font = skin.fonts.get("PartnerBoxBouquetList0", ("Regular", 20, 30))
		self.l.setFont(0, gFont(font[0], font[1]))
		self.ItemHeight = int(font[2])
		font = skin.fonts.get("PartnerBoxBouquetList1", ("Regular", 18))
		self.l.setFont(1, gFont(font[0], font[1]))

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(self.ItemHeight)

	def buildList(self,listnew):
		self.list=[]
		width = self.l.getItemSize().width()
		for bouquets in listnew:
			res = [ bouquets ]
			x, y, h = skin.parameters.get("PartnerBoxBouquetListName",(0, 0, 30))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, width, h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, bouquets.servicename))
			self.list.append(res)
		self.l.setList(self.list)
		self.moveToIndex(0)

class E2ChannelList(MenuList):
	def __init__(self, list, selChangedCB=None, enableWrapAround = True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.onSelChanged = [ ]
		if selChangedCB is not None:
			self.onSelChanged.append(selChangedCB)
		font = skin.fonts.get("PartnerBoxChannelList0", ("Regular", 20, 70))
		self.l.setFont(0, gFont(font[0], font[1]))
		self.ItemHeight = int(font[2])
		font = skin.fonts.get("PartnerBoxChannelList1", ("Regular", 18))
		self.l.setFont(1, gFont(font[0], font[1]))

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(self.ItemHeight)
		instance.selectionChanged.get().append(self.selectionChanged)

	def preWidgetRemove(self, instance):
		instance.selectionChanged.get().remove(self.selectionChanged)

	def selectionChanged(self):
		for x in self.onSelChanged:
			if x is not None:
				x()

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def moveSelectionTo(self,index):
		self.moveToIndex(index)

	def moveSelection(self, how):
		 self.instance.moveSelection(how)

	def buildList(self,listnew):
		self.list=[]
		width = self.l.getItemSize().width()
		for epgdata in listnew:
			res = [ epgdata ]
			event_text = epgdata.eventtitle
			if event_text == "None":
				event_text = ''
			x, y, h = skin.parameters.get("PartnerBoxChannelListName",(0, 0, 30))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, width, h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, epgdata.servicename))
			x, y, h = skin.parameters.get("PartnerBoxChannelListTitle",(0, 30, 20))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, width, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, event_text))
			if epgdata.eventstart != 0:
				endtime = int(epgdata.eventstart + epgdata.eventduration)
				prefix = "+"
				remaining = (endtime - int(time.time())) / 60
				if remaining <= 0:
					prefix = ""
				Time = _("%s%d min") % (prefix, remaining)
				x, y, w, h = skin.parameters.get("PartnerBoxChannelListTime",(0, 50, 150, 20))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, width-w, h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, Time + '  ' + (("%s ... %s (%d " + _("mins") + ")") % (FuzzyTime(epgdata.eventstart)[1], FuzzyTime(endtime)[1], (endtime - epgdata.eventstart) / 60))))
			self.list.append(res)
		self.l.setList(self.list)
		self.moveToIndex(0)

class E2EPGList(MenuList):
	def __init__(self, list, selChangedCB=None, enableWrapAround = True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.onSelChanged = [ ]
		if selChangedCB is not None:
			self.onSelChanged.append(selChangedCB)
		font = skin.fonts.get("PartnerBoxChannelEPGList0", ("Regular", 22, 30))
		self.l.setFont(0, gFont(font[0], font[1]))
		self.ItemHeight = int(font[2])
		font = skin.fonts.get("PartnerBoxChannelEPGList1", ("Regular", 16))
		self.l.setFont(1, gFont(font[0], font[1]))
		self.days = [ _("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun") ]
		self.timer_list = []
		self.clock_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock.png')
		self.clock_add_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_add.png')
		self.clock_pre_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_pre.png')
		self.clock_post_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_post.png')
		self.clock_prepost_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_prepost.png')
		self.zapclock_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_zapclock.png')
		self.zapclock_add_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_zapclock_add.png')
		self.zapclock_pre_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_zapclock_pre.png')
		self.zapclock_post_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_zapclock_post.png')
		self.zapclock_prepost_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_zapclock_prepost.png')
		#repeat
		self.repclock_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_repepgclock.png')
		self.repclock_add_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_repepgclock_add.png')
		self.repclock_pre_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_repepgclock_pre.png')
		self.repclock_post_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_repepgclock_post.png')
		self.repclock_prepost_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_repepgclock_prepost.png')
		self.repzapclock_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_repzapclock.png')
		self.repzapclock_add_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_repzapclock_add.png')
		self.repzapclock_pre_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_repzapclock_pre.png')
		self.repzapclock_post_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_repzapclock_post.png')
		self.repzapclock_prepost_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_repzapclock_prepost.png')

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(self.ItemHeight)
		instance.selectionChanged.get().append(self.selectionChanged)

	def preWidgetRemove(self, instance):
		instance.selectionChanged.get().remove(self.selectionChanged)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def moveSelectionTo(self,index):
		self.moveToIndex(index)

	def selectionChanged(self):
		for x in self.onSelChanged:
			if x is not None:
				x()

	def buildList(self,listnew, timerlist):
		self.list=[]
		self.timer_list = timerlist
		for epgdata in listnew:
			res = [ epgdata ]
			rec=epgdata.eventstart and (self.isInTimer(epgdata.eventstart, epgdata.eventduration, epgdata.servicereference))
			esize = self.l.getItemSize()
			width = esize.width()
			height = esize.height()
			r1 = Rect(0, 0, width/20*2-10, height)
			r2 = Rect(width/20*2, 0, width/20*5-15, height)
			r3 = Rect(width/20*7, 0, width/20*13, height)
			t = localtime(epgdata.eventstart)
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_RIGHT, self.days[t[6]]))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r2.left(), r2.top(), r2.width(), r1.height(), 0, RT_HALIGN_RIGHT, "%02d.%02d, %02d:%02d"%(t[2],t[1],t[3],t[4])))
			if rec:
				clock_pic = self.getClockPixmap(epgdata.servicereference, epgdata.eventstart, epgdata.eventduration, epgdata.eventid)
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left(), r3.top() + 2, 21, 21, clock_pic))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left() + 25, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, epgdata.eventtitle))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, epgdata.eventtitle))

			self.list.append(res)
		self.l.setList(self.list)
		self.moveToIndex(0)

	def isInTimer(self, begin, duration, service):
		time_match = 0
		chktime = None
		chktimecmp = None
		chktimecmp_end = None
		end = begin + duration
		service_str = ':'.join(str(service).split(':')[:11])
		for x in self.timer_list:
			servicereference_str = ':'.join(str(x.servicereference).split(':')[:11])
			if servicereference_str.upper() == service_str.upper():
				if x.repeated != 0:
					if chktime is None:
						chktime = localtime(begin)
						chktimecmp = chktime.tm_wday * 1440 + chktime.tm_hour * 60 + chktime.tm_min
						chktimecmp_end = chktimecmp + (duration / 60)
					time = localtime(x.timebegin)
					for y in range(7):
						if x.repeated & (2 ** y):
							timecmp = y * 1440 + time.tm_hour * 60 + time.tm_min
							if timecmp <= chktimecmp < (timecmp + ((x.timeend - x.timebegin) / 60)):
								time_match = ((timecmp + ((x.timeend - x.timebegin) / 60)) - chktimecmp) * 60
							elif chktimecmp <= timecmp < chktimecmp_end:
								time_match = (chktimecmp_end - timecmp) * 60
				else:
					if begin <= x.timebegin <= end:
						diff = end - x.timebegin
						if time_match < diff:
							time_match = diff
					elif x.timebegin <= begin <= x.timeend:
						diff = x.timeend - begin
						if time_match < diff:
							time_match = diff
				if time_match:
					break
		return time_match

	def getClockPixmap(self, refstr, beginTime, duration, eventId):
		type = 0
		time_match = 0
		justplay = 0
		repeated = 0
		endTime = beginTime + duration
		ref_str = ':'.join(str(refstr).split(':')[:11])
		for x in self.timer_list:
			servicereference_str = ':'.join(str(x.servicereference).split(':')[:11])
			if servicereference_str.upper() == ref_str.upper():
				justplay = x.justplay
				repeated = x.repeated
				beg = x.timebegin
				end = x.timeend
				if x.justplay:
					if (end - beg) <= 1:
						end += 60
				if beginTime < beg <= endTime:
					if end < endTime:
						time_match = end - beg
						type = 3
					else:
						time_match = endTime - beg
						type = 1
				elif beg <= beginTime <= end:
					if end < endTime:
						time_match = end - beginTime
						type = 4
					else:
						time_match = endTime - beginTime
						type = 2
				if time_match:
					if type == 2:
						if justplay:
							if repeated != 0:
								return self.repzapclock_pixmap
							else:
								return self.zapclock_pixmap
						else:
							if repeated != 0:
								return self.repclock_pixmap
							else:
								return self.clock_pixmap
					elif type == 3:
						if justplay:
							if repeated != 0:
								return self.repzapclock_prepost_pixmap
							else:
								return self.zapclock_prepost_pixmap
						else:
							if repeated != 0:
								return self.repclock_prepost_pixmap
							else:
								return self.clock_prepost_pixmap
					elif type == 4:
						if justplay:
							if repeated != 0:
								return self.repzapclock_post_pixmap
							else:
								return self.zapclock_post_pixmap
						else:
							if repeated != 0:
								return self.repclock_post_pixmap
							else:
								return self.clock_post_pixmap
					elif type == 1:
						if justplay:
							if repeated != 0:
								return self.repzapclock_pre_pixmap
							else:
								return self.zapclock_pre_pixmap
						else:
							if repeated != 0:
								return self.repclock_pre_pixmap
							else:
								return self.clock_pre_pixmap
		if justplay:
			if repeated != 0:
				return self.repzapclock_add_pixmap
			else:
				return self.zapclock_add_pixmap
		else:
			if repeated != 0:
				return self.repclock_add_pixmap
			else:
				return self.clock_add_pixmap

class RemoteTimerEventView(Screen):
	EMPTY = 0
	ADD_TIMER = 1
	REMOVE_TIMER = 2
	skin = """
		<screen name="RemoteTimerEventView" position="center,center" size="560,430" title="Eventview">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
			<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
			<widget name="epg_description" position="10,50" size="540,330" font="Regular;22" />
			<widget name="datetime" position="10,395" size="130,25" font="Regular;22" />
			<widget name="duration" position="140,395" size="100,25" font="Regular;22" />
			<widget name="channel" position="240,395" size="305,25" font="Regular;22" halign="right" />
		</screen>"""

	def __init__(self, session, E2Timerlist, epgdata , partnerboxentry):
		self.session = session
		Screen.__init__(self, session)
		self.setTitle(_("Eventview"))
		self["epg_description"] = ScrollLabel()
		self["datetime"] = Label()
		self["channel"] = Label()
		self["duration"] = Label()
		self["key_red"] = Label() # Dummy, kommt eventuell noch was
		self["key_green"] = Label() # Dummy, kommt eventuell noch was
		self["key_yellow"] = Label() # Dummy, kommt eventuell noch was
		self["key_blue"] = Label() # Dummy, kommt eventuell noch was
		self.key_green_choice = self.ADD_TIMER
		self.onLayoutFinish.append(self.startRun)
		self.E2TimerList = E2Timerlist
		self.epgdata = epgdata

		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "EventViewActions"],
		{
			"back": self.close,
			"pageUp": self.pageUp,
			"pageDown": self.pageDown,
		}, -1)

		self.PartnerboxEntry = partnerboxentry
		self.password = partnerboxentry.password.value
		self.username = "root"
		self.ip = "%d.%d.%d.%d" % tuple(partnerboxentry.ip.value)
		port = partnerboxentry.port.value
		self.http = "http://%s:%d" % (self.ip,port)
		self.enigma_type = int(partnerboxentry.enigma.value)
		self.useinternal = int(partnerboxentry.useinternal.value)

	def startRun(self):
		name = self.epgdata.servicename
		if name != "n/a":
			self["channel"].setText(name)
		else:
			self["channel"].setText(_("unknown service"))
		text = self.epgdata.eventtitle
		if text == "None":
			text = ""
		short = self.epgdata.eventdescription
		if short == "None":
			short = ""
		ext = self.epgdata.eventdescriptionextended
		if ext == "None":
			ext = ""
		if len(short) > 0 and short != text:
			text = text + '\n\n' + short
		if len(ext) > 0:
			if len(text) > 0:
				text = text + '\n\n'
			text = text + ext
		event_text = self.epgdata.eventtitle
		if event_text == "None":
			event_text = ""
		self.setTitle(event_text)
		self["epg_description"].setText(text)
		endtime = int(self.epgdata.eventstart + self.epgdata.eventduration)
		t = localtime(self.epgdata.eventstart)
		datetime = ("%02d.%02d, %02d:%02d"%(t[2],t[1],t[3],t[4]))
		duration = (" (%d " + _("mins")+")") % ((self.epgdata.eventduration ) / 60)
		self["datetime"].setText(datetime)
		self["duration"].setText(duration)
		self["key_red"].setText("")

	def pageUp(self):
		self["epg_description"].pageUp()

	def pageDown(self):
		self["epg_description"].pageDown()

from Screens.ChannelSelection import ChannelContextMenu, OFF, MODE_TV
from Components.ChoiceList import ChoiceEntryComponent
from Tools.BoundFunction import boundFunction

def autostart_ChannelContextMenu(session, **kwargs):
	partnerboxChannelContextMenuInit()

baseChannelContextMenu__init__ = None
def partnerboxChannelContextMenuInit():
	global baseChannelContextMenu__init__
	if baseChannelContextMenu__init__ is None:
		baseChannelContextMenu__init__ = ChannelContextMenu.__init__
	ChannelContextMenu.__init__ = partnerboxChannelContextMenu__init__
	ChannelContextMenu.addPartnerboxService = addPartnerboxService
	ChannelContextMenu.callbackPartnerboxServiceList = callbackPartnerboxServiceList
	ChannelContextMenu.startAddParnerboxService = startAddParnerboxService
	ChannelContextMenu.setPartnerboxService = setPartnerboxService
	ChannelContextMenu.setParentalControlPin = setParentalControlPin
	ChannelContextMenu.parentalControlPinEntered = parentalControlPinEntered

def partnerboxChannelContextMenu__init__(self, session, csel):
	baseChannelContextMenu__init__(self, session, csel)
	if not config.plugins.Partnerbox.enablepartnerboxchannelselector.value:
		return
	if csel.mode == MODE_TV:
		current_root = csel.getRoot()
		current = csel.getCurrentSelection()
		inBouquetRootList = current_root and current_root.getPath().find('FROM BOUQUET "bouquets.') != -1 #FIXME HACK
		inBouquet = csel.getMutableList() is not None
		if csel.bouquet_mark_edit == OFF and not csel.movemode:
			if not inBouquetRootList:
				if inBouquet and current and current.valid():
					if config.ParentalControl.configured.value:
						callFunction = self.setParentalControlPin
					else:
						callFunction = self.addPartnerboxService
					self["menu"].list.insert(1, ChoiceEntryComponent(text = (_("add Partnerbox service"), boundFunction(callFunction,0))))
			if (not inBouquetRootList and not inBouquet) or (inBouquetRootList):
				if config.usage.multibouquet.value:
					if config.ParentalControl.configured.value:
						callFunction = self.setParentalControlPin
					else:
						callFunction = self.addPartnerboxService
					self["menu"].list.insert(1, ChoiceEntryComponent(text = (_("add Partnerbox bouquet"), boundFunction(callFunction,1))))

def addPartnerboxService(self, insertType):
	count = config.plugins.Partnerbox.entriescount.value
	if count == 1:
		self.startAddParnerboxService(insertType, None, None, config.plugins.Partnerbox.Entries[0])
	else:
		self.session.openWithCallback(boundFunction(self.startAddParnerboxService,insertType), PartnerboxEntriesListConfigScreen, 0)

def startAddParnerboxService(self, insertType, session, what, partnerboxentry = None):
	if partnerboxentry is None:
		self.close()
	else:
		if int(partnerboxentry.enigma.value) == 0:
			self.session.openWithCallback(self.callbackPartnerboxServiceList, PartnerBouquetList, [], partnerboxentry, 1, insertType)
		else:
			self.session.open(MessageBox,_("You can not add services or bouquets from Enigma1-receivers into the channellist..."), MessageBox.TYPE_INFO)

def setParentalControlPin(self, insertType):
		self.session.openWithCallback(boundFunction(self.parentalControlPinEntered, insertType), PinInput, pinList = [config.ParentalControl.servicepin[0].value], triesEntry = config.ParentalControl.retries.servicepin, title = _("Enter the service pin"), windowTitle = _("Change pin code"))

def parentalControlPinEntered(self, insertType, result):
		if result:
			self.addPartnerboxService(insertType)
		else:
			self.session.openWithCallback(self.close, MessageBox, _("The pin code you entered is wrong."), MessageBox.TYPE_ERROR)

def callbackPartnerboxServiceList(self, result):
	if result and result[1]:
		isBouquet = result[0]
		partnerboxentry = result[2]
		if isBouquet == 0:
			servicelist = result[1]
			item = servicelist[0]
			if item and item.servicereference and str(item.servicereference).startswith("1:134:"):
				self.session.openWithCallback(self.close, MessageBox, _("Alternative services are not supported!"), MessageBox.TYPE_ERROR)
				return
			if item and item.servicereference and '%3a//' in str(item.servicereference):
				self.session.openWithCallback(self.close, MessageBox, _("Internet services are not supported!"), MessageBox.TYPE_ERROR)
				return
			current_root = self.csel.getRoot()
			mutableList = self.csel.getMutableList(current_root)
			if not mutableList is None:
				service = self.setPartnerboxService(item, partnerboxentry)
				if not mutableList.addService(service):
					self.csel.bouquetNumOffsetCache = { }
					mutableList.flushChanges()
					self.csel.servicelist.addService(service)
		elif isBouquet == 1:
			servicelist = result[1][0]
			bouquet = result[1][1]
			services = []
			for item in servicelist:
				if str(item.servicereference).startswith("1:134:"):
					continue
				if '%3a//' in str(item.servicereference):
					continue
				services.append(self.setPartnerboxService(item, partnerboxentry))
			self.csel.addBouquet("%s (%s)" % (bouquet.servicename.replace("(TV)",""), partnerboxentry.name.value), services)
	self.close()

def setPartnerboxService(self, item, partnerboxentry):
	password = partnerboxentry.password.value
	ip = "%d.%d.%d.%d" % tuple(partnerboxentry.ip.value)
	port = 8001
	if password:
		http = "http://root:%s@%s:%d/%s" % (password, ip, port, item.servicereference)
	else:
		http = "http://%s:%d/%s" % (ip, port, item.servicereference)
	service = eServiceReference(item.servicereference)
	service.setPath(http)
	service.setName("%s (%s)" % (item.servicename, partnerboxentry.name.value))
	return service

class PartnerBouquetList(RemoteTimerBouquetList):
	def __init__(self, session, E2Timerlist, partnerboxentry, playeronly, insertType):
		RemoteTimerBouquetList.__init__(self, session, E2Timerlist, partnerboxentry, playeronly)
		self.skinName = "RemoteTimerBouquetList"
		self.useinternal = 0 # always use partnerbox services
		self.insertType = insertType
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions"],
		{
			"ok": self.action,
			"back": self.closeScreen,
		}, -1)

	def action(self):
		if self.insertType == 0:
			try:
				sel = self["bouquetlist"].l.getCurrentSelection()[0]
				if sel is None:
					return
				self.session.openWithCallback(self.callbackChannelList, PartnerChannelList, self.E2TimerList, sel.servicereference, sel.servicename, self.PartnerboxEntry, self.playeronly)
			except: return
		else:
			self.takeBouquet()

	def callbackChannelList(self, result):
		self.close((0, result, self.PartnerboxEntry))

	def closeScreen(self):
		self.close(None)

	def takeBouquet(self):
		sel = None
		try:
			sel = self["bouquetlist"].l.getCurrentSelection()[0]
			if sel is None:
				return
		except: return
		ref = urllib.quote(sel.servicereference.decode('utf-8').encode('utf-8','ignore'))
		url = self.http + "/web/epgnow?bRef=" + ref
		sendPartnerBoxWebCommand(url, None,10, self.username, self.password).addCallback(self.ChannelListDownloadCallback, sel).addErrback(self.ChannelListDownloadError)

	def ChannelListDownloadCallback(self, xmlstring, sel):
		e2ChannelList = []
		if xmlstring:
			root = xml.etree.cElementTree.fromstring(xmlstring)
			for events in root.findall("e2event"):
				servicereference = str(events.findtext("e2eventservicereference", '').decode("utf-8").encode("utf-8", 'ignore'))
				servicename = str(events.findtext("e2eventservicename", 'n/a').decode("utf-8").encode("utf-8", 'ignore'))
				e2ChannelList.append(E2EPGListAllData(servicereference = servicereference, servicename = servicename))
		result = (e2ChannelList, sel)
		self.close((1, result, self.PartnerboxEntry))

	def ChannelListDownloadError(self, error = None):
		if error is not None:
			self["text"].setText(str(_(error.getErrorMessage())))

class PartnerChannelList(RemoteTimerChannelList):
	def __init__(self, session, E2Timerlist, ServiceReference, ServiceName, partnerboxentry, playeronly):
		RemoteTimerChannelList.__init__(self, session, E2Timerlist, ServiceReference, ServiceName, partnerboxentry, "",  playeronly)
		self.skinName = "RemoteTimerChannelList"
		self.useinternal = 0 # always use partnerbox services
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions"],
		{
			"ok": self.getEntry,
			"back": self.closeScreen,
			"yellow": self.doNothing,
			"blue": self.doNothing,
			"red": self.closeScreen,
		}, -1)
		self["key_green"].setText(_("Apply"))
		self.key_green_choice = self.EMPTY
		self["key_yellow"].setText("")
		self["key_blue"].setText("")
		self["key_red"].setText(_("Abort"))

	def onSelectionChanged(self):
		pass

	def doNothing(self):
		pass

	def getEntry(self):
		try:
			sel = self["channellist"].l.getCurrentSelection()[0]
		except:
			sel = None
		if sel is None:
			return
		self.close([sel])

	def closeScreen(self):
		self.close(None)
