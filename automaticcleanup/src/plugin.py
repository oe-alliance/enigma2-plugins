# -*- coding: utf-8 -*-
#
#  AutomaticCleanup E2
#
#  $Id$
#
#  Coded by JuSt611 © 2011
#  Derived from Automatic Timerlist Cleanup plugin written by Dr. Best
#  and EMC plugin written by moveq
#  and placed in the public domain. They have my thanks.
#  Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=159095
#
#  Provided with no warranties of any sort.
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

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# Enigma
from enigma import eTimer
from time import mktime, strftime, strptime, time, localtime

# Timer
from timer import TimerEntry

# OS
from glob import glob
from os import path, remove, listdir

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

# Configuration
from Components.config import config, ConfigSubsection, ConfigSelection, getConfigListEntry, ConfigYesNo, ConfigText
from Components.Sources.StaticText import StaticText

# MessageBox
from Screens.MessageBox import MessageBox

# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen

# GUI (Summary)
from Screens.Setup import SetupSummary

from boxbranding import getImageDistro
###############################################################################        
VERSION = "0.1.9"
# History:
# 0.1.2 First public version
# 0.1.3 Prevention of timerlist cleanup if duplicated with EMC plugin
#       Fix producing crash of Softwaremanager
#       Show version in print messages for ease of crashlog check
# 0.1.4 Option added to cleanup orphaned movie files
#       Delete expired disabled timerlist entries, except those marked "repeated"
#       Performance improvement: Check timerentry StateChange only if option
#       "Timerlist cleanup immediately after recording" is set
#       Help button added
#       Cleanup crashlog feature invalidated for DMM plugin feed distribution
# 0.1.5 Fix infinite loop when timerlist cleanup is set to option "immediately after recording"
# 0.1.6 Fix crash if settings backup file date ends with "2"
# 0.1.7 Cleanup of orphaned movie files modified to support EMC v3
# 0.1.8 Performance improvement: avoid duplicate cleanup of orphaned movie files if EMC movie_homepath is same as E2 moviePath
# 0.1.9	Remove orphaned files in movie path marked for E2 smooth deletion (during session start only, to avoid conflicting E2)
#		Simplify translation code: Setting the os LANGUAGE variable isn't needed anymore
###############################################################################  
pluginPrintname = "[AutomaticCleanup Ver. %s]" %VERSION
DEBUG = False # If set True, plugin won't remove any file physically, instead prints file names in log for verification purposes
###############################################################################

config.plugins.AutomaticCleanup = ConfigSubsection()
config.plugins.AutomaticCleanup.deleteCrashlogsOlderThan = ConfigSelection(default = "-1",
	choices = [("-1",_("void"))])
config.plugins.AutomaticCleanup.keepCrashlogs = ConfigSelection(default = "-1",
	choices = [("-1",_("all"))])
config.plugins.AutomaticCleanup.deleteSettingsOlderThan = ConfigSelection(default = "-1",
	choices = [("-1",_("cleanup disabled")),("183",_("older than 6 months")),("91",_("older than 3 months")),("28",_("older than 4 weeks")),("14",_("older than 2 weeks")),("7",_("older than 1 week"))])
config.plugins.AutomaticCleanup.keepSettings = ConfigSelection(default = "-1",
	choices = [("-1",_("all")), ("10",_("last 10")),("5",_("last 5")),("3",_("last 3")),("2",_("last 2")),("1",_("only last one"))])
config.plugins.AutomaticCleanup.deleteTimersOlderThan = ConfigSelection(default = "-1",
	choices = [("-1",_("cleanup disabled")),("42",_("older than 6 weeks")),("28",_("older than 4 weeks")),("14",_("older than 2 weeks")),("7",_("older than 1 week")),("3",_("older than 3 days")),("1",_("older than 1 day")),("0",_("immediately after recording"))])
config.plugins.AutomaticCleanup.deleteOrphanedMovieFiles = ConfigYesNo(default = False)


