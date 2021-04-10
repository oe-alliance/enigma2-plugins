#!/usr/bin/python
# -*- coding: utf-8 -*- 
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  Coded by cmikula (c)2013
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
import os
from .Globals import printStackTrace
from .MovieConfig import MovieConfig
from ServiceProvider import eServiceReferenceHotplug
from enigma import eTimer


class Hotplug():
    NTFS_3G_DRIVER_DELAY = 3000

    def __init__(self):
        self.notifier = []
        self.hotplugServices = []
        self.hotplug_timer = eTimer()
        self.hotplug_timer.callback.append(self.updateHotplugDevices)
        self.addHotplugNotifier()
        self.hotplugChanged()

    def addHotplugNotifier(self):
        from Plugins.SystemPlugins.Hotplug.plugin import hotplugNotifier
        if not self.hotplugNotifier in hotplugNotifier:
            print("add hotplugNotifier") 
            hotplugNotifier.append(self.hotplugNotifier)
        
    def removeHotplugNotifier(self):
        from Plugins.SystemPlugins.Hotplug.plugin import hotplugNotifier
        if self.hotplugNotifier in hotplugNotifier:
            print("remove hotplugNotifier") 
            hotplugNotifier.remove(self.hotplugNotifier)
    
    def hotplugNotifier(self, dev, media_state):
        print("[hotplugNotifier]", dev, media_state)
        if len(dev) > 2 and dev[0:2] in ("sd") and dev[-1].isdigit():
            if media_state == "add":
                self.hotplugChanged(self.NTFS_3G_DRIVER_DELAY)
            else:
                self.hotplugChanged(200)

    def hotplugChanged(self, delay=200):
        print("[start hotplugNotifier]", str(delay) + "ms")
        self.hotplug_timer.start(delay, True)

    def updateHotplugDevices(self):
        self.hotplugServices = []
        print("[update hutplug]")
        try:
            from Components.Harddisk import Harddisk
            import commands
            movieConfig = MovieConfig()
            lines = commands.getoutput('mount | grep /dev/sd').split('\n')
            print(lines)
            for mount in lines:
                if len(mount) < 2:
                    continue
                m = mount.split(' type')[0].split(' on ')
                m_dev, m_path = m[0], m[1]
                label = os.path.split(m_path)[-1]
                blkid = commands.getoutput('blkid ' + m_dev).split("\"")
                if len(blkid) > 2 and blkid[1]:
                    label = blkid[1]
                if os.path.normpath(m_path) == "/media/hdd" or label in ("DUMBO", "TIMOTHY"):
                    continue
                if not movieConfig.isHiddenHotplug(label):
                    if m_path[-1] != "/":
                        m_path += "/"
                    service = eServiceReferenceHotplug(m_path)
                    hdd = Harddisk(m_dev.replace("/dev/", "")[:-1])
                    if label:
                        label += " - "
                    service.setName(label + hdd.model() + " - " + hdd.capacity())
                    self.hotplugServices.append(service)
            
            for callback in self.notifier:
                try:
                    callback()
                except:
                    printStackTrace()
        except:
            printStackTrace()
    
    def getHotplugServices(self):
        return self.hotplugServices


hotplug = Hotplug()
