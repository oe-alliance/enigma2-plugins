from enigma import loadPic
from enigma import eTimer

from Screens.Screen import Screen
from Components.AVSwitch import AVSwitch
from Components.config import config
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from twisted.web.client import downloadPage

class PictureScreen(Screen):
    skin = ""
    prozessing =False # if fetching or converting is active
    autoreload =False
    def __init__(self, session,title,filename, slideshowcallback = None,args=0):
        self.session=session
        self.slideshowcallback=slideshowcallback
        self.screentitle = title
        self.skin = """
        <screen position="0,0" size="720,576" title="%s" flags=\"wfNoBorder\">
             <widget name="pixmap" position="0,0" size="720,576" backgroundColor=\"black\"/>
        </screen>""" % (filename)
        Screen.__init__(self, session)
        self.filename = filename
        self["pixmap"] = Pixmap()
        
        self["actions"] = ActionMap(["WizardActions", "DirectionActions","ChannelSelectBaseActions","ShortcutActions"], 
            {
             "ok": self.do,
             "back": self.exit,
             "green":self.AutoReloaderSwitch,
             }, -1)
        
        self.onLayoutFinish.append(self.do)
        
    def AutoReloaderSwitch(self):
        if self.filename.startswith("http") or self.filename.startswith("ftp"):            
            if self.autoreload is False:
                self.autoreload = True
                self.do()
            else:
                self.autoreload = False
            
    def do(self): 
        if self.prozessing:
            pass       
        elif self.filename.startswith("http") or self.filename.startswith("ftp"):            
            self.fetchFile(self.filename)
        else:
            self.sourcefile = self.filename
            self.setPicture(self.filename)

    def exit(self):
        self.cleanUP()
        self.close()

    def cleanUP(self):
        try:
            if os.path.exists("/tmp/loadedfile"):
                os.remove("/tmp/loadedfile")
        except:## OSerror??
            pass
    
    def fetchFile(self,url):
        self.prozessing =True        
        self.setTitle("loading File")
        print "fetching URL ",url
        self.sourcefile = "/tmp/loadedfile"
        downloadPage(url,self.sourcefile).addCallback(self.fetchFinished).addErrback(self.fetchFailed)
            
        
    def fetchFailed(self,string):
        print "fetch failed",string
        self.setTitle( "fetch failed: "+string)
        
    def fetchFinished(self,string):
        print "fetching finished "
        self.setPicture(self.sourcefile)   
              
    def setPicture(self,string):
        self.setTitle(self.filename.split("/")[-1])        
        pixmap = loadPic(string,720,576, AVSwitch().getAspectRatioSetting()/2,1, 0,1)
        if pixmap is not None:
            self["pixmap"].instance.setPixmap(pixmap)
        self.prozessing =False
        
        if self.autoreload is True:
                self.cleanUP()
                self.do()
        elif self.slideshowcallback is not None:
                self.closetimer = eTimer()
                self.closetimer.timeout.get().append(self.slideshowcallback)
                print "waiting ",config.plugins.pictureviewer.slideshowtime.value," seconds for next picture"
                self.closetimer.start(int(config.plugins.pictureviewer.slideshowtime.value))
        
