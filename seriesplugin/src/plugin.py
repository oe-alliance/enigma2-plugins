# -*- coding: utf-8 -*-
import os, sys, traceback

# Localization
from . import _

from time import time

# GUI (Screens)
from Screens.MessageBox import MessageBox

# Config
from Components.config import config, ConfigSubsection, ConfigEnableDisable, ConfigNumber, ConfigSelection, ConfigYesNo, ConfigText, ConfigSelectionNumber

# Plugin
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

# Plugin internal
from SeriesPluginTimer import SeriesPluginTimer
from SeriesPluginInfoScreen import SeriesPluginInfoScreen
from SeriesPluginRenamer import SeriesPluginRenamer
from SeriesPluginIndependent import startIndependent, runIndependent
from SeriesPluginConfiguration import SeriesPluginConfiguration
from Logger import splog


#######################################################
# Constants
NAME = "SeriesPlugin"
VERSION = "2.4" # Based on e
DESCRIPTION = _("SeriesPlugin")
SHOWINFO = _("Show series info (SP)")
RENAMESERIES = _("Rename serie(s) (SP)")
CHECKTIMERS = _("Check timer list for series (SP)")
SUPPORT = "http://bit.ly/seriespluginihad"
DONATE = "http://bit.ly/seriespluginpaypal"
ABOUT = "\n  " + NAME + " " + VERSION + "\n\n" \
				+ _("  (C) 2012 by betonme @ IHAD \n\n") \
				+ _("  {lookups:d} successful lookups.\n") \
				+ _("  How much time have You saved?\n\n") \
				+ _("  Support: ") + SUPPORT + "\n" \
				+ _("  Feel free to donate. \n") \
				+ _("  PayPal: ") + DONATE
try:
	from Tools.HardwareInfo import HardwareInfo
	DEVICE = HardwareInfo().get_device_name().strip()
	
	# Get Box Info
	#from Components.Network import iNetwork
	#self.BoxID = iNetwork.getAdapterAttribute("eth0", "mac")
	#self.DeviceName = HardwareInfo().get_device_name()
	#from Components.About import about
	#self.EnigmaVersion = about.getEnigmaVersionString()
	#self.ImageVersion = about.getVersionString()
except:
	DEVICE = ''

WHERE_EPGMENU     = 'WHERE_EPGMENU'
WHERE_CHANNELMENU = 'WHERE_CHANNELMENU'


#######################################################
# Initialize Configuration
config.plugins.seriesplugin = ConfigSubsection()

config.plugins.seriesplugin.enabled                   = ConfigEnableDisable(default = False)

config.plugins.seriesplugin.menu_info                 = ConfigYesNo(default = True)
config.plugins.seriesplugin.menu_extensions           = ConfigYesNo(default = False)
config.plugins.seriesplugin.menu_epg                  = ConfigYesNo(default = False)
config.plugins.seriesplugin.menu_channel              = ConfigYesNo(default = True)
config.plugins.seriesplugin.menu_movie_info           = ConfigYesNo(default = True)
config.plugins.seriesplugin.menu_movie_rename         = ConfigYesNo(default = True)

#TODO config.plugins.seriesplugin.open MessageBox or TheTVDB  ConfigSelection if hasTheTVDB

config.plugins.seriesplugin.identifier_elapsed        = ConfigText(default = "", fixed_size = False)
config.plugins.seriesplugin.identifier_today          = ConfigText(default = "", fixed_size = False)
config.plugins.seriesplugin.identifier_future         = ConfigText(default = "", fixed_size = False)

#config.plugins.seriesplugin.manager                   = ConfigSelection(choices = [("", "")], default = "")
#config.plugins.seriesplugin.guide                     = ConfigSelection(choices = [("", "")], default = "")

config.plugins.seriesplugin.pattern_file              = ConfigText(default = "/etc/enigma2/seriesplugin_patterns.json", fixed_size = False)
config.plugins.seriesplugin.pattern_title             = ConfigText(default = "{org:s} S{season:02d}E{episode:02d} {title:s}", fixed_size = False)
config.plugins.seriesplugin.pattern_description       = ConfigText(default = "S{season:02d}E{episode:02d} {title:s} {org:s}", fixed_size = False)
#config.plugins.seriesplugin.pattern_record            = ConfigText(default = "{org:s} S{season:02d}E{episode:02d} {title:s}", fixed_size = False)

