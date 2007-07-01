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

        returnList = []
        from Screens.MediaPlayer import MediaPlayer
        from Components.MediaPlayer import PlayList, PlaylistEntryComponent
        mp = self.session.open(MediaPlayer)
     
        #index = 0
        #counter = -1
        mp.filelist = FileList(root, matchingPattern = "(?i)^.*\.(mp3|ogg|ts|wav|wave|m3u|pls|e2pls|mpg|vob)", useServiceRef = True)
        #for x in mp.filelist.getFileList():
        #    counter = counter +1
        #    if x[0][1] == False: #isDir
        #        if x[0][0].toString() == str(file):
        #            index = counter
        #        mp.playlist.addFile(x[0][0])
        print mp.playlist
        mp.playlist = PlayList()
        mp.playlist.addFile(eServiceReference(file))
        print mp.playlist
        mp.playlist.updateList()
        mp.changeEntry(0)
        mp.playEntry()
        
        returnList.append(["started","started","started"])
        return returnList

    
    def getList(self):
        return self.result
    
    list = property(getList)
    lut = {"ServiceReference": 0
           ,"IsDirectory": 1
           ,"Root": 2
           }
