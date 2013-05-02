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

from Components.AVSwitch import AVSwitch
from enigma import ePicLoad

class PicLoader:
    def __init__(self, width, height, sc=None):
        self.picload = ePicLoad()
        if(not sc):
            sc = AVSwitch().getFramebufferScale()
        self.picload.setPara((width, height, sc[0], sc[1], False, 1, "#00000000"))

    def load(self, filename):
        self.picload.startDecode(filename, 0, 0, False)
        data = self.picload.getData()
        return data
    
    def destroy(self):
        del self.picload

