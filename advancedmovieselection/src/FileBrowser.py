#!/usr/bin/python
# -*- coding: utf-8 -*-
#  Advanced Movie Selection for Dreambox-Enigma2
#
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
from __future__ import print_function
from __future__ import absolute_import
from .__init__ import _
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.FileList import FileList
from Tools.Directories import pathExists

lastpath = ""


class FileBrowser(Screen):
    def __init__(self, session, current_path=None):
        Screen.__init__(self, session)
        global lastpath
        if current_path:
            lastpath = current_path
        if lastpath is not None:
            currDir = lastpath
        else:
            currDir = "/media/"
        if not pathExists(currDir):
            currDir = "/"
        if lastpath == "":  # 'None' is magic to start at the list of mountpoints
            currDir = None

        #inhibitDirs = ["/bin", "/boot", "/dev", "/etc", "/home", "/lib", "/proc", "/sbin", "/share", "/sys", "/tmp", "/usr", "/var"]
        self.filelist = FileList(currDir, matchingPattern="(?i)^.*\.(backup)", useServiceRef=False)
        self["filelist"] = self.filelist

        self["FilelistActions"] = ActionMap(["SetupActions"],
            {
                "save": self.ok,
                "ok": self.ok,
                "cancel": self.exit
            })
        self["key_red"] = StaticText(_("Cancel"))
        self["key_green"] = StaticText(_("OK"))
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(_("File Browser"))

    def ok(self):
        global lastpath
        if self["filelist"].canDescent(): # isDir
            self["filelist"].descent()
            lastpath = self["filelist"].getCurrentDirectory() or lastpath
        else:
            file_name = self["filelist"].getFilename()
            lastpath = self["filelist"].getCurrentDirectory() or lastpath
            print("lastpath directory=", lastpath)
            self.close(lastpath + file_name)

    def exit(self):
        self.close(None)
