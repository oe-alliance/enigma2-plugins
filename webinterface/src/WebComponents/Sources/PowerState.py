from enigma import *
from Components.Sources.Source import Source


class PowerState( Source):
        
    def __init__(self,session):
        self.cmd = []
        self.session = session
        Source.__init__(self)

    def handleCommand(self, cmd):
        self.cmd = cmd
        
    def do_func(self):
        list = []
        
        if self.cmd == "" or self.cmd is None:
            print "the PowerState was not defined (%s)" % self.cmd
            return [[False,"the PowerState was not defined"]]
        
        newState = self.cmd
        print self.cmd
        print "PowerState wurde aufgerufen"
        if newState == "poweroff":
            print "power changing to poweroff"
            quitMainloop(1)
            return [[True,"power changing to poweroff"]]
        elif newState == "rebootenigma":
            print "power changing to rebootenigma"
            quitMainloop(3)
            return [[True,"power changing to rebootenigma"]]
        elif newState == "rebootdreambox":
            print "power changing to rebootdreambox"
            quitMainloop(2)
            return [[True,"power changing to rebootdreambox"]]
        elif newState == "standby":
            print "power changing to standby"
            quitMainloop(4)
            return [[True,"power changing to standby"]]
        else:
            print "the PowerState was not defined"
            return [[False,"the PowerState was not defined"]]
    
    list = property(do_func)
    lut = {"Result": 0
           ,"ResultText": 1
           }
