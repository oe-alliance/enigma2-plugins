import re,datetime,md5
from twisted.internet import reactor

from enigma import iServiceInformation,iPlayableService
from Components.config import config

import httpclient


class LastFMScrobbler(object):
    client     = "tst" # this must be changed to a own ID
    version    = "1.0"
    host        = "post.audioscrobbler.com"
    port       = 80
    loggedin  = False # indicates, if we are logged in

    def __init__(self,user,password):
        self.user = user
        self.password = password
        self.tracks2Submit = []
    
    def addTrack2Submit(self,track):
        self.tracks2Submit.append(track)
    
    def removeTrack2Submit(self,track):
        self.tracks2Submit.remove(track)
        
    def handshake(self):
        print "[LastFMScrobbler] try logging into lastfm-submission-server"
        url = "http://"+self.host+":"+str(self.port)+"?"+httpclient.urlencode({
            "hs":"true",
            "p":"1.1",
            "c":self.client,
            "v":self.version,
            "u":self.user
            })
        httpclient.getPage(self.host,self.port,url,method="GET",callback=self.handshakeCB,errorback=self.handshakeCBError)
    
    def handshakeCBError(self,data): 
        self.failed(data.split("\n"))

    def handshakeCB(self,data): 
        result = data.split("\n")   
        if result[0].startswith("BADUSER"):
            return self.baduser(result[1:])
        if result[0].startswith("UPTODATE"):
            return self.uptodate(result[1:])
        if result[0].startswith("FAILED"):
            return self.failed(result)

    def uptodate(self,lines):
        self.md5 = re.sub("\n$","",lines[0])
        self.submiturl = re.sub("\n$","",lines[1])
        self.loggedin = True
        
    def baduser(self,lines):
        print "[LastFMScrobbler] Bad user"
        
    def failed(self,lines):
        print "[LastFMScrobbler] FAILED",lines[0]
           
    def submit(self):
        if self.loggedin is False:
            print "[LastFMScrobbler] Submitting cancled, because not logged in"
            return False
        tracks = self.tracks2Submit
        print "[LastFMScrobbler] Submitting ",len(tracks)," tracks"
        md5response = md5.md5(md5.md5(self.password).hexdigest()+self.md5).hexdigest()
        post = "u="+self.user+"&s="+md5response
        count = 0
        for track in tracks:
            post += "&"
            post += track.urlencoded(count)
            count += 1
        (host,port) = self.submiturl.split("/")[2].split(":")
        url = "/"+"/".join(self.submiturl.split("/")[3:])+"?"+post
        httpclient.getPage(host,int(port),url,method="POST",callback=self.submitCB,errorback=self.submitCBError)
        
    def submitCBError(self,data):
        self.failed(data.split("\n"))
        
    def submitCB(self,data):
        results = data.split("\n")
        if results[0].startswith("OK"):
            print "[LastFMScrobbler] Submitting successful"
            self.tracks2Submit = []
        if results[0].startswith("FAILED"):
            print "[LastFMScrobbler] Submitting failed,",results[0]
            self.failed([results[0],"INTERVAL 0"])

############

class Track(object):
    def __init__(self,artist,name,album,length=-1,mbid=None,tracktime=None):
        self.params = {}
        self.artist = artist
        self.name = name
        self.album = album
        self.length = length
        self.mbid = mbid
        self.tracktime = tracktime
        self.date = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
    def __repr__(self):
        return "'"+self.name+"' by '"+self.artist+"' from '"+self.album+"' with length of "+str(self.length)+" sec."

    def urlencoded(self,num):
        encode = ""
        encode += "a["+str(num)+"]="+httpclient.quote_plus(self.artist)
        encode += "&t["+str(num)+"]="+httpclient.quote_plus(self.name)
        if self.length is not None:
            encode += "&l["+str(num)+"]="+httpclient.quote_plus(str(self.length))
        else:
            encode += "&l["+str(num)+"]="            
        encode += "&i["+str(num)+"]="+httpclient.quote_plus(self.date)
        if self.mbid is not None:
            encode += "&m["+str(num)+"]="+httpclient.quote_plus(self.mbid)
        else:
            encode += "&m["+str(num)+"]="
        encode += "&b["+str(num)+"]="+httpclient.quote_plus(self.album)
        return encode
##########
class EventListener:
    time2wait4submit = 30
    
    def __init__(self,session):
        self.session = session
        self.tracks_checking_for = []
        self.scrobbler = LastFMScrobbler(config.plugins.LastFM.username.value,config.plugins.LastFM.password.value)
        self.scrobbler.handshake()
        
    def onEvent(self,event):
        if event == iPlayableService.evUpdatedInfo:
            track = self.getCurrentServiceType()
            try:
                self.tracks_checking_for.index(str(track))
            except ValueError,e:
                if track is not False:
                    self.tracks_checking_for.append(str(track))
                    if track.length < self.time2wait4submit:
                        waittime = self.time2wait4submit
                    else:
                        waittime = track.length/2
                    print "[LastFMScrobbler] waiting",waittime,"sec. until checking if the track '"+str(track)+"' is still playing"
                    reactor.callLater(waittime, self.checkTrack, track)

    def startListenToEvents(self):
        self.session.nav.event.append(self.onEvent)

    def stopListentoEvents(self):
        self.session.nav.event.remove(self.onEvent)
    
    def getCurrentServiceType(self):
        currPlay = self.session.nav.getCurrentService()
        sref=self.session.nav.getCurrentlyPlayingServiceReference()
        if sref is None:
            print "[LastFMScrobbler] CurrentlyPlayingServiceReference is None, not submitting to LastFM"
            return False
        elif sref.toString().startswith("4097:0:0:0:0:0:0:0:0:0:") is not True:
            print "[LastFMScrobbler] CurrentlyPlayingServiceReference is not a File, not submitting to LastFM"
            return False
        elif sref.toString().endswith("lastfm.mp3") is True:
            print "[LastFMScrobbler] LastFm-Plugin is playing, not submitting"
            return False
        elif currPlay is not None:
            tracklength = -1
            seek = currPlay and currPlay.seek()
            if seek != None:
                r= seek.getLength()
                if not r[0]:
                    tracklength = r[1] / 90000
            return self.getTrack( artist = currPlay.info().getInfoString(iServiceInformation.sArtist),
                                  title = currPlay.info().getInfoString(iServiceInformation.sTitle),
                                  album = currPlay.info().getInfoString(iServiceInformation.sAlbum),
                                  length = tracklength,
                                 )
             
             
    def getTrack(self , artist = None, title = None, album = None,length=-1):
        if artist == "" or artist is None:
            print "[LastFMScrobbler] CurrentlyPlayingServiceReference has no Artist, not submitting to LastFM"
            return False
        elif title == "" or title is None:
            print "[LastFMScrobbler] CurrentlyPlayingServiceReference has no Tracktitle, not submitting to LastFM"
            return False
        else:
            return Track(artist,title,album,length=length)
            
    
    def checkTrack(self,track):
        trackcurrent = self.getCurrentServiceType()
        if str(track) == str(trackcurrent):
            print "[LastFMScrobbler] sending track to lastfm as now playing... "+str(track)
            self.scrobbler.addTrack2Submit(track)
            self.scrobbler.submit()
            self.tracks_checking_for.remove(str(track))
        else:
            print "[LastFMScrobbler] track is not playing, skipping sending "+str(track)
            