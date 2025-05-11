from __future__ import print_function
#####################################################
# TVCharts Plugin for Enigma2 Dreamboxes
# Coded by Homey (c) 2011
#
# Version: 1.5
# Support: www.i-have-a-dreambox.com
#####################################################
from Components.About import about
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config, configfile, getConfigListEntry, ConfigSubsection, ConfigYesNo, ConfigInteger
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Network import iNetwork
from Components.ServiceEventTracker import ServiceEventTracker
from Components.SystemInfo import BoxInfo
from Components.Sources.StaticText import StaticText
from Components.UsageConfig import preferredTimerPath
from RecordTimer import RecordTimerEntry, parseEvent
from ServiceReference import ServiceReference
from Screens.EventView import EventViewSimple
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Setup import SetupSummary
from Screens.TimerEntry import TimerEntry
from Screens.TimerEdit import TimerSanityConflict
from Tools.Directories import fileExists, SCOPE_ACTIVE_SKIN, resolveFilename
from Plugins.Plugin import PluginDescriptor

from enigma import eTimer, eEPGCache, loadPNG, eListboxPythonMultiContent, gFont, eServiceReference, eServiceCenter, iPlayableService, BT_SCALE
from random import randint
from os import system as os_system
from time import time, gmtime, strftime
from twisted.web.client import getPage
from xml.dom.minidom import parse, parseString
from six.moves.urllib.parse import urlencode
import six
import timer
import xml.etree.cElementTree
import Screens.Standby

##############################
#####  CONFIG SETTINGS   #####
##############################
config.plugins.tvcharts = ConfigSubsection()
config.plugins.tvcharts.enabled = ConfigYesNo(default=True)
config.plugins.tvcharts.maxentries = ConfigInteger(default=10, limits=(5, 100))
config.plugins.tvcharts.maxtimerentries = ConfigInteger(default=10, limits=(5, 100))
config.plugins.tvcharts.submittimers = ConfigYesNo(default=True)
config.plugins.tvcharts.submitplugins = ConfigYesNo(default=True)
config.plugins.tvcharts.bouquetfilter = ConfigYesNo(default=True)

##########################################################
session = []

#Channellist Menu Entry


class ChannelListMenu(MenuList):
	def __init__(self, list, enableWrapAround=False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 24))
		self.l.setFont(1, gFont("Regular", 20))
		self.l.setFont(2, gFont("Regular", 16))
		self.l.setItemHeight(76)


def ChannelListEntryComponent(type, channelname, serviceref, eventid, eventname, starttime, endtime, usercount, percent):
	res = [(serviceref, eventid)]

	# PIXMAP / PICON
	pixmap = resolveFilename(SCOPE_ACTIVE_SKIN, "picon_default.png")
	searchPaths = ('/usr/share/enigma2/picon/', '/media/cf/picon/', '/media/usb/picon/')

	srefstring = serviceref
	pos = srefstring.rfind(':')
	if pos != -1:
		srefstring = srefstring[:pos].rstrip(':').replace(':', '_')
		for path in searchPaths:
			pngname = path + srefstring + ".png"
			if fileExists(pngname):
				pixmap = pngname

	# Build Menu
	if type == "tvcharts":
		res.append(MultiContentEntryPixmapAlphaTest(pos=(8, 8), size=(100, 60), png=loadPNG(pixmap), flags=BT_SCALE))
		res.append(MultiContentEntryText(pos=(130, 5), size=(480, 30), font=0, text="%s (Viewer: %s)" % (channelname, usercount)))
		res.append(MultiContentEntryText(pos=(130, 35), size=(480, 25), font=1, text=eventname))
	elif type == "timercharts":
		res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 10), size=(100, 60), png=loadPNG(pixmap), flags=BT_SCALE))
		res.append(MultiContentEntryText(pos=(130, 5), size=(480, 28), font=0, text="%s (User: %s)" % (channelname, usercount)))
		res.append(MultiContentEntryText(pos=(130, 33), size=(480, 25), font=1, text=eventname))
		res.append(MultiContentEntryText(pos=(130, 57), size=(480, 20), font=2, text="%s Uhr - %s Uhr (%smin)" % (strftime("%d.%m.%Y %H:%M", gmtime(starttime)), strftime("%H:%M", gmtime(endtime)), int((endtime - starttime) / 60))))
	elif type == "moviecharts":
		res.append(MultiContentEntryPixmapAlphaTest(pos=(8, 8), size=(100, 60), png=loadPNG(pixmap), flags=BT_SCALE))
		res.append(MultiContentEntryText(pos=(130, 5), size=(480, 30), font=0, text=eventname))
		res.append(MultiContentEntryText(pos=(130, 33), size=(480, 25), font=1, text="Viewer: %s" % (usercount)))
		res.append(MultiContentEntryText(pos=(130, 57), size=(480, 20), font=2, text="%s Uhr - %s" % (strftime("%d.%m.%Y %H:%M", gmtime(starttime)), channelname)))

	return res

