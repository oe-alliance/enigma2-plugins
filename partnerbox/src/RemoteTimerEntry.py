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

from Screens.Screen import Screen
import Screens.ChannelSelection
from ServiceReference import ServiceReference
from Components.config import config, ConfigSelection, ConfigText, ConfigSubList, ConfigDateTime, ConfigClock, ConfigYesNo, getConfigListEntry
from Components.ActionMap import NumberActionMap
from Components.ConfigList import ConfigListScreen
from Components.MenuList import MenuList
from Components.Button import Button
from Components.Label import Label
from Components.Pixmap import Pixmap
from Screens.MovieSelection import getPreferredTagEditor
from Screens.LocationBox import MovieLocationBox
from Screens.ChoiceBox import ChoiceBox
from RecordTimer import AFTEREVENT
from Tools.Directories import resolveFilename, SCOPE_HDD
from enigma import eEPGCache
from time import localtime, mktime, time, strftime
from datetime import datetime
from Screens.TimerEntry import TimerEntry
from Screens.MessageBox import MessageBox
from Tools.BoundFunction import boundFunction
import urllib

from twisted.internet import reactor
from twisted.web import client
from twisted.web.client import HTTPClientFactory
from base64 import encodestring
import xml.dom.minidom

from Components.EpgList import EPGList
from enigma import eListboxPythonMultiContent, eListbox, gFont, \
	RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, RT_HALIGN_CENTER
import xml.dom.minidom
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_SKIN_IMAGE

remote_timer_list = None


class E2Timer:
	def __init__(self, servicereference = "", servicename = "", name = "", disabled = 0, timebegin = 0, timeend = 0, duration = 0, startprepare = 0, state = 0, repeated = 0, justplay = 0, eventId = 0, afterevent = 0, dirname = "", description = "", type = 0):
		self.servicereference = servicereference
		self.servicename = servicename
		self.name = name
		self.disabled = disabled
		self.timebegin = timebegin
		self.timeend = timeend
		self.duration = duration
		self.startprepare = startprepare
		self.state = state
		self.repeated = repeated
		self.justplay = justplay
		self.eventId = eventId
		self.afterevent = afterevent
		self.dirname = dirname
		self.description = description
		self.type = type
		if type != 0: # E1 Timerlist
			self.timeend = timebegin + duration
			self.name = description
			if type & PlaylistEntry.isRepeating:
				self.repeated = 1
			self.dirname = "/hdd/movie/"

def FillE2TimerList(xmlstring):
	E2TimerList = []
	dom = xml.dom.minidom.parseString(xmlstring)
	for node in dom.firstChild.childNodes:
		servicereference = ""
		servicename = ""
		name = ""
		disabled = 0
		timebegin = 0
		timeend = 0
		duration = 0
		startprepare = 0
		state = 0
		repeated = 0
		justplay = 0
		eventId = -1
		afterevent = 0
		dirname = ""
		description = ""
		if node.nodeName == "e2timer":
			for node2 in node.childNodes:
				if node2.nodeName == "e2servicereference": servicereference = str(node2.firstChild.data.strip().encode("utf-8"))
				if node2.nodeName == "e2servicename":
					try:servicename = str(node2.firstChild.data.strip().encode("utf-8"))
					except:servicename = "n/a"
				if node2.nodeName == "e2eit": 
					try: eventId = int(node2.firstChild.data.strip())
					except: pass
				if node2.nodeName == "e2name":
					try:name = str(node2.firstChild.data.strip().encode("utf-8"))
					except:name = ""
				if node2.nodeName == "e2description":
					try:description = str(node2.firstChild.data.strip().encode("utf-8"))
					except:description = ""
				if node2.nodeName == "e2dirname" or node2.nodeName == "e2location": # vorerst Kompatibilitaet zum alten Webinterface-Api aufrecht erhalten (e2dirname)
					try:dirname = str(node2.firstChild.data.strip().encode("utf-8"))
					except:dirname = ""
				if node2.nodeName == "e2afterevent": afterevent = int(node2.firstChild.data.strip())
				if node2.nodeName == "e2disabled": disabled = int(node2.firstChild.data.strip())
				if node2.nodeName == "e2timebegin": timebegin = int(node2.firstChild.data.strip())
				if node2.nodeName == "e2timeend": timeend = int(node2.firstChild.data.strip())
				if node2.nodeName == "e2duration": duration = int(node2.firstChild.data.strip())
				if node2.nodeName == "e2startprepare": startprepare = int(node2.firstChild.data.strip())
				if node2.nodeName == "e2state":  state= int(node2.firstChild.data.strip())
				if node2.nodeName == "e2justplay":  justplay= int(node2.firstChild.data.strip())
				if node2.nodeName == "e2repeated":
					repeated= int(node2.firstChild.data.strip())
					E2TimerList.append(E2Timer(servicereference = servicereference, servicename = servicename, name = name, disabled = disabled, timebegin = timebegin, timeend = timeend, duration = duration, startprepare = startprepare, state = state , repeated = repeated, justplay= justplay, eventId = eventId, afterevent = afterevent, dirname = dirname, description = description, type = 0 ))
	return E2TimerList


