from enigma import *

import os
import struct
from struct import *

from Components.Sources.Source import Source

class RemoteControl( Source):
        
    def __init__(self,session):
        self.cmd = []
        self.session = session
        Source.__init__(self)

    def handleCommand(self, cmd):
        self.cmd = cmd
        
    def do_func(self):
        list = []
        
        print "RemoteControl wurde aufgerufen ",self.cmd
        
        if self.cmd == "" or self.cmd is None:
            print "the RemoteControl was not defined (%s)" % self.cmd
            return [[False,"the RemoteControl was not defined"]]
        
        type = int(self.cmd)
        if type <= 0:
            print "the command was not greater 0 (%s)" % type
            return [[False,"the command was not greater 0"]]
        
        dataon  = struct.pack('iiHHi',0,0,1,type,1)
        dataoff  = struct.pack('iiHHi',0,0,1,type,0)
        
        fp=open("/dev/input/event1", 'wb')
        
        fp.write(dataon)    
        
        fp.write(dataoff)    
        
        fp.close()
        
        print "command was was sent (%s)" % type
        return [[True,"command was was sent"]]


    list = property(do_func)
    lut = {"Result": 0
           ,"ResultText": 1
           }