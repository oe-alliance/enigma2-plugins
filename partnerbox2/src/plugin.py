# Copyright (C) 2024 jbleyel, Mr.Servo
# This file is part of enigma2-plugins <https://github.com/oe-alliance/enigma2-plugins>.
#
# PartnerBox is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# dogtag is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PartnerBox.  If not, see <http://www.gnu.org/licenses/>.

# Changelog:
# 1.0 Initial version

# This plugin is a complete refactored version of the old PartnerBox by Dr.Best

# PYTHON IMPORTS
from datetime import datetime, timedelta
from functools import cmp_to_key
from html import unescape
from json import loads
from requests import get, exceptions
from socket import gethostbyname, gaierror
from time import localtime, mktime, time
from timer import TimerEntry
from twisted.internet.threads import deferToThread
import traceback

# ENIGMA IMPORTS
from enigma import eEPGCache, eServiceCenter, eServiceReference, eTimer, getPeerStreamingBoxes, ePoint
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.config import config, configfile, ConfigClock, ConfigSelection, ConfigSubsection, ConfigSubList, ConfigInteger, ConfigYesNo, ConfigText, ConfigIP
from Components.ChoiceList import ChoiceEntryComponent
from Components.Element import cached
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.Sources.Source import Source
from Components.Sources.StaticText import StaticText
from Components.SystemInfo import BoxInfo
from Components.Task import job_manager, Job, Task
from Plugins.Plugin import PluginDescriptor
from RecordTimer import RecordTimer, RecordTimerEntry
from ServiceReference import ServiceReference
from Screens.ChannelSelection import ChannelContextMenu, OFF, MODE_TV, service_types_tv, service_types_radio
from Screens.EpgSelection import EPGSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import InfoBar
from Screens.InfoBarGenerics import InfoBarAudioSelection
from Screens.InputBox import PinInput
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen, ScreenSummary
from Screens.Setup import Setup
import Screens.Standby
from Screens.TagEditor import TagEditor
from Screens.Timers import RecordTimerOverview, RecordTimerEdit
from Tools.BoundFunction import boundFunction

# PLUGIN IMPORTS
from . import _   # for plugin localized messages
from . import __   # for enigma localized messages

# GLOBALS
VERSION = "1.0"
MODULE_NAME = __name__.split(".")[-2]
WEBIF_ERRMSG = "Unexpected error accessing WebIF"
WEBIF_ERRMSG_TRANS = _("Unexpected error accessing WebIF")
originalChannelContextMenu__init__ = None
originalEPGSelectionRecordTimerQuestion = None
originalEPGSelectiongetRecordEvent = None


def initPartnerboxEntryConfig(index):
	now = localtime()
	begin = int(mktime((now.tm_year, now.tm_mon, now.tm_mday, 0o3, 0, 0, now.tm_wday, now.tm_yday, now.tm_isdst)))
	config.plugins.Partnerbox.Entries.append(ConfigSubsection())
	config.plugins.Partnerbox.Entries[index].name = ConfigText(default="Remote box", visible_width=50, fixed_size=False)
	config.plugins.Partnerbox.Entries[index].ip = ConfigIP(default=[192, 168, 0, 98])
	config.plugins.Partnerbox.Entries[index].port = ConfigInteger(default=80, limits=(1, 65555))
	config.plugins.Partnerbox.Entries[index].password = ConfigText(default="root", visible_width=50, fixed_size=False)
	config.plugins.Partnerbox.Entries[index].zaptoservicewhenstreaming = ConfigYesNo(default=False)
	config.plugins.Partnerbox.Entries[index].epg = ConfigYesNo(default=False)
	config.plugins.Partnerbox.Entries[index].epgtime = ConfigClock(default=begin)
	config.plugins.Partnerbox.Entries[index].epglastrun = ConfigInteger(default=0)
	config.plugins.Partnerbox.Entries[index].index = ConfigInteger(default=index)
	return config.plugins.Partnerbox.Entries[index]


config.plugins.Partnerbox = ConfigSubsection()
config.plugins.Partnerbox.showremotetvinextensionsmenu = ConfigYesNo(default=False)
config.plugins.Partnerbox.showcurrentstreaminextensionsmenu = ConfigYesNo(default=False)
config.plugins.Partnerbox.enablepartnerboxepglist = ConfigYesNo(default=False)
config.plugins.Partnerbox.enablepartnerboxchannelselector = ConfigYesNo(default=False)
config.plugins.Partnerbox.entriescount = ConfigInteger(0)
config.plugins.Partnerbox.debuglog = ConfigYesNo(default=True)
choices = [(30, _("%d Minutes") % 30)] + [(x * 60, ngettext("%d Hour", "%d Hours", x) % x) for x in (1, 2, 4, 6, 12)]
config.plugins.Partnerbox.refreshTimerList = ConfigSelection(default=60, choices=choices)
config.plugins.Partnerbox.Entries = ConfigSubList()
for idx in range(config.plugins.Partnerbox.entriescount.value):
	initPartnerboxEntryConfig(idx)


def logUserInfo(session, info="", webif=False, log=True, timeout=3):
	if log:
		print(f"[{MODULE_NAME}] {info}")
	if webif:
		info = f'{WEBIF_ERRMSG_TRANS}: {info}'
	session.open(MessageBox, info, MessageBox.TYPE_INFO, timeout=timeout, close_on_any_key=True)


def logError(modulename, error, addinfo=""):
	print(f"[{MODULE_NAME}] ERROR in module '{modulename}' - {addinfo}: {_(str(error))}")


def logDebug(message):
	if config.plugins.Partnerbox.debuglog.value:
		print(f"[{MODULE_NAME}-DEBUG] {str(message)}")


def getIPString(configentry):
	return ".".join([str(x) for x in configentry.ip.value])


def getBaseUrl(configentry):
	return f"http://{getIPString(configentry)}:{configentry.port.value}"


def getRefstrIpPort(sref):
	ip = getIPfromSref(str(sref))
	port = None
	baseUrl = None
	reflist = str(sref).split(':')[:11]
	refstr = f"{':'.join(reflist[:10])}:"
	if ip and "http" in reflist[10]:  # remote sref
		for configentry in config.plugins.Partnerbox.Entries:
			if ip == getIPString(configentry):
				port = str(configentry.port.value)
				baseUrl = f"http://{ip}:{port}"
				break
		if not port:
			logError("getRefstrIpPort", f"IP ({ip}) is not listed in Partnerbox settings.")
	return (refstr, ip, port, baseUrl)


def getIndexFromSref(sref):
	index = -1  # local box
	if str(sref).split(":")[:11][10].lower().startswith("http"):
		refstr, ip, port, baseUrl = getRefstrIpPort(sref)
		if port and ip:
			index = getIndexFromIp(ip)
	return index


def getIPfromSref(sref):
	if "http" in sref:  # remote sref
		reflist = sref.split(':')[:11]
		trimmed = reflist[10].replace("http%3a//", "").replace("https%3a//", "")
		ip = trimmed[:trimmed.find("%3a")]
	else:
		ip = None
	return ip


def getIndexFromIp(ip):
	if ip:
		index = None
		for idx, configentry in enumerate(config.plugins.Partnerbox.Entries):
			if ip == getIPString(configentry):
				index = idx
				break
		if index is None:
			index = -1  # local box
			logError("getIndexFromIp", f"IP ({ip}) is not listed in Partnerbox settings.")
	else:
		index = -1  # local box
	return index


class RemoteTimersData:
	def __init__(self):
		self.timerData = {}

	def setTimerData(self, index, timerlist, locations, tags, default):
		self.timerData[index] = (timerlist, locations, tags, default)


remoteTimersData = RemoteTimersData()


class PartnerboxGlobals:
	def __init__(self, session):
		self.session = session

	def loadExternalEPGlist(self, sref, baseUrl, password, callback):
		cmd = f"{baseUrl}/api/epgnow?bRef={sref}&showstreamrelay=1"
		sendAPIcommand(cmd, password).addCallback(self.loadExternalEPGlistCallback, callback).addErrback(self.loadExternalEPGlistError)

	def loadExternalEPGlistCallback(self, jsondict, callback):
		epglist = []
		if jsondict:
			for event in jsondict.get("events", []):
				eid = event.get("id", 0)
				begin = event.get("begin_timestamp", 0)
				duration = event.get("duration_sec", 0)
				title = unescape(event.get("title", ""))
				shortdesc = unescape(event.get("shortdesc", ""))
				longdesc = unescape(event.get("longdesc", ""))
				sref = event.get("sref", "")
				sname = unescape(event.get("sname", _("n/a")))
				begintime = datetime.fromtimestamp(begin)
				end = begintime + timedelta(seconds=duration)
				btimestr = begintime.strftime("%H:%M")
				dtimestr = str(int(duration / 60.0))
				etimestr = end.strftime("%H:%M")
				rest = (end - datetime.now()).total_seconds()
				rtimestr = int(rest / 60)
				progress = 100 - int(rest / duration * 100) if duration else 0
				timeline = f'+{rtimestr}  {btimestr} ... {etimestr} ({dtimestr}  {__("Minutes")})'
				epglist.append((event, sname, title, progress, timeline, btimestr, etimestr, dtimestr, rest))
		callback((True, epglist))

	def loadExternalEPGlistError(self, error):
		if error:
			logError("loadExternalEPGlistError", error, addinfo=WEBIF_ERRMSG)
			logUserInfo(self.session, error, timeout=10, webif=True)

	def getTimerlistValues(self, jsondict, index):
		timerlist = []
		locations = []
		tags = []
		default = None
		if jsondict:
			for timer in jsondict.get("timers", []):
				timerlist.append(self.createTimer(timer, index))
			locations = jsondict.get("locations", ["/media/hdd/movie"])
			tags = jsondict.get("tags", [])
			default = jsondict.get("default", default)  # TODO evtl geht auch leerstring wobei default IMMER gesetzt sein muss
		return timerlist, locations, tags, default

	def createTimer(self, timerdict, index):
		serviceref = ServiceReference(timerdict.get("serviceref", 0))
		serviceref.ref.setName(timerdict.get("servicename", ""))
		eit = timerdict.get("eit", "None")
		eit = int(eit) if eit != "None" else None
		name = timerdict.get("name")
		description = timerdict.get("description", "None")
		disabled = timerdict.get("disabled", 0)
		begin = timerdict.get("begin", 0)
		end = timerdict.get("end", 0)
		justplay = timerdict.get("justplay", 0)
		afterevent = timerdict.get("afterevent", 0)
		dirname = timerdict.get("dirname", None) or remoteTimersData.timerData.get(index, ([], [], [], None))[3]
		tags = timerdict.get("tags", "")
		tags = tags.split(" ") if tags else None
		repeated = timerdict.get("repeated", 0)
		marginBefore = timerdict.get("marginBefore", -1)
		marginAfter = timerdict.get("marginAfter", -1)
		descramble = timerdict.get("descramble", 1)
		recordecm = timerdict.get("record_ecm", 0)
		vpsenabled = timerdict.get("vpsplugin_enabled", False)
		vpsoverwrite = timerdict.get("vpsplugin_overwrite", False)
		vpstime = timerdict.get("vpsplugin_time", -1)
		always_zap = timerdict.get("always_zap", 0)
		isAutotimer = timerdict.get("isAutoTimer", 0)
		ice_timer_id = timerdict.get("ice_timer_id", 0)
		if ice_timer_id == -1:
			ice_timer_id = 0
		if marginBefore == -1:
			marginBefore = (getattr(config.recording, "zap_margin_before" if justplay else "margin_before").value * 60)
		if marginAfter == -1:
			marginAfter = (getattr(config.recording, "zap_margin_after" if justplay else "margin_after").value * 60)
		eventbegin = timerdict.get("eventbegin", 0)
		if eventbegin == 0:
			eventbegin = begin + marginBefore
		eventend = timerdict.get("eventend", 0)
		if eventend == 0:
			eventend = end - marginAfter
		hasEndTime = timerdict.get("hasEndTime", False)
		renamerepeat = timerdict.get("rename_repeat", True)
		timer = RecordTimerEntry(serviceref, begin, end, name, description, eit, disabled, justplay, afterevent, dirname=dirname, tags=tags, descramble=descramble,
								 record_ecm=recordecm, isAutoTimer=isAutotimer, ice_timer_id=ice_timer_id, always_zap=always_zap, rename_repeat=renamerepeat)
		timer.marginBefore = marginBefore
		timer.eventbegin = eventbegin
		timer.eventend = eventend
		timer.marginAfter = marginAfter
		timer.hasEndTime = hasEndTime
		timer.repeated = repeated
		timer.vpsplugin_overwrite = vpsoverwrite
		timer.vpsplugin_enabled = vpsenabled
		if vpstime and vpstime != "None":
			timer.vpsplugin_time = vpstime
		for log in timerdict.get("logentries", []):
			timer.log_entries.append((log[0], log[1], log[2]))
		timer.state = timerdict.get("state", 0)
		timer.index = index
		return timer

	def getServiceRef(self, serviceref):
		if serviceref:
			hindex = serviceref.find("http")
			return serviceref[:hindex] if hindex > 0 else serviceref  # is Partnerbox service or not?
		return ""


