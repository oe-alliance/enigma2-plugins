#!/usr/bin/python
# -*- coding: utf-8 -*- 
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  Coded by cmikula (c)2012
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

import os
from LocaleInit import _
from ServiceUtils import diskUsage, getDirSize, realSize
from Globals import printStackTrace
from enigma import eServiceReference, iServiceInformation
from Config import config

class MovieInfo():
    idDVB = eServiceReference.idDVB
    idDVD = 0x1111 # 4369
    idMP3 = 0x1001 # 4097
    idBD = 0x0004
    def __init__(self, name, serviceref, info=None, begin=-1, length=-1, file_name=None):
        self.name = name
        self.info = info
        self.begin = begin
        self.length = length
        self.serviceref = serviceref
        if serviceref:
            self.flags = serviceref.flags
            self.type = serviceref.type
            self.path = serviceref.getPath()
            self.s_type = type(serviceref)
        else:
            self.flags = 0
            self.type = self.idDVB
            self.path = file_name
            self.s_type = eServiceReference

    def __repr__(self):
        return self.name + "\t" + self.path
    
    def createService(self):
        if self.serviceref == None:
            self.serviceref = self.s_type(self.type, self.flags, self.path)
            if self.flags & eServiceReference.mustDescent:
                self.serviceref.setName(self.name)
        return self.serviceref

    #serviceref = property(getService)

    def getPath(self):
        return self.serviceref.getPath()
    
    def getTags(self):
        if self.info is None:
            return []
        this_tags = self.info.getInfoString(self.serviceref, iServiceInformation.sTags).split(' ')
        if this_tags is None or this_tags == ['']:
            this_tags = []
        return this_tags

class DirectoryInfo():
    def __init__(self, dir_path):
        if dir_path and dir_path[-1] != '/':
            dir_path += '/'
        self.dir_path = dir_path
        self.meta_file = dir_path + ".meta"
        self.name = os.path.split(os.path.dirname(dir_path))[1]
        self.sort_type = -1
        self.used = -1
        self.dir_size = -1
        self.dir_count = -1
        self.mov_count = -1
        if dir_path != '/':
            self.__read(dir_path)
    
    def __repr__(self):
        return ", ".join((str(self.__class__.__name__), self.name, self.dir_path, str(self.dir_count), str(self.mov_count)))  

    def __parse_int(self, metafile):
        try:
            entry = metafile.readline().rstrip()
            if entry is not None:
                return int(entry)
        except:
            pass
        return -1

    def __read(self, dir_path):
        try:
            if os.path.exists(self.meta_file):
                metafile = open(self.meta_file, "r")
                self.name = metafile.readline().rstrip()
                self.sort_type = self.__parse_int(metafile)
                self.used = self.__parse_int(metafile)
                self.dir_size = self.__parse_int(metafile)
                self.dir_count = self.__parse_int(metafile)
                self.mov_count = self.__parse_int(metafile)
                #self.rest = metafile.read()
                metafile.close()
        except:
            printStackTrace()

    def write(self):
        if self.meta_file == '/.meta':
            print "[AdvancedMovieSelection] Write new meta skipped"
            return
        metafile = None
        try:
            print "[AdvancedMovieSelection] Write new meta:", self.meta_file, self.sort_type, self.used
            metafile = open(self.meta_file, "w")
            metafile.write(str(self.name) + '\n')
            metafile.write(str(self.sort_type) + '\n')
            #metafile.write(str(self.used) + '\n')
            #metafile.write(str(self.dir_size) + '\n')
            #metafile.write(str(self.dir_count) + '\n')
            #metafile.write(str(self.mov_count) + '\n')
            metafile.close()
        except:
            printStackTrace()
            if metafile is not None:
                metafile.close()

    
    def setSortType(self, sort_type):
        self.sort_type = sort_type
    
    def setName(self, name):
        self.name = name

    def isDiskSpaceChanged(self, update=True):
        total, used, free = diskUsage(self.dir_path)
        result = self.used != used
        if result and update:
            print "[AdvancedMovieSelection] update disc usage:", total, self.used, used, free
            self.used = used
        return result

    def updateFolderSize(self):
        self.dir_size = getDirSize(self.dir_path)
        print "scanned folder size", self.dir_size
    
    def getmount(self, path=None):
        path = path and path or self.dir_path
        path = os.path.abspath(path)
        while path != os.path.sep:
            if os.path.ismount(path):
                return path
            path = os.path.abspath(os.path.join(path, os.pardir))
        if path == '/':
            return None
        return path
    
    def updateDiskUsage(self, dir_count=None, movie_count=None):
        #mount = self.getmount()
        #if not mount:
        #    return
        try:
            if self.isDiskSpaceChanged():
                self.updateFolderSize()
                if dir_count is not None:
                    self.dir_count = dir_count
                if movie_count is not None:
                    self.mov_count = movie_count
                #self.write()
        except:
            printStackTrace()
        # update disk usage on mount directory
        #di = DirectoryInfo(mount)
        #if di.isDiskSpaceChanged():
        #    di.updateFolderSize()
        #    di.write()

