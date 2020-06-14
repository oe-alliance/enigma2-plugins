# -*- coding: utf-8 -*-
# CurlyTx configuration window
# Copyright (C) 2011 Christian Weiske <cweiske@cweiske.de>
# License: GPLv3 or later

from . import _

from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox

from . import config
from config import createPage, loadDefaultPageOptions
from Components.config import config, getConfigListEntry, ConfigSelection
from Components.ConfigList import ConfigList, ConfigListScreen

class CurlyTxSettings(ConfigListScreen, HelpableScreen, Screen):
    skin = """
	<screen name="Setup" position="center,center" size="560,430" title="Settings">
	  <ePixmap pixmap="skin_default/buttons/red.png"    position="0,0"   size="140,40" transparent="1" alphatest="on" />
	  <ePixmap pixmap="skin_default/buttons/green.png"  position="140,0" size="140,40" transparent="1" alphatest="on" />
	  <ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
	  <ePixmap pixmap="skin_default/buttons/blue.png"   position="420,0" size="140,40" transparent="1" alphatest="on" />
	  <widget source="key_red"    render="Label" position="0,0"   zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
	  <widget source="key_green"  render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
	  <widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#a08500" transparent="1" />
	  <widget source="key_blue"   render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#18188b" transparent="1" />
	  <widget name="config" position="5,50" size="550,325" scrollbarMode="showOnDemand" />
	</screen>"""

    def __init__(self, session):
        self.skin = CurlyTxSettings.skin
        Screen.__init__(self, session)
        HelpableScreen.__init__(self)
        #self.skinName = [ "CurlyTxSettings", "Setup" ]
        self.setup_title = _("Settings")

        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "cancel": self.keyCancel,
                "save": self.keySave,
                "ok": self.editPage,
                "yellow": self.newPage,
                "blue": self.deletePage
            }, -2)

        self["key_red"]    = StaticText(_("Cancel"))
        self["key_green"]  = StaticText(_("OK"))
        self["key_yellow"] = StaticText(_("New"))
        self["key_blue"]   = StaticText(_("Delete"))

        ConfigListScreen.__init__(self, self.getConfigList(), session = self.session)

        self.loadHelp()

    def getConfigList(self):
        #reload titles
        loadDefaultPageOptions()
        cfg = config.plugins.CurlyTx

        list = [
            getConfigListEntry(_("Page:") + " " + x.title.value, x.uri)
                for x in cfg.pages
            ]
        if len(cfg.pages):
            list.append(getConfigListEntry(_("Default page"), cfg.defaultPage))
        list.append(getConfigListEntry(_("Show in main menu"), cfg.menuMain))
        list.append(getConfigListEntry(_("Show in extensions menu"), cfg.menuExtensions))
        list.append(getConfigListEntry(_("Menu title"), cfg.menuTitle))
        list.append(getConfigListEntry(_("Page feed URL"), cfg.feedUrl))
        return list

    def loadHelp(self):
        self.helpList.append((
                self["actions"], "SetupActions",
                [("cancel", _("Dismiss all setting changes"))]))
        self.helpList.append((
                self["actions"], "SetupActions",
                [("save", _("Save settings and close screen"))]))
        self.helpList.append((
                self["actions"], "SetupActions",
                [("ok", _("Edit selected page"))]))
        self.helpList.append((
                self["actions"], "SetupActions",
                [("ok", _("Load pages from feed"))]))
        self.helpList.append((
                self["actions"], "ColorActions",
                [("yellow", _("Add new page"))]))
        self.helpList.append((
                self["actions"], "ColorActions",
                [("blue", _("Delete selected page"))]))

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)

    def keyRight(self):
        ConfigListScreen.keyRight(self)

    def deletePage(self):
        pageCount = len(config.plugins.CurlyTx.pages)
        if pageCount == 0 or self["config"].getCurrentIndex() >= pageCount:
            return

        from Screens.MessageBox import MessageBox
        self.session.openWithCallback(
            self.deletePageConfirm,
            MessageBox,
            _("Really delete this page?\nIt cannot be recovered!")
            )

    def deletePageConfirm(self, result):
        if not result:
            return

        id = self["config"].getCurrentIndex()
        del config.plugins.CurlyTx.pages[id]

        config.plugins.CurlyTx.pages.save()

        self["config"].setList(self.getConfigList())

    def newPage(self):
        from CurlyTxSettings import CurlyTxSettings
        self.session.openWithCallback(self.pageEdited, CurlyTxPageEdit, createPage(), True)

    def editPage(self):
        id = self["config"].getCurrentIndex()
        if id < len(config.plugins.CurlyTx.pages):
            self.session.openWithCallback(
                self.pageEdited, CurlyTxPageEdit,
                config.plugins.CurlyTx.pages[id], False
                )
        elif config.plugins.CurlyTx.feedUrl.value:
            from AtomFeed import AtomFeed
            AtomFeed(
                config.plugins.CurlyTx.feedUrl.value,
                self.feedPagesReceived, self.feedPagesFail
                )
        else:
            self.session.open(
                MessageBox, _("No page feed URL defined"), MessageBox.TYPE_ERROR
                )

    def pageEdited(self, page, new):
        if not page:
            return

        if new:
            config.plugins.CurlyTx.pages.append(page)

        self["config"].setList(self.getConfigList())

    def feedPagesReceived(self, pages):
        if len(pages) == 0:
            return

        del config.plugins.CurlyTx.pages[:]

        for pageData in pages:
            page = createPage()
            config.plugins.CurlyTx.pages.append(page)
            page.title.setValue(pageData["title"])
            page.uri.setValue(pageData["url"])

        self["config"].setList(self.getConfigList())

    def feedPagesFail(self, failure):
        """ Downloading the page url feed failed somehow """
        self.session.open(
            MessageBox,
            _("Error loading page feed:") + "\n\n" + str(failure.getErrorMessage()),
            MessageBox.TYPE_ERROR
            )

    def keySave(self):
        for i in list(range(0, len(config.plugins.CurlyTx.pages))):
            config.plugins.CurlyTx.pages[i].save()

        config.plugins.CurlyTx.pages.save()
        ConfigListScreen.keySave(self)

    def cancelConfirm(self, result):
        """Overwriting ConfigListScreen.cancelConfirm to call cancelAll method"""
        if not result:
            return

        self.cancelAll()
        self.close()

    def cancelAll(self):
        for x in self["config"].list:
            x[1].cancel()

        #restore old page configuration
        cfg = config.plugins.CurlyTx
        del cfg.pages[:]
        for i in cfg.pages.stored_values:
            cfg.pages.append(createPage())



class CurlyTxPageEdit(Screen, ConfigListScreen):
    def __init__(self, session, page, new = False):
        Screen.__init__(self, session)
        self.skinName = [ "CurlyTxPageEdit", "Setup" ]

        self["key_red"]   = StaticText(_("Cancel"))
        self["key_green"] = StaticText(_("OK"))

        self["setupActions"] = ActionMap(["SetupActions"],
            {
                "save": self.save,
                "cancel": self.keyCancel
	    }, -1)

        self.page = page
        self.new = new
        list = [
            getConfigListEntry(_("Page URL"), page.uri),
            getConfigListEntry(_("Title"), page.title),
            getConfigListEntry(_("Font size"), page.fontSize),
            ]
        ConfigListScreen.__init__(self, list, session = self.session)

    def save(self):
        self.close(self.page, self.new)

    def keyCancel(self):
        self.close(None, self.new)
