#!/usr/bin/python
# -*- coding: utf-8 -*- 
#  VideoColorSpace for Dreambox-Enigma2
#
#  Coded by cmikula (c)2012
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
import commands
from os import system

from .__init__ import _
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry, config, ConfigSubsection, ConfigSelection
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen

def getColorSpace():
    mode = commands.getoutput('cat /proc/stb/video/hdmi_colorspace')
    print("[VideoColorSpace] current hdmi_colorspace:", mode)
    return mode

def setColorSpace(mode):
    print("[VideoColorSpace] set hdmi_colorspace:", mode)
    result = system("echo %s > /proc/stb/video/hdmi_colorspace" % (mode)) >> 8
    if result != 0:
        print("[VideoColorSpace] error setting hdmi_colorspace")
        getColorSpace()

def initializeConfig():
    modes = commands.getoutput('cat /proc/stb/video/hdmi_colorspace_choices').split()
    config.VideoColorSpace = ConfigSubsection()
    config.VideoColorSpace.color_space = ConfigSelection(modes, "None")
    value = config.VideoColorSpace.color_space.value
    if value != getColorSpace() and value != "None":
        setColorSpace(value)

class VideoColorSpace(Screen, ConfigListScreen):
    skin = """
        <screen name="VideoColorSpace" position="center,center" size="560,440" title="Video color space setup">
            <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
            <widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
            <widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
            <widget name="config" position="5,50" size="550,350" scrollbarMode="showOnDemand" />
        </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)

        self.session = session
        self.onChangedEntry = []
        self.current_mode = getColorSpace()
        config.VideoColorSpace.color_space.value = self.current_mode
        config.VideoColorSpace.color_space.save()

        l = []
        l.append(getConfigListEntry(_("Mode:"), config.VideoColorSpace.color_space))
        ConfigListScreen.__init__(self, l, session=self.session)

        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
            {
                "cancel": self.cancel,
                "save": self.save,
            }, -2)

        self["key_red"] = StaticText(_("Cancel"))
        self["key_green"] = StaticText(_("OK"))

        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self.setTitle(_("Color space setup"))

    def save(self):
        config.VideoColorSpace.color_space.save()
        self.close()

    def cancel(self):
        if config.VideoColorSpace.color_space.isChanged():
            setColorSpace(self.current_mode)
        self.keyCancel()
        config.VideoColorSpace.color_space.value = self.current_mode

    def newColorSpaceFromConfig(self):
        current = self["config"].getCurrent()
        mode = current[1].getValue()
        setColorSpace(mode)

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.newColorSpaceFromConfig()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.newColorSpaceFromConfig()
