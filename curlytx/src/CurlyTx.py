# -*- coding: utf-8 -*-
# CurlyTx main window
# Copyright (C) 2011 Christian Weiske <cweiske@cweiske.de>
# License: GPLv3 or later

from . import _

from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from twisted.web import client
from twisted.web.client import _makeGetterFactory, HTTPClientFactory
from enigma import gFont

from . import config
from Components.config import config

class CurlyTx(Screen, HelpableScreen):
    skin = """
        <screen name="CurlyTx" position="center,center" size="560,430" title="CurlyTx" >
	  <ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
	  <ePixmap position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
	  <ePixmap position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
	  <ePixmap position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
	  <widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" />
	  <widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" />
	  <widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" />
	  <widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" />
	  <widget name="text" position="5,45" size="550,380" font="Console;20" />
        </screen>"""

    currentUrl = None
    currentPage = None
    currentFontSize = 20
    httpGetterFactory = None
    showingHeaders = False

    def __init__(self, session, args = None):
        #self.skin = CurlyTx.skin
        Screen.__init__(self, session)
        HelpableScreen.__init__(self)
        #self.skinName = [ "CurlyTx", "Setup" ]

        self["text"] = ScrollLabel("foo")

        self["key_red"]    = StaticText(_("Settings"))
        self["key_green"]  = StaticText(_("Reload"))
        self["key_yellow"] = StaticText(_("Prev"))
        self["key_blue"]   = StaticText(_("Next"))


        self["actions"] = ActionMap(
            ["WizardActions", "ColorActions", "InputActions", "InfobarEPGActions"], {
                "ok":   self.close,
                "back": self.close,
                "up":   self.pageUp,
                "down": self.pageDown,

                "red":    self.showSettings,
                "green":  self.reload,
                "yellow": self.prevPage,
                "blue":   self.nextPage,

                "showEventInfo": self.showHeader
            }, -1)

        self.loadHelp()
        self.loadButtons()
        self.onLayoutFinish.append(self.afterLayout)

    def afterLayout(self):
        self.setTextFont
        self.loadUrl(config.plugins.CurlyTx.defaultPage.value)

    def loadHelp(self):
        self.helpList.append((
                self["actions"], "WizardActions",
                [("up", _("Scroll page contents up"))]))
        self.helpList.append((
                self["actions"], "WizardActions",
                [("down", _("Scroll page contents down"))]))
        self.helpList.append((
                self["actions"], "InfobarEPGActions",
                [("showEventInfo", _("Show HTTP response headers"))]))
        self.helpList.append((
                self["actions"], "ColorActions",
                [("red", _("Show program settings"))]))
        self.helpList.append((
                self["actions"], "ColorActions",
                [("green", _("Reload current page URL"))]))
        self.helpList.append((
                self["actions"], "ColorActions",
                [("yellow", _("Switch to next configured page URL"))]))
        self.helpList.append((
                self["actions"], "ColorActions",
                [("blue", _("Switch to previous configured page URL"))]))
        self.helpList.append((
                self["actions"], "WizardActions",
                [("ok", _("Close window"))]))
        self.helpList.append((
                self["actions"], "WizardActions",
                [("back", _("Close window"))]))
        self.helpList.append((
                self["actions"], "HelpActions",
                [("displayHelp", _("Show this help screen"))]))

    def loadButtons(self):
        pageCount = len(config.plugins.CurlyTx.pages)
        if pageCount == 0:
            self["key_green"].setText("")
            self["key_yellow"].setText("")
            self["key_blue"].setText("")
        elif pageCount == 1:
            self["key_green"].setText(_("Reload"))
            self["key_yellow"].setText("")
            self["key_blue"].setText("")
        else:
            self["key_green"].setText(_("Reload"))
            self["key_yellow"].setText(_("Prev"))
            self["key_blue"].setText(_("Next"))

    def pageUp(self):
        self["text"].pageUp()

    def pageDown(self):
        self["text"].pageDown()

    def prevPage(self):
        if self.currentPage == None:
            return

        pageId = self.currentPage - 1
        if pageId < 0:
            pageId = len(config.plugins.CurlyTx.pages) - 1
        self.loadUrl(pageId)

    def nextPage(self):
        if self.currentPage == None:
            return

        pageId = self.currentPage + 1
        if pageId > len(config.plugins.CurlyTx.pages) - 1:
            pageId = 0
        self.loadUrl(pageId)

    def reload(self):
        if self.currentPage == None:
            return

        self.loadUrl(self.currentPage)

    def loadUrl(self, pageId):
        if pageId == None:
            self.loadNoPage()
            return

        cfg = config.plugins.CurlyTx
        pageCount = len(cfg.pages)
        pageId = int(pageId)
        if pageId > (pageCount - 1):
            if len(cfg.pages) == 0:
                self.loadNoPage()
            else:
                self["text"].setText(_("Invalid page") + " " + pageId);
            return

        url   = cfg.pages[pageId].uri.value
        title = cfg.pages[pageId].title.value

        if pageCount > 1:
            title = "{0} [{1}/{2}]".format(title, pageId + 1, pageCount)

        self.currentPage = pageId
        self.currentUrl = url
        self.currentFontSize = cfg.pages[pageId].fontSize.value

        self.setTitle(title)
        self.setTextFont()
        self["text"].setText(_("Loading ...") + "\n" + url);

        self.getPageWebClient(url).addCallback(self.urlLoaded).addErrback(self.urlFailed, url)

    def setTextFont(self):
        if self["text"].long_text is not None:
            self["text"].long_text.setFont(gFont("Console", self.currentFontSize))

    def urlLoaded(self, html):
        self["text"].setText(html)

    def urlFailed(self, error, url):
        self["text"].setText(
            _("Error fetching URL:") + "\n " + error.getErrorMessage()
            + "\n\nURL: " + url
            )

    def loadNoPage(self):
        self["text"].setText(_("Go and add a page in the settings"));

    def showHeader(self):
        if self.showingHeaders:
            self["text"].setText(self.pageContent)
            self.pageContent    = None
            self.showingHeaders = False
        elif self.httpGetterFactory.response_headers:
            headers = _("HTTP response headers for") + "\n" + self.currentUrl + "\n\n"
            for (k, v) in self.httpGetterFactory.response_headers.items():
                headers += k + ": " + ("\n" + k + ": ").join(v) + "\n"
            self.pageContent = self["text"].getText()
            self["text"].setText(headers)
            self.showingHeaders = True

    def showSettings(self):
        from CurlyTxSettings import CurlyTxSettings
        self.session.openWithCallback(self.onSettingsChanged, CurlyTxSettings)

    def onSettingsChanged(self):
        self.loadButtons()
        if len(config.plugins.CurlyTx.pages) == 0:
            self.currentPage = None
            self.loadUrl(self.currentPage)
        elif self.currentPage == None:
            self.currentPage = 0
            self.loadUrl(self.currentPage)


    def getPageWebClient(self, url, contextFactory=None, *args, **kwargs):
        """
        Download a web page as a string.

        COPY OF twisted.web.client.getPage to store the factory

        Download a page. Return a deferred, which will callback with a
        page (as a string) or errback with a description of the error.

        See L{HTTPClientFactory} to see what extra arguments can be passed.
        """
        self.httpGetterFactory = _makeGetterFactory(
            url,
            HTTPClientFactory,
            contextFactory=contextFactory,
            *args, **kwargs)
        return self.httpGetterFactory.deferred
