from __future__ import absolute_import
#
#  MerlinEPGCenter E2 Plugin
#
#  $Id: ConfigTabs.py,v 1.0 2011-06-13 17:15:00 shaderman Exp $
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

# ENIGMA IMPORTS
from Components.config import config, ConfigSubsection, getConfigListEntry, ConfigSet, ConfigClock, ConfigYesNo, ConfigInteger, ConfigSelection, ConfigText, NoSave, ConfigSelectionNumber
from enigma import eEnv
from Tools.Directories import SCOPE_CURRENT_PLUGIN, resolveFilename

STYLE_SIMPLE_BAR = "0"
STYLE_PIXMAP_BAR = "1"
STYLE_MULTI_PIXMAP = "2"
STYLE_PERCENT_TEXT = "3"
STYLE_SIMPLE_BAR_LIST_OFF = "4"
STYLE_PIXMAP_BAR_LIST_OFF = "5"
STYLE_MULTI_PIXMAP_LIST_OFF = "6"
STYLE_PERCENT_TEXT_LIST_OFF = "7"

SKINDIR = "Extensions/MerlinEPGCenter/skins/"

SKINLIST = [ # order is important (HD_BORDER, XD_BORDER, SD, HD, XD)!
		(resolveFilename(SCOPE_CURRENT_PLUGIN, ''.join([SKINDIR, "HD_border.xml"])), "HD_border.xml"),
		(resolveFilename(SCOPE_CURRENT_PLUGIN, ''.join([SKINDIR, "XD_border.xml"])), "XD_border.xml"),
		(resolveFilename(SCOPE_CURRENT_PLUGIN, ''.join([SKINDIR, "SD_default.xml"])), "SD_default.xml"),
		(resolveFilename(SCOPE_CURRENT_PLUGIN, ''.join([SKINDIR, "HD_default.xml"])), "HD_default.xml"),
		(resolveFilename(SCOPE_CURRENT_PLUGIN, ''.join([SKINDIR, "XD_default.xml"])), "XD_default.xml")
		]
		
# check Merlin2 feature "keep outdated events in epgcache"
try:
	KEEP_OUTDATED_TIME = config.merlin2.keep_outdated_epg.value * 60
except KeyError:
	KEEP_OUTDATED_TIME = 0
	

# OWN IMPORTS
from .EpgCenterList import MULTI_EPG_NOW, MULTI_EPG_NEXT, SINGLE_EPG, MULTI_EPG_PRIMETIME, TIMERLIST, EPGSEARCH_HISTORY
from .MerlinEPGCenter import STYLE_SINGLE_LINE, STYLE_SHORT_DESCRIPTION, TAB_TEXT_EPGLIST
from .SkinFinder import SkinFinder

TAB_CHOICES = [("-1", _("disabled")),
		(str(MULTI_EPG_NOW), TAB_TEXT_EPGLIST[MULTI_EPG_NOW]),
		(str(MULTI_EPG_NEXT), TAB_TEXT_EPGLIST[MULTI_EPG_NEXT]),
		(str(SINGLE_EPG), TAB_TEXT_EPGLIST[SINGLE_EPG]),
		(str(MULTI_EPG_PRIMETIME), TAB_TEXT_EPGLIST[MULTI_EPG_PRIMETIME]),
		(str(TIMERLIST), TAB_TEXT_EPGLIST[TIMERLIST]),
		(str(EPGSEARCH_HISTORY), TAB_TEXT_EPGLIST[EPGSEARCH_HISTORY]), ]


config.plugins.merlinEpgCenter = ConfigSubsection()
config.plugins.merlinEpgCenter.primeTime = ConfigClock(default=69300)
config.plugins.merlinEpgCenter.showListNumbers = ConfigYesNo(True)
config.plugins.merlinEpgCenter.showPicons = ConfigYesNo(False)
config.plugins.merlinEpgCenter.showServiceName = ConfigYesNo(True)
config.plugins.merlinEpgCenter.serviceNameWidth = ConfigSelectionNumber(min=-10, max=20, stepwidth=1, default=0)
config.plugins.merlinEpgCenter.lastUsedTab = ConfigInteger(0)
config.plugins.merlinEpgCenter.showEventInfo = ConfigYesNo(True)
config.plugins.merlinEpgCenter.showVideoPicture = ConfigYesNo(True)
config.plugins.merlinEpgCenter.rememberLastTab = ConfigYesNo(True)
config.plugins.merlinEpgCenter.selectRunningService = ConfigYesNo(True)
config.plugins.merlinEpgCenter.replaceInfobarEpg = ConfigYesNo(False)
config.plugins.merlinEpgCenter.replaceInfobarChannelUp = ConfigSelection(default="-1", choices=TAB_CHOICES)
config.plugins.merlinEpgCenter.replaceInfobarChannelDown = ConfigSelection(default="-1", choices=TAB_CHOICES)
config.plugins.merlinEpgCenter.replaceShowEventView = ConfigSelection(default="-1", choices=TAB_CHOICES)
config.plugins.merlinEpgCenter.epgPaths = ConfigSelection(default=eEnv.resolve('${datadir}/enigma2/picon_50x30/'), choices=[
				(eEnv.resolve('${datadir}/enigma2/picon_50x30/'), eEnv.resolve('${datadir}/enigma2/picon_50x30')),
				('/media/cf/picon_50x30/', '/media/cf/picon_50x30'),
				('/media/usb/picon_50x30/', '/media/usb/picon_50x30'),
				])
