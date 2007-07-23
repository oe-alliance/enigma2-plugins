from Components.Sources.Source import Source

class PowerState(Source):
        
    def __init__(self,session):
        self.cmd = []
        self.session = session
        Source.__init__(self)

    def handleCommand(self, cmd):
        self.cmd = cmd
        print "PowerState:",self.cmd
        if self.cmd == "" or self.cmd is None:
            print "the PowerState was not defined (%s)" % self.cmd
            return [[False,"the PowerState was not defined"]]
        
        # 1: poweroff/deepstandby
        # 2: rebootdreambox
        # 3: rebootenigma
        # 4: standby
        
        type = int(self.cmd)
        if type == 0:
            print "Standby if"
            from Screens.Standby import Standby
            self.session.open(Standby)
        elif type < 4:
            print "TryQuitMainloop if"
            from Screens.Standby import TryQuitMainloop
            self.session.open(TryQuitMainloop, type)
        else:
            print "PowerState was not defined correctly (%s)" % type

        #quitMainloop(type)