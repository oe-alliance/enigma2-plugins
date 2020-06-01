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
from Components.ActionMap import ActionMap
from Components.config import config, ConfigNumber, ConfigSelection, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import MovingPixmap
from enigma import eTimer, getDesktop, ePoint
from keyids import KEYIDS
from Screens.InfoBar import MoviePlayer
from Screens.Screen import Screen
from Tools.KeyBindings import addKeyBinding
import keymapparser
from Source.Globals import SkinTools

class Seekbar(ConfigListScreen, Screen):
    def __init__(self, session, instance, fwd):
        Screen.__init__(self, session)
        self.skinName = SkinTools.appendResolution("AdvancedMovieSelectionSeekbar")
        self.session = session
        self.infobarInstance = instance
        self.fwd = fwd
        if isinstance(session.current_dialog, MoviePlayer):
            self.dvd = False
        else:
            self.dvd = True
        self.percent = 0.0
        self.length = None
        service = session.nav.getCurrentService()
        if service:
            self.seek = service.seek()
            if self.seek:
                self.length = self.seek.getLength()
                position = self.seek.getPlayPosition()
                if self.length and position:
                    if int(position[1]) > 0:
                        self.percent = float(position[1]) * 100.0 / float(self.length[1])
        
        self.minuteInput = ConfigNumber(default=5)
        self.positionEntry = ConfigSelection(choices=[_("Use arrow left/right for position")], default=_("Use arrow left/right for position"))
        if self.fwd:
            txt = _("Jump x minutes forward (OK for seek):")
        else:
            txt = _("Jump x minutes back (OK for seek):")
        ConfigListScreen.__init__(self, [getConfigListEntry(txt, self.minuteInput), getConfigListEntry(_("Go manual to position (OK for seek):"), self.positionEntry)])        
        self["cursor"] = MovingPixmap()
        self["time"] = Label()
        self["actions"] = ActionMap(["WizardActions"], 
            {"back": self.exit}, 
        -1)
        self.cursorTimer = eTimer()
        self.cursorTimer.callback.append(self.updateCursor)
        self.cursorTimer.start(200, False)
        self.onShown.append(self.setWindowTitle)
        self.onLayoutFinish.append(self.firstStart)
        self.firstime = True
        self.onExecBegin.append(self.__onExecBegin)

    def __onExecBegin(self):
        if self.firstime:
            orgpos = self.instance.position()    
            self.instance.move(ePoint(orgpos.x() + config.AdvancedMovieSelection.movieplayer_infobar_position_offset_x.value, orgpos.y() + config.AdvancedMovieSelection.movieplayer_infobar_position_offset_y.value))
            self.firstime = False

    def setWindowTitle(self):
        self.setTitle(_("Advanced Movie Selection Seek"))

    def firstStart(self):
        self["config"].setCurrentIndex(1)

    def updateCursor(self):
        if self.length:
            try:
                sz_w = getDesktop(0).size().width()
            except:
                sz_w = 720
            if sz_w == 1280:
                x = 60 + int(11.5 * self.percent)
            elif sz_w == 1024:
                x = 60 + int(9.0 * self.percent)
            else:
                x = 5 + int(6.8 * self.percent)
            self["cursor"].moveTo(x, 100, 1)
            self["cursor"].startMoving()
            pts = int(float(self.length[1]) / 100.0 * self.percent)
            self["time"].setText(_("Manual jump to:") + ' ' + ("%d:%02d" % ((pts/60/90000), ((pts/90000)%60))))

    def exit(self):
        self.cursorTimer.stop()
        ConfigListScreen.saveAll(self)
        self.close()

    def keyOK(self):
        sel = self["config"].getCurrent()[1]
        if sel == self.positionEntry:
            if self.length:
                if self.dvd: # seekTo() doesn't work for DVD Player
                    oldPosition = self.seek.getPlayPosition()[1]
                    newPosition = int(float(self.length[1]) / 100.0 * self.percent)
                    if newPosition > oldPosition:
                        pts = newPosition - oldPosition
                    else:
                        pts = -1*(oldPosition - newPosition)
                    DVDPlayer.doSeekRelative(self.infobarInstance, pts)
                else:
                    self.seek.seekTo(int(float(self.length[1]) / 100.0 * self.percent))
                self.exit()
        elif sel == self.minuteInput:
            pts = self.minuteInput.value * 60 * 90000
            if self.fwd == False:
                pts = -1*pts
            if self.dvd:
                DVDPlayer.doSeekRelative(self.infobarInstance, pts)
            else:
                MoviePlayer.doSeekRelative(self.infobarInstance, pts)
            self.exit()

    def keyLeft(self):
        sel = self["config"].getCurrent()[1]
        if sel == self.positionEntry:
            self.percent -= float(config.AdvancedMovieSelection.sensibility.value) / 1.0
            if self.percent < 0.0:
                self.percent = 0.0
        else:
            ConfigListScreen.keyLeft(self)

    def keyRight(self):
        sel = self["config"].getCurrent()[1]
        if sel == self.positionEntry:
            self.percent += float(config.AdvancedMovieSelection.sensibility.value) / 1.0
            if self.percent > 100.0:
                self.percent = 100.0
        else:
            ConfigListScreen.keyRight(self)

    def keyNumberGlobal(self, number):
        sel = self["config"].getCurrent()[1]
        if sel == self.positionEntry:
            self.percent = float(number) * 10.0
        else:
            ConfigListScreen.keyNumberGlobal(self, number)