class AutomaticCleanupSetup(Screen, ConfigListScreen): # config

	skin = """
		<screen name="SystemCleanup" position="center,center" size="630,315" title="Automatic System Cleanup Setup" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="5,5" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="165,5" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="325,5" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="485,5" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			
			<widget render="Label" source="key_red" position="5,5" size="140,40" zPosition="2" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="165,5" size="140,40" zPosition="2" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_yellow" position="325,5" size="140,40" zPosition="2" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />

			<widget name="config" position="5,60" size="620,155" scrollbarMode="showOnDemand" />

			<ePixmap pixmap="skin_default/div-h.png" position="0,220" zPosition="1" size="630,2" />
			<widget source="help" render="Label" position="5,235" size="620,75" font="Regular;21" /> 
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
			getConfigListEntry(_("Delete orphaned movie files"), config.plugins.AutomaticCleanup.deleteOrphanedMovieFiles,
				_("If enabled, orphaned movie files will be automatically deleted from movie directories.")),
			getConfigListEntry(_("Delete crashlogs"), config.plugins.AutomaticCleanup.deleteCrashlogsOlderThan,
				_('Sorry, this feature is not available due to license reasons. To get the full version, please search the web for "dreambox automaticcleanup."')),
			getConfigListEntry(_("Maximum number of crashlogs"), config.plugins.AutomaticCleanup.keepCrashlogs,
				_('Sorry, this feature is not available due to license reasons. To get the full version, please search the web for "dreambox automaticcleanup."')),
			]

		try:
			# try to import EMC module to check for its existence
			from Plugins.Extensions.EnhancedMovieCenter.EnhancedMovieCenter import EnhancedMovieCenterMenu 
			self.EMC_timer_autocln = config.EMC.timer_autocln.value
		except ImportError, ie:
			print pluginPrintname, "EMC not installed:", ie
			self.EMC_timer_autocln = False
			
		if self.EMC_timer_autocln: # Timer cleanup enabled in EMC plugin?
			self.list.append(getConfigListEntry(_("Delete timerlist entries"), config.plugins.AutomaticCleanup.deleteTimersOlderThan,
				_("Timerlist cleanup is enabled in EMC plugin! To avoid crashes, we won't delete entries whilst this option is enabled in EMC."))) # Avoid duplicate cleanup
		else:
			self.list.append(getConfigListEntry(_("Delete timerlist entries"), config.plugins.AutomaticCleanup.deleteTimersOlderThan,
				_("Specify, how long expired timer list entries shall be kept at most. Deactivated repeat timer entries won't be deleted ever.")))
			
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
		self["key_yellow"] = StaticText(_("Help"))

		self["help"] = StaticText()		

		# Define Actions		
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
			{
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow": self.keyHelp,		
			"cancel": self.keyCancel,
			"save": self.keySave,
			"ok": self.keySave,
			}, -2)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(' '.join((_("Automatic System Cleanup Setup"), _("Ver."), VERSION)))

	def configHelp(self):
		self["help"].text = self["config"].getCurrent()[2]

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
		
	def keyHelp(self):            
		self.session.open(MessageBox,
			_('Cleanup timerlist, orphaned movie files and stored setting backups automatically.\n\nModify the settings to match your preferences. More detailed explanations given with each adjustable option.'), 
			MessageBox.TYPE_INFO)


class AutomaticCleanup:
	if DEBUG:
		checkInterval = 60 * 3 # check timerlist every 3 minutes
	else:
		checkInterval = 60 * 60 * 24 # check timerlist every 24 hours

	def __init__(self, session):
		self.session = session
		if DEBUG: print pluginPrintname, "Starting in debugging mode..."
		else: print pluginPrintname, "Starting AutomaticCleanup..."
		self.timer = eTimer() # check timer
		self.timer.callback.append(self.doCleanup)
		self.initialState = True
		self.doCleanup() # always check immediately after starting plugin
		self.initialState = False
		config.plugins.AutomaticCleanup.deleteSettingsOlderThan.addNotifier(self.configChange, initial_call = False)
		config.plugins.AutomaticCleanup.keepSettings.addNotifier(self.configChange, initial_call = False)
		config.plugins.AutomaticCleanup.deleteOrphanedMovieFiles.addNotifier(self.configChange, initial_call = False)
		config.plugins.AutomaticCleanup.deleteTimersOlderThan.addNotifier(self.configChange, initial_call = False)
		self.session.nav.RecordTimer.on_state_change.append(self.timerentryOnStateChange)
		
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
		if self.timer.isActive(): # stop timer if running
			self.timer.stop()
		if self.cleanupEnabled(): # check only if feature is enabled
			self.cleanupSettings()
			self.cleanupMovies()
			self.cleanupTimerlist()
			print pluginPrintname, "Next automatic cleanup at", strftime("%c", localtime(time()+self.checkInterval))
			self.timer.startLongTimer(self.checkInterval) # check again after x secs
		else:
			print pluginPrintname, "Cleanup disabled"
		
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
			print pluginPrintname, "Setting backups cleanup disabled"
				
	def filterSettings(self):
		self.deleteList = [ ]
		
		keep = int(config.plugins.AutomaticCleanup.keepSettings.value)
		if keep > -1: # don't keep all setting backups
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
				i = self.numSettings - keep + 1 # increment for uncounted latest
				# if there are less settings than we want to keep, check the
				# whole settings list
				if i < 0:
					i = 0
			else:
				i = 0
			
			while i < self.numSettings:
				self.backupPath = self.getBackupPath()
				backupDatePos = self.settingList[i].rfind('/') + 1
				backupDate = self.settingList[i][backupDatePos:backupDatePos + 10]
				if DEBUG: print pluginPrintname, "Backup path: %s, file: %s, date: %s"  %(self.backupPath, self.settingList[i], backupDate)
				settingTime = mktime(strptime(backupDate, "%Y-%m-%d"))
				if int(settingTime) > deleteOlderThan:
					break
				self.deleteList.append(self.settingList[i])
				i += 1
			
			print pluginPrintname, "Found %i outdated setting backup(s)"  % i

		for setting in self.deleteList:
			if DEBUG: print pluginPrintname, "Setting backup to delete:", setting
			else: remove(setting)

		print pluginPrintname, "Deleted %i setting backup(s)"  % len(self.deleteList)
						
	def getBackupPath(self):	
		try:
			# try to import SoftwareManager module to check for its existence
			from Plugins.SystemPlugins.SoftwareManager.plugin import UpdatePluginMenu
			backuppath = config.plugins.configurationbackup.backuplocation.value
		except ImportError, ie:
			print pluginPrintname, "SoftwareManager not installed:", ie
			backuppath = '/media/hdd/'
		if backuppath.endswith('/'): return (backuppath + 'backup')
		else: return (backuppath + '/backup')		
		
	def cleanupTimerlist(self):
		try:
			# try to import EMC module to check for its existence
			from Plugins.Extensions.EnhancedMovieCenter.EnhancedMovieCenter import EnhancedMovieCenterMenu 
			self.EMC_timer_autocln = config.EMC.timer_autocln.value
		except ImportError, ie:
			print pluginPrintname, "EMC not installed:", ie
			self.EMC_timer_autocln = False
			
		if int(config.plugins.AutomaticCleanup.deleteTimersOlderThan.value) > -1:  # check only if feature is enabled
			if self.EMC_timer_autocln:	# Duplicate cleanup?
				print pluginPrintname, "Timerlist cleanup skipped because it is already enabled in EMC" # we skip check to avoid crash
			else:
				expiration = time() - int(config.plugins.AutomaticCleanup.deleteTimersOlderThan.value) * 86400 # calculate end time for comparison with processed timers
				print pluginPrintname, "Cleaning up timerlist-entries older than", strftime("%c", localtime(expiration))
				if not DEBUG:
					self.session.nav.RecordTimer.processed_timers = [timerentry for timerentry in self.session.nav.RecordTimer.processed_timers if timerentry.repeated or (timerentry.end and timerentry.end > expiration)] # cleanup timerlist
		else:
			print pluginPrintname, "Timerlist cleanup disabled"
		
	def timerentryOnStateChange(self, timer):
		if int(config.plugins.AutomaticCleanup.deleteTimersOlderThan.value) == 0 and timer.state == TimerEntry.StateEnded and timer.cancelled is not True: #if enabled, timerentry ended and it was not cancelled by user
			print pluginPrintname, "Timerentry has been changed to StateEnd"
			self.cleanupTimerlist() # and check if entries have to be cleaned up in the timerlist
		
	def cleanupMovies(self):
		if config.plugins.AutomaticCleanup.deleteOrphanedMovieFiles.value: # check only if feature is enabled
			print pluginPrintname, "Cleaning up orphaned movies"
			moviePath = []
			excludePath = []
			
			from Components.UsageConfig import defaultMoviePath
			if defaultMoviePath().endswith('/'): moviePath.append(defaultMoviePath())
			else: moviePath.append(defaultMoviePath() + "/")
			if config.usage.instantrec_path.value.endswith('/'): excludePath.append(config.usage.instantrec_path.value)
			else: excludePath.append(config.usage.instantrec_path.value + "/")			
			if config.usage.timeshift_path.value.endswith('/'): excludePath.append(config.usage.timeshift_path.value)
			else: excludePath.append(config.usage.timeshift_path.value + "/")

			try:
				# try to import EMC module to check for its existence
				from Plugins.Extensions.EnhancedMovieCenter.EnhancedMovieCenter import EnhancedMovieCenterMenu
				if config.EMC.movie_homepath.value:
					path = config.EMC.movie_homepath.value
					if not path.endswith("/"): path += "/"
					if path not in moviePath:
						moviePath.append(path)
				try: # with v3 name
					if len(config.EMC.movie_trashcan_path.value) > 1:	# Trashpath specified?
						if DEBUG: print pluginPrintname, "EMC v3 trashcan path is", config.EMC.movie_trashcan_path.value
						if config.EMC.movie_trashcan_path.value.endswith('/'): excludePath.append(config.EMC.movie_trashcan_path.value)
						else: excludePath.append(config.EMC.movie_trashcan_path.value + "/")
				except KeyError, ke:
					print pluginPrintname, "EMC v3 trashcan path not specified", ke
					try: # else with v2 name
						if len(config.EMC.movie_trashpath.value) > 1:	# Trashpath specified?
							if DEBUG: print pluginPrintname, "EMC v2 trashcan path is", config.EMC.movie_trashpath.value
							if config.EMC.movie_trashpath.value.endswith('/'): excludePath.append(config.EMC.movie_trashpath.value)
							else: excludePath.append(config.EMC.movie_trashpath.value + "/")
					except KeyError, ke:
						print pluginPrintname, "EMC v2 trashcan path not specified", ke
			except ImportError, ie:
				print pluginPrintname, "EMC not installed:", ie

			if len(moviePath) == 0:
				print pluginPrintname, "No movies found!"
			else:
				for f in range(len(excludePath)):
					if excludePath[f].startswith("/hdd"): excludePath[f] = "/media" + excludePath[f]
				print pluginPrintname, "Movie path:", moviePath
				print pluginPrintname, "Excluded movie path:", excludePath
				for checkPath in moviePath:	
					self.filterMovies(str(checkPath), excludePath)				
		else:
			print pluginPrintname, "Orphaned movies cleanup disabled"

	def filterMovies(self, scanPath, exclude = []):
		if not scanPath.endswith("/"): scanPath += "/"
		if scanPath.startswith("/hdd"): scanPath = "/media" + scanPath
		if not path.exists(scanPath) or scanPath in exclude: return
		if DEBUG: print pluginPrintname, "Checking moviepath:", scanPath

		if self.initialState: 
			extensions =[".ts.ap", ".ts.cuts", ".ts.cutsr", ".ts.gm", ".ts.meta", ".ts.sc", ".eit", ".png", ".ts_mp.jpg", ".ts.del", ".ts.ap.del", ".ts.cuts.del", ".ts.cutsr.del", ".ts.gm.del", ".ts.meta.del", ".ts.sc.del", ".eit.del"] # include orphaned files marked for E2 smooth deletion
		else:
			extensions = [".ts.ap", ".ts.cuts", ".ts.cutsr", ".ts.gm", ".ts.meta", ".ts.sc", ".eit", ".png", ".ts_mp.jpg"]

		for p in listdir(scanPath):
			if path.isdir(scanPath + p):
				try: self.filterMovies(scanPath + p, exclude)
				except: pass
			else:
				for ext in extensions:
					if p.endswith(ext):
						if not path.exists(scanPath + p.replace(ext, ".ts")):							
							if DEBUG:
								print pluginPrintname, "Deletable orphaned movie file:", scanPath + p
							else:
								remove(scanPath + p)
								print pluginPrintname, "Orphaned movie file deleted:", scanPath + p
						break

	def cleanupEnabled(self):
		if int(config.plugins.AutomaticCleanup.deleteTimersOlderThan.value) > -1 or \
		   int(config.plugins.AutomaticCleanup.keepSettings.value) > -1 or \
		   int(config.plugins.AutomaticCleanup.deleteSettingsOlderThan.value) > -1 or \
		   config.plugins.AutomaticCleanup.deleteOrphanedMovieFiles.value:
			return True
		else:
			return False


def autostart(session, **kwargs):
	AutomaticCleanup(session) # start plugin at sessionstart

def setup(session, **kwargs):
	session.open(AutomaticCleanupSetup) # start setup

def startSetup(menuid):
	if getImageDistro() in ('openmips'):
		if menuid != "general_menu":
			return [ ]
	else:
		if menuid != "system":
			return []
	return [(_("System cleanup"), setup, "AutomaticCleanup", 50)]
	
def Plugins(**kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart), PluginDescriptor(name="System cleanup", description=_("Automatic System Cleanup Setup"), where = PluginDescriptor.WHERE_MENU, fnc=startSetup) ]
