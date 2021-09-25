#!/usr/bin/python
# -*- coding: utf-8 -*-
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  The plugin is developed on the basis from a lot of single plugins (thx for the code @ all)
#  Coded by JackDaniel @ cmikula (c)2011
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
from __future__ import print_function
from __future__ import absolute_import
from .__init__ import _
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Pixmap import Pixmap
from Components.Button import Button
from Components.config import config, getConfigListEntry
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.MultiContent import MultiContentEntryText
from Components.GUIComponent import GUIComponent
from Components.Sources.StaticText import StaticText
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT
from .Source.Remote.MessageServer import serverInstance, getIpAddress
from .Source.Remote.Client import getClients
from time import localtime, strftime
from .Source.Globals import SkinTools

staticIP = None


class ClientSetupList(GUIComponent):
    def __init__(self, ip_address):
        GUIComponent.__init__(self)
        self.l = eListboxPythonMultiContent()
        self.l.setFont(0, gFont("Regular", 22))
        self.l.setFont(1, gFont("Regular", 18))
        self.l.setItemHeight(100)
        self.l.setBuildFunc(self.buildMovieListEntry)
        self.onSelectionChanged = []
        self.staticIP = ip_address

    def connectSelChanged(self, fnc):
        if not fnc in self.onSelectionChanged:
            self.onSelectionChanged.append(fnc)

    def disconnectSelChanged(self, fnc):
        if fnc in self.onSelectionChanged:
            self.onSelectionChanged.remove(fnc)

    def selectionChanged(self):
        for x in self.onSelectionChanged:
            x()

    def buildMovieListEntry(self, client):
        res = [None]
        width = self.l.getItemSize().width()
        width_up_r = 250
        width_up_l = width - width_up_r
        width_dn_r = width / 2
        width_dn_l = width - width_dn_r
        pos_up_r = width - width_up_r
        pos_dn_r = width - width_dn_r
        if client.isRecording():
            stby_text = _("Status:") + ' ' + _("Recording")
        elif client.inStandby():
            stby_text = _("Status:") + ' ' + _("Standby")
        else:
            stby_text = _("Status:") + ' ' + _("Switched on")
        last_trash_clean_status = ""
        lastEvent = client.lastTrashEvent()
        if lastEvent == -1:
            last_trash_clean_status = (_("The %s is a client box") % client.getDeviceName())
        elif lastEvent > 0:
            t = localtime(lastEvent)
            last_trash_clean_status = _("Last remote wastebasket empty at %s") % (strftime(("%02d.%02d.%04d" % (t[2], t[1], t[0])) + ' ' + _("at") + ' ' + ("%02d:%02d" % (t[3], t[4])) + ' ' + _("Clock")))
        next_trash_clean_status = ""
        nextEvent = client.nextTrashEvent()
        if nextEvent == -1:
            trash_clean_status = (_("The %s is a client box") % client.getDeviceName())
        elif nextEvent > 0:
            t = localtime(nextEvent)
            next_trash_clean_status = _("Next remote wastebasket empty at %s") % (strftime(("%02d.%02d.%04d" % (t[2], t[1], t[0])) + ' ' + _("at") + ' ' + ("%02d:%02d" % (t[3], t[4])) + ' ' + _("Clock")))
        hostname = _("Hostname:") + ' ' + client.getDeviceName()
        ip_addr = client.getAddress()
        addr = _("IP:") + ' ' + ip_addr
        if ip_addr == self.staticIP:
            addr = addr + ' ' + _("<Local device>")
        port = _("Port:") + ' ' + str(client.getPort())
        res.append(MultiContentEntryText(pos=(5, 2), size=(width_up_l, 30), font=0, flags=RT_HALIGN_LEFT, text=hostname))
        res.append(MultiContentEntryText(pos=(pos_up_r, 3), size=(width_up_r, 22), font=1, flags=RT_HALIGN_RIGHT, text=stby_text))
        res.append(MultiContentEntryText(pos=(5, 26), size=(width_dn_l, 30), font=1, flags=RT_HALIGN_LEFT, text=addr))
        res.append(MultiContentEntryText(pos=(pos_dn_r, 28), size=(width_dn_r, 22), font=1, flags=RT_HALIGN_RIGHT, text=port))
        res.append(MultiContentEntryText(pos=(5, 50), size=(width, 30), font=1, flags=RT_HALIGN_LEFT, text=last_trash_clean_status))
        res.append(MultiContentEntryText(pos=(5, 75), size=(width, 30), font=1, flags=RT_HALIGN_LEFT, text=next_trash_clean_status))
        return res

    def moveToIndex(self, index):
        self.instance.moveSelectionTo(index)

    def getCurrentIndex(self):
        return self.instance.getCurrentIndex()

    def getCurrent(self):
        l = self.l.getCurrentSelection()
        return l and l[0]

    GUI_WIDGET = eListbox

    def postWidgetCreate(self, instance):
        instance.setContent(self.l)
        instance.selectionChanged.get().append(self.selectionChanged)

    def preWidgetRemove(self, instance):
        instance.setContent(None)
        instance.selectionChanged.get().remove(self.selectionChanged)

    def reload(self):
        self.list = []
        for client in getClients():
            self.list.append((client,))
            print(client.getAddress())
        self.l.setList(self.list)

    def remove(self, x):
        for l in self.list[:]:
            if l[0] == x:
                self.list.remove(l)
        self.l.setList(self.list)

    def __len__(self):
        return len(self.list)

    def moveTo(self, client):
        count = 0
        for x in self.list:
            if x[0] == client:
                self.instance.moveSelectionTo(count)
                return True
            count += 1
        return False