##############################################
# This hack overwrites the functions seekFwdManual and seekBackManual of the InfoBarSeek class (MoviePlayer and DVDPlayer)

def seekbar(instance, fwd=True):
    if instance and instance.session:
        instance.session.open(Seekbar, instance, fwd)

def seekbarBack(instance):
    seekbar(instance, False)

MoviePlayer.seekFwdManual = seekbar
MoviePlayer.seekBackManual = seekbarBack

from Source.Globals import pluginPresent
if pluginPresent.DVDPlayer:
    from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
    DVDPlayer.seekFwdManual = seekbar
    DVDPlayer.seekBackManual = seekbarBack

##############################################
# This hack puts the functions seekFwdManual and seekBackManual to the maped keys to seekbarRight and seekbarLeft

DoBind = ActionMap.doBind
def doBind(instance):
    if not instance.bound:
        for ctx in instance.contexts:
            if ctx == "InfobarSeekActions":
                if "seekFwdManual" in instance.actions:
                    instance.actions["seekbarRight"] = instance.actions["seekFwdManual"]
                if "seekBackManual" in instance.actions:
                    instance.actions["seekbarLeft"] = instance.actions["seekBackManual"]
            DoBind(instance)

if config.AdvancedMovieSelection.overwrite_left_right.value:
    ActionMap.doBind = doBind

##############################################
# This hack maps the keys left and right to seekbarRight and seekbarLeft in the InfobarSeekActions-context

KeymapError = keymapparser.KeymapError
ParseKeys = keymapparser.parseKeys
def parseKeys(context, filename, actionmap, device, keys):
    if context == "InfobarSeekActions":
        if device == "generic":
            for x in keys.findall("key"):
                get_attr = x.attrib.get
                mapto = get_attr("mapto")
                id = get_attr("id")
                if id == "KEY_LEFT":
                    mapto = "seekbarLeft"
                if id == "KEY_RIGHT":
                    mapto = "seekbarRight"
                flags = get_attr("flags")
                flag_ascii_to_id = lambda x: {'m':1,'b':2,'r':4,'l':8}[x]
                flags = sum(map(flag_ascii_to_id, flags))
                assert mapto, "%s: must specify mapto in context %s, id '%s'" % (filename, context, id)
                assert id, "%s: must specify id in context %s, mapto '%s'" % (filename, context, mapto)
                assert flags, "%s: must specify at least one flag in context %s, id '%s'" % (filename, context, id)
                if len(id) == 1:
                    keyid = ord(id) | 0x8000
                elif id[0] == '\\':
                    if id[1] == 'x':
                        keyid = int(id[2:], 0x10) | 0x8000
                    elif id[1] == 'd':
                        keyid = int(id[2:]) | 0x8000
                    else:
                        raise KeymapError("key id '" + str(id) + "' is neither hex nor dec")
                else:
                    try:
                        keyid = KEYIDS[id]
                    except:
                        raise KeymapError("key id '" + str(id) + "' is illegal")
                actionmap.bindKey(filename, device, keyid, flags, context, mapto)
                addKeyBinding(filename, keyid, context, mapto, flags)
        else:
            ParseKeys(context, filename, actionmap, device, keys)
    else:
        ParseKeys(context, filename, actionmap, device, keys)

if config.AdvancedMovieSelection.overwrite_left_right.value:
    keymapparser.parseKeys = parseKeys
    keymapparser.removeKeymap(config.usage.keymap.value)
    keymapparser.readKeymap(config.usage.keymap.value)