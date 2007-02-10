from enigma import *

from Components.config import config

import os
import struct
from struct import *

from Components.Sources.Source import Source

class Settings( Source):
        
    def __init__(self,session):
        self.cmd = []
        self.session = session
        Source.__init__(self)

    def handleCommand(self, cmd):
        self.cmd = cmd
        
    def do_func(self):
        list = []
        
        print "Settings wurde aufgerufen ",self.cmd
        #list.append([config.plugins.Webinterface.enable.value, 'config.plugins.Webinterface.enable'])
        #list.append([config.plugins.Webinterface.password.value, 'config.plugins.Webinterface.password'])
        #list.append([config.plugins.Webinterface.includehdd.value, 'config.plugins.Webinterface.includehdd'])
        list.append([config.recording.margin_before.value, 'config.recording.margin_before'])
        list.append([config.recording.margin_after.value, 'config.recording.margin_after'])
        
        print "Settings was was sent (%s)" % type
        print list
        return list


    list = property(do_func)
    lut = {"Value": 0
           ,"Name": 1           
           }