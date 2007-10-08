from enigma import eServiceReference, iServiceInformation, eServiceCenter
from Components.Sources.Source import Source
from ServiceReference import ServiceReference
from Components.FileList import FileList
from os import path as os_path

class MP( Source):
    LIST = 0
    PLAY = 1
    COMMAND = 3
    WRITEPLAYLIST = 4
    
    def __init__(self, session,func = LIST):
        Source.__init__(self)
        self.func = func
        self.session = session
        error = "unknown command (%s)" % func
        self.result = [[error,error,error]]
    
    def handleCommand(self,cmd):       
        self.cmd = cmd
        if self.func is self.LIST:
            self.result = self.getFileList(cmd)
        elif self.func is self.PLAY:
            self.result = self.playFile(cmd)
        elif self.func is self.COMMAND:
            self.result = self.command(cmd)
        elif self.func is self.WRITEPLAYLIST:
            self.result = self.writePlaylist(cmd)

    def tryOpenMP(self):
        # See is the Link is still active
        if self.session.mediaplayer is not None:
            try:
                test = len(self.session.mediaplayer.playlist)
                return True
            except:
                pass
        
        # Link inactive, instantiate new MP
        try:
            from Plugins.Extensions.MediaPlayer.plugin import MediaPlayer, MyPlayList
            self.session.mediaplayer = self.session.open(MediaPlayer)
            self.session.mediaplayer.playlist = MyPlayList()
            return True
        
        # No MP installed
        except ImportError, ie:
            return False
           
    def getFileList(self,param):
        print "getFileList:",param
        
        returnList = []
        
        if param["path"] == "playlist":
            # TODO: Fix dummy return if unable to load mp
            if not self.tryOpenMP():
                returnList.append(["empty","True","playlist"])
                return returnList
            
            mp = self.session.mediaplayer
            if len(mp.playlist) != 0:
                serviceRefList = mp.playlist.getServiceRefList()
                for count in range(len(serviceRefList)):
                    returnList.append([serviceRefList[count].toString(),"True","playlist"])
            else:
                returnList.append(["empty","True","playlist"])
            
            return returnList

        matchingPattern = "(?i)^.*\.(mp3|ogg|ts|wav|wave|m3u|pls|e2pls|mpg|vob)" #MediaPlayer-Match
        useServiceRef = False
        if param["types"] == "audio":
            matchingPattern = "(?i)^.*\.(mp3|ogg|wav|wave|m3u|pls|e2pls)"
            useServiceRef = True
        elif param["types"] == "video":
            matchingPattern = "(?i)^.*\.(ts|avi|mpeg|m3u|pls|e2pls|mpg|vob)"
            useServiceRef = True
        elif param["types"] == "any":
            matchingPattern = ".*"
        else:
            matchingPattern = param["types"]
        
        #__init__(self, directory, showDirectories = True, showFiles = True, matchingPattern = None, useServiceRef = False, isTop = False):
        filelist = FileList(param["path"], True, True, matchingPattern, useServiceRef, False)
        list = filelist.getFileList()
        for x in list:
            if useServiceRef == True:
                if x[0][1] == False: #isDir
                    returnList.append([x[0][0].toString(),x[0][1],param["path"]])
                else:
                    returnList.append([x[0][0],x[0][1],param["path"]])
            else:
                if x[0][1] == False: #isDir
                    returnList.append([param["path"]+x[0][0],x[0][1],param["path"]])
                else:
                    returnList.append([x[0][0],x[0][1],param["path"]])

        return returnList

    def playFile(self,param):
        print "playFile: ",param
        # TODO: fix error handling
        if not self.tryOpenMP():
            return

        root = param["root"]
        file = param["file"]

        mp = self.session.mediaplayer
        ref = eServiceReference(file)
        
        mp.switchToPlayList()
        
        if len(mp.playlist) == 1:
                mp.changeEntry(0)
        
        mp.playlist.addFile(ref)

        #mp.playServiceRefEntry(ref)
        print "len len(mp.playlist.getServiceRefList()): ",len(mp.playlist.getServiceRefList())
        if len(mp.playlist.getServiceRefList()):
            lastEntry = len(mp.playlist.getServiceRefList()) -1
            currref = mp.playlist.getServiceRefList()[lastEntry]
            if self.session.nav.getCurrentlyPlayingServiceReference() is None or currref != self.session.nav.getCurrentlyPlayingServiceReference():
                self.session.nav.playService(mp.playlist.getServiceRefList()[lastEntry])
                info = eServiceCenter.getInstance().info(currref)
                description = info and info.getInfoString(currref, iServiceInformation.sDescription) or ""
                mp["title"].setText(description)
            mp.unPauseService()
            #mp.playEntry(len(self.playlist.getServiceRefList()))
        
        mp.playlist.updateList()
        mp.infoTimerFire()
        return
    #
    def writePlaylist(self,param):
        print "writePlaylist: ",param
        filename = "playlist/%s.e2pls" % param
        from Tools.Directories import resolveFilename, SCOPE_CONFIG
        
        # TODO: fix error handling
        if not self.tryOpenMP():
            return
        
        mp = self.session.mediaplayer
        mp.playlistIOInternal.save(resolveFilename(SCOPE_CONFIG, filename))
        
    def command(self,param):
        print "command: ",param
        param = int(param)
        
        # TODO: fix error handling
        if not self.tryOpenMP():
            return
        
        mp = self.session.mediaplayer
        
        if param == 0:
            mp.previousEntry()
        elif param == 1:
            mp.playEntry()
        elif param == 2:
            mp.pauseEntry()
        elif param == 3:
            mp.nextEntry()
        elif param == 4:
            mp.stopEntry()
        elif param == 5:
            mp.exit()
        
        return
    
    def getList(self):
        return self.result
    
    list = property(getList)
    lut = {"ServiceReference": 0
           ,"IsDirectory": 1
           ,"Root": 2
           }