class DirectoryEvent(DirectoryInfo):
    def __init__(self, serviceref):
        DirectoryInfo.__init__(self, serviceref.getPath())
        self.is_movielibrary = False
        from ServiceProvider import eServiceReferenceListAll
        if isinstance(serviceref, eServiceReferenceListAll):
            self.is_movielibrary = True
        elif serviceref is not None:
            from MovieScanner import movieScanner
            dbinfo = movieScanner.movielibrary.getInfo(serviceref.getPath())
            if dbinfo is not None:
                self.mov_count = dbinfo[0]
                self.dir_count = dbinfo[1]
                self.dir_size = dbinfo[2]

    def getEventName(self):
        return self.name
    
    def getShortDescription(self):
        return self.dir_path

    def getDBDescription(self):
        from MovieScanner import movieScanner
        self.dir_size = movieScanner.movielibrary.getSize()
        self.dir_count, self.mov_count = movieScanner.movielibrary.getFullCount()
        text1 = []
        
        if self.dir_size > -1:
            text1.append(realSize(self.dir_size, 3))
        if self.dir_count > 0:
            text1.append(str(self.dir_count) + ' ' + _("Directories"))
        if self.mov_count > 0:
            text1.append(str(self.mov_count) + ' ' + _("Movies"))
        
        result = ", ".join(text1)
        if movieScanner.last_update:
            result += "\r\n" + _("Last update:") + ' ' + movieScanner.getLastUpdate()
        
        return result

    def getDirDescription(self):
        text = _("Name:") + ' ' + self.name
        text1 = []
        if self.dir_size > -1:
            text1.append(realSize(self.dir_size, 3))
        if self.dir_count > 0:
            text1.append(str(self.dir_count) + ' ' + _("Directories"))
        if self.mov_count > 0:
            text1.append(str(self.mov_count) + ' ' + _("Movies"))

        if len(text1) > 0:
            text += "  (" + ", ".join(text1) + ")"
        text = [text]

        #mount_path = self.getmount()
        # TODO temporary disabled, performance issue on mass storage devices
        if config.AdvancedMovieSelection.show_diskusage.value and os.path.exists(self.dir_path):
            total, used, free = diskUsage(self.dir_path)
            #text.append(_("Media:") + ' ' + str(mount_path))
            text.append(_("Total:") + ' ' + realSize(total, 3))
            text.append(_("Used:") + ' ' + realSize(used, 3))
            text.append(_("Free:") + ' ' + realSize(free, 3))
            real_path = os.path.realpath(self.dir_path) + os.sep
            if self.dir_path != real_path:
                text.append(_("Symlink:") + ' ' + real_path)
        
        return "\n".join(text)

    def getExtendedDescription(self):
        if not self.is_movielibrary:
            return self.getDirDescription()
        else:
            return self.getDBDescription()

    def getEventId(self):
        return 0

    def getBeginTimeString(self):
        return ""
    
    def getDuration(self):
        return 0
    
    def getBeginTime(self):
        return 0