class TimerListTask(Task, PartnerboxGlobals):
	def __init__(self, job, name, index, session):
		Task.__init__(self, job, name)
		self.index = index
		self.session = session
		self.weighting = 1

	def work(self):
		configentry = config.plugins.Partnerbox.Entries[self.index]
		password = configentry.password.value
		url = f"{getBaseUrl(configentry)}/api/timerlist"
		auth = ("root", password) if password else None
		try:
			response = get(url, headers={}, auth=auth, timeout=(3.05, 3), verify=False)
			response.raise_for_status()
			timerlist, locations, tags, default = self.getTimerlistValues(loads(response.content), self.index)  # get current timerlist
			remoteTimersData.setTimerData(self.index, timerlist, locations, tags, default)
			self.session.nav.RecordTimer.setRemoteTimers(timerlist, self.index + 1)
		except exceptions.RequestException as error:
			logError("TimerListTask work fetch", error)
		except Exception as error:
			logError("TimerListTask work import", error)
			traceback.print_exc()

	def _run(self):
		self.aborted = False
		self.pos = 0
		deferToThread(self.work).addBoth(self.onComplete)

	def onComplete(self, result):
		self.finish()


class EPGTask(Task):
	def __init__(self, job, name, index, sref):
		Task.__init__(self, job, name)
		self.index = index
		self.sref = sref
		self.weighting = 1
		self.servicecount = 0

	def work(self):
		configentry = config.plugins.Partnerbox.Entries[self.index]
		password = configentry.password.value
		url = f"{getBaseUrl(configentry)}/api/epgservice?sRef={self.sref}&endTime=1440"
		auth = ("root", password) if password else None
		try:
			response = get(url, headers={}, auth=auth, timeout=(3.05, 3), verify=False)
			response.raise_for_status()
			jsondict = loads(response.content)
			events = []
			for event in jsondict.get("events"):
				events.append((
					event.get("begin_timestamp"),
					event.get("duration_sec"),
					event.get("title"),
					event.get("shortdesc"),
					event.get("longdesc"),
					0,
					event.get("id")
				))
			if events:
				epgcache = eEPGCache.getInstance()
				epgcache.importEvents(self.sref, events)
				self.servicecount = len(events)
		except exceptions.RequestException as error:
			logError("EPGTask work fetch", error)
		except Exception as error:
			logError("EPGTask work import", error)
			traceback.print_exc()

	def _run(self):
		self.aborted = False
		self.pos = 0
		deferToThread(self.work).addBoth(self.onComplete)

	def onComplete(self, result):
		self.finish()


class PBAutoPoller:
	def __init__(self):
		self.epgTimer = eTimer()
		self.timerListTimer = eTimer()
		self.session = None
		self.allservices = []
		self.updateRefreshtimes()
		self.epgTimer.callback.append(self.runEpgTimerUpdate)
		self.timerListTimer.callback.append(self.runTimerListUpdate)

	def updateRefreshtimes(self):  # TODO: This needs to called again if the configuration was changed
		self.refreshtimes = []
		nextEPGUpdateRun = 0
		now = localtime()
		for index, configentry in enumerate(config.plugins.Partnerbox.Entries):
			if configentry.epg.value:
				nextstarttime = mktime((now.tm_year, now.tm_mon, now.tm_mday, configentry.epgtime.value[0], configentry.epgtime.value[1], 0, now.tm_wday, now.tm_yday, now.tm_isdst))
				if nextstarttime < mktime(now):
					nextstarttime += 86400  # next day
				nextEPGUpdateRun = nextstarttime if nextEPGUpdateRun == 0 else min(nextstarttime, nextEPGUpdateRun)
				self.refreshtimes.append((nextstarttime, index))

		if nextEPGUpdateRun:
			self.epgTimer.startLongTimer(int(nextEPGUpdateRun - mktime(now)))

	def startPoller(self):
		if config.plugins.Partnerbox.refreshTimerList.value:
			self.timerListTimer.start(15000)  # 15 sec after boot

	def stopPoller(self):
		self.epgTimer.stop()

	def runTimerListUpdate(self):
		def failCallback(job, task, problems):
			logError("runTimerListUpdate", f"job: {job}, task: {task}, problems: {problems}", addinfo=WEBIF_ERRMSG)

		def successCallback(job):
			pass

		self.timerListTimer.changeInterval(config.plugins.Partnerbox.refreshTimerList.value * 60000)
		if config.plugins.Partnerbox.enablepartnerboxepglist.value:
			if not Screens.Standby.inStandby:  # do not run in standby
				for index, configentry in enumerate(config.plugins.Partnerbox.Entries):
					job_manager.AddJob(self.createTimerListTask(index), onSuccess=successCallback, onFail=failCallback)

	def createTimerListTask(self, index):
		job = Job("PartnerBoxTimer")
		taskname = f"PartnerBoxTimer_{index}"
		task = TimerListTask(job, taskname, index, self.session)
		return job

	def runEpgTimerUpdate(self, index=-1):
		def failCallback(job, task, problems):
			self.updateRefreshtimes()

		def successCallback(job):
			services = 0
			for t in job.tasks:
				services += t.servicecount
			if services:
				epgcache = eEPGCache.getInstance()
				epgcache.save()
			self.updateRefreshtimes()

		self.epgTimer.stop()
		refreshIndexes = []
		if index > -1:
			refreshIndexes.append(index)
		else:
			now = int(mktime(localtime())) - 5  # 5 seconds calulation offset
			for remotetime in self.refreshtimes:
				if now > remotetime[0]:
					refreshIndexes.append(remotetime[1])
		if refreshIndexes:
			if not self.allservices:
				self.allservices = self.getAllServices() + self.getAllServices(stype="radio")
			for index in refreshIndexes:
				services = self.getServices(index)
				if services:
					job_manager.AddJob(self.createEpgTask(index, services), onSuccess=successCallback, onFail=failCallback)
		else:
			self.updateRefreshtimes()

	def createEpgTask(self, index, services):
		config.plugins.Partnerbox.Entries[index].epglastrun.value = int(time())
		config.plugins.Partnerbox.Entries[index].epglastrun.save()

		job = Job("PartnerBoxEPG")
		for sindex, service in enumerate(services):
			taskname = f"PartnerBoxEPG_{index}_{sindex}"
			task = EPGTask(job, taskname, index, service)
		return job

	def getServices(self, index):
		services = []
		for service in self.allservices:
			if "http%3a//" in service and "8001" in service:
				if index == getIndexFromSref(service):
					sref = service.split("http")[0]
					if sref not in self.allservices:
						services.append(sref)
		return services

	def getAllServices(self, stype="tv"):
		result = []
		s_type, s_type2 = (service_types_radio, "bouquets.radio") if stype == "radio" else (service_types_tv, "bouquets.tv")
		servicehandler = eServiceCenter.getInstance()
		services = servicehandler.list(eServiceReference(f'{s_type} FROM BOUQUET "{s_type2}" ORDER BY bouquet'))
		bouquets = services and services.getContent("SN", True)
		for bouquet in bouquets:
			if "lastscanned" not in bouquet[1] and int(bouquet[0].split(":")[1]) & eServiceReference.isInvisible == 0:
				bqservices = servicehandler.list(eServiceReference(bouquet[0]))
				slist = bqservices and bqservices.getContent("S", True)
				for item in slist:
					flags = int(item.split(":")[1])
					if flags & eServiceReference.isInvisible == 0 and flags & eServiceReference.isMarker == 0:
						result.append(item)
		return result


pbAutopoller = PBAutoPoller()


class BouquetChoiceBox(ChoiceBox, PartnerboxGlobals):
	def __init__(self, session, configentry, inserttype):
		self.configentry = configentry
		self.inserttype = inserttype
		self.password = configentry.password.value
		self.bouquetlist = []
		self.servicelist = []
		print(f"[BouquetChoiceBox] DEBUG ip='{configentry.ip.value}' port='{configentry.port.value}'")
		ChoiceBox.__init__(self, session, choiceList=[("", ""), ("", "")])
		self.cmd = f"{getBaseUrl(configentry)}/api/getservices"

	def layoutFinished(self):
		ChoiceBox.layoutFinished(self)
		self["list"].setList([])
		self["text"].setText("getting data....")
		self.getBouquets()
		self.setTitle(_("Partnerbox: Select Bouquet"))

	def getBouquets(self):
		def getBouquetsCallback(jsondict):
			self["text"].setText("")
			self.choiceList = []
			for service in jsondict.get("services", []):
				sname = unescape(service.get("servicename", _("n/a")))
				sref = service.get("servicereference", _("n/a"))
				self.bouquetlist.append(PBepg(sname=sname, sref=sref))
				self.choiceList.append(ChoiceEntryComponent(key="dummy", text=(sname, sref)))
			self["list"].setList(self.choiceList)
		sendAPIcommand(f"{self.cmd}", self.password).addCallback(getBouquetsCallback).addErrback(self.listError)

	def getServices(self, item):
		def getServicesCallback(jsondict):
			self["text"].setText("")
			self.choiceList = []
			for service in jsondict.get("services", []):
				sname = unescape(service.get("servicename", _("n/a")))
				sref = service.get("servicereference", _("n/a"))
				streamrelay = service.get("streamrelay", False)
				self.servicelist.append(PBepg(sname=sname, sref=sref, streamrelay=streamrelay))
				self.choiceList.append(ChoiceEntryComponent(key="dummy", text=(sname, sref)))
			if self.inserttype == 1:  # bouquet
				self.close((self.inserttype, (self.servicelist, item), self.configentry))
			else:
				self["list"].setList(self.choiceList)

		cmd = f"{self.cmd}?sRef={item.sref}&showstreamrelay=1"
		sendAPIcommand(cmd, self.password).addCallback(getServicesCallback).addErrback(self.listError)

	def listError(self, error=None):
		if error:
			logError("getBouquet/-Services_DownloadError", error, addinfo=WEBIF_ERRMSG)
			self["text"].setText(error)
#			logUserInfo(self.session, error, timeout=10, webif=True)

	def keySelect(self):  # Run the currently selected entry.
		current = self["list"].getCurrent()
		if current:
			currentIndex = self["list"].getSelectionIndex()
			if self.inserttype == 1:  # bouquet
				self.getServices(self.bouquetlist[currentIndex])
			elif self.inserttype == 2:  # player
				self.session.open(RemoteChannelList, [], self.bouquetlist[currentIndex].sref, self.configentry, True)
				self.close(None)
			else:
				if self.servicelist:
					self.close((self.inserttype, ([], self.servicelist[currentIndex]), self.configentry))
				else:
					self.setTitle(_("Partnerbox: Select Channel"))
					self.getServices(self.bouquetlist[currentIndex])

		# callback inserttype 0 -> ( 0 , ([], item), configentry)
		# callback inserttype 1 -> ( 1 , ([items], bouquet), configentry)


def setPartnerboxService(self, item, configentry):
	ip = getIPString(configentry)
	service = eServiceReference(item.sref)
	refstr = ":".join(item.sref.split(":")[:11])
	streamPort = 17999 if item.streamrelay else 8001
	service.setPath(f"http://{ip}:{streamPort}/{refstr}")
	service.setName(f"{item.sname} ({configentry.name.value})")
	return service


