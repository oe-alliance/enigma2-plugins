from enigma import eServiceReference
import os
class StreamPlayer:
    is_playing = False
    
    def __init__(self,session, args = 0):
        print " init StreamPlayer"
        self.session = session
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.session.nav.event.append(self.__event)
    
    def __event(self, ev):
        print "EVENT ==>",ev

    def play(self,stream):
        print " start streaming %s" %stream.getURL()
        if self.is_playing is True:
            self.stop()
            self.play(stream)
        else:
            if stream.getURL().startswith("/") is not True:
                print "playing remote stream",stream.getURL()
                self.session.nav.stopService()
#                sref = eServiceReference("4097:0:0:0:0:0:0:0:0:0:%s"%stream.getURL().replace(":","&colon;"))
#                self.session.nav.playService(sref)
                self.targetfile = "/tmp/streamtarget."+stream.getType().lower() 
                os.system("mknod %s p" %self.targetfile)
                os.system("wget %s -O- > %s&" %(stream.getURL(),self.targetfile))
                self.session.nav.playService(eServiceReference("4097:0:0:0:0:0:0:0:0:0:%s"%self.targetfile))
            else:
                print "playing local stream",stream.getURL()
                esref = eServiceReference("4097:0:0:0:0:0:0:0:0:0:%s"%stream.getURL())
                self.session.nav.playService(esref)
            self.is_playing = True
            
    def stop(self,text=""):
        if self.is_playing is True:
            print " stop streaming",text
            try:
                
                self.session.nav.stopService()
                os.system("killall -9 wget")
                os.system("rm %s" %self.targetfile)
                self.session.nav.playService(self.oldService)
                self.is_playing = False
            except TypeError,e:
                print " ERROR ",e
                self.exit()
        else:
            pass
    def exit(self):
        self.stop()
 