###############################################################################
# Copyright (c) 2008 Rico Schulte, 3c5x9. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
###############################################################################

from enigma import loadPic,ePixmap, getDesktop 
from Components.Pixmap import Pixmap
from twisted.web.client import downloadPage
from urllib import quote_plus
from os import remove as os_remove, mkdir as os_mkdir
from os.path import isdir as os_path_isdir, isfile as os_isfile

from Components.AVSwitch import AVSwitch

def getAspect():
    val = AVSwitch().getAspectRatioSetting()
    if val == 0:
        r = 3
    elif val == 1:
        r = 3
    elif val == 2:
        r = 1
    elif val == 3:
        r = 1
    elif val == 4:
        r = 2
    elif val == 5:
        r = 2
    elif val == 6:
        r = 1
    return r

class WebPixmap(Pixmap):
    def __init__(self,url=None,text=""):
        self.url = url
        self.default = "/usr/lib/enigma2/python/Plugins/Extensions/GoogleMaps/404.png"
        self.cachedir = "/tmp/googlemaps/"
        Pixmap.__init__(self)

    def load(self,url=None):
        self.url = url
        tmpfile = self.cachedir+quote_plus(url)+".jpg"
        if os_path_isdir(self.cachedir) is False:
            print "cachedir not existing, creating it"
            os_mkdir(self.cachedir)
        if os_isfile(tmpfile):
            self.tmpfile = tmpfile
            self.onLoadFinished(None)
        elif url is not None:
            self.tmpfile = tmpfile
            head = {
                       "Accept":"image/png,image/*;q=0.8,*/*;q=0.5",
                       "Accept-Language":"de",
                       "Accept-Encoding":"gzip,deflate",
                       "Accept-Charset":"ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                       "Keep-Alive":"300",
                       "Referer":"http://maps.google.de/",
                       "Cookie:": "khcookie=fzwq1BaIQeBvxLjHsDGOezbBcCBU1T_t0oZKpA; PREF=ID=a9eb9d6fbca69f5f:TM=1219251671:LM=1219251671:S=daYFLkncM3cSOKsF; NID=15=ADVC1mqIWQWyJ0Wz655SirSOMG6pXP2ocdXwdfBZX56SgYaDXNNySnaOav-6_lE8G37iWaD7aBFza-gsX-kujQeH_8WTelqP9PpaEg0A_vZ9G7r50tzRBAZ-8GUwnEfl",
                       "Connection":"keep-alive"
                       }
            agt = "Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.0.2) Gecko/2008091620 Firefox/3.0.2"
            downloadPage(url,self.tmpfile,headers=head,agent=agt).addCallback(self.onLoadFinished).addErrback(self.onLoadFailed)
        else:
            if self.default is not None:
                self.setPixmapFromFile(self.default)

    def onLoadFinished(self,result):
        self.setPixmapFromFile(self.tmpfile)
        if os_isfile(self.tmpfile):
            os_remove(self.tmpfile)
        
    def onLoadFailed(self,error):
        print "WebPixmap:onLoadFAILED",error
        if self.default is not None:
            self.setPixmapFromFile(self.default)
        if os_isfile(self.tmpfile):
            os_remove(self.tmpfile)
    
    def setPixmapFromFile(self,file):
        if self.instance is not None:
            h = self.instance.size().height()
            w = self.instance.size().width()
            aspect = getAspect()
            resize = 1
            rotate = 0
            background = 1
            self.pixmap = loadPic(file, w,h,aspect,resize, rotate,background)
            if self.pixmap is not None:
                self.instance.setPixmap(self.pixmap.__deref__())
                
              