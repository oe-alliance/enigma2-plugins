# -*- coding: utf-8 -*-
#
#  AutomaticCleanup E2
#
#  $Id$
#
#  Coded by JuSt611 (c) 2011
#  based on scripts by Shaderman & Dr. Best
#  Support: http://i-have-a-dreambox.com/
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

from Plugins.Plugin import PluginDescriptor
from enigma import eTimer
from time import mktime, strftime, strptime, time, localtime
from timer import TimerEntry
from glob import glob
from os import path, remove

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

# Configuration
from Components.config import config, ConfigSubsection, ConfigSelection, getConfigListEntry, ConfigYesNo, ConfigText
from Components.Sources.StaticText import StaticText

# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen

# GUI (Summary)
from Screens.Setup import SetupSummary


###############################################################################        
cleanup_pluginversion = "0.1.2"
pluginPrintname = "[AutomaticCleanup]"
debug = False # If set True, plugin won't remove any file physically, instead prints file names in log for verification purposes
###############################################################################

config.plugins.AutomaticCleanup = ConfigSubsection()
config.plugins.AutomaticCleanup.deleteCrashlogsOlderThan = ConfigSelection(default = "-1",
	choices = [("-1",_("cleanup disabled")),("28",_("older than 4 weeks")),("14",_("older than 2 weeks")),("7",_("older than 1 week")),("3",_("older than 3 days")),("1",_("older than 1 day"))])
config.plugins.AutomaticCleanup.keepCrashlogs = ConfigSelection(default = "-1",
	choices = [("-1",_("all")), ("10",_("last 10")),("5",_("last 5")),("3",_("last 3")),("1",_("only last one"))])
config.plugins.AutomaticCleanup.deleteSettingsOlderThan = ConfigSelection(default = "-1",
	choices = [("-1",_("cleanup disabled")),("183",_("older than 6 months")),("91",_("older than 3 months")),("28",_("older than 4 weeks")),("14",_("older than 2 weeks")),("7",_("older than 1 week"))])
config.plugins.AutomaticCleanup.keepSettings = ConfigSelection(default = "-1",
	choices = [("-1",_("all")), ("10",_("last 10")),("5",_("last 5")),("3",_("last 3")),("2",_("last 2")),("1",_("only last one"))])
config.plugins.AutomaticCleanup.deleteTimersOlderThan = ConfigSelection(default = "-1",
	choices = [("-1",_("cleanup disabled")),("42",_("older than 6 weeks")),("28",_("older than 4 weeks")),("14",_("older than 2 weeks")),("7",_("older than 1 week")),("3",_("older than 3 days")),("1",_("older than 1 day")),("0",_("immediately after recording"))])