def sendAPIcommand(url, password="", timeout=(3.05, 3), headers={}, verify=False):
	def sendUrl(url, timeout, headers, auth):
		print("[Partnerbox] sendUrl:")  # TODO remove debug if finished
		print(url)
		try:
			response = get(url, headers=headers, auth=auth, timeout=timeout, verify=verify)
			response.raise_for_status()
			return loads(response.content)
		except exceptions.RequestException as error:
			logError("sendAPIcommand", error)

	auth = ("root", password) if password else None
	return deferToThread(lambda: sendUrl(url, timeout, headers, auth))


def getBoxList():
	boxlist = []
	for index, rawdata in enumerate(config.plugins.Partnerbox.Entries):
		name = rawdata.name.value
		ip = ".".join(map(str, rawdata.ip.value))
		port = rawdata.port.value
		boxlist.append((f"{name}\t{ip}\t{port}", index))
	return boxlist


class PBepg:  # for details see JSON-result from {box-ip}/api/epgservicenow?sRef={reference}
	def __init__(self, **kwargs):
		self.id = kwargs.get("id", 0)
		self.begin = kwargs.get("begin", 0)
		self.duration = kwargs.get("duration", 0)
		self.end = kwargs.get("end", 0)
		self.rest = kwargs.get("rest", 0)
		self.title = kwargs.get("title", 0)
		self.shortdesc = kwargs.get("shortdesc", "")
		self.longdesc = kwargs.get("longdesc", "")
		self.sref = kwargs.get("sref", "")
		self.sname = kwargs.get("sname", "")
		self.streamrelay = kwargs.get("streamrelay", False)


class PBtimer:  # for details see JSON-result from {box-ip}/api/timerlist
	def __init__(self, **kwargs):
		# TODO: Vollständigkeit prüfen und unterscheiden: was ist Umfang unter TIMER.xxx und was ist Allgemeinumfang
		# derzeit noch Maximalumfang hieraus: https://github.com/oe-alliance/OpenWebif/blob/main/plugin/controllers/web.py#L1100
		timer = kwargs.get("timer")
		if timer:
			self.service_ref = timer.service_ref
			self.begin = timer.begin
			self.end = timer.end
			self.name = timer.name
			self.justplay = timer.justplay
			self.isAutoTimer = timer.isAutoTimer
			self.repeated = timer.repeated
			self.hasEndTime = timer.hasEndTime
			self.marginBefore = timer.marginBefore
			self.marginAfter = timer.marginAfter
			self.descramble = timer.descramble
			self.record_ecm = timer.record_ecm
			self.description = timer.description
			self.eit = timer.eit
			self.afterEvent = timer.afterEvent
			self.tags = timer.tags
			self.dirname = timer.dirname or ""
			self.always_zap = timer.always_zap
			self.external = timer.external
		else:
			self.service_ref = kwargs.get("service_ref", _("No servicereference available"))
			self.begin = kwargs.get("begin", 0)  # NOTE: begin = eventBegin - marginBefore
			self.end = kwargs.get("end", 0)  # NOTE: end = eventEnd + marginAfter
			self.name = kwargs.get("name", _("No name available"))
			self.justplay = kwargs.get("justplay", 0)  # NOTE: 1 only in case of ZAP
			self.isAutoTimer = kwargs.get("isAutoTimer", 0)
			self.repeated = kwargs.get("repeated", 0)
			self.hasEndTime = kwargs.get("hasEndTime", True)
			self.recordingtype = kwargs.get("recordingtype", "normal")
			self.marginBefore = kwargs.get("marginBefore", -1)
			self.marginAfter = kwargs.get("marginAfter", -1)
			self.description = kwargs.get("description", _("No description available"))
			self.eit = kwargs.get("eit", 0)
			self.descramble = {"normal": True, "descrambled+ecm": True, "scrambled+ecm": False}[self.recordingtype]
			self.record_ecm = {"normal": False, "descrambled+ecm": True, "scrambled+ecm": True}[self.recordingtype]
			self.afterEvent = kwargs.get("afterEvent", 3)  # NOTE: 1 only in case of RECORD+ZAP, justplay and afterEvent never both on 1
			self.tags = kwargs.get("tags", [])
			self.dirname = kwargs.get("dirname", "None")
			self.always_zap = kwargs.get("always_zap", 0)
			self.external = kwargs.get("external", False)

		self.service_name = kwargs.get("service_name", _("No servicename available"))
		self.disabled = kwargs.get("disabled", 0)
		self.repeatedbegindate = self.begin
		self.duration = kwargs.get("duration", 0)
		self.startprepare = kwargs.get("startprepare", 0)
		self.state = kwargs.get("state", 0)
		self.ice_timer_id = kwargs.get("ice_timer_id", -1)
		self.eventBegin = kwargs.get("eventBegin", 0)
		self.eventEnd = kwargs.get("eventEnd", 0)
		self.rename_repeat = kwargs.get("rename_repeat", True)
		self.vpsplugin_overwrite = kwargs.get("vpsplugin_overwrite", True)
		self.vpsplugin_time = kwargs.get("vpsplugin_time", -1)
		self.log_entries = kwargs.get("log_entries", [])
		self.index = kwargs.get("index", -1)  # indexing for the associated partnerbox
		self.flags = set()

	def __str__(self):
		result = {}
		for x in dir(self):
			if not x.startswith("_"):
				result[x] = getattr(self, x)
		return str(result)

	def resetRepeated(self):
		self.repeated = 0

	def timerurldata(self):
		# this exists:	justplay, afterevent, dirname, tags, repeated, description, sRef, begin, end,
		# 				eit, always_zap, recordingtype, marginbefore, marginafter, hasendtime
		if self.record_ecm and self.descramble:
			recordingType = "&recordingtype=descrambled+ecm"
		elif self.record_ecm:
			recordingType = "&recordingtype=scrambled+ecm"
		else:
			recordingType = ""
		tags = f"&tags={' '.join(self.tags)}" if self.tags else ""
		justplay = "&justplay=1" if self.justplay else ""
		always_zap = "&always_zap=1" if self.always_zap else ""
		repeated = f"&repeated={self.repeated}" if self.repeated else ""
		hasendtime = "&hasendtime=1" if self.hasEndTime else ""
		# TOOD nicht alle parameter sind notwendig. Add maybe later: vpsplugin_enable, vpsplugin_overwrite, vpsplugin__time
		# Anmerkung: dies wurde aussortiert: duration={self.duration}
		return f"""&begin={self.begin}&end={self.end}&marginafter={self.marginAfter}&marginbefore={self.marginBefore}&eit={self.eit}\
&afterevent={self.afterEvent}&name={self.name}&description={self.description}&dirname={self.dirname}\
{hasendtime}{repeated}{justplay}{always_zap}{tags}{recordingType}"""
# Don't change this: If these both code lines are not completely left-aligned, tabs are included despite the line break separator ('\')


class CurrentRemoteTV(Screen, PartnerboxGlobals):
	def __init__(self, session, configentry):
		self.session = session
		self.configentry = configentry
		Screen.__init__(self, session)
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.password = configentry.password.value
		ip = getIPString(configentry)
		self.streamurl = f"http://{ip}:8001/"
		cmd = f"{getBaseUrl(configentry)}/api/getcurrent"
		sendAPIcommand(cmd, self.password).addCallback(self.remotePlayerCallback).addErrback(self.remotePlayerError)

	def remotePlayerCallback(self, jsondict):
		def remotePlayerFinished():
			if self.oldService:
				self.session.nav.playService(self.oldService)
			else:
				self.session.nav.stopService()
			self.close()
		if jsondict:
			info = jsondict.get("info", {})
			now = jsondict.get("now", {})
			if info.get("result", False) and now:
				refstr = info.get("ref", "")
				logDebug(f"Current sref={refstr}")
				streamRelayCheck = "http%253a//127.0.0.1%253a17999/"
				if isPBservice(self.session, refstr) or streamRelayCheck in refstr:
					if streamRelayCheck in refstr:
						refstr = refstr.split(streamRelayCheck)[1]
						streamUrl = self.streamurl.replace(":8001/", ":17999/")
						url = f"{streamUrl}{refstr}"
					else:
						url = f"{self.streamurl}{refstr}"
					name = info.get("name", "")
					playerRef = eServiceReference(refstr)
					playerRef.setName(name)
					playerRef.setPath(url)
					self.session.nav.playService(playerRef, adjust=False)
					self.session.openWithCallback(remotePlayerFinished, RemotePlayer, name, refstr, self.configentry, self.session.current_dialog)
					return
		self.close()

	def remotePlayerError(self, error=None):
		logError("RemotePlayerError", error)
		logUserInfo(self.session, f'{_("Unexpected error accessing stream")}: {error}', timeout=10)
		self.close()


class RemoteTagEditor(TagEditor):
	def __init__(self, session, tags=None, service=None, parent=None, remoteTags=None, isLocal=False):
		self.remoteTags = remoteTags
		self.isLocal = isLocal
		TagEditor.__init__(self, session, tags, service, parent)

	def loadTags(self):
		if self.isLocal:
			return TagEditor.loadTags(self)
		else:
			return self.remoteTags

	def saveTags(self):
		if self.isLocal:
			TagEditor.saveTags(self)
		else:
			pass  # send tags to remote box if changed but this is may not really needed


class RemoteTimerEdit(RecordTimerEdit):
	def __init__(self, session, timer, locations, tags, allowLocal):
		self.remoteLocations = locations
		self.remoteTags = tags
		self.entryguilist = [(timer.index, config.plugins.Partnerbox.Entries[timer.index].name.value)]
		if allowLocal:
			self.entryguilist.append((-1, _("Local box")))
		self.remoteTimerentry = ConfigSelection(default=timer.index, choices=self.entryguilist)
		RecordTimerEdit.__init__(self, session, timer)

	def isLocal(self):
		return self.timer.index == -1

	def createSetup(self):  # NOSONAR silence S2638
		Setup.createSetup(self, prependItems=[(_("Remote box:"), self.remoteTimerentry)])
#		self.list.insert(0, (_("Remote box:"), self.remoteTimerentry))
#		self["config"].updateList = self.list

	def getTags(self):
		if self.isLocal():
			RecordTimerEdit.getTags(self)
		else:
			self.session.openWithCallback(self.tagsCallback, RemoteTagEditor, tags=self.tags, remoteTags=self.remoteTags, isLocal=False)

	def tagsCallback(self, result):
		if result:
			self.tags = result
			self.timerTags.setChoices([not result and "None" or " ".join(result)])

	def getChannels(self):
		if self.isLocal():
			RecordTimerEdit.getChannels(self)
		# TODO get channels from remote box
#		from Screens.ChannelSelection import SimpleChannelSelection  # This import must be located here to avoid a boot loop!
#		self.session.openWithCallback(self.channelCallback, SimpleChannelSelection, _("Select the channel from which to record:"), currentBouquet=True)

#	def channelCallback(self, *result):
#		if result:
#			self.timerServiceReference = ServiceReference(result[0])
#			self.timerService.setCurrentText(self.timerServiceReference.getServiceName())
#			for callback in onRecordTimerChannelChange:
#				callback(self)

	def saveMovieDir(self):  # owerwrite from base class
		if self.isLocal():
			RecordTimerEdit.saveMovieDir(self)

#	def lookupEvent(self):
#		event = eEPGCache.getInstance().lookupEventId(self.timer.service_ref.ref, self.timer.eit)
#		if event:
#			parent = self.timer.service_ref.ref
#			linkServices = event.getNumOfLinkageServices()
#			if linkServices > 1:
#				subServiceList = []
#				ref = self.session.nav.getCurrentlyPlayingServiceOrGroup()
#				selection = 0
#				for linkService in range(linkServices):
#					service = event.getLinkageService(parent, linkService)
#					if service.toString() == ref.toString():
#						selection = linkService
#					subServiceList.append((service.getName(), service))
#				self.session.openWithCallback(self.subServiceCallback, ChoiceBox, title=_("Please select the sub-service to record:"), list=subServiceList, selection=selection)
#				return False
#			elif linkServices > 0:
#				self.timer.service_ref = ServiceReference(event.getLinkageService(parent, 0))
#		return True

	def saveTimers(self):
		if self.isLocal():
			self.timer.service_ref = eServiceReference(self.timer.fullServiceRef)  # TODO TEST !!!
			RecordTimerEdit.saveTimers(self)

