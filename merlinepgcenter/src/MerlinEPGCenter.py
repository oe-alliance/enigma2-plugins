#
#  MerlinEPGCenter E2 Plugin
#
#  $Id: MerlinEPGCenter.py,v 1.0 2011-02-14 21:53:00 shaderman Exp $
#
#  Coded by Shaderman (c) 2011
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#

NUM_EPG_TABS = 5 # 0 based
NUM_CONFIG_TABS = 2 # 0 based

STYLE_SINGLE_LINE = "0"
STYLE_SHORT_DESCRIPTION = "1"

MODE_TV = 0
MODE_RADIO = 1

# PYTHON IMPORTS
from time import localtime, strftime, mktime, time
from datetime import datetime

# ENIGMA IMPORTS
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Button import Button
from Components.config import config, NoSave, ConfigText, KEY_0, KEY_LEFT, KEY_RIGHT, KEY_OK, KEY_DELETE, KEY_BACKSPACE
from Components.ConfigList import ConfigList
from Components.Label import Label, MultiColorLabel
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap, MultiPixmap
from Components.ProgressBar import ProgressBar
from Components.UsageConfig import preferredTimerPath
from Components.VideoWindow import VideoWindow
from enigma import eServiceReference, eServiceCenter, eEPGCache, getDesktop, eSize, eTimer, fontRenderClass, ePoint
from math import fabs
import NavigationInstance
from RecordTimer import AFTEREVENT
from Screens.EpgSelection import EPGSelection
from Screens.Screen import Screen
from Screens.TimerEdit import TimerEditList, TimerSanityConflict
from Screens.TimerEntry import TimerEntry
from ServiceReference import ServiceReference
from skin import parseColor, loadSkin
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN
from Tools.LoadPixmap import LoadPixmap

# OWN IMPORTS
from ConfigTabs import KEEP_OUTDATED_TIME, ConfigBaseTab, ConfigGeneral, ConfigListSettings, ConfigEventInfo, SKINDIR, SKINLIST, STYLE_SIMPLE_BAR, STYLE_PIXMAP_BAR, STYLE_MULTI_PIXMAP
from EpgActions import MerlinEPGActions
from EpgCenterList import EpgCenterList, EpgCenterTimerlist, MODE_HD, MODE_XD, MODE_SD, MULTI_EPG_NOW, MULTI_EPG_NEXT, SINGLE_EPG, MULTI_EPG_PRIMETIME, TIMERLIST, EPGSEARCH_HISTORY, EPGSEARCH_RESULT, EPGSEARCH_MANUAL, UPCOMING
from EpgTabs import EpgBaseTab, EpgNowTab, EpgNextTab, EpgSingleTab, EpgPrimeTimeTab, EpgTimerListTab, EpgSearchHistoryTab, EpgSearchManualTab, EpgSearchResultTab
from HelperFunctions import PiconLoader, findDefaultPicon, ResizeScrollLabel, BlinkTimer, LIST_TYPE_EPG, LIST_TYPE_UPCOMING, RecTimerEntry
from SkinFinder import SkinFinder

# for localized messages
from . import _


