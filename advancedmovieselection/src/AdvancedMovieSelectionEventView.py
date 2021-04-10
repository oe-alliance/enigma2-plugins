#!/usr/bin/python
# -*- coding: utf-8 -*- 
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  The plugin is developed on the basis from a lot of single plugins (thx for the code @ all)
#  Coded by JackDaniel & cmikula (c)2011
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
from __future__ import absolute_import
from .__init__ import _
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.config import config
from .Source.ServiceProvider import ServiceCenter, ServiceEvent
from Components.ScrollLabel import ScrollLabel
from .MoviePreview import MoviePreview
from .Source.Globals import SkinTools, pluginPresent
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
import os


class EventViewBase:    
    def __init__(self, event, ref, callback=None, similarEPGCB=None):
        self.similarEPGCB = similarEPGCB
        self.cbFunc = callback
        self.currentService = ref
        self.event = event
        self["key_red"] = StaticText("")
        self["red_button"] = Pixmap()
        self["key_green"] = StaticText("")
        self["green_button"] = Pixmap()
        self["key_yellow"] = StaticText("")
        self["yellow_button"] = Pixmap()
        self["key_blue"] = StaticText("")
        self["blue_button"] = Pixmap()        
        self["Location"] = Label()
        self["epg_description"] = ScrollLabel()
        self["Service"] = ServiceEvent()
        self["actions"] = ActionMap(["OkCancelActions", "EventViewActions", "ColorActions"],
            {
                "cancel": self.close,
                "ok": self.close,
                "red": self.red_button,
                "green": self.green_button,
                "yellow": self.yellow_button,
                "blue": self.blue_button,
                "prevEvent": self.prevEvent,
                "nextEvent": self.nextEvent,
                "pageUp": self.pageUp,
                "pageDown": self.pageDown
            })
        self.onShown.append(self.onCreate)

    def onCreate(self):
        self["key_red"].setText(_("TheTVDB search"))
        self["key_green"].setText(_("TMDb search"))
        if pluginPresent.IMDb:
            self["key_yellow"].setText(_("IMDB search"))
        else:
            self["yellow_button"].hide()
            self["key_yellow"].setText("")
        if pluginPresent.OFDb:
            self["key_blue"].setText(_("OFDb search"))
        else:
            self["blue_button"].hide()
            self["key_blue"].setText("")
        self.setEvent(self.event)

    def prevEvent(self):
        if self.cbFunc is not None:
            self.cbFunc(self.setEvent, self.setService, -1)

    def nextEvent(self):
        if self.cbFunc is not None:
            self.cbFunc(self.setEvent, self.setService, +1)

    def setService(self, service):
        self.currentService = service
        return
        if self.isRecording:
            self["channel"].setText(_("Recording"))
        else:
            name = self.currentService.getServiceName()
            if name is not None:
                self["channel"].setText(name)
            else:
                self["channel"].setText(_("Unknown service"))

    def setEvent(self, event):
        self.event = event
        if event is None:
            return
        description = event.getExtendedDescription()
        self["epg_description"].setText(description)

        title = self.getEventName()
        self.setTitle(_("Infos for: %s") % title)
        current_path = os.path.dirname(self.currentService.getPath()) + '/'
        self["Location"].setText(_("Movie location: %s") % (current_path))
        serviceref = self.currentService
        self["Service"].newService(serviceref)
        self.loadPreview(serviceref)

    def pageUp(self):
        self["epg_description"].pageUp()

    def pageDown(self):
        self["epg_description"].pageDown()

    def getEventName(self):
        ref = self.currentService
        info = ServiceCenter.getInstance().info(ref)
        return info and info.getName(ref)

    def red_button(self):
        name = self.getEventName()
        if name:
            from SearchTVDb import TheTVDBMain
            self.session.open(TheTVDBMain, self.currentService)
        
    def green_button(self):
        name = self.getEventName()
        if name:
            from SearchTMDb import TMDbMain
            self.session.open(TMDbMain, name, self.currentService) 
        
    def yellow_button(self):
        name = self.getEventName()
        if pluginPresent.IMDb and name:
            from Plugins.Extensions.IMDb.plugin import IMDB
            self.session.open(IMDB, name)
        
    def blue_button(self):
        name = self.getEventName()
        if pluginPresent.OFDb and name:
            from Plugins.Extensions.OFDb.plugin import OFDB
            self.session.open(OFDB, name)


class EventViewSimple(Screen, EventViewBase, MoviePreview):
    def __init__(self, session, event, ref, callback=None, similarEPGCB=None):
        Screen.__init__(self, session)
        self.skinName = SkinTools.appendResolution("AdvancedMovieSelectionEventView")
        EventViewBase.__init__(self, event, ref, callback, similarEPGCB)
        MoviePreview.__init__(self, session)
