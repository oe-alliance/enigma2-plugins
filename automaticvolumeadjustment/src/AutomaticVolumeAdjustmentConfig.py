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
# for localized messages
from . import _

from Components.config import ConfigSubsection, ConfigText, \
	config, ConfigInteger, Config, ConfigSubList, ConfigDirectory, NoSave, ConfigYesNo, ConfigSelectionNumber, ConfigSelection
from os import path as os_path, open as os_open, close as os_close, O_RDWR as os_O_RDWR, O_CREAT  as os_O_CREAT 
from pickle import load as pickle_load, dump as pickle_dump
from enigma import eEnv

CONFIG_FILE_VOLUME = eEnv.resolve('${sysconfdir}/enigma2/ava_volume.cfg')

def getVolumeDict():
	if os_path.exists(CONFIG_FILE_VOLUME):
		pkl_file = open(CONFIG_FILE_VOLUME, 'rb')
		if pkl_file:
			volumedict = pickle_load(pkl_file)
			pkl_file.close()
			return volumedict
	return {}

def saveVolumeDict(dict):
	pkl_file = open(CONFIG_FILE_VOLUME, 'wb')
	if pkl_file:
		pickle_dump(dict, pkl_file)
		pkl_file.close()

class AutomaticVolumeAdjustmentConfig():
	def __init__(self):
		self.CONFIG_FILE = eEnv.resolve('${sysconfdir}/enigma2/ava_setup.cfg')
		# load config file
		self.loadConfigFile()

	# load config file and initialize 
	def loadConfigFile(self):
		print "[AutomaticVolumeAdjustmentConfig] Loading config file..."
		self.config = Config()
		if not os_path.exists(self.CONFIG_FILE):
			try:
				fd = os_open( self.CONFIG_FILE, os_O_RDWR|os_O_CREAT)
				os_close( fd )
			except Exception, e:
				print "Error: ", e
		try:
			self.config.loadFromFile(self.CONFIG_FILE)
		except Exception, e:
			print "Error: ", e
		self.config.entriescount =  ConfigInteger(0)
		self.config.Entries = ConfigSubList()
		self.config.enable = ConfigYesNo(default=False)
		self.config.modus = ConfigSelection(choices=[("0", _("Automatic volume adjust")), ("1", _("Remember service volume value"))], default="0")
		self.config.adustvalue = ConfigSelectionNumber(-50, 50, 5, default=25)
		self.config.mpeg_max_volume = ConfigSelectionNumber(10, 100, 5, default=100)
		self.config.show_volumebar = ConfigYesNo(default=False)
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
		self.config.Entries[i].servicereference = ConfigText(default="")
		self.config.Entries[i].name = NoSave(ConfigDirectory(default=_("Press OK to select a service")))
		self.config.Entries[i].adjustvalue = ConfigSelectionNumber(-50, 50, 5, default=25)
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