#	def getServiceName(self, service_ref):
#		serviceName = ""
#		try:  # No current service available?  (FIXME: Some service-chooser needed here!)
#			serviceName = service_ref.getServiceName()
#		except Exception:
#			serviceName = _("N/A")
#		return serviceName

	def getLocationInfo(self):
		if self.isLocal():
			return RecordTimerEdit.getLocationInfo(self)
		else:
			default = self.remoteLocations[0] if self.remoteLocations else ""
			return (default, self.remoteLocations)

	def getLocation(self):
		if self.isLocal():
			RecordTimerEdit.getLocation(self)
		else:
			menu = [(loc, loc) for loc in self.remoteLocations]
			self.session.openWithCallback(self.getLocationCallback, ChoiceBox, title=_("Select the location in which to store the recording:"), list=menu)

	def getLocationCallback(self, result):
		if self.isLocal():
			RecordTimerEdit.getLocationCallback(self, result)
		else:
			if result:
				self.timerLocation.setChoices(self.remoteLocations, default=result[0])
				self.timerLocation.value = result[0]

	def getSpace(self):  # Don't call this because we cannot test the space on a remote box yet
		if self.isLocal():
			RecordTimerEdit.getSpace(self)

	def changedEntry(self):
		RecordTimerEdit.changedEntry(self)
		current = self["config"].getCurrent()[1]
		if current == self.remoteTimerentry:
			self.timer.index = self.remoteTimerentry.value
		self.createSetup()


class RemoteTimerOverview(RecordTimerOverview, PartnerboxGlobals):  # subclass from RecordTimerOverview
	def __init__(self, session, configentry, not_epg=False):
		self.configentry = configentry
		self["timerlist"] = List([])
		self.timerlist = []
		self.locations = []
		self.tags = []
		self.default = None
		self.password = configentry.password.value
		self.index = configentry.index.value
		self.baseUrl = getBaseUrl(configentry)
		RecordTimerOverview.__init__(self, session)
		self["key_green"].setText("")
		self["addActions"].setEnabled(False)
		title = _("Timer overview from: %s") % configentry.name.value
		self.setTitle(title)
		self["title"] = StaticText(title)
		self.onLayoutFinish.append(self.updateTimerlist)

### UPDATE TIMERLIST ###
	def updateTimerlist(self):
		cmd = f"{self.baseUrl}/api/timerlist"
		sendAPIcommand(cmd, self.password).addCallback(self.updateTimerlistCallback).addErrback(self.updateTimerlistError)

	def updateTimerlistCallback(self, jsondict):
		self.timerlist, self.locations, self.tags, self.default = self.getTimerlistValues(jsondict, self.index)  # get current timerlist
		self.loadTimerList()

	def updateTimerlistError(self, error=None):
		if error:
			logError("updateTimerlistError", error, addinfo=WEBIF_ERRMSG)
			logUserInfo(self.session, error, timeout=10, webif=True)
			self["footnote"].setText(WEBIF_ERRMSG_TRANS)

	def loadTimerList(self):
		def cmp(a, b):  # Helper function to move finished timers to end of list.
			return (a > b) - (a < b)

		def endCompare(x, y):
			if x[0].state != y[0].state and x[0].state == TimerEntry.StateEnded or y[0].state == TimerEntry.StateEnded:
				return cmp(x[0].state, y[0].state)
			return cmp(x[0].begin, y[0].begin)

		timerlist = []
		timerlist.extend([(timer, False) for timer in self.timerlist if timer.state != 3])
		timerlist.extend([(timer, True) for timer in self.timerlist if timer.state == 3])
		if config.usage.timerlist_finished_timer_position.index:  # End of list.
			timerlist.sort(key=cmp_to_key(endCompare))
		else:
			timerlist.sort(key=lambda x: x[0].begin)
		self["timerlist"].setList(timerlist)
		self.selectionChanged()

	def saveTimers(self):  # override save .. this will be done as callback
		pass

### ADD TIMER ###
	def addTimer(self):
		pass
#		timerObj = {}  TODO: What channel and time should we use ?
#		timerObj = self.createTimer(timerObj, self.index)
#		self.session.openWithCallback(self.addTimerEntryFinished, RemoteTimerEdit, timerObj, self.locations, self.tags, False)

	def addTimerEntryFinished(self, answer):
		if answer and answer[0]:
			edata = answer[1]
			entry = PBtimer(timer=edata)
			cmd = f"{self.baseUrl}/api/timeradd?sRef={entry.service_ref}{entry.timerurldata()}"
			sendAPIcommand(cmd, self.password).addCallback(self.timerDownloadCallback).addErrback(self.timerDownloadError)
		else:
			logUserInfo(self.session, _("Record timer not added."), log=False)

	def timerDownloadCallback(self, jsondict):
		self.updateTimerlist()
		if jsondict and jsondict.get("result", False):
			logUserInfo(self.session, jsondict.get("message", _("No message from box received.")))

### DELETE TIMER ###
	def deleteTimer(self):
		current = self["timerlist"].getCurrent()
		title = ""
		if current:
			title = current.repeated and _("Attention, this is a repeated timer!\n") or ""
		self.session.openWithCallback(self.deleteTimerConfirmed, MessageBox, f'{title}{_("Do you really want to delete the timer?")}\n{current.name}?', MessageBox.TYPE_YESNO, timeout=10, default=False)

	def deleteTimerConfirmed(self, answer):
		if answer:
			current = self["timerlist"].getCurrent()
			if current:
				cmd = f"{self.baseUrl}/api/timerdelete?sRef={current.service_ref}&begin={current.begin}&end={current.end}"
				sendAPIcommand(cmd, self.password).addCallback(self.timerDownloadCallback).addErrback(self.timerDownloadError)

### EDIT TIMER ###
	def editTimer(self):
		current = self["timerlist"].getCurrent()
		if current:
			self.oldbegin = current.begin
			self.oldend = current.end
			self.oldsref = current.service_ref
			self.session.openWithCallback(self.editTimerEntryFinished, RemoteTimerEdit, current, self.locations, self.tags, False)

	def editTimerEntryFinished(self, result=None):
		if result and result[0]:
			edata = result[1]
			entry = PBtimer(timer=edata)
			cmd = f"{self.baseUrl}/api/timerchange?sRef={entry.service_ref}{entry.timerurldata()}&channelOld={self.oldsref}&beginOld={self.oldbegin}&endOld={self.oldend}"
			sendAPIcommand(cmd, self.password).addCallback(self.timerDownloadCallback).addErrback(self.timerDownloadError)
		# else:
		# 	logUserInfo(self.session, _("Record timer not updated."))

### TOGGLE TIMER ###
	def toggleTimer(self):
		current = self["timerlist"].getCurrent()
		if current:
			cmd = f"{self.baseUrl}/api/timertogglestatus?sRef={current.service_ref}&begin={current.begin}&end={current.end}"
			sendAPIcommand(cmd, self.password).addCallback(self.timerDownloadCallback).addErrback(self.timerDownloadError)

### CLEANUP TIMERS ###
	def cleanupTimers(self):
		self.session.openWithCallback(self.cleanupTimersCallback, MessageBox, _("Clean up (delete) all completed timers?"), timeout=10, default=False, close_on_any_key=True, windowTitle=self.getTitle())

	def cleanupTimersCallback(self, answer):
		if answer:
			cmd = f"{self.baseUrl}/api/timercleanup?cleanup=true"
			sendAPIcommand(cmd, self.password).addCallback(self.timerDownloadCallback).addErrback(self.timerDownloadError)

	def timerDownloadError(self, error=None):
		if error:
			logError("timerDownloadError", error, addinfo=WEBIF_ERRMSG)
			logUserInfo(self.session, error, timeout=10, webif=True)
			self["footnote"].setText(WEBIF_ERRMSG_TRANS)

	def getEventDescription(self, timer):  # TODO: Dies ist erst nur mal eine Kopie aus der aktuellen Screens.Timers.py (GIT)
		# timer: RecordTimerEntry(name=Mein leckerer Garten, begin=Mon Feb 19 20:58:00 2024, end=Mon Feb 19 22:05:00 2024, serviceref=1:0:19:2840:41B:1:FFFF0000:0:0:0:, justplay=0, isAutoTimer=0)
		description = timer.description
		event = eEPGCache.getInstance().lookupEventId(timer.service_ref.ref, timer.eit) if timer.eit else None
		if event:
			self["Event"].newEvent(event)
			#
			# This is not in openATV but could be helpful to update the timer description with the actual recording details!
			#
			# shortDescription = event.getShortDescription()
			# if shortDescription and description != shortDescription:
			# 	if description and shortDescription:
			# 		description = "%s %s\n\n%s %s" % (_("Timer:"), description, _("EPG:"), shortDescription)
			# 	elif shortDescription:
			# 		description = shortDescription
			# 		timer.description = shortDescription
			# extendDescription = event.getExtendedDescription()
			# if extendDescription and description != extendDescription:
			# 	description = "%s\n%s" % (description, extendDescription) if description else extendDescription
		return description