class AutomaticCleanupSetup(Screen, ConfigListScreen): # config

	skin = """
		<screen name="SystemCleanup" position="center,center" size="630,290" title="Automatic System Cleanup Setup" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="5,5" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="165,5" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="325,5" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="485,5" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			
			<widget render="Label" source="key_red" position="5,5" size="140,40" zPosition="2" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="165,5" size="140,40" zPosition="2" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />

			<widget name="config" position="5,60" size="620,130" scrollbarMode="showOnDemand" />

			<ePixmap pixmap="skin_default/div-h.png" position="0,195" zPosition="1" size="630,2" />
			<widget source="help" render="Label" position="5,210" size="620,75" font="Regular;21" /> 
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		
		#Summary
		self.setup_title = _("Automatic System Cleanup Setup")

		self.onChangedEntry = []
		
		self.list = [
			getConfigListEntry(_("Delete system setting backups"), config.plugins.AutomaticCleanup.deleteSettingsOlderThan,
				_("Specify, how long system setting backups shall be kept at most (even if maximum number is not yet exceeded). Latest backup will be kept anyway!")),
			getConfigListEntry(_("Maximum number of system setting backups"), config.plugins.AutomaticCleanup.keepSettings,
				_("Maximum number of system setting backups to keep, regardless of retention period.")),
			getConfigListEntry(_("Delete timerlist entries"), config.plugins.AutomaticCleanup.deleteTimersOlderThan,
				_("Specify, how long expired timer list entries shall be kept at most.")),
			]

		if (path.exists('/media/hdd') == True):
			self.list.insert(2, getConfigListEntry(_("Delete crashlogs"), config.plugins.AutomaticCleanup.deleteCrashlogsOlderThan,
				_("Specify, how long crashlogs shall be kept at most (even if maximum number is not yet exceeded).")))
			self.list.insert(3, getConfigListEntry(_("Maximum number of crashlogs"), config.plugins.AutomaticCleanup.keepCrashlogs,
				_("Maximum number of crashlogs to keep, regardless of retention period.")))
			
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)
		
		def selectionChanged():
			if self["config"].current:
				self["config"].current[1].onDeselect(self.session)
			self["config"].current = self["config"].getCurrent()
			if self["config"].current:
				self["config"].current[1].onSelect(self.session)
			for x in self["config"].onSelectionChanged:
				x()
				
		self["config"].selectionChanged = selectionChanged
		self["config"].onSelectionChanged.append(self.configHelp)

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		self["help"] = StaticText()		

		# Define Actions		
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
			{
			"red": self.keyCancel,
			"green": self.keySave,
			"cancel": self.keyCancel,
			"save": self.keySave,
			"ok": self.keySave,
			}, -2)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Automatic System Cleanup Setup") + " "  + _("Ver.") + " " + cleanup_pluginversion)

	def configHelp(self):
		cur = self["config"].getCurrent()
		self["help"].text = cur[2]

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass	
			
	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary


class AutomaticCleanup:
        checkInterval = 60 * 60 * 24 # check timerlist every 24 hours
	def __init__(self, session):
		self.session = session
		if debug:
			print pluginPrintname, "Starting in debugging mode..."
		else:
			print pluginPrintname, "Starting AutomaticCleanup..."
		self.timer = eTimer() # check timer
		self.timer.callback.append(self.doCleanup)
		if self.timer.isActive(): # stop timer if running
			self.timer.stop()
		self.doCleanup() # always check immediately after starting plugin
		config.plugins.AutomaticCleanup.deleteCrashlogsOlderThan.addNotifier(self.configChange, initial_call = False)
		config.plugins.AutomaticCleanup.keepCrashlogs.addNotifier(self.configChange, initial_call = False)
		config.plugins.AutomaticCleanup.deleteSettingsOlderThan.addNotifier(self.configChange, initial_call = False)
		config.plugins.AutomaticCleanup.keepSettings.addNotifier(self.configChange, initial_call = False)
		config.plugins.AutomaticCleanup.deleteTimersOlderThan.addNotifier(self.configChange, initial_call = False)
		
	def configChange(self, configElement = None):
		# config was changed in setup
		if self.timer.isActive(): # stop timer if running
			self.timer.stop()
		print pluginPrintname, "Setup values have changed"
		if self.cleanupEnabled(): # check only if feature is enabled
			print pluginPrintname, "Next automatic timerlist cleanup at ", strftime("%c", localtime(time()+120))
			self.timer.startLongTimer(120) # check timerlist in 2 minutes after changing 
		else:
			print pluginPrintname, "Cleanup disabled"
			
	def doCleanup(self):
		if self.cleanupEnabled(): # check only if feature is enabled
			self.cleanupCrashlogs()
			self.cleanupSettings()
			self.cleanupTimerlist()
			print pluginPrintname, "Next automatic cleanup at", strftime("%c", localtime(time()+self.checkInterval))
			self.timer.startLongTimer(self.checkInterval) # check again after x secs
		else:
			print pluginPrintname, "Cleanup disabled"

	def cleanupCrashlogs(self):
		if int(config.plugins.AutomaticCleanup.keepCrashlogs.value) > -1 or int(config.plugins.AutomaticCleanup.deleteCrashlogsOlderThan.value) > -1: # check only if feature is enabled
			print pluginPrintname, "Cleaning up crashlogs"
			if (path.exists('/media/hdd') == False):
				print pluginPrintname, "No HDD available!"
				return
			self.crashlogList = glob('/media/hdd/enigma2_crash_*.log')
			self.crashlogList.extend(glob('/media/hdd/enigma2_crash_*.log.sent'))			
			self.numCrashlogs = len(self.crashlogList)
			if self.numCrashlogs == 0:
				print pluginPrintname, "No crashlog found!"
			else:
				self.crashlogList.sort()
				self.filterCrashlogs()
		else:
			print pluginPrintname, "Cleaning up crashlogs disabled"

	def filterCrashlogs(self):
		self.deleteList = [ ]
		
		keep = int(config.plugins.AutomaticCleanup.keepCrashlogs.value)
		if keep > -1: # don't keep all crashlogs
			if keep >= self.numCrashlogs:
				print pluginPrintname, "Found %i crashlog(s), keeping max %i" % (self.numCrashlogs, keep)
			else:
				print pluginPrintname, "Keeping the %i latest crashlogs" % keep
				# add all crashlogs > config.plugins.AutomaticCleanup.keepCrashlogs.value
				# to a new list. the crashlogs in this new list will be deleted later.
				self.deleteList = self.crashlogList[0 : self.numCrashlogs - keep]

		if int(config.plugins.AutomaticCleanup.deleteCrashlogsOlderThan.value) > -1:
			print pluginPrintname, "Searching for outdated crashlogs"
			now = int(time())
			# 86400 = one day in seconds
			deleteOlderThan = now - 86400 * int(config.plugins.AutomaticCleanup.deleteCrashlogsOlderThan.value)
			
			if keep > -1: # don't keep all crashlogs
				# start checking the range in self.crashlogList which wasn't copied to
				# self.deleteList
				i = self.numCrashlogs - keep
				# if there are less crashlogs than we want to keep, check the
				# whole crashlog list
				if i < 0:
					i = 0
			else:
				i = 0
			
			while i < self.numCrashlogs:
				crashTime = self.crashlogList[i].lstrip('/media/hdd/enigma2_crash_')
				crashTime = crashTime.rstrip('.sent')
				crashTime = crashTime.rstrip('.log')
				if int(crashTime) > deleteOlderThan:
					break
				self.deleteList.append(self.crashlogList[i])
				i += 1
			
			print pluginPrintname, "Found %i outdated crashlog(s)"  % i

		for crashlog in self.deleteList:
			if debug:
				print pluginPrintname, "Crashlog to delete: %s"  % crashlog
			else:				
				remove(crashlog)

		print pluginPrintname, "Deleted %i crashlog(s)"  % len(self.deleteList)
		
	def cleanupSettings(self):
		if int(config.plugins.AutomaticCleanup.keepSettings.value) > -1 or int(config.plugins.AutomaticCleanup.deleteSettingsOlderThan.value) > -1: # check only if feature is enabled
			print pluginPrintname, "Cleaning up setting backups"
			self.backupPath = self.getBackupPath()
			if (path.exists(self.backupPath) == False):
				print pluginPrintname, "No backup directory available!"
				return
			self.settingList = glob(self.backupPath + '/*-enigma2settingsbackup.tar.gz')
			self.numSettings = len(self.settingList)
			if self.numSettings == 0:
				print pluginPrintname, "No deletable setting backup found!"
			else:
				self.settingList.sort()
				self.filterSettings()
		else:
			print pluginPrintname, "Cleaning up setting backups disabled"
				
	def filterSettings(self):
		self.deleteList = [ ]
		
		keep = int(config.plugins.AutomaticCleanup.keepSettings.value)
		if keep > -1: # don't keep all crashlogs
			if keep > self.numSettings:
				print pluginPrintname, "Found %i setting backup(s), keeping max %i" %(self.numSettings+1, keep) # increment for uncounted latest
			else:
				print pluginPrintname, "Keeping the %i latest settings"  % keep
				# add all settings > config.plugins.AutomaticCleanup.keepSettings.value
				# to a new list. the settings in this new list will be deleted later.
				self.deleteList = self.settingList[0 : self.numSettings - keep + 1] # increment for uncounted latest

		if int(config.plugins.AutomaticCleanup.deleteSettingsOlderThan.value) > -1:
			print pluginPrintname, "Searching for outdated setting backup(s)"
			now = int(time())
			# 86400 = one day in seconds
			deleteOlderThan = now - 86400 * int(config.plugins.AutomaticCleanup.deleteSettingsOlderThan.value)
			
			if keep > -1: # don't keep all settings
				# start checking the range in self.settingList which wasn't copied to
				# self.deleteList
				i = self.numSettings - keep
				# if there are less settings than we want to keep, check the
				# whole settings list
				if i < 0:
					i = 0
			else:
				i = 0
			
			while i < self.numSettings:
				#print (pluginPrintname, "Backup path %s"  % self.settingList[i] if debug)
				backupDate = self.settingList[i].lstrip(self.getBackupPath() + "/")
				#print (pluginPrintname, "Backup file %s"  % backupDate if debug)
				backupDate = backupDate.rstrip('-enigma2settingsbackup.tar.gz')
				#print (pluginPrintname, "Backup date %s"  % backupDate if debug)
				settingTime = mktime(strptime(backupDate, "%Y-%m-%d"))
				if int(settingTime) > deleteOlderThan:
					break
				self.deleteList.append(self.settingList[i])
				i += 1
			
			print pluginPrintname, "Found %i outdated setting backup(s)"  % i

		for setting in self.deleteList:
			if debug:
				print pluginPrintname, "Setting backup to delete: %s"  % setting
			else:
				remove(setting)

		print pluginPrintname, "Deleted %i setting backup(s)"  % len(self.deleteList)
						
	def getBackupPath(self):
		config.plugins.configurationbackup = ConfigSubsection()
		config.plugins.configurationbackup.backuplocation = ConfigText(default = '/media/hdd/')
		backuppath = config.plugins.configurationbackup.backuplocation.value
		if backuppath.endswith('/'):
			return backuppath + 'backup'
		else:
			return backuppath + '/backup'
		
	def cleanupTimerlist(self):
		if int(config.plugins.AutomaticCleanup.deleteTimersOlderThan.value) > -1: # check only if feature is enabled
			self.session.nav.RecordTimer.on_state_change.append(self.timerentryOnStateChange)
			value = time() - int(config.plugins.AutomaticCleanup.deleteTimersOlderThan.value) * 86400 # calculate end time for comparison with processed timers
			print pluginPrintname, "Cleaning up timerlist-entries older than",strftime("%c", localtime(value))
			if not debug:
				self.session.nav.RecordTimer.processed_timers = [ timerentry for timerentry in self.session.nav.RecordTimer.processed_timers if timerentry.disabled or (timerentry.end and timerentry.end > value) ] # cleanup timerlist			
		else:
			print pluginPrintname, "Timerlist cleanup disabled"
		
	def timerentryOnStateChange(self, timer):
		if int(config.plugins.AutomaticCleanup.deleteTimersOlderThan.value) > -1 and timer.state == TimerEntry.StateEnded and timer.cancelled is not True: #if enabled, timerentry ended and it was not cancelled by user
			print pluginPrintname, "Timerentry has been changed to StateEnd"
			self.cleanupTimerlist() # and check if entries have to be cleaned up in the timerlist
						
	def cleanupEnabled(self):
		if int(config.plugins.AutomaticCleanup.deleteTimersOlderThan.value) > -1 or \
		   int(config.plugins.AutomaticCleanup.keepCrashlogs.value) > -1 or \
		   int(config.plugins.AutomaticCleanup.deleteCrashlogsOlderThan.value) > -1 or \
		   int(config.plugins.AutomaticCleanup.keepSettings.value) > -1 or \
		   int(config.plugins.AutomaticCleanup.deleteSettingsOlderThan.value) > -1:
			return True
		else:
			return False


def autostart(session, **kwargs):
	AutomaticCleanup(session) # start plugin at sessionstart
	
def setup(session, **kwargs):
	session.open(AutomaticCleanupSetup) # start setup

def startSetup(menuid):
	if menuid != "system": # show setup only in system level menu
		return []
	return [(_("System cleanup"), setup, "AutomaticCleanup", 46)]
	
def Plugins(**kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart), PluginDescriptor(name="System cleanup", description=_("Automatic System Cleanup Setup"), where = PluginDescriptor.WHERE_MENU, fnc=startSetup) ]
