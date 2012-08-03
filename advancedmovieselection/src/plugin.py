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
from Config import initializeConfig

initializeConfig()

def updateLocale():
    # set locale for tmdb search
    import tmdb, tvdb
    from AboutParser import AboutParser
    from Components.Language import language
    ln = language.lang[language.activeLanguage][1]
    tmdb.setLocale(ln)
    tvdb.setLocale(ln)
    AboutParser.setLocale(ln)

def autostart(reason, **kwargs):
    if reason == 0:
        session = kwargs["session"]
        if not config.AdvancedMovieSelection.ml_disable.value:
            try:
                from MoviePlayer import showMovies, movieSelected
                InfoBar.movieSelected = movieSelected
                value = config.AdvancedMovieSelection.movie_launch.value
                if value == "showMovies": InfoBar.showMovies = showMovies
                elif value == "showTv": InfoBar.showTv = showMovies
                elif value == "showRadio": InfoBar.showRadio = showMovies
                elif value == "timeshiftStart": InfoBar.startTimeshift = showMovies
                from Wastebasket import waste_timer, WastebasketTimer
                waste_timer = WastebasketTimer(session)
                value = int(config.AdvancedMovieSelection.auto_empty_wastebasket.value)
                if value != -1:
                    print "[AdvancedMovieSelection] Auto empty from wastebasket enabled..."
                else:
                    waste_timer.stopTimer()
                    print "[AdvancedMovieSelection] Auto empty from wastebasket disabled..."
                from MessageServer import serverInstance
                if config.AdvancedMovieSelection.server_enabled.value:
                    serverInstance.setPort(config.AdvancedMovieSelection.server_port.value)
                    serverInstance.start()
                    serverInstance.setSearchRange(config.AdvancedMovieSelection.start_search_ip.value, config.AdvancedMovieSelection.stop_search_ip.value)
                    serverInstance.startScanForClients()
                
                from Components.Language import language
                language.addCallback(updateLocale)
                updateLocale()
                
                from EpgListExtension import epgListExtension
                epgListExtension.enabled(config.AdvancedMovieSelection.epg_extension.value)
            except:
                pass

def pluginOpen(session, **kwargs):
    session.open(AdvancedMovieSelectionSetup)

def Setup(menuid, **kwargs):
    if menuid == "system":
        return [(_("Setup Advanced Movie Selection"), pluginOpen, "SetupAdvancedMovieSelection", None)]
    return []

def nostart(reason, **kwargs):
    print"[Advanced Movie Selection] -----> Disabled"
    pass

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
    
    if not config.AdvancedMovieSelection.ml_disable.value:
        descriptors = [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=autostart, needsRestart=True)]
    else:
        descriptors = [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=nostart, needsRestart=True)]
    descriptors.append(PluginDescriptor(where=PluginDescriptor.WHERE_MENU, description=_("Alternate Movie Selection"), fnc=Setup, needsRestart=True))
    return descriptors
