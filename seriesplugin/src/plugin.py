# -*- coding: utf-8 -*-
import os, sys, traceback

# Localization
from . import _

from time import time

# GUI (Screens)
from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup

from Components.config import config

# Plugin
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

# Plugin internal
from SeriesPluginTimer import SeriesPluginTimer
from SeriesPluginInfoScreen import SeriesPluginInfoScreen
from SeriesPluginRenamer import SeriesPluginRenamer
from SeriesPluginIndependent import startIndependent, runIndependent
from SeriesPluginConfiguration import SeriesPluginConfiguration
from Logger import logDebug, logInfo


#######################################################
# Constants
NAME = "SeriesPlugin"
VERSION = "4.1.5"
DESCRIPTION = _("SeriesPlugin")
SHOWINFO = _("Show series info (SP)")
RENAMESERIES = _("Rename serie(s) (SP)")
CHECKTIMERS = _("Check timer list for series (SP)")
SUPPORT = "http://bit.ly/seriespluginihad"
DONATE = "http://bit.ly/seriespluginpaypal"
TERMS = "TBD"
ABOUT = "\n  " + NAME + " " + VERSION + "\n\n" \
				+ _("  (C) 2012 by betonme @ IHAD \n\n") \
				+ _("  Terms: ") + TERMS + "\n\n" \
				+ _("  {lookups:d} successful lookups.\n") \
				+ _("  How much time have You saved?\n\n") \
				+ _("  Support: ") + SUPPORT + "\n" \
				+ _("  Feel free to donate. \n") \
				+ _("  PayPal: ") + DONATE

PROXY = "http://serienrecorder.lima-city.de/proxy.php"
USER_AGENT = "Enigma2-"+NAME

try:
	from Tools.HardwareInfo import HardwareInfo
	DEVICE = HardwareInfo().get_device_name().strip()
except:
	DEVICE = ''

REQUEST_PARAMETER = "?device=" + DEVICE + "&version=SP" + VERSION

WHERE_EPGMENU     = 'WHERE_EPGMENU'
WHERE_CHANNELMENU = 'WHERE_CHANNELMENU'


def buildURL(url):
	return PROXY + REQUEST_PARAMETER + "&url=" + url


#######################################################
# Test
def test(**kwargs):
	# http://dm7080/autotimer
	# http://www.unixtime.de/
	try:
		from SeriesPluginBare import bareGetSeasonEpisode 	#future=True, today=False, elapsed=False
		#bareGetSeasonEpisode("1:0:19:7C:6:85:FFFF0000:0:0:0:", "The Walking Dead", 1448740500, 1448745600, "Description", "/media/hdd/movie", True, False, False)
		bareGetSeasonEpisode("1:0:1:2F50:F1:270F:FFFF0000:0:0:0:", "Are You the One?", 1448923500, 1448926500, "Description", "/media/hdd/movie", False, False, True)
		
		#TEST INFOSCREEN MOVIE
		#if kwargs.has_key("session"):
		#	from enigma import eServiceReference
		#	session = kwargs["session"]
			#service = eServiceReference(eServiceReference.idDVB, 0, "/media/hdd/movie/20151120 0139 - Pro7 HD - The 100.ts")
			#service = eServiceReference(eServiceReference.idDVB, 0, "/media/hdd/movie/20151205 1625 - TNT Serie HD (S) - The Last Ship - Staffel 1.ts")
			#service = eServiceReference(eServiceReference.idDVB, 0, "/media/hdd/movie/20151204 1825 - VIVA_COMEDY CENTRAL HD - Rules of Engagement.ts")
		#	movielist_info(session, service)
		
		#TEST AUTOTIMER
		#from SeriesPluginBare import bareGetSeasonEpisode
		#bareGetSeasonEpisode("1:0:1:2F50:F1:270F:FFFF0000:0:0:0:", "Are You the One", 1448751000, 1448754000, "Description", "/media/hdd/movie", False, False, True)
		#bareGetSeasonEpisode("1:0:19:8150:14B:270F:FFFF0000:0:0:0:", "Dragons Auf zu neuen Ufern TEST_TO_BE_REMOVED", 1449390300, 1449393300, "Description", "/media/hdd/movie", False, False, True)
		
	except Exception as e:
		logDebug(_("SeriesPlugin test exception ") + str(e))
	
