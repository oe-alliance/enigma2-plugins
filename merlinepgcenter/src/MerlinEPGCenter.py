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


# for localized messages
from . import _


NUM_EPG_TABS = 5 # 0 based
NUM_CONFIG_TABS = 3 # 0 based

STYLE_SINGLE_LINE = "0"
STYLE_SHORT_DESCRIPTION = "1"

MODE_TV = 0
MODE_RADIO = 1

TIMER_TYPE_RECORD = 0
TIMER_TYPE_AUTOTIMER = 1

LIST_MODE_TIMER = 0
LIST_MODE_AUTOTIMER = 1

TAB_TEXT_EPGLIST = (_("Now"), _("Upcoming"), _("Single"), _("Prime Time"), _("Timer"), _("Search"))
TAB_TEXT_CONFIGLIST = [_("General"), _("Lists"), _("Event Info"), _("Keys"), "", ""]
	
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
from Components.TimerSanityCheck import TimerSanityCheck
from Components.UsageConfig import preferredTimerPath
from Components.VideoWindow import VideoWindow
from Components.VolumeBar import VolumeBar
from enigma import eServiceReference, eServiceCenter, eEPGCache, getDesktop, eSize, eTimer, fontRenderClass, ePoint, gFont, gPixmapPtr
from GlobalActions import globalActionMap
from math import fabs
import NavigationInstance
from RecordTimer import AFTEREVENT, RecordTimerEntry
from Screens.EpgSelection import EPGSelection
from Screens.Screen import Screen
from Screens.TimerEdit import TimerEditList, TimerSanityConflict
from Screens.TimerEntry import TimerEntry, TimerLog
from ServiceReference import ServiceReference
from skin import parseColor, loadSkin
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN, SCOPE_HDD
from Tools.LoadPixmap import LoadPixmap

# OWN IMPORTS
from Components.VolumeControl import VolumeControl
from ConfigTabs import KEEP_OUTDATED_TIME, ConfigBaseTab, ConfigGeneral, ConfigListSettings, ConfigEventInfo, ConfigKeys, SKINDIR, SKINLIST, STYLE_SIMPLE_BAR, STYLE_PIXMAP_BAR, STYLE_MULTI_PIXMAP, STYLE_PERCENT_TEXT, STYLE_SIMPLE_BAR_LIST_OFF, STYLE_PIXMAP_BAR_LIST_OFF, STYLE_MULTI_PIXMAP_LIST_OFF, STYLE_PERCENT_TEXT_LIST_OFF
from EpgActions import MerlinEPGActions
from EpgCenterList import EpgCenterList, EpgCenterTimerlist, MODE_HD, MODE_XD, MODE_SD, MULTI_EPG_NOW, MULTI_EPG_NEXT, SINGLE_EPG, MULTI_EPG_PRIMETIME, TIMERLIST, EPGSEARCH_HISTORY, EPGSEARCH_RESULT, EPGSEARCH_MANUAL, UPCOMING
from EpgTabs import EpgBaseTab, EpgNowTab, EpgNextTab, EpgSingleTab, EpgPrimeTimeTab, EpgTimerListTab, EpgSearchHistoryTab, EpgSearchManualTab, EpgSearchResultTab
from HelperFunctions import PiconLoader, findDefaultPicon, ResizeScrollLabel, BlinkTimer, LIST_TYPE_EPG, LIST_TYPE_UPCOMING, TimerListObject, EmbeddedVolumeControl
from SkinFinder import SkinFinder

# check for Autotimer support
try:
	from Plugins.Extensions.AutoTimer.plugin import autotimer
	from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer, XML_CONFIG
	from Plugins.Extensions.AutoTimer.AutoTimerConfiguration import buildConfig
	from Plugins.Extensions.AutoTimer.AutoTimerComponent import preferredAutoTimerComponent
	from Plugins.Extensions.AutoTimer.AutoTimerEditor import AutoTimerEditor, weekdays
	from Plugins.Extensions.AutoTimer.AutoTimerOverview import AutoTimerPreview
	from Plugins.Extensions.AutoTimer.AutoTimerImporter import AutoTimerImporter
	AUTOTIMER = True
	# now we need a ChoiceBox to select between timer and autotimer on green button
	from Screens.ChoiceBox import ChoiceBox
except ImportError:
	AUTOTIMER = False

# check for IMDb support
try:
	from Plugins.Extensions.IMDb.plugin import IMDB
	IMDB_INSTALLED = True
except ImportError:
	IMDB_INSTALLED = False

# check for YTTrailer support
try:
	from Plugins.Extensions.YTTrailer.plugin import YTTrailerList
	YTTRAILER_INSTALLED = True
except ImportError:
	YTTRAILER_INSTALLED = False
	

