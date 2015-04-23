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
from __init__ import _
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from VideoColorSpace import VideoColorSpace, initializeConfig
from boxbranding import getImageDistro

def autostart(reason, **kwargs):
    if reason == 0:
        print "[VideoColorSpace] startup..."
        initializeConfig()

def pluginOpen(session, **kwargs):
    session.open(VideoColorSpace)

def startSetup(menuid):
    if getImageDistro() in ('openhdf'):
        if menuid != "video_menu":
            return [ ]
    else:
        if menuid != "system":
            return []
    return [(_("A/V-Color space settings"), pluginOpen, "av_colorspace_setup", 40)]

def Plugins(**kwargs):
    descriptors = []
    if config.usage.setup_level.index >= 2:
        descriptors.append(PluginDescriptor(name=_("Color space setup"), description=_("Setup color space for video"), where=PluginDescriptor.WHERE_SESSIONSTART, fnc=autostart))
        descriptors.append(PluginDescriptor(name=_("Color space setup"), description=_("Setup color space for video"), where=PluginDescriptor.WHERE_MENU, fnc=startSetup))
    return descriptors
