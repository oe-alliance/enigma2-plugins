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

# for localized messages
from . import _
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
from enigma import eEPGCache, getDesktop
from time import localtime, mktime, time, strftime
from datetime import datetime
from Screens.TimerEntry import TimerEntry
from Screens.MessageBox import MessageBox
from Tools.BoundFunction import boundFunction
import urllib

import xml.etree.cElementTree
from Components.ActionMap import ActionMap

from PartnerboxFunctions import PlaylistEntry, SetPartnerboxTimerlist, sendPartnerBoxWebCommand, getServiceRef
import PartnerboxFunctions as partnerboxfunctions

HD = False
try:
	sz_w = getDesktop(0).size().width()
	if sz_w >= 1280:
		HD = True
except:
	pass
class RemoteTimerEntry(Screen, ConfigListScreen):
	if HD:
		skin = """
			<screen name="RemoteTimerEntry" position="center,center" size="760,430" title="Timer entry">
				<widget name="cancel" pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
				<widget name="ok" pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
				<widget name="canceltext" position="0,0" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" backgroundColor="#9f1313" transparent="1" />
				<widget name="oktext" position="140,0" zPosition="2" size="140,40" halign="center" valign="center" font="Regular;21" backgroundColor="#1f771f" transparent="1" />
				<widget name="config" position="10,45" size="740,385" scrollbarMode="showOnDemand" />
			</screen>"""
	else:
		skin = """
			<screen name="RemoteTimerEntry" position="center,center" size="560,430" title="Timer entry">
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
		self.setTitle(_("Timer entry"))
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
				afterevent = 3
		
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
			if default == "None":
				if self.Locations:
					default = self.Locations[0]
				else:
					default = "N/A"
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
			if self.timerentry_dirname.value == "N/A" or self.timerentry_dirname.value == "None":
				self.session.open(MessageBox,_("Timer can not be added...no locations on partnerbox available."),MessageBox.TYPE_INFO)
				return
			else:
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
baseTimer__init__ = None

def RemoteTimerInit():
	global baseTimerEntrySetup, baseTimerEntryGo, baseTimerEntrynewConfig, baseTimerkeyLeft, baseTimerkeyRight, baseTimerkeySelect, baseTimercreateConfig, baseTimer__init__
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
	if baseTimer__init__ is None:
		baseTimer__init__ = TimerEntry.__init__
	
	TimerEntry.createConfig = RemoteTimerConfig
	TimerEntry.keyLeft = RemoteTimerkeyLeft 
	TimerEntry.keyRight = RemoteTimerkeyRight
	TimerEntry.keySelect = RemoteTimerkeySelect
	TimerEntry.createSetup = createRemoteTimerSetup
	TimerEntry.keyGo = RemoteTimerGo
	TimerEntry.newConfig = RemoteTimernewConfig
	TimerEntry.__init__ = RemoteTimer__init__

def RemoteTimer__init__(self, session, timer):
	baseTimer__init__(self, session, timer)
	if int(self.timerentry_remote.value) != 0:
		RemoteTimernewConfig(self)

def RemoteTimerConfig(self):
	self.Locations = []
	self.entryguilist = []
	self.entryguilist.append(("0",_("No"),None))
	index = 1
	for c in config.plugins.Partnerbox.Entries:
		self.entryguilist.append((str(index),str(c.name.value),c))
		index = index + 1
	if config.plugins.Partnerbox.enabledefaultpartnerboxintimeredit.value and index > 1:
		default = "1"
	else:
		default = "0"
	self.timerentry_remote = ConfigSelection(default = default, choices = self.entryguilist)
	baseTimercreateConfig(self)

#def getLocationsError(self, error):
#	RemoteTimercreateConfig(self)
#	RemoteTimerCreateSetup(self,"config")

def getLocations(self, url, check):
	try:
		f = urllib.urlopen(url)
		sxml = f.read()
		getLocationsCallback(self,sxml, check)
	except: pass

def getLocationsCallback(self, xmlstring, check = False):
	try: root = xml.etree.cElementTree.fromstring(xmlstring)
	except: return 
	for location in root.findall("e2location"):
		add = True
		if check:
			add = location.text.decode("utf-8").encode("utf-8", 'ignore') not in self.Locations
		if add:
			self.Locations.append(location.text.decode("utf-8").encode("utf-8", 'ignore'))
	for location in root.findall("e2simplexmlitem"):
		add = True
		if check:
			add = location.text.decode("utf-8").encode("utf-8", 'ignore') not in self.Locations
		if add:
			self.Locations.append(location.text.decode("utf-8").encode("utf-8", 'ignore'))

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
				self.Locations = []
				getLocations(self, "http://root:" + self.entryguilist[int(self.timerentry_remote.value)][2].password.value + "@" + http_ + "/web/getlocations", False)
				if len(self.Locations) == 0:
					getLocations(self, "http://root:" + self.entryguilist[int(self.timerentry_remote.value)][2].password.value + "@" + http_ + "/web/getcurrlocation", True)
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

	if isVPSplugin():
		if self["config"].getCurrent() == self.timerVps_enabled_Entry:
			if self.timerentry_vpsplugin_enabled.value == "no":
				self.timerentry_vpsplugin_dontcheck_pdc = False

			self.createSetup("config")
			self["config"].setCurrentIndex(self["config"].getCurrentIndex() + 1)

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
		if self.Locations:
			default = self.Locations[0]
		else:
			default = "N/A"
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
	self.timerentry_vps_in_timerevent = ConfigSelection(default = "no", choices = [("no", _("No")), ("yes_safe", _("Yes (safe mode)")), ("yes", _("Yes"))])

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
	if config.plugins.Partnerbox.enablevpsintimerevent.value:
		if isVPSplugin():
			cfg = self.timerentry_vpsplugin_enabled
		else:
			cfg = self.timerentry_vps_in_timerevent
		self.list.append(getConfigListEntry(_("Enable VPS"), cfg ))
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
			if dirname == "N/A":
				self.session.open(MessageBox,_("Timer can not be added...no locations on partnerbox available."),MessageBox.TYPE_INFO)
			else:
				afterevent = {
				"deepstandby": AFTEREVENT.DEEPSTANDBY,
				"standby": AFTEREVENT.STANDBY,
				"nothing": AFTEREVENT.NONE,
				"auto": AFTEREVENT.AUTO
				}.get(self.timerentry_afterevent.value, AFTEREVENT.AUTO)
				try:
					eit = self.timer.eit
				except:
					eit = 0
				if eit is None: eit = 0
				if service_ref.getPath(): # partnerbox service ?
					service_ref = getServiceRef(service_ref.ref.toString())
				refstr = ':'.join(str(service_ref).split(':')[:11])
				sCommand = "%s/web/timeradd?sRef=%s&begin=%d&end=%d&name=%s&description=%s&dirname=%s&eit=%d&justplay=%d&afterevent=%s&vps_pbox=%s" % (http,refstr,begin,end,name,descr,dirname,eit,justplay,afterevent,vpsValue(self))
				sendPartnerBoxWebCommand(sCommand, None,3, "root", str(self.entryguilist[int(self.timerentry_remote.value)][2].password.value)).addCallback(boundFunction(AddTimerE2Callback,self, self.session)).addErrback(boundFunction(AddTimerError,self,self.session))

def AddTimerE2Callback(self, session, answer):
	text = ""
	try: root = xml.etree.cElementTree.fromstring(answer)
	except: pass
	statetext = root.findtext("e2statetext")
	state = root.findtext("e2state")
	if statetext:
		text = statetext.encode("utf-8", 'ignore')
	ok = state == "True"
	session.open(MessageBox,_("Partnerbox Answer: \n%s") % _(text),MessageBox.TYPE_INFO, timeout = 10)
	if ok:
		if (config.plugins.Partnerbox.enablepartnerboxepglist.value): 
			# Timerlist der Partnerbox neu laden --> Anzeige fuer EPGList, aber nur, wenn die gleiche IP in EPGList auch angezeigt wird
			if partnerboxfunctions.CurrentIP == self.entryguilist[int(self.timerentry_remote.value)][2].ip.value:
				SetPartnerboxTimerlist(self.entryguilist[int(self.timerentry_remote.value)][2])
		self.keyCancel()

def AddTimerE1Callback(self, session, answer):
	ok = answer == "Timer event was created successfully."
	if answer == "Timer event was created successfully.":
		answer = _("Timer event was created successfully.")
	session.open(MessageBox,_("Partnerbox Answer: \n%s") % (answer),MessageBox.TYPE_INFO, timeout = 10)
	if ok:
		if (config.plugins.Partnerbox.enablepartnerboxepglist.value): 
			# Timerlist der Partnerbox neu laden --> Anzeige fuer EPGList, aber nur, wenn die gleiche IP in EPGList auch angezeigt wird
			if partnerboxfunctions.CurrentIP == self.entryguilist[int(self.timerentry_remote.value)][2].ip.value:
				SetPartnerboxTimerlist(self.entryguilist[int(self.timerentry_remote.value)][2])
		self.keyCancel()

def AddTimerError(self, session, error):
	session.open(MessageBox,str(_(error.getErrorMessage())),MessageBox.TYPE_INFO)

def isVPSplugin():
	try:
		from Plugins.SystemPlugins.vps.Modifications import vps_already_registered
		if vps_already_registered:
			return True
	except:
		return False

def vpsValue(self):
	if isVPSplugin():
		return self.timerentry_vpsplugin_enabled.value
	if config.plugins.Partnerbox.enablevpsintimerevent.value:
		return self.timerentry_vps_in_timerevent.value
	return ""