def FillE1TimerList(xmlstring):
	E1TimerList = []
	dom = xml.dom.minidom.parseString(xmlstring)
	for node in dom.firstChild.childNodes:
		type = 0
		servicereference = ""
		servicename = ""
		name = ""
		disabled = 0
		timebegin = 0
		timeend = 0
		duration = 0
		startprepare = 0
		state = 0
		repeated = 0
		justplay = 0
		eventId = -1
		afterevent = 0
		dirname = ""
		description = ""
		if node.nodeName == "timer":
			for node2 in node.childNodes:
				if node2.nodeName == "typedata": type = int(node2.firstChild.data.strip())
				if node2.nodeName == "service":
					for node3 in node2.childNodes:
						if node3.nodeName == "reference": servicereference = str(node3.firstChild.data.strip().encode("utf-8"))
						if node3.nodeName == "name":
							try:servicename = str(node3.firstChild.data.strip().encode("utf-8"))
							except:servicename = "n/a"
				if node2.nodeName == "event":
					for node3 in node2.childNodes:
						if node3.nodeName == "start": timebegin = int(node3.firstChild.data.strip())
						if node3.nodeName == "duration": duration = int(node3.firstChild.data.strip())
						if node3.nodeName == "description":
							try:description = str(node3.firstChild.data.strip().encode("utf-8"))
							except:description = ""
							E1TimerList.append(E2Timer(servicereference = servicereference, servicename = servicename, name = name, disabled = disabled, timebegin = timebegin, timeend = timeend, duration = duration, startprepare = startprepare, state = state , repeated = repeated, justplay= justplay, eventId = eventId, afterevent = afterevent, dirname = dirname, description = description, type = type ))
	return E1TimerList

class myHTTPClientFactory(HTTPClientFactory):
	def __init__(self, url, method='GET', postdata=None, headers=None,
	agent="Twisted Remotetimer", timeout=0, cookies=None,
	followRedirect=1, lastModified=None, etag=None):
		HTTPClientFactory.__init__(self, url, method=method, postdata=postdata,
		headers=headers, agent=agent, timeout=timeout, cookies=cookies,followRedirect=followRedirect)


def sendPartnerBoxWebCommand(url, contextFactory=None, timeout=60, username = "root", password = "", *args, **kwargs):
	scheme, host, port, path = client._parse(url)
	basicAuth = encodestring(("%s:%s")%(username,password))
	authHeader = "Basic " + basicAuth.strip()
	AuthHeaders = {"Authorization": authHeader}
	if kwargs.has_key("headers"):
		kwargs["headers"].update(AuthHeaders)
	else:
		kwargs["headers"] = AuthHeaders
	factory = myHTTPClientFactory(url, *args, **kwargs)
	reactor.connectTCP(host, port, factory, timeout=timeout)
	return factory.deferred

class PlaylistEntry:

	PlaylistEntry=1			# normal PlaylistEntry (no Timerlist entry)
	SwitchTimerEntry=2		#simple service switch timer
	RecTimerEntry=4			#timer do recording
	
	recDVR=8				#timer do DVR recording
	recVCR=16				#timer do VCR recording (LIRC) not used yet
	recNgrab=131072			#timer do record via Ngrab Server

	stateWaiting=32			#timer is waiting
	stateRunning=64			#timer is running
	statePaused=128			#timer is paused
	stateFinished=256		#timer is finished
	stateError=512			#timer has error state(s)

	errorNoSpaceLeft=1024	#HDD no space Left ( recDVR )
	errorUserAborted=2048	#User Action aborts this event
	errorZapFailed=4096		#Zap to service failed
	errorOutdated=8192		#Outdated event

	boundFile=16384			#Playlistentry have an bounded file
	isSmartTimer=32768		#this is a smart timer (EIT related) not uses Yet
	isRepeating=262144		#this timer is repeating
	doFinishOnly=65536		#Finish an running event/action

	doShutdown=67108864		#timer shutdown the box
	doGoSleep=134217728		#timer set box to standby

	Su=524288
	Mo=1048576
	Tue=2097152
	Wed=4194304
	Thu=8388608
	Fr=16777216
	Sa=33554432