class RemoteChannelList(Screen, PartnerboxGlobals):
	skin = """
		<screen name="RemoteChannelList" position="center,center" flags="wfNoBorder" backgroundColor="#200a1232" size="1280,720" resolution="1280,720" title="Partnerbox: Channel List">
			<widget source="Title" render="Label" position="23,8" size="776,40" font="Regular; 27" foregroundColor="white" backgroundColor="#50a1232" valign="center" zPosition="1" transparent="1" />
			<widget source="global.CurrentTime" render="Label" position="820,8" size="440,40" font="Regular; 27" foregroundColor="white" backgroundColor="#50a1232" halign="right" transparent="1" valign="center">
  				<convert type="ClockToText">Format %a.%e %b. %Y %H:%M</convert>
			</widget>
			<widget source="menulist" render="Listbox" position="23,60" size="780,600" scrollbarMode="showOnDemand" foregroundColor="white" backgroundColor="#50a1232" zPosition="1" transparent="1">
  				<convert type="TemplatedMultiContent">
					{"template":
						[  # indexlist:rawdata, sname, title, progress, timeline, btimestr, etimestr, dtimestr, rest
						MultiContentEntryText(pos=(5,2), size=(160,24), font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=1), # servicename
						MultiContentEntryText(pos=(180,2), size=(570,24), font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_ELLIPSIS, text=2), # title
						MultiContentEntryProgress(pos=(5,30), size=(155,10), percent=-3), # percent
						MultiContentEntryText(pos=(180,26), size=(570,24), font=1, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER, text=4)# timeline
						],
						"fonts": [gFont("Regular",20), gFont("Regular",18)],
						"itemHeight":50
					}
				</convert>
			</widget>
			<widget source="ServiceEvent" render="Label" position="823,60" size="433,80" font="Regular;22" halign="center" valign="center" foregroundColor="white" backgroundColor="#50a1232" zPosition="1" transparent="1">
			  <convert type="EventName">Name</convert>
			</widget>
			<widget source="ServiceEvent" render="RunningText" options="movetype=none,startdelay=600,steptime=60,direction=top,startpoint=0,wrap=1,always=0,repeat=2,oneshot=1" position="823,190" size="433,466" font="Regular;20" halign="left" valign="top" foregroundColor="white" backgroundColor="#50a1232" zPosition="1" transparent="1">
			  <convert type="EventName">FullDescription</convert>
			</widget>
			<widget source="footnote" render="Label" position="center,677" size="780,30" font="Regular;24" halign="center" valign="center" foregroundColor="white" backgroundColor="#50a1232" zPosition="1" transparent="1" />
			<widget source="ServiceEvent" render="Label" position="850,153" size="67,20" font="Regular;18" foregroundColor="white" backgroundColor="#50a1232" transparent="1" halign="right" valign="center">
	  			<convert type="EventTime">StartTime</convert>
	  			<convert type="ClockToText">Format:%H:%M</convert>
			</widget>
			<widget source="ServiceEvent" render="Label" position="1163,153" size="67,20" font="Regular;18" foregroundColor="white" backgroundColor="#50a1232" transparent="1" valign="center">
	  			<convert type="EventTime">EndTime</convert>
				<convert type="ClockToText">Format:%H:%M</convert>
			</widget>
			<widget source="ServiceEvent" render="Progress" position="923,160" size="233,8" backgroundColor="#50a1232" foregroundColor="white" zPosition="1" borderWidth="1" borderColor="white">
	  			<convert type="EventTime">Progress</convert>
			</widget>
			<eLabel name="background" position="0,663" size="1280,56" backgroundColor="#1502050e" zPosition="-1" />
			<eLabel name="background" position="15,56" size="1250,605" backgroundColor="#1502050e" zPosition="-2" transparent="1" />
			<eLabel name="background" position="0,54" size="15,609" backgroundColor="#1502050e" zPosition="-3" />
			<eLabel name="background" position="1265,54" size="15,608" backgroundColor="#1502050e" zPosition="-3" />
			<eLabel name="background" position="0,0" size="1280,54" backgroundColor="#1502050e" zPosition="-1" />
			<eLabel name="line" position="823,140" size="433,2" backgroundColor="#c0c0c0" zPosition="3" />
			<eLabel name="line" position="15,52" size="1250,2" backgroundColor="#c0c0c0" zPosition="3" />
			<eLabel name="line" position="15,663" size="1250,2" backgroundColor="#c0c0c0" zPosition="3" />
			<widget source="key_red" render="Label" position="70,680" size="170,26" font="Regular;18" halign="left" valign="center" transparent="1" noWrap="1" zPosition="+1" foregroundColor="white" backgroundColor="#50a1232" objectTypes="key_red,StaticText" />
			<eLabel text="EXIT" position="1206,680" size="50,24" font="Regular;18" zPosition="10" foregroundColor="white" cornerRadius="4" backgroundGradient="#00838383,#009d9d9d,#00b6b6b6, vertical" verticalAlignment="center" horizontalAlignment="center" />
			<eLabel text="OK" position="1136,680" size="50,24" font="Regular;18" zPosition="10" foregroundColor="white" cornerRadius="4" backgroundGradient="#00838383,#009d9d9d,#00b6b6b6, vertical" verticalAlignment="center" horizontalAlignment="center" />
			<eLabel name="button_red" position="23,680" size="40,24"  zPosition="10"  cornerRadius="4" backgroundGradient="#00e60000,#00f75e25,#00ff0088, vertical" verticalAlignment="center" horizontalAlignment="center" />
		</screen>
		"""

	REMOTE_TV_MODE = 1
	REMOTE_TIMER_MODE = 0

	def __init__(self, session, timerlist, sref, configentry, playeronly):
		self.session = session
		self.timerlist = timerlist
		self.sref = sref
		self.configentry = configentry
		self.playeronly = playeronly
		Screen.__init__(self, session, mandatoryWidgets=["menulist", "footnote"])
		title = _("Channel list from: %s") % configentry.name.value
		self.setTitle(title)
		self["menulist"] = List([])
		self["key_red"] = StaticText(_("Zap"))
		self["footnote"] = StaticText()
		self["ServiceEvent"] = PBServiceEvent()

		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions"],
		{
			"ok": self.keyOK,
			"cancel": self.exit,
			"red": self.zapTV,
			"nextBouquet": self.keyPageUp,
			"prevBouquet": self.keyPageDown,
		}, -1)
		self.password = configentry.password.value
		ip = getIPString(configentry)
		self.streamurl = f"http://{ip}:8001/"
		self.baseUrl = getBaseUrl(configentry)
		self.epgcache = eEPGCache.getInstance()
		self.mode = self.REMOTE_TIMER_MODE
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.zaptoservicewhenstreaming = configentry.zaptoservicewhenstreaming.value
		self.zapTimer = eTimer()
		self.zapTimer.callback.append(self.zapTimerFinished)
		self.onClose.append(self.__onClose)
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self["menulist"].onSelectionChanged.append(self.updateScreenElements)
		self.updateChannellist()

	def updateChannellist(self):
		self["footnote"].setText(_("Getting channel information..."))
		self.loadExternalEPGlist(self.sref, self.baseUrl, self.password, self.loadRTepglistCallback)

	def loadRTepglistCallback(self, result):
		self["footnote"].setText("")
		success, epglist = result
		if success:
			self["menulist"].updateList(epglist)
			self.updateScreenElements()
		else:
			self["footnote"].setText(epglist)

	def zapTV(self):
		def zapTVCallback(jsondict=None):
			if self.mode == self.REMOTE_TIMER_MODE:
				self["footnote"].setText(_("Give Enigma time to fill epg cache..."))
				self.zapTimer.start(10000)
			else:
				self.zapTimer.start(3000)
		current = self["menulist"].getCurrent()
		if current:
			self.zap = current[0]
			self.clistidx = self["menulist"].getCurrentIndex()
			sref = self.zap.get("sref", "")
			if sref:
				self["footnote"].setText(f'{_("Zapping to")} {self.zap.get("sname", "")}')
				cmd = f"{self.baseUrl}/api/zap?sRef={sref}"
				sendAPIcommand(cmd, self.password).addCallback(zapTVCallback)

	def zapTimerFinished(self):
		if self.zapTimer.isActive():
			self.zapTimer.stop()
		if self.mode == self.REMOTE_TIMER_MODE:
			self.updateChannellist()
		else:
			self.startStream()

	def keyOK(self):
		current = self["menulist"].getCurrent()
		if current:
			if self.playeronly:
				self.zap = current[0]
				self.playRemoteStream()
			else:
				self.close(current[0])

	def keyPageUp(self):
		self["menulist"].pageUp()

	def keyPageDown(self):
		self["menulist"].pageDown()

	def playRemoteStream(self):
		if self.playeronly:
			if self.mode == self.REMOTE_TIMER_MODE:
				self.mode = self.REMOTE_TV_MODE
				if self.zaptoservicewhenstreaming:
					self.zapTV()
				else:
					self.startStream()
			else:
				if self.oldService:
					self.session.nav.playService(self.oldService)
				else:
					self.session.nav.stopService()
				self.mode = self.REMOTE_TIMER_MODE

	def startStream(self):
		self.session.nav.stopService()
		sref = self.zap.get("sref", "")
		if sref:
			playerRef = eServiceReference(sref)
			playerRef.setName(self.zap.get("sname", ""))
			streamurl = self.streamurl.replace(":8001/", ":17999/") if self.zap.get("streamrelay", False) else self.streamurl
			playerRef.setPath(f"{streamurl}{self.zap.get("sref", "")}")
			self.session.nav.playService(playerRef, adjust=False)
			self.session.openWithCallback(self.playRemoteStream, RemotePlayer, self.zap.get("sname", ""), sref, self.configentry, self.session.current_dialog)

	def updateScreenElements(self):
		current = self["menulist"].getCurrent()
		if current:
			self["ServiceEvent"].setEvent(current[0])

	def __onClose(self):
		if self.zapTimer.isActive():
			self.zapTimer.stop()

	def exit(self):
		self.close(None)


class PBCurrentService(Source):
	def __init__(self):
		Source.__init__(self)
		self.service = None
		self.serviceref = None
		self.info = " "

	def refresh(self, sref):
		if self.serviceref != sref:
			self.service = eServiceReference(sref)
			self.serviceref = sref
			self.changed((self.CHANGED_ALL,))

	def destroy(self):
		Source.destroy(self)


class PBServiceEvent(Source):
	def __init__(self):
		Source.__init__(self)
		self.m_EventName = ""
		self.m_ShortDescription = ""
		self.m_ExtendedDescription = ""
		self.m_Begin = int(time())
		self.m_Duration = 0

	def setEvent(self, event):
		self.m_Begin = event.get("begin_timestamp", 0)
		self.m_Duration = event.get("duration_sec", 0)
		self.m_EventName = unescape(event.get("title", ""))
		self.m_ShortDescription = event.get("shortdesc", "")
		self.m_ExtendedDescription = event.get("longdesc", "")
		self.changed((self.CHANGED_ALL,))

	def getEventName(self):
		return self.m_EventName

	def getShortDescription(self):
		return self.m_ShortDescription

	def getExtendedDescription(self):
		return self.m_ExtendedDescription

	def getBeginTime(self):
		return self.m_Begin

	def getDuration(self):
		return self.m_Duration

	def getEventId(self):
		return 0

	def getBeginTimeString(self):
		return ""

	def getExtraEventData(self):
		return None

	def destroy(self):
		Source.destroy(self)

	@cached
	def getEvent(self):
		return self

	event = property(getEvent)