class ClientSetup(ConfigListScreen, Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.skinName = SkinTools.appendResolution("AdvancedMovieSelection_ClientSetup_")
        self.staticIP = getIpAddress('eth0')
        self.session = session
        self["key_red"] = Button(_("Close"))
        self["key_green"] = StaticText("")
        self["key_yellow"] = StaticText("")
        self["actions"] = ActionMap(["WizardActions", "MenuActions", "ShortcutActions", "EPGSelectActions"],
            {
                 "ok": self.keySave,
                 "back": self.keyCancel,
                 "red": self.keyCancel,
                 "green": self.keySave,
                 "yellow": self.keyYellow,
                 "up": self.keyUp,
                 "down": self.keyDown,
                 "nextBouquet": self.keyBouquetUp,
                 "prevBouquet": self.keyBouquetDown,
             }, -1)
        self["status"] = StaticText("")
        self["help"] = StaticText("")
        self["green_button"] = Pixmap()
        self["yellow_button"] = Pixmap()
        self["green_button"].hide()
        self["yellow_button"].hide()
        self["clienttxt"] = StaticText("")
        self["list"] = ClientSetupList(self.staticIP)
        self.list = self["list"]
        self.list.reload()
        self.configList = []
        ConfigListScreen.__init__(self, self.configList, session=self.session)
        if not self.showHelp in self["config"].onSelectionChanged:
            self["config"].onSelectionChanged.append(self.showHelp)
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(_("Advanced Movie Selection - Clientbox setup"))
        if self.staticIP:
            self.createSetup()
            self["key_green"].setText(_("Save"))
            self["key_yellow"].setText(_("Manual search"))
            self["green_button"].show()
            self["yellow_button"].show()
            self["status"].setText(_("Local IP: %s") % self.staticIP)
            if config.AdvancedMovieSelection.server_enabled.value:
                self["clienttxt"].setText(_("Available Server/Clients"))
            else:
                self["clienttxt"].setText(_("Remoteserver disabled!"))
        else:
            self["status"].setText(_("ATTENTION: DHCP in lan configuration is activ, no clientbox services available!"))

    def createSetup(self):
        self.configList = []
        self.configList.append(getConfigListEntry(_("Port address:"), config.AdvancedMovieSelection.server_port, _("Set the port address for client and server. Port address from connected clients will be automatically updated.")))
        self.configList.append(getConfigListEntry(_("Start search IP:"), config.AdvancedMovieSelection.start_search_ip, _("Only last three digits from the IP must be set.")))
        self.configList.append(getConfigListEntry(_("Stop search IP:"), config.AdvancedMovieSelection.stop_search_ip, _("Only last three digits from the IP must be set.")))
        self["config"].setList(self.configList)

    def showHelp(self):
        current = self["config"].getCurrent()
        if len(current) > 2 and current[2] is not None:
            self["help"].setText(current[2])
        else:
            self["help"].setText(_("No Helptext available!"))

    def cancelConfirm(self, result):
        if not result:
            return
        for x in self["config"].list:
            x[1].cancel()
        self.close()

    def keyCancel(self):
        if self["config"].isChanged():
            self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
        else:
            self.close()

    def keySave(self):
        if config.AdvancedMovieSelection.server_port.isChanged():
            self.setPort()
        if self.staticIP:
            ConfigListScreen.keySave(self)

    def keyYellow(self):
        if self.staticIP:
            if config.AdvancedMovieSelection.server_port.isChanged():
                self.setPort()
            self["status"].setText(_("Searching for clients, please wait ...")) #TODO: status wird nicht angezeigt ;(
            serverInstance.setSearchRange(config.AdvancedMovieSelection.start_search_ip.value, config.AdvancedMovieSelection.stop_search_ip.value)
            serverInstance.findClients()
            self.finishedState()

    def finishedState(self):
        self["status"].setText(_("Manual search finished"))
        self.list.reload()

    def setPort(self):
        config.AdvancedMovieSelection.server_port.save()
        port = config.AdvancedMovieSelection.server_port.value
        for client in getClients():
            if client.getAddress() != self.staticIP:
                client.setPort(port)
            else:
                # this only set the port of local client !don't reconnect it!
                client.port = port
        serverInstance.reconnect(port=port)

    def keyUp(self):
        self["config"].instance.moveSelection(self["config"].instance.moveUp)

    def keyDown(self):
        self["config"].instance.moveSelection(self["config"].instance.moveDown)

    def keyBouquetUp(self):
        self["list"].instance.moveSelection(self["list"].instance.pageUp)

    def keyBouquetDown(self):
        self["list"].instance.moveSelection(self["list"].instance.pageDown)
