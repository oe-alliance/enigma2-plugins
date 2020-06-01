#!/usr/bin/python
# -*- coding: utf-8 -*- 
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  Coded by cmikula & JackDaniel (c)2012
#  Support: www.i-have-a-dreambox.com
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#

from __future__ import print_function
import os
from datetime import datetime
from ServiceProvider import ServiceCenter, eServiceReferenceDvd, eServiceReferenceBludisc
from ServiceProvider import detectDVDStructure, detectBludiscStructure
from ServiceDescriptor import MovieInfo
from ServiceUtils import serviceUtil, diskUsage, getDirSize
from AutoNetwork import autoNetwork
from MovieConfig import MovieConfig
from Globals import printStackTrace
from Trashcan import TRASH_NAME
from enigma import eServiceReference, iServiceInformation
from ISOInfo import ISOInfo
from Components.config import config
from StopWatch import clockit
from RecordTimerEvent import recordTimerEvent
from MovieLibrary import MovieLibrary
from Hotplug import hotplug

SCAN_EXCLUDE = (ISOInfo.MOUNT_PATH, "DUMBO", "TIMOTHY", "/media/swap", "/media/ram", "/media/ba")
AUDIO_EXCLUDE = ("mp3", "ogg", "wav", "m4a")

def getDirectories(l, root, hidden=False):
    root = os.path.realpath(root) + os.sep
    if not autoNetwork.isMountOnline(root):
        print("not connected:", root)
        return
    if not os.path.exists(root):
        print("path not exists:", root)
        return
    if not root in l:
        l.append(root)
    for entry in os.listdir(root):
        try:
            if not hidden and entry.startswith('.'):
                continue
            dir_path = os.path.join(root, entry)
            if not os.path.isdir(dir_path):
                continue
            dir_path = os.path.realpath(dir_path) + os.sep
            # Skip excluded directories here
            if any(item.lower() in dir_path.lower() for item in SCAN_EXCLUDE):
                print("skip folder: \"%s\"" % (dir_path))
                continue
            dvd = detectDVDStructure(dir_path)
            bludisc = detectBludiscStructure(dir_path)
            if dvd or bludisc:
                continue
            if not dir_path in l:
                l.append(dir_path)
            getDirectories(l, dir_path, hidden)
        except:
            printStackTrace()


