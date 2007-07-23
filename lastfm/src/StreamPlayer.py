from enigma import eServiceReference
from os import system

class StreamPlayer:
    is_playing = False
    
    def __init__(self,session, args = 0):
        print " init StreamPlayer"
        self.session = session
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.session.nav.event.append(self.__event)
        self.onStateChanged = []

    def stateChanged(self):
        for i in self.onStateChanged:
            i()   
 
    def __event(self, ev):
        print "EVENT ==>",ev
        if ev ==6:
            self.stop("got EVENT 6, GST stopped")

    def play(self,stream):
        print " start streaming %s" %stream
        if self.is_playing is True:
            self.stop()
            self.play(stream)
        else:
            if stream.startswith("/") is not True:
                print "playing remote stream",stream
                self.session.nav.stopService()
#                sref = eServiceReference(4097,0,stream )
#                sref = eServiceReference("4097:0:0:0:0:0:0:0:0:0:%s"%stream.replace(":","&colon;"))
#                self.session.nav.playService(sref)
                self.targetfile = "/tmp/lastfm.mp3"
                system("mknod %s p" %self.targetfile)
                system("wget %s -O- > %s&" %(stream,self.targetfile))
                self.session.nav.playService(eServiceReference("4097:0:0:0:0:0:0:0:0:0:%s"%self.targetfile))
            else:
                print "playing local stream",stream
                esref = eServiceReference("4097:0:0:0:0:0:0:0:0:0:%s"%stream)
                self.session.nav.playService(esref)
            self.is_playing = True
        self.stateChanged()
            
    def stop(self,text=""):
        if self.is_playing is True:
            print " stop streaming",text
            self.session.nav.stopService()
            system("killall -9 wget")
            system("rm %s" %self.targetfile)
            self.session.nav.playService(self.oldService)
        self.is_playing = False
        self.stateChanged()
    def exit(self):
        self.stop()
 