class RemotePlayer(Screen, InfoBarAudioSelection, PartnerboxGlobals):
	skin = """
		<screen name="RemotePlayer" flags="wfNoBorder" position="0,0" size="1280,720" resolution="1280,720" title="RemotePlayer" backgroundColor="transparent">
			<widget font="Regular;80" foregroundColor="#80C0C0C0" backgroundColor="#050a1232" noWrap="1" position="30,455" render="Label" size="1252,105" source="Name" transparent="1" valign="bottom" zPosition="-30"  borderWidth="1" borderColor="black" shadowColor="black" shadowOffset="-2,-2"/>
			<widget render="RunningText" options="movetype=none,startdelay=900,steptime=1,step=3,direction=left,startpoint=0,wrap=1,always=0,repeat=2,oneshot=1" foregroundColor="#FFFFFF" backgroundColor="#050a1232" font="Regular; 40" halign="left" noWrap="1" position="287,580" size="805,56" source="Event_Now" transparent="1" valign="center">
				<convert type="EventName">Name</convert>
			</widget>
			<widget render="RunningText" options="movetype=none,startdelay=900,steptime=1,step=3,direction=left,startpoint=0,wrap=1,always=0,repeat=2,oneshot=1" font="Regular; 35" foregroundColor="#FFFFFF" backgroundColor="#050a1232" halign="left" noWrap="1" position="287,645" size="805,56" source="Event_Next" transparent="1" valign="center">
				<convert type="EventName">Name</convert>
			</widget>
			<widget alphatest="blend" position="33,574" size="220,132" render="Picon" source="CurrentService" transparent="1" zPosition="4">
				<convert type="ServiceName">Reference</convert>
			</widget>
			<eLabel name="GRADIENT_BACKGROUND" backgroundColor="#3502050e" position="0,560" size="1280,160" zPosition="-10" />
			<widget foregroundColor="#C0C0C0" backgroundColor="#050a1232" font="Regular;19" halign="right" position="1092,588" render="Label" size="75,30" source="Event_Now" transparent="1">
				<convert type="EventTime">StartTime</convert>
				<convert type="ClockToText">Default</convert>
			</widget>
			<eLabel foregroundColor="#C0C0C0" backgroundColor="#050a1232" font="Regular;19" halign="center" position="1173,588" size="15,30" text="-" transparent="1" />
			<widget foregroundColor="#C0C0C0" backgroundColor="#050a1232" font="Regular;19" halign="right" position="1178,588" render="Label" size="60,30" source="Event_Now" transparent="1">
				<convert type="EventTime">EndTime</convert>
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget foregroundColor="#C0C0C0" backgroundColor="#050a1232" font="Regular;19" halign="right" position="1125,610" render="Label" size="113,30" source="Event_Now" transparent="1">
				<convert type="EventTime">Remaining</convert>
				<convert type="RemainingToText"></convert>
			</widget>
			<eLabel backgroundColor="#FFFFFF" name="new eLabel" position="287,640" size="951,1" />
			<widget render="Progress" position="287,636" size="951,9" source="Event_Now" foregroundColor="#15C0C0C0" transparent="1" zPosition="7">
				<convert type="EventTime">Progress</convert>
			</widget>
			<widget foregroundColor="#C0C0C0" backgroundColor="#050a1232" font="Regular;18" halign="right" noWrap="1" position="1092,649" render="Label" size="75,28" source="Event_Next" transparent="1" valign="top">
				<convert type="EventTime">StartTime</convert>
				<convert type="ClockToText">Default</convert>
			</widget>
			<eLabel foregroundColor="#C0C0C0" backgroundColor="#050a1232" font="Regular;18" halign="center" noWrap="1" position="1173,649" size="15,28" text="-" transparent="1" valign="top" />
			<widget foregroundColor="#C0C0C0" backgroundColor="#050a1232" font="Regular;18" halign="right" noWrap="1" position="1178,649" render="Label" size="60,28" source="Event_Next" transparent="1" valign="top">
				<convert type="EventTime">EndTime</convert>
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget foregroundColor="#C0C0C0" backgroundColor="#050a1232" font="Regular;18" halign="right" position="1125,670" render="Label" size="113,28" source="Event_Next" transparent="1">
				<convert type="EventTime">Duration</convert>
				<convert type="ClockToText">InMinutes</convert>
			</widget>
		</screen>
		"""

	def __init__(self, session, title, sref, configentry, parent=None):
		self.session = session
		self.sref = sref
		Screen.__init__(self, session, parent=parent)
		self.setTitle(_("Partnerbox: Remote player"))
		InfoBarAudioSelection.__init__(self)
		self.password = configentry.password.value
		self.baseUrl = getBaseUrl(configentry)
		self["Name"] = StaticText(title)
		self["Event_Now"] = PBServiceEvent()
		self["Event_Next"] = PBServiceEvent()
		self["CurrentService"] = PBCurrentService()
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions", "MoviePlayerActions"],
		{
			"ok": self.showPlayerBar,
			"cancel": self.exit,
			"leavePlayer": self.exit,
			"right": self.nextChannel,
			"left": self.previousChannel,
			"chplus": self.nextChannel,
			"chminus": self.previousChannel,
			"up": self.nextPipService,
			"down": self.prevPipService,
			"red": self.activatePiP,
			"green": self.openServiceList,
		}, -1)
		self.servicelist = InfoBar.instance.servicelist if InfoBar.instance else None
		self.pipZapAvailable = self.servicelist.dopipzap if self.servicelist else False
		self.playerBarTimer = eTimer()
		self.playerBarTimer.callback.append(self.hidePlayerBar)
		self.onClose.append(self.__onClose)
		self.onLayoutFinish.append(self.updateEPGinfo)

	def updateEPGinfo(self):
		def updateEPGinfoError(error=None):
			if error:
				logError("CurrentEPGError", error)

		def updateEPGinfoCallback(jsondict):
			if jsondict:
				events = jsondict.get("events", [{}, {}])[:2]
				self["Event_Now"].setEvent(events[0])
				self["Event_Next"].setEvent(events[1])
				self["CurrentService"].refresh(events[0].get("sref", ""))

		self.isVisible = True
		idx = config.usage.infobar_timeout.index
		self.playerBarTimer.start(idx * 1000 if idx else 6 * 1000)
		cmd = f"{self.baseUrl}/api/epgservicenownext?sRef={self.sref}"
		sendAPIcommand(cmd, self.password).addCallback(updateEPGinfoCallback).addErrback(updateEPGinfoError)

	def openServiceList(self):
		if self.pipZapAvailable and self.servicelist and self.servicelist.dopipzap:
			self.session.execDialog(self.servicelist)

	def activatePiP(self):
		if self.pipZapAvailable:
			dlg = None
			if (BoxInfo.getItem("NumVideoDecoders", 1) > 1) and InfoBar.instance:
				modeslist = []
				keyslist = []
				if InfoBar.pipShown(InfoBar.instance):
					slist = self.servicelist
					if slist:
						modeslist.append((_("Zap focus to main screen") if slist.dopipzap else _("Zap focus to Picture in Picture"), "pipzap"))
						keyslist.append('red')
					modeslist.append((_("Move Picture in Picture"), "move"))
					keyslist.append('green')
					modeslist.append((_("Disable Picture in Picture"), "stop"))
					keyslist.append('blue')
				else:
					modeslist.append((_("Activate Picture in Picture"), "start"))
					keyslist.append('blue')
				dlg = self.session.openWithCallback(self.pipAnswerConfirmed, ChoiceBox, title=_("Choose action:"), list=modeslist, keys=keyslist)
			if dlg:
				dlg.setTitle(_("Menu PiP"))

	def pipAnswerConfirmed(self, answer):
		answer = answer and answer[1]
		if answer:
			if answer == "pipzap":
				InfoBar.togglePipzap(InfoBar.instance)
			elif answer == "move":
				if InfoBar.instance:
					InfoBar.movePiP(InfoBar.instance)
			elif answer == "stop":
				if InfoBar.instance and InfoBar.pipShown(InfoBar.instance):
					slist = self.servicelist
					if slist and slist.dopipzap:
						slist.togglePipzap()
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
				if slist and (not slist.dopipzap and hasattr(self.session, 'pip')):
					InfoBar.togglePipzap(InfoBar.instance)

	def nextPipService(self):
		if self.pipZapAvailable:
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
				slist.zap(enable_pipzap=True)

	def prevPipService(self):
		if self.pipZapAvailable:
			slist = self.servicelist
			if slist and slist.dopipzap:
				if slist.inBouquet():
					prev = slist.getCurrentSelection()
					if prev:
						prev = prev.toString()
						while True:
							if config.usage.quickzap_bouquet_change.value and slist.atBegin():
								slist.prevBouquet()
							slist.moveUp()
							cur = slist.getCurrentSelection()
							if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
								break
				else:
					slist.moveUp()
				slist.zap(enable_pipzap=True)

	def nextChannel(self):
		if self.parent:
			self.parent["menulist"].goLineDown()
			self.restart()

	def previousChannel(self):
		if self.parent:
			self.parent["menulist"].goLineUp()
			self.restart()

	def restart(self):
		current = self.parent["menulist"].getCurrent()
		if current:
			streamurl = self.parent.streamurl
			zap = current[0]
			self.sref = zap.get("sref", "")
			if self.sref:
				self.session.nav.stopService()
				playerRef = eServiceReference(self.sref)
				sname = zap.get("sname", "")
				playerRef.setName(sname)
				self["Name"].setText(sname)
				streamurl = streamurl.replace(":8001/", ":17999/") if zap.get("streamrelay", False) else streamurl
				playerRef.setPath(f"{streamurl}{zap.get("sref", "")}")
				self.session.nav.playService(playerRef, adjust=False)
				self.updateEPGinfo()
				self.show()

	def hidePlayerBar(self):
		if self.playerBarTimer.isActive():
			self.playerBarTimer.stop()
		self.hide()

	def showPlayerBar(self):
		if self.isVisible:
			if self.playerBarTimer.isActive():
				self.playerBarTimer.stop()
			self.hide()
		else:
			self.updateEPGinfo()
			self.show()
		self.isVisible = not self.isVisible

	def __onClose(self):
		if self.playerBarTimer.isActive():
			self.playerBarTimer.stop()

	def exit(self):
		self.session.nav.stopService()
		self.close()


class PartnerboxSettings(Setup):
	def __init__(self, session, args=None):
		Setup.__init__(self, session, "partnerbox", plugin="Extensions/Partnerbox", PluginLanguageDomain="Partnerbox")
		self.setTitle(_("Partnerbox: Setup"))
		self["key_yellow"] = StaticText(_("Partnerboxes"))
		self["key_blue"] = StaticText("")
		self["selectEntriesActions"] = HelpableActionMap(self, ["ColorActions"],
		{
			"yellow": (self.keyYellow, _("Partnerbox entries")),
			"blue": (self.keyBlue, _("EPG refresh"))
		}, prio=0, description=_("Partnerbox Setup Actions"))
		self.onLayoutFinish.append(self.refreshKeyBlue)

	def refreshKeyBlue(self):
		text = ""
		for index, configentry in enumerate(config.plugins.Partnerbox.Entries):
			if configentry.epg.value:
				text = _("EPG refresh")
				break
		self["key_blue"].setText(text)

	def keyBlue(self):
		for index, configentry in enumerate(config.plugins.Partnerbox.Entries):
			if configentry.epg.value:
				pbAutopoller.runEpgTimerUpdate(index)

	def keyYellow(self):
		def partnerboxEntriesCallback(result=None):
			self.refreshKeyBlue()
			pbAutopoller.updateRefreshtimes()

		self.session.openWithCallback(partnerboxEntriesCallback, PartnerboxEntriesListConfigScreen)


class PartnerboxCommonScreen(Screen):
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skinName = "Setup"
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["footnote"] = Label()
		self["description"] = Label()
		self["config"] = MenuList([])

	def createSummary(self):
		return ScreenSummary


class PartnerboxEntriesListConfigScreen(PartnerboxCommonScreen, PartnerboxGlobals):
	def __init__(self, session, what=None):
		self.session = session
		self.what = what
		PartnerboxCommonScreen.__init__(self, session)
		self.skinName = "Setup"
		self.setTitle(_("Partnerbox: List of partnerboxes"))
		self["key_red"] = StaticText(__("Cancel"))
		self["key_green"] = StaticText(_("Add"))
		self["key_blue"] = StaticText(__("Power"))
		self["key_yellow"] = StaticText(_("Delete"))

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.keyOK,
			"cancel": self.close,
			"red": self.close,
			"blue": self.powerMenu,
			"yellow": self.keyDelete,
			"green": self.keyAdd,
		}, -1)
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self.refreshBoxList()

	def refreshBoxList(self):
		boxlist = []
		self["footnote"].setText(_("Loading partnerboxes"))
		for rawdata in config.plugins.Partnerbox.Entries:
			name = rawdata.name.value
			ip = ".".join(map(str, rawdata.ip.value))
			port = str(rawdata.port.value)
			boxlist.append((f"{name}\t{ip}\t{port}", rawdata))
		self["config"].setList(boxlist)
		self["footnote"].setText("")

	def keyAdd(self):
		def addBoxCallback(entry=None):
			if entry:
				config.plugins.Partnerbox.Entries[entry.index.value] = entry
			else:
				config.plugins.Partnerbox.Entries.remove(current)
			config.plugins.Partnerbox.Entries.save()
			config.plugins.Partnerbox.entriescount.value = len(config.plugins.Partnerbox.Entries)
			config.plugins.Partnerbox.entriescount.save()
			config.plugins.Partnerbox.save()
			configfile.save()
			pbAutopoller.runTimerListUpdate()
			self.refreshBoxList()

		current = initPartnerboxEntryConfig(config.plugins.Partnerbox.entriescount.value)
		self.session.openWithCallback(addBoxCallback, PartnerboxEntryConfig, current, addNew=True)

	def keyOK(self):
		def editBoxCallback(entry=None):
			if entry:
				config.plugins.Partnerbox.Entries[current[1].index.value] = entry
				config.plugins.Partnerbox.Entries.save()
				config.plugins.Partnerbox.save()
				configfile.save()
				self.refreshBoxList()
		current = self["config"].getCurrent()
		if current:
			self.session.openWithCallback(editBoxCallback, PartnerboxEntryConfig, current[1])

	def keyDelete(self):
		current = self["config"].getCurrent()
		if current:
			self.session.openWithCallback(self.deleteEntryConfirmed, MessageBox, _("Do you really want to remove this partnerbox from list?"), MessageBox.TYPE_YESNO, timeout=5, default=False)

	def deleteEntryConfirmed(self, answer):
		if answer:
			current = self["config"].getCurrent()
			if current:
				config.plugins.Partnerbox.entriescount.value -= 1
				config.plugins.Partnerbox.entriescount.save()
				config.plugins.Partnerbox.Entries.remove(current[1])
				config.plugins.Partnerbox.Entries.save()
				config.plugins.Partnerbox.save()
				configfile.save()
				logUserInfo(self.session, _("Box was successfully removed!"))
				self.refreshBoxList()

	def powerMenu(self):
		current = self["config"].getCurrent()
		if current:
			menu = []
			menu.append((__("Wake up"), 0))
			menu.append((__("Standby"), 1))
			menu.append((__("Restart"), 2))
			menu.append((__("Restart GUI"), 3))
			menu.append((_("Toggle Standby"), 4))
			menu.append((__("Deep Standby"), 5))
			self.session.openWithCallback(self.menuCallback, ChoiceBox, title=(_("Select operation for") + ": " + "%s" % (current[1].name.value)), list=menu)

	def menuCallback(self, choice):
		if choice:
			current = self["config"].getCurrent()
			if current:
				password = current[1].password.value
				baseUrl = getBaseUrl(current[1])
				selection = {0: "4", 1: "5", 2: "3", 3: "2", 4: "0", 5: "1"}.get(choice[1], None)
				if selection:
					cmd = f"{baseUrl}/api/powerstate?newstate={selection}"
					sendAPIcommand(cmd, password)


