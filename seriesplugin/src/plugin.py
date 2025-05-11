# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import sys
import traceback

# Localization
from . import _

from time import time

from Components.config import config

# Plugin
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

# Plugin internal
from .SeriesPluginTimer import SeriesPluginTimer
from .SeriesPluginInfoScreen import SeriesPluginInfoScreen
from .SeriesPluginRenamer import SeriesPluginRenamer
from .SeriesPluginIndependent import startIndependent, runIndependent
from .SeriesPluginConfiguration import SeriesPluginConfiguration
from .Logger import log

from .spEPGSelection import SPEPGSelectionInit, SPEPGSelectionUndo
from .spChannelContextMenu import SPChannelContextMenuInit, SPChannelContextMenuUndo


#######################################################
# Constants
NAME = "SeriesPlugin"
VERSION = "5.9.8"
DESCRIPTION = _("SeriesPlugin")
SHOWINFO = _("Show series info (SP)")
RENAMESERIES = _("Rename serie(s) (SP)")
CHECKTIMERS = _("Check timer list for series (SP)")
SUPPORT = "http://bit.ly/seriespluginihad"
DONATE = "http://bit.ly/seriespluginpaypal"
TERMS = "http://www.serienserver.de"
ABOUT = "\n  " + NAME + " " + VERSION + "\n\n" \
				+ _("  (C) 2012 by betonme @ IHAD \n\n") \
				+ _("  Terms: ") + TERMS + "\n\n" \
				+ _("  {lookups:d} successful lookups.\n") \
				+ _("  How much time have You saved?\n\n") \
				+ _("  Support: ") + SUPPORT + "\n" \
				+ _("  Feel free to donate. \n") \
				+ _("  PayPal: ") + DONATE

USER_AGENT = "Enigma2-" + NAME

try:
	from Components.SystemInfo import BoxInfo
	DEVICE = BoxInfo.getItem("model")
except:
	DEVICE = ''

REQUEST_PARAMETER = "?device=" + DEVICE + "&version=SP" + VERSION

WHERE_EPGMENU = 'WHERE_EPGMENU'
WHERE_CHANNELMENU = 'WHERE_CHANNELMENU'


def buildURL(url):
	if config.plugins.seriesplugin.proxy_url.value:
		return config.plugins.seriesplugin.proxy_url.value + REQUEST_PARAMETER + "&url=" + url
	else:
		return url


#######################################################
# Test
def test(session=None):
	# http://dm7080/autotimer
	# http://www.unixtime.de/
	try:
		#from SeriesPluginBare import bareGetEpisode 	#future=True, today=False, elapsed=False
		#bareGetEpisode("1:0:19:7C:6:85:FFFF0000:0:0:0:", "The Walking Dead", 1448740500, 1448745600, "Description", "/media/hdd/movie", True, False, False)
		#bareGetEpisode("1:0:1:2F50:F1:270F:FFFF0000:0:0:0:", "Are You the One?", 1448923500, 1448926500, "Description", "/media/hdd/movie", False, False, True)
		#bareGetEpisode("1:0:19:814D:14B:270F:FFFF0000:0:0:0:", "Bones", 1451416200, 1451416200, "Description", "/media/hdd/movie", False, True, False)
		#sp = bareGetEpisode("1:0:19:2B66:437:66:FFFF0000:0:0:0:", "Bares für Rares", 1451311500, 1451311500, "Description", "/media/hdd/movie", False, True, False)
		#sp = bareGetEpisode("1:0:19:7980:1C3:270F:FFFF0000:0:0:0:", "Offroad Survivors", 1451492100, 1451492100, "Description", "/media/hdd/movie", False, True, False)
		#from Tools.Notifications import AddPopup
		#from Screens.MessageBox import MessageBox
		#AddPopup( sp[0], MessageBox.TYPE_INFO, 0, 'SP_PopUp_ID_Test' )

		#TEST INFOSCREEN MOVIE
		#	from enigma import eServiceReference
			#service = eServiceReference(eServiceReference.idDVB, 0, "/media/hdd/movie/20151120 0139 - Pro7 HD - The 100.ts")
			#service = eServiceReference(eServiceReference.idDVB, 0, "/media/hdd/movie/20151205 1625 - TNT Serie HD (S) - The Last Ship - Staffel 1.ts")
			#service = eServiceReference(eServiceReference.idDVB, 0, "/media/hdd/movie/20151204 1825 - VIVA_COMEDY CENTRAL HD - Rules of Engagement.ts")
		#	movielist_info(session, service)

		#TEST AUTOTIMER
		#from SeriesPluginBare import bareGetEpisode
		#bareGetEpisode("1:0:1:2F50:F1:270F:FFFF0000:0:0:0:", "Are You the One", 1448751000, 1448754000, "Description", "/media/hdd/movie", False, False, True)
		#bareGetEpisode("1:0:19:8150:14B:270F:FFFF0000:0:0:0:", "Dragons Auf zu neuen Ufern TEST_TO_BE_REMOVED", 1449390300, 1449393300, "Description", "/media/hdd/movie", False, False, True)
		pass

	except Exception as e:
		log.exception(_("SeriesPlugin test exception ") + str(e))

