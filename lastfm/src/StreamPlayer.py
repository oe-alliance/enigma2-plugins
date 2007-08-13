from enigma import eServiceReference
from os import system
from math import ceil
import time 
class StreamPlayer:
    STATE_PLAYINGSTARTED = 0
    STATE_STOP = 1
    STATE_PLAYLISTENDS = 2
    is_playing = False
    trackstarttime = 0
    currentplaylistitemnumber = 0
    playlist = None
    
    def __init__(self,session, args = 0):
        print " init StreamPlayer"
        self.session = session
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.session.nav.event.append(self.__event)
        self.onStateChanged = []
    
    def setPlaylist(self,playlist):
        if self.playlist is not None:
            self.currentplaylistitemnumber = 0 
        self.playlist = playlist
        
    def stateChanged(self,reason):
        for i in self.onStateChanged:
            i(reason)   
 
    def __event(self, ev):
        print "EVENT ==>",ev
        if ev == 6:
            self.stop("got EVENT 6, GST stopped")
        if ev == 4:
            self.trackstarttime = time.time()

    def getRemaining(self):
        remaining = int((self.playlist.getTrack(self.currentplaylistitemnumber)["duration"]/1000) - (time.time() - self.trackstarttime))
        minutes = int(remaining/60)
        seconds = int(remaining-(minutes*60))
        def shiftchars(integer,char):
            if integer in range(0,10):
                return char+str(integer)
            else:
                return str(integer)
        return "-%s:%s"%(shiftchars(minutes," "), shiftchars(seconds,"0"))
    
    def play(self,tracknumber=False):
        self.session.nav.stopService()
            
        if tracknumber is False:
            self.currentplaylistitemnumber = 0 
        else:
            self.currentplaylistitemnumber = tracknumber
        
        track = self.playlist.getTrack(self.currentplaylistitemnumber)
        
        if track['location'] != "no location":
            print "playing item "+str(self.currentplaylistitemnumber) +"/"+str(self.playlist.length)+" with url ",track['location']
            self.session.nav.stopService()
            self.targetfile = "/tmp/lastfm.mp3"
            system("mknod %s p" %self.targetfile)
            system("wget %s -O- > %s&" %(track['location'],self.targetfile))
            self.session.nav.playService(eServiceReference("4097:0:0:0:0:0:0:0:0:0:%s"%self.targetfile))
        self.is_playing = True

    def skip(self):
        self.stop()
                
    def stop(self,text="",force=False):
        if self.playlist is None:
            self.is_playing = False
            self.stateChanged(self.STATE_STOP)
        elif force is False and self.playlist.length > 0 and (self.playlist.length-1) > self.currentplaylistitemnumber:
            self.play(tracknumber=self.currentplaylistitemnumber+1)
            self.stateChanged(self.STATE_PLAYINGSTARTED)
        elif self.is_playing is True and force is True:
            self.session.nav.stopService()
            system("killall -9 wget")
            system("rm %s" %self.targetfile)
            self.session.nav.playService(self.oldService)
            self.is_playing = False
            self.stateChanged(self.STATE_STOP)
            
        else:
            self.stateChanged(self.STATE_PLAYLISTENDS)
            
    def exit(self):
        self.stop()
    
    def getMetadata(self,key):
        try:
            track = self.playlist.getTrack(self.currentplaylistitemnumber)
            return track[key]
        except:
            return "N/A"