class PartnerboxEntryConfig(Setup, PartnerboxGlobals):
	def __init__(self, session, entry, addNew=False):
		self.addNew = addNew
		self.entry = entry
		Setup.__init__(self, session, "partnerboxconfig", plugin="Extensions/Partnerbox", PluginLanguageDomain="Partnerbox")
		self["key_yellow"] = StaticText(_("Boxsearch"))
		self["entryActions"] = HelpableActionMap(self, ["ColorActions"],
		{
			"yellow": (self.searchBox, _("Boxsearch"))
		}, prio=0, description=_("Partnerbox Entry Actions"))

	def keySave(self):
		self.close(self.entry)

	def keyCancel(self):
		self.close()

	def searchBox(self):
		self.session.openWithCallback(self.searchBoxCallback, PartnerboxBoxSearch)

	def searchBoxCallback(self, result):
		boxname, boxip = result
		if boxname and boxip:
			self.entry.name.value = boxname
			self.entry.ip.value = boxip


class PartnerboxBoxSearch(PartnerboxCommonScreen):
	def __init__(self, session):
		PartnerboxCommonScreen.__init__(self, session)
		self.setTitle(_("Partnerbox: Boxes found in network"))
		self["key_red"] = StaticText(__("Cancel"))
		self["key_yellow"] = StaticText(_("Upper/lower case"))
		self["key_green"] = StaticText(_("Take over"))
		self.uppercase = False
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.keyOK,
			"red": self.exit,
			"green": self.keyOK,
			"yellow": self.keyYellow,
			"cancel": self.exit
		}, -1)
		self.onLayoutFinish.append(self.getPeerBoxList)

	def getPeerBoxList(self):
		self["footnote"].setText(_("Searching for active and standby boxes in peer-to-peer network..."))
		self.boxlist = []
		for streamurl in getPeerStreamingBoxes():  # example streamurls: ['http://gbue4k.local:8001', 'http://sf8008.local:8001']
			url = streamurl[:streamurl.rfind(":")]
			url = url[url.find("//") + 2:]
			try:
				ip = gethostbyname(url)
			except gaierror:
				ip = None
			if ip and int(ip.split(".")[0]):
				found = False
				for configentry in config.plugins.Partnerbox.Entries:
					if ip == getIPString(configentry):
						found = True
						break
				foundmsg = _("already installed") if found else _("not installed yet")
				self.boxlist.append((f"{url.replace(".local", "")}\t{ip}\t\t({foundmsg})", found))
		self["config"].setList(self.boxlist)

	def keyYellow(self):
		boxlist = self["config"].getList()
		newboxlist = []
		for element in list(boxlist):
			items = element[0].split("\t")
			name = items[0].lower() if self.uppercase else items[0].upper()
			newboxlist.append((f"{name}\t{items[1]}\t\t{items[3]}", element[1]))
		boxlist = newboxlist[:]
		self["config"].setList(boxlist)
		self.uppercase = not self.uppercase

	def keyOK(self):
		current = self["config"].getCurrent()
		if current[1]:
			logUserInfo(self.session, _("This box is already installed!"))
			result = (None, None)
		else:
			entry = current[0].split("\t")
			iplist = [int(ip) for ip in entry[1].split(".") if ip.isdigit()]
			result = (entry[0], iplist) if len(iplist) == 4 else (None, None)
		self.close(result)

	def exit(self):
		self.close((None, None))


# RecordTimer override functions

def setRemoteTimers(self, timerList, remoteIndex=0):
	if remoteIndex:
		self.remoteTimers[remoteIndex] = timerList


def getTimers(self, service):
	remoteTimerIndex = getIndexFromSref(service) + 1  # this index must be start with 1 so add 1
	if remoteTimerIndex:
		service = ":".join(service.split(":")[:10]) + ":"
		return [timer for timer in self.remoteTimers.get(remoteTimerIndex, []) if timer.serviceRefString == service]
	else:
		return [timer for timer in self.timer_list if timer.serviceRefString == service]

# EPGSelection override functions


def partnerboxgetRecordEvent(self, serviceRefStr, event):
	foundIndex = getIndexFromSref(serviceRefStr)
	if foundIndex is None:  # is not a listed remote box
		if originalEPGSelectiongetRecordEvent:
			return originalEPGSelectiongetRecordEvent(self, serviceRefStr, event)
	else:
		remoteTimerIndex = foundIndex + 1  # this index must be start with 1 so add 1
		recordEvent = None
		eventID = event.getEventId()
		for timer in [x for x in self.session.nav.RecordTimer.remoteTimers.get(remoteTimerIndex, []) if x.eit == eventID]:
			if timer.service_ref.ref.toCompareString() == ":".join(serviceRefStr.split(":")[:10]) + ":":
				recordEvent = timer
				break
		else:
			if self.session.nav.isRecordTimerImageStandard:
				isInTimer = self.session.nav.RecordTimer.isInTimer(eventID, event.getBeginTime(), event.getDuration(), serviceRefStr, True)
				if isInTimer and isInTimer[1] in (2, 7, 12):
					recordEvent = isInTimer[3]
		return recordEvent


def partnerboxEPGSelectionRecordTimerQuestion(self, manual=False):
	def setOldValues(timer):
		self.oldbegin = timer.begin
		self.oldend = timer.end
		self.oldsref = timer.service_ref

	def actionRemoteTimerEnd(entry, action, jsondict):
		message = _("No message from box received.")
		if jsondict:
			if jsondict.get("result", False):
				timerObj = jsondict.get("timer")
				if timerObj or action in (ACTION_TOGGLE, ACTION_REMOVE):
					timerData = remoteTimersData.timerData.get(index)
					pbGlobals = PartnerboxGlobals(None)
					timerObj = timerObj and pbGlobals.createTimer(timerObj, index)
					if timerData:
						timerList = timerData[0]
						if action != ACTION_ADD:
							foundTimer = None
							for oldTimer in timerList:
								if oldTimer.begin == self.oldbegin and oldTimer.end == self.oldend and oldTimer.service_ref == self.oldsref:
									foundTimer = oldTimer
									break
							if foundTimer:
								if action == ACTION_TOGGLE:
									foundTimer.disabled = not foundTimer.disabled
								else:
									timerList.remove(foundTimer)
						if timerObj:
							timerList.append(timerObj)
						remoteTimersData.setTimerData(index, timerList, timerData[1], timerData[2], timerData[3])
						self.session.nav.RecordTimer.setRemoteTimers(timerList, index + 1)
						self.setTimerButtonText("" if action == ACTION_REMOVE else __("Change Timer"))
						self.refreshlist()
						message = ""   # supress success message
			else:
				message = jsondict.get("message")
		if message:
			logUserInfo(self.session, message)

	def actionRemoteTimerFinished(action, answer):
		if answer and answer[0]:
			entry = answer[1]
			refstr, ip, port, baseUrl = getRefstrIpPort(sref)
			if ip and port:
				configentry = config.plugins.Partnerbox.Entries[entry.index]
				if action == ACTION_ADD:
					cmd = f"{baseUrl}/api/timeradd?sRef={refstr}{entry.timerurldata()}&returntimer=1"
					sendAPIcommand(cmd, configentry.password.value).addCallback(boundFunction(actionRemoteTimerEnd, entry, action)).addErrback(boundFunction(actionRemoteTimerError, action))
				elif action == ACTION_EDIT:
					entry = PBtimer(timer=entry)
					cmd = f"{baseUrl}/api/timerchange?sRef={refstr}{entry.timerurldata()}&channelOld={self.oldsref}&beginOld={self.oldbegin}&endOld={self.oldend}&returntimer=1"
					sendAPIcommand(cmd, configentry.password.value).addCallback(boundFunction(actionRemoteTimerEnd, entry, action)).addErrback(boundFunction(actionRemoteTimerError, action))
				elif action == ACTION_REMOVE:
					cmd = f"{baseUrl}/api/timerdelete?sRef={refstr}&begin={entry.begin}&end={entry.end}"
					sendAPIcommand(cmd, configentry.password.value).addCallback(boundFunction(actionRemoteTimerEnd, entry, action)).addErrback(boundFunction(actionRemoteTimerError, action))
				elif action == ACTION_TOGGLE:
					cmd = f"{baseUrl}/api/timertogglestatus?sRef={refstr}&begin={timer.begin}&end={timer.end}"
					sendAPIcommand(cmd, configentry.password.value).addCallback(boundFunction(actionRemoteTimerEnd, entry, action)).addErrback(boundFunction(actionRemoteTimerError, action))

	def actionRemoteTimerError(action, error):
		if error:
			logError(f"actionRemoteTimerError:{action}", error, addinfo=WEBIF_ERRMSG)
			logUserInfo(self.session, error, timeout=10, webif=True)

	def editRemoteTimer(timer):
		timerdata = remoteTimersData.timerData.get(index, ([], [], [], ""))
		locations = timerdata[1]
		tags = timerdata[2]
		setOldValues(timer)
		self.session.openWithCallback(boundFunction(actionRemoteTimerFinished, ACTION_EDIT), RemoteTimerEdit, timer, locations, tags, False)

	def addRemoteTimer():
		eit = event.getEventId()
		name = event.getEventName()
		description = event.getShortDescription() or event.getExtendedDescription()
		eventBegin = event.getBeginTime()
		eventEnd = eventBegin + event.getDuration()
		marginbefore = getattr(config.recording, "margin_before").value * 60
		marginafter = getattr(config.recording, "margin_after").value * 60
		timerdata = remoteTimersData.timerData.get(index, ([], [], [], None))
		locations = timerdata[1]
		tags = timerdata[2]
		default = timerdata[3]
		if default:  # : Add full serviceref to PBtimer if local timer needed .. this is currently disabled
			timerentry = PBtimer(service_ref=sref, eit=eit, name=name, description=description, eventBegin=eventBegin, eventEnd=eventEnd,
								marginBefore=marginbefore, marginAfter=marginafter, dirname=default, index=index)
			self.session.openWithCallback(boundFunction(actionRemoteTimerFinished, ACTION_ADD), RemoteTimerEdit, timerentry, locations, tags, False)

	def removeRemoteTimer(timer):
		setOldValues(timer)
		timerentry = PBtimer(service_ref=sref, begin=timer.begin, end=timer.end, index=index)
		self.session.openWithCallback(boundFunction(removeTimerConfirmed, timerentry), MessageBox, f'{__("Do you really want to delete this timer?")}\n{timer.name}?', MessageBox.TYPE_YESNO, timeout=5, default=False)

	def removeTimerConfirmed(timerentry, answer):
		if answer:
			actionRemoteTimerFinished(ACTION_REMOVE, (True, timerentry))

	def toggleRemoteTimer(timer):
		setOldValues(timer)
		timerentry = PBtimer(service_ref=sref, begin=timer.begin, end=timer.end, index=index)
		actionRemoteTimerFinished(ACTION_TOGGLE, (True, timerentry))

	ACTION_ADD = 0
	ACTION_EDIT = 1
	ACTION_REMOVE = 2
	ACTION_TOGGLE = 3

	cur = self[f"list{self.activeList}"].getCurrent()
	event = cur[0]
	sref = cur[1]
	if event:
		index = getIndexFromSref(sref)
		if index != -1:  # is a listed remote box
			foundtimer = self.getRecordEvent(str(sref), event)
			if foundtimer:
				timer = foundtimer
				cb_func1 = lambda ret: removeRemoteTimer(timer)
				cb_func2 = lambda ret: editRemoteTimer(timer)
				cb_func3 = lambda ret: toggleRemoteTimer(timer)
				menu = [
						(__("Delete Timer"), "CALLFUNC", self.RemoveChoiceBoxCB, cb_func1),
						(__("Edit Timer"), "CALLFUNC", self.RemoveChoiceBoxCB, cb_func2)
						]
				if not timer.isRunning():
					enableDisable = _("Enable Timer") if timer.disabled else _("Disable Timer")
					menu.append((enableDisable, "CALLFUNC", self.RemoveChoiceBoxCB, cb_func3))
				title = __("Select action for timer %s:") % event.getEventName()
				self.ChoiceBoxDialog = self.session.instantiateDialog(ChoiceBox, text=title, choiceList=menu, buttonList=["red", "green", "yellow", "blue"], skinName="RecordTimerQuestion")
				serviceRef = eServiceReference(str(self[f"list{self.activeList}"].getCurrent()[1]))
				pos = self[f"list{self.activeList}"].getSelectionPosition(serviceRef, self.activeList)
				posX = max(self.instance.position().x() + pos[0] - self.ChoiceBoxDialog.instance.size().width(), 0)
				posY = self.instance.position().y() + pos[1]
				posY += self[f"list{self.activeList}"].itemHeight - 2
				if posY + self.ChoiceBoxDialog.instance.size().height() > 720:
					posY -= self[f"list{self.activeList}"].itemHeight - 4 + self.ChoiceBoxDialog.instance.size().height()
				self.ChoiceBoxDialog.instance.move(ePoint(int(posX), int(posY)))
				self.showChoiceBoxDialog()
			else:
				addRemoteTimer()
			return
	if originalEPGSelectionRecordTimerQuestion:
		originalEPGSelectionRecordTimerQuestion(self, manual)