config.plugins.merlinEpgCenter.showColoredEpgTimes = ConfigYesNo(True)
config.plugins.merlinEpgCenter.searchString = NoSave(ConfigText(default=""))
config.plugins.merlinEpgCenter.searchHistory = ConfigSet(choices=[])
config.plugins.merlinEpgCenter.showInputHelp = ConfigYesNo(True)
config.plugins.merlinEpgCenter.listItemHeight = ConfigSelectionNumber(min=0, max=20, stepwidth=2, default=0, wraparound=True)
config.plugins.merlinEpgCenter.listStyle = ConfigSelection(default=STYLE_SINGLE_LINE, choices=[
				(STYLE_SINGLE_LINE, _("single line style")),
				(STYLE_SHORT_DESCRIPTION, _("with short description")),
				])
config.plugins.merlinEpgCenter.skin = ConfigText(default="")
config.plugins.merlinEpgCenter.skinSelection = NoSave(ConfigSelection(choices=[]))
config.plugins.merlinEpgCenter.limitSearchToBouquetServices = ConfigYesNo(False)
config.plugins.merlinEpgCenter.exitOnTvRadioSwitch = ConfigYesNo(False)
config.plugins.merlinEpgCenter.numNextEvents = ConfigSelectionNumber(min=0, max=3, stepwidth=1, default=1, wraparound=True)
config.plugins.merlinEpgCenter.showDuration = ConfigYesNo(True)
config.plugins.merlinEpgCenter.showBeginRemainTime = ConfigYesNo(True)
config.plugins.merlinEpgCenter.listProgressStyle = ConfigSelection(default=STYLE_PIXMAP_BAR, choices=[
				(STYLE_SIMPLE_BAR, _("list and event info: simple")),
				(STYLE_PIXMAP_BAR, _("list and event info: gradient")),
				(STYLE_MULTI_PIXMAP, _("list and event info: four parts")),
				(STYLE_PERCENT_TEXT, _("list and event info: percent (text)")),
				(STYLE_SIMPLE_BAR_LIST_OFF, _("list: off, event info: simple")),
				(STYLE_PIXMAP_BAR_LIST_OFF, _("list: off, event info: gradient")),
				(STYLE_MULTI_PIXMAP_LIST_OFF, _("list: off, event info: four parts")),
				(STYLE_PERCENT_TEXT_LIST_OFF, _("list: off, event info: percent (text)")),
				])
config.plugins.merlinEpgCenter.blinkingPicon = ConfigYesNo(False)
config.plugins.merlinEpgCenter.showShortDescInEventInfo = ConfigYesNo(True)
config.plugins.merlinEpgCenter.adjustFontSize = ConfigSelectionNumber(min=-5, max=5, stepwidth=1, default=0)
config.plugins.merlinEpgCenter.mainTab = ConfigSelection(default="-1", choices=TAB_CHOICES)
config.plugins.merlinEpgCenter.embeddedVolume = ConfigYesNo(False)
config.plugins.merlinEpgCenter.columnSpace = ConfigSelectionNumber(min=0, max=40, stepwidth=1, default=5, wraparound=True)

# INVISIBLE OPTIONS
# These config values should be set in the skin in a <applet type="onLayoutFinish"></applet> tag

# Set it to false to disable the dependency between the videoPicture/MiniTv and the description widget.
# This allows moving the videoPicture/MiniTv widget above the description text.
config.plugins.merlinEpgCenter.setDescriptionSize = NoSave(ConfigYesNo(True))

# Two background Pixmaps can be set. These will be swapped for the lists "timerlist", "list", "history" and "settings",
# depending on the value of config.plugins.merlinEpgCenter.showEventInfo
config.plugins.merlinEpgCenter.backgroundPixmapShort = NoSave(ConfigText(default=""))
config.plugins.merlinEpgCenter.backgroundPixmapLong = NoSave(ConfigText(default=""))

config.plugins.merlinEpgCenter.selectionPixmapShort = NoSave(ConfigText(default=""))
config.plugins.merlinEpgCenter.selectionPixmapLong = NoSave(ConfigText(default=""))

# Use this to override the default tab text color
config.plugins.merlinEpgCenter.tabTextColorSelected = NoSave(ConfigText(default="#ef7f1a"))

# Default is to show the text "Bouquet:" in front of a bouquet name. Use this option to hide it
config.plugins.merlinEpgCenter.showBouquetText = NoSave(ConfigYesNo(True))

# Allows changing the color of the event title in lists
config.plugins.merlinEpgCenter.titleColor = NoSave(ConfigInteger(default=0x00ffffff))
config.plugins.merlinEpgCenter.titleColorSelected = NoSave(ConfigInteger(default=0x00ffffff))

# Show the primetime value on tab 4 instead of the text "Prime Time"
config.plugins.merlinEpgCenter.showPrimeTimeValue = NoSave(ConfigYesNo(False))


############################################################################################
# CONFIG CLASSES

# base class for all config tab classes
class ConfigBaseTab():
	settingsWidget = None
	
	def __init__(self):
		pass
		
	# activate this tab
	def show(self):
		ConfigBaseTab.settingsWidget.setList(self.configList)
		
	def expandableSettingChanged(self, configElement=None):
		self.buildConfigList()
		self.show()
		
	def removeNotifier(self):
		pass
		
# config general
class ConfigGeneral(ConfigBaseTab):
	def __init__(self):
		ConfigBaseTab.__init__(self)
		self.configList = []
		self.buildConfigList()
		
	def show(self):
		ConfigBaseTab.settingsWidget.setList(self.configList)
		
	def buildConfigList(self):
		cfgList = []
		cfgList.append(getConfigListEntry(_("Prime time:"), config.plugins.merlinEpgCenter.primeTime))
		cfgList.append(getConfigListEntry(_("Remember last tab:"), config.plugins.merlinEpgCenter.rememberLastTab))
		cfgList.append(getConfigListEntry(_("Select running service on start:"), config.plugins.merlinEpgCenter.selectRunningService))
		cfgList.append(getConfigListEntry(_("Show text input help for epg search:"), config.plugins.merlinEpgCenter.showInputHelp))
		cfgList.append(getConfigListEntry(_("Use skin:"), config.plugins.merlinEpgCenter.skinSelection))
		cfgList.append(getConfigListEntry(_("Limit search results to bouquet services:"), config.plugins.merlinEpgCenter.limitSearchToBouquetServices))
		cfgList.append(getConfigListEntry(_("Exit on TV <-> Radio switch:"), config.plugins.merlinEpgCenter.exitOnTvRadioSwitch))
		cfgList.append(getConfigListEntry(_("Adjust font size:"), config.plugins.merlinEpgCenter.adjustFontSize))
		cfgList.append(getConfigListEntry(_("Embed volume slider:"), config.plugins.merlinEpgCenter.embeddedVolume))
		self.configList = cfgList
		