class MovieScanner():
    def __init__(self):
        self.movielibrary = MovieLibrary()
        self.isWorking = False
        self.movieConfig = MovieConfig()
        self.callback = None
        self.serviceHandler = ServiceCenter.getInstance()
        #self.full_used_detect = 0
        self.enabled = False
        self.last_update = None
    
    def setEnabled(self, enabled):
        self.enabled = enabled
        print("[AdvancedMovieSelection] Set MovieScanner:", str(enabled))
        if enabled:
            recordTimerEvent.appendCallback(self.timerStateChanged)
            self.addHotplugNotifier()
            self.reloadMoviesAsync()
        else:
            recordTimerEvent.removeCallback(self.timerStateChanged)
            self.removeHotplugNotifier()
    
    def updateReloadTime(self):
        self.last_update = datetime.now()

    def getLastUpdate(self):
        if self.last_update is not None:
            return self.last_update.strftime("%d.%m.%Y %H:%M")
    
    def isMovieRecorded(self, name):
        entries = self.movielibrary.findMovies(name)
        for mi in entries:
            if mi.serviceref.getPath().endswith(".ts"):
                return 1
        if len(entries) > 0:
            return 2
        return 0
    
    def reloadMoviesAsync(self, dir_list=None, delay=0):
        if self.isWorking:
            print("[AdvancedMovieSelection] MovieScanner action canceled! reload in progress")
            return
        from thread import start_new_thread
        start_new_thread(self.updateMovieList, (dir_list, delay))
        self.isWorking = True

    def getFullUsed(self):
        full_used = 0
        for p in config.AdvancedMovieSelection.videodirs.value:
            total, used, free = diskUsage(p)
            full_used += used
        return full_used

    @clockit
    def updateDirectories(self):
        config.AdvancedMovieSelection.videodirs.load()
        new_list = []
        for p in config.AdvancedMovieSelection.videodirs.value:
            getDirectories(new_list, p)
        return new_list
    
    @clockit
    def updateMovieList(self, dir_list=None, delay=0):
        print("[AdvancedMovieSelection] Start scanning movies")
        try:
            # print(dir_list)
            self.isWorking = True
            if delay > 0:
                print("waiting", str(delay))
                import time
                time.sleep(delay)
            self.updateReloadTime()
            if dir_list is None:
                self.movielibrary.clearAll()
                dir_list = self.updateDirectories()
            
            # print "-" * 80
            # for p in dir_list:
            #    print(p)
            # print "-" * 80
            
            for p in dir_list:
                self.scanForMovies(p)
            
            # self.full_used_detect = self.getFullUsed()
            if self.callback is not None:
                self.callback()

            # from MovieLibrary import dict2xml
            # xml = dict2xml(self.movielibrary)
            # xml.write("/tmp/movie_list.xml")
        except:
            printStackTrace()
        self.isWorking = False
        directories, movies = self.movielibrary.getFullCount()
        print("[AdvancedMovieSelection] Finished scanning movies", str(directories), str(movies))

    def scanForMovies(self, root):
        # print "[AdvancedMovieSelection] scan folder:", root

        scan_service = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + root)
        root_list = self.serviceHandler.list(scan_service)
        if root_list is None:
            print("listing of movies failed")
            return
        tags = set()
        l = []
        dirs = []
        while True:
            serviceref = root_list.getNext()
            if not serviceref.valid():
                break
            dvd = None
            # print(serviceref.getPath())
            # dvd structure
            if serviceref.flags & eServiceReference.mustDescent:
                dvd = detectDVDStructure(serviceref.getPath())
                if dvd is not None:
                    if serviceref.getPath()[:-1].endswith(TRASH_NAME):
                        continue
                    serviceref = eServiceReferenceDvd(serviceref, True)
                bludisc = detectBludiscStructure(serviceref.getPath())
                if bludisc is not None:
                    if serviceref.getPath()[:-1].endswith(TRASH_NAME):
                        continue
                    serviceref = eServiceReferenceBludisc(serviceref, True)
                
                if not dvd and not bludisc:
                    continue
                
                if False:
                    # add folder dir
                    tempDir = serviceref.getPath()
                    parts = tempDir.split(os.sep)
                    dirName = parts[-2]
                    if self.movieConfig.isHidden(dirName):
                        continue
                    serviceref.setName(dirName)
                    dirs.append((serviceref, None, -1, -1))
                    continue
            
            # check hidden files
            temp = serviceref.getPath()
            parts = temp.split(os.sep)
            if self.movieConfig.isHidden(parts[-1]):
                continue
            
            ext = temp.split(".")[-1].lower()
            if ext in AUDIO_EXCLUDE:
                continue
            
            # check currently moving files
            if serviceUtil.isServiceMoving(serviceref):
                continue
            
            # check iso and img files
            extension = serviceref.getPath().split(".")[-1].lower()
            if extension == "iso" or extension == "img":
                serviceref = eServiceReferenceDvd(serviceref)

            info = self.serviceHandler.info(serviceref)

            # get begin time
            if dvd is not None:
                begin = long(os.stat(dvd).st_mtime)
            else:
                begin = info.getInfo(serviceref, iServiceInformation.sTimeCreate)

            # convert space-seperated list of tags into a set
            this_tags = info.getInfoString(serviceref, iServiceInformation.sTags).split(' ')
            if this_tags is None or this_tags == ['']:
                this_tags = []
            this_tags = set(this_tags)
            tags |= this_tags

            # add to list
            service_name = info.getName(serviceref)
            mi = MovieInfo(service_name, serviceref, info, begin)
            l.append(mi)

        # we always must add location to movielibrary
        dir_size = getDirSize(root)
        self.movielibrary.addMovieList(root, l, dir_size)
        self.movielibrary.addTags(tags)
    
    def findMovies___(self, name):
        l = []
        for mi in self.list:
            if name == mi[0].name:
                l.append(mi)
        return l

    def findMovie___(self, serviceref):
        for mi in self.list:
            if serviceref.getPath() == mi[0].getPath():
                return mi[0]

    def removeMovie(self, file_service_list):
        self.movielibrary.removeMovie(file_service_list)
        self.updateReloadTime()

    def timerStateChanged(self, timer):
        try:
            from timer import TimerEntry 
            print("timer.event", timer.name)
            print("timer.state", timer.state)
            if timer.state == TimerEntry.StateRunning:
                print("TimerEntry", timer.name)
                print(timer.Filename + ".ts")
                mi = MovieInfo(timer.name, None, file_name=timer.Filename + ".ts")
                serviceref = mi.createService()
                mi.info = self.serviceHandler.info(serviceref)
                mi.begin = mi.info.getInfo(serviceref, iServiceInformation.sTimeCreate)
                movie_path = os.path.dirname(mi.serviceref.getPath()) + os.sep
                self.movielibrary.addMovie(movie_path, mi)
                self.updateReloadTime()
                print("add:", mi)
        except:
            printStackTrace()

    def needFullUpdate(self):
        videodirs = config.AdvancedMovieSelection.videodirs.value[:]
        config.AdvancedMovieSelection.videodirs.load()
        print("checking directories")
        print(videodirs)
        print(config.AdvancedMovieSelection.videodirs.value)
        if len(videodirs) < len(config.AdvancedMovieSelection.videodirs.value):
            print("size changed")
            return True
        if len(videodirs) == len(config.AdvancedMovieSelection.videodirs.value) and videodirs != config.AdvancedMovieSelection.videodirs.value:
            print("path changed")
            return True
        return False

    @clockit
    def checkAllAvailable(self):
        # print "*" * 80
        if self.isWorking:
            print("canceled, scan in progress")
            return

        if self.needFullUpdate():
            print("need update")
            not_in_db = self.movielibrary.getMissingLocations(config.AdvancedMovieSelection.videodirs.value)
            new_list = []
            for p in not_in_db:
                getDirectories(new_list, p)
            self.reloadMoviesAsync(new_list)

        # remove locations from movielibrary if path not exists
        for location in self.movielibrary.getDirectoryList():
            if not os.path.exists(location):
                self.updateReloadTime()
                self.movielibrary.removeLocation(location)
            
        # print "*" * 80

    def updateServiceInfo(self, serviceref):
        if not serviceref:
            return
        if serviceref.flags & eServiceReference.mustDescent:
            return
        print("update service info", serviceref.toString())
        movie_info = self.movielibrary.findMoviePath(serviceref)
        if movie_info is not None:
            movie_info.info = self.serviceHandler.info(serviceref)
            movie_info.name = movie_info.info.getName(serviceref)
            print(movie_info)

    def addHotplugNotifier(self):
        if not self.checkAllAvailable in hotplug.notifier:
            print("add hotplugNotifier") 
            hotplug.notifier.append(self.checkAllAvailable)
            hotplug.hotplugChanged()
        
    def removeHotplugNotifier(self):
        if self.checkAllAvailable in hotplug.notifier:
            print("remove hotplugNotifier") 
            hotplug.notifier.remove(self.checkAllAvailable)
    

movieScanner = MovieScanner()
