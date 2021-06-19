#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2011 cmikula
#
#    In case of reuse of this source code please do not remove this copyright.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    For more information on the GNU General Public License see:
#    <http://www.gnu.org/licenses/>.
#
#    For example, if you distribute copies of such a program, whether gratis or for a fee, you
#    must pass on to the recipients the same freedoms that you received. You must make sure
#    that they, too, receive or can get the source code. And you must show them these terms so they know their rights.
#

from __future__ import print_function
from Tools.Directories import fileExists
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN, SCOPE_CONFIG
from shutil import copyfile

if fileExists(resolveFilename(SCOPE_CURRENT_PLUGIN, "Bp/geminimain/plugin.pyo")):
    __CONF__ = resolveFilename(SCOPE_CONFIG, "gemini_DateiBrowser.conf")
else:
    __CONF__ = resolveFilename(SCOPE_CONFIG, "AdvancedMovieSelection.conf")

if not fileExists(__CONF__):
    copyfile(resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/AdvancedMovieSelection/AdvancedMovieSelection.conf"), __CONF__)
DMCONFFILE = __CONF__


class MovieConfig:
    def __init__(self):
        self.readDMconf()

    def readDMconf(self):
        self.hidelist = []
        self.hotplug = []
        self.rename = []
        try:
            rfile = open(DMCONFFILE, 'r')
            for x in rfile.readlines():
                val = x.strip()
                if val.startswith('#'):
                    self.hotplug.append(val[1:])
                elif val.startswith('%'):
                    self.rename.append(val[1:])
                else:
                    self.hidelist.append(val)
            rfile.close()
        except:
            pass

    def isHidden(self, name):
        return name in self.hidelist

    def isHiddenHotplug(self, name):
        return name in self.hotplug

    def getRenamedName(self, name):
        try:
            for item in self.rename:
                i = item.split("\t")
                if i[0] == name:
                    return i[1]
        except:
            pass
        return name

    def safe(self):
        try:
            f = open(DMCONFFILE, 'w')
            for x in self.hidelist:
                f.write(x + "\r\n")
            for x in self.hotplug:
                f.write('#' + x + "\r\n")
            for x in self.rename:
                f.write('%' + x + "\r\n")
            f.close()
        except Exception, e:
            print(e)
