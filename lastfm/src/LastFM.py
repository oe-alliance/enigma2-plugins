import httpclient

import os
import md5 # to encode password
import string
import time
import urllib
import Image
import xml.dom.minidom



class LastFM:
    DEFAULT_NAMESPACES = (
        None, # RSS 0.91, 0.92, 0.93, 0.94, 2.0
        'http://purl.org/rss/1.0/', # RSS 1.0
        'http://my.netscape.com/rdf/simple/0.9/' # RSS 0.90
    )
    DUBLIN_CORE = ('http://purl.org/dc/elements/1.1/',)
    
    version = "1.0.1"
    platform = "linux"
    host = "ws.audioscrobbler.com"
    port = 80
    metadata = {}
    info={}
    cache_toptags= "/tmp/toptags"
    
    def __init__(self):
        self.state = False # if logged in
    
    def _loadURL(self,url):
        s = httpclient.httpclient(self.host, self.port)
        s.req(url)
        return s.response
    
    def connect(self,username,password):
        self.info = self.parselines(self._loadURL("/radio/handshake.php?version=" + self.version + "&platform=" + self.platform + "&username=" + username + "&passwordmd5=" + self.hexify(md5.md5(password).digest())))
        if self.info.has_key("session"):
            self.session = self.info["session"]
            if self.session.startswith("FAILED"):
                return False,self.info["msg"]
            else:
                self.streamurl = self.info["stream_url"]
                self.baseurl = self.info["base_url"]
                self.basepath = self.info["base_path"]
                self.subscriber = self.info["subscriber"]
                self.framehack = self.info["base_path"]
                self.state = True
                return True,"loggedin"
        else:
            return False,"Could not login, wrong username or password?"
        
    def parselines(self, str):
        res = {}
        vars = string.split(str, "\n")
        for v in vars:
            x = string.split(string.rstrip(v), "=", 1)
            if len(x) == 2:
                res[x[0]] = x[1]
            elif x != [""]:
                print "(urk?", x, ")"
        return res
    
    def getPersonalURL(self,username,level=50):
        return "lastfm://user/%s/recommended/32"%username
    
    def getNeighboursURL(self,username):
        return "lastfm://user/%s/neighbours"%username

    def getLovedURL(self,username):
        return "lastfm://user/%s/loved"%username
    
    def getSimilarArtistsURL(self,artist=None):
        if artist is None and self.metadata.has_key('artist'):
            return "lastfm://artist/%s/similarartists"%self.metadata['artist'].replace(" ","%20")
        else:
            return "lastfm://artist/%s/similarartists"%artist.replace(" ","%20")

    def getArtistsLikedByFans(self,artist=None):
        if artist is None and self.metadata.has_key('artist'):
            return "lastfm://artist/%s/fans"%self.metadata['artist'].replace(" ","%20")
        else:
            return "lastfm://artist/%s/fans"%artist.replace(" ","%20")
    
    def getArtistGroup(self,artist=None):
        if artist is None and self.metadata.has_key('artist'):
            return "lastfm://group/%s"%self.metadata['artist'].replace(" ","%20")
        else:
            return "lastfm://group/%s"%artist.replace(" ","%20")
    
    def getmetadata(self):
        if self.state is not True:
            return False
        else:
            s = httpclient.httpclient(self.info["base_url"], 80)
            s.req(self.info["base_path"] + "/np.php?session=" + self.info["session"])
            tmp = self.parselines(s.response)
            if tmp.has_key('\xef\xbb\xbfstreaming'):
                tmp["streaming"] = tmp['\xef\xbb\xbfstreaming']
    
            if tmp.has_key("streaming"):
                if tmp["streaming"] == "false" or (tmp["streaming"] == "true" and tmp.has_key("artist") and tmp.has_key("track") and tmp.has_key("trackduration")):
                    if not tmp.has_key("album"):
                        tmp["album"] = ""
                        tmp["album_url"] = ""
                    self.metadata = tmp
                    self.metadatatime = time.time()
                    self.metadataage = str(int(time.time() - self.metadatatime))
                    #print self.metadata
                    #print self.metadatatime
                    #print "age",self.metadataage
                    return True
            return False

    def command(self, cmd):
        if self.state is not True:
            return False
        else:
            try:
                # commands = skip, love, ban, rtp, nortp
                s = httpclient.httpclient(self.info["base_url"], 80)
                s.req(self.info["base_path"] + "/control.php?command=" + cmd + "&session=" + self.info["session"])
                res = self.parselines(s.response)
                if res["response"] != "OK":
                    return True
                else:
                    return False
            except Exception,e:
                print "Error",e
                return False
    
    def hexify(self,s):
        result = ""
        for c in s:
            result = result + ("%02x" % ord(c))
        return result
    
    def love(self):
        return self.command("love")

    def ban(self):
        return self.command("ban")

    def skip(self):
        return self.command("skip")
    

    def XMLgetElementsByTagName( self, node, tagName, possibleNamespaces=DEFAULT_NAMESPACES ):
        for namespace in possibleNamespaces:
            children = node.getElementsByTagNameNS(namespace, tagName)
            if len(children): return children
        return []

    def XMLnode_data( self, node, tagName, possibleNamespaces=DEFAULT_NAMESPACES):
        children = self.XMLgetElementsByTagName(node, tagName, possibleNamespaces)
        node = len(children) and children[0] or None
        return node and "".join([child.data.encode("utf-8") for child in node.childNodes]) or None

    def XMLget_txt( self, node, tagName, default_txt="" ):
        return self.XMLnode_data( node, tagName ) or self.XMLnode_data( node, tagName, self.DUBLIN_CORE ) or default_txt

    def getGlobalTags( self ,force_reload=False):
        if self.state is not True:
            return []
        else:
            #TODO IOError
            try: 
                if os.path.isfile(self.cache_toptags) is False or force_reload is True :
                    s = httpclient.httpclient(self.info["base_url"], 80)
                    s.req("/1.0/tag/toptags.xml")
                    xmlsrc = s.response
                    fp = open(self.cache_toptags,"w")
                    fp.write(xmlsrc)
                    fp.close()
                else:
                    fp = open(self.cache_toptags)
                    xmlsrc = fp.read()
                    fp.close()
                rssDocument = xml.dom.minidom.parseString(xmlsrc)
                data =[]
                for node in self.XMLgetElementsByTagName(rssDocument, 'tag'):
                    nodex={}
                    nodex['_display'] = nodex['name'] = node.getAttribute("name").encode("utf-8")
                    nodex['count'] =  node.getAttribute("count").encode("utf-8")
                    nodex['stationurl'] = "lastfm://globaltags/"+node.getAttribute("name").encode("utf-8").replace(" ","%20")
                    nodex['url'] =  node.getAttribute("url").encode("utf-8")
                    data.append(nodex)
                return data
            except xml.parsers.expat.ExpatError,e:
                print e
                return []

    def getTopTracks(self,username):
        if self.state is not True:
            return []
        else:
            s = httpclient.httpclient(self.info["base_url"], 80)
            s.req("/1.0/user/%s/toptracks.xml"%username)
            return self._parseTracks(s.response)

    def getRecentTracks(self,username):
        if self.state is not True:
            return []
        else:
            s = httpclient.httpclient(self.info["base_url"], 80)
            s.req("/1.0/user/%s/recenttracks.xml"%username)
            return self._parseTracks(s.response)
    def getRecentLovedTracks(self,username):
        if self.state is not True:
            return []
        else:
            s = httpclient.httpclient(self.info["base_url"], 80)
            s.req("/1.0/user/%s/recentlovedtracks.xml"%username)
            return self._parseTracks(s.response)

    def getRecentBannedTracks(self,username):
        if self.state is not True:
            return []
        else:
            s = httpclient.httpclient(self.info["base_url"], 80)
            s.req("/1.0/user/%s/recentbannedtracks.xml"%username)
            return self._parseTracks(s.response)

    def _parseTracks(self,xmlrawdata):
        #print xmlrawdata
        try:
            rssDocument = xml.dom.minidom.parseString(xmlrawdata)
            data =[]
            for node in self.XMLgetElementsByTagName(rssDocument, 'track'):
                nodex={}
                nodex['name'] = self.XMLget_txt(node, "name", "N/A" )
                nodex['artist'] =  self.XMLget_txt(node, "artist", "N/A" )
                nodex['playcount'] = self.XMLget_txt(node, "playcount", "N/A" )
                nodex['stationurl'] =  "lastfm://artist/"+nodex['artist'].replace(" ","%20")+"/"+nodex['name'].replace(" ","%20")
                nodex['url'] =  self.XMLget_txt(node, "url", "N/A" )
                nodex['_display'] = nodex['artist']+" - "+nodex['name']
                data.append(nodex)
            return data
        except xml.parsers.expat.ExpatError,e:
            print e
            return []

    def getNeighbours(self,username):
        if self.state is not True:
            return []
        else:
            s = httpclient.httpclient(self.info["base_url"], 80)
            s.req("/1.0/user/%s/neighbours.xml"%username)
            return self._parseUser(s.response)

    def getFriends(self,username):
        if self.state is not True:
            return []
        else:
            s = httpclient.httpclient(self.info["base_url"], 80)
            s.req("/1.0/user/%s/friends.xml"%username)
            return self._parseUser(s.response)

    def _parseUser(self,xmlrawdata):
        print xmlrawdata
        try:
            rssDocument = xml.dom.minidom.parseString(xmlrawdata)
            data =[]
            for node in self.XMLgetElementsByTagName(rssDocument, 'user'):
                nodex={}
                nodex['name'] = node.getAttribute("username").encode("utf-8")
                nodex['url'] =  self.XMLget_txt(node, "url", "N/A" )
                nodex['stationurl'] =  "lastfm://user/"+nodex['name']+"/personal"
                nodex['_display'] = nodex['name']
                data.append(nodex)
            return data
        except xml.parsers.expat.ExpatError,e:
            print e
            return []

    def changestation(self, url):
        print "#"*20,self.state
        if self.state is not True:
            return False
        else:
            s = httpclient.httpclient(self.info["base_url"], 80)
            s.req(self.info["base_path"] + "/adjust.php?session=" + self.info["session"] + "&url=" + url)
            res = self.parselines(s.response)
            if res["response"] != "OK":
                print "station " + url + " returned:", res
            return res