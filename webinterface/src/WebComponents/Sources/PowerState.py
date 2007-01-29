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
        
        # 1: poweroff/deepstandby
        # 2: rebootdreambox
        # 3: rebootenigma
        # 4: standby
        
        type = int(self.cmd)
        if type < 0 or type > 4:
            print "PowerState was not defined correctly (%s)" % type
            return [[False,"PowerState was not defined correctly"]]
        
        quitMainloop(type)
        
        return [[True,"PowerState was changed"]]
        
    list = property(do_func)
    lut = {"Result": 0
           ,"ResultText": 1
           }
