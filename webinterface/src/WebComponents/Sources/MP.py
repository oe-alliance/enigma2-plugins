from enigma import *
from enigma import eServiceReference#, iServiceInformation
from Components.Sources.Source import Source
from ServiceReference import ServiceReference,eServiceCenter
#from Tools.Directories import resolveFilename,SCOPE_HDD
from Components.FileList import FileList#, FileEntryComponent

#import os

class MP( Source):
    LIST = 0
    PLAY = 1
    COMMAND= 3
    
    def __init__(self, session,func = LIST):
        Source.__init__(self)
        self.func = func
        self.session = session
        error = "unknown command (%s)" % func
        self.result = [[error,error,error]]
    
    def handleCommand(self,cmd):
        
        from Screens.MediaPlayer import MediaPlayer
        from Components.MediaPlayer import PlayList, PlaylistEntryComponent
        if self.session.mediaplayer is None:
            self.session.mediaplayer = self.session.open(MediaPlayer)
            #self.session.mediaplayer.filelist = FileList(root, matchingPattern = "(?i)^.*\.(mp3|ogg|ts|wav|wave|m3u|pls|e2pls|mpg|vob)", useServiceRef = True)
            self.session.mediaplayer.playlist = PlayList()
        try:
            test = len(self.session.mediaplayer.playlist)
            #Just a test, wether the link is still active.
        except:
            self.session.mediaplayer = self.session.open(MediaPlayer)
            #self.session.mediaplayer.filelist = FileList(root, matchingPattern = "(?i)^.*\.(mp3|ogg|ts|wav|wave|m3u|pls|e2pls|mpg|vob)", useServiceRef = True)
            self.session.mediaplayer.playlist = PlayList()

        self.cmd = cmd
        if self.func is self.LIST:
            self.result = self.getFileList(cmd)
        elif self.func is self.PLAY:
            self.result = self.playFile(cmd)
        elif self.func is self.COMMAND:
            self.result = self.command(cmd)
           
    def getFileList(self,param):
        print "getFileList:",param
        
        returnList = []
        
        filelist = FileList(param, matchingPattern = "(?i)^.*\.(mp3|ogg|ts|wav|wave|m3u|pls|e2pls|mpg|vob)", useServiceRef = True)
        list = filelist.getFileList()
        for x in list:
            if x[0][1] == False: #isDir
                returnList.append([x[0][0].toString(),x[0][1],param])
            else:
                returnList.append([x[0][0],x[0][1],param])
        return returnList

    def playFile(self,param):
        print "playFile: ",param
        root = param["root"]
        file = param["file"]

        mp = self.session.mediaplayer
        ref = eServiceReference(file)
        mp.playlist.addFile(ref)
        mp.playlist.updateList()

        mp.playServiceRefEntry(ref)
        return
        
    def command(self,param):
        print "command: ",param
        param = int(param)
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
