# -*- coding: utf-8 -*-
#
#  AutomaticVolumeAdjustment E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2010
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
from Components.config import ConfigSubsection, ConfigText, \
	config, ConfigInteger, Config, ConfigSubList, ConfigDirectory, NoSave, ConfigYesNo
from os import path as os_path, open as os_open, close as os_close, O_RDWR as os_O_RDWR, O_CREAT  as os_O_CREAT 

class AutomaticVolumeAdjustmentConfig():
	def __init__(self):
		self.CONFIG_FILE = '/usr/lib/enigma2/python/Plugins/SystemPlugins/AutomaticVolumeAdjustment/config'
		# load config file
		self.loadConfigFile()

	# load config file and initialize 
	def loadConfigFile(self):
		print "[AutomaticVolumeAdjustmentConfig] Loading config file..."
		self.config = Config()
		if not os_path.exists(self.CONFIG_FILE):
			fd = os_open( self.CONFIG_FILE, os_O_RDWR|os_O_CREAT)
			os_close( fd )
		self.config.loadFromFile(self.CONFIG_FILE)
		self.config.entriescount =  ConfigInteger(0)
		self.config.Entries = ConfigSubList()
		self.config.enable = ConfigYesNo(default = False)
		self.config.adustvalue = ConfigInteger(default=25, limits=(0,50))
		self.config.mpeg_max_volume = ConfigInteger(default=100, limits=(10,100))
		self.config.show_volumebar = ConfigYesNo(default = False)
		self.initConfig()

	def initConfig(self):
		count = self.config.entriescount.value
		if count != 0:
			i = 0
			while i < count:
				self.initEntryConfig()
				i += 1
		print "[AutomaticVolumeAdjustmentConfig] Loaded %s entries from config file..." % count

	def initEntryConfig(self):
		self.config.Entries.append(ConfigSubsection())
		i = len(self.config.Entries) - 1
		self.config.Entries[i].servicereference = ConfigText(default = "")
		self.config.Entries[i].name = NoSave(ConfigDirectory(default = _("Press OK to select a service")))
		self.config.Entries[i].adjustvalue = ConfigInteger(default=25, limits=(0,50))
		return self.config.Entries[i]
	
	def remove(self, configItem):
		self.config.entriescount.value = self.config.entriescount.value - 1
		self.config.entriescount.save()
		self.config.Entries.remove(configItem)
		self.config.Entries.save()
		self.save()
	
	def save(self):
		print "[AutomaticVolumeAdjustmentConfig] saving config file..."
		self.config.saveToFile(self.CONFIG_FILE)