class MerlinEPGCenter(TimerEditList, MerlinEPGActions, EmbeddedVolumeControl):
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

	def __init__(self, session, servicelist, currentBouquet, bouquetList, currentIndex, startTab = None, doSearch = False):
		Screen.__init__(self, session)
		MerlinEPGActions.__init__(self) # note: this overwrites TimerEditList.["actions"]
		EmbeddedVolumeControl.__init__(self)
		
		self.session = session
		self.servicelist = servicelist
		self.currentBouquet = currentBouquet # eServiceReference of the current bouquet
		self.currentBouquetIndex = currentIndex # current bouquet index from InfoBar
		self.bouquetList = bouquetList # a list of tuples of all bouquets (Name, eServicereference)
		self.startTab = startTab
		self.doSearch = doSearch
		
		self.onChangedEntry = [ ]
		from Screens.InfoBar import InfoBar
		self.infoBarInstance = InfoBar.instance
		self.epgcache = eEPGCache.getInstance()
		
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
		self.autoTimerPixmapLarge = None
		self.removeAutoTimerInstance = False
		self.timerListMode = LIST_MODE_TIMER
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
		self["upcoming"].mode = UPCOMING
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
		self["eventProgressText"] = Label("")
		self["endTime"] = Label("")
		self["duration"] = Label("")
		self["remaining"] = MultiColorLabel()
		self["isRecording"] = Pixmap()
		self["description"] = Label("")
		self["bouquet"] = Label("")
		self["videoPicture"] = VideoWindow(decoder = 0, fb_width = self.desktopSize.width(), fb_height = self.desktopSize.height())
		self["volume"] = VolumeBar()
		self["mute"] = Pixmap()
		
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
		
		self.widgetFontSizes = []
		
		self.initTabLabels(TAB_TEXT_EPGLIST)
		
		self.getPrimeTime()
		self.initEpgBaseTab()
		
		if config.plugins.merlinEpgCenter.selectRunningService.value:
			self.selectRunningService = True
		else:
			self.selectRunningService = False
			
		self.lastMultiEpgIndex = None
		self.showOutdated = False
		self.hideOutdated = False
		self.numNextEvents = None
		self.configTabsShown = False
		self.configEditMode = False
		self.oldMode = None
		self.currentMode = None
		
		self.onLayoutFinish.append(self.startRun)
		self.onShown.append(self.setListPixmaps)
		self.onShown.append(self.setTabs)
		self.onShown.append(self.setBouquetName)
		
	############################################################################################
	# INITIALISATION & CLEANUP
	
	def startRun(self):
		self.getWidgetSizes()
		self.searchField.help_window.hide()
		self.hideWidgets()
		
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
		
		# Initialise the blink timer if there's already a recording running
		self.blinkTimer.gotRecordEvent(None, None)
		
		self.session.nav.RecordTimer.on_state_change.append(self.onStateChange)
		
		self.blinkTimer.appendList(self["list"])
		self.blinkTimer.appendList(self["upcoming"])
		self.blinkTimer.timer.callback.append(self.setEventPiconBlinkState)
		self.blinkTimer.timer.callback.append(self.setRecordingBlinkState)
		
		self["list"].onSelectionChanged.append(self.onListSelectionChanged)
		self["timerlist"].onSelectionChanged.append(self.onListSelectionChanged)
		
		self.configTabObjectList = []
		self.configTabObjectList.append(ConfigGeneral())
		self.configTabObjectList.append(ConfigListSettings())
		self.configTabObjectList.append(ConfigEventInfo())
		self.configTabObjectList.append(ConfigKeys())
		
		# similar events
		self.similarTimer = eTimer()
		self.similarTimer.callback.append(self.getSimilarEvents)
		self.similarTimer.callback.append(self.getUpcomingEvents)
		self.similarShown = False
		
		searchFieldPos = self["search"].getPosition()
		self["search"].getCurrent()[1].help_window.instance.move(ePoint(searchFieldPos[0], searchFieldPos[1] + 40))
		
		self.setStartTab(self.startTab, self.doSearch)
		self.setBouquetName()
		
		self.savedVolUp = None
		self.savedVolDown = None
		self.savedVolMute = None
		self.savedMuteDialog = None
		
		self.setNotifier()
		
	def suspend(self):
		self.suspendedInMode = self.infoBarInstance.servicelist.mode
		self.session.nav.RecordTimer.on_state_change.remove(self.onStateChange)
		self.clockTimer.callback.remove(self.checkTimeChange)
		# reset the timer tab to Timer
		if self.timerListMode == LIST_MODE_AUTOTIMER:
			self.timerListMode = LIST_MODE_TIMER
			self["tab_text_%d" % TIMERLIST].setText(_("Timer"))
			
		if config.plugins.merlinEpgCenter.embeddedVolume.value:
			self.unsetVolumeControl()
			self.savedMuteDialog = VolumeControl.instance.muteDialog
			if self.getIsMuted():
				self.savedMuteDialog.show()
				
		if self.blinkTimer.getIsRunning():
			self["isRecording"].hide()
			
		self.blinkTimer.suspend()
		
		if self.similarShown:
			self.keyRed(forceHideSimilar = True)
			
		if self.currentMode > NUM_EPG_TABS:
			config.plugins.merlinEpgCenter.lastUsedTab.value = NUM_EPG_TABS
		else:
			config.plugins.merlinEpgCenter.lastUsedTab.value = self.currentMode
		config.plugins.merlinEpgCenter.save()
			
	def resume(self):
		# reset the tab text color of the last tab before suspending
		lastTab = config.plugins.merlinEpgCenter.lastUsedTab.value
		self["tab_text_%d" % lastTab].instance.setForegroundColor(parseColor("#ffffff")) # inactive
		
		# reread bouquet information if TV or radio mode was changed while we were suspended
		if self.suspendedInMode is not self.infoBarInstance.servicelist.mode:
			self.updateBouquets()
			
		if config.plugins.merlinEpgCenter.embeddedVolume.value:
			VolumeControl.instance.muteDialog = self.savedMuteDialog
			self.setVolumeControl()
			self.setMutePixmap()
			if self.getIsMuted():
				self.savedMuteDialog.hide()
				
		self.getPrimeTime()
		self.session.nav.RecordTimer.on_state_change.append(self.onStateChange)
		self.clockTimer.callback.append(self.checkTimeChange)
		self.checkTimeChange()
		self.blinkTimer.resume()
		
	############################################################################################
	# TAB STUFF
	
	def setStartTab(self, startTab, doSearch):
		if doSearch:
			lastUsedTab = config.plugins.merlinEpgCenter.lastUsedTab.value
			self["tab_text_%d" % lastUsedTab].instance.setForegroundColor(parseColor("#ffffff")) # inactive
			self.oldMode = EPGSEARCH_HISTORY
			self.currentMode = EPGSEARCH_HISTORY
			self.epgTabObjectList[self.oldMode].hide()
			self.epgTabObjectList[self.currentMode].show()
			
		if startTab is not None:
			if self.currentMode != startTab:
				self.oldMode = self.currentMode
				self.currentMode = startTab
		else:
			if config.plugins.merlinEpgCenter.rememberLastTab.value:
				self.currentMode = config.plugins.merlinEpgCenter.lastUsedTab.value
			else:
				self.currentMode = 0
		self.setMode(doSearch = doSearch)
		
		if config.plugins.merlinEpgCenter.selectRunningService.value and (self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == SINGLE_EPG or self.currentMode == MULTI_EPG_PRIMETIME):
			self.setSelectionToRunningService()
			self.setBouquetName()
			
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
		
	def initTabLabels(self, tabList):
		i = 0
		while i <= NUM_EPG_TABS:
			if (i == MULTI_EPG_PRIMETIME) and config.plugins.merlinEpgCenter.showPrimeTimeValue.value:
				hours = str(config.plugins.merlinEpgCenter.primeTime.value[0])
				minutes = str(config.plugins.merlinEpgCenter.primeTime.value[1])
				timeString = hours + ":" + minutes
				self["tab_text_%d" % MULTI_EPG_PRIMETIME] = Label(timeString)
			else:
				self["tab_text_%d" % i] = Label(tabList[i])
			i += 1
			
	def setTabText(self, tabList):
		if self.configTabsShown:
			numTabs = NUM_CONFIG_TABS
		else:
			numTabs = NUM_EPG_TABS
			
		i = 0
		while i <= numTabs:
			if (not self.configTabsShown) and (i == MULTI_EPG_PRIMETIME) and config.plugins.merlinEpgCenter.showPrimeTimeValue.value:
				hours = str(config.plugins.merlinEpgCenter.primeTime.value[0])
				minutes = str(config.plugins.merlinEpgCenter.primeTime.value[1])
				timeString = hours + ":" + minutes
				self["tab_text_%d" % MULTI_EPG_PRIMETIME].setText(timeString)
			else:
				self["tab_text_%d" % i].setText(tabList[i])
			i += 1
			
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
			self["tab_text_%d" % numTabs].instance.setForegroundColor(parseColor(config.plugins.merlinEpgCenter.tabTextColorSelected.value)) # active
		else:
			self["tab_text_%d" % self.currentMode].instance.setForegroundColor(parseColor(config.plugins.merlinEpgCenter.tabTextColorSelected.value)) # active
			
	############################################################################################
	# VOLUME CONTROL
	
	def toggleEmbeddedVolume(self, configElement = None):
		if configElement.value:
			self.setVolumeControl()
		else:
			self.unsetVolumeControl()
			
		self.setMutePixmap()
		
	def setVolumeControl(self):
		global globalActionMap
		self.savedVolUp = globalActionMap.actions["volumeUp"]
		self.savedVolDown = globalActionMap.actions["volumeDown"]
		self.savedVolMute = globalActionMap.actions["volumeMute"]
		globalActionMap.actions["volumeUp"] = self.volUp
		globalActionMap.actions["volumeDown"] = self.volDown
		globalActionMap.actions["volumeMute"] = self.volMute
		self.setMutePixmap()
		
	def unsetVolumeControl(self):
		if self.savedVolUp == None:
			return
		global globalActionMap
		globalActionMap.actions["volumeUp"] = self.savedVolUp
		globalActionMap.actions["volumeDown"] = self.savedVolDown
		globalActionMap.actions["volumeMute"] = self.savedVolMute
		
	############################################################################################
	# MISC FUNCTIONS
	
	def setProgressbarStyle(self, configElement = None):
		if not config.plugins.merlinEpgCenter.showEventInfo.value:
			return
			
		if config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_SIMPLE_BAR or config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_SIMPLE_BAR_LIST_OFF:
			self["eventProgressImage"].hide()
			self["eventProgress"].instance.setPixmap(gPixmapPtr())
			self["eventProgressText"].hide()
			self["eventProgress"].show()
		elif config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_PIXMAP_BAR or config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_PIXMAP_BAR_LIST_OFF:
			self["eventProgressImage"].hide()
			self["eventProgressText"].hide()
			if self.progressPixmap == None:
				pixmapPath = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/EventProgress.png")
				self.progressPixmap = LoadPixmap(cached = False, path = pixmapPath)
			self["eventProgress"].instance.setPixmap(self.progressPixmap)
			self["eventProgress"].show()
		elif config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_MULTI_PIXMAP or config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_MULTI_PIXMAP_LIST_OFF:
			self["eventProgress"].hide()
			self["eventProgressText"].hide()
			self["eventProgressImage"].show()
		elif config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_PERCENT_TEXT or config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_PERCENT_TEXT_LIST_OFF:
			self["eventProgressImage"].hide()
			self["eventProgress"].instance.setPixmap(gPixmapPtr())
			self["eventProgress"].hide()
			self["eventProgressText"].show()
			
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
		self["eventProgressText"].hide()
		self["isRecording"].hide()
		self["volume"].hide()
		self["mute"].hide()
		
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
		# self["beginTime"]
		for (attrib, value) in self["beginTime"].skinAttributes:
			if attrib == "font":
				font = [x for x in value.split(";")]
				self.widgetFontSizes.append(("beginTime", font[0], int(font[1])))
		# self["endTime"]
		for (attrib, value) in self["endTime"].skinAttributes:
			if attrib == "font":
				font = [x for x in value.split(";")]
				self.widgetFontSizes.append(("endTime", font[0], int(font[1])))
		# self["duration"]
		for (attrib, value) in self["duration"].skinAttributes:
			if attrib == "font":
				font = [x for x in value.split(";")]
				self.widgetFontSizes.append(("duration", font[0], int(font[1])))
		# self["remaining"]
		for (attrib, value) in self["remaining"].skinAttributes:
			if attrib == "font":
				font = [x for x in value.split(";")]
				self.widgetFontSizes.append(("remaining", font[0], int(font[1])))
		# self["description"]
		for (attrib, value) in self["description"].skinAttributes:
			if attrib == "position":
				self.descriptionPosX, self.descriptionPosY = [int(x) for x in value.split(",")]
			if attrib == "size":
				self.descriptionWidthMax, self.descriptionHeightMax = [int(x) for x in value.split(",")]
			if attrib == "font":
				font = [x for x in value.split(";")]
				self.widgetFontSizes.append(("description", font[0], int(font[1])))
		# self["videoPicture"]
		for (attrib, value) in self["videoPicture"].skinAttributes:
			if attrib == "position":
				self.videoPicturePosX, self.videoPicturePosY = [int(x) for x in value.split(",")]
		# self["infoText"]
		for (attrib, value) in self["infoText"].skinAttributes:
			if attrib == "font":
				font = [x for x in value.split(";")]
				self.widgetFontSizes.append(("infoText", font[0], int(font[1])))
				
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
		config.plugins.merlinEpgCenter.showVideoPicture.addNotifier(self.setVideoPicture, initial_call = False)
		config.plugins.merlinEpgCenter.showEventInfo.addNotifier(self.setEventInfo, initial_call = True)
		config.plugins.merlinEpgCenter.showInputHelp.addNotifier(self.setInputHelp, initial_call = False)
		config.plugins.merlinEpgCenter.listStyle.addNotifier(self.setListStyle, initial_call = False)
		config.plugins.merlinEpgCenter.skinSelection.addNotifier(self.setSkinFile, initial_call = True)
		config.plugins.merlinEpgCenter.numNextEvents.addNotifier(self.setUpcomingWidgets, initial_call = True)
		config.plugins.merlinEpgCenter.listItemHeight.addNotifier(self.setUpcomingWidgets, initial_call = False)
		config.plugins.merlinEpgCenter.listProgressStyle.addNotifier(self.setProgressbarStyle, initial_call = True)
		config.plugins.merlinEpgCenter.adjustFontSize.addNotifier(self.setFontSizes, initial_call = True)
		config.plugins.merlinEpgCenter.embeddedVolume.addNotifier(self.toggleEmbeddedVolume, initial_call = True)
		
	def removeNotifier(self):
		self["list"].onSelectionChanged.remove(self.onListSelectionChanged)
		self["timerlist"].onSelectionChanged.remove(self.onListSelectionChanged)
		
		for configTabObject in self.configTabObjectList:
			configTabObject.removeNotifier()
		
		config.plugins.merlinEpgCenter.primeTime.removeNotifier(self.getPrimeTime)
		config.plugins.merlinEpgCenter.showVideoPicture.removeNotifier(self.setVideoPicture)
		config.plugins.merlinEpgCenter.showEventInfo.removeNotifier(self.setEventInfo)
		config.plugins.merlinEpgCenter.showInputHelp.removeNotifier(self.setInputHelp)
		config.plugins.merlinEpgCenter.listStyle.removeNotifier(self.setListStyle)
		config.plugins.merlinEpgCenter.skinSelection.removeNotifier(self.setSkinFile)
		config.plugins.merlinEpgCenter.numNextEvents.removeNotifier(self.setUpcomingWidgets)
		config.plugins.merlinEpgCenter.listItemHeight.removeNotifier(self.setUpcomingWidgets)
		config.plugins.merlinEpgCenter.listProgressStyle.removeNotifier(self.setProgressbarStyle)
		config.plugins.merlinEpgCenter.adjustFontSize.removeNotifier(self.setFontSizes)
		config.plugins.merlinEpgCenter.embeddedVolume.removeNotifier(self.toggleEmbeddedVolume)
		
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
		
	def setFontSizes(self, configElement = None):
		diff = configElement.getValue()
		
		for widget, font, fontSize in self.widgetFontSizes:
			if widget == "infoText":
				self[widget].long_text.setFont(gFont(font, fontSize + diff))
			else:
				self[widget].instance.setFont(gFont(font, fontSize + diff))
			
	def getPrimeTime(self, configElement = None):
		now = localtime(time())
		dt = datetime(now.tm_year, now.tm_mon, now.tm_mday, config.plugins.merlinEpgCenter.primeTime.value[0], config.plugins.merlinEpgCenter.primeTime.value[1])
		self.primeTime = int(mktime(dt.timetuple()))
		EpgBaseTab.primeTime = self.primeTime
		
	def addTimer(self, timer):
		if self.currentMode == TIMERLIST:
			if self.timerListMode == LIST_MODE_TIMER:
				self.session.openWithCallback(self.finishedAdd, TimerEntry, timer)
			elif self.timerListMode == LIST_MODE_AUTOTIMER:
				self.addAutotimerFromString("", addNewTimer = True)
		else:
			self.session.openWithCallback(self.finishedAdd, TimerEntry, timer)
			
	def addTimerEntry(self):
		cur = self["list"].getCurrent()
		if cur == None or cur[1] == None or cur[2] == "":
			return
			
		# cur = ignoreMe, eventid, sRef, begin, duration, title, short, desc
		eit = cur[1]
		serviceref = ServiceReference(cur[2])
		begin = cur[3]
		end = cur[3] + cur[4]
		name = cur[5]
		description = cur[6]
		begin -= config.recording.margin_before.getValue() * 60
		end += config.recording.margin_after.getValue() * 60
		data = (begin, end, name, description, eit)
		# TimerEditList method
		self.addTimer(RecordTimerEntry(serviceref, checkOldTimers = True, dirname = preferredTimerPath(), *data))
		
	def timerChoice(self):
		choices = []
		choices.append((_("Record or zap timer"), TIMER_TYPE_RECORD))
		choices.append((_("AutoTimer timer"), TIMER_TYPE_AUTOTIMER))
		self.session.openWithCallback(self.cbTimerChoice, ChoiceBox, title = _("Please select a timer type to add:"), list = choices, keys=["green", "yellow"])
		
	def cbTimerChoice(self, result):
		if not result:
			return
		elif result[1] == TIMER_TYPE_RECORD:
			self.addTimerEntry()
		elif result[1] == TIMER_TYPE_AUTOTIMER:
			# cur = ignoreMe, eventid, sRef, begin, duration, title, short, desc
			cur = self["list"].getCurrent()
			if cur == None or cur[1] == None or cur[2] == "":
				return
				
			self.addAutotimerFromString(cur[5], addNewTimer = True, begin = cur[3], end = cur[3] + cur[4], sRef = ServiceReference(cur[2]))
			
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
			self.updateState()
			
			cur = self["list"].getCurrent()
			if cur is not None:
				self.key_green_choice = self.ADD_TIMER
				self.setTimerButtonState(cur)
				self.setButtonText(timerAdded = True)
				self.getSimilarEvents()
				
	# TimerEditList function (overwritten to either edit a timer or AutoTimer timer)
	def openEdit(self):
		cur = self["timerlist"].getCurrent()
		if cur:
			if isinstance(cur, RecordTimerEntry):
				self.session.openWithCallback(self.finishedEdit, TimerEntry, cur)
			else: # AutoTimer entry
				autotimerEntry = None
				self.getAutoTimerInstance()
				
				# find the corresponding AutoTimer entry by id
				timerList = autotimer.getTimerList()
				for autotimerEntry in timerList:
					if autotimerEntry.getId() == cur.autoTimerId:
						break
						
				if autotimerEntry:
					self.session.openWithCallback(self.cbOpenEdit, AutoTimerEditor, autotimerEntry)
					
				self.deleteAutoTimerInstance()
				
	# TimerEditList function (overwritten to either edit a timer or AutoTimer timer)
	def showLog(self):
		cur = self["timerlist"].getCurrent()
		if cur:
			if isinstance(cur, RecordTimerEntry):
				self.session.openWithCallback(self.finishedEdit, TimerLog, cur)
			else:
				global autotimer
				self.getAutoTimerInstance()
				total, new, modified, timers, conflicts, similars = autotimer.parseEPG(simulateOnly = True)
				self.session.openWithCallback(self.cbAutoTimerPreview, AutoTimerPreview, timers)
				
	def cbAutoTimerPreview(self, ret):
		# clear the AutoTimer instance
		self.deleteAutoTimerInstance()
		
	def cbOpenEdit(self, ret):
		if ret:
			self.updateAutoTimerEntry(ret.getId(), ret)
			self.updateState()
			
	def fillAutoTimerList(self):
		self.list = []
		self.getAutoTimerInstance()
		timerList = autotimer.getTimerList()
		
		for autoTimer in timerList:
			obj = self.getTimerListObjectFromAutoTimer(autoTimer)
			self.list.extend([(obj, False)]) # extend the TimerEditList list
		self.deleteAutoTimerInstance()
		self["timerlist"].l.setList(self.list)
		
	def getTimerListObjectFromAutoTimer(self, autoTimer):
		now = localtime(time())
		if autoTimer.timespan is not None and autoTimer.timespan[0] is not None:
			timeSpan = autoTimer.getTimespanBegin()
			if timeSpan is not None:
				parts = timeSpan.split(":")
				dt = datetime(now.tm_year, now.tm_mon, now.tm_mday, int(parts[0]), int(parts[1]))
				begin = int(mktime(dt.timetuple()))
			else:
				begin = 0
				
			timeSpan = autoTimer.getTimespanEnd()
			if timeSpan is not None:
				parts = timeSpan.split(":")
				dt = datetime(now.tm_year, now.tm_mon, now.tm_mday, int(parts[0]), int(parts[1]))
				end = int(mktime(dt.timetuple()))
			else:
				end = 0
		else:
			dt = datetime(now.tm_year, now.tm_mon, now.tm_mday, 0, 0)
			end = begin = int(mktime(dt.timetuple()))
			
		if autoTimer.getEnabled() == "no":
			enabled = True
		else:
			enabled = False
			
		return TimerListObject(begin, end, "", autoTimer.getName(), int(autoTimer.getJustplay()), enabled, autoTimer.getId(), autoTimer.getMatch(), autoTimer.searchType, autoTimer.getCounter(), autoTimer.getCounterLeft(), autoTimer.destination, autoTimer.getServices(), autoTimer.getBouquets(), autoTimer.getIncludedDays(), autoTimer.getExcludedDays())
		
	# TimerEditList method. Overwritten to support AutoTimer timers
	def toggleDisabledState(self):
		cur = self["timerlist"].getCurrent()
		if cur and isinstance(cur, RecordTimerEntry):
			t = cur
			if t.disabled:
				print "try to ENABLE timer"
				t.enable()
				timersanitycheck = TimerSanityCheck(self.session.nav.RecordTimer.timer_list, cur)
				if not timersanitycheck.check():
					t.disable()
					print "Sanity check failed"
					simulTimerList = timersanitycheck.getSimulTimerList()
					if simulTimerList is not None:
						self.session.openWithCallback(self.finishedEdit, TimerSanityConflict, simulTimerList)
				else:
					print "Sanity check passed"
					if timersanitycheck.doubleCheck():
						t.disable()
			else:
				if t.isRunning():
					if t.repeated:
						list = (
							(_("Stop current event but not coming events"), "stoponlycurrent"),
							(_("Stop current event and disable coming events"), "stopall"),
							(_("Don't stop current event but disable coming events"), "stoponlycoming")
						)
						self.session.openWithCallback(boundFunction(self.runningEventCallback, t), ChoiceBox, title=_("Repeating event currently recording... What do you want to do?"), list = list)
				else:
					t.disable()
			self.session.nav.RecordTimer.timeChanged(t)
		else: # AutoTimer timer
			global autotimer
			self.getAutoTimerInstance()
			
			# find the corresponding AutoTimer entry by id
			timerList = autotimer.getTimerList()
			for autotimerEntry in timerList:
				if autotimerEntry.getId() == cur.autoTimerId:
					autotimerEntry.enabled = not autotimerEntry.enabled
					cur.disabled = not cur.disabled
					autotimer.writeXml()
					break
					
			self.deleteAutoTimerInstance()
			
		# refresh the list
		idx = self["timerlist"].getCurrentIndex()
		self["timerlist"].l.invalidateEntry(idx)
		self.updateState()
			
	# TimerEditList method. Overwritten to support AutoTimer timers
	def removeTimer(self, result):
		if not result:
			return
		list = self["timerlist"]
		cur = list.getCurrent()
		if cur and isinstance(cur, RecordTimerEntry):
			timer = cur
			timer.afterEvent = AFTEREVENT.NONE
			self.session.nav.RecordTimer.removeEntry(timer)
			self.refill()
			self.updateState()
		else: # AutoTimer timer
			global autotimer
			self.getAutoTimerInstance()
			
			# find the corresponding AutoTimer entry by id
			timerList = autotimer.getTimerList()
			for autotimerEntry in timerList:
				if autotimerEntry.getId() == cur.autoTimerId:
					autotimer.remove(cur.autoTimerId)
					autotimer.writeXml()
					break
					
			self.deleteAutoTimerInstance()
			
			# remove the timerlist entry
			idx = self["timerlist"].getCurrentIndex()
			self.list.pop(idx)
			self["timerlist"].l.setList(self.list)
			self["timerlist"].invalidate()
			
	def onListSelectionChanged(self):
		isAutoTimer = False
		
		if self.currentMode == TIMERLIST:
			sel = self["timerlist"].getCurrent()
			if sel is None:
				# TODO hide event info
				return
			else:
				# build a tuple similar to the one returned by epg lists. the leading 0 is needed to make the list equal
				# to the epg list's (make list entries without event id selectable)
				if isinstance(sel, RecordTimerEntry):
					cur = (0, sel.eit, str(sel.service_ref), sel.begin, sel.end - sel.begin, sel.name, sel.description, None, sel.service_ref.getServiceName())
				else: # AutoTimer
					isAutoTimer = True
					cur = (0, 0, str(sel.service_ref), sel.begin, sel.end - sel.begin, sel.name, "", None, "")
					
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
		if self.currentMode == TIMERLIST:
			(ignoreMe, eventid, sRef, begin, duration, title, shortDesc, description, serviceName) = cur
			if isAutoTimer:
				dest = sel.destination or resolveFilename(SCOPE_HDD)
				
				description = ''.join([_("Match title:"), " ", sel.match, "\n"])
				if len(sel.services):
					serv = " "
					for service in sel.services:
						serv = ''.join([serv, ServiceReference(service).getServiceName(), ", "])
					serv = serv.rstrip(", ")
					description = ''.join([description, _("Services:"), " ", serv, "\n"])
				if len(sel.bouquets):
					bouq = " "
					for bouquet in sel.bouquets:
						bouq = ''.join([bouq, ServiceReference(bouquet).getServiceName(), ", "])
					bouq = bouq.rstrip(", ")
					description = ''.join([description, _("Bouquets:"), " ", bouq, "\n"])
				if len(sel.includedDays):
					days = ""
					for day in sel.includedDays:
						days = ''.join([days, [y[1] for x,y in enumerate(weekdays) if y[0] == day][0], ", "])
					days = days.rstrip(", ")
					description = ''.join([description, _("Included days:"), " ", days, "\n"])
				if len(sel.excludedDays):
					days = ""
					for day in sel.excludedDays:
						days = ''.join([days, [y[1] for x,y in enumerate(weekdays) if y[0] == day][0], ", "])
					days = days.rstrip(", ")
					description = ''.join([description, _("Excluded days:"), " ", days, "\n"])
				description = ''.join([description, _("Record a maximum of x times:"), " ", str(sel.counter), "\n",
					_("Amount of recordings left:"), " ", str(sel.counterLeft), "\n",
					_("Search type:"), " ", sel.searchType, "\n",
					_("Location:"), " ", dest.rstrip('/')
					])
		else:
			(ignoreMe, eventid, sRef, begin, duration, title, shortDesc, description) = cur
		
		# set timer button state
		self.setTimerButtonState(cur)
		
		self.setEventViewPicon(cur, isAutoTimer)
		
		if isAutoTimer:
			serviceName = "AutoTimer"
		elif sRef in EpgCenterList.allServicesNameDict:
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
						
				if (KEEP_OUTDATED_TIME == 0 and (begin + duration) > now) or (KEEP_OUTDATED_TIME != 0 and (begin + duration) > now):
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
					
				if config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_MULTI_PIXMAP or config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_MULTI_PIXMAP_LIST_OFF:
					self["eventProgressImage"].setPixmapNum(4)
				elif config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_PERCENT_TEXT or config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_PERCENT_TEXT_LIST_OFF:
					self["eventProgressText"].setText("100%")
				else:
					self["eventProgress"].setValue(100)
			else:
				try:
					textColor = parseColor("ListboxForeground").argb()
				except:
					textColor = parseColor("#ffffff")
					
				if config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_MULTI_PIXMAP or config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_MULTI_PIXMAP_LIST_OFF:
					if percent > 0:
						part = int(round(percent / 25)) + 1
						if part < 0:
							part = 0
						elif part > 4:
							part = 4
					else:
						part = 0
					self["eventProgressImage"].setPixmapNum(part)
				elif config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_PERCENT_TEXT or config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_PERCENT_TEXT_LIST_OFF:
					self["eventProgressText"].setText(str(percent) + "%")
				else:
					self["eventProgress"].setValue(percent)
					
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
			
		self.similarShown = False
		if self.infoTextShown:
			self.keyInfo()
			
		if mode == MODE_TV:
			self.infoBarInstance.servicelist.setModeTv()
		else:
			self.infoBarInstance.servicelist.setModeRadio()
		self.infoBarInstance.servicelist.zap()
		self.updateBouquets()
		
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
			if self.currentMode == SINGLE_EPG and KEEP_OUTDATED_TIME != 0:
				if not self.showOutdated:
					self["key_blue"].setText(_("Outdated on"))
				else:
					self["key_blue"].setText(_("Outdated off"))
			else:
				self["key_blue"].setText("")
				
			if IMDB_INSTALLED:
				self["key_yellow"].setText(_("IMDb"))
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
			
	def setRecordingBlinkState(self):
		if self.blinkTimer.getBlinkState() and not self.blinkTimer.getIsStopping():
			self["isRecording"].show()
		else:
			self["isRecording"].hide()
			
	def setEventPiconBlinkState(self):
		if self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == SINGLE_EPG or self.currentMode == MULTI_EPG_PRIMETIME or self.currentMode == EPGSEARCH_RESULT:
			cur = self["list"].getCurrent()
			self.setEventViewPicon(cur)
			
	def setEventViewPicon(self, cur, isAutoTimer = False):
		if isAutoTimer:
			if not self.autoTimerPixmapLarge:
				pixmapPath = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/AutoTimerLarge.png")
				self.autoTimerPixmapLarge = LoadPixmap(cached = False, path = pixmapPath)
			if self.autoTimerPixmapLarge:
				self["picon"].instance.setPixmap(self.autoTimerPixmapLarge)
		else:
			idx = self["list"].instance.getCurrentIndex()
			if config.plugins.merlinEpgCenter.blinkingPicon.value and self.blinkTimer.getIsInList(idx) and not self.blinkTimer.getBlinkState():
				self["picon"].instance.setPixmap(gPixmapPtr())
			elif cur is not None:
				sRef = cur[2]
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
	# BOUQUET RELATED FUNCTIONS
	
	def getBouquetName(self):
		name = self.bouquetList[self.currentBouquetIndex][0]
		showBouquetText = config.plugins.merlinEpgCenter.showBouquetText.value
		if self.infoBarInstance.servicelist.mode == MODE_TV:
			if name[len(name) -5:] == ' (TV)':
				if showBouquetText:
					return 'Bouquet: %s' % name[:len(name) -5]
				else:
					return '%s' % name[:len(name) -5]
			else:
				if showBouquetText:
					return 'Bouquet: %s' % name # Partnerbox bouquet
				else:
					return '%s' % name # Partnerbox bouquet
		else:
			if name[len(name) -8:] == ' (Radio)':
				if showBouquetText:
					return 'Bouquet: %s' % name[:len(name) -8]
				else:
					return '%s' % name[:len(name) -8]
			else:
				if showBouquetText:
					return 'Bouquet: %s' % name # Partnerbox bouquet
				else:
					return '%s' % name # Partnerbox bouquet
				
	def setBouquetName(self):
		self["bouquet"].setText(self.getBouquetName())
		
	def updateBouquets(self):
		from plugin import getBouquetInformation
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
		
	############################################################################################
	# AUTOTIMER

	def getAutoTimerInstance(self):
		global autotimer
		
		# create autotimer instance if needed
		if autotimer is None:
			self.removeAutoTimerInstance = True
			autotimer = AutoTimer()
			autotimer.readXml()
		else:
			self.removeAutoTimerInstance = False
			
	def deleteAutoTimerInstance(self):
		if self.removeAutoTimerInstance:
			global autotimer
			autotimer = None
			
	# Taken from AutoTimerEditor
	def addAutotimerFromString(self, match, addNewTimer = False, begin = None, end = None, sRef = None):
		global autotimer
		self.getAutoTimerInstance()
		
		newTimer = autotimer.defaultTimer.clone()
		newTimer.id = autotimer.getUniqueId()
		newTimer.name = match
		newTimer.match = ''
		newTimer.enabled = True
		
		if begin != None and end != None:
			begin -= 3600
			end += 3600
			
		self.session.openWithCallback(
			boundFunction(self.importerCallback, addNewTimer),
			AutoTimerImporter,
			newTimer,
			match,		# Proposed Match
			begin,		# Proposed Begin
			end,		# Proposed End
			None,		# Proposed Disabled
			sRef,		# Proposed ServiceReference
			None,		# Proposed afterEvent
			None,		# Proposed justplay
			None,		# Proposed dirname, can we get anything useful here?
			[]		# Proposed tags
		)
	
	def importerCallback(self, addNewTimer, ret):
		if ret:
			ret, session = ret

			self.session.openWithCallback(
				boundFunction(self.editorCallback, addNewTimer),
				AutoTimerEditor,
				ret
			)
		else:
			self.deleteAutoTimerInstance()

	def editorCallback(self, addNewTimer, ret):
		if ret:
			global autotimer
			self.getAutoTimerInstance()
			autotimer.add(ret)
			autotimer.writeXml()
			idx = self["timerlist"].getCurrentIndex()
			obj = self.getTimerListObjectFromAutoTimer(ret)
			if addNewTimer:
				self.list.append((obj, False))
			else:
				self.list[idx] = (obj, False)
			self.updateState()
			
		self.deleteAutoTimerInstance()
		
	def updateAutoTimerEntry(self, id, changedTimer):
		global autotimer
		self.getAutoTimerInstance()
		
		idx = 0
		for timer in autotimer.timers:
			if timer.getId() == id:
				autotimer.timers[idx] = changedTimer
				break
			idx += 1
		autotimer.writeXml()
		self.deleteAutoTimerInstance()
		
		# update the list entry
		idx = self["timerlist"].getCurrentIndex()
		obj = self.getTimerListObjectFromAutoTimer(changedTimer)
		self.list[idx] = (obj, False)
		self["timerlist"].l.invalidateEntry(idx)
		self.onListSelectionChanged()
		
	############################################################################################
	# MODE CONTROL
	
	def setMode(self, searchEpg = False, historySearch = False, manualSearch = False, switchTvRadio = False, doSearch = False):
		self.setTabs()
		self.setUpcomingWidgets()
		
		if self.blinkTimer.getIsRunning():
			self.blinkTimer.reset()
		
		# TODO only hide if the plugin wasn't just started
		if not historySearch and self.oldMode != None:
			self.epgTabObjectList[self.oldMode].hide()
			
		if doSearch:
			playingSref = NavigationInstance.instance.getCurrentlyPlayingServiceReference() # get the currently playing service
			if playingSref is not None:
				event = self.epgcache.lookupEventTime(playingSref, -1, 0) # get the matching event
				if event is not None:
					searchString = event.getEventName() # set the event name as search string
				else:
					searchString = ""
				self.currentMode = EPGSEARCH_RESULT
				self.epgTabObjectList[self.currentMode].show(searchString, self.currentMode)
		elif searchEpg:
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
				self.setSelectionToRunningService()
			elif self.oldMode == SINGLE_EPG or self.oldMode == EPGSEARCH_RESULT or self.oldMode == EPGSEARCH_HISTORY:
				if self.lastMultiEpgIndex > 0:
					self["list"].instance.moveSelectionTo(self.lastMultiEpgIndex)
				else:
					self["list"].instance.moveSelectionTo(0)
		elif self.currentMode == SINGLE_EPG:
			sRef = None
			if self.selectRunningService:
				self.setSelectionToRunningService()
			if self.showOutdated and not self.hideOutdated:
				self.hideOutdated = True
			elif self.showOutdated and self.hideOutdated:
				self.showOutdated = False
				self.hideOutdated = False
			elif not self.showOutdated and not self.hideOutdated and not self.oldMode == EPGSEARCH_RESULT and not self.selectRunningService:
				self.lastMultiEpgIndex = self["list"].instance.getCurrentIndex()
				
			self.selectRunningService = False
				
			if switchTvRadio:
				self.oldMode = None
				
			self.epgTabObjectList[self.currentMode].show(self.oldMode, self.bouquetList[0], self.currentBouquet, self.currentBouquetIndex, self.currentMode, self.showOutdated, sRef, self.timerListMode)
		elif self.currentMode == TIMERLIST:
			if self.timerListMode == LIST_MODE_TIMER:
				self.fillTimerList()
			else:
				self.fillAutoTimerList()
			self.onListSelectionChanged()
			self["timerlist"].moveToIndex(0)
			self.epgTabObjectList[self.currentMode].show()
		if self.listStyle == STYLE_SINGLE_LINE:
			if (self.currentMode == SINGLE_EPG or self.currentMode == EPGSEARCH_RESULT) and (self.oldMode != SINGLE_EPG and self.oldMode != EPGSEARCH_RESULT):
				self.setUpcomingWidgets()
			elif (self.currentMode != SINGLE_EPG and self.currentMode != EPGSEARCH_RESULT) and (self.oldMode == SINGLE_EPG or self.oldMode == EPGSEARCH_RESULT):
				self.setUpcomingWidgets()
				
		self.setButtonText()
		self.setActions()
		
	def setSelectionToRunningService(self):
		playingSref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
		if not playingSref:
			return
			
		from plugin import getBouquetInformation
		(self.servicelist, self.currentBouquet, self.bouquetList, self.currentBouquetIndex) = getBouquetInformation()
		EpgCenterList.bouquetList = self.bouquetList
		EpgCenterList.currentBouquetIndex = self.currentBouquetIndex
		sRef = playingSref.toCompareString()
		if sRef in self["list"].bouquetServices[self.currentBouquetIndex]:
			self.lastMultiEpgIndex = self["list"].bouquetServices[self.currentBouquetIndex].index(sRef)
		
		if self.currentMode == SINGLE_EPG:
			if sRef in self["list"].bouquetServices[self.currentBouquetIndex]:
				self.epgTabObjectList[self.currentMode].show(self.oldMode, self.bouquetList[0], self.currentBouquet, self.currentBouquetIndex, self.currentMode, self.showOutdated, sRef, self.timerListMode)
		else:
			if sRef in self["list"].bouquetServices[self.currentBouquetIndex]:
				self.epgTabObjectList[self.currentMode].show(self.currentBouquet, self.currentBouquetIndex, self.currentMode)
				
			i = 0
			while i < len(self["list"].list):
				if self["list"].list[i][2] == sRef:
					self.lastMultiEpgIndex = i
					self["list"].instance.moveSelectionTo(self.lastMultiEpgIndex)
					break
				i += 1
				
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
				
	def keyRed(self, forceHideSimilar = False):
		if self.currentMode == EPGSEARCH_HISTORY:
			self.removeFromEpgSearchHistory()
		else:
			if not forceHideSimilar:
				self.similarShown = not self.similarShown
			else:
				self.similarShown = False
				
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
		if self.currentMode == EPGSEARCH_HISTORY:
			self.setMode(historySearch = True)
		elif self.currentMode == EPGSEARCH_MANUAL:
			self.keyOk()
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
				if AUTOTIMER:
					self.timerChoice()
				else:
					self.addTimerEntry()
					
	def keyYellow(self):
		if self.currentMode == EPGSEARCH_HISTORY:
			self.setMode(manualSearch = True)
		elif self.configTabsShown:
			self.keyEditMode()
		elif IMDB_INSTALLED and (self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == SINGLE_EPG or self.currentMode == MULTI_EPG_PRIMETIME or self.currentMode == EPGSEARCH_RESULT):
			cur = self["list"].getCurrent()
			self.session.open(IMDB, cur[5])
			
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
		mainTabValue = int(config.plugins.merlinEpgCenter.mainTab.getValue())
		if self.configTabsShown:
			self.keyMenu()
			return
		elif mainTabValue != -1 and self.currentMode != mainTabValue:
			self.keyNumber(mainTabValue +1)
			return
		elif self.infoTextShown:
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
			self.suspend()
			self.close(None)
			
	# really shutdown everything when enigma2 is shut down
	def shutdown(self):
		self.removeNotifier()
		self.blinkTimer.timer.callback.remove(self.setEventPiconBlinkState)
		self.blinkTimer.timer.callback.remove(self.setRecordingBlinkState)
		self.releaseEpgBaseTab()
		self.blinkTimer.suspend()
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
			if self.oldMode == number -1 and not self.oldMode == TIMERLIST: # same mode, there's nothing to do for other modes than TIMERLIST
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
				elif number == 5 and AUTOTIMER and self.oldMode == TIMERLIST: # toggle timer / autotimer
					if self.timerListMode == LIST_MODE_TIMER:
						self.timerListMode = LIST_MODE_AUTOTIMER
						self["tab_text_%d" % TIMERLIST].setText("AutoTimer")
						self.getAutoTimerInstance()
						self.fillAutoTimerList()
						self.deleteAutoTimerInstance()
					elif self.timerListMode == LIST_MODE_AUTOTIMER:
						self.timerListMode = LIST_MODE_TIMER
						self["tab_text_%d" % TIMERLIST].setText(_("Timer"))
						self.fillTimerList()
						
					self["timerlist"].moveToIndex(0)
					self["timerlist"].invalidate()
					self.updateState()
					self.onListSelectionChanged()
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
				if cur is None:
					title = ""
					shortDesc = ""
					description = ""
				else:
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
		
	def keyVideo(self):
		if YTTRAILER_INSTALLED:
			if self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == SINGLE_EPG or self.currentMode == MULTI_EPG_PRIMETIME or self.currentMode == EPGSEARCH_RESULT:
				cur = self["list"].getCurrent()
				if cur:
					self.session.open(YTTrailerList, cur[5])
			elif self.currentMode == TIMERLIST:
				cur = self["timerlist"].getCurrent()
				if cur:
					self.session.open(YTTrailerList, cur.name)
					
	def keyText(self):
		if self.currentMode == SINGLE_EPG:
			if self.epgTabObjectList[self.currentMode].sortMode == EpgSingleTab.SORT_MODE_TIME:
				self.epgTabObjectList[self.currentMode].sortMode = EpgSingleTab.SORT_MODE_NAME
			else:
				self.epgTabObjectList[self.currentMode].sortMode = EpgSingleTab.SORT_MODE_TIME
			self.epgTabObjectList[self.currentMode].sort()
			
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
			self.setTabText(TAB_TEXT_EPGLIST)
			if self.currentMode <= NUM_EPG_TABS:
				self["tab_text_%d" % self.currentMode].instance.setForegroundColor(parseColor(config.plugins.merlinEpgCenter.tabTextColorSelected.value)) # active
				self["tabbar"].setPixmapNum(self.currentMode)
			else:
				self["tab_text_%d" % NUM_EPG_TABS].instance.setForegroundColor(parseColor(config.plugins.merlinEpgCenter.tabTextColorSelected.value)) # active
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
			self["tab_text_%d" % self.currentMode].instance.setForegroundColor(parseColor(config.plugins.merlinEpgCenter.tabTextColorSelected.value)) # active
			self["tabbar"].setPixmapNum(self.currentMode)
			self.configTabsShown = True
			self.setTabText(TAB_TEXT_CONFIGLIST)
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
			
	def setDescriptionSize(self):
		# Invisible option to allow moving the videoPicture above the event description in skins
		if not config.plugins.merlinEpgCenter.setDescriptionSize.value:
			return
			
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
		self["search"].instance.resize(eSize(newSize.width() - border -15, newSize.height()))
		self["history"].instance.resize(eSize(newSize.width() - border, newSize.height()))
		self["settings"].instance.resize(eSize(newSize.width() - border, newSize.height()))
		self["upcomingSeparator"].instance.resize(eSize(newSize.width() + border, newSize.height())) # touch the event info separator
		self["timerlist"].setMaxWidth(newSize)
		
		self.setUpcomingWidgets()
		self.setVideoPicture()
		self.setListPixmaps()
		
	def setListPixmaps(self):
		backgroundPixmap = None
		if config.plugins.merlinEpgCenter.showEventInfo.value and config.plugins.merlinEpgCenter.backgroundPixmapShort.value != "":
			backgroundPixmap = LoadPixmap(cached = True, path = config.plugins.merlinEpgCenter.backgroundPixmapShort.value)
		elif not config.plugins.merlinEpgCenter.showEventInfo.value and config.plugins.merlinEpgCenter.backgroundPixmapLong.value != "":
			backgroundPixmap = LoadPixmap(cached = True, path = config.plugins.merlinEpgCenter.backgroundPixmapLong.value)
		if backgroundPixmap is not None:
			self["timerlist"].instance.setBackgroundPicture(backgroundPixmap)
			self["list"].instance.setBackgroundPicture(backgroundPixmap)
			self["upcoming"].instance.setBackgroundPicture(backgroundPixmap)
			self["history"].instance.setBackgroundPicture(backgroundPixmap)
			self["settings"].instance.setBackgroundPicture(backgroundPixmap)
			
		selectionPixmap = None
		if config.plugins.merlinEpgCenter.showEventInfo.value and config.plugins.merlinEpgCenter.selectionPixmapShort.value != "":
			selectionPixmap = LoadPixmap(cached = True, path = config.plugins.merlinEpgCenter.selectionPixmapShort.value)
		elif not config.plugins.merlinEpgCenter.showEventInfo.value and config.plugins.merlinEpgCenter.selectionPixmapLong.value != "":
			selectionPixmap = LoadPixmap(cached = True, path = config.plugins.merlinEpgCenter.selectionPixmapLong.value)
		if selectionPixmap is not None:
			self["timerlist"].instance.setSelectionPicture(selectionPixmap)
			self["list"].instance.setSelectionPicture(selectionPixmap)
			self["history"].instance.setSelectionPicture(selectionPixmap)
			self["settings"].instance.setSelectionPicture(selectionPixmap)
			