config.plugins.seriesplugin.replace_chars             = ConfigText(default = ":!/\\,\(\)", fixed_size = False)

config.plugins.seriesplugin.channel_file              = ConfigText(default = "/etc/enigma2/seriesplugin_channels.xml", fixed_size = False)

config.plugins.seriesplugin.bouquet_main              = ConfigText(default = "", fixed_size = False)

config.plugins.seriesplugin.rename_file               = ConfigYesNo(default = True)
config.plugins.seriesplugin.rename_tidy               = ConfigYesNo(default = False)
config.plugins.seriesplugin.rename_legacy             = ConfigYesNo(default = False)
config.plugins.seriesplugin.rename_existing_files     = ConfigYesNo(default = False)
config.plugins.seriesplugin.rename_popups             = ConfigYesNo(default = True)
config.plugins.seriesplugin.rename_popups_success     = ConfigYesNo(default = False)
config.plugins.seriesplugin.rename_popups_timeout     = ConfigSelectionNumber(-1, 20, 1, default = 3)

config.plugins.seriesplugin.max_time_drift            = ConfigSelectionNumber(0, 600, 1, default = 15)
config.plugins.seriesplugin.search_depths             = ConfigSelectionNumber(0, 10, 1, default = 0)

config.plugins.seriesplugin.skip_during_records       = ConfigYesNo(default=False)
config.plugins.seriesplugin.skip_pattern_match        = ConfigYesNo(default=True)

config.plugins.seriesplugin.autotimer_independent     = ConfigYesNo(default = False)
config.plugins.seriesplugin.independent_cycle         = ConfigSelectionNumber(5, 24*60, 5, default = 60)
config.plugins.seriesplugin.independent_retry         = ConfigYesNo(default = False)

config.plugins.seriesplugin.check_timer_list          = ConfigYesNo(default = False)

config.plugins.seriesplugin.timer_popups              = ConfigYesNo(default = True)
config.plugins.seriesplugin.timer_popups_success      = ConfigYesNo(default = False)
config.plugins.seriesplugin.timer_popups_timeout     = ConfigSelectionNumber(-1, 20, 1, default = 3)

config.plugins.seriesplugin.caching                   = ConfigYesNo(default = True)

config.plugins.seriesplugin.debug_prints              = ConfigYesNo(default = False)
config.plugins.seriesplugin.write_log                 = ConfigYesNo(default = False)
config.plugins.seriesplugin.log_file                  = ConfigText(default = "/tmp/seriesplugin.log", fixed_size = False)
config.plugins.seriesplugin.log_reply_user            = ConfigText(default = "Dreambox User", fixed_size = False)
config.plugins.seriesplugin.log_reply_mail            = ConfigText(default = "myemail@home.com", fixed_size = False)

config.plugins.seriesplugin.ganalytics                = ConfigYesNo(default = True)

# Internal
config.plugins.seriesplugin.lookup_counter            = ConfigNumber(default = 0)
#config.plugins.seriesplugin.uid                       = ConfigText(default = str(time()), fixed_size = False)