class MerlinEPGCenter(TimerEditList, MerlinEPGActions):
	(skinFile, skinList) = SkinFinder.getSkinData(SKINLIST, SKINDIR, config.plugins.merlinEpgCenter.skin.value)
	if skinFile is not None:
		if config.plugins.merlinEpgCenter.skin.value != skinFile:
			config.plugins.merlinEpgCenter.skin.value = skinFile
			config.plugins.merlinEpgCenter.skin.save()
		config.plugins.merlinEpgCenter.skinSelection.setChoices(skinList, default = skinFile)
		loadSkin(skinFile, "")
		
	desktopSize = getDesktop(0).size()
	if desktopSize.width() == 1280:
		videoMode = MODE_HD
	elif desktopSize.width() == 1024:
		videoMode = MODE_XD
	elif desktopSize.width() == 720:
		videoMode = MODE_SD
		
	# TimerEditList timer key states
	# EMPTY = 0
	# ENABLE = 1
	# DISABLE = 2
	ADD_TIMER = 3
	REMOVE_TIMER = 4

	def __init__(self, session, servicelist, currentBouquet, bouquetList, currentIndex, startWithTab = None):
		Screen.__init__(self, session)
		
		self.session = session
		self.servicelist = servicelist
		self.currentBouquet = currentBouquet # eServiceReference of the current bouquet
		self.currentBouquetIndex = currentIndex # current bouquet index from InfoBar
		self.bouquetList = bouquetList # a list of tuples of all bouquets (Name, eServicereference)
		self.startWithTab = startWithTab
		
		self.piconLoader = PiconLoader()
		self.piconSize = eSize(50,30)
		
		self.blinkTimer = BlinkTimer(session)
		
		self.listStyle = config.plugins.merlinEpgCenter.listStyle.value
		
		# check Merlin 2 feature "Event tuner check in EPG list"
		# http://www.dreambox-tools.info/thread.php?postid=31822#post31822
		try:
			if config.merlin2.show_event_not_available.value:
				from Components.EpgList import EPGList
				self.epgList = EPGList(timer = self.session.nav.RecordTimer)
			else:
				self.epgList = None
		except KeyError:
			self.epgList = None
			
		# needed stuff for timerlist
		list = [ ]
		self.list = list # TimerEditList property, needed
		
		self.key_green_choice = self.EMPTY
		self.key_red_choice = self.EMPTY # from TimerEditList
		self.key_yellow_choice = self.EMPTY # from TimerEditList
		self.key_blue_choice = self.EMPTY # from TimerEditList

		self["key_red"] = Button(" ") # from TimerEditList
		self["key_green"] = Button(" ") # from TimerEditList
		self["key_yellow"] = Button(" ") # from TimerEditList
		self["key_blue"] = Button(" ") # from TimerEditList
		
		self["tabbar"] = MultiPixmap()
		self["tabBackground"] = Pixmap()
		self["upcoming"] = EpgCenterList(self.blinkTimer, LIST_TYPE_UPCOMING, self.videoMode, self.piconLoader, bouquetList, currentIndex, self.piconSize, self.listStyle, self.epgList)
		self["upcomingSeparator"] = Pixmap()
		self["list"] = EpgCenterList(self.blinkTimer, LIST_TYPE_EPG, self.videoMode, self.piconLoader, bouquetList, currentIndex, self.piconSize, self.listStyle, self.epgList)
		self["timerlist"] = EpgCenterTimerlist(list, self.videoMode, self.piconLoader, self.piconSize, self.listStyle)
		self["eventInfoSeparator"] = Pixmap()
		self["picon"] = Pixmap()
		self["serviceName"] = Label("")
		self["eventTitle"] = Label("")
		self["beginTime"] = Label("")
		self["eventProgress"] = ProgressBar()
		self.progressPixmap = None
		self["eventProgressImage"] = MultiPixmap()
		self["endTime"] = Label("")
		self["duration"] = Label("")
		self["remaining"] = MultiColorLabel()
		self["isRecording"] = Pixmap()
		self["description"] = Label("")
		self["bouquet"] = Label("")
		self["videoPicture"] = VideoWindow(decoder = 0, fb_width = self.desktopSize.width(), fb_height = self.desktopSize.height())
		
		self.historyList = config.plugins.merlinEpgCenter.searchHistory.value
		self["history"] = MenuList(self.historyList)
		
		self["searchLabel"] = Label(_("Search for:"))
		self.searchField = NoSave(ConfigText(default = "", fixed_size = False))
		self.searchList = [("", self.searchField)]
		self["search"] = ConfigList(self.searchList, session = session)
		
		self["settings"] = ConfigList([], session = session)
		ConfigBaseTab.settingsWidget = self["settings"]
		
		self["infoText"] = ResizeScrollLabel("")
		self.infoTextShown = False
		
		self.tabTextEpgList = [_("Now"), _("Upcoming"), _("Single"), _("Prime Time"), _("Timer"), _("Search")]
		self.initTabLabels(self.tabTextEpgList)
		
		self.onLayoutFinish.append(self.startRun)
		
	############################################################################################
	# INITIALISATION & CLEANUP
	
	def startRun(self):
		MerlinEPGActions.__init__(self) # note: this overwrites TimerEditList.["actions"]
		
		self.getPrimeTime()
		self.initEpgBaseTab()
		
		from Screens.InfoBar import InfoBar
		self.infoBarInstance = InfoBar.instance
		self.hideWidgets()
		self["upcoming"].mode = UPCOMING
		self.getWidgetSizes()
		self.searchField.help_window.hide()
		
		self.epgcache = eEPGCache.getInstance()
		
		# store the current minute for list refreshs
		t = localtime(time())
		self.oldTime = "%02d" % t.tm_min
		
		# used to wait another global timer tick (1 second) before updating the epg list
		# this is needed because we're using the global Clock() timer which can differ up to 1 second and
		# could result in a time different between the clock widget and the time shown in the epg list
		self.delayTick = True
		
		# get notifications from the global timer every second to refresh lists on time change
		self.clockTimer = self.global_screen["CurrentTime"].clock_timer
		self.clockTimer.callback.append(self.checkTimeChange)
		
		# Don't show RecordTimer messages when recording starts
		self.showRecordingMessage = config.usage.show_message_when_recording_starts.value
		config.usage.show_message_when_recording_starts.value = False
		
		# Initialise the blink timer if there's already a recording running
		self.blinkTimer.gotRecordEvent(None, None)
		
		self.session.nav.RecordTimer.on_state_change.append(self.onStateChange)
		
		self.blinkTimer.appendList(self["list"])
		self.blinkTimer.appendList(self["upcoming"])
		self.blinkTimer.timer.callback.append(self.setEventPiconBlinkState)
		self.blinkTimer.timer.callback.append(self.setRecordingBlinkState)
		
		self["list"].onSelectionChanged.append(self.onListSelectionChanged)
		self["timerlist"].onSelectionChanged.append(self.onListSelectionChanged)
		
		self.fillTimerList() # TimerEditList method --> tuple (RecordTimer.RecordTimerEntry, processed state)
		
		# set tab captions
		self.configTabsShown = False
		self.configEditMode = False
		self.tabTextConfigList = [_("General"), _("Lists"), _("Event Info"), "", "", ""]
		
		self.configTabObjectList = []
		self.configTabObjectList.append(ConfigGeneral())
		self.configTabObjectList.append(ConfigListSettings())
		self.configTabObjectList.append(ConfigEventInfo())
		
		# similar events
		self.similarTimer = eTimer()
		self.similarTimer.callback.append(self.getSimilarEvents)
		self.similarTimer.callback.append(self.getUpcomingEvents)
		self.similarShown = False
		
		# initialize
		if self.startWithTab is not None:
			self.currentMode = self.startWithTab
		else:
			if config.plugins.merlinEpgCenter.rememberLastTab.value:
				self.currentMode = config.plugins.merlinEpgCenter.lastUsedTab.value
			else:
				self.currentMode = 0
				
		self.oldMode = None
			
		if config.plugins.merlinEpgCenter.selectRunningService.value:
			self.selectRunningService = True
		else:
			self.selectRunningService = False
			
		self.lastMultiEpgIndex = None
		self.showOutdated = False
		self.hideOutdated = False
		self.numNextEvents = None
		
		searchFieldPos = self["search"].getPosition()
		self["search"].getCurrent()[1].help_window.instance.move(ePoint(searchFieldPos[0], searchFieldPos[1] + 40))
		
		self.setMode()
		self.setBouquetName()
		
		self.setNotifier()
		self.onClose.append(self.removeNotifier)
				
	def initEpgBaseTab(self):
		# set ourself, the action map and prime time
		EpgBaseTab.parentInstance	= self
		EpgBaseTab.primeTime		= self.primeTime
		
		self.epgTabObjectList = []
		self.epgTabObjectList.append(EpgNowTab(self["list"]))
		self.epgTabObjectList.append(EpgNextTab(self["list"]))
		self.epgTabObjectList.append(EpgSingleTab(self["list"]))
		self.epgTabObjectList.append(EpgPrimeTimeTab(self["list"]))
		self.epgTabObjectList.append(EpgTimerListTab(self["timerlist"]))
		self.epgTabObjectList.append(EpgSearchHistoryTab(self["history"]))
		self.epgTabObjectList.append(EpgSearchResultTab(self["list"]))
		self.epgTabObjectList.append(EpgSearchManualTab(self["search"], self["searchLabel"]))
		
	def releaseEpgBaseTab(self):
		EpgBaseTab.parentInstance	= None
		EpgBaseTab.primeTime		= None
		
	############################################################################################
	# TAB STUFF
	
	def initTabLabels(self, tabList):
		i = 0
		while i <= NUM_EPG_TABS:
			self["tab_text_%d" % i] = Label(tabList[i])
			i += 1
			
	def setTabText(self, tabList):
		if self.configTabsShown:
			numTabs = NUM_CONFIG_TABS
		else:
			numTabs = NUM_EPG_TABS
			
		i = 0
		while i <= numTabs:
			self["tab_text_%d" % i].setText(tabList[i])
			i += 1
			
	############################################################################################
	# MISC FUNCTIONS
	
	def setProgressbarStyle(self, configElement = None):
		if not config.plugins.merlinEpgCenter.showEventInfo.value:
			return
			
		if config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_SIMPLE_BAR:
			self["eventProgressImage"].hide()
			self["eventProgress"].instance.setPixmap(None)
			self["eventProgress"].show()
		elif config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_PIXMAP_BAR:
			self["eventProgressImage"].hide()
			if self.progressPixmap == None:
				pixmapPath = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/EventProgress.png")
				self.progressPixmap = LoadPixmap(cached = False, path = pixmapPath)
			self["eventProgress"].instance.setPixmap(self.progressPixmap)
			self["eventProgress"].show()
		elif config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_MULTI_PIXMAP:
			self["eventProgress"].hide()
			self["eventProgressImage"].show()
			
		# we need to reset the bar to draw correctly
		value = self["eventProgress"].getValue()
		self["eventProgress"].setValue(0)
		self["eventProgress"].setValue(value)
		
	def getSimilarEvents(self):
		if self.similarShown or self.configTabsShown or (self.currentMode != MULTI_EPG_NOW and self.currentMode != MULTI_EPG_NEXT and self.currentMode != SINGLE_EPG and self.currentMode != MULTI_EPG_PRIMETIME):
			return
			
		# get the selected entry
		cur = self["list"].getCurrent()
		# cur[1] = eventId, cur[2] = sRef
		if cur != None and cur[2] != "" and cur[1] != None:
			serviceList = self.epgcache.search(('R', 100, eEPGCache.SIMILAR_BROADCASTINGS_SEARCH, cur[2], cur[1]))
			knownSimilar = False
			if serviceList is not None and config.plugins.merlinEpgCenter.limitSearchToBouquetServices.value:
				for sRef in serviceList:
					if sRef[0] in EpgCenterList.allServicesNameDict:
						knownSimilar = True
						break
			elif serviceList is not None:
				knownSimilar = True
				
			if knownSimilar:
				self["key_red"].setText(_("Similar"))
				self["epgRedActions"].setEnabled(True)
			elif self["epgRedActions"].enabled:
				self["epgRedActions"].setEnabled(False)
		elif self["epgRedActions"].enabled:
			self["epgRedActions"].setEnabled(False)
				
	def getUpcomingEvents(self):
		size = int(config.plugins.merlinEpgCenter.numNextEvents.value)
		if size == 0 or self.configTabsShown or (self.currentMode != MULTI_EPG_NOW and self.currentMode != MULTI_EPG_NEXT and self.currentMode != MULTI_EPG_PRIMETIME and self.currentMode != EPGSEARCH_RESULT):
			if size > 0:
				self["upcoming"].setList([])
			return
			
		upcomingEvents = []
		cur = self["list"].getCurrent()
		if cur == None:
			return
			
		sRef		= cur[2]
		begin		= cur[3]
		duration	= cur[4]
		
		if sRef == None or begin == None or duration == None:
			nextEvent = -1
		else:
			nextEvent = self.epgcache.startTimeQuery(eServiceReference(sRef), begin + duration)
		
		if nextEvent == -1:
			self["upcoming"].setList([])
			return
			
		i = 0
		while i < size:
			nextEvent = self.epgcache.getNextTimeEntry()
			if nextEvent <= 0:
				break
			else:
				data = (0, nextEvent.getEventId(), sRef, nextEvent.getBeginTime(), nextEvent.getDuration(), nextEvent.getEventName(), nextEvent.getShortDescription(), nextEvent.getExtendedDescription())
				upcomingEvents.append(data)
				i += 1
				
		self["upcoming"].currentBouquetIndex = self.currentBouquetIndex
		self["upcoming"].setList(upcomingEvents)
		
	def hideWidgets(self):
		self["timerlist"].hide()
		self["list"].hide()
		self["settings"].hide()
		self["searchLabel"].hide()
		self["search"].hide()
		self["history"].hide()
		self["videoPicture"].hide()
		self["infoText"].hide()
		self["upcoming"].hide()
		self["upcoming"].instance.setSelectionEnable(0)
		self["upcomingSeparator"].hide()
		self["eventInfoSeparator"].hide()
		self["eventProgress"].hide()
		self["eventProgressImage"].hide()
		self["isRecording"].hide()
		
	# get some widget sizes
	def getWidgetSizes(self):
		# self["list"]
		for (attrib, value) in self["list"].skinAttributes:
			if attrib == "size":
				self.listWidthMin, self.listHeightMin = [int(x) for x in value.split(",")]
		# self["tabBackground"] (this is used to determine the maximum list width)
		for (attrib, value) in self["tabBackground"].skinAttributes:
			if attrib == "size":
				self.listWidthMax, self.listHeightMax = [int(x) for x in value.split(",")]
		# self["upcomingSeparator"]
		for (attrib, value) in self["upcomingSeparator"].skinAttributes:
			if attrib == "position":
				self.upcomingSepPosX, self.upcomingSepPosY = [int(x) for x in value.split(",")]
			elif attrib == "size":
				self.separatorWidth, self.separatorHeight = [int(x) for x in value.split(",")]
		# self["description"]
		for (attrib, value) in self["description"].skinAttributes:
			if attrib == "position":
				self.descriptionPosX, self.descriptionPosY = [int(x) for x in value.split(",")]
			if attrib == "size":
				self.descriptionWidthMax, self.descriptionHeightMax = [int(x) for x in value.split(",")]
		# self["videoPicture"]
		for (attrib, value) in self["videoPicture"].skinAttributes:
			if attrib == "position":
				self.videoPicturePosX, self.videoPicturePosY = [int(x) for x in value.split(",")]
	def setSkinFile(self, configElement = None):
		config.plugins.merlinEpgCenter.skin.value = configElement.getValue()
		
	def setUpcomingWidgets(self, configElement = None):
		self.numNextEvents = int(config.plugins.merlinEpgCenter.numNextEvents.value)
		
		if self.numNextEvents == 0 or self.currentMode == SINGLE_EPG or self.currentMode == TIMERLIST or self.currentMode == EPGSEARCH_HISTORY or self.currentMode == EPGSEARCH_MANUAL or self.currentMode == EPGSEARCH_RESULT:
			self["upcomingSeparator"].hide()
			self["upcoming"].hide()
			
			newHeight = self.listHeightMin / self["list"].itemHeight * self["list"].itemHeight
			
			if config.plugins.merlinEpgCenter.showEventInfo.value:
				self["list"].maxWidth = self.listWidthMin
				newListSize = eSize(self.listWidthMin, newHeight)
			else:
				self["list"].maxWidth = self.listWidthMax
				newListSize = eSize(self.listWidthMax, newHeight)
			self["list"].instance.resize(newListSize)
			return
		
		self.heightDiff = self["list"].itemHeight * self.numNextEvents
		border = 5
		
		# resize self["list"] and self["upcoming"]
		newHeight = ((self.listHeightMin - self.heightDiff - border) / self["list"].itemHeight) * self["list"].itemHeight
		
		if config.plugins.merlinEpgCenter.showEventInfo.value:
			self["list"].maxWidth = self.listWidthMin
			self["upcoming"].maxWidth = self.listWidthMin
			newListSize = eSize(self.listWidthMin, newHeight)
		else:
			self["list"].maxWidth = self.listWidthMax
			self["upcoming"].maxWidth = self.listWidthMax
			newListSize = eSize(self.listWidthMax, newHeight)
			
		newPosY = self.upcomingSepPosY - self.heightDiff
		self["list"].instance.resize(newListSize)
		self["upcoming"].setPosition(self.upcomingSepPosX, newPosY + self.separatorHeight + border)
		self["upcoming"].instance.resize(newListSize)
		
		# set self["upcomingSeparator"] position
		self["upcomingSeparator"].setPosition(self.upcomingSepPosX, newPosY)
		if not self.configTabsShown:
			self["upcoming"].show()
			self["upcomingSeparator"].show()
			
	def checkTimeChange(self):
		t = localtime(time())
		tmpTime = "%02d" % t.tm_min
		if self.oldTime != tmpTime:
			if self.delayTick:
				# delay one more tick (1 second)
				self.delayTick = False
				return
			self.oldTime = tmpTime
			if self.similarShown:
				self.epgTabObjectList[self.currentMode].refreshSimilar()
			else:
				self.epgTabObjectList[self.currentMode].refresh()
			self.delayTick = True
			
	def setNotifier(self):
		config.plugins.merlinEpgCenter.primeTime.addNotifier(self.getPrimeTime, initial_call = False)
		config.plugins.merlinEpgCenter.showVideoPicture.addNotifier(self.setVideoPicture, initial_call = True)
		config.plugins.merlinEpgCenter.showEventInfo.addNotifier(self.setEventInfo, initial_call = True)
		config.plugins.merlinEpgCenter.showInputHelp.addNotifier(self.setInputHelp, initial_call = False)
		config.plugins.merlinEpgCenter.listStyle.addNotifier(self.setListStyle, initial_call = False)
		config.plugins.merlinEpgCenter.skinSelection.addNotifier(self.setSkinFile, initial_call = True)
		config.plugins.merlinEpgCenter.numNextEvents.addNotifier(self.setUpcomingWidgets, initial_call = True)
		config.plugins.merlinEpgCenter.listItemHeight.addNotifier(self.setUpcomingWidgets, initial_call = False)
		config.plugins.merlinEpgCenter.listProgressStyle.addNotifier(self.setProgressbarStyle, initial_call = True)
		
	def removeNotifier(self):
		self["list"].onSelectionChanged.remove(self.onListSelectionChanged)
		self["timerlist"].onSelectionChanged.remove(self.onListSelectionChanged)
		
		self.clockTimer.callback.remove(self.checkTimeChange)
		
		self.piconLoader.removeNotifier()
		
		for configTabObject in self.configTabObjectList:
			configTabObject.removeNotifier()
		
		config.plugins.merlinEpgCenter.primeTime.notifiers.remove(self.getPrimeTime)
		config.plugins.merlinEpgCenter.showVideoPicture.notifiers.remove(self.setVideoPicture)
		config.plugins.merlinEpgCenter.showEventInfo.notifiers.remove(self.setEventInfo)
		config.plugins.merlinEpgCenter.showInputHelp.notifiers.remove(self.setInputHelp)
		config.plugins.merlinEpgCenter.listStyle.notifiers.remove(self.setListStyle)
		config.plugins.merlinEpgCenter.skinSelection.notifiers.remove(self.setSkinFile)
		config.plugins.merlinEpgCenter.numNextEvents.notifiers.remove(self.setUpcomingWidgets)
		config.plugins.merlinEpgCenter.listItemHeight.notifiers.remove(self.setUpcomingWidgets)
		config.plugins.merlinEpgCenter.listProgressStyle.notifiers.remove(self.setProgressbarStyle)
		
	def setListStyle(self, configElement = None):
		itemHeight = self.piconSize.height() + int(config.plugins.merlinEpgCenter.listItemHeight.value)
		
		self.listStyle = configElement.value
		if self.listStyle != STYLE_SINGLE_LINE:
			itemHeight += 24 # TODO this should depend on font height
			
		self["list"].changeHeight()
		self["upcoming"].changeHeight()
		if self.numNextEvents > 0:
			self.setUpcomingWidgets()
		self["timerlist"].changeHeight()
		
	def getPrimeTime(self, configElement = None):
		now = localtime(time())
		dt = datetime(now.tm_year, now.tm_mon, now.tm_mday, config.plugins.merlinEpgCenter.primeTime.value[0], config.plugins.merlinEpgCenter.primeTime.value[1])
		self.primeTime = int(mktime(dt.timetuple()))
		EpgBaseTab.primeTime = self.primeTime
		
	def addTimer(self, timer):
		self.session.openWithCallback(self.finishedAdd, TimerEntry, timer)
		
	# TimerEditList function (overwritten to update the timer button state)
	def finishedAdd(self, answer):
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
			self.fillTimerList()
			self.updateState()
			
			cur = self["list"].getCurrent()
			if cur is not None:
				self.key_green_choice = self.ADD_TIMER
				self.setTimerButtonState(cur)
				self.setButtonText(timerAdded = True)
				self.getSimilarEvents()
		else:
			print "Timeredit aborted"
			
	def getBouquetName(self):
		name = self.bouquetList[self.currentBouquetIndex][0]
		if self.infoBarInstance.servicelist.mode == MODE_TV:
			return 'Bouquet: ' + name.rstrip(' (TV)')
		else:
			return 'Bouquet: ' + name.rstrip(' (Radio)')
			
	def onListSelectionChanged(self):
		if self.currentMode == TIMERLIST:
			sel = self["timerlist"].getCurrent()
			if sel is None:
				# TODO hide event info
				return
			else:
				# build a tuple similar to the one returned by epg lists. the leading 0 is needed to make the list equal
				# to the epg list's (make list entries without event id selectable)
				cur = (0, sel.eit, str(sel.service_ref), sel.begin, sel.end - sel.begin, sel.name, sel.description, None)
				remainBeginString = ""
				percent = 0
				duraString = "%d" % ((sel.end - sel.begin) / 60)
		else:
			# check for similar events if similar events aren't shown already
			if not self.similarShown and (self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == SINGLE_EPG or self.currentMode == MULTI_EPG_PRIMETIME):
				self["key_red"].setText("")
				self.similarTimer.start(400, True)
				
			cur = self["list"].getCurrent()
			if cur is None:
				# TODO hide event info
				return
				
		# use variable names to make the code more readable
		(ignoreMe, eventid, sRef, begin, duration, title, shortDesc, description) = cur
		
		# set timer button state
		self.setTimerButtonState(cur)
		
		self.setEventViewPicon(cur)
		
		if sRef in EpgCenterList.allServicesNameDict:
			serviceName = EpgCenterList.allServicesNameDict[sRef]
		else:
			serviceName = ServiceReference(sRef).getServiceName()
		self["serviceName"].setText(serviceName)

		if begin != None and duration != None:
			beginString = strftime("%H:%M", localtime(begin))
			endString = strftime("%H:%M", localtime(begin + duration))
			
			if self.currentMode != TIMERLIST:
				duraString = "%d" % (duration / 60)
				now = int(time())
				
				if self.currentMode == SINGLE_EPG:
					if self["list"].instance.getCurrentIndex() == 0:
						timeValue = (begin + duration - now) /  60 + 1
						percent = int((now - begin) * 100 / duration)
					else:
						timeValue = (now - begin) /  60
						percent = 0
				elif self.currentMode == MULTI_EPG_NEXT:
					timeValue = (now - begin) /  60
					percent = 0
				else:
					if now >= begin:
						timeValue = (begin + duration - now) /  60 + 1
						percent = int((now - begin) * 100 / duration)
					else:
						timeValue = (now - begin) /  60
						percent = 0
						
				if (KEEP_OUTDATED_TIME == None and (begin + duration) > now) or (KEEP_OUTDATED_TIME != None and (begin + duration) > now):
					remainBeginString = " I "
					if timeValue > 0:
						remainBeginString += "+"
					if fabs(timeValue) >= 120 and fabs(timeValue) < 1440:
						timeValue /= 60
						remainBeginString += "%02dh" % timeValue
					elif fabs(timeValue) >= 1440:
						timeValue = (timeValue / 1440) +1
						remainBeginString += "%02dd" % timeValue
					else:
						if timeValue < 0:
							remainBeginString += "%03d" % timeValue
						else:
							remainBeginString += "%02d" % timeValue
				else:
					remainBeginString = " I <->"
			else:
				remainBeginString = ""
				
			if remainBeginString.endswith('>'): # KEEP_OUTDATED_TIME
				outdated = True
				try:
					progColor = parseColor("eventNotAvailable").argb()
				except:
					progColor = 0x777777
			elif config.plugins.merlinEpgCenter.showColoredEpgTimes.value:
				outdated = False
				if remainBeginString.endswith('h'): # begins in... hours
					self["remaining"].setForegroundColorNum(0)
				elif remainBeginString.endswith('d'): # begins in... days
					self["remaining"].setForegroundColorNum(1)
				elif remainBeginString.startswith(' I +'): # already running
					self["remaining"].setForegroundColorNum(2)
				elif remainBeginString.startswith(' I -'): # begins in... minutes
					self["remaining"].setForegroundColorNum(3)
				else: # undefined, shouldn't happen
					self["remaining"].setForegroundColorNum(4)
			else:
				outdated = False
				self["remaining"].setForegroundColorNum(3)
				
			if outdated:
				try:
					textColor = parseColor("eventNotAvailable").argb()
				except:
					textColor = parseColor("#777777")
					
				if config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_MULTI_PIXMAP:
					self["eventProgressImage"].setPixmapNum(4)
				else:
					self["eventProgress"].setValue(100)
			else:
				try:
					textColor = parseColor("ListboxForeground").argb()
				except:
					textColor = parseColor("#ffffff")
					
				if config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_MULTI_PIXMAP:
					if percent > 0:
						part = int(round(percent / 25)) + 1
						if part < 0:
							part = 0
						elif part > 4:
							part = 4
					else:
						part = 0
					self["eventProgressImage"].setPixmapNum(part)
				else:
					self["eventProgress"].setValue(percent)
					
			self["remaining"].instance.setForegroundColor(textColor)
				
			self["beginTime"].setText(beginString)
			self["endTime"].setText(endString)
			self["remaining"].setText(remainBeginString)
			self["duration"].setText(duraString)
			
		# all lists
		self["eventTitle"].setText(title)
		
		if config.plugins.merlinEpgCenter.showShortDescInEventInfo.value:
			newDescription = ""
			
			if shortDesc != None and shortDesc != "" and shortDesc != title:
				if newDescription == "":
					newDescription = shortDesc
				else:
					newDescription = ''.join([newDescription, "\n\n", shortDesc])
			if description != None and description != "":
				if newDescription == "":
					newDescription = description
				else:
					newDescription = ''.join([newDescription, "\n\n", description])
			description = newDescription

		self["description"].setText(description)
		
	def prepareFillMultiEpg(self):
		self.currentBouquet = self.bouquetList[self.currentBouquetIndex][1]
		if self.currentMode == MULTI_EPG_PRIMETIME:
			stime = self.primeTime
		else:
			stime = -1

		self.epgTabObjectList[self.currentMode].show(self.currentBouquet, self.currentBouquetIndex, self.currentMode)
		self.setBouquetName()
		
	def switchTvRadio(self, mode):
		if self.configTabsShown or mode == self.infoBarInstance.servicelist.mode:
			return
			
		if self.infoTextShown:
			self.keyInfo()
			
		from plugin import getBouquetInformation
		if mode == MODE_TV:
			self.infoBarInstance.servicelist.setModeTv()
		else:
			self.infoBarInstance.servicelist.setModeRadio()
		self.infoBarInstance.servicelist.zap()
		
		(self.servicelist, self.currentBouquet, self.bouquetList, self.currentBouquetIndex) = getBouquetInformation()
		self.similarShown = False
		
		EpgCenterList.bouquetList = self.bouquetList
		EpgCenterList.currentBouquetIndex = self.currentBouquetIndex
		EpgCenterList.updateBouquetServices()
		
		if self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == SINGLE_EPG or self.currentMode == MULTI_EPG_PRIMETIME:
			self.selectRunningService = True
			self.setMode(switchTvRadio = True)
			self["list"].l.invalidate()
			
		self.setBouquetName()
			
		if config.plugins.merlinEpgCenter.exitOnTvRadioSwitch.value:
			self.keyExit()
			
	def setButtonText(self, timerAdded = False):
		# cleanup button text
		if self.configTabsShown:
			self["key_red"].setText("")
			self["key_green"].setText("")
			self["key_blue"].setText("")
			return
		elif self.oldMode == SINGLE_EPG:
			self["key_blue"].setText("")
		elif self.oldMode == TIMERLIST:
			self["key_red"].setText("")
			self["key_yellow"].setText("")
			self["key_blue"].setText("")
		elif self.oldMode == EPGSEARCH_HISTORY or timerAdded:
			if not self.similarShown:
				self["key_red"].setText("")
			self["key_yellow"].setText("")
			self["key_blue"].setText("")
			
		# set button text
		if self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == SINGLE_EPG or self.currentMode == MULTI_EPG_PRIMETIME or self.currentMode == EPGSEARCH_RESULT:
			if self.currentMode == SINGLE_EPG and KEEP_OUTDATED_TIME != None:
				if not self.showOutdated:
					self["key_blue"].setText(_("Outdated on"))
				else:
					self["key_blue"].setText(_("Outdated off"))
			else:
				self["key_blue"].setText("")
		elif self.currentMode == TIMERLIST:
			self.key_red_choice = self.EMPTY # TimerEditList method
			self.key_yellow_choice = self.EMPTY # TimerEditList method
			self.key_blue_choice = self.EMPTY # TimerEditList method
			self.updateState() # TimerEditList method
			self["key_green"].setText(_("Add"))
		elif self.currentMode == EPGSEARCH_HISTORY:
			self["key_red"].setText(_("Remove"))
			self["key_green"].setText(_("OK"))
			self["key_yellow"].setText(_("New Search"))
			
	def setTimerButtonState(self, cur):
		if self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == SINGLE_EPG or self.currentMode == MULTI_EPG_PRIMETIME or self.currentMode == EPGSEARCH_RESULT or self.currentMode == EPGSEARCH_HISTORY:
			isRecordEvent = False
			for timer in self.session.nav.RecordTimer.timer_list:
				if timer.eit == cur[1] and timer.service_ref.ref.toString() == cur[2]:
					isRecordEvent = True
					break
			if isRecordEvent:
				self["key_green"].setText(_("Remove timer"))
				self.key_green_choice = self.REMOVE_TIMER
			elif not isRecordEvent:
				self["key_green"].setText(_("Add timer"))
				self.key_green_choice = self.ADD_TIMER
		elif self.currentMode == TIMERLIST:
			self.key_green_choice = self.EMPTY
			
	def deleteTimer(self, timer):
		timer.afterEvent = AFTEREVENT.NONE
		self.session.nav.RecordTimer.removeEntry(timer)
		self["key_green"].setText(_("Add timer"))
		self.key_green_choice = self.ADD_TIMER
		# refresh timer pixmaps in our list
		self["list"].l.invalidate()
		size = int(config.plugins.merlinEpgCenter.numNextEvents.value)
		if not (size == 0 or self.configTabsShown or (self.currentMode != MULTI_EPG_NOW and self.currentMode != MULTI_EPG_NEXT and self.currentMode != MULTI_EPG_PRIMETIME and self.currentMode != EPGSEARCH_RESULT)):
			self["upcoming"].l.invalidate()
		# rebuild the timer list
		self.fillTimerList() # TimerEditList method
		
	def setBouquetName(self):
		self["bouquet"].setText(self.getBouquetName())
		
	def setRecordingBlinkState(self):
		if self.blinkTimer.getBlinkState() and not self.blinkTimer.getIsStopping():
			self["isRecording"].show()
		else:
			self["isRecording"].hide()
			
	def setEventPiconBlinkState(self):
		if self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == SINGLE_EPG or self.currentMode == MULTI_EPG_PRIMETIME or self.currentMode == EPGSEARCH_RESULT:
			cur = self["list"].getCurrent()
			self.setEventViewPicon(cur)
			
	def setEventViewPicon(self, cur):
		idx = self["list"].instance.getCurrentIndex()
		if config.plugins.merlinEpgCenter.blinkingPicon.value and self.blinkTimer.getIsInList(idx) and not self.blinkTimer.getBlinkState():
			self["picon"].instance.setPixmap(None)
		elif cur is not None:
			sRef = cur[2]
			picon = self.piconLoader.getPicon(sRef)
			if self["picon"].instance is not None:
				fileName = findDefaultPicon(sRef)
				if fileName is not "":
					picon = LoadPixmap(fileName)
					self["picon"].instance.setPixmap(picon)
				
	def removeFromEpgSearchHistory(self):
		if len(self["history"].list):
			cur = self["history"].getCurrent()
			config.plugins.merlinEpgCenter.searchHistory.value.remove(cur)
			self["history"].setList(config.plugins.merlinEpgCenter.searchHistory.value)
			
	def setInputHelp(self, configElement = None):
		if config.plugins.merlinEpgCenter.showInputHelp.value:
			self.searchField.help_window.show()
		else:
			self.searchField.help_window.hide()
			
	############################################################################################
	# TAB HANDLING

	def setTabs(self):
		if self.configTabsShown:
			numTabs = NUM_CONFIG_TABS
		else:
			numTabs = NUM_EPG_TABS
			
		# set tab text color
		if self.currentMode > numTabs:
			self["tabbar"].setPixmapNum(numTabs) # last tab
		else:
			self["tabbar"].setPixmapNum(self.currentMode)
			
		if self.oldMode != None:
			if self.oldMode >= numTabs:
				self["tab_text_%d" % numTabs].instance.setForegroundColor(parseColor("#ffffff")) # inactive
			else:
				self["tab_text_%d" % self.oldMode].instance.setForegroundColor(parseColor("#ffffff")) # inactive
			
		if self.currentMode >= numTabs:
			self["tab_text_%d" % numTabs].instance.setForegroundColor(parseColor("#ef7f1a")) # active
		else:
			self["tab_text_%d" % self.currentMode].instance.setForegroundColor(parseColor("#ef7f1a")) # active
			
	def setMode(self, searchEpg = False, historySearch = False, manualSearch = False, switchTvRadio = False):
		self.setTabs()
		self.setUpcomingWidgets()
		
		if self.blinkTimer.getIsRunning():
			self.blinkTimer.reset()
		
		# TODO only hide if the plugin wasn't just started
		if not historySearch and self.oldMode != None:
			self.epgTabObjectList[self.oldMode].hide()
			
		if searchEpg:
			cur = None
			if self.oldMode == MULTI_EPG_NOW or self.oldMode == MULTI_EPG_NEXT or self.oldMode == SINGLE_EPG or self.oldMode == MULTI_EPG_PRIMETIME:
				cur = self["list"].getCurrent()
				if cur:
					searchString = cur[5]
			elif self.oldMode == TIMERLIST:
				cur = self["timerlist"].getCurrent()
				if cur:
					searchString = cur.name
			elif self.currentMode == EPGSEARCH_MANUAL:
				self.oldMode = self.currentMode
				self.currentMode = EPGSEARCH_RESULT
				searchString = self["search"].list[0][1].value
				self.epgTabObjectList[self.oldMode].hide()
				self.epgTabObjectList[self.currentMode].show(searchString, self.currentMode)
			if cur:
				self.currentMode = EPGSEARCH_RESULT
				self.epgTabObjectList[self.currentMode].show(searchString, self.currentMode)
		elif manualSearch:
			self.oldMode = self.currentMode
			self.currentMode = EPGSEARCH_MANUAL
			self.epgTabObjectList[self.oldMode].hide()
			self.epgTabObjectList[self.currentMode].show()
		elif self.currentMode == EPGSEARCH_HISTORY:
			if historySearch:
				self.oldMode = self.currentMode
				cur = self["history"].getCurrent()
				if cur:
					self.currentMode = EPGSEARCH_RESULT
					self.epgTabObjectList[self.oldMode].hide()
					self.epgTabObjectList[self.currentMode].show(cur, self.currentMode)
			else:
				self.epgTabObjectList[self.currentMode].show()
		elif self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == MULTI_EPG_PRIMETIME:
			self.epgTabObjectList[self.currentMode].show(self.currentBouquet, self.currentBouquetIndex, self.currentMode)
			# set the marker to the currently running service on plugin start
			if self.selectRunningService:
				self.selectRunningService = False
				playingSref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
				if not playingSref:
					return
				sRef = playingSref.toCompareString()
				
				i = 0
				while i < len(self["list"].list):
					if self["list"].list[i][2] == sRef:
						self.lastMultiEpgIndex = i
						self["list"].instance.moveSelectionTo(self.lastMultiEpgIndex)
						break
					i += 1
			elif self.oldMode == SINGLE_EPG or self.oldMode == EPGSEARCH_RESULT or self.oldMode == EPGSEARCH_HISTORY:
				if self.lastMultiEpgIndex > 0:
					self["list"].instance.moveSelectionTo(self.lastMultiEpgIndex)
				else:
					self["list"].instance.moveSelectionTo(0)
		elif self.currentMode == SINGLE_EPG:
			sRef = None
			if self.selectRunningService:
				playingSref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
				if playingSref:
					sRef = playingSref.toCompareString()
					if sRef in self["list"].bouquetServices[self.currentBouquetIndex]:
						self.lastMultiEpgIndex = self["list"].bouquetServices[self.currentBouquetIndex].index(sRef)
			if self.showOutdated and not self.hideOutdated:
				self.hideOutdated = True
			elif self.showOutdated and self.hideOutdated:
				self.showOutdated = False
				self.hideOutdated = False
			elif not self.showOutdated and not self.hideOutdated and not self.oldMode == EPGSEARCH_RESULT and not self.selectRunningService:
				self.lastMultiEpgIndex = self["list"].instance.getCurrentIndex()
				
			if self.selectRunningService:
				self.selectRunningService = False
				
			if switchTvRadio:
				self.oldMode = None
				
			self.epgTabObjectList[self.currentMode].show(self.oldMode, self.bouquetList[0], self.currentBouquet, self.currentBouquetIndex, self.currentMode, self.showOutdated, sRef)
		elif self.currentMode == TIMERLIST:
			self.onListSelectionChanged()
			self.epgTabObjectList[self.currentMode].show()
			
		if self.listStyle == STYLE_SINGLE_LINE:
			if (self.currentMode == SINGLE_EPG or self.currentMode == EPGSEARCH_RESULT) and (self.oldMode != SINGLE_EPG and self.oldMode != EPGSEARCH_RESULT):
				self.setUpcomingWidgets()
			elif (self.currentMode != SINGLE_EPG and self.currentMode != EPGSEARCH_RESULT) and (self.oldMode == SINGLE_EPG or self.oldMode == EPGSEARCH_RESULT):
				self.setUpcomingWidgets()
				
		self.setButtonText()
		self.setActions()
		
	############################################################################################
	# KEY HANDLING
	
	def keyEditMode(self):
		if self.configEditMode == False:
			self.configEditMode = True
			self["key_yellow"].setText(_("Edit Off"))
		else:
			self.configEditMode = False
			if self.configTabsShown:
				self["key_yellow"].setText(_("Edit On"))
			else:
				self["key_yellow"].setText("")
				
	def keyRed(self):
		if self.currentMode == EPGSEARCH_HISTORY:
			self.removeFromEpgSearchHistory()
		else:
			self.similarShown = not self.similarShown
		
			if not self.similarShown:
				self.epgTabObjectList[self.currentMode].hideSimilar()
				self["key_red"].setText("")
				self["epgRedActions"].setEnabled(False)
			else:
				if self.infoTextShown:
					self.keyInfo()
				self.epgTabObjectList[self.currentMode].showSimilar()
				self["key_red"].setText(_("return"))
				self["epgRedActions"].setEnabled(True)
				
	def keyGreen(self):
		if self.currentMode == TIMERLIST:
			sel = self["timerlist"].getCurrent()
			if sel is None:
				return
			
			data = (sel.begin, sel.end, sel.name, sel.description, sel.eit)
			self.addTimer(RecTimerEntry(self.session, sel.service_ref, checkOldTimers = True, dirname = preferredTimerPath(), *data))
		elif self.currentMode == EPGSEARCH_HISTORY:
			self.setMode(historySearch = True)
		else:
			cur = self["list"].getCurrent()
			if cur == None or cur[1] == None or cur[2] == "":
				return
			
			addTimer = True
			for timer in self.session.nav.RecordTimer.timer_list:
				if timer.eit == cur[1] and timer.service_ref.ref.toString() == cur[2]:
					addTimer = False
					self.deleteTimer(timer)
					self.setButtonText(timerAdded = True)
					self.getSimilarEvents()
					self.setEventViewPicon(cur)
					break
					
			if addTimer:
				# cur = ignoreMe, eventid, sRef, begin, duration, title, short, desc
				eit = cur[1]
				serviceref = ServiceReference(cur[2])
				begin = cur[3]
				end = cur[3] + cur[4]
				name = cur[5]
				description = cur[6]
				begin -= config.recording.margin_before.value * 60
				end += config.recording.margin_after.value * 60
				data = (begin, end, name, description, eit)
				# TimerEditList method
				self.addTimer(RecTimerEntry(self.session, serviceref, checkOldTimers = True, dirname = preferredTimerPath(), *data))
				
	def keyYellow(self):
		if self.currentMode == EPGSEARCH_HISTORY:
			self.setMode(manualSearch = True)
		elif self.configTabsShown:
			self.keyEditMode()
			
	def keyBlue(self):
		if self.currentMode == EPGSEARCH_RESULT:
			cur = self["list"].getCurrent()
			if cur == None or cur[5] == None:
				return
			self.epgTabObjectList[self.currentMode].updateEpgSearchHistory(cur[5]) # save the searchString in the search history
			# remove possibility to add the service name to the list of epg search terms
			self["key_blue"].setText("")
			self["epgBlueActions"].setEnabled(False)
		elif KEEP_OUTDATED_TIME > 0:
			if not self.showOutdated:
				self.showOutdated = True
			if self.similarShown:
				self.similarShown = False
				self["key_red"].setText("")
			self.setMode()
		
	def keyLeft(self):
		if self.configTabsShown:
			if self.configEditMode:
				self["settings"].handleKey(KEY_LEFT)
		elif self.currentMode == EPGSEARCH_MANUAL:
			self["search"].handleKey(KEY_LEFT)
		elif self.currentMode == EPGSEARCH_HISTORY:
			self["history"].pageUp()
		elif self.infoTextShown:
			self["infoText"].pageUp()
		elif self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == SINGLE_EPG or self.currentMode == MULTI_EPG_PRIMETIME or self.currentMode == EPGSEARCH_RESULT:
			self["list"].pageUp()
			
	def keyRight(self):
		if self.configTabsShown:
			if self.configEditMode:
				self["settings"].handleKey(KEY_RIGHT)
		elif self.currentMode == EPGSEARCH_MANUAL:
			self["search"].handleKey(KEY_RIGHT)
		elif self.currentMode == EPGSEARCH_HISTORY:
			self["history"].pageDown()
		elif self.infoTextShown:
			self["infoText"].pageDown()
		elif self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == SINGLE_EPG or self.currentMode == MULTI_EPG_PRIMETIME or self.currentMode == EPGSEARCH_RESULT:
			self["list"].pageDown()
			
	def keyUp(self):
		if self["list"].getVisible():
			self["list"].moveUp()
		elif self.currentMode == EPGSEARCH_HISTORY:
			self["history"].up()
		elif self.configTabsShown:
			self["settings"].instance.moveSelection(self["settings"].instance.moveUp)
		elif self.infoTextShown:
			self["infoText"].pageUp()
			
	def keyDown(self):
		if self["list"].getVisible():
			self["list"].moveDown()
		elif self.currentMode == EPGSEARCH_HISTORY:
			self["history"].down()
		elif self.configTabsShown:
			self["settings"].instance.moveSelection(self["settings"].instance.moveDown)
		elif self.infoTextShown:
			self["infoText"].pageDown()
			
	def keyExit(self):
		if self.infoTextShown:
			self.keyInfo()
			return
		
		if self.currentMode == EPGSEARCH_MANUAL or self.currentMode == EPGSEARCH_RESULT:
			self.oldMode = self.currentMode
			self.currentMode = EPGSEARCH_HISTORY
			self.epgTabObjectList[self.oldMode].hide()
			self.epgTabObjectList[self.currentMode].show()
			self.setActions()
			self.setButtonText()
		else:
			self.blinkTimer.timer.callback.remove(self.setEventPiconBlinkState)
			self.blinkTimer.timer.callback.remove(self.setRecordingBlinkState)
			if config.plugins.merlinEpgCenter.rememberLastTab.value:
				if self.currentMode > NUM_EPG_TABS:
					config.plugins.merlinEpgCenter.lastUsedTab.value = NUM_EPG_TABS
				else:
					config.plugins.merlinEpgCenter.lastUsedTab.value = self.currentMode
			config.plugins.merlinEpgCenter.save()
			self.session.nav.RecordTimer.on_state_change.remove(self.onStateChange)
			self.releaseEpgBaseTab()
			config.usage.show_message_when_recording_starts.value = self.showRecordingMessage
			self.blinkTimer.shutdown()
			self.close(None)
			
	def keyDirection(self, direction):
		if self.similarShown:
			self.keyRed()
		elif self.infoTextShown:
			self.keyInfo()
			
		if self.configEditMode:
			if direction == -1:
				self["settings"].handleKey(KEY_BACKSPACE)
			elif direction == 1:
				self["settings"].handleKey(KEY_DELETE)
		elif self.currentMode == EPGSEARCH_MANUAL:
			if direction == -1:
				self["search"].handleKey(KEY_BACKSPACE)
			elif direction == 1:
				self["search"].handleKey(KEY_DELETE)
		else:
			if self.configTabsShown:
				numTabs = NUM_CONFIG_TABS
			else:
				numTabs = NUM_EPG_TABS
				
			self.oldMode = self.currentMode
			if direction == 1: # right
				self.currentMode += 1
				if self.currentMode > numTabs:
					self.currentMode = 0 # set to first tab
			else:
				self.currentMode -= 1
				if self.currentMode >= numTabs:
					self.currentMode = numTabs -1 # set to last tab -1
				elif self.currentMode == -1:
					self.currentMode = numTabs # set to last tab
			
			if self.configTabsShown:
				self.setTabs()
				self.configTabObjectList[self.currentMode].settingsWidget.setCurrentIndex(0)
				self.configTabObjectList[self.currentMode].show()
			else:
				self.setMode()
				
	def keyNumber(self, number):
		if self.configTabsShown:
			if self.configEditMode:
				self["settings"].handleKey(KEY_0 + number)
			else:
				if number != 0 and self.currentMode != number -1 and number -1 <= NUM_CONFIG_TABS:
					self["tab_text_%d" % self.currentMode].instance.setForegroundColor(parseColor("#ffffff")) # inactive
					self.currentMode = number -1
					self.setTabs()
					self.configTabObjectList[self.currentMode].settingsWidget.setCurrentIndex(0)
					self.configTabObjectList[self.currentMode].show()
			return
		elif self.similarShown:
			self.keyRed()
		elif self.infoTextShown:
			self.keyInfo()
			
		self.oldMode = self.currentMode
		if self.oldMode == MULTI_EPG_NOW or self.oldMode == MULTI_EPG_NEXT or self.oldMode == MULTI_EPG_PRIMETIME:
			self.lastMultiEpgIndex = self["list"].instance.getCurrentIndex()
			
		if self.currentMode == EPGSEARCH_MANUAL:
			self["search"].handleKey(KEY_0 + number)
		else:
			if self.oldMode == number -1: # same mode, there's nothing to do
				return
			elif number <= (NUM_EPG_TABS +1): # make sure one of our tabs was selected
				self.currentMode = number -1 # 0 based
				if number == 6 and self.oldMode != EPGSEARCH_RESULT: # epg search
					self.setMode(searchEpg = True)
					
					# reset / don't show similar events option
					self.similarShown = False
					self["key_red"].setText("")
					self["epgRedActions"].setEnabled(False)
					
					# add possibility to add the service name to the list of epg search terms
					self["key_blue"].setText(_("Set search term"))
					self["epgBlueActions"].setEnabled(True)
				else:
					self.setMode()
			
	def keyOk(self):
		if self.currentMode == EPGSEARCH_MANUAL:
			self.epgTabObjectList[self.currentMode].updateEpgSearchHistory() # save the searchString in the search history
			self.setMode(searchEpg = True)
		elif self.currentMode == EPGSEARCH_HISTORY:
			self.setMode(historySearch = True)
		elif self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == SINGLE_EPG or self.currentMode == MULTI_EPG_PRIMETIME:
			cur = self["list"].getCurrent()
			if cur != None:
				# update the infobar servicelist...
				self.infoBarInstance.epg_bouquet = self.bouquetList[self.currentBouquetIndex][1]
				self.infoBarInstance.zapToService(eServiceReference(cur[2]))
				# ...and exit
				self.keyExit()
				
	def keyBouquetUp(self):
		if self.infoTextShown:
			self.keyInfo()
			
		if self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == MULTI_EPG_PRIMETIME:
			if (self.currentBouquetIndex +1)  <= (len(self.bouquetList) -1):
				self.currentBouquetIndex += 1
			else:
				self.currentBouquetIndex = 0
			self.prepareFillMultiEpg()
			
			# set selection to the first list entry
			self.lastMultiEpgIndex = 0
			self["list"].instance.moveSelectionTo(self.lastMultiEpgIndex)
		elif self.currentMode == SINGLE_EPG:
			self.epgTabObjectList[self.currentMode].changeService(1)
			
	def keyBouquetDown(self):
		if self.infoTextShown:
			self.keyInfo()
			
		if self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == MULTI_EPG_PRIMETIME:
			if (self.currentBouquetIndex - 1) >= 0:
				self.currentBouquetIndex -= 1
			else:
				self.currentBouquetIndex = len(self.bouquetList) - 1
			self.prepareFillMultiEpg()
			
			# set selection to the first list entry
			self.lastMultiEpgIndex = 0
			self["list"].instance.moveSelectionTo(self.lastMultiEpgIndex)
		elif self.currentMode == SINGLE_EPG:
			self.epgTabObjectList[self.currentMode].changeService(-1)
			
	def keyMenu(self):
		if self.infoTextShown:
			self.keyInfo()
		if self.similarShown:
			self.keyRed()
		self.toggleConfigTabs()
		
	# show short and long description for the selected event
	def keyInfo(self):
		if self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == SINGLE_EPG or self.currentMode == MULTI_EPG_PRIMETIME or self.currentMode == EPGSEARCH_RESULT:
			if self.infoTextShown:
				self["infoText"].hide()
				self["list"].show()
				if config.plugins.merlinEpgCenter.showEventInfo.value:
					self["description"].show()
					
			else:
				# get the selected entry
				cur = self["list"].getCurrent()
				title = cur[5]
				shortDesc = cur[6]
				description = cur[7]
				
				if title != None and title != "":
					infoText = title
				else:
					infoText = ""
					
				if shortDesc != None and shortDesc != "" and shortDesc != title:
					if infoText == "":
						infoText = shortDesc
					else:
						infoText = ''.join([infoText, "\n\n", shortDesc])
				if description != None and description != "":
					if infoText == "":
						infoText = description
					else:
						infoText = ''.join([infoText, "\n\n", description])
					
				self["infoText"].setText(infoText)
				size = self["list"].instance.size()
				self["infoText"].resize(eSize(size.width() - 5, size.height()))
				self["list"].hide()
				self["description"].hide()
				self["infoText"].show()
				
			self.infoTextShown = not self.infoTextShown
			
	def keyTv(self):
		self.switchTvRadio(MODE_TV)
		
	def keyRadio(self):
		self.switchTvRadio(MODE_RADIO)
		
	############################################################################################
	# TAB TOGGLING
	
	def toggleConfigTabs(self):
		if self.configTabsShown: # show epg tabs again
			self["settings"].hide()
			self.configTabsShown = False
			self["tab_text_%d" % self.currentMode].instance.setForegroundColor(parseColor("#ffffff")) # inactive
			self.currentMode = self.savedCurrentMode
			if self.numNextEvents > 0 and (self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == MULTI_EPG_PRIMETIME):
				self["upcomingSeparator"].show()
			self.oldMode = self.savedOldMode
			self.setTabText(self.tabTextEpgList)
			if self.currentMode <= NUM_EPG_TABS:
				self["tab_text_%d" % self.currentMode].instance.setForegroundColor(parseColor("#ef7f1a")) # active
				self["tabbar"].setPixmapNum(self.currentMode)
			else:
				self["tab_text_%d" % NUM_EPG_TABS].instance.setForegroundColor(parseColor("#ef7f1a")) # active
				self["tabbar"].setPixmapNum(NUM_EPG_TABS)
			
			if self.currentMode == EPGSEARCH_MANUAL:
				self.setMode(manualSearch = True)
			elif self.currentMode == EPGSEARCH_RESULT:
				self["list"].show()
			else:
				self.setMode()
				
			self.configEditMode = True
			self.keyEditMode()
			
			# reset the timer button text
			cur = self["list"].getCurrent()
			if cur is not None:
				self.setTimerButtonState(cur)
		else: # show config tabs
			self["upcoming"].hide()
			self["upcomingSeparator"].hide()
			self.epgTabObjectList[self.currentMode].hide()
			if self.currentMode <= NUM_EPG_TABS:
				self["tab_text_%d" % self.currentMode].instance.setForegroundColor(parseColor("#ffffff")) # inactive
			else:
				self["tab_text_%d" % NUM_EPG_TABS].instance.setForegroundColor(parseColor("#ffffff")) # inactive
			self.savedCurrentMode = self.currentMode
			self.savedOldMode = self.oldMode
			self.currentMode = 0 # first config tab
			self.setTabText(self.tabTextConfigList)
			self["tab_text_%d" % self.currentMode].instance.setForegroundColor(parseColor("#ef7f1a")) # active
			self["tabbar"].setPixmapNum(self.currentMode)
			self.configTabsShown = True
			self.configEditMode = True
			self.keyEditMode()
			self["settings"].show()
			self.configTabObjectList[self.currentMode].show()
			
		self.setButtonText()
		self.setActions()
			
	############################################################################################
	# EVENT INFORMATION
	
	def setVideoPicture(self, configElement = None):
		if config.plugins.merlinEpgCenter.showEventInfo.value:
			if config.plugins.merlinEpgCenter.showVideoPicture.value:
				self["videoPicture"].show()
			else:
				self["videoPicture"].hide()
			self.setDescriptionSize()
			
	def setDescriptionSize(self):
		lineHeight = int(fontRenderClass.getInstance().getLineHeight(self["description"].instance.getFont()))
		if config.plugins.merlinEpgCenter.showVideoPicture.value:
			maxVisibleLines = int((self.videoPicturePosY - self.descriptionPosY - 5) / lineHeight)
		else:
			maxVisibleLines = int(self.descriptionHeightMax / lineHeight)
		newHeight = lineHeight * maxVisibleLines
		self["description"].instance.resize(eSize(self.descriptionWidthMax, newHeight))
		
	def setEventInfo(self, configElement = None):
		if config.plugins.merlinEpgCenter.showEventInfo.value:
			newSize = eSize(self.listWidthMin, self.listHeightMin)
			self["eventInfoSeparator"].show()
			self["picon"].show()
			self["serviceName"].show()
			self["eventTitle"].show()
			self["beginTime"].show()
			self["eventProgress"].show()
			self["endTime"].show()
			self["duration"].show()
			self["remaining"].show()
			self["description"].show()
			self["videoPicture"].show()
		else:
			newSize = eSize(self.listWidthMax, self.listHeightMin)
			self["eventInfoSeparator"].hide()
			self["picon"].hide()
			self["serviceName"].hide()
			self["eventTitle"].hide()
			self["beginTime"].hide()
			self["eventProgress"].hide()
			self["endTime"].hide()
			self["duration"].hide()
			self["remaining"].hide()
			self["description"].hide()
			self["videoPicture"].hide()
			
		border = 5
		self["timerlist"].instance.resize(newSize)
		self["search"].instance.resize(eSize(newSize.width() - border, newSize.height()))
		self["history"].instance.resize(eSize(newSize.width() - border, newSize.height()))
		self["settings"].instance.resize(eSize(newSize.width() - border, newSize.height()))
		self["upcomingSeparator"].instance.resize(eSize(newSize.width() + border, newSize.height())) # touch the event info separator
		self["timerlist"].setMaxWidth(newSize)
		
		self.setUpcomingWidgets()
		self.setVideoPicture()
		self.setDescriptionSize()
		
