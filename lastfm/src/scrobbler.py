import socket,urllib,urllib2,re,time,datetime,md5
from twisted.internet import reactor

from enigma import iServiceInformation
from Components.config import config



class LastFMScrobbler(object):
    client="tst" # this must be changed to a own ID
    version="1.0"
    url="http://post.audioscrobbler.com/"

    def __init__(self,user,password):
        self.user = user
        self.password = password

    def handshake(self):
        url = self.url+"?"+urllib.urlencode({
            "hs":"true",
            "p":"1.1",
            "c":self.client,
            "v":self.version,
            "u":self.user
            })
        result = urllib2.urlopen(url).readlines()
        if result[0].startswith("BADUSER"):
            return self.baduser(result[1:])
        if result[0].startswith("UPTODATE"):
            return self.uptodate(result[1:])
        if result[0].startswith("FAILED"):
            return self.failed(result)

    def uptodate(self,lines):
        self.md5 = re.sub("\n$","",lines[0])
        self.submiturl = re.sub("\n$","",lines[1])
        self.interval(lines[2])
    def baduser(self,lines):
        print "Bad user"
    def failed(self,lines):
        print "FAILD",lines[0]
        self.interval(lines[1])
    def interval(self,line):
        match = re.match("INTERVAL (\d+)",line)
        if match is not None:
            print "[audioscrobbler] Sleeping for",match.group(1),"secs"
            #time.sleep(int(match.group(1)))
            
    def submit(self,tracks):
        print "[audioscrobbler] Submitting"
        md5response = md5.md5(md5.md5(self.password).hexdigest()+self.md5).hexdigest()
        post = "u="+self.user+"&s="+md5response
        count = 0
        for track in tracks:
            post += "&"
            post += track.urlencoded(count)
            count += 1
        post = unicode(post)
        result = urllib2.urlopen(self.submiturl,post)
        results = result.readlines()
        print results
        if results[0].startswith("OK"):
            print "OK"
            self.interval(results[1])
        if results[0].startswith("FAILED"):
            self.failed([results[0],"INTERVAL 0"])

############

class Track(object):
    def __init__(self,artist,name,album,length=232,mbid=None,tracktime=None):
        self.params = {}
        self.artist = artist
        self.name = name
        self.album = album
        self.length = length
        self.mbid = mbid
        self.tracktime = tracktime
        self.date = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
    def __repr__(self):
        return "'"+self.name+"' by '"+self.artist+"' from '"+self.album+"'"

    def urlencoded(self,num):
        encode = ""
        encode += "a["+str(num)+"]="+urllib.quote_plus(self.artist)
        encode += "&t["+str(num)+"]="+urllib.quote_plus(self.name)
        if self.length is not None:
            encode += "&l["+str(num)+"]="+urllib.quote_plus(str(self.length))
        else:
            encode += "&l["+str(num)+"]="            
        encode += "&i["+str(num)+"]="+urllib.quote_plus(self.date)
        if self.mbid is not None:
            encode += "&m["+str(num)+"]="+urllib.quote_plus(self.mbid)
        else:
            encode += "&m["+str(num)+"]="
        encode += "&b["+str(num)+"]="+urllib.quote_plus(self.album)
        return encode
##########
class EventListener:
    time2wait4submit = 30
    def __init__(self,session):
        self.session = session
        
    def onEvent(self,event):
        if event == 4:
            track = self.getCurrentServiceType()
            if track is not False:
                print "waiting",self.time2wait4submit,"until checking if the track is still playing"
                reactor.callLater(self.time2wait4submit, self.checkTrack, track)

    def startListenToEvents(self):
        self.session.nav.event.append(self.onEvent)

    def stopListentoEvents(self):
        self.session.nav.event.remove(self.onEvent)
    
    def getCurrentServiceType(self):
        print "getCurrentServiceType"
        currPlay = self.session.nav.getCurrentService()
        sref=self.session.nav.getCurrentlyPlayingServiceReference()
        if sref is None:
            return False
        elif sref.toString().startswith("4097:0:0:0:0:0:0:0:0:0:") is not True:
            return False
        elif sref.toString().endswith("lastfm.mp3") is True:
            return False
        elif currPlay is not None:
            return self.getTrack( artist = currPlay.info().getInfoString(iServiceInformation.sArtist),
                                  title = currPlay.info().getInfoString(iServiceInformation.sTitle),
                                  album = currPlay.info().getInfoString(iServiceInformation.sAlbum),
                                 )
             
             
    def getTrack(self , artist = None, title = None, album = None):
        print "updateMusicInformation",artist,title,album
        if artist == "" or artist is None:
            return False
        elif title == "" or title is None:
            return False
        else:
            return Track(artist,title,album)
            
    
    def checkTrack(self,track):
        print "checkTrack",track
        trackcurrent = self.getCurrentServiceType()
        print "currentTrack",trackcurrent
        if str(track) == str(trackcurrent):
            print "Tracks match!!!"
            submitTrack(trackcurrent)
            
        
def submitTrack(track):
    c = LastFMScrobbler(config.plugins.LastFM.username.value,config.plugins.LastFM.password.value)
    print "HANDSHAKE",c.handshake() 
    #tracks.append(Track(artist,name,album))
    print "SUBMIT",c.submit([track])

#c = LastFMScrobbler("hanshase","ftgz67")
#hr= c.handshake() 
#print "HANDSHAKE",hr
#sr=c.submit([Track("ArtistArtist","namename","AlbumAlbum")])
#print "SUBMIT",sr