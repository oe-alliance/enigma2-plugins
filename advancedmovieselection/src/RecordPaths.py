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
from __init__ import _
from Screens.Screen import Screen
from Screens.LocationBox import MovieLocationBox, TimeshiftLocationBox
from Screens.MessageBox import MessageBox
from Components.config import config, ConfigSelection, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.UsageConfig import preferredPath
from Tools.Directories import fileExists

class RecordPathsSettings(Screen, ConfigListScreen):
    skin = """
        <screen name="RecordPathsSettings" position="center,center" size="620,200" title="Recording paths">
            <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on"/>
            <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on"/>
            <widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1"/>
            <widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1"/>
            <widget name="config" position="0,50" size="620,146"/>
        </screen>"""

    def __init__(self, session):
        from Components.Sources.StaticText import StaticText
        Screen.__init__(self, session)
        self["key_red"] = StaticText(_("Cancel"))
        self["key_green"] = StaticText(_("Save"))

        ConfigListScreen.__init__(self, [])
        self.initConfigList()

        self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
        {
            "green": self.save,
            "red": self.cancel,
            "cancel": self.cancel,
            "ok": self.ok,
        }, -2)
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(_("Record Paths Settings"))

    def checkReadWriteDir(self, configele):
        print "checkReadWrite: ", configele.value
        if configele.value in [x[0] for x in self.styles] or fileExists(configele.value, "w"):
            configele.last_value = configele.value
            return True
        else:
            dir = configele.value
            configele.value = configele.last_value
            self.session.open(
                MessageBox,
                _("The directory %s is not writable.\nMake sure you select a writable directory instead.") % dir,
                type=MessageBox.TYPE_ERROR
                )
            return False

    def initConfigList(self):
        self.styles = [ ("<default>", _("<Default movie location>")), ("<current>", _("<Current movielist location>")), ("<timer>", _("<Last timer location>")) ]
        styles_keys = [x[0] for x in self.styles]        
        
        tmp = config.movielist.videodirs.value
        default = config.usage.default_path.value
        if default not in tmp:
            tmp = tmp[:]
            tmp.append(default)
        print "DefaultPath: ", default, tmp
        self.default_dirname = ConfigSelection(default=default, choices=tmp)        
        tmp = config.movielist.videodirs.value        
        default = config.usage.timer_path.value        
        if default not in tmp and default not in styles_keys:
            tmp = tmp[:]
            tmp.append(default)
        print "TimerPath: ", default, tmp
        self.timer_dirname = ConfigSelection(default=default, choices=self.styles + tmp)        
        tmp = config.movielist.videodirs.value        
        default = config.usage.instantrec_path.value        
        if default not in tmp and default not in styles_keys:
            tmp = tmp[:]
            tmp.append(default)
        print "InstantrecPath: ", default, tmp
        self.instantrec_dirname = ConfigSelection(default=default, choices=self.styles + tmp)        
        tmp = config.usage.allowed_timeshift_paths.value
        default = config.usage.timeshift_path.value                        
        if default not in tmp:
            tmp = tmp[:]
            tmp.append(default)
        print "TimeshiftPath: ", default, tmp
        self.timeshift_dirname = ConfigSelection(default=default, choices=tmp)        
        tmp = config.movielist.videodirs.value
        default = config.AdvancedMovieSelection.movecopydirs.value
        if default not in tmp:
            tmp = tmp[:]
            tmp.append(default)
        print "MoveCopyPath: ", default, tmp        
        self.movecopy_dirname = ConfigSelection(default=default, choices=tmp)                
        self.default_dirname.addNotifier(self.checkReadWriteDir, initial_call=False, immediate_feedback=False)
        self.default_dirname.last_value = self.default_dirname.value
        self.timer_dirname.addNotifier(self.checkReadWriteDir, initial_call=False, immediate_feedback=False)
        self.timer_dirname.last_value = self.timer_dirname.value
        self.instantrec_dirname.addNotifier(self.checkReadWriteDir, initial_call=False, immediate_feedback=False)
        self.instantrec_dirname.last_value = self.instantrec_dirname.value
        self.timeshift_dirname.addNotifier(self.checkReadWriteDir, initial_call=False, immediate_feedback=False)
        self.timeshift_dirname.last_value = self.timeshift_dirname.value        
        self.movecopy_dirname.addNotifier(self.checkReadWriteDir, initial_call=False, immediate_feedback=False)
        self.movecopy_dirname.last_value = config.AdvancedMovieSelection.movecopydirs.value
        
        self.list = []
        self.default_entry = getConfigListEntry(_("Default movie location:"), self.default_dirname)
        self.list.append(self.default_entry)
        self.timer_entry = getConfigListEntry(_("Timer record location:"), self.timer_dirname)
        self.list.append(self.timer_entry)
        self.instantrec_entry = getConfigListEntry(_("Instant record location:"), self.instantrec_dirname)
        self.list.append(self.instantrec_entry)
        self.timeshift_entry = getConfigListEntry(_("Timeshift location:"), self.timeshift_dirname)
        self.list.append(self.timeshift_entry)
        self.movecopy_entry = getConfigListEntry(_("Move/copy location:"), self.movecopy_dirname)
        self.list.append(self.movecopy_entry)
        self["config"].setList(self.list)

    def ok(self):
        currentry = self["config"].getCurrent()
        self.lastvideodirs = config.movielist.videodirs.value
        self.lasttimeshiftdirs = config.usage.allowed_timeshift_paths.value
        self.lastmovecopydir = config.AdvancedMovieSelection.movecopydirs.value
        txt = _("Default movie location")
        if currentry == self.default_entry:
            self.entrydirname = self.default_dirname
            self.session.openWithCallback(
                self.dirnameSelected,
                MovieLocationBox,
                txt,
                preferredPath(self.default_dirname.value)
            )
        elif currentry == self.timer_entry:
            self.entrydirname = self.timer_dirname
            self.session.openWithCallback(
                self.dirnameSelected,
                MovieLocationBox,
                _("Initial location in new timers"),
                preferredPath(self.timer_dirname.value)
            )
        elif currentry == self.instantrec_entry:
            self.entrydirname = self.instantrec_dirname
            self.session.openWithCallback(
                self.dirnameSelected,
                MovieLocationBox,
                _("Location for instant recordings"),
                preferredPath(self.instantrec_dirname.value)
            )
        elif currentry == self.timeshift_entry:
            self.entrydirname = self.timeshift_dirname
            config.usage.timeshift_path.value = self.timeshift_dirname.value
            self.session.openWithCallback(
                self.dirnameSelected,
                TimeshiftLocationBox
            )
        elif currentry == self.movecopy_entry:
            self.entrydirname = self.movecopy_dirname
            self.session.openWithCallback(
                self.dirnameSelected,
                MovieLocationBox,
                _("Location for move/copy files"),
                preferredPath(self.movecopy_dirname.value)
            )

    def dirnameSelected(self, res):
        if res is not None:
            self.entrydirname.value = res
            if config.movielist.videodirs.value != self.lastvideodirs:
                styles_keys = [x[0] for x in self.styles]
                tmp = config.movielist.videodirs.value
                default = self.default_dirname.value
                if default not in tmp:
                    tmp = tmp[:]
                    tmp.append(default)
                self.default_dirname.setChoices(tmp, default=default)
                tmp = config.movielist.videodirs.value
                default = self.timer_dirname.value
                if default not in tmp and default not in styles_keys:
                    tmp = tmp[:]
                    tmp.append(default)
                self.timer_dirname.setChoices(self.styles + tmp, default=default)
                tmp = config.movielist.videodirs.value
                default = self.instantrec_dirname.value
                if default not in tmp and default not in styles_keys:
                    tmp = tmp[:]
                    tmp.append(default)
                self.instantrec_dirname.setChoices(self.styles + tmp, default=default)
                self.entrydirname.value = res
            if config.usage.allowed_timeshift_paths.value != self.lasttimeshiftdirs:
                tmp = config.usage.allowed_timeshift_paths.value
                default = self.instantrec_dirname.value
                if default not in tmp:
                    tmp = tmp[:]
                    tmp.append(default)
                self.timeshift_dirname.setChoices(tmp, default=default)
                self.entrydirname.value = res
            if self.entrydirname.last_value != res:
                self.checkReadWriteDir(self.entrydirname)

            if config.AdvancedMovieSelection.movecopydirs.value != self.lastmovecopydir:
                tmp = config.AdvancedMovieSelection.movecopydirs.value
                default = self.movecopy_dirname.value
                if default not in tmp:
                    tmp = tmp[:]
                    tmp.append(default)
                self.movecopy_dirname.setChoices(tmp, default=default)

    def save(self):
        currentry = self["config"].getCurrent()
        if self.checkReadWriteDir(currentry[1]):
            config.usage.default_path.value = self.default_dirname.value
            config.usage.timer_path.value = self.timer_dirname.value
            config.usage.instantrec_path.value = self.instantrec_dirname.value 
            config.usage.timeshift_path.value = self.timeshift_dirname.value
            config.AdvancedMovieSelection.movecopydirs.value = self.movecopy_dirname.value
            config.usage.default_path.save()
            config.usage.timer_path.save()
            config.usage.instantrec_path.save()
            config.usage.timeshift_path.save()
            config.AdvancedMovieSelection.movecopydirs.save()
            self.close()

    def cancel(self):
        self.close()