#######################################################
# Start
def start(reason, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		# Startup
		if reason == 0:
			
			#TEST AUTOTIMER
			#test(kwargs)
			#TESTEND
			
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
		logDebug(_("SeriesPlugin setup exception ") + str(e))


#######################################################
# Event Info
def info(session, service=None, event=None, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			session.open(SeriesPluginInfoScreen, service, event)
		except Exception as e:
			logDebug(_("SeriesPlugin info exception ") + str(e))


#######################################################
# Extensions menu
def sp_extension(session, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			if session:
				session.open(SeriesPluginInfoScreen)
		except Exception as e:
			logDebug(_("SeriesPlugin extension exception ") + str(e))


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
			logDebug(_("SeriesPlugin extension exception ") + str(e))


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
			logDebug(_("SeriesPlugin renamer exception ") + str(e))


#######################################################
# Movielist menu info
def movielist_info(session, service, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			session.open(SeriesPluginInfoScreen, service)
		except Exception as e:
			logDebug(_("SeriesPlugin extension exception ") + str(e))


#######################################################
# Timer renaming

# Synchronous call, blocks until we have the information
def getSeasonEpisode4(service_ref, name, begin, end, description, path, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		from SeriesPluginBare import bareGetSeasonEpisode
		try:
			return bareGetSeasonEpisode(service_ref, name, begin, end, description, path, True, False, False)
		except Exception as e:
			logDebug( "SeriesPlugin getSeasonEpisode4 exception " + str(e))
			return str(e)

def showResult(*args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		from SeriesPluginBare import bareShowResult
		bareShowResult()


# Call asynchronous
def renameTimer(timer, name, begin, end, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			SeriesPluginTimer(timer, name, begin, end)
		except Exception as e:
			logDebug(_("SeriesPlugin label exception ") + str(e))


# For compatibility reasons
def modifyTimer(timer, name, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		logDebug("SeriesPlugin modifyTimer is deprecated - Update Your AutoTimer!")
		try:
			SeriesPluginTimer(timer, name or timer.name, timer.begin, timer.end)
		except Exception as e:
			logDebug(_("SeriesPlugin label exception ") + str(e))


# For compatibility reasons
def labelTimer(timer, begin=None, end=None, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		logDebug("SeriesPlugin labelTimer is deprecated - Update Your AutoTimer!")
		try:
			SeriesPluginTimer(timer, timer.name, timer.begin, timer.end)
		except Exception as e:
			logDebug(_("SeriesPlugin label exception ") + str(e))

def getSeasonAndEpisode(timer, name, begin, end, *args, **kwargs):
	result = None
	if config.plugins.seriesplugin.enabled.value:
		logDebug("SeriesPlugin getSeasonEpisode is deprecated - Update Your AutoTimer!")
		try:
			spt = SeriesPluginTimer(timer, name, begin, end, True)
			result = spt.getSeasonAndEpisode(timer, name, begin, end, True, False, False)
		except Exception as e:
			logDebug(_("SeriesPlugin label exception ") + str(e))
	return result

def getSeasonEpisode(service_ref, name, begin, end, description, path, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		logDebug("SeriesPlugin getSeasonEpisode is deprecated - Update Your AutoTimer!")
		from SeriesPluginBare import bareGetSeasonEpisode
		try:
			result = bareGetSeasonEpisode(service_ref, name, begin, end, description, path)
			if result and len(result) == 4:
				return (result[0],result[1],result[2])
			else:
				return str(result)
		except Exception as e:
			logDebug( "SeriesPlugin getSeasonEpisode4 exception " + str(e))
			return str(e)


#######################################################
# Plugin main function
def Plugins(**kwargs):
	descriptors = []
	
	descriptors.append( PluginDescriptor(
											name = NAME + " " + _("Setup"),
											description = NAME + " " + _("Setup"),
											where = PluginDescriptor.WHERE_PLUGINMENU,
											fnc = setup,
											needsRestart = False) )
	
	if config.plugins.seriesplugin.enabled.value:
		
		overwriteAutoTimer()
		
		descriptors.append( PluginDescriptor(
													where = PluginDescriptor.WHERE_SESSIONSTART,
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
	print "[SeriesPlugin] override EPGSelection"
	global EPGSelection_enterDateTime #, EPGSelection_openOutdatedEPGSelection
	if EPGSelection_enterDateTime is None: # and EPGSelection_openOutdatedEPGSelection is None:
		from Screens.EpgSelection import EPGSelection
		EPGSelection_enterDateTime = EPGSelection.enterDateTime
		EPGSelection.enterDateTime = enterDateTime
		#EPGSelection_openOutdatedEPGSelection = EPGSelection.openOutdatedEPGSelection
		#EPGSelection.openOutdatedEPGSelection = openOutdatedEPGSelection
		EPGSelection.SPcloseafterfinish = closeafterfinish

def SPEPGSelectionUndo():
	print "[SeriesPlugin] undo override EPGSelection"
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
	logDebug( "[SeriesPlugin] channelShowSeriesInfo ")
	if config.plugins.seriesplugin.enabled.value:
		try:
			from enigma import eServiceCenter
			service = self.csel.servicelist.getCurrent()
			info = eServiceCenter.getInstance().info(service)
			event = info.getEvent(service)
			self.session.openWithCallback(self.SPcloseafterfinish, SeriesPluginInfoScreen, service, event)
		except Exception as e:
			logDebug(_("SeriesPlugin info exception ") + str(e))

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
		logDebug("SeriesPlugin found old AutoTimer")


def recoverAutoTimer():
	try:
		global ATmodifyTimer
		if AutoTimer:
			if ATmodifyTimer:
				AutoTimer.modifyTimer = ATmodifyTimer
				ATmodifyTimer = None
	except:
		logDebug("SeriesPlugin found old AutoTimer")


#######################################################
# Customized support functions

from difflib import SequenceMatcher
from ServiceReference import ServiceReference

def SPmodifyTimer(self, timer, name, shortdesc, begin, end, serviceref, eit=None):
	# Never overwrite existing names, You will lose Your series informations
	#timer.name = name
	# Only overwrite non existing descriptions
	#timer.description = timer.description or shortdesc
	timer.begin = int(begin)
	timer.end = int(end)
	timer.service_ref = ServiceReference(serviceref)
	if eit:
		timer.eit = eit
