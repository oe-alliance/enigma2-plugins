# -*- coding: utf-8 -*-
# for localized messages
from __init__ import _
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config, ConfigIP, NoSave, ConfigText, ConfigEnableDisable, ConfigPassword, ConfigSelection, getConfigListEntry, ConfigYesNo
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap, NumberActionMap
from enigma import ePoint
from AutoMount import iAutoMount, AutoMount
from re import sub as re_sub

class AutoMountEdit(Screen, ConfigListScreen):
        skin = """
                <screen name="AutoMountEdit" position="90,110" size="560,400" title="MountEdit">
                        <widget name="config" position="10,10" size="540,200" zPosition="1" scrollbarMode="showOnDemand" />
                        <widget name="ButtonGreen" pixmap="skin_default/buttons/button_green.png" position="30,365" zPosition="10" size="15,16" transparent="1" alphatest="on" />
                        <widget name="introduction2" position="110,330" size="300,20" zPosition="10" font="Regular;21" halign="center" transparent="1" />
                        <widget name="ButtonRedtext" position="410,365" size="140,21" zPosition="10" font="Regular;21" transparent="1" />
                        <widget name="ButtonRed" pixmap="skin_default/buttons/button_red.png" position="390,365" zPosition="10" size="15,16" transparent="1" alphatest="on" />
                        <widget name="VKeyIcon" pixmap="skin_default/vkey_icon.png" position="40,345" zPosition="10" size="60,48" transparent="1" alphatest="on" />
                        <widget name="HelpWindow" pixmap="skin_default/vkey_icon.png" position="175,325" zPosition="1" size="1,1" transparent="1" alphatest="on" />
                        <ePixmap pixmap="skin_default/bottombar.png" position="10,310" size="540,120" zPosition="1" transparent="1" alphatest="on" />
                </screen>"""

        def __init__(self, session, plugin_path, mountinfo = None ):
                self.skin_path = plugin_path
                self.session = session
                Screen.__init__(self, self.session)

                self.mountinfo = mountinfo
                if self.mountinfo is None:
                        #Initialize blank mount enty
                        self.mountinfo = { 'isMounted': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False, 'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }

                self.applyConfigRef = None
                self.updateConfigRef = None
                self.mounts = iAutoMount.getMountsList()
                self.createConfig()

                self["actions"] = NumberActionMap(["SetupActions"],
                {
                        "ok": self.ok,
                        "back": self.close,
                        "cancel": self.close,
                        "red": self.close,
                }, -2)

                self["VirtualKB"] = ActionMap(["ShortcutActions"],
                {
                        "green": self.KeyGreen,
                }, -2)

                self.list = []
                ConfigListScreen.__init__(self, self.list,session = self.session)
                self.createSetup()
                self.onLayoutFinish.append(self.layoutFinished)
                # Initialize Buttons
                self["ButtonGreen"] = Pixmap()
                self["VKeyIcon"] = Pixmap()
                self["HelpWindow"] = Pixmap()
                self["introduction2"] = Label(_("Press OK to activate the settings."))
                self["ButtonRed"] = Pixmap()
                self["ButtonRedtext"] = Label(_("Close"))


        def layoutFinished(self):
                self.setTitle(_("Mounts editor"))
                self["ButtonGreen"].hide()
                self["VKeyIcon"].hide()
                self["VirtualKB"].setEnabled(False)
                self["HelpWindow"].hide()

        # helper function to convert ips from a sring to a list of ints
        def convertIP(self, ip):
                strIP = ip.split('.')
                ip = []
                for x in strIP:
                        ip.append(int(x))
                return ip

        def exit(self):
                self.close()

        def createConfig(self):
                self.sharenameEntry = None
                self.mounttypeEntry = None
                self.activeEntry = None
                self.ipEntry = None
                self.sharedirEntry = None
                self.optionsEntry = None
                self.usernameEntry = None
                self.passwordEntry = None
                self.hdd_replacementEntry = None

                self.sharetypelist = []
                self.sharetypelist.append(("nfs", _("NFS share")))
                self.sharetypelist.append(("cifs", _("CIFS share")))

                if self.mountinfo.has_key('mounttype'):
                        mounttype = self.mountinfo['mounttype']
                else:
                        mounttype = "nfs"

                if self.mountinfo.has_key('active'):
                        active = self.mountinfo['active']
                        if active == 'True':
                                active = True
                        if active == 'False':
                                active = False
                else:
                        active = True
                if self.mountinfo.has_key('ip'):
                        if self.mountinfo['ip'] is False:
                                ip = [192, 168, 0, 0]
                        else:
                                ip = self.convertIP(self.mountinfo['ip'])
                else:
                        ip = [192, 168, 0, 0]
                if self.mountinfo.has_key('sharename'):
                        sharename = self.mountinfo['sharename']
                else:
                        sharename = "Sharename"
                if self.mountinfo.has_key('sharedir'):
                        sharedir = self.mountinfo['sharedir']
                else:
                        sharedir = "/export/hdd"
                if self.mountinfo.has_key('options'):
                        options = self.mountinfo['options']
                else:
                        options = "rw,nolock"
                if self.mountinfo.has_key('username'):
                        username = self.mountinfo['username']
                else:
                        username = ""
                if self.mountinfo.has_key('password'):
                        password = self.mountinfo['password']
                else:
                        password = ""
                if self.mountinfo.has_key('hdd_replacement'):
                        hdd_replacement = self.mountinfo['hdd_replacement']
                        if hdd_replacement == 'True':
                                hdd_replacement = True
                        if hdd_replacement == 'False':
                                hdd_replacement = False
                else:
                        hdd_replacement = False
                if sharename is False:
                        sharename = "Sharename"
                if sharedir is False:
                        sharedir = "/export/hdd"
                if options is False:
                        if mounttype == "nfs":
                                options = "rw,nolock"
                        else:
                                options = "rw"
                if username is False:
                        username = ""
                if password is False:
                        password = ""
                if mounttype is False:
                        mounttype = "nfs"

                self.activeConfigEntry = NoSave(ConfigEnableDisable(default = active))
                self.ipConfigEntry = NoSave(ConfigIP(default = ip))
                self.sharenameConfigEntry = NoSave(ConfigText(default = sharename, visible_width = 50, fixed_size = False))
                self.sharedirConfigEntry = NoSave(ConfigText(default = sharedir, visible_width = 50, fixed_size = False))
                self.optionsConfigEntry = NoSave(ConfigText(default = options, visible_width = 50, fixed_size = False))
                self.usernameConfigEntry = NoSave(ConfigText(default = username, visible_width = 50, fixed_size = False))
                self.passwordConfigEntry = NoSave(ConfigPassword(default = password, visible_width = 50, fixed_size = False))
                self.mounttypeConfigEntry = NoSave(ConfigSelection(self.sharetypelist, default = mounttype ))
                self.hdd_replacementConfigEntry = NoSave(ConfigYesNo(default = hdd_replacement))

        def createSetup(self):
                self.list = []
                self.activeEntry = getConfigListEntry(_("Active"), self.activeConfigEntry)
                self.list.append(self.activeEntry)
                self.sharenameEntry = getConfigListEntry(_("Local share name"), self.sharenameConfigEntry)
                self.list.append(self.sharenameEntry)
                self.mounttypeEntry = getConfigListEntry(_("Mount type"), self.mounttypeConfigEntry)
                self.list.append(self.mounttypeEntry)
                self.ipEntry = getConfigListEntry(_("Server IP"), self.ipConfigEntry)
                self.list.append(self.ipEntry)
                self.sharedirEntry = getConfigListEntry(_("Server share"), self.sharedirConfigEntry)
                self.list.append(self.sharedirEntry)
                self.hdd_replacementEntry = getConfigListEntry(_("use as HDD replacement"), self.hdd_replacementConfigEntry)
                self.list.append(self.hdd_replacementEntry)
                if self.mounttypeConfigEntry.value == "cifs":
                        self.optionsConfigEntry = NoSave(ConfigText(default = "rw", visible_width = 50, fixed_size = False))
                else:
                        self.optionsConfigEntry = NoSave(ConfigText(default = "rw,nolock", visible_width = 50, fixed_size = False))
                self.optionsEntry = getConfigListEntry(_("Mount options"), self.optionsConfigEntry)
                self.list.append(self.optionsEntry)
                if self.mounttypeConfigEntry.value == "cifs":
                        self.usernameEntry = getConfigListEntry(_("Username"), self.usernameConfigEntry)
                        self.list.append(self.usernameEntry)
                        self.passwordEntry = getConfigListEntry(_("Password"), self.passwordConfigEntry)
                        self.list.append(self.passwordEntry)

                self["config"].list = self.list
                self["config"].l.setList(self.list)
                self["config"].onSelectionChanged.append(self.selectionChanged)

        def newConfig(self):
                if self["config"].getCurrent() == self.mounttypeEntry:
                        self.createSetup()

        def KeyGreen(self):
                print "Green Pressed"
                if self["config"].getCurrent() == self.sharenameEntry:
                        self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'sharename'), VirtualKeyBoard, title = (_("Enter share name:")), text = self.sharenameConfigEntry.value)
                if self["config"].getCurrent() == self.sharedirEntry:
                        self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'sharedir'), VirtualKeyBoard, title = (_("Enter share directory:")), text = self.sharedirConfigEntry.value)
                if self["config"].getCurrent() == self.optionsEntry:
                        self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'options'), VirtualKeyBoard, title = (_("Enter options:")), text = self.optionsConfigEntry.value)
                if self["config"].getCurrent() == self.usernameEntry:
                        self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'username'), VirtualKeyBoard, title = (_("Enter username:")), text = self.usernameConfigEntry.value)
                if self["config"].getCurrent() == self.passwordEntry:
                        self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'password'), VirtualKeyBoard, title = (_("Enter password:")), text = self.passwordConfigEntry.value)

        def VirtualKeyBoardCallback(self, callback = None, entry = None):
                if callback is not None and len(callback) and entry is not None and len(entry):
                        if entry == 'sharename':
                                self.sharenameConfigEntry = NoSave(ConfigText(default = callback, visible_width = 50, fixed_size = False))
                                self.createSetup()
                        if entry == 'sharedir':
                                self.sharedirConfigEntry = NoSave(ConfigText(default = callback, visible_width = 50, fixed_size = False))
                                self.createSetup()
                        if entry == 'options':
                                self.optionsConfigEntry = NoSave(ConfigText(default = callback, visible_width = 50, fixed_size = False))
                                self.createSetup()
                        if entry == 'username':
                                self.usernameConfigEntry = NoSave(ConfigText(default = callback, visible_width = 50, fixed_size = False))
                                self.createSetup()
                        if entry == 'password':
                                self.passwordConfigEntry = NoSave(ConfigPassword(default = callback, visible_width = 50, fixed_size = False))
                                self.createSetup()

        def keyLeft(self):
                ConfigListScreen.keyLeft(self)
                self.newConfig()

        def keyRight(self):
                ConfigListScreen.keyRight(self)
                self.newConfig()

        def selectionChanged(self):
                current = self["config"].getCurrent()
                if current == self.activeEntry or current == self.ipEntry or current == self.mounttypeEntry or current == self.hdd_replacementEntry:
                        self["ButtonGreen"].hide()
                        self["VKeyIcon"].hide()
                        self["VirtualKB"].setEnabled(False)
                else:
                        helpwindowpos = self["HelpWindow"].getPosition()
                        if current[1].help_window.instance is not None:
                                current[1].help_window.instance.move(ePoint(helpwindowpos[0],helpwindowpos[1]))
                                self["ButtonGreen"].show()
                                self["VKeyIcon"].show()
                                self["VirtualKB"].setEnabled(True)

        def ok(self):
                current = self["config"].getCurrent()
                if current == self.sharenameEntry or current == self.sharedirEntry or current == self.sharedirEntry or current == self.optionsEntry or current == self.usernameEntry or current == self.passwordEntry:
                        if current[1].help_window.instance is not None:
                                current[1].help_window.instance.hide()
                sharename = self.sharenameConfigEntry.value

                if self.mounts.has_key(sharename) is True:
                        self.session.openWithCallback(self.updateConfig, MessageBox, (_("A mount entry with this name already exists!\nUpdate existing entry and continue?\n") ) )
                else:
                        self.session.openWithCallback(self.applyConfig, MessageBox, (_("Are you sure you want to save this network mount?\n\n") ) )

        def updateConfig(self, ret = False):
                if (ret == True):
                        iAutoMount.setMountsAttribute(self.sharenameConfigEntry.value, "sharename", self.sharenameConfigEntry.value)
                        iAutoMount.setMountsAttribute(self.sharenameConfigEntry.value, "active", self.activeConfigEntry.value)
                        iAutoMount.setMountsAttribute(self.sharenameConfigEntry.value, "ip", self.ipConfigEntry.getText())
                        iAutoMount.setMountsAttribute(self.sharenameConfigEntry.value, "sharedir", self.sharedirConfigEntry.value)
                        iAutoMount.setMountsAttribute(self.sharenameConfigEntry.value, "mounttype", self.mounttypeConfigEntry.value)
                        iAutoMount.setMountsAttribute(self.sharenameConfigEntry.value, "options", self.optionsConfigEntry.value)
                        iAutoMount.setMountsAttribute(self.sharenameConfigEntry.value, "username", self.usernameConfigEntry.value)
                        iAutoMount.setMountsAttribute(self.sharenameConfigEntry.value, "password", self.passwordConfigEntry.value)
                        iAutoMount.setMountsAttribute(self.sharenameConfigEntry.value, "hdd_replacement", self.hdd_replacementConfigEntry.value)

                        self.updateConfigRef = None
                        self.updateConfigRef = self.session.openWithCallback(self.updateConfigfinishedCB, MessageBox, _("Please wait while updating your network mount..."), type = MessageBox.TYPE_INFO, enable_input = False)
                        iAutoMount.writeMountsConfig()
                        iAutoMount.getAutoMountPoints(self.updateConfigDataAvail)
                else:
                        self.close()

        def updateConfigDataAvail(self, data):
                if data is True:
                        self.updateConfigRef.close(True)

        def updateConfigfinishedCB(self,data):
                if data is True:
                        self.session.openWithCallback(self.Updatefinished, MessageBox, _("Your network mount has been updated."), type = MessageBox.TYPE_INFO, timeout = 10)

        def Updatefinished(self,data):
                if data is not None:
                        if data is True:
                                self.close()

        def applyConfig(self, ret = False):
                if (ret == True):
                        data = { 'isMounted': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, \
                                        'username': False, 'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }
                        data['active'] = self.activeConfigEntry.value
                        data['ip'] = self.ipConfigEntry.getText()
                        data['sharename'] = re_sub("\W", "", self.sharenameConfigEntry.value)
                        # "\W" matches everything that is "not numbers, letters, or underscores",where the alphabet defaults to ASCII.
                        data['sharedir'] = self.sharedirConfigEntry.value
                        data['options'] =  self.optionsConfigEntry.value
                        data['mounttype'] = self.mounttypeConfigEntry.value
                        data['username'] = self.usernameConfigEntry.value
                        data['password'] = self.passwordConfigEntry.value
                        data['hdd_replacement'] = self.hdd_replacementConfigEntry.value
                        self.applyConfigRef = None
                        self.applyConfigRef = self.session.openWithCallback(self.applyConfigfinishedCB, MessageBox, _("Please wait for activation of your network mount..."), type = MessageBox.TYPE_INFO, enable_input = False)
                        iAutoMount.automounts[self.sharenameConfigEntry.value] = data
                        iAutoMount.writeMountsConfig()
                        iAutoMount.getAutoMountPoints(self.applyConfigDataAvail)
                else:
                        self.close()

        def applyConfigDataAvail(self, data):
                if data is True:
                        self.applyConfigRef.close(True)

        def applyConfigfinishedCB(self,data):
                if data is True:
                        self.session.openWithCallback(self.applyfinished, MessageBox, _("Your network mount has been activated."), type = MessageBox.TYPE_INFO, timeout = 10)

        def applyfinished(self,data):
                if data is not None:
                        if data is True:
                                self.close()