##############################
#####   TV Charts MAIN   #####
##############################


class TVChartsMain(Screen):

	skin = """
	<screen position="center,center" size="620,510" title="TV Charts">
		<widget name="channellist" position="10,10" zPosition="1" size="600,458" scrollbarMode="showOnDemand" />
		<widget name="info" position="0,447" zPosition="2" size="620,20" font="Regular;18" noWrap="1" foregroundColor="#ffffff" transparent="1" halign="center" valign="center" />
		<ePixmap name="red"    position="22,470"  zPosition="3" size="140,40" pixmap="/usr/share/enigma2/skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap name="green"  position="167,470" zPosition="3" size="140,40" pixmap="/usr/share/enigma2/skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap name="yellow" position="312,470" zPosition="3" size="140,40" pixmap="/usr/share/enigma2/skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap name="blue"   position="457,470" zPosition="3" size="140,40" pixmap="/usr/share/enigma2/skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="22,470" zPosition="4" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="167,470" zPosition="4" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="312,470" zPosition="4" size="140,40" valign="center" halign="center"  font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="457,470" zPosition="4" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self.session = session

		self["channellist"] = ChannelListMenu([])
		self["info"] = Label()

		self["key_red"] = Button("TV Charts")
		self["key_green"] = Button("Timer Charts")
		self["key_yellow"] = Button("Movie Charts")
		self["key_blue"] = Button("Settings")

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "EPGSelectActions"],
		{
			"ok": self.okClicked,
			"red": self.switchToTVCharts,
			"green": self.switchToTimerCharts,
			"yellow": self.switchToMovieCharts,
			"blue": self.SettingsMenu,
			"info": self.ShowEventInfo,
			"cancel": self.close
		}, -1)

		self.epgcache = eEPGCache.getInstance()
		self.eventcache = []

		self.RefreshTimer = eTimer()
		self.RefreshTimer.callback.append(self.downloadList)

		self.onLayoutFinish.append(self.firstPluginExec)

	def firstPluginExec(self):
		self.updateEventCache()
		self.switchToTVCharts()

	def okClicked(self):
		current = self["channellist"].getCurrent()
		if current is None:
			return

		if self.mode == "tvcharts":
			service = eServiceReference(str(current[0][0]))
			self.session.nav.playService(service)
		elif self.mode == "timercharts":
			serviceref = ServiceReference(current[0][0])
			eventid = int(current[0][1])
			event = self.getEventFromId(serviceref, eventid)
			if event is not None:
				newEntry = RecordTimerEntry(serviceref, *parseEvent(event), checkOldTimers=True, dirname=preferredTimerPath())
				self.session.openWithCallback(self.addTimerCallback, TimerEntry, newEntry)
			else:
				self.session.open(MessageBox, "Sorry, no EPG Info available for this event", type=MessageBox.TYPE_ERROR, timeout=10)
		elif self.mode == "moviecharts":
			print("[TVCharts] ToDo: Show Movie Info here ...")
			return

	def addTimerCallback(self, answer):
		if answer[0]:
			entry = answer[1]
			simulTimerList = self.session.nav.RecordTimer.record(entry)
			if simulTimerList is not None:
				for x in simulTimerList:
					if x.setAutoincreaseEnd(entry):
						self.session.nav.RecordTimer.timeChanged(x)
				simulTimerList = self.session.nav.RecordTimer.record(entry)
				if simulTimerList is not None:
					self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)
		else:
			print("Timeredit aborted")

	def finishSanityCorrection(self, answer):
		self.addTimerCallback(answer)

	def SettingsMenu(self):
		self.session.open(TVChartsSetup)

	def ShowEventInfo(self):
		current = self["channellist"].getCurrent()
		if current is None:
			return

		serviceref = current[0][0]
		eventid = current[0][1]

		service = ServiceReference(serviceref)
		event = self.getEventFromId(service, eventid)

		if event is not None:
			self.session.open(EventViewSimple, event, service)

	def getEventFromId(self, service, eventid):
		event = None
		if self.epgcache is not None and eventid is not None:
			event = self.epgcache.lookupEventId(service.ref, eventid)
		return event

	def updateEventCache(self):
		try:
			from Screens.ChannelSelection import service_types_tv
			from Components.Sources.ServiceList import ServiceList
			bouquetlist = ServiceList(eServiceReference(service_types_tv + ' FROM BOUQUET "bouquets.tv" ORDER BY bouquet'), validate_commands=False).getServicesAsList()
			for bouquetitem in bouquetlist:
				serviceHandler = eServiceCenter.getInstance()
				list = serviceHandler.list(eServiceReference(str(bouquetitem[0])))
				services = list and list.getContent('S')
				search = ['IBDCTSERNX']

				if services:  # It's a Bouquet
					search.extend([(service, 0, -1) for service in services])

				events = self.epgcache.lookupEvent(search)

				for eventinfo in events:
					#0 eventID | 4 eventname | 5 short descr | 6 long descr | 7 serviceref | 8 channelname
					self.eventcache.append((eventinfo[0], eventinfo[7], eventinfo[8], eventinfo[4]))

		except Exception:
			print("[TVCharts Plugin] Error creating eventcache!")

	def switchToTVCharts(self):
		self.mode = "tvcharts"
		self.setTitle("TV Charts")
		self["channellist"].setList([])
		self.feedurl = "http://www.dreambox-plugins.de/feeds/topchannels.php"
		self.downloadList()

	def switchToTimerCharts(self):
		self.mode = "timercharts"
		self.setTitle("Timer Charts")
		self["channellist"].setList([])
		self.feedurl = "http://www.dreambox-plugins.de/feeds/toptimers.php?limit=%s" % config.plugins.tvcharts.maxtimerentries.value
		self.downloadList()

	def switchToMovieCharts(self):
		self.mode = "moviecharts"
		self.setTitle("Movie Charts")
		self["channellist"].setList([])
		self.feedurl = "http://www.dreambox-plugins.de/feeds/topmovies.php"
		self.downloadList()

	def downloadList(self):
		if config.plugins.tvcharts.enabled.value:
			self["info"].setText("Downloading feeds from server ...")
			getPage(six.ensure_binary(self.feedurl)).addCallback(self.downloadListCallback).addErrback(self.downloadListError)
		else:
			self["info"].setText("Error: Plugin disabled in Settings ...")

	def downloadListError(self, error=""):
		print(str(error))
		self.session.open(MessageBox, "Error downloading Feed:\n%s" % str(error), type=MessageBox.TYPE_ERROR)
		self["info"].setText("Error downloading Feed!")

	def downloadListCallback(self, page=""):
		self["info"].setText("Parsing Feeds ...")

		channellist = []
		channelcount = 0
		useronline = 0
		totalusers = 0
		totaltimer = 0
		totalmovies = 0
		xml = parseString(page)

		if self.mode == "tvcharts":
			for node in xml.getElementsByTagName("DATA"):
				useronline = int(node.getElementsByTagName("USERCOUNT")[0].childNodes[0].data)
				totalusers = int(node.getElementsByTagName("TOTALUSERS")[0].childNodes[0].data)

			for node in xml.getElementsByTagName("CHANNEL"):
				event_id = None
				inBouquet = False
				channelname = str(node.getElementsByTagName("NAME")[0].childNodes[0].data)
				serviceref = str(node.getElementsByTagName("SERVICEREF")[0].childNodes[0].data)
				eventname = str(node.getElementsByTagName("EVENTNAME")[0].childNodes[0].data)
				usercount = int(node.getElementsByTagName("USERCOUNT")[0].childNodes[0].data)
				percent = int(node.getElementsByTagName("PERCENT")[0].childNodes[0].data)

				# Look for favourite channel for this event in my bouqets
				for sepginfo in self.eventcache:
					if sepginfo[2] == channelname:
						inBouquet = True
					if sepginfo[3] == eventname:
						event_id = sepginfo[0]
					if sepginfo[3] == eventname and sepginfo[1] != serviceref:
						if channelname[0:3].lower() == sepginfo[2][0:3].lower():
							serviceref = sepginfo[1]
							channelname = sepginfo[2]
						inBouquet = True
						break
					elif sepginfo[3] == eventname and sepginfo[1] == serviceref:
						break

				# Skip Channels that are not in my bouquets
				if config.plugins.tvcharts.bouquetfilter.value and not inBouquet:
					continue

				# Skip Channels that are not in my bouquets
				channelcount += 1
				if channelcount > config.plugins.tvcharts.maxentries.value:
					break

				# Add to List
				channellist.append(ChannelListEntryComponent(self.mode, channelname, serviceref, event_id, eventname, 0, 0, usercount, percent))

			if totalusers > 0:
				self.setTitle("TV Charts (User online: %s of %s)" % (useronline, totalusers))

		elif self.mode == "timercharts":
			for node in xml.getElementsByTagName("DATA"):
				totaltimer = int(node.getElementsByTagName("TIMERCOUNT")[0].childNodes[0].data)

			for node in xml.getElementsByTagName("TIMER"):
				eitID = int(node.getElementsByTagName("ID")[0].childNodes[0].data)
				channelname = str(node.getElementsByTagName("CHANNELNAME")[0].childNodes[0].data)
				serviceref = str(node.getElementsByTagName("SERVICEREF")[0].childNodes[0].data)
				eventname = str(node.getElementsByTagName("EVENTNAME")[0].childNodes[0].data)
				starttime = int(node.getElementsByTagName("STARTTIME")[0].childNodes[0].data)
				endtime = int(node.getElementsByTagName("ENDTIME")[0].childNodes[0].data)
				usercount = int(node.getElementsByTagName("USERCOUNT")[0].childNodes[0].data)
				percent = int(node.getElementsByTagName("PERCENT")[0].childNodes[0].data)

				# Look for favourite channel for this event in my bouqets
				for sepginfo in self.eventcache:
					if sepginfo[2] == channelname:
						serviceref = sepginfo[1]
						channelname = sepginfo[2]
						inBouquet = True
						break

				# Add to List
				channellist.append(ChannelListEntryComponent(self.mode, channelname, serviceref, eitID, eventname, starttime, endtime, usercount, percent))

			if totaltimer > 0:
				self.setTitle("Timer Charts (Total Timer: %s)" % (totaltimer))

		elif self.mode == "moviecharts":
			for node in xml.getElementsByTagName("DATA"):
				totalmovies = int(node.getElementsByTagName("MOVIECOUNT")[0].childNodes[0].data)

			for node in xml.getElementsByTagName("MOVIE"):
				eventid = int(node.getElementsByTagName("EVENTID")[0].childNodes[0].data)
				eventname = str(node.getElementsByTagName("EVENTNAME")[0].childNodes[0].data)
				channelname = str(node.getElementsByTagName("CHANNELNAME")[0].childNodes[0].data)
				serviceref = str(node.getElementsByTagName("SERVICEREF")[0].childNodes[0].data)
				starttime = int(node.getElementsByTagName("STARTTIME")[0].childNodes[0].data)
				usercount = int(node.getElementsByTagName("USERCOUNT")[0].childNodes[0].data)

				# Add to List
				channellist.append(ChannelListEntryComponent(self.mode, channelname, serviceref, eventid, eventname, starttime, 0, usercount, 0))

			#if totalmovies > 0:
			#	self.setTitle("Movie Charts (Total Movies: %s)" % (totalmovies))

		self["info"].setText("")
		self["channellist"].setList(channellist)

		self.RefreshTimer.start(60000, True)

############################
#####  SETTINGS SCREEN #####
############################


class TVChartsSetup(ConfigListScreen, Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ["TVChartsSetup", "Setup"]
		self.setup_title = _("TV Charts Settings")

		self.onChangedEntry = []
		self.list = []
		ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changedEntry)

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.SaveSettings,
			"green": self.SaveSettings,
			"red": self.Exit,
			"cancel": self.Exit
		}, -2)

		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))

		self.createSetup()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(self.setup_title)

	def createSetup(self):
		self.list = [getConfigListEntry(_("TV Charts Plugin Enable"), config.plugins.tvcharts.enabled)]
		if config.plugins.tvcharts.enabled.value:
			self.list.extend((
				getConfigListEntry(_("Max Toplist Entries"), config.plugins.tvcharts.maxentries),
				getConfigListEntry(_("Max Timerlist Entries"), config.plugins.tvcharts.maxtimerentries),
				getConfigListEntry(_("Enable Bouquet-Filter?"), config.plugins.tvcharts.bouquetfilter),
				getConfigListEntry(_("Submit Timerlist?"), config.plugins.tvcharts.submittimers),
				getConfigListEntry(_("Submit Pluginlist?"), config.plugins.tvcharts.submitplugins)
			))

		self["config"].list = self.list
		self["config"].setList(self.list)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		if self["config"].getCurrent()[1] == config.plugins.tvcharts.enabled:
			self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		if self["config"].getCurrent()[1] == config.plugins.tvcharts.enabled:
			self.createSetup()

	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def SaveSettings(self):
		config.plugins.tvcharts.save()
		configfile.save()
		self.close()

	def Exit(self):
		self.close()


##############################
#####   UPDATE STATUS    #####
##############################
class DBUpdateStatus(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)

		self.DBStatusTimer = eTimer()
		self.DBStatusTimer.callback.append(self.updateStatus)

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evUpdatedInfo: self.restartTimer,
				iPlayableService.evUpdatedEventInfo: self.restartTimer
			})

		self.recordtimer = session.nav.RecordTimer
		self.NetworkConnectionAvailable = False
		self.LastTimerlistUpdate = 0

		self.timerlist = ""
		self.pluginlist = ""

		self.onShow.append(self.restartTimer)

	def restartTimer(self):
		if self.NetworkConnectionAvailable:
			self.DBStatusTimer.stop()
			self.DBStatusTimer.start((randint(15, 60)) * 1000, True)
		else:
			iNetwork.checkNetworkState(self.checkNetworkCB)

	def checkNetworkCB(self, data):
		if data is not None:
			if data <= 2:
				self.NetworkConnectionAvailable = True
				self.restartTimer()
			else:
				self.NetworkConnectionAvailable = False
				self.DBStatusTimer.stop()

	def updateStatus(self):
		print("[TVCharts] Status Update ...")
		self.DBStatusTimer.stop()

		if not config.plugins.tvcharts.enabled.value or Screens.Standby.inStandby:
			return

		# Get Channelname
		sref = self.session.nav.getCurrentlyPlayingServiceReference()
		if sref is not None:
			ref = eServiceReference(sref.toString())
			ref.setName("")
			serviceHandler = eServiceCenter.getInstance()
			info = serviceHandler.info(ref)
			channel_name = info and info.getName(ref).replace('\xc2\x86', '').replace('\xc2\x87', '').decode("utf-8", "ignore").encode("utf-8") or ""
			self.serviceref = ref.toString()
		else:
			channel_name = ""
			self.serviceref = ""

		# Get Event Info
		service = self.session.nav.getCurrentService()
		info = service and service.info()
		event = info and info.getEvent(0)
		event_name = event and event.getEventName() or ""
		event_description = ""
		event_begin = 0

		if event is not None:
			curEvent = parseEvent(event)
			event_begin = int(curEvent[0]) + (config.recording.margin_before.getValue() * 60)
			event_description = event.getExtendedDescription()

		# Get Box Info
		self.BoxID = iNetwork.getAdapterAttribute("eth0", "mac")
		self.DeviceName = BoxInfo.getItem("model")
		try:
			from enigma import getEnigmaVersionString
			from boxbranding import getImageVersion, getImageBuild
			self.EnigmaVersion = getEnigmaVersionString()
			self.ImageVersion = getImageVersion() + '.' + getImageBuild()
		except:
			self.EnigmaVersion = about.getEnigmaVersionString()
			self.ImageVersion = about.getVersionString()

		# Get TimerList
		self.timerlist = ""
		if config.plugins.tvcharts.submittimers.value and self.LastTimerlistUpdate <= (time() - 1800):
			self.LastTimerlistUpdate = time()
			try:
				for timer in self.recordtimer.timer_list:
					if timer.disabled == 0 and timer.justplay == 0:
						self.timerlist += "%s|%s|%s|%s|%s|%s|%s\n" % (timer.eit, str(int(timer.begin) + (config.recording.margin_before.getValue() * 60)), str(int(timer.end) - (config.recording.margin_after.getValue() * 60)), str(timer.service_ref), timer.name, timer.service_ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '').decode("utf-8", "ignore").encode("utf-8"), timer.repeated)
			except Exception:
				print("[TVCharts] Error loading timers!")

		# Get Pluginlist
		if config.plugins.tvcharts.submitplugins.value and self.pluginlist == "":
			try:
				os_system("opkg list_installed | grep enigma2-plugin- > /tmp/plugins.txt")
				for plugin in open('/tmp/plugins.txt', 'r'):
					self.pluginlist += plugin[0:plugin.find(' - ')] + "\n"
				os_system("rm -f /tmp/plugins.txt")
			except Exception:
				print("[TVCharts] Error loading plugins!")

		# Status Update
		getPage(url=b'http://www.dreambox-plugins.de/feeds/TVCharts/status.php', agent="Mozilla/5.0 (Windows; U; MSIE 7.0; Windows NT 6.0; en-US)", timeout=60, method='POST', headers={'Content-Type': 'application/x-www-form-urlencoded'}, postdata=urlencode({'boxid': self.BoxID, 'devicename': self.DeviceName, 'imageversion': self.ImageVersion, 'enigmaversion': self.EnigmaVersion, 'lastchannel': channel_name, 'lastevent': event_name, 'eventdescr': event_description, 'lastbegin': event_begin, 'lastserviceref': self.serviceref, 'timerlist': self.timerlist, 'pluginlist': self.pluginlist})).addErrback(self.updateError)

		# Restart Timer
		self.DBStatusTimer.start(900000, True)

	def updateError(self, error=""):
		self.NetworkConnectionAvailable = False
		self.DBStatusTimer.stop()

#############################
#####    INIT PLUGIN    #####
#############################


def main(session, **kwargs):
	session.open(TVChartsMain)


def autostart(reason, **kwargs):
	global session
	if "session" in kwargs:
		session = kwargs["session"]
		DBUpdateStatus(session)


def Plugins(path, **kwargs):
	return [
		PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart),
		PluginDescriptor(name="TV Charts", description="TV Charts Plugin", icon="plugin.png", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main),
		PluginDescriptor(name="TV Charts", description="TV Charts Plugin", icon="plugin.png", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main)]
