from Plugins.Extensions.Widgets.Widget import Widget
from enigma import ePicLoad, ePixmap, getDesktop, eTimer
from Components.Pixmap import Pixmap
from twisted.web.client import downloadPage
from urllib import quote_plus
from os import remove as os_remove, mkdir as os_mkdir
from os.path import isdir as os_path_isdir, isfile as os_isfile

from Components.AVSwitch import AVSwitch
def getAspect():
    val = AVSwitch().getAspectRatioSetting()
    if val == 0 or val == 1:
        r = (5*576, 4*720)
    elif val == 2 or val == 3 or val == 6:
        r = (16*720, 9*1280)
    elif val == 4 or val == 5:
        r = (16*576, 10*720)
    return r

class WebPixmap(Pixmap):
    def __init__(self, default=None):
        Pixmap.__init__(self)
        self.picload = ePicLoad()
        self.picload.PictureData.get().append(self.setPixmapCB)
        self.cachedir = "/tmp/"
        self.default = default

    def onShow(self):
        Pixmap.onShow(self)
        sc = getAspect()
        resize = 1
        background = '#ff000000'
        self.picload.setPara((self.instance.size().width(), self.instance.size().height(), sc[0], sc[1], False, resize, background))

    def load(self, url=None):
        tmpfile = ''.join((self.cachedir, quote_plus(url), ''))
        if os_path_isdir(self.cachedir) is False:
            print "cachedir not existing, creating it"
            os_mkdir(self.cachedir)
        if os_isfile(tmpfile):
            self.tmpfile = tmpfile
            self.onLoadFinished(None)
        elif url is not None:
            self.tmpfile = tmpfile
            head = {}
            agt = "Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.0.2) Gecko/2008091620 Firefox/3.0.2"
            downloadPage(url,self.tmpfile,headers=head,agent=agt).addCallback(self.onLoadFinished).addErrback(self.onLoadFailed)
        elif self.default:
            self.picload.startDecode(self.default)

    def onLoadFinished(self,result):
        self.picload.startDecode(self.tmpfile)

    def onLoadFailed(self,error):
        print "WebPixmap:onLoadFAILED", error
        if self.default and self.instance:
            print "showing 404", self.default
            self.picload.startDecode(self.default)
        if os_isfile(self.tmpfile):
            os_remove(self.tmpfile)

    def setPixmapCB(self, picInfo=None):
        if os_isfile(self.tmpfile):
            os_remove(self.tmpfile)
        ptr = self.picload.getData()
        if ptr and self.instance:
            self.instance.setPixmap(ptr)
        

class ImageswitchWidget(Widget):
    def __init__(self,session):
        Widget.__init__(self,session,name="Image Switch Widget",description="Example of a simple Widget images from the web",version="0.1",author="3c5x9",homepage="cvs://schwerkraft")
        self.elements["imageswitch_pixmap"] = WebPixmap()
        self.Timer = eTimer()
        self.Timer.callback.append(self.TimerFire)
        self.last = False
       
    def onLoadFinished(self,instance):
        self.instance = instance
        self.TimerFire()
        
    def onClose(self):
        self.Timer.stop()
        
    def TimerFire(self):
        if self.last:
            self.getElement("imageswitch_pixmap").load("http://www.google.de/intl/de_de/images/logo.gif")
            self.last = False
        else:
            self.getElement("imageswitch_pixmap").load("http://maps.google.de/intl/de_de/images/maps_small_horizontal_logo.png")
            self.last = True
            
        self.Timer.start(5000)

        
def get_widget(session):
    return ImageswitchWidget(session)
