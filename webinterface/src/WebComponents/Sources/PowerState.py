from Components.Sources.Source import Source

class PowerState(Source):
        
    def __init__(self,session):
        self.cmd = []
        self.session = session
        Source.__init__(self)

    def handleCommand(self, cmd):
        self.cmd = cmd
    
    def do_func(self):
        print "PowerState:", self.cmd
        if self.cmd == "" or self.cmd is None:
            print "the PowerState was not defined (%s)" % self.cmd
            return [[False,"the PowerState was not defined"]]
        
        #-1: get current state
        # 0: toggle standby
        # 1: poweroff/deepstandby
        # 2: rebootdreambox
        # 3: rebootenigma
        try:
            type = int(self.cmd)
            if type == -1:
                from Screens.Standby import inStandby
                if inStandby == None:
                    return "false"
                else:
                    return "true"
                
            elif type == 0:
                print "Standby 0"
                from Screens.Standby import inStandby
                if inStandby == None:
                    from Screens.Standby import Standby
                    self.session.open(Standby)
                    return "true"
                else:
                    inStandby.Power()
                    return "false"
                
            elif 0 < type < 4:
                print "TryQuitMainloop if"
                from Screens.Standby import TryQuitMainloop
                self.session.open(TryQuitMainloop, type)
                return "true"
            else:
                print "PowerState was not defined correctly (%s)" % type
                return "error"
        except ValueError:
            return "error"
        
    text = property(do_func)