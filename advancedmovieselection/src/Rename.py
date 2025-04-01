#!/usr/bin/python
# -*- coding: utf-8 -*-
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  The plugin is developed on the basis from a lot of single plugins (thx for the code @ all)
#  Coded by JackDaniel (c)2011
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
# for localized messages
from __future__ import print_function
from __future__ import absolute_import
from .__init__ import _
from Screens.Screen import Screen
from Components.config import ConfigText, getConfigListEntry
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from enigma import eServiceReference, iServiceInformation, ePoint
from .Source.ServiceProvider import ServiceCenter, eServiceReferenceVDir
import os
from Components.Label import Label
from Components.Pixmap import Pixmap
from .Source.MovieConfig import MovieConfig
from .Source.Globals import SkinTools, printStackTrace


class MovieRetitle(ConfigListScreen, Screen):
    def __init__(self, session, service):
        Screen.__init__(self, session)
        self.skinName = SkinTools.appendResolution("AdvancedMovieSelection_Rename_")
        self.service = service
        self.movieConfig = MovieConfig()
        self.is_vdir = isinstance(service, eServiceReferenceVDir)
        self.is_dir = service.flags & eServiceReference.mustDescent
        serviceHandler = ServiceCenter.getInstance()
        info = serviceHandler.info(service)
        path = service.getPath()
        if self.is_vdir:
            parts = path.split("/")
            if len(parts) > 2:
                dirName = parts[-3] + "/" + parts[-2]
            else:
                dirName = parts[-2]
            self.original_file = dirName
        elif self.is_dir:
            self.original_file = service.getName()
        else:
            self.original_file = os.path.basename(os.path.splitext(path)[0])
        if self.is_vdir:
            self.original_name = self.movieConfig.getRenamedName(service.getName())
        else:
            self.original_name = info.getName(service)
        self.original_desc = info.getInfoString(service, iServiceInformation.sDescription)
        self.input_file = ConfigText(default=self.original_file, fixed_size=False, visible_width=82)
        self.input_title = ConfigText(default=self.original_name, fixed_size=False, visible_width=82)
        self.input_descr = ConfigText(default=self.original_desc, fixed_size=False, visible_width=82)
        self["key_green"] = StaticText(_("Save"))
        self["key_red"] = StaticText(_("Cancel"))
        self["actions"] = ActionMap(["SetupActions"],
        {
            "ok": self.keyGo,
            "save": self.keyGo,
            "cancel": self.keyCancel,
        }, -2)
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session)
        self.createSetup()
        self["Path"] = Label(_("Location:") + ' ' + os.path.dirname(os.path.splitext(path)[0]))
        self["HelpWindow"] = Pixmap()
        self.onLayoutFinish.append(self.setCustomTitle)

    def createSetup(self):
        self.list = []
        if self.is_vdir:
            self.list.append(getConfigListEntry(_("Displayed bookmark name:"), self.input_title))
        elif self.is_dir:
            self.list.append(getConfigListEntry(_("Foldername:"), self.input_file))
        else:
            self.list.append(getConfigListEntry(_("Filename:"), self.input_file))
            self.list.append(getConfigListEntry(_("Movietitle:"), self.input_title))
            self.list.append(getConfigListEntry(_("Description:"), self.input_descr))

        self["config"].setList(self.list)

    def showKeypad(self, retval=None):
        current = self["config"].getCurrent()
        helpwindowpos = self["HelpWindow"].getPosition()
        if hasattr(current[1], 'help_window'):
            if current[1].help_window.instance is not None:
                current[1].help_window.instance.show()
                current[1].help_window.instance.move(ePoint(helpwindowpos[0], helpwindowpos[1]))

    def setCustomTitle(self):
        if self.is_vdir:
            self.setTitle(_("Change Bookmarkname"))
        elif self.is_dir:
            self.setTitle(_("Change Foldername"))
        else:
            self.setTitle(_("Change File/Moviename and/or Description"))

    def keyGo(self):
        if self.is_vdir:
            if self.input_title.getText() != self.original_name:
                self.renameVDir(self.original_file, self.input_title.getText())
                self.original_name = self.input_title.getText()
        if self.is_dir:
            if self.input_file.getText() != self.original_file:
                self.renameDirectory(self.service, self.input_file.getText())
                self.original_file = self.input_file.getText()
        else:
            if self.input_title.getText() != self.original_name or self.input_descr.getText() != self.original_desc:
                self.setTitleDescr(self.service, self.input_title.getText(), self.input_descr.getText())
                self.original_name = self.input_title.getText()
                self.original_desc = self.input_descr.getText()
            if self.input_file.getText() != self.original_file:
                self.renameFile(self.service, self.input_file.getText())
                self.original_file = self.input_file.getText()
        self.close()

    def keyCancel(self):
        self.close()

    def setTitleDescr(self, service, title, descr):
        try:
            if service.getPath().endswith(".ts"):
                meta_file = service.getPath() + ".meta"
            else:
                meta_file = service.getPath() + ".ts.meta"

            # Create new meta for ts files
            if not os.path.exists(meta_file):
                if os.path.isfile(service.getPath()):
                    _title = os.path.basename(os.path.splitext(service.getPath())[0])
                else:
                    _title = service.getName()
                _sid = "0:0:0:0:0:0:0:0:0:0:"
                _descr = ""
                _time = ""
                _tags = ""
                metafile = open(meta_file, "w")
                metafile.write("%s\n%s\n%s\n%s\n%s" % (_sid, _title, _descr, _time, _tags))
                metafile.close()

            if os.path.exists(meta_file):
                metafile = open(meta_file, "r")
                sid = metafile.readline()
                oldtitle = metafile.readline().rstrip()
                olddescr = metafile.readline().rstrip()
                rest = metafile.read()
                metafile.close()
                if not title and title != "":
                    title = oldtitle
                if not descr and descr != "":
                    descr = olddescr
                metafile = open(meta_file, "w")
                metafile.write("%s%s\n%s\n%s" % (sid, title, descr, rest))
                metafile.close()
        except:
            printStackTrace()

    def renameDirectory(self, service, new_name):
        try:
            dir_name = os.path.dirname(self.service.getPath()[0:-1])
            os.rename(self.service.getPath(), os.path.join(dir_name, self.input_file.getText() + "/"))
            self.original_file = self.input_file.getText()
        except:
            printStackTrace()

    def renameFile(self, service, new_name):
        try:
            path = os.path.dirname(service.getPath())
            file_name = os.path.basename(os.path.splitext(service.getPath())[0])
            src = os.path.join(path, file_name)
            dst = os.path.join(path, new_name)
            import glob
            for f in glob.glob(os.path.join(path, src + "*")):
                os.rename(f, f.replace(src, dst))
        except:
            printStackTrace()

    def renameVDir(self, dir_name, name):
        try:
            if dir_name + "\t" + self.original_name not in self.movieConfig.rename:
                self.movieConfig.rename.append(dir_name + "\t" + name)
            elif name == "":
                for index, item in enumerate(self.movieConfig.rename):
                    i = item.split("\t")
                    if i[0] == dir_name:
                        print(dir_name + "\t" + name)
                        del self.movieConfig.rename[index]
            else:
                for index, item in enumerate(self.movieConfig.rename):
                    i = item.split("\t")
                    if i[0] == dir_name:
                        self.movieConfig.rename[index] = dir_name + "\t" + name
            self.movieConfig.safe()
        except:
            printStackTrace()
