from Components.Converter.Converter import Converter
from enigma import eDVBVolumecontrol #this is not nice

class VolumeToText(Converter, object):
    
    def __init__(self, type):
        Converter.__init__(self, type)
        self.volctrl = eDVBVolumecontrol.getInstance() # this is not nice
        
    def getHTML(self, id):
        return self.getText() # encode & etc. here!
    def getText(self):
        r = "%s\n"%config.audio.volume.value
        if self.volctrl.isMuted():
            r+="muted"
        else:
            r+="notmuted"
        return r
        

    text = property(getText)
