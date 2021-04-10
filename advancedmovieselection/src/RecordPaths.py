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
from __future__ import print_function
from __future__ import absolute_import
from .__init__ import _
# Topfi: use local eRecordPaths instead of Screens.RecordPaths
from .eRecordPaths import RecordPathsSettings as eRecordPathsSettings 
from Screens.LocationBox import MovieLocationBox
from Components.config import config, ConfigSelection, getConfigListEntry
from Components.UsageConfig import preferredPath


class RecordPathsSettings(eRecordPathsSettings):
    def __init__(self, session):
        eRecordPathsSettings.__init__(self, session)
        self.onShown.append(self.__setWindowTitle)

    def __setWindowTitle(self):
        self.setTitle(_("Record Paths Settings"))

    def initConfigList(self):
        eRecordPathsSettings.initConfigList(self)
        tmp = config.movielist.videodirs.value
        default = config.AdvancedMovieSelection.movecopydirs.value
        if default not in tmp:
            tmp = tmp[:]
            tmp.append(default)
        print("MoveCopyPath: ", default, tmp)        
        self.movecopy_dirname = ConfigSelection(default=default, choices=tmp)                
        self.movecopy_dirname.addNotifier(self.checkReadWriteDir, initial_call=False, immediate_feedback=False)
        self.movecopy_dirname.last_value = config.AdvancedMovieSelection.movecopydirs.value
        self.movecopy_entry = getConfigListEntry(_("Move/copy location:"), self.movecopy_dirname)
        self.list.append(self.movecopy_entry)
        self["config"].setList(self.list)
        if not self.selectionChanged in self["config"].onSelectionChanged:
            self["config"].onSelectionChanged.append(self.selectionChanged)

    def selectionChanged(self):
        # Topfi: disabled three lines which causes GS
        #eRecordPathsSettings.selectionChanged(self)
        currentry = self["config"].getCurrent()
        #if currentry == self.movecopy_entry:
        #    self["introduction"].setText(_("Please select the default move/copy location which is used for move/copy movies."))

    def ok(self):
        eRecordPathsSettings.ok(self)
        currentry = self["config"].getCurrent()
        if currentry == self.movecopy_entry:
            self.entrydirname = self.movecopy_dirname
            self.session.openWithCallback(
                self.dirnameSelected,
                MovieLocationBox,
                _("Location for move/copy files"),
                preferredPath(self.movecopy_dirname.value)
            )

    def dirnameSelected(self, res):
        eRecordPathsSettings.dirnameSelected(self, res)
        if res is not None:
            if config.AdvancedMovieSelection.movecopydirs.value != res:
                tmp = config.movielist.videodirs.value
                default = config.AdvancedMovieSelection.movecopydirs.value
                if default not in tmp:
                    tmp = tmp[:]
                    tmp.append(default)
                self.movecopy_dirname.setChoices(tmp, default=default)

    def save(self):
        currentry = self["config"].getCurrent()
        if self.checkReadWriteDir(currentry[1]):
            config.AdvancedMovieSelection.movecopydirs.value = self.movecopy_dirname.value
            config.AdvancedMovieSelection.movecopydirs.save()
        eRecordPathsSettings.save(self)