class RemoteTimerEntry(Screen, ConfigListScreen):
	skin = """
		<screen name="RemoteTimerEntry" position="90,95" size="560,430" title="Timer entry">
			<widget name="cancel" pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<widget name="ok" pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<widget name="canceltext" position="0,0" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" backgroundColor="#9f1313" transparent="1" />
			<widget name="oktext" position="140,0" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="10,45" size="540,385" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, timer, Locations):
		self.session = session
		Screen.__init__(self, session)
		self.timer = timer
		self.Locations = Locations
		self.entryDate = None
		self.entryService = None
		self["oktext"] = Label(_("OK"))
		self["canceltext"] = Label(_("Cancel"))
		self["ok"] = Pixmap()
		self["cancel"] = Pixmap()
		self.createConfig()
		self["actions"] = NumberActionMap(["SetupActions", "GlobalActions", "PiPSetupActions"],
		{
			"save": self.keyGo,
			"cancel": self.keyCancel,
			"volumeUp": self.incrementStart,
			"volumeDown": self.decrementStart,
			"size+": self.incrementEnd,
			"size-": self.decrementEnd
		}, -2)
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = session)
		self.createSetup("config")

	def createConfig(self):
		
		if self.timer.type == 0:
			justplay = self.timer.justplay
			afterevent = {
				0: "nothing",
				2: "deepstandby",
				1: "standby",
				3: "auto"
				}[self.timer.afterevent]
		else:
			if self.timer.type & PlaylistEntry.doShutdown:
				afterevent = PlaylistEntry.doShutdown
			elif self.timer.type & PlaylistEntry.doGoSleep:
				afterevent = PlaylistEntry.doGoSleep
			else:
				afterevent = 0
		
			if self.timer.type & PlaylistEntry.RecTimerEntry:
				if self.timer.type & PlaylistEntry.recDVR:
					justplay = PlaylistEntry.recDVR
				elif self.timer.type & PlaylistEntry.recNgrab:
					justplay = PlaylistEntry.recNgrab
			elif self.timer.type & PlaylistEntry.SwitchTimerEntry:
				justplay = PlaylistEntry.SwitchTimerEntry
		
		weekday_table = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
		day = []
		weekday = 0
		for x in (0, 1, 2, 3, 4, 5, 6):
			day.append(0)
		begin = self.timer.timebegin
		end = self.timer.timeend
		weekday = (int(strftime("%w", localtime(begin))) - 1) % 7
		day[weekday] = 1
		name = self.timer.name 
		description = self.timer.description
		if self.timer.type == 0:
			self.timerentry_justplay = ConfigSelection(choices = [("1", _("zap")), ("0", _("record"))], default = str(justplay))
			self.timerentry_afterevent = ConfigSelection(choices = [("nothing", _("do nothing")), ("standby", _("go to standby")), ("deepstandby", _("go to deep standby")), ("auto", _("auto"))], default = afterevent)
			self.timerentry_name = ConfigText(default = name, visible_width = 50, fixed_size = False)
		else:
			self.timerentry_justplay = ConfigSelection(choices = [(str(PlaylistEntry.SwitchTimerEntry), _("zap")), (str(PlaylistEntry.recNgrab), _("NGRAB")),(str(PlaylistEntry.recDVR), _("DVR"))], default = str(justplay))
			self.timerentry_afterevent = ConfigSelection(choices = [("0", _("do nothing")), (str(PlaylistEntry.doGoSleep), _("go to standby")), (str(PlaylistEntry.doShutdown), _("go to deep standby"))], default = str(afterevent))
		self.timerentry_description = ConfigText(default = description, visible_width = 50, fixed_size = False)
		self.timerentry_date = ConfigDateTime(default = begin, formatstring = _("%d.%B %Y"), increment = 86400)
		self.timerentry_starttime = ConfigClock(default = begin)
		self.timerentry_endtime = ConfigClock(default = end)
		if self.timer.type == 0:
			default = self.timer.dirname
			if default not in self.Locations:
				self.Locations.append(default)
			self.timerentry_dirname = ConfigSelection(default = default, choices = self.Locations)
		self.timerentry_weekday = ConfigSelection(default = weekday_table[weekday], choices = [("mon",_("Monday")), ("tue", _("Tuesday")), ("wed",_("Wednesday")), ("thu", _("Thursday")), ("fri", _("Friday")), ("sat", _("Saturday")), ("sun", _("Sunday"))])
		self.timerentry_day = ConfigSubList()
		for x in (0, 1, 2, 3, 4, 5, 6):
			self.timerentry_day.append(ConfigYesNo(default = day[x]))
		servicename = self.timer.servicename
		self.timerentry_service = ConfigSelection([servicename])

	def createSetup(self, widget):
		self.list = []
		if self.timer.type == 0:
			self.list.append(getConfigListEntry(_("Name"), self.timerentry_name))
		self.list.append(getConfigListEntry(_("Description"), self.timerentry_description))
		self.timerJustplayEntry = getConfigListEntry(_("Timer Type"), self.timerentry_justplay)
		self.list.append(self.timerJustplayEntry)
		self.entryDate = getConfigListEntry(_("Date"), self.timerentry_date)
		self.list.append(self.entryDate)
		self.entryStartTime = getConfigListEntry(_("StartTime"), self.timerentry_starttime)
		self.list.append(self.entryStartTime)
		if self.timer.type == 0:
			if int(self.timerentry_justplay.value) != 1:
				self.entryEndTime = getConfigListEntry(_("EndTime"), self.timerentry_endtime)
				self.list.append(self.entryEndTime)
			else:
				self.entryEndTime = None
		else:
			self.entryEndTime = getConfigListEntry(_("EndTime"), self.timerentry_endtime)
			self.list.append(self.entryEndTime)
		self.channelEntry = getConfigListEntry(_("Channel"), self.timerentry_service)
		self.list.append(self.channelEntry)
		if self.timer.type == 0:
			self.dirname = getConfigListEntry(_("Location"), self.timerentry_dirname)
			if int(self.timerentry_justplay.value) != 1:
				self.list.append(self.dirname)
				self.list.append(getConfigListEntry(_("After event"), self.timerentry_afterevent))
		else:
			self.list.append(getConfigListEntry(_("After event"), self.timerentry_afterevent))
		self[widget].list = self.list
		self[widget].l.setList(self.list)
		
	def newConfig(self):
		if self["config"].getCurrent() == self.timerJustplayEntry:
			self.createSetup("config")
			
	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()
		
	def getTimestamp(self, date, mytime):
		d = localtime(date)
		dt = datetime(d.tm_year, d.tm_mon, d.tm_mday, mytime[0], mytime[1])
		return int(mktime(dt.timetuple()))

	def getBeginEnd(self):
		date = self.timerentry_date.value
		endtime = self.timerentry_endtime.value
		starttime = self.timerentry_starttime.value
		begin = self.getTimestamp(date, starttime)
		end = self.getTimestamp(date, endtime)
		if end < begin:
			end += 86400
		return begin, end

	def keyCancel(self):
		self.close((False,))
		
	def keyGo(self):
		if self.timer.type == 0:
			self.timer.name = self.timerentry_name.value
			self.timer.dirname = self.timerentry_dirname.value
			self.timer.afterevent = {
			"nothing": 0,
			"deepstandby": 2,
			"standby": 1,
			"auto": 3
			}[self.timerentry_afterevent.value]
		else:
			self.timer.afterevent = int(self.timerentry_afterevent.value)
		self.timer.description = self.timerentry_description.value
		self.timer.justplay = int(self.timerentry_justplay.value)
		
		self.timer.timebegin, self.timer.timeend = self.getBeginEnd()
		self.close((True, self.timer))

	def incrementStart(self):
		self.timerentry_starttime.increment()
		self["config"].invalidate(self.entryStartTime)

	def decrementStart(self):
		self.timerentry_starttime.decrement()
		self["config"].invalidate(self.entryStartTime)

	def incrementEnd(self):
		if self.entryEndTime is not None:
			self.timerentry_endtime.increment()
			self["config"].invalidate(self.entryEndTime)

	def decrementEnd(self):
		if self.entryEndTime is not None:
			self.timerentry_endtime.decrement()
			self["config"].invalidate(self.entryEndTime)
			
			
			
# ##########################################
# TimerEntry
# ##########################################
baseTimerEntrySetup = None
baseTimerEntryGo = None
baseTimerEntrynewConfig = None
baseTimerkeyLeft = None
baseTimerkeyRight = None
baseTimerkeySelect = None
baseTimercreateConfig = None

def RemoteTimerInit():
	global baseTimerEntrySetup, baseTimerEntryGo, baseTimerEntrynewConfig, baseTimerkeyLeft, baseTimerkeyRight, baseTimerkeySelect, baseTimercreateConfig
	if baseTimerEntrySetup is None:
		baseTimerEntrySetup = TimerEntry.createSetup
	if baseTimerEntryGo is None:
		baseTimerEntryGo = TimerEntry.keyGo
	if baseTimerEntrynewConfig is None:
		baseTimerEntrynewConfig = TimerEntry.newConfig
	if baseTimerkeyLeft is None:
		baseTimerkeyLeft = TimerEntry.keyLeft
	if baseTimerkeyRight is None:
		baseTimerkeyRight = TimerEntry.keyRight
	if baseTimerkeySelect is None:
		baseTimerkeySelect = TimerEntry.keySelect
	if baseTimercreateConfig is None:
		baseTimercreateConfig  = TimerEntry.createConfig
	
	TimerEntry.createConfig = RemoteTimerConfig
	TimerEntry.keyLeft = RemoteTimerkeyLeft 
	TimerEntry.keyRight = RemoteTimerkeyRight
	TimerEntry.keySelect = RemoteTimerkeySelect
	TimerEntry.createSetup = createRemoteTimerSetup
	TimerEntry.keyGo = RemoteTimerGo
	TimerEntry.newConfig = RemoteTimernewConfig
	
def RemoteTimerConfig(self):
	self.Locations = []
	self.entryguilist = []
	self.entryguilist.append(("0",_("Nein"),None))
	index = 1
	for c in config.plugins.Partnerbox.Entries:
		self.entryguilist.append((str(index),str(c.name.value),c))
		index = index + 1
	self.timerentry_remote = ConfigSelection(default = "0", choices = self.entryguilist)
	baseTimercreateConfig(self)

#def getLocationsError(self, error):
#	RemoteTimercreateConfig(self)
#	RemoteTimerCreateSetup(self,"config")
	
def getLocationsCallback(self, xmlstring):
	self.Locations = []
	dom = xml.dom.minidom.parseString(xmlstring)
	for node in dom.firstChild.childNodes:
		dirname = ""
		if node.nodeName == "e2simplexmlitem" or node.nodeName == "e2location": # vorerst Kompatibilitaet zum alten Webinterface-Api aufrecht erhalten (e2simplexmlitem)
			dirname = str(node.firstChild.data.strip().encode("utf-8"))
			self.Locations.append(dirname)
		
def createRemoteTimerSetup(self, widget):
	baseTimerEntrySetup(self, widget)
	self.display = _("Remote Timer")
	self.timerRemoteEntry = getConfigListEntry(self.display, self.timerentry_remote)
	self.list.insert(0, self.timerRemoteEntry)
	self[widget].list = self.list
	
def RemoteTimerkeyLeft(self):
	if int(self.timerentry_remote.value) != 0:
		ConfigListScreen.keyLeft(self)
		RemoteTimernewConfig(self)
	else:
		baseTimerkeyLeft(self)

def RemoteTimerkeyRight(self):
	if int(self.timerentry_remote.value) != 0:
		ConfigListScreen.keyRight(self)
		RemoteTimernewConfig(self)
	else:
		baseTimerkeyRight(self)

def RemoteTimerkeySelect(self):
	if int(self.timerentry_remote.value) != 0:
		RemoteTimerGo(self)
	else:
		baseTimerkeySelect(self)
	
	
def RemoteTimernewConfig(self):
	if self["config"].getCurrent() == self.timerRemoteEntry:
		if int(self.timerentry_remote.value) != 0:
			if int(self.entryguilist[int(self.timerentry_remote.value)][2].enigma.value) == 1: # E1
				self.timertype = PlaylistEntry.RecTimerEntry|PlaylistEntry.recDVR
			else: # E2
				self.timertype = 0
				ip = "%d.%d.%d.%d" % tuple(self.entryguilist[int(self.timerentry_remote.value)][2].ip.value)
				port = self.entryguilist[int(self.timerentry_remote.value)][2].port.value
				http_ = "%s:%d" % (ip,port)
				sCommand = "http://root:" + self.entryguilist[int(self.timerentry_remote.value)][2].password.value + "@" + http_ + "/web/getlocations"
				#sCommand = self.http + "/web/getlocations"
				#sendPartnerBoxWebCommand(sCommand, None,3, self.username, self.password).addCallback(boundFunction(getLocationsCallback,self)).addErrback(boundFunction(getLocationsError,self))
				# ich mach das besser synchron, falls die Partnerbox aus ist ( dann koennte man hier schon abbrechen und eine Meldung bringen...)
				try:
					f = urllib.urlopen(sCommand)
					sxml = f.read()
					getLocationsCallback(self,sxml)
				except: pass
			RemoteTimercreateConfig(self)
			RemoteTimerCreateSetup(self,"config")
		else:
			baseTimercreateConfig(self)
			createRemoteTimerSetup(self, "config")
	elif self["config"].getCurrent() == self.timerJustplayEntry:
		if int(self.timerentry_remote.value) != 0:
			RemoteTimerCreateSetup(self,"config")
		else:
			baseTimerEntrynewConfig(self)
	else:
			if int(self.timerentry_remote.value) == 0:
				baseTimerEntrynewConfig(self)
	
def  RemoteTimercreateConfig(self):
	if int(self.entryguilist[int(self.timerentry_remote.value)][2].enigma.value) == 0:
		justplay = self.timer.justplay
		afterevent = {
			AFTEREVENT.NONE: "nothing",
			AFTEREVENT.DEEPSTANDBY: "deepstandby",
			 AFTEREVENT.STANDBY: "standby",
			 AFTEREVENT.AUTO: "auto"
			}[self.timer.afterEvent]
	else:
		if self.timertype & PlaylistEntry.doShutdown:
			afterevent = PlaylistEntry.doShutdown
		elif self.timertype & PlaylistEntry.doGoSleep:
			afterevent = PlaylistEntry.doGoSleep
		else:
			afterevent = 0
		if self.timertype & PlaylistEntry.RecTimerEntry:
			if self.timertype & PlaylistEntry.recDVR:
				justplay = PlaylistEntry.recDVR
			elif self.timertype & PlaylistEntry.recNgrab:
				justplay = PlaylistEntry.recNgrab
		elif self.timertype & PlaylistEntry.SwitchTimerEntry:
			justplay = PlaylistEntry.SwitchTimerEntry
	weekday_table = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
	day = []
	weekday = 0
	for x in (0, 1, 2, 3, 4, 5, 6):
		day.append(0)
	begin = self.timer.begin
	end = self.timer.end
	weekday = (int(strftime("%w", localtime(begin))) - 1) % 7
	day[weekday] = 1
	if int(self.entryguilist[int(self.timerentry_remote.value)][2].enigma.value) == 0:
		name = self.timer.name 
		description = self.timer.description
		self.timerentry_justplay = ConfigSelection(choices = [("zap", _("zap")), ("record", _("record"))], default = {0: "record", 1: "zap"}[justplay])
		self.timerentry_afterevent = ConfigSelection(choices = [("nothing", _("do nothing")), ("standby", _("go to standby")), ("deepstandby", _("go to deep standby")), ("auto", _("auto"))], default = afterevent)
		self.timerentry_name = ConfigText(default = name, visible_width = 50, fixed_size = False)
	else:
		description = self.timer.name 
		self.timerentry_justplay = ConfigSelection(choices = [(str(PlaylistEntry.SwitchTimerEntry), _("zap")), (str(PlaylistEntry.recNgrab), _("NGRAB")),(str(PlaylistEntry.recDVR), _("DVR"))], default = str(justplay))
		self.timerentry_afterevent = ConfigSelection(choices = [("0", _("do nothing")), (str(PlaylistEntry.doGoSleep), _("go to standby")), (str(PlaylistEntry.doShutdown), _("go to deep standby"))], default = str(afterevent))
	self.timerentry_description = ConfigText(default = description, visible_width = 50, fixed_size = False)
	self.timerentry_date = ConfigDateTime(default = begin, formatstring = _("%d.%B %Y"), increment = 86400)
	self.timerentry_starttime = ConfigClock(default = begin)
	self.timerentry_endtime = ConfigClock(default = end)
	if int(self.entryguilist[int(self.timerentry_remote.value)][2].enigma.value) == 0:
		default = "/hdd/movie/"
		if default not in self.Locations:
			self.Locations.append(default)
		self.timerentry_dirname = ConfigSelection(default = default, choices = self.Locations)
	self.timerentry_weekday = ConfigSelection(default = weekday_table[weekday], choices = [("mon",_("Monday")), ("tue", _("Tuesday")), ("wed",_("Wednesday")), ("thu", _("Thursday")), ("fri", _("Friday")), ("sat", _("Saturday")), ("sun", _("Sunday"))])
	self.timerentry_day = ConfigSubList()
	for x in (0, 1, 2, 3, 4, 5, 6):
		self.timerentry_day.append(ConfigYesNo(default = day[x]))
	# FIXME some service-chooser needed here
	servicename = "N/A"
	try: # no current service available?
		servicename = str(self.timer.service_ref.getServiceName())
	except:
		pass
	self.timerentry_service_ref = self.timer.service_ref
	self.timerentry_service = ConfigSelection([servicename])

def RemoteTimerCreateSetup(self, widget):
	self.list = []
	self.timerRemoteEntry = getConfigListEntry(self.display, self.timerentry_remote)
	self.list.append(self.timerRemoteEntry)
	if int(self.entryguilist[int(self.timerentry_remote.value)][2].enigma.value) == 0:
		self.list.append(getConfigListEntry(_("Name"), self.timerentry_name))
	self.list.append(getConfigListEntry(_("Description"), self.timerentry_description))
	self.timerJustplayEntry = getConfigListEntry(_("Timer Type"), self.timerentry_justplay)
	self.list.append(self.timerJustplayEntry)
	self.entryDate = getConfigListEntry(_("Date"), self.timerentry_date)
	self.list.append(self.entryDate)
	self.entryStartTime = getConfigListEntry(_("StartTime"), self.timerentry_starttime)
	self.list.append(self.entryStartTime)
	if int(self.entryguilist[int(self.timerentry_remote.value)][2].enigma.value) == 0:
		if self.timerentry_justplay.value != "zap":
			self.entryEndTime = getConfigListEntry(_("EndTime"), self.timerentry_endtime)
			self.list.append(self.entryEndTime)
		else:
			self.entryEndTime = None
	else:
		self.entryEndTime = getConfigListEntry(_("EndTime"), self.timerentry_endtime)
		self.list.append(self.entryEndTime)
	self.channelEntry = getConfigListEntry(_("Channel"), self.timerentry_service)
	self.list.append(self.channelEntry)
	if int(self.entryguilist[int(self.timerentry_remote.value)][2].enigma.value) == 0:
		self.dirname = getConfigListEntry(_("Location"), self.timerentry_dirname)
		if self.timerentry_justplay.value != "zap":
			self.list.append(self.dirname)
			self.list.append(getConfigListEntry(_("After event"), self.timerentry_afterevent))
	else:
		self.list.append(getConfigListEntry(_("After event"), self.timerentry_afterevent))
	self[widget].list = self.list
	self[widget].l.setList(self.list)

def RemoteTimerGo(self):
	if int(self.timerentry_remote.value) == 0:
		baseTimerEntryGo(self)
	else:
		service_ref = self.timerentry_service_ref
		descr = urllib.quote(self.timerentry_description.value)
		begin, end = self.getBeginEnd()
		ip = "%d.%d.%d.%d" % tuple(self.entryguilist[int(self.timerentry_remote.value)][2].ip.value)
		port = self.entryguilist[int(self.timerentry_remote.value)][2].port.value
		http = "http://%s:%d" % (ip,port)
		if int(self.entryguilist[int(self.timerentry_remote.value)][2].enigma.value) == 1:
			# E1
			afterevent = self.timerentry_afterevent.value
			justplay = int(self.timerentry_justplay.value)
			if justplay & PlaylistEntry.SwitchTimerEntry:
				action = "zap"
			elif justplay & PlaylistEntry.recNgrab:
				action = "ngrab"
			else:
				action = ""
			# FIXME some service-chooser needed here
			servicename = "N/A"
			try: # no current service available?
				servicename = str(service_ref .getServiceName())
			except:
				pass
			channel = urllib.quote(servicename)
			sCommand = "%s/addTimerEvent?ref=%s&start=%d&duration=%d&descr=%s&channel=%s&after_event=%s&action=%s" % (http, service_ref , begin, end - begin, descr, channel, afterevent, action)
			sendPartnerBoxWebCommand(sCommand, None,3, "root", str(self.entryguilist[int(self.timerentry_remote.value)][2].password.value)).addCallback(boundFunction(AddTimerE1Callback,self, self.session)).addErrback(boundFunction(AddTimerError,self, self.session))
		else:
			# E2
			name = urllib.quote(self.timerentry_name.value)
			self.timer.tags = self.timerentry_tags
			if self.timerentry_justplay.value == "zap":
				justplay = 1
				dirname = ""
			else:
				justplay = 0
				dirname = urllib.quote(self.timerentry_dirname.value)
			afterevent = {
			"deepstandby": AFTEREVENT.DEEPSTANDBY,
			"standby": AFTEREVENT.STANDBY,
			}.get(self.timerentry_afterevent.value, AFTEREVENT.NONE)
			sCommand = "%s/web/timeradd?sRef=%s&begin=%d&end=%d&name=%s&description=%s&dirname=%s&eit=0&justplay=%d&afterevent=%s" % (http, service_ref,begin,end,name,descr,dirname,justplay,afterevent)
			sendPartnerBoxWebCommand(sCommand, None,3, "root", str(self.entryguilist[int(self.timerentry_remote.value)][2].password.value)).addCallback(boundFunction(AddTimerE2Callback,self, self.session)).addErrback(boundFunction(AddTimerError,self,self.session))

def AddTimerE2Callback(self, session, answer):
	text = ""
	dom = xml.dom.minidom.parseString(answer)
	for node in dom.firstChild.childNodes:
		dirname = ""
		if node.nodeName == "e2statetext":
			text = str(node.firstChild.data.strip().encode("utf-8"))
	ok = text == "Timer added successfully!"
	session.open(MessageBox,_("Partnerbox Answer: \n%s") % (text),MessageBox.TYPE_INFO, timeout = 3)
	if ok:
		if (int(self.timerentry_remote.value) == 1 and config.plugins.Partnerbox.enablepartnerboxepglist.value): # nur, wenn Partnerbox1 gewaehlt wurde
			# Timerlist der Partnerbox neu laden --> Anzeige fuer EPGList
			global remote_timer_list
			remote_timer_list = [] 
			password = self.entryguilist[int(self.timerentry_remote.value)][2].password.value
			username = "root"
			ip = "%d.%d.%d.%d" % tuple(self.entryguilist[int(self.timerentry_remote.value)][2].ip.value)
			port = self.entryguilist[int(self.timerentry_remote.value)][2].port.value
			sCommand = "http://%s:%s@%s:%d/web/timerlist" % (username, password, ip,port)
			print "[RemoteTimer] Getting timerlist data from %s..."%ip
			try:
				f = urllib.urlopen(sCommand)
				sxml = f.read()
				remote_timer_list = FillE2TimerList(sxml)
			except: pass
		self.keyCancel()

def AddTimerE1Callback(self, session, answer):
	ok = answer == "Timer event was created successfully."
	session.open(MessageBox,_("Partnerbox Answer: \n%s") % (answer),MessageBox.TYPE_INFO, timeout = 3)
	if ok:
		
		if (int(self.timerentry_remote.value) == 1 and config.plugins.Partnerbox.enablepartnerboxepglist.value): # nur, wenn Partnerbox1 gewaehlt wurde
			# Timerlist der Partnerbox neu laden --> Anzeige fuer EPGList
			global remote_timer_list
			remote_timer_list = []
			password = self.entryguilist[int(self.timerentry_remote.value)][2].password.value
			username = "root"
			ip = "%d.%d.%d.%d" % tuple(self.entryguilist[int(self.timerentry_remote.value)][2].ip.value)
			port = self.entryguilist[int(self.timerentry_remote.value)][2].port.value
			sCommand = "http://%s:%s@%s:%d/xml/timers" % (username, password, ip,port)
			print "[RemoteTimer] Getting timerlist data from %s..."%ip
			try:
				f = urllib.urlopen(sCommand)
				sxml = f.read()
				remote_timer_list = FillE1TimerList(sxml)
			except: pass
		self.keyCancel()
		
def AddTimerError(self, session, error):
	session.open(MessageBox,str(error.getErrorMessage()),MessageBox.TYPE_INFO)
	


# ##########################################
# EPGList
# ##########################################
baseEPGList__init__ = None
basebuildSingleEntry = None
basebuildSimilarEntry = None
basebuildMultiEntry = None

def Partnerbox_EPGListInit():
	global baseEPGList__init__, basebuildSingleEntry, basebuildSimilarEntry, basebuildMultiEntry, remote_timer_list
	if baseEPGList__init__ is None:
		baseEPGList__init__ = EPGList.__init__
	if basebuildSingleEntry is None:
		basebuildSingleEntry = EPGList.buildSingleEntry
	if basebuildSimilarEntry is None:
		basebuildSimilarEntry = EPGList.buildSimilarEntry
	if basebuildMultiEntry is None:
		basebuildMultiEntry = EPGList.buildMultiEntry
	if remote_timer_list is None:
		remote_timer_list = []
	EPGList.__init__ = Partnerbox_EPGList__init__
	EPGList.buildSingleEntry = Partnerbox_SingleEntry
	EPGList.buildSimilarEntry = Partnerbox_SimilarEntry
	EPGList.buildMultiEntry = Partnerbox_MultiEntry

def Partnerbox_EPGList__init__(self, type=0, selChangedCB=None, timer = None):
	global remote_timer_list
	remote_timer_list = []
	if int(config.plugins.Partnerbox.entriescount.value) >= 1:
		try:
			partnerboxentry = config.plugins.Partnerbox.Entries[0]
			password = partnerboxentry.password.value
			username = "root"
			ip = "%d.%d.%d.%d" % tuple(partnerboxentry.ip.value)
			port = partnerboxentry.port.value
			if int(partnerboxentry.enigma.value) == 0:
				sCommand = "http://%s:%s@%s:%d/web/timerlist" % (username, password, ip,port)
			else:
				sCommand = "http://%s:%s@%s:%d/xml/timers" % (username, password, ip,port)
			print "[RemoteEPGList] Getting timerlist data from %s..."%ip
			f = urllib.urlopen(sCommand)
			sxml = f.read()
			if int(partnerboxentry.enigma.value) == 0:
				remote_timer_list = FillE2TimerList(sxml)
			else:
				remote_timer_list = FillE1TimerList(sxml)
		except: pass
	# Partnerbox Clock Icons
	self.remote_clock_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock.png')
	self.remote_clock_add_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_add.png')
	self.remote_clock_pre_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_pre.png')
	self.remote_clock_post_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_post.png')
	self.remote_clock_prepost_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_prepost.png')
	baseEPGList__init__(self, type, selChangedCB, timer)

def Partnerbox_SingleEntry(self, service, eventId, beginTime, duration, EventName):
	rec1=beginTime and (self.timer.isInTimer(eventId, beginTime, duration, service))
	rec2=beginTime and (isInRemoteTimer(self,beginTime, duration, service))
	r1=self.weekday_rect
	r2=self.datetime_rect
	r3=self.descr_rect
	t = localtime(beginTime)
	res = [
		None, # no private data needed
		(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_RIGHT, self.days[t[6]]),
		(eListboxPythonMultiContent.TYPE_TEXT, r2.left(), r2.top(), r2.width(), r1.height(), 0, RT_HALIGN_RIGHT, "%02d.%02d, %02d:%02d"%(t[2],t[1],t[3],t[4]))
	]
	if rec1 or rec2:
		if rec1:			
			clock_pic = self.getClockPixmap(service, beginTime, duration, eventId)
			#eventuell auch in der Partnerbox
			if rec2:
				clock_pic_partnerbox = getRemoteClockPixmap(self,service, beginTime, duration, eventId)
		else:
			clock_pic = getRemoteClockPixmap(self,service, beginTime, duration, eventId)
		if rec1 and rec2:
			# wenn sowohl lokal als auch auf Partnerbox
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left(), r3.top(), 21, 21, clock_pic),
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + 25, r3.top(), 21, 21, clock_pic_partnerbox),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.left() + 50, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, EventName)))
		else:
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left(), r3.top(), 21, 21, clock_pic),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.left() + 25, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, EventName)))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, EventName))
	return res


def Partnerbox_SimilarEntry(self, service, eventId, beginTime, service_name, duration):
	rec1=beginTime and (self.timer.isInTimer(eventId, beginTime, duration, service))
	rec2=beginTime and (isInRemoteTimer(self,beginTime, duration, service))
	r1=self.weekday_rect
	r2=self.datetime_rect
	r3=self.service_rect
	t = localtime(beginTime)
	res = [
		None,  # no private data needed
		(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_RIGHT, self.days[t[6]]),
		(eListboxPythonMultiContent.TYPE_TEXT, r2.left(), r2.top(), r2.width(), r1.height(), 0, RT_HALIGN_RIGHT, "%02d.%02d, %02d:%02d"%(t[2],t[1],t[3],t[4]))
	]
	if rec1 or rec2:
		if rec1:			
			clock_pic = self.getClockPixmap(service, beginTime, duration, eventId)
			#eventuell auch in der Partnerbox
			if rec2:
				clock_pic_partnerbox = getRemoteClockPixmap(self,service, beginTime, duration, eventId)
		else:
			clock_pic = getRemoteClockPixmap(self,service, beginTime, duration, eventId)
		if rec1 and rec2:
			# wenn sowohl lokal als auch auf Partnerbox
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left(), r3.top(), 21, 21, clock_pic),
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + 25, r3.top(), 21, 21, clock_pic_partnerbox),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.left() + 50, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, service_name)
			))
		else:
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left(), r3.top(), 21, 21, clock_pic),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.left() + 25, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, service_name)
			))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, service_name))
	return res

def Partnerbox_MultiEntry(self, changecount, service, eventId, begTime, duration, EventName, nowTime, service_name):
	# so wie es aussieht wird der MultiEPG ueber ein Plugin angefahren...lasse den Code dennoch mal drinnen...
	rec1=begTime and (self.timer.isInTimer(eventId, begTime, duration, service))
	rec2=begTime and (isInRemoteTimer(self,begTime, duration, service))
	r1=self.service_rect
	r2=self.progress_rect
	r3=self.descr_rect
	r4=self.start_end_rect
	res = [ None ] # no private data needed
	if rec1 or rec2:
		if rec1:			
			clock_pic = self.getClockPixmap(service, begTime, duration, eventId)
			#eventuell auch in der Partnerbox
			if rec2:
				clock_pic_partnerbox = getRemoteClockPixmap(self,service, begTime, duration, eventId)
		else:
			clock_pic = getRemoteClockPixmap(self,service, begTime, duration, eventId)
		if rec1 and rec2:
			# wenn sowohl lokal als auch auf Partnerbox
			res.extend((
				(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width()-41, r1.height(), 0, RT_HALIGN_LEFT, service_name),
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r1.left()+r1.width()-32, r1.top(), 21, 21, clock_pic),
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r1.left()+r1.width()-16, r1.top(), 21, 21, clock_pic_partnerbox)
			))
		else:
			res.extend((
				(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width()-21, r1.height(), 0, RT_HALIGN_LEFT, service_name),
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r1.left()+r1.width()-16, r1.top(), 21, 21, clock_pic)
			))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_LEFT, service_name))
	if begTime is not None:
		if nowTime < begTime:
			begin = localtime(begTime)
			end = localtime(begTime+duration)
			res.extend((
				(eListboxPythonMultiContent.TYPE_TEXT, r4.left(), r4.top(), r4.width(), r4.height(), 1, RT_HALIGN_CENTER|RT_VALIGN_CENTER, "%02d.%02d - %02d.%02d"%(begin[3],begin[4],end[3],end[4])),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, EventName)
			))
		else:
			percent = (nowTime - begTime) * 100 / duration
			res.extend((
				(eListboxPythonMultiContent.TYPE_PROGRESS, r2.left(), r2.top(), r2.width(), r2.height(), percent),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, EventName)
			))
	return res



def isInRemoteTimer(self, begin, duration, service):
	global remote_timer_list
	time_match = 0
	chktime = None
	chktimecmp = None
	chktimecmp_end = None
	end = begin + duration
	for x in remote_timer_list:
		print "------------>begin = %d,  x.timebegin = %d, end = %d" % (begin, x.timebegin, end)
		print "------------>service = %s, x.servicereference = %s" % (service, x.servicereference)
		if x.servicereference.upper() == service.upper():
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


def getRemoteClockPixmap(self, refstr, beginTime, duration, eventId):
	global remote_timer_list
	pre_clock = 1
	post_clock = 2
	clock_type = 0
	endTime = beginTime + duration
	for x in remote_timer_list:
		if x.servicereference.upper() == refstr.upper():
			if x.eventId == eventId:
				return self.remote_clock_pixmap
			beg = x.timebegin
			end = x.timeend
			if beginTime > beg and beginTime < end and endTime > end:
				clock_type |= pre_clock
			elif beginTime < beg and endTime > beg and endTime < end:
				clock_type |= post_clock
	if clock_type == 0:
		return self.remote_clock_add_pixmap
	elif clock_type == pre_clock:
		return self.remote_clock_pre_pixmap
	elif clock_type == post_clock:
		return self.remote_clock_post_pixmap
	else:
		return self.remote_clock_prepost_pixmap
