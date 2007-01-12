from enigma import eDVBVolumecontrol #this is not nice

from Components.config import config
from Components.Sources.Source import Source

from GlobalActions import globalActionMap

from mytest import VolumeControl

class Volume(Source):
        
    def __init__(self,session,command_default="state"):
        self.cmd = command_default
        Source.__init__(self)
        global globalActionMap # hackalert :)       
        self.actionmap = globalActionMap
        self.volctrl = eDVBVolumecontrol.getInstance() # this is not nice
        #self.volcontrol = VolumeControl(session)
    def handleCommand(self, cmd):
        self.cmd = cmd
        
    def do_func(self):
        list = []
        if self.cmd == "state":
            list.append("state")
        elif self.cmd == "up":
            self.actionmap.actions["volumeUp"]()
            list.append(True)
            list.append("volume changed")
        elif self.cmd == "down":
            self.actionmap.actions["volumeDown"]()
            list.append(True)
            list.append("volume changed")
        elif self.cmd == "mute":
            self.actionmap.actions["volumeMute"]()
            list.append(True)
            list.append("mute toggled")
        elif self.cmd.startswith("set"):
            try:
                targetvol = int(self.cmd[3:])
                if targetvol>100:
                    targetvol = 100
                if targetvol<0:
                    targetvol = 0
                # because we can not set a fix volume in mytest.VolumeControl, we have to do in manualy here
                self.volctrl.setVolume(targetvol,targetvol) 
                #self.volcontrol.volumeDialog.setValue(targetvol)
                #self.volcontrol.volumeDialog.show()
                #self.volcontrol.hideVolTimer.start(3000, True)
                #self.volcontrol.volSave()
                list.append(True)
                list.append("volume set to %i" % targetvol)
            except ValueError: # if cmd was set12NotInt
                list.append(False)
                list.append("wrong parameter format 'set=%s'. Use set=set15 "%self.cmd)
        else:
            list.append(False)
            list.append("unknown Volume command %s" %self.cmd)
        list.append(self.volctrl.getVolume())
        list.append(self.volctrl.isMuted())
        return [list]
    
    list = property(do_func)
    lut = {"Result": 0
           ,"ResultText": 1
           ,"Volume": 2
           ,"isMuted": 3
           }

        