#######################################################
# Start
def start(reason, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		# Startup
		if reason == 0:
			# Start on demand if it is requested
			if config.plugins.seriesplugin.autotimer_independent.value:
				startIndependent()
			
		# Shutdown
		elif reason == 1:
			from SeriesPlugin import resetInstance
			resetInstance()


#######################################################
# Plugin configuration
def setup(session, *args, **kwargs):
	try:
		session.open(SeriesPluginConfiguration)
	except Exception as e:
		splog(_("SeriesPlugin setup exception ") + str(e))
		#exc_type, exc_value, exc_traceback = sys.exc_info()
		#splog( exc_type, exc_value, exc_traceback )


#######################################################
# Event Info
def info(session, service=None, event=None, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			session.open(SeriesPluginInfoScreen, service, event)
		except Exception as e:
			splog(_("SeriesPlugin info exception ") + str(e))
			#exc_type, exc_value, exc_traceback = sys.exc_info()
			#splog( exc_type, exc_value, exc_traceback )


#######################################################
# Extensions menu
def sp_extension(session, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			if session:
				session.open(SeriesPluginInfoScreen)
		except Exception as e:
			splog(_("SeriesPlugin extension exception ") + str(e))


#######################################################
# Channel menu
def channel(session, service=None, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			from enigma import eServiceCenter
			info = eServiceCenter.getInstance().info(service)
			event = info.getEvent(service)
			session.open(SeriesPluginInfoScreen, service, event)
		except Exception as e:
			splog(_("SeriesPlugin extension exception ") + str(e))


#######################################################
# Timer
def checkTimers(session, *args, **kwargs):
	runIndependent()


#######################################################
# Movielist menu rename
def movielist_rename(session, service, services=None, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			if services:
				if not isinstance(services, list):
					services = [services]	
			else:
				services = [service]
			SeriesPluginRenamer(session, services)
		except Exception as e:
			splog(_("SeriesPlugin renamer exception ") + str(e))


#######################################################
# Movielist menu info
def movielist_info(session, service, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			session.open(SeriesPluginInfoScreen, service)
		except Exception as e:
			splog(_("SeriesPlugin extension exception ") + str(e))


#######################################################
# Timer renaming

# Synchronous call, blocks until we have the information
def getSeasonAndEpisode(timer, name, begin, end, *args, **kwargs):
	result = None
	if config.plugins.seriesplugin.enabled.value:
		try:
			result = SeriesPluginTimer(timer, name, begin, end, True)
		except Exception as e:
			splog(_("SeriesPlugin label exception ") + str(e))
	return result

# Call asynchronous
def renameTimer(timer, name, begin, end, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			SeriesPluginTimer(timer, name, begin, end)
		except Exception as e:
			splog(_("SeriesPlugin label exception ") + str(e))


# For compatibility reasons
def modifyTimer(timer, name, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		splog("SeriesPlugin modifyTimer is deprecated - Update Your AutoTimer!")
		try:
			SeriesPluginTimer(timer, name or timer.name, timer.begin, timer.end)
		except Exception as e:
			splog(_("SeriesPlugin label exception ") + str(e))


# For compatibility reasons
def labelTimer(timer, begin=None, end=None, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		splog("SeriesPlugin labelTimer is deprecated - Update Your AutoTimer!")
		try:
			SeriesPluginTimer(timer, timer.name, timer.begin, timer.end)
		except Exception as e:
			splog(_("SeriesPlugin label exception ") + str(e))


#######################################################
# Plugin main function
def Plugins(**kwargs):
	descriptors = []
	
	#TODO icon
	descriptors.append( PluginDescriptor(
											name = NAME + " " + _("Setup"),
											description = NAME + " " + _("Setup"),
											where = PluginDescriptor.WHERE_PLUGINMENU,
											fnc = setup,
											needsRestart = False) )
	
	if config.plugins.seriesplugin.enabled.value:
		
		overwriteAutoTimer()
		
		descriptors.append( PluginDescriptor(
													#where = PluginDescriptor.WHERE_SESSIONSTART,
													where = PluginDescriptor.WHERE_AUTOSTART,
													needsRestart = False,
													fnc = start) )

		if config.plugins.seriesplugin.menu_info.value:
			descriptors.append( PluginDescriptor(
													name = SHOWINFO,
													description = SHOWINFO,
													where = PluginDescriptor.WHERE_EVENTINFO,
													needsRestart = False,
													fnc = info) )

		if config.plugins.seriesplugin.menu_extensions.value:
			descriptors.append(PluginDescriptor(
													name = SHOWINFO,
													description = SHOWINFO,
													where = PluginDescriptor.WHERE_EXTENSIONSMENU,
													fnc = sp_extension,
													needsRestart = False) )
		
		if config.plugins.seriesplugin.check_timer_list.value:
			descriptors.append(PluginDescriptor(
													name = CHECKTIMERS,
													description = CHECKTIMERS,
													where = PluginDescriptor.WHERE_EXTENSIONSMENU,
													fnc = checkTimers,
													needsRestart = False) )
		
		if config.plugins.seriesplugin.menu_movie_info.value:
			descriptors.append( PluginDescriptor(
													name = SHOWINFO,
													description = SHOWINFO,
													where = PluginDescriptor.WHERE_MOVIELIST,
													fnc = movielist_info,
													needsRestart = False) )
		
		if config.plugins.seriesplugin.menu_movie_rename.value:
			descriptors.append( PluginDescriptor(
													name = RENAMESERIES,
													description = RENAMESERIES,
													where = PluginDescriptor.WHERE_MOVIELIST,
													fnc = movielist_rename,
													needsRestart = False) )
		
		if config.plugins.seriesplugin.menu_channel.value:
			try:
				descriptors.append( PluginDescriptor(
													name = SHOWINFO,
													description = SHOWINFO,
													where = PluginDescriptor.WHERE_CHANNEL_CONTEXT_MENU,
													fnc = channel,
													needsRestart = False) )
			except:
				addSeriesPlugin(WHERE_CHANNELMENU, SHOWINFO)
		
		if config.plugins.seriesplugin.menu_epg.value:
			addSeriesPlugin(WHERE_EPGMENU, SHOWINFO)

	return descriptors


#######################################################
# Override EPGSelection enterDateTime
EPGSelection_enterDateTime = None
#EPGSelection_openOutdatedEPGSelection = None
def SPEPGSelectionInit():
	print "SeriesPlugin override EPGSelection"
	global EPGSelection_enterDateTime #, EPGSelection_openOutdatedEPGSelection
	if EPGSelection_enterDateTime is None: # and EPGSelection_openOutdatedEPGSelection is None:
		from Screens.EpgSelection import EPGSelection
		EPGSelection_enterDateTime = EPGSelection.enterDateTime
		EPGSelection.enterDateTime = enterDateTime
		#EPGSelection_openOutdatedEPGSelection = EPGSelection.openOutdatedEPGSelection
		#EPGSelection.openOutdatedEPGSelection = openOutdatedEPGSelection
		EPGSelection.SPcloseafterfinish = closeafterfinish

def SPEPGSelectionUndo():
	print "SeriesPlugin undo override EPGSelection"
	global EPGSelection_enterDateTime #, EPGSelection_openOutdatedEPGSelection
	if EPGSelection_enterDateTime: # and EPGSelection_openOutdatedEPGSelection:
		from Screens.EpgSelection import EPGSelection
		EPGSelection.enterDateTime = EPGSelection_enterDateTime
		EPGSelection_enterDateTime = None
		#EPGSelection.openOutdatedEPGSelection = EPGSelection_openOutdatedEPGSelection
		#EPGSelection_openOutdatedEPGSelection = None

def enterDateTime(self):
	from Screens.EpgSelection import EPG_TYPE_SINGLE,EPG_TYPE_MULTI,EPG_TYPE_SIMILAR
	event = self["Event"].event
	if self.type == EPG_TYPE_SINGLE:
		service = self.currentService
	elif self.type == EPG_TYPE_MULTI:	
		service = self.services
	elif self.type == EPG_TYPE_SIMILAR:
		service = self.currentService
	if service and event:
		self.session.openWithCallback(self.SPcloseafterfinish, SeriesPluginInfoScreen, service, event) 
		return
	EPGSelection_enterDateTime(self)

#def openOutdatedEPGSelection(self, reason=None):
#	if reason == 1:
#		EPGSelection_enterDateTime(self)


#######################################################
# Override ChannelContextMenu
ChannelContextMenu__init__ = None
def SPChannelContextMenuInit():
	print "[SeriesPlugin] override ChannelContextMenu.__init__"
	global ChannelContextMenu__init__
	if ChannelContextMenu__init__ is None:
		from Screens.ChannelSelection import ChannelContextMenu
		ChannelContextMenu__init__ = ChannelContextMenu.__init__
		ChannelContextMenu.__init__ = SPChannelContextMenu__init__
		ChannelContextMenu.SPchannelShowSeriesInfo = channelShowSeriesInfo
		ChannelContextMenu.SPcloseafterfinish = closeafterfinish

def SPChannelContextMenuUndo():
	print "[SeriesPlugin] override ChannelContextMenu.__init__"
	global ChannelContextMenu__init__
	if ChannelContextMenu__init__:
		from Screens.ChannelSelection import ChannelContextMenu
		ChannelContextMenu.__init__ = ChannelContextMenu__init__
		ChannelContextMenu__init__ = None

def SPChannelContextMenu__init__(self, session, csel):
	from Components.ChoiceList import ChoiceEntryComponent
	from Screens.ChannelSelection import MODE_TV
	from Tools.BoundFunction import boundFunction
	from enigma import eServiceReference
	ChannelContextMenu__init__(self, session, csel)
	current = csel.getCurrentSelection()
	current_sel_path = current.getPath()
	current_sel_flags = current.flags
	if csel.mode == MODE_TV and not (current_sel_path or current_sel_flags & (eServiceReference.isDirectory|eServiceReference.isMarker)):
		self["menu"].list.insert(0, ChoiceEntryComponent(text=(SHOWINFO, boundFunction(self.SPchannelShowSeriesInfo))))

def channelShowSeriesInfo(self):
	splog( "[SeriesPlugin] channelShowSeriesInfo ")
	if config.plugins.seriesplugin.enabled.value:
		try:
			from enigma import eServiceCenter
			service = self.csel.servicelist.getCurrent()
			info = eServiceCenter.getInstance().info(service)
			event = info.getEvent(service)
			self.session.openWithCallback(self.SPcloseafterfinish, SeriesPluginInfoScreen, service, event)
		except Exception as e:
			splog(_("SeriesPlugin info exception ") + str(e))

def closeafterfinish(self, retval=None):
	self.close()


#######################################################
# Add / Remove menu functions
def addSeriesPlugin(menu, title, fnc=None):
	# Add to menu
	if( menu == WHERE_EPGMENU ):
		SPEPGSelectionInit()
	elif( menu == WHERE_CHANNELMENU ):
		try:
			addSeriesPlugin(PluginDescriptor.WHERE_CHANNEL_CONTEXT_MENU, SHOWINFO, fnc)
		except:
			SPChannelContextMenuInit()
	else:
		from Components.PluginComponent import plugins
		if plugins:
			for p in plugins.getPlugins( where = menu ):
				if p.name == title:
					# Plugin is already in menu
					break
			else:
				# Plugin not in menu - add it
				plugin = PluginDescriptor(
																name = title,
																description = title,
																where = menu,
																needsRestart = False,
																fnc = fnc)
				if menu in plugins.plugins:
					plugins.plugins[ menu ].append(plugin)


def removeSeriesPlugin(menu, title):
	# Remove from menu
	if( menu == WHERE_EPGMENU ):
		SPEPGSelectionUndo()
	elif( menu == WHERE_CHANNELMENU ):
		try:
			removeSeriesPlugin(PluginDescriptor.WHERE_CHANNEL_CONTEXT_MENU, SHOWINFO)
		except:
			SPChannelContextMenuUndo()
	else:
		from Components.PluginComponent import plugins
		if plugins:
			for p in plugins.getPlugins( where = menu ):
				if p.name == title:
					plugins.plugins[ menu ].remove(p)
					break


#######################################################
# Overwrite AutoTimer support functions

try:
	from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
	#from Plugins.Extensions.AutoTimer.plugin import autotimer as AutoTimer
except:
	AutoTimer = None

ATmodifyTimer = None


def overwriteAutoTimer():
	try:
		global ATmodifyTimer
		if AutoTimer:
			if ATmodifyTimer is None:
				# Backup original function
				ATmodifyTimer = AutoTimer.modifyTimer
				# Overwrite function
				AutoTimer.modifyTimer = SPmodifyTimer
	except:
		splog("SeriesPlugin found old AutoTimer")


def recoverAutoTimer():
	try:
		global ATmodifyTimer
		if AutoTimer:
			if ATmodifyTimer:
				AutoTimer.modifyTimer = ATmodifyTimer
				ATmodifyTimer = None
	except:
		splog("SeriesPlugin found old AutoTimer")


#######################################################
# Customized support functions

from difflib import SequenceMatcher
from ServiceReference import ServiceReference

def SPmodifyTimer(self, timer, name, shortdesc, begin, end, serviceref, eit=None):
	# Never overwrite existing names, You will lose Your series informations
	#timer.name = name
	# Only overwrite non existing descriptions
	timer.description = timer.description or shortdesc
	timer.begin = int(begin)
	timer.end = int(end)
	timer.service_ref = ServiceReference(serviceref)
	if eit:
		timer.eit = eit
