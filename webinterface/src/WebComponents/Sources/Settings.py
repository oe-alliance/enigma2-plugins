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
        
        list.append([config.recording.margin_before.value, 'config.recording.margin_before'])
        list.append([config.recording.margin_after.value, 'config.recording.margin_after'])
        
        list.append([config.ParentalControl.servicepinactive.value, 'config.ParentalControl.servicepinactive'])
        list.append([config.ParentalControl.setuppin.value, 'config.ParentalControl.setuppin'])
        list.append([config.ParentalControl.servicepin[0].value, 'config.ParentalControl.servicepin.0'])
        list.append([config.ParentalControl.configured.value, 'config.ParentalControl.configured'])
        list.append([config.ParentalControl.setuppinactive.value, 'config.ParentalControl.setuppinactive'])
        list.append([config.ParentalControl.type.value, 'config.ParentalControl.type'])

        print "Settings was was sent (%s)" % type
        return list


    list = property(do_func)
    lut = {"Value": 0
           ,"Name": 1           
           }