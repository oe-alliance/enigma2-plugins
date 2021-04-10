#!/usr/bin/python
# -*- coding: utf-8 -*- 
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  The plugin is developed on the basis from a lot of single plugins (thx for the code @ all)
#  Coded by cmikula & JackDaniel (c)2012
#  Support: www.i-have-a-dreambox.com
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
from __init__ import _
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import InfoBar
from Components.config import config
from AdvancedMovieSelectionSetup import AdvancedMovieSelectionSetup
from TagEditor import TagEditor
from Source.Config import initializeConfig

initializeConfig()


def sessionstart(reason, **kwargs):
    if reason == 0:
        session = kwargs["session"]
        if not config.AdvancedMovieSelection.ml_disable.value:
            try:
                from MoviePlayer import showMovies
                value = config.AdvancedMovieSelection.movie_launch.value
                if value == "showMovies":
                    InfoBar.showMovies = showMovies
                elif value == "showTv":
                    InfoBar.showTv = showMovies
                elif value == "showRadio":
                    InfoBar.showRadio = showMovies
                elif value == "timeshiftStart":
                    InfoBar.startTimeshift = showMovies
                from Wastebasket import createWasteTimer
                createWasteTimer(session)
                from Source.Remote.MessageServer import serverInstance
                if config.AdvancedMovieSelection.server_enabled.value:
                    serverInstance.setPort(config.AdvancedMovieSelection.server_port.value)
                    serverInstance.start()
                    serverInstance.setSearchRange(config.AdvancedMovieSelection.start_search_ip.value, config.AdvancedMovieSelection.stop_search_ip.value)
                    serverInstance.startScanForClients()
                
                from Source.EpgListExtension import epgListExtension
                epgListExtension.setEnabled(config.AdvancedMovieSelection.epg_extension.value)
                
                from Source.MovieScanner import movieScanner
                movieScanner.setEnabled(True)
            except:
                print '-' * 50
                import traceback
                import sys
                traceback.print_exc(file=sys.stdout)
                print '-' * 50


def pluginOpen(session, **kwargs):
    from MoviePlayer import initPlayerChoice
    initPlayerChoice(session)
    from MovieSelection import MovieSelection
    from MoviePlayer import playerChoice
    session.openWithCallback(playerChoice.playService, MovieSelection)


def openProgress(session, **kwargs):
    from MoveCopy import MoveCopyProgress
    session.open(MoveCopyProgress)


def pluginMenu(session, **kwargs):
    session.open(AdvancedMovieSelectionSetup)


def Setup(menuid, **kwargs):
    # black_64: move AMS setup to: Menu > Settings > System
    #if menuid == "setup":
    if menuid == "system":
        return [(_("Setup Advanced Movie Selection"), pluginMenu, "SetupAdvancedMovieSelection", None)]
    return []


def tmdbInfo(session, eventName="", **kwargs):
    try:
        s = session.nav.getCurrentService()
        info = s.info()
        event = info.getEvent(0)
        if event:
            eventName = event.getEventName()
        if eventName:
            from SearchTMDb import TMDbMain
            session.open(TMDbMain, eventName)
    except Exception, e:
        print e
        

def tvdbInfo(session, eventName="", **kwargs):
    try:
        s = session.nav.getCurrentService()
        info = s.info()
        event = info.getEvent(0)
        shortdescr = ""
        if event:
            eventName = event.getEventName()
            shortdescr = event.getShortDescription()
        if eventName:
            from SearchTVDb import TheTVDBMain
            session.open(TheTVDBMain, None, eventName, shortdescr) 
    except Exception, e:
        print e


def Plugins(**kwargs):
    try:
        if config.AdvancedMovieSelection.debug.value:
            config.AdvancedMovieSelection.debug.value = False
            config.AdvancedMovieSelection.debug.save() 
        if not config.AdvancedMovieSelection.ml_disable.value:
            from Screens.MovieSelection import setPreferredTagEditor
            setPreferredTagEditor(TagEditor)
        if not config.AdvancedMovieSelection.ml_disable.value and config.AdvancedMovieSelection.useseekbar.value:
            from Seekbar import Seekbar
    except Exception, e:
        print e
    
    descriptors = []
    if not config.AdvancedMovieSelection.ml_disable.value:
        descriptors.append(PluginDescriptor(name=_("Advanced Movie Selection"), where=PluginDescriptor.WHERE_SESSIONSTART, description=_("Alternate Movie Selection"), fnc=sessionstart, needsRestart=True))
        descriptors.append(PluginDescriptor(name=_("Advanced Movie Selection"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, description=_("Alternate Movie Selection"), fnc=pluginOpen))
        descriptors.append(PluginDescriptor(name=_("Move Copy Progress"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, description=_("Show progress of move or copy job"), fnc=openProgress))
    descriptors.append(PluginDescriptor(name=_("Setup Advanced Movie Selection"), where=PluginDescriptor.WHERE_PLUGINMENU, description=_("Alternate Movie Selection"), fnc=pluginMenu, needsRestart=True))
    descriptors.append(PluginDescriptor(where=PluginDescriptor.WHERE_MENU, description=_("Alternate Movie Selection"), fnc=Setup, needsRestart=True))
    
    # descriptors.append(PluginDescriptor(name=_("TMDb Info"), where=PluginDescriptor.WHERE_EVENTINFO, description=_("TMDb Info"), fnc=tmdbInfo))
    # descriptors.append(PluginDescriptor(name=_("TVDb Info"), where=PluginDescriptor.WHERE_EVENTINFO, description=_("TVDb Info"), fnc=tvdbInfo))
    return descriptors