def partnerboxChannelContextMenuInit():
	global originalChannelContextMenu__init__
	if originalChannelContextMenu__init__ is None:
		originalChannelContextMenu__init__ = ChannelContextMenu.__init__
	ChannelContextMenu.__init__ = partnerboxChannelContextMenu__init__
	ChannelContextMenu.addPartnerboxService = addPartnerboxService
	ChannelContextMenu.callbackPartnerboxServiceList = callbackPartnerboxServiceList
	ChannelContextMenu.startAddPartnerboxService = startAddPartnerboxService
	ChannelContextMenu.setPartnerboxService = setPartnerboxService
	ChannelContextMenu.setParentalControlPin = setParentalControlPin
	ChannelContextMenu.parentalControlPinEntered = parentalControlPinEntered

# ChannelContextMenu override functions


def partnerboxChannelContextMenu__init__(self, session, csel):
	self.session = session
	if originalChannelContextMenu__init__:
		originalChannelContextMenu__init__(self, session, csel)
	if config.plugins.Partnerbox.enablepartnerboxchannelselector.value:
		if csel.mode == MODE_TV:
			current_root = csel.getRoot()
			current = csel.getCurrentSelection()
			inbouquetlist = current_root and current_root.getPath().find('FROM BOUQUET "bouquets.') != -1
			inbouquet = csel.getMutableList()
			if csel.bouquet_mark_edit == OFF and not csel.movemode:
				if not inbouquetlist and inbouquet and current and current.valid():
					callfunction = self.setParentalControlPin if config.ParentalControl.configured.value else self.addPartnerboxService
					self["menu"].list.insert(1, ChoiceEntryComponent("dummy", (_("Add Partnerbox Channels"), boundFunction(callfunction, 0))))
				if (not inbouquetlist and not inbouquet) or inbouquetlist:
					if config.usage.multibouquet.value:
						callfunction = self.setParentalControlPin if config.ParentalControl.configured.value else self.addPartnerboxService
						self["menu"].list.insert(1, ChoiceEntryComponent("dummy", (_("Add Partnerbox Bouquets"), boundFunction(callfunction, 1))))


def isPBservice(session, refstr):
	if refstr.startswith("1:134:"):
		logUserInfo(session, _("Alternative bouquets/services are not supported!"))
		return False
	if refstr.startswith("1:0:0:0:0:0:0:0:0:0:"):
		logUserInfo(session, _("Partnerbox is currently streaming from media and this cannot be forwarded!"))
		return False
	if "3a//" in refstr.lower():
		logUserInfo(session, _("Partnerbox is currently streaming from internet and this cannot be forwarded!"))
		return False
	return True


def addPartnerboxService(self, inserttype):  # inserttypes: 0= Service, 1=Bouquet
	if config.plugins.Partnerbox.entriescount.value == 1:  # if only one box is listed in config
		self.startAddPartnerboxService(inserttype, 0)
	else:  # selection list if several boxes are available
		self.session.openWithCallback(boundFunction(self.startAddPartnerboxService, inserttype), MessageBox, _("Partnerbox: List of partnerboxes"), list=getBoxList(), timeout=10, default=0)


def startAddPartnerboxService(self, inserttype, answer):
	if answer is not False:  # don't change: desired answer can be '0', 'False' if cancel
		configentry = config.plugins.Partnerbox.Entries[answer]
		self.session.openWithCallback(self.callbackPartnerboxServiceList, BouquetChoiceBox, configentry, inserttype)
	else:
		self.close()


def callbackPartnerboxServiceList(self, result):
	if result and result[1]:
		configentry = result[2]
		if result[0] == 0:  # is service, e.g. result=(0, ([], <Partnerbox.plugin.PBepg object at 0xa67de828>), <Components.config.ConfigSubsection object at 0xb01c5498>)
			item = result[1][1]
			if item and item.sref and isPBservice(self.session, item.sref):
				mutablelist = self.csel.getMutableList(self.csel.getRoot())
				if mutablelist:
					service = self.setPartnerboxService(item, configentry)
					if not mutablelist.addService(service):
						self.csel.bouquetNumOffsetCache = {}
						mutablelist.flushChanges()
						self.csel.servicelist.addService(service)
						logUserInfo(self.session, _("Service '%s' successfully added from '%s'.") % (item.sname, configentry.name.value))
					else:
						logUserInfo(self.session, _("Service '%s' from '%s' was already added.") % (item.sname, configentry.name.value))
		elif result[0] == 1:  # is bouquet, e.g. result=(1, ([<Partnerbox.plugin.PBepg object at 0xa6003210>, ...], <Partnerbox.plugin.PBepg object at 0xa6052cc0>), <Components.config.ConfigSubsection object at 0xb015c528>)
			bouquet = result[1][1]
			if bouquet:
				services = []
				for item in result[1][0]:
					if item.sref.startswith("1:134:") or item.sref.startswith("1:0:0:0:0:0:0:0:0:0:") or "3a//" in item.sref.lower():
						continue
					services.append(self.setPartnerboxService(item, configentry))
				self.csel.addBouquet(f"{bouquet.sname.replace('(TV)', '')} {configentry.name.value}", services)
				logUserInfo(self.session, _("Bouquet '%s' successfully added from '%s'.") % (bouquet.sname, configentry.name.value))
	self.close()


def setParentalControlPin(self, inserttype):
	self.session.openWithCallback(boundFunction(self.parentalControlPinEntered, inserttype), PinInput, pinList=[config.ParentalControl.servicepin[0].value],
									triesEntry=config.ParentalControl.retries.servicepin, title=__("Enter the service pin"), windowTitle=__("Change pin code"))


def parentalControlPinEntered(self, inserttype, result):
	if result:
		self.addPartnerboxService(inserttype)
	else:
		logUserInfo(self.session, __("The pin code you entered is wrong."))


# replacement of getService() in PiconsUpdater
def getServicePB(service, excludeiptv):
	sref = service.toString()
	if "%" in sref:
		name = service.getName()
		for configentry in config.plugins.Partnerbox.Entries:
			if getIPString(configentry) in sref:
				name = name[:name.rfind("(")].strip()
				break
		fields = sref.split(':', 10)[:10]
		if not excludeiptv or fields[0] == '1':
			sref = ':'.join(fields) + ':'
			newService = ServiceReference(sref)
			newService.ref.setName(name)
			return newService
		else:
			return None
	else:
		return ServiceReference(service)


def partnerboxPiconUpdaterInit():
	BoxInfo.setItem("getServiceHook", getServicePB)


def partnerboxpluginStart(session, what):
	if config.plugins.Partnerbox.entriescount.value:
		if config.plugins.Partnerbox.entriescount.value == 1:  # if only one box is listed
			partnerboxplugin(session, what, config.plugins.Partnerbox.Entries[0])
		else:  # selection list if several boxes are available
			session.openWithCallback(boundFunction(partnerboxpluginCallback, session, what), MessageBox, _("Partnerbox: List of partnerboxes"), list=getBoxList(), timeout=10, default=0)


def partnerboxpluginCallback(session, what, answer):
	if answer is not False:  # don't change: desired answer can be '0', 'False' if cancel
		configentry = config.plugins.Partnerbox.Entries[answer]
		partnerboxplugin(session, what, configentry)


def partnerboxplugin(session, what, configentry=None):
	if configentry:
		if what == 0:  # CurrentRemoteTV
			session.open(CurrentRemoteTV, configentry)
		elif what == 1:  # RemoteTV
			session.open(BouquetChoiceBox, configentry, 2)
		elif what == 2:  # RemoteTimer
			session.open(RemoteTimerOverview, configentry)


def partnerbox_EPGSelectionInit():
	global originalEPGSelectionRecordTimerQuestion, originalEPGSelectiongetRecordEvent
	if originalEPGSelectionRecordTimerQuestion is None:
		originalEPGSelectionRecordTimerQuestion = EPGSelection.RecordTimerQuestion
		EPGSelection.RecordTimerQuestion = partnerboxEPGSelectionRecordTimerQuestion
		originalEPGSelectiongetRecordEvent = EPGSelection.getRecordEvent
		EPGSelection.getRecordEvent = partnerboxgetRecordEvent


def sessionStart_EPGList(reason, **kwargs):
	if "session" in kwargs:
		partnerbox_EPGSelectionInit()


def setup(session, **kwargs):
	session.open(PartnerboxSettings)


def currentremotetv(session, **kwargs):
	partnerboxpluginStart(session, 0)


def remotetvplayer(session, **kwargs):
	partnerboxpluginStart(session, 1)


def main(session, **kwargs):
	partnerboxpluginStart(session, 2)


def timermenu(menuid, **kwargs):
	return [("Partnerbox: RemoteTimer", main, "partnerbox", None)] if menuid == "timermenu" else []


def sessionstart(reason, **kwargs):
	if reason == 0 and "session" in kwargs:
		session = kwargs["session"]
		partnerboxChannelContextMenuInit()
		partnerboxPiconUpdaterInit()
		pbAutopoller.session = session
		pbAutopoller.startPoller()
	if reason == 1:  # End
		pbAutopoller.stopPoller()


def autostart(reason, **kwargs):
	if reason == 0:  # needs to be done here before RecordTimer init
		RecordTimer.setRemoteTimers = setRemoteTimers
		RecordTimer.getTimers = getTimers
		RecordTimer.remoteTimers = {}


def Plugins(**kwargs):
	clist = [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart, needsRestart=False)]
	clist.append(PluginDescriptor(name=_("Partnerbox: RemoteTimer"), description=_("Manage timer for other boxes in network"), where=PluginDescriptor.WHERE_MENU, fnc=timermenu))

	if config.plugins.Partnerbox.enablepartnerboxepglist.value:
		clist.append(PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionStart_EPGList))
		clist.append(PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart))

	if config.plugins.Partnerbox.showremotetvinextensionsmenu.value:
		clist.append(PluginDescriptor(name=_("Partnerbox: RemoteTV Player"), description=_("Stream TV from your partnerbox"), where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=remotetvplayer))
	if config.plugins.Partnerbox.showcurrentstreaminextensionsmenu.value:
		clist.append(PluginDescriptor(name=_("Partnerbox: Stream current RemoteChannel"), description=_("Stream current channel from partnerbox"), where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=currentremotetv))
	clist.append(PluginDescriptor(name=_("Partnerbox"), description=_("Setup for Partnerbox"), where=[PluginDescriptor.WHERE_PLUGINMENU], icon="logo.png", fnc=setup))
	return clist
