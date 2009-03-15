# -*- coding: utf-8 -*-
# for localized messages
from __init__ import _
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Network import iNetwork
from Components.Sources.List import List
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
from AutoMount import iAutoMount, AutoMount
from MountEdit import AutoMountEdit

class AutoMountView(Screen):
        skin = """
                <screen name="AutoMountView" position="90,140" size="560,350" title="MountView">
                        <widget name="legend1" position="0,0" zPosition="1" size="130,40" font="Regular;18" halign="center" valign="center" />
                        <widget name="legend2" position="130,0" zPosition="1" size="310,40" font="Regular;18" halign="center" valign="center" />
                        <widget name="legend3" position="410,0" zPosition="1" size="100,40" font="Regular;18" halign="center" valign="center" />
                        <ePixmap pixmap="skin_default/div-h.png" position="0,40" zPosition="2" size="560,2" />
                        <widget source="config" render="Listbox" position="5,50" size="555,200" scrollbarMode="showOnDemand">
                                <convert type="TemplatedMultiContent">
                                        {"template": [
                                                        MultiContentEntryPixmapAlphaTest(pos = (15, 1), size = (48, 48), png = 0), # index 0 is the isMounted pixmap
                                                        MultiContentEntryText(pos = (100, 3), size = (200, 25), font=0, flags = RT_HALIGN_LEFT, text = 1), # index 1 is the sharename
                                                        MultiContentEntryText(pos = (290, 5), size = (150, 17), font=1, flags = RT_HALIGN_LEFT, text = 2), # index 2 is the IPdescription
                                                        MultiContentEntryText(pos = (100, 29), size = (350, 17), font=1, flags = RT_HALIGN_LEFT, text = 3), # index 3 is the DIRdescription
                                                        MultiContentEntryPixmapAlphaTest(pos = (450, 9), size = (48, 48), png = 4), # index 4 is the activepng pixmap
                                                        MultiContentEntryPixmapAlphaTest(pos = (480, 1), size = (48, 48), png = 5), # index 4 is the mounttype pixmap
                                                ],
                                        "fonts": [gFont("Regular", 20),gFont("Regular", 14)],
                                        "itemHeight": 50
                                        }
                                </convert>
                        </widget>
                        <widget name="introduction" position="110,270" size="300,20" zPosition="10" font="Regular;21" halign="center" transparent="1" />
                        <widget name="ButtonRedtext" position="410,305" size="140,21" zPosition="10" font="Regular;21" transparent="1" />
                        <ePixmap pixmap="skin_default/buttons/button_red.png" position="390,305" zPosition="10" size="15,16" transparent="1" alphatest="on" />
                        <ePixmap pixmap="skin_default/buttons/button_yellow.png" position="30,305" zPosition="10" size="15,16" transparent="1" alphatest="on" />
                        <widget name="deletetext" position="50,305" size="350,21" zPosition="10" font="Regular;21" transparent="1" />
                        <ePixmap pixmap="skin_default/bottombar.png" position="10,250" size="540,120" zPosition="1" transparent="1" alphatest="on" />
                </screen>"""

        def __init__(self, session, plugin_path):
                self.skin_path = plugin_path
                self.session = session
                Screen.__init__(self, session)
                self.mounts = None
                self.applyConfigRef = None
                self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions"],
                {
                        "ok": self.keyOK,
                        "back": self.exit,
                        "cancel": self.exit,
                        "red": self.exit,
                        "yellow": self.delete,
                })
                self["legend1"] = Label(_("Mounted/\nUnmounted"))
                self["legend2"] = Label(_("Mount informations"))
                self["legend3"] = Label(_("Active/\nInactive"))
                self["introduction"] = Label(_("Press OK to edit the settings."))
                self["ButtonRedtext"] = Label(_("Close"))
                self["deletetext"] = Label(_("Delete selected mount"))

                self.list = []
                self["config"] = List(self.list)
                self.showMountsList()

        def showMountsList(self):
                self.list = []
                self.mounts = iAutoMount.getMountsList()
                for sharename in self.mounts.keys():
                        mountentry = iAutoMount.automounts[sharename]
                        self.list.append(self.buildMountViewItem(mountentry))
                self["config"].setList(self.list)

        def buildMountViewItem(self, entry):
                if entry["isMounted"] is True:
                        isMountedpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/ok.png"))
                if entry["isMounted"] is False:
                        isMountedpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/cancel.png"))
                sharename = entry["sharename"]
                IPdescription = _("IP:") + " " + str(entry["ip"])
                DIRdescription = _("Dir:") + " " + str(entry["sharedir"])
                if entry["active"] == 'True' or entry["active"] == True:
                        activepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/lock_on.png"))
                if entry["active"] == 'False' or entry["active"] == False:
                        activepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/lock_error.png"))
                if entry["mounttype"] == 'nfs':
                        mounttypepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/i-nfs.png"))
                if entry["mounttype"] == 'cifs':
                        mounttypepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/i-smb.png"))
                return((isMountedpng, sharename, IPdescription, DIRdescription, activepng, mounttypepng))

        def exit(self):
                self.close()

        def keyOK(self, returnValue = None):
                cur = self["config"].getCurrent()
                if cur:
                        returnValue = cur[1]
                        self.session.openWithCallback(self.MountEditClosed, AutoMountEdit, self.skin_path, iAutoMount.automounts[returnValue])

        def MountEditClosed(self, returnValue = None):
                if returnValue == None:
                        self.showMountsList()

        def delete(self, returnValue = None):
                cur = self["config"].getCurrent()
                if cur:
                        returnValue = cur[1]
                        self.applyConfigRef = self.session.openWithCallback(self.applyConfigfinishedCB, MessageBox, _("Please wait while removing your network mount..."), type = MessageBox.TYPE_INFO, enable_input = False)
                        iAutoMount.removeMount(returnValue,self.removeDataAvail)

        def removeDataAvail(self, data):
                if data is True:
                        iAutoMount.writeMountsConfig()
                        iAutoMount.getAutoMountPoints(self.deleteDataAvail)

        def deleteDataAvail(self, data):
                if data is True:
                        if self.applyConfigRef.execing:
                                self.applyConfigRef.close(True)

        def applyConfigfinishedCB(self,data):
                if data is True:
                        self.session.openWithCallback(self.ConfigfinishedCB, MessageBox, _("Your network mount has been removed."), type = MessageBox.TYPE_INFO, timeout = 10)

        def ConfigfinishedCB(self,data):
                if data is not None:
                        if data is True:
                                self.showMountsList()

