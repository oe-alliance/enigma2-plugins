from enigma import eServiceReference
from sys import exc_info

class StreamPlayer:
    is_playing = False
    
    def __init__(self,session, args = 0):
        print " init StreamPlayer"
        self.is_playing = False
        self.session = session
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.session.nav.event.append(self.__event)
    
    def __event(self, ev):
        print "[NETcaster] EVENT ==>",ev

    def play(self,stream):
        try:
            print "[NETcaster] start streaming %s" %stream.getURL()
            if self.is_playing:
                self.stop()
            url = stream.getURL()
            if not url:
            	print "no URL provided for play"
            	return
            print "playing stream", url
            esref = eServiceReference("4097:0:0:0:0:0:0:0:0:0:%s" % url.replace(':', '%3a'))
            self.session.nav.playService(esref)
            self.is_playing = True
        except:
            print "[NETcaster] Failed to start: %s: %s" % exc_info()[:2]

    def stop(self,text=""):
        if self.is_playing:
            print "[NETcaster] stop streaming",text
            try:
                self.is_playing = False
                self.session.nav.stopService()
                self.session.nav.playService(self.oldService)
            except TypeError,e:
                print " ERROR ",e
                self.exit()

    def exit(self):
        self.stop()

