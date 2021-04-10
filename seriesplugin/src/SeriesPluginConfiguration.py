# -*- coding: utf-8 -*-
#######################################################################
#
#    Series Plugin for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=TBD
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################

import os


# for localized messages
from . import _

# Config
from Components.config import *
from Components.ConfigList import ConfigListScreen
from Components.Button import Button
from Components.Sources.StaticText import StaticText

from Components.ActionMap import ActionMap
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Setup import SetupSummary

from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from Plugins.Plugin import PluginDescriptor

# Plugin internal
from SeriesPlugin import resetInstance, getInstance
from SeriesPluginIndependent import startIndependent, stopIndependent
from FilePatterns import readFilePatterns
from DirectoryPatterns import readDirectoryPatterns
from Logger import log
from ShowLogScreen import ShowLogScreen
from Channels import getTVBouquets
from ChannelEditor import ChannelEditor


def checkList(cfg):
	for choices in cfg.choices.choices:
		if cfg.value == choices[0]:
			return
	for choices in cfg.choices.choices:
		if cfg.default == choices[0]:
			cfg.value = cfg.default
			return
	cfg.value = cfg.choices.choices[0][0]


#######################################################
# Configuration screen
class SeriesPluginConfiguration(ConfigListScreen, Screen):
	
	skinfile = os.path.join(resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/Skins/Setup.xml")
	skin = open(skinfile).read()
	
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ["SeriesPluginConfiguration"]
		
		from plugin import NAME, VERSION
		self.setup_title = NAME + " " + _("Configuration") + " " + VERSION
		
		log.debug("SeriesPluginConfiguration")
		
		self.onChangedEntry = []
		
		# Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_blue"] = Button(_("Show Log"))
		self["key_yellow"] = Button(_("Channel Edit"))
		
		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ChannelSelectBaseActions", "ColorActions"],
		{
			"cancel":		self.keyCancel,
			"save":			self.keySave,
			"nextBouquet":	self.pageUp,
			"prevBouquet":	self.pageDown,
			"blue":			self.showLog,
			"yellow":		self.openChannelEditor,
			"ok": 			self.keyOK,
			"left": 		self.keyLeft,
			"right": 		self.keyRight,
		}, -2) # higher priority
		
		stopIndependent()
		#resetInstance()
		self.seriesPlugin = getInstance()
		
		# Create temporary identifier config elements
		identifiers = self.seriesPlugin.modules
		identifiers_elapsed = [k for k,v in identifiers.items() if v.knowsElapsed()]
		identifiers_today   = [k for k,v in identifiers.items() if v.knowsToday()]
		identifiers_future  = [k for k,v in identifiers.items() if v.knowsFuture()]
		if config.plugins.seriesplugin.identifier_elapsed.value in identifiers_elapsed:
			self.cfg_identifier_elapsed = NoSave(ConfigSelection(choices=identifiers_elapsed, default=config.plugins.seriesplugin.identifier_elapsed.value))
		else:
			self.cfg_identifier_elapsed = NoSave(ConfigSelection(choices=identifiers_elapsed, default=identifiers_elapsed[0]))
			self.changesMade = True
		if config.plugins.seriesplugin.identifier_today.value in identifiers_today:
			self.cfg_identifier_today   = NoSave(ConfigSelection(choices=identifiers_today,   default=config.plugins.seriesplugin.identifier_today.value))
		else:
			self.cfg_identifier_today   = NoSave(ConfigSelection(choices=identifiers_today,   default=identifiers_today[0]))
			self.changesMade = True
		if config.plugins.seriesplugin.identifier_future.value in identifiers_future:
			self.cfg_identifier_future  = NoSave(ConfigSelection(choices=identifiers_future,  default=config.plugins.seriesplugin.identifier_future.value))
		else:
			self.cfg_identifier_future  = NoSave(ConfigSelection(choices=identifiers_future,  default=identifiers_future[0]))
			self.changesMade = True
		
		# Load patterns
		patterns_file = readFilePatterns()
		self.cfg_pattern_title       = NoSave(ConfigSelection(choices=patterns_file, default=config.plugins.seriesplugin.pattern_title.value))
		self.cfg_pattern_description = NoSave(ConfigSelection(choices=patterns_file, default=config.plugins.seriesplugin.pattern_description.value))
		#self.cfg_pattern_record     = NoSave( ConfigSelection(choices = patterns_file, default = config.plugins.seriesplugin.pattern_record.value ) )
		patterns_directory = readDirectoryPatterns()
		self.cfg_pattern_directory   = NoSave(ConfigSelection(choices=patterns_directory, default=config.plugins.seriesplugin.pattern_directory.value))
		
		bouquetList = [("", "")]
		tvbouquets = getTVBouquets()
		for bouquet in tvbouquets:
			bouquetList.append((bouquet[1], bouquet[1]))
		self.cfg_bouquet_main = NoSave(ConfigSelection(choices=bouquetList,  default=config.plugins.seriesplugin.bouquet_main.value or str(list(zip(*bouquetList)[1]))))
		
		checkList(self.cfg_pattern_title)
		checkList(self.cfg_pattern_description)
		checkList(self.cfg_pattern_directory)
		checkList(self.cfg_bouquet_main)
		
		self.changesMade = False
		
		# Initialize Configuration
		self.list = []
		self.buildConfig()
		ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changed)
		
		self.changed()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_(self.setup_title))

	def buildConfig(self):
		#    _config list entry
		#    _                                                                                     , config element
		
		self.list.append(getConfigListEntry(_("Enable SeriesPlugin"), config.plugins.seriesplugin.enabled))
		
		if config.plugins.seriesplugin.enabled.value:
			
			# Check if xmltvimport exists
			if os.path.exists("/etc/epgimport"):
				log.debug("Config: Found epgimport")
				self.list.append(getConfigListEntry(_("Enable support for EPGImport"), config.plugins.seriesplugin.epgimport))
			elif config.plugins.seriesplugin.epgimport.value:
				self.changesMade = True
				config.plugins.seriesplugin.epgimport.value = False
			
			# Check if xmltvimport exists
			if os.path.exists("/etc/xmltvimport"):
				log.debug("Config: Found xmltvimport")
				self.list.append(getConfigListEntry(_("Enable support for XMLTVImport"), config.plugins.seriesplugin.xmltvimport))
			elif config.plugins.seriesplugin.xmltvimport.value:
				self.changesMade = True
				config.plugins.seriesplugin.xmltvimport.value = False
			
			self.list.append(getConfigListEntry(_("Show in info menu"), config.plugins.seriesplugin.menu_info))
			self.list.append(getConfigListEntry(_("Show in extensions menu"), config.plugins.seriesplugin.menu_extensions))
			self.list.append(getConfigListEntry(_("Show in epg menu"), config.plugins.seriesplugin.menu_epg))
			self.list.append(getConfigListEntry(_("Show in channel menu"), config.plugins.seriesplugin.menu_channel))
			self.list.append(getConfigListEntry(_("Show Info in movie list menu"), config.plugins.seriesplugin.menu_movie_info))
			self.list.append(getConfigListEntry(_("Show Rename in movie list menu"), config.plugins.seriesplugin.menu_movie_rename))
			self.list.append(getConfigListEntry(_("Check timer list from extension menu"), config.plugins.seriesplugin.check_timer_list))
			
			#if len( config.plugins.seriesplugin.identifier_elapsed.choices ) > 1:
			#self.list.append( getConfigListEntry(  _("Select identifier for elapsed events")       , self.cfg_identifier_elapsed ) )
			#if len( config.plugins.seriesplugin.identifier_today.choices ) > 1:
			#self.list.append( getConfigListEntry(  _("Select identifier for today events")         , self.cfg_identifier_today ) )
			#if len( config.plugins.seriesplugin.identifier_future.choices ) > 1:
			#self.list.append( getConfigListEntry(  _("Select identifier for future events")        , self.cfg_identifier_future ) )
			
			self.list.append(getConfigListEntry(_("Record title episode pattern"), self.cfg_pattern_title))
			self.list.append(getConfigListEntry(_("Record description episode pattern"), self.cfg_pattern_description))
			
			self.list.append(getConfigListEntry("E2: "+_("Composition of the recording filenames"), config.recording.filename_composition))
			self.list.append(getConfigListEntry(_("Record directory pattern"), self.cfg_pattern_directory))
			
			self.list.append(getConfigListEntry(_("Default season"), config.plugins.seriesplugin.default_season))
			self.list.append(getConfigListEntry(_("Default episode"), config.plugins.seriesplugin.default_episode))
			
			self.list.append(getConfigListEntry(_("Replace special characters in title"), config.plugins.seriesplugin.replace_chars))
			
			self.list.append(getConfigListEntry(_("Main bouquet for channel editor"), self.cfg_bouquet_main))
			
			self.list.append(getConfigListEntry(_("Rename files"), config.plugins.seriesplugin.rename_file))
			if config.plugins.seriesplugin.rename_file.value:
				self.list.append(getConfigListEntry(_("Use legacy filenames") + " (ä to ae)", config.plugins.seriesplugin.rename_legacy))
				self.list.append(getConfigListEntry(_("Append '_' if file exist"), config.plugins.seriesplugin.rename_existing_files))
			
			self.list.append(getConfigListEntry(_("Max time drift to match episode"), config.plugins.seriesplugin.max_time_drift))
			self.list.append(getConfigListEntry(_("Title search depths"), config.plugins.seriesplugin.search_depths))
			
			self.list.append(getConfigListEntry(_("Skip search if pattern matches"), config.plugins.seriesplugin.skip_pattern_match))
			self.list.append(getConfigListEntry(_("Skip search during records"), config.plugins.seriesplugin.skip_during_records))
			
			self.list.append(getConfigListEntry(_("AutoTimer independent mode"), config.plugins.seriesplugin.autotimer_independent))
			if config.plugins.seriesplugin.autotimer_independent.value:
				self.list.append(getConfigListEntry(_("Check timer every x minutes"), config.plugins.seriesplugin.independent_cycle))
			
			self.list.append(getConfigListEntry(_("Check Timer for corresponding EPG events"), config.plugins.seriesplugin.timer_eit_check))
			self.list.append(getConfigListEntry(_("Add tag 'SeriesPlugin' to timer"), config.plugins.seriesplugin.timer_add_tag))
			
			self.list.append(getConfigListEntry(_("Socket timeout"), config.plugins.seriesplugin.socket_timeout))
			
			self.list.append(getConfigListEntry(_("Timeout for Success Popups"), config.plugins.seriesplugin.popups_success_timeout))
			self.list.append(getConfigListEntry(_("Timeout for Warnings Popups"), config.plugins.seriesplugin.popups_warning_timeout))
			
			#self.list.append( getConfigListEntry(  _("Use local caching")                         , config.plugins.seriesplugin.caching ) )
			#if config.plugins.seriesplugin.caching.value:
			#	self.list.append( getConfigListEntry(  _("Cache expires after x hours")            , config.plugins.seriesplugin.caching_expiration ) )
			
			self.list.append(getConfigListEntry(_("Channel matching file"), config.plugins.seriesplugin.channel_file))
			self.list.append(getConfigListEntry(_("Episode pattern file"), config.plugins.seriesplugin.pattern_file))
			self.list.append(getConfigListEntry(_("Directory pattern file"), config.plugins.seriesplugin.pattern_file_directories))
			
			try:
				self.list.append(getConfigListEntry("AT: "+_("Poll automatically"), config.plugins.autotimer.autopoll))
				self.list.append(getConfigListEntry("AT: "+_("Startup delay (in min)"), config.plugins.autotimer.delay))
				self.list.append(getConfigListEntry("AT: "+_("Poll Interval (in h)"), config.plugins.autotimer.interval))
				self.list.append(getConfigListEntry("AT: "+_("Timeout (in min)"), config.plugins.autotimer.timeout))
			except:
				pass
			
			self.list.append(getConfigListEntry(_("Debug: Print debug messages (Shell)"), config.plugins.seriesplugin.debug_prints))
			self.list.append(getConfigListEntry(_("Debug: Write Log"), config.plugins.seriesplugin.write_log))
			if config.plugins.seriesplugin.write_log.value:
				self.list.append(getConfigListEntry(_("Debug: Log file path"), config.plugins.seriesplugin.log_file))
				#self.list.append( getConfigListEntry(  _("Debug: Forum user name")                  , config.plugins.seriesplugin.log_reply_user ) )
				#self.list.append( getConfigListEntry(  _("Debug: User mail address")                , config.plugins.seriesplugin.log_reply_mail ) )
			
			try:
				self.list.append(getConfigListEntry("AT: "+_("Send debug messages to shell"), config.plugins.autotimer.log_shell))
				self.list.append(getConfigListEntry("AT: "+ _("Write debug messages into file"), config.plugins.autotimer.log_write))
				if config.plugins.autotimer.log_write.value:
					self.list.append(getConfigListEntry("AT: "+_("Location and name of log file"), config.plugins.autotimer.log_file))
			except:
				pass
			
			try:
				self.list.append(getConfigListEntry("E2: "+_("Enable recording debug (Timer log)"), config.recording.debug))
			except:
				pass

	def changeConfig(self):
		self.list = []
		self.buildConfig()
		self["config"].setList(self.list)

	def changed(self):
		for x in self.onChangedEntry:
			x()
		current = self["config"].getCurrent()[1]
		if (current == config.plugins.seriesplugin.enabled or 
			current == config.plugins.seriesplugin.rename_file or
			current == config.plugins.seriesplugin.autotimer_independent or 
			current == config.plugins.seriesplugin.write_log):
			self.changeConfig()
			return
		try:
			if current == config.plugins.autotimer.log_write.value:
				self.changeConfig()
				return
		except:
			pass

	# Overwrite ConfigListScreen keySave function
	def keySave(self):
		self.saveAll()
		
		config.plugins.seriesplugin.identifier_elapsed.value = self.cfg_identifier_elapsed.value
		config.plugins.seriesplugin.identifier_today.value   = self.cfg_identifier_today.value
		config.plugins.seriesplugin.identifier_future.value  = self.cfg_identifier_future.value
		config.plugins.seriesplugin.pattern_title.value       = self.cfg_pattern_title.value
		config.plugins.seriesplugin.pattern_description.value = self.cfg_pattern_description.value
		#config.plugins.seriesplugin.pattern_record.value      = self.cfg_pattern_record.value
		config.plugins.seriesplugin.pattern_directory.value       = self.cfg_pattern_directory.value
		config.plugins.seriesplugin.bouquet_main.value = self.cfg_bouquet_main.value
		config.plugins.seriesplugin.save()
		
		self.seriesPlugin.saveXML()
		
		# Set new configuration
		from plugin import WHERE_EPGMENU, WHERE_CHANNELMENU, addSeriesPlugin, removeSeriesPlugin, SHOWINFO, RENAMESERIES, CHECKTIMERS, info, sp_extension, channel, movielist_info, movielist_rename, checkTimers
		
		if config.plugins.seriesplugin.menu_info.value:
			addSeriesPlugin(PluginDescriptor.WHERE_EVENTINFO, SHOWINFO, info)
		else:
			removeSeriesPlugin(PluginDescriptor.WHERE_EVENTINFO, SHOWINFO)
		
		if config.plugins.seriesplugin.menu_extensions.value:
			addSeriesPlugin(PluginDescriptor.WHERE_EXTENSIONSMENU, SHOWINFO, sp_extension)
		else:
			removeSeriesPlugin(PluginDescriptor.WHERE_EXTENSIONSMENU, SHOWINFO)
		
		if config.plugins.seriesplugin.menu_epg.value:
			addSeriesPlugin(WHERE_EPGMENU, SHOWINFO)
		else:
			removeSeriesPlugin(WHERE_EPGMENU, SHOWINFO)
		
		if config.plugins.seriesplugin.menu_channel.value:
			addSeriesPlugin(WHERE_CHANNELMENU, SHOWINFO, channel)
		else:
			removeSeriesPlugin(WHERE_CHANNELMENU, SHOWINFO)
		
		if config.plugins.seriesplugin.menu_movie_info.value:
			addSeriesPlugin(PluginDescriptor.WHERE_MOVIELIST, SHOWINFO, movielist_info)
		else:
			removeSeriesPlugin(PluginDescriptor.WHERE_MOVIELIST, SHOWINFO)
		
		if config.plugins.seriesplugin.menu_movie_rename.value:
			addSeriesPlugin(PluginDescriptor.WHERE_MOVIELIST, RENAMESERIES, movielist_rename)
		else:
			removeSeriesPlugin(PluginDescriptor.WHERE_MOVIELIST, RENAMESERIES)
		
		if config.plugins.seriesplugin.check_timer_list.value:
			addSeriesPlugin(PluginDescriptor.WHERE_EXTENSIONSMENU, CHECKTIMERS, checkTimers)
		else:
			removeSeriesPlugin(PluginDescriptor.WHERE_EXTENSIONSMENU, CHECKTIMERS)
		
		# To set new module configuration
		resetInstance()
		
		if config.plugins.seriesplugin.autotimer_independent.value:
			from SeriesPluginIndependent import startIndependent
			startIndependent()
			
		self.close()

	# Overwrite ConfigListScreen keyCancel function
	def keyCancel(self):
		self.help_window_was_shown = False
		log.debug("SPC keyCancel")
		#self.seriesPlugin.resetChannels()
		resetInstance()
		if self["config"].isChanged() or self.changesMade:
			self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
		else:
			self.close()

	# Overwrite Screen close function
	def close(self):
		from plugin import ABOUT
		about = ABOUT.format(**{'lookups': config.plugins.seriesplugin.lookup_counter.value})
		self.session.openWithCallback(self.closeConfirm, MessageBox, about, MessageBox.TYPE_INFO)

	def closeConfirm(self, dummy=None):
		# Call baseclass function
		Screen.close(self)
	
	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def pageUp(self):
		self["config"].instance.moveSelection(self["config"].instance.pageUp)

	def pageDown(self):
		self["config"].instance.moveSelection(self["config"].instance.pageDown)

	def showLog(self):
		#self.sendLog()
		self.session.open(ShowLogScreen, config.plugins.seriesplugin.log_file.value)

	def openChannelEditor(self):
		self.session.openWithCallback(self.channelEditorClosed, ChannelEditor)

	def channelEditorClosed(self, result=None):
		log.debug("SPC channelEditorClosed", result)
		if result:
			self.changesMade = True
		else:
			self.seriesPlugin.resetChannels()
