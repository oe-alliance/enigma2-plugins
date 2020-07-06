#!/usr/bin/python
# -*- coding: utf-8 -*- 
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  The plugin is developed on the basis from a lot of single plugins (thx for the code @ all)
#  Coded by JackDaniel and cmikula (c)2012
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
from Components.Sources.StaticText import StaticText
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from .Source.AboutParser import AboutParser
from Components.GUIComponent import GUIComponent
from enigma import RT_HALIGN_LEFT, gFont, eListbox, eListboxPythonMultiContent
from Components.ScrollLabel import ScrollLabel
from .Source.Globals import SkinTools
from . import Version

class VersionList(GUIComponent):
    def __init__(self):
        GUIComponent.__init__(self)
        self.l = eListboxPythonMultiContent()
        self.l.setBuildFunc(self.buildMovieSelectionListEntry)
        self.l.setFont(0, gFont("Regular", 20))                             
        self.l.setItemHeight(30)
        self.onSelectionChanged = [ ]

    def connectSelChanged(self, fnc):
        if not fnc in self.onSelectionChanged:
            self.onSelectionChanged.append(fnc)

    def disconnectSelChanged(self, fnc):
        if fnc in self.onSelectionChanged:
            self.onSelectionChanged.remove(fnc)

    def selectionChanged(self):
        for x in self.onSelectionChanged:
            x()        

    def buildMovieSelectionListEntry(self, version):
        width = self.l.getItemSize().width()
        res = [ None ]        
        res.append((eListboxPythonMultiContent.TYPE_TEXT, 5, 2, width - 30, 23, 0, RT_HALIGN_LEFT, "%s" % version.getVersion()))
        return res

    GUI_WIDGET = eListbox
    
    def postWidgetCreate(self, instance):
        instance.setContent(self.l)
        instance.selectionChanged.get().append(self.selectionChanged)

    def preWidgetRemove(self, instance):
        instance.setContent(None)
        instance.selectionChanged.get().remove(self.selectionChanged)

    def getCurrentIndex(self):
        return self.instance.getCurrentIndex()
    
    def getSelectionIndex(self):
        return self.l.getCurrentSelectionIndex()

    def setList(self, l):
        self.l.setList(l)
    
    def getCurrent(self):
        l = self.l.getCurrentSelection()
        return l and l[0]

class AdvancedMovieSelectionAbout(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.skinName = SkinTools.appendResolution("AdvancedMovieSelectionAbout")
        self["aboutActions"] = ActionMap(["ShortcutActions", "WizardActions", "InfobarEPGActions"],
        {
            "red": self.close,
            "green": self.showchanges,
            "back": self.close,
            "ok": self.close,
        }, -1)
        v = _("Version:")
        b = _("Branch:")
        info = "%s %s.r%s, %s\n  %s %s" % (v, Version.__version__, Version.__revision__, Version.__date__, b, Version.__branch__)
        self["version"] = StaticText(info)
        self["author"] = StaticText(_("Developer:\n  JackDaniel, cmikula"))
        self["translation"] = StaticText(_("Thanks for translation to:\n") + '  nl=Bschaar', 'it=mikark')
        self["license"] = StaticText(_("This plugin may only executed on hardware which is licensed by Dream Multimedia GmbH."))
        self["thanks"] = StaticText(_("Thanks to all other for help and so many very good code."))
        self["key_red"] = StaticText(_("Close"))
        self["key_green"] = StaticText(_("Show changes"))
        self["red"] = Pixmap()
        self["green"] = Pixmap()
        self.onLayoutFinish.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(_("About Advanced Movie Selection"))

    def showchanges(self):
        self.session.openWithCallback(self.close, AboutDetails)

class AboutDetails(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.skinName = SkinTools.appendResolution("AdvancedMovieSelectionAboutDetails_")
        self["aboutActions"] = ActionMap(["ShortcutActions", "WizardActions", "InfobarEPGActions", "EPGSelectActions"],
        {
            "red": self.close,
            "back": self.close,
            "nextBouquet": self.pageUp,
            "nextBouquet": self.pageUp,
            "prevBouquet": self.pageDown,
            "prevBouquet": self.pageDown,
        }, -1)
        self["key_red"] = StaticText()
        self["red"] = Pixmap()
        self["red"].hide()
        self["bouquet+"] = Pixmap()
        self["bouquet+"].hide()
        self["bouquet-"] = Pixmap()
        self["bouquet-"].hide()
        self["version_list"] = VersionList()
        self["version_list"].hide()
        self["details"] = ScrollLabel()
        self["details"].hide()
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(_("Advanced Movie Selection - History"))
        versions = AboutParser.parseChanges()
        versionList = []
        for version in versions:
            versionList.append((version,))
            
        self["bouquet+"].show()
        self["bouquet-"].show()
        self["red"].show()
        self["key_red"].setText(_("Close"))
        self["version_list"].setList(versionList)
        self["version_list"].show()
        #if len(versionList) > 0:
        #    self["version_list"].instance.moveSelectionTo(len(versionList) - 1)
        if not self.selectionChanged in self["version_list"].onSelectionChanged:
            self["version_list"].onSelectionChanged.append(self.selectionChanged)
        self.selectionChanged()

    def selectionChanged(self):
        cur = self["version_list"].getCurrent()
        if cur is not None:
            self["details"].setText(str(cur))
            self["details"].show()

    def pageUp(self):
        self["details"].pageUp()

    def pageDown(self):
        self["details"].pageDown()
