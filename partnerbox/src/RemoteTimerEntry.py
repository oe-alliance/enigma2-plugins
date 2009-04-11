#
#  Partnerbox E2
#  Release: 0.93
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
baseTimercreateConfig = None

def RemoteTimerInit():
	global baseTimerEntrySetup, baseTimerEntryGo, baseTimerEntrynewConfig, baseTimerkeyLeft, baseTimerkeyRight, baseTimercreateConfig
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
	if baseTimercreateConfig is None:
		baseTimercreateConfig  = TimerEntry.createConfig
	
	TimerEntry.createConfig = RemoteTimerCreateConfig
	TimerEntry.keyLeft = RemoteTimerkeyLeft 
	TimerEntry.keyRight = RemoteTimerkeyRight
	TimerEntry.createSetup = createRemoteTimerSetup
	TimerEntry.keyGo = RemoteTimerGo
	TimerEntry.newConfig = RemoteTimernewConfig
	
def RemoteTimerCreateConfig(self):
	
	self.password = config.plugins.partnerbox.password.value
	self.username = "root"
	self.ip = "%d.%d.%d.%d" % tuple(config.plugins.partnerbox.ip.value)
	port = config.plugins.partnerbox.port.value
	self.http = "http://%s:%d" % (self.ip,port)
	self.Locations = []
	self.enigmatype = int(config.plugins.partnerbox.enigma.value) # E2 = 0 | E1 = 1
	self.timerentry_remote = ConfigYesNo()
	baseTimercreateConfig(self)

#def getLocationsError(self, error):
#	RemoteTimercreateConfig(self)
#	RemoteTimerCreateSetup(self,"config")
	
def getLocationsCallback(self, xmlstring):
	self.Locations = []
	dom = xml.dom.minidom.parseString(xmlstring)
	for node in dom.firstChild.childNodes:
		dirname = ""
		if node.nodeName == "e2simplexmlitem":
			dirname = str(node.firstChild.data.strip().encode("utf-8"))
			self.Locations.append(dirname)
	RemoteTimercreateConfig(self)
	RemoteTimerCreateSetup(self,"config")
		
def createRemoteTimerSetup(self, widget):
	baseTimerEntrySetup(self, widget)
	self.display = _("Remote Timer (%s)") % (self.ip)
	self.timerRemoteEntry = getConfigListEntry(self.display, self.timerentry_remote)
	self.list.insert(0, self.timerRemoteEntry)
	self[widget].list = self.list
	
def RemoteTimerkeyLeft(self):
	if self.timerentry_remote.value:
		ConfigListScreen.keyLeft(self)
		RemoteTimernewConfig(self)
	else:
		baseTimerkeyLeft(self)

def RemoteTimerkeyRight(self):
	if self.timerentry_remote.value:
		ConfigListScreen.keyRight(self)
		RemoteTimernewConfig(self)
	else:
		baseTimerkeyRight(self)
	
def RemoteTimernewConfig(self):
	if self["config"].getCurrent() == self.timerRemoteEntry:
		if self.timerentry_remote.value:
			if self.enigmatype == 1: # E1
				self.timertype = PlaylistEntry.RecTimerEntry|PlaylistEntry.recDVR
			else: # E2
				self.timertype = 0
				sCommand = "http://" + self.username + ":" + self.password + "@" + self.ip + "/web/getlocations"
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
		if self.timerentry_remote.value:
			RemoteTimerCreateSetup(self,"config")
		else:
			baseTimerEntrynewConfig(self)
	else:
			if not self.timerentry_remote.value:
				baseTimerEntrynewConfig(self)
	
def  RemoteTimercreateConfig(self):
	if self.enigmatype == 0:
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
	if self.enigmatype == 0:
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
	if self.enigmatype == 0:
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
	if self.enigmatype == 0:
		self.list.append(getConfigListEntry(_("Name"), self.timerentry_name))
	self.list.append(getConfigListEntry(_("Description"), self.timerentry_description))
	self.timerJustplayEntry = getConfigListEntry(_("Timer Type"), self.timerentry_justplay)
	self.list.append(self.timerJustplayEntry)
	self.entryDate = getConfigListEntry(_("Date"), self.timerentry_date)
	self.list.append(self.entryDate)
	self.entryStartTime = getConfigListEntry(_("StartTime"), self.timerentry_starttime)
	self.list.append(self.entryStartTime)
	if self.enigmatype == 0:
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
	if self.enigmatype == 0:
		self.dirname = getConfigListEntry(_("Location"), self.timerentry_dirname)
		if self.timerentry_justplay.value != "zap":
			self.list.append(self.dirname)
			self.list.append(getConfigListEntry(_("After event"), self.timerentry_afterevent))
	else:
		self.list.append(getConfigListEntry(_("After event"), self.timerentry_afterevent))
	self[widget].list = self.list
	self[widget].l.setList(self.list)

def RemoteTimerGo(self):
	if not self.timerentry_remote.value:
		baseTimerEntryGo(self)
	else:
		service_ref = self.timerentry_service_ref
		descr = urllib.quote(self.timerentry_description.value)
		begin, end = self.getBeginEnd()
		if self.enigmatype == 1:
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
			sCommand = "%s/addTimerEvent?ref=%s&start=%d&duration=%d&descr=%s&channel=%s&after_event=%s&action=%s" % (self.http, service_ref , begin, end - begin, descr, channel, afterevent, action)
			sendPartnerBoxWebCommand(sCommand, None,3, self.username, self.password).addCallback(boundFunction(AddTimerE1Callback,self, self.session)).addErrback(boundFunction(AddTimerError,self, self.session))
		else:
			# E2
			name = urllib.quote(self.timerentry_name.value)
			self.timer.tags = self.timerentry_tags
			if self.timerentry_justplay.value == "zap":
				justplay = 1
				dirname = ""
			else:
				justplay = 0
				dirname = self.timerentry_dirname.value
			afterevent = {
			"deepstandby": AFTEREVENT.DEEPSTANDBY,
			"standby": AFTEREVENT.STANDBY,
			}.get(self.timerentry_afterevent.value, AFTEREVENT.NONE)
			sCommand = "%s/web/timeradd?sRef=%s&begin=%d&end=%d&name=%s&description=%s&dirname=%s&eit=0&justplay=%d&afterevent=%s" % (self.http, service_ref,begin,end,name,descr,dirname,justplay,afterevent)
			sendPartnerBoxWebCommand(sCommand, None,3, self.username, self.password).addCallback(boundFunction(AddTimerE2Callback,self, self.session)).addErrback(boundFunction(AddTimerError,self,self.session))

def AddTimerE2Callback(self, session, answer):
	text = ""
	dom = xml.dom.minidom.parseString(answer)
	for node in dom.firstChild.childNodes:
		dirname = ""
		if node.nodeName == "e2statetext":
			text = str(node.firstChild.data.strip().encode("utf-8"))
	ok = text == "Timer added successfully!"
	session.open(MessageBox,_("Partnerbox Answer: \n%s") % (text),MessageBox.TYPE_INFO)
	if ok:
		self.keyCancel()

def AddTimerE1Callback(self, session, answer):
	ok = answer == "Timer event was created successfully."
	session.open(MessageBox,_("Partnerbox Answer: \n%s") % (answer),MessageBox.TYPE_INFO)
	if ok:
		self.keyCancel()
		
def AddTimerError(self, session, error):
	session.open(MessageBox,str(error.getErrorMessage()),MessageBox.TYPE_INFO)
	