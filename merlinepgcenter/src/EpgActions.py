from __future__ import absolute_import
#
#  MerlinEPGCenter E2 Plugin
#
#  $Id: EpgActions.py,v 1.0 2011-07-17 08:00:00 shaderman Exp $
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

# ENIGMA IMPORTS
from Components.ActionMap import ActionMap, NumberActionMap
from Tools.BoundFunction import boundFunction

# OWN IMPORTS
from .ConfigTabs import KEEP_OUTDATED_TIME
from .EpgCenterList import MULTI_EPG_NOW, MULTI_EPG_NEXT, SINGLE_EPG, MULTI_EPG_PRIMETIME, TIMERLIST, EPGSEARCH_HISTORY, EPGSEARCH_RESULT, EPGSEARCH_MANUAL

class MerlinEPGActions():		
	def __init__(self):
		# TIMEREDITLIST
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ShortcutActions", "TimerEditActions", "YttrailerActions"],
		{
			"ok":			self.openEdit,
			"cancel":		self.keyExit, # overwritten to use our own exit function
			"green":		self.addCurrentTimer,
			"log":			self.showLog,
			"left":			self.left,
			"right":		self.right,
			"up":			self.up,
			"down":			self.down,
			"video":		self.keyVideo,
		}, -1)
		
		# TAB NAVIGATION
		self["tabNavigationActions"] = ActionMap(["TabNavigationActions"],
		{
			"nextTab":		boundFunction(self.keyDirection, direction = 1),
			"prevTab": 		boundFunction(self.keyDirection, direction = -1),
			"1":			boundFunction(self.keyNumber, number = 1),
			"2":			boundFunction(self.keyNumber, number = 2),
			"3":			boundFunction(self.keyNumber, number = 3),
			"4":			boundFunction(self.keyNumber, number = 4),
			"5":			boundFunction(self.keyNumber, number = 5),
			"6":			boundFunction(self.keyNumber, number = 6),
		}, -1)
		
		# EPG TABS
		self["epgTabBaseActions"] = ActionMap(["EpgTabBaseActions"],
		{
			"exit":			self.keyExit,
			"moveUp":		self.keyUp,
			"moveDown":		self.keyDown,
			"pageUp":		self.keyLeft,
			"pageDown":		self.keyRight,
			"nextBouquet":		self.keyBouquetUp,
			"prevBouquet": 		self.keyBouquetDown,
			"showRadio":		self.keyRadio,
			"showTv":		self.keyTv,
			"showEventInfo":	self.keyInfo,
			"ok":			self.keyOk,
			"video":		self.keyVideo,
			"text":			self.keyText,
		}, -1)
		
		# EPG HISTORY ACTIONS
		self["epgHistoryActions"] = ActionMap(["EpgHistoryActions"],
		{
			"exit":			self.keyExit,
			"ok":			self.keyOk,
			"moveUp":		self.keyUp,
			"moveDown":		self.keyDown,
			"pageUp":		self.keyLeft,
			"pageDown":		self.keyRight,
		}, -1)
		
		# EPG MANUAL SEARCH ACTIONS
		self["epgManualSearchActions"] = ActionMap(["EpgManualSearchActions"],
		{
			"exit":			self.keyExit,
			"ok":			self.keyOk,
			"left":			self.keyLeft,
			"right":		self.keyRight,
			"next":			boundFunction(self.keyDirection, direction = 1),
			"previous":		boundFunction(self.keyDirection, direction = -1),
			"1":			boundFunction(self.keyNumber, number = 1),
			"2":			boundFunction(self.keyNumber, number = 2),
			"3":			boundFunction(self.keyNumber, number = 3),
			"4":			boundFunction(self.keyNumber, number = 4),
			"5":			boundFunction(self.keyNumber, number = 5),
			"6":			boundFunction(self.keyNumber, number = 6),
			"7":			boundFunction(self.keyNumber, number = 7),
			"8":			boundFunction(self.keyNumber, number = 8),
			"9":			boundFunction(self.keyNumber, number = 9),
			"0":			boundFunction(self.keyNumber, number = 0),
		}, -1)
		
		# EPG RED
		self["epgRedActions"] = ActionMap(["EpgRedActions"],
		{
			"red":			self.keyRed,
		}, -1)
		
		# EPG GREEN
		self["epgGreenActions"] = ActionMap(["EpgGreenActions"],
		{
			"green":		self.keyGreen,
		}, -1)
		
		# EPG BLUE
		self["epgBlueActions"] = ActionMap(["EpgBlueActions"],
		{
			"blue":			self.keyBlue,
		}, -1)
		
		# EPG YELLOW
		self["epgYellowActions"] = ActionMap(["EpgYellowActions"],
		{
			"yellow":		self.keyYellow,
		}, -1)
		
		# SETTINGS ACTIONS
		self["settingsActions"] = ActionMap(["SettingsActions"],
		{
			"nextTab":		boundFunction(self.keyDirection, direction = 1),
			"prevTab": 		boundFunction(self.keyDirection, direction = -1),
			"1":			boundFunction(self.keyNumber, number = 1),
			"2":			boundFunction(self.keyNumber, number = 2),
			"3":			boundFunction(self.keyNumber, number = 3),
			"4":			boundFunction(self.keyNumber, number = 4),
			"5":			boundFunction(self.keyNumber, number = 5),
			"6":			boundFunction(self.keyNumber, number = 6),
			"7":			boundFunction(self.keyNumber, number = 7),
			"8":			boundFunction(self.keyNumber, number = 8),
			"9":			boundFunction(self.keyNumber, number = 9),
			"0":			boundFunction(self.keyNumber, number = 0),
			"exit":			self.keyExit,
			"moveUp":		self.keyUp,
			"moveDown":		self.keyDown,
			"left":			self.keyLeft,
			"right":		self.keyRight,
		}, -1)
		
		# TOGGLE CONFIG
		self["toggleConfigActions"] = ActionMap(["ToggleConfigActions"],
		{
			"toggleConfig":		self.keyMenu,
		}, -1)
		
		# disable several action maps on start
		self["actions"].setEnabled(False)
		self["epgHistoryActions"].setEnabled(False)
		self["epgManualSearchActions"].setEnabled(False)
		self["epgRedActions"].setEnabled(False)
		self["epgYellowActions"].setEnabled(False)
		self["epgBlueActions"].setEnabled(False)
		self["settingsActions"].setEnabled(False)
		self["toggleConfigActions"].setEnabled(True)
		
	def setActions(self):
		from .MerlinEPGCenter import IMDB_INSTALLED
		
		# unset action map
		if self.oldMode == MULTI_EPG_NOW or self.oldMode == MULTI_EPG_NEXT or self.oldMode == MULTI_EPG_PRIMETIME or self.oldMode == EPGSEARCH_RESULT:
			self["epgTabBaseActions"].setEnabled(False)
			self["epgRedActions"].setEnabled(False)
			self["epgGreenActions"].setEnabled(False)
			if IMDB_INSTALLED:
				self["epgYellowActions"].setEnabled(False)
		elif self.oldMode == SINGLE_EPG:
			self["epgTabBaseActions"].setEnabled(False)
			self["epgRedActions"].setEnabled(False)
			self["epgGreenActions"].setEnabled(False)
			if KEEP_OUTDATED_TIME != 0:
				self["epgBlueActions"].setEnabled(False)
			if IMDB_INSTALLED:
				self["epgYellowActions"].setEnabled(False)
		elif self.oldMode == TIMERLIST:
			self["actions"].setEnabled(False)
		elif self.oldMode == EPGSEARCH_HISTORY:
			self["epgTabBaseActions"].setEnabled(False)
			self["epgHistoryActions"].setEnabled(False)
			self["epgRedActions"].setEnabled(False)
			self["epgGreenActions"].setEnabled(False)
			self["epgYellowActions"].setEnabled(False)
		elif self.oldMode == EPGSEARCH_MANUAL:
			self["epgManualSearchActions"].setEnabled(False)
			self["tabNavigationActions"].setEnabled(True)
			
		# set action map
		if self.configTabsShown:
			self["tabNavigationActions"].setEnabled(False)
			self["actions"].setEnabled(False)
			self["epgTabBaseActions"].setEnabled(False)
			self["epgHistoryActions"].setEnabled(False)
			self["epgManualSearchActions"].setEnabled(False)
			self["epgRedActions"].setEnabled(False)
			self["epgGreenActions"].setEnabled(False)
			self["epgBlueActions"].setEnabled(False)
			self["epgYellowActions"].setEnabled(True)
			self["settingsActions"].setEnabled(True)
		elif self.currentMode == MULTI_EPG_NOW or self.currentMode == MULTI_EPG_NEXT or self.currentMode == MULTI_EPG_PRIMETIME or self.currentMode == EPGSEARCH_RESULT:
			self["epgTabBaseActions"].setEnabled(True)
			self["epgGreenActions"].setEnabled(True)
			if IMDB_INSTALLED:
				self["epgYellowActions"].setEnabled(True)
		elif self.currentMode == SINGLE_EPG:
			self["epgTabBaseActions"].setEnabled(True)
			self["epgGreenActions"].setEnabled(True)
			if KEEP_OUTDATED_TIME != 0:
				self["epgBlueActions"].setEnabled(True)
			if IMDB_INSTALLED:
				self["epgYellowActions"].setEnabled(True)
		elif self.currentMode == TIMERLIST:
			self["actions"].setEnabled(True)
		elif self.currentMode == EPGSEARCH_HISTORY:
			self["epgHistoryActions"].setEnabled(True)
			self["epgRedActions"].setEnabled(True)
			self["epgGreenActions"].setEnabled(True)
			self["epgYellowActions"].setEnabled(True)
		elif self.currentMode == EPGSEARCH_MANUAL:
			self["tabNavigationActions"].setEnabled(False)
			self["epgManualSearchActions"].setEnabled(True)
		elif self.currentMode == EPGSEARCH_RESULT:
			self["tabNavigationActions"].setEnabled(False)
			
		if not self.configTabsShown:
			self["settingsActions"].setEnabled(False)
			self["tabNavigationActions"].setEnabled(True)
			self["epgGreenActions"].setEnabled(True)
			