#######################################################
# Start


def start(reason, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		# Startup
		if reason == 0:

			#TEST AUTOTIMER
			#test()
			#if kwargs.has_key("session"):
			#	session = kwargs["session"]
			#	test(session)
			#TESTEND

			# Start on demand if it is requested
			if config.plugins.seriesplugin.autotimer_independent.value:
				startIndependent()

		# Shutdown
		elif reason == 1:
			from .SeriesPlugin import resetInstance
			resetInstance()


#######################################################
# Plugin configuration
def setup(session, *args, **kwargs):
	try:
		session.open(SeriesPluginConfiguration)
	except Exception as e:
		log.exception(_("SeriesPlugin setup exception ") + str(e))


#######################################################
# Event Info
def info(session, service=None, event=None, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			session.open(SeriesPluginInfoScreen, service, event)
		except Exception as e:
			log.exception(_("SeriesPlugin info exception ") + str(e))


#######################################################
# Extensions menu
def sp_extension(session, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			if session:
				session.open(SeriesPluginInfoScreen)
		except Exception as e:
			log.exception(_("SeriesPlugin extension exception ") + str(e))


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
			log.exception(_("SeriesPlugin extension exception ") + str(e))


#######################################################
# Timer
def checkTimers(session, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		runIndependent()

# Call from timer list - not used yet


def showTimerInfo(session, timer, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		from enigma import eEPGCache
		try:
			event = timer.eit and epgcache.lookupEventId(timer.service_ref.ref, timer.eit)
			session.open(SeriesPluginInfoScreen, timer.service_ref, event)
		except Exception as e:
			log.exception(_("SeriesPlugin info exception ") + str(e))


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
			log.exception(_("SeriesPlugin renamer exception ") + str(e))


#######################################################
# Movielist menu info
def movielist_info(session, service, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			session.open(SeriesPluginInfoScreen, service)
		except Exception as e:
			log.exception(_("SeriesPlugin extension exception ") + str(e))


#######################################################
# Timer renaming

# Synchronous call, blocks until we have the information
def getSeasonEpisode4(service_ref, name, begin, end, description, path, returnData=False, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		from .SeriesPluginBare import bareGetEpisode
		try:
			return bareGetEpisode(service_ref, name, begin, end, description, path, True, False, False, returnData)
		except Exception as e:
			log.exception("SeriesPlugin getSeasonEpisode4 exception " + str(e))
			return str(e)


def showResult(*args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		from .SeriesPluginBare import bareShowResult
		bareShowResult()


# Call asynchronous
# Can also be called from a timer list - not used yet
def renameTimer(timer, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			spt = SeriesPluginTimer()
			spt.getEpisode(timer)
		except Exception as e:
			log.exception(_("SeriesPlugin label exception ") + str(e))


def renameTimers(timers, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		try:
			spt = SeriesPluginTimer()
			for timer in timers:
				spt.getEpisode(timer)
		except Exception as e:
			log.exception(_("SeriesPlugin label exception ") + str(e))


#######################################################
# For compatibility reasons
def modifyTimer(timer, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		log.debug("SeriesPlugin modifyTimer is deprecated - Update Your AutoTimer!")
		try:
			spt = SeriesPluginTimer()
			spt.getEpisode(timer)
		except Exception as e:
			log.exception(_("SeriesPlugin label exception ") + str(e))


# For compatibility reasons
def labelTimer(timer, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		log.debug("SeriesPlugin labelTimer is deprecated - Update Your AutoTimer!")
		try:
			spt = SeriesPluginTimer()
			spt.getEpisode(timer)
		except Exception as e:
			log.exception(_("SeriesPlugin label exception ") + str(e))

# For compatibility reasons


def getSeasonAndEpisode(timer, *args, **kwargs):
	result = None
	if config.plugins.seriesplugin.enabled.value:
		log.debug("SeriesPlugin getSeasonAndEpisode is deprecated - Update Your AutoTimer!")
		try:
			spt = SeriesPluginTimer()
			result = spt.getEpisode(timer, True)
		except Exception as e:
			log.exception(_("SeriesPlugin label exception ") + str(e))
	return result

# For compatibility reasons


def getSeasonEpisode(service_ref, name, begin, end, description, path, *args, **kwargs):
	if config.plugins.seriesplugin.enabled.value:
		log.debug("SeriesPlugin getSeasonEpisode is deprecated - Update Your AutoTimer!")
		from .SeriesPluginBare import bareGetEpisode
		try:
			result = bareGetEpisode(service_ref, name, begin, end, description, path)
			if result and isinstance(result, dict):
				return (result[0], result[1], result[2])
			else:
				return str(result)
		except Exception as e:
			log.exception("SeriesPlugin getSeasonEpisode4 exception " + str(e))
			return str(e)


#######################################################
# Plugin main function
def Plugins(**kwargs):
	descriptors = []

	descriptors.append(PluginDescriptor(
											name=NAME + " " + _("Setup"),
											description=NAME + " " + _("Setup"),
											where=PluginDescriptor.WHERE_PLUGINMENU,
											fnc=setup,
											icon="plugin.png",
											needsRestart=False))

	if config.plugins.seriesplugin.enabled.value:

		descriptors.append(PluginDescriptor(
													where=PluginDescriptor.WHERE_SESSIONSTART,
													needsRestart=False,
													fnc=start))

		if config.plugins.seriesplugin.menu_info.value:
			descriptors.append(PluginDescriptor(
													name=SHOWINFO,
													description=SHOWINFO,
													where=PluginDescriptor.WHERE_EVENTINFO,
													needsRestart=False,
													fnc=info))

		if config.plugins.seriesplugin.menu_extensions.value:
			descriptors.append(PluginDescriptor(
													name=SHOWINFO,
													description=SHOWINFO,
													where=PluginDescriptor.WHERE_EXTENSIONSMENU,
													fnc=sp_extension,
													needsRestart=False))

		if config.plugins.seriesplugin.check_timer_list.value:
			descriptors.append(PluginDescriptor(
													name=CHECKTIMERS,
													description=CHECKTIMERS,
													where=PluginDescriptor.WHERE_EXTENSIONSMENU,
													fnc=checkTimers,
													needsRestart=False))

		if config.plugins.seriesplugin.menu_movie_info.value:
			descriptors.append(PluginDescriptor(
													name=SHOWINFO,
													description=SHOWINFO,
													where=PluginDescriptor.WHERE_MOVIELIST,
													fnc=movielist_info,
													needsRestart=False))

		if config.plugins.seriesplugin.menu_movie_rename.value:
			descriptors.append(PluginDescriptor(
													name=RENAMESERIES,
													description=RENAMESERIES,
													where=PluginDescriptor.WHERE_MOVIELIST,
													fnc=movielist_rename,
													needsRestart=False))

		if config.plugins.seriesplugin.menu_channel.value:
			try:
				descriptors.append(PluginDescriptor(
													name=SHOWINFO,
													description=SHOWINFO,
													where=PluginDescriptor.WHERE_CHANNEL_CONTEXT_MENU,
													fnc=channel,
													needsRestart=False))
			except:
				addSeriesPlugin(WHERE_CHANNELMENU, SHOWINFO)

		if config.plugins.seriesplugin.menu_epg.value:
			addSeriesPlugin(WHERE_EPGMENU, SHOWINFO)

	return descriptors

#######################################################
# Add / Remove menu functions


def addSeriesPlugin(menu, title, fnc=None):
	# Add to menu
	if (menu == WHERE_EPGMENU):
		SPEPGSelectionInit()
	elif (menu == WHERE_CHANNELMENU):
		try:
			addSeriesPlugin(PluginDescriptor.WHERE_CHANNEL_CONTEXT_MENU, SHOWINFO, fnc)
		except:
			SPChannelContextMenuInit()
	else:
		from Components.PluginComponent import plugins
		if plugins:
			for p in plugins.getPlugins(where=menu):
				if p.name == title:
					# Plugin is already in menu
					break
			else:
				# Plugin not in menu - add it
				plugin = PluginDescriptor(
																name=title,
																description=title,
																where=menu,
																icon="plugin.png",
																needsRestart=False,
																fnc=fnc)
				if menu in plugins.plugins:
					plugins.plugins[menu].append(plugin)


def removeSeriesPlugin(menu, title):
	# Remove from menu
	if (menu == WHERE_EPGMENU):
		SPEPGSelectionUndo()
	elif (menu == WHERE_CHANNELMENU):
		try:
			removeSeriesPlugin(PluginDescriptor.WHERE_CHANNEL_CONTEXT_MENU, SHOWINFO)
		except:
			SPChannelContextMenuUndo()
	else:
		from Components.PluginComponent import plugins
		if plugins:
			for p in plugins.getPlugins(where=menu):
				if p.name == title:
					plugins.plugins[menu].remove(p)
					break