# config list settings
class ConfigListSettings(ConfigBaseTab):
	def __init__(self):
		ConfigBaseTab.__init__(self)
		self.configList = []
		self.buildConfigList()
		self.setNotifier()
		
	def buildConfigList(self):
		cfgList = []
		cfgList.append(getConfigListEntry(_("Show list numbers:"), config.plugins.merlinEpgCenter.showListNumbers))
		cfgList.append(getConfigListEntry(_("Show picons:"), config.plugins.merlinEpgCenter.showPicons))
		if config.plugins.merlinEpgCenter.showPicons.value:
			cfgList.append(getConfigListEntry(_("Use picons (50x30) from:"), config.plugins.merlinEpgCenter.epgPaths))
		cfgList.append(getConfigListEntry(_("Show service name:"), config.plugins.merlinEpgCenter.showServiceName))
		if config.plugins.merlinEpgCenter.showServiceName.value:
			cfgList.append(getConfigListEntry(_("Adjust service name column width:"), config.plugins.merlinEpgCenter.serviceNameWidth))
		cfgList.append(getConfigListEntry(_("Show duration:"), config.plugins.merlinEpgCenter.showDuration))
		cfgList.append(getConfigListEntry(_("Show begin/remain times:"), config.plugins.merlinEpgCenter.showBeginRemainTime))
		if config.plugins.merlinEpgCenter.showBeginRemainTime.value:
			cfgList.append(getConfigListEntry(_("Show multi colored begin/remain times:"), config.plugins.merlinEpgCenter.showColoredEpgTimes))
		cfgList.append(getConfigListEntry(_("Increase list item height:"), config.plugins.merlinEpgCenter.listItemHeight))
		cfgList.append(getConfigListEntry(_("Space between columns:"), config.plugins.merlinEpgCenter.columnSpace))
		cfgList.append(getConfigListEntry(_("List style:"), config.plugins.merlinEpgCenter.listStyle))
		cfgList.append(getConfigListEntry(_("Progress bar style:"), config.plugins.merlinEpgCenter.listProgressStyle))
		cfgList.append(getConfigListEntry(_("Number of upcoming events to show:"), config.plugins.merlinEpgCenter.numNextEvents))
		self.configList = cfgList
		
	def setNotifier(self):
		config.plugins.merlinEpgCenter.showPicons.addNotifier(self.expandableSettingChanged, initial_call=False)
		config.plugins.merlinEpgCenter.epgPaths.addNotifier(self.piconPathChanged, initial_call=False)
		config.plugins.merlinEpgCenter.showBeginRemainTime.addNotifier(self.expandableSettingChanged, initial_call=False)
		config.plugins.merlinEpgCenter.showServiceName.addNotifier(self.expandableSettingChanged, initial_call=False)
		
	def removeNotifier(self):
		config.plugins.merlinEpgCenter.showPicons.removeNotifier(self.expandableSettingChanged)
		config.plugins.merlinEpgCenter.epgPaths.removeNotifier(self.piconPathChanged)
		config.plugins.merlinEpgCenter.showBeginRemainTime.removeNotifier(self.expandableSettingChanged)
		config.plugins.merlinEpgCenter.showServiceName.removeNotifier(self.expandableSettingChanged)
		
	def piconPathChanged(self, configElement=None):
		config.plugins.merlinEpgCenter.epgPaths.save()
		
# config event information
class ConfigEventInfo(ConfigBaseTab):
	def __init__(self):
		ConfigBaseTab.__init__(self)
		self.configList = []
		self.buildConfigList()
		self.setNotifier()
		
	def buildConfigList(self):
		cfgList = []
		cfgList.append(getConfigListEntry(_("Show event information:"), config.plugins.merlinEpgCenter.showEventInfo))
		if config.plugins.merlinEpgCenter.showEventInfo.value:
			cfgList.append(getConfigListEntry(_("Show video picture:"), config.plugins.merlinEpgCenter.showVideoPicture))
		cfgList.append(getConfigListEntry(_("Show blinking picon for running timers:"), config.plugins.merlinEpgCenter.blinkingPicon))
		cfgList.append(getConfigListEntry(_("Show short description:"), config.plugins.merlinEpgCenter.showShortDescInEventInfo))
		self.configList = cfgList
			
	def setNotifier(self):
		config.plugins.merlinEpgCenter.showEventInfo.addNotifier(self.expandableSettingChanged, initial_call=False)
		
	def removeNotifier(self):
		config.plugins.merlinEpgCenter.showEventInfo.removeNotifier(self.expandableSettingChanged)
		
# config key settings
class ConfigKeys(ConfigBaseTab):
	def __init__(self):
		ConfigBaseTab.__init__(self)
		self.configList = []
		self.buildConfigList()
		
	def buildConfigList(self):
		cfgList = []
		cfgList.append(getConfigListEntry(_("Return to main tab with exit:"), config.plugins.merlinEpgCenter.mainTab))
		cfgList.append(getConfigListEntry(_("Replace InfoBar single and multi EPG:"), config.plugins.merlinEpgCenter.replaceInfobarEpg))
		cfgList.append(getConfigListEntry(_("Replace ChannelSelection key up to start with tab:"), config.plugins.merlinEpgCenter.replaceInfobarChannelUp))
		cfgList.append(getConfigListEntry(_("Replace ChannelSelection key down to start with tab:"), config.plugins.merlinEpgCenter.replaceInfobarChannelDown))
		cfgList.append(getConfigListEntry(_("Replace EventView key to start with tab:"), config.plugins.merlinEpgCenter.replaceShowEventView))
		self.configList = cfgList
		
