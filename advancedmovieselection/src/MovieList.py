#!/usr/bin/python
# -*- coding: utf-8 -*- 
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  The plugin is developed on the basis from a lot of single plugins (thx for the code @ all)
#  Coded by JackDaniel & cmikula (c)2011
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
from __init__ import _
from Components.GUIComponent import GUIComponent
from Tools.FuzzyDate import FuzzyTime
from ServiceReference import ServiceReference
from Components.MultiContent import MultiContentEntryText, MultiContentEntryProgress
from Components.config import config
from enigma import eListboxPythonMultiContent, eListbox, gFont, iServiceInformation, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, eServiceReference, RT_HALIGN_CENTER
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN
import os
from skin import parseColor
import NavigationInstance
from timer import TimerEntry
from stat import ST_MTIME as stat_ST_MTIME
from time import time as time_time
from math import fabs as math_fabs
from datetime import datetime
from ServiceProvider import getCutList, Info, ServiceCenter, MovieConfig, hasLastPosition, getDirSize, getFolderSize, PicLoader, getServiceInfoValue, Network
from ServiceProvider import detectDVDStructure, eServiceReferenceDvd
from ServiceProvider import detectBludiscStructure, eServiceReferenceBludisc
from Trashcan import TRASH_NAME
from Components.Harddisk import Harddisk
from EventInformationTable import EventInformationTable, appendShortDescriptionToMeta
from AccessRestriction import accessRestriction

IMAGE_PATH = "Extensions/AdvancedMovieSelection/images/"

MEDIAEXTENSIONS = {
        "ts": "movie",
        "avi": "movie",
        "divx": "movie",
        "mpg": "movie",
        "mpeg": "movie",
        "mkv": "movie",
        "mp4": "movie",
        "m4v": "movie",
        "flv": "movie",
        "m2ts": "movie",
        "mov": "movie",
        "trash": "movie"
    }

class eServiceReferenceVDir(eServiceReference):
    pass

class eServiceReferenceHotplug(eServiceReference):
    pass

class eServiceReferenceBackDir(eServiceReference):
    pass

class MovieList(GUIComponent):
    SORT_ALPHANUMERIC = 1
    SORT_RECORDED = 2

    SORT_DATE_ASC = 3
    SORT_DATE_DESC = 4
    SORT_DESCRIPTION = 5

    LISTTYPE_ORIGINAL = 1
    LISTTYPE_COMPACT_DESCRIPTION = 2
    LISTTYPE_COMPACT = 3
    LISTTYPE_MINIMAL = 4
    LISTTYPE_MINIMAL_AdvancedMovieSelection = 5
    LISTTYPE_EXTENDED = 6

    HIDE_DESCRIPTION = 1
    SHOW_DESCRIPTION = 2
    HIDE_DATE = 1
    SHOW_DATE = 2
    HIDE_TIME = 1
    SHOW_TIME = 2
    HIDE_SERVICE = 1
    SHOW_SERVICE = 2
    HIDE_TAGS = 1
    SHOW_TAGS = 2
    
    COLOR_MOVIE_ICON = None
    COLOR_PERCENT_1 = None
    COLOR_PERCENT_2 = None
    DATE_TIME_FORMAT = ""

    def __init__(self, root, list_type=None, sort_type=None, descr_state=None, show_folders=False, show_progressbar=False, show_percent=False, show_statusicon=False, show_statuscolor=False, show_date=True, show_time=True, show_service=True, show_tags=False):
        GUIComponent.__init__(self)
        self.movieConfig = MovieConfig()
        self.picloader = PicLoader(75, 75)
        self.list_type = list_type or self.LISTTYPE_ORIGINAL
        self.descr_state = descr_state or self.HIDE_DESCRIPTION
        self.sort_type = sort_type or self.SORT_DATE_ASC
        self.sort_type = sort_type or self.SORT_DATE_DESC
        self.show_folders = show_folders
        self.show_progressbar = show_progressbar
        self.show_percent = show_percent
        self.show_statusicon = show_statusicon
        self.show_statuscolor = show_statuscolor
        self.show_date = show_date or self.HIDE_DATE
        self.show_date = show_date or self.SHOW_DATE
        self.show_time = show_time or self.HIDE_TIME
        self.show_time = show_time or self.SHOW_TIME
        self.show_service = show_service or self.HIDE_SERVICE
        self.show_service = show_service or self.SHOW_SERVICE
        self.show_tags = show_tags or self.HIDE_TAGS
        self.show_tags = show_tags or self.SHOW_TAGS
        self.l = eListboxPythonMultiContent()
        self.tags = set()
        self.filter_description = None
        
        if root is not None:
            self.reload(root)
        
        self.redrawList()
        self.l.setBuildFunc(self.buildMovieListEntry)
        self.onSelectionChanged = [ ]
        self.updateHotplugDevices()

    def destroy(self):
        self.picloader.destroy()
        GUIComponent.destroy(self)
    
    def onShow(self):
        GUIComponent.onShow(self)
        self.updateSettings()
        
    def updateSettings(self):
        if config.AdvancedMovieSelection.color1.value == "yellow":
            newcolor1 = 0xffcc00
        elif config.AdvancedMovieSelection.color1.value == "blue":
            newcolor1 = 0x8585ff
        elif config.AdvancedMovieSelection.color1.value == "red":
            newcolor1 = 0xff4A3C
        elif config.AdvancedMovieSelection.color1.value == "black":
            newcolor1 = 0x000000
        elif config.AdvancedMovieSelection.color1.value == "green":
            newcolor1 = 0x38FF48           
        
        if config.AdvancedMovieSelection.color2.value == "yellow":
            newcolor2 = 0xffcc00
        elif config.AdvancedMovieSelection.color2.value == "blue":
            newcolor2 = 0x8585ff
        elif config.AdvancedMovieSelection.color2.value == "red":
            newcolor2 = 0xff4A3C
        elif config.AdvancedMovieSelection.color2.value == "black":
            newcolor2 = 0x000000
        elif config.AdvancedMovieSelection.color2.value == "green":
            newcolor2 = 0x38FF48                  
        
        if config.AdvancedMovieSelection.color3.value == "yellow":
            newcolor3 = 0xffcc00
        elif config.AdvancedMovieSelection.color3.value == "blue":
            newcolor3 = 0x8585ff
        elif config.AdvancedMovieSelection.color3.value == "red":
            newcolor3 = 0xff4A3C
        elif config.AdvancedMovieSelection.color3.value == "black":
            newcolor3 = 0x000000
        elif config.AdvancedMovieSelection.color3.value == "green":
            newcolor3 = 0x38FF48    
        
        if config.AdvancedMovieSelection.color4.value == "yellow":
            newcolor4 = 0xffcc00
        elif config.AdvancedMovieSelection.color4.value == "blue":
            newcolor4 = 0x8585ff
        elif config.AdvancedMovieSelection.color4.value == "red":
            newcolor4 = 0xff4A3C
        elif config.AdvancedMovieSelection.color4.value == "black":
            newcolor4 = 0x000000
        elif config.AdvancedMovieSelection.color4.value == "green":
            newcolor4 = 0x38FF48  
        elif config.AdvancedMovieSelection.color4.value == "grey":
            newcolor4 = 0x7F7F7F
        elif config.AdvancedMovieSelection.color4.value == "orange":
            newcolor4 = 0xffa500 

        self.mark_color = newcolor4
        try: self.watching_color = parseColor("movieWatching").argb()    
        except: self.watching_color = newcolor1
        try: self.finished_color = parseColor("movieFinished").argb()    
        except: self.finished_color = newcolor2
        try: self.recording_color = parseColor("movieRecording").argb()    
        except: self.recording_color = newcolor3

        if self.show_statusicon and self.show_folders:
            if config.AdvancedMovieSelection.color3.value == "yellow":
                self.COLOR_MOVIE_ICON = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "yellow_movieicon.png"))
            elif config.AdvancedMovieSelection.color3.value == "blue":
                self.COLOR_MOVIE_ICON = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "blue_movieicon.png"))
            elif config.AdvancedMovieSelection.color3.value == "red":
                self.COLOR_MOVIE_ICON = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "red_movieicon.png"))
            elif config.AdvancedMovieSelection.color3.value == "black":
                self.COLOR_MOVIE_ICON = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "black_movieicon.png"))
            elif config.AdvancedMovieSelection.color3.value == "green":
                self.COLOR_MOVIE_ICON = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "green_movieicon.png"))
            else:
                self.COLOR_MOVIE_ICON = None
        else:
            self.COLOR_MOVIE_ICON = None
            
        if config.AdvancedMovieSelection.color1.value == "yellow":
            self.COLOR_PERCENT_1 = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "yellow_movieicon.png"))
        elif config.AdvancedMovieSelection.color1.value == "blue":
            self.COLOR_PERCENT_1 = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "blue_movieicon.png"))
        elif config.AdvancedMovieSelection.color1.value == "red":
            self.COLOR_PERCENT_1 = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "red_movieicon.png"))
        elif config.AdvancedMovieSelection.color1.value == "black":
            self.COLOR_PERCENT_1 = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "black_movieicon.png"))
        elif config.AdvancedMovieSelection.color1.value == "green":
            self.COLOR_PERCENT_1 = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "green_movieicon.png"))
        
        if config.AdvancedMovieSelection.color2.value == "yellow":
            self.COLOR_PERCENT_2 = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "yellow_movieicon.png"))
        elif config.AdvancedMovieSelection.color2.value == "blue":
            self.COLOR_PERCENT_2 = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "blue_movieicon.png"))
        elif config.AdvancedMovieSelection.color2.value == "red":
            self.COLOR_PERCENT_2 = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "red_movieicon.png"))
        elif config.AdvancedMovieSelection.color2.value == "black":
            self.COLOR_PERCENT_2 = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "black_movieicon.png"))
        elif config.AdvancedMovieSelection.color2.value == "green":
            self.COLOR_PERCENT_2 = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "green_movieicon.png"))

        if config.AdvancedMovieSelection.dateformat.value == "1":
            self.DATE_TIME_FORMAT = "%d.%m.%Y"
        elif config.AdvancedMovieSelection.dateformat.value == "4":
            self.DATE_TIME_FORMAT = "%m.%d.%Y"
        elif config.AdvancedMovieSelection.dateformat.value == "5":
            self.DATE_TIME_FORMAT = "%m.%d.%Y - %H:%M"
        elif config.AdvancedMovieSelection.dateformat.value == "6":
            self.DATE_TIME_FORMAT = "%d.%m"
        elif config.AdvancedMovieSelection.dateformat.value == "7":
            self.DATE_TIME_FORMAT = "%m.%d"
        else:
            self.DATE_TIME_FORMAT = "%d.%m.%Y - %H:%M"

        from Components.Language import language
        lang = language.getLanguage()
        if lang == "de_DE" or lang == "de":
            self.MOVIE_NEW_PNG = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "movie_de_new.png"))
            self.NO_COVER_PNG_FILE = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/AdvancedMovieSelection/images/nocover_de.png")
        elif lang == "en":
            self.MOVIE_NEW_PNG = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "movie_en_new.png"))
            self.NO_COVER_PNG_FILE = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/AdvancedMovieSelection/images/nocover_en.png")
        else:
            self.MOVIE_NEW_PNG = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "movie_new.png"))
            self.NO_COVER_PNG_FILE = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/AdvancedMovieSelection/images/nocover_en.png")

    def updateHotplugDevices(self):
        self.automounts = []
        if config.AdvancedMovieSelection.hotplug.value == False:
            return
        try:
            import commands
            lines = commands.getoutput('mount | grep /dev/sd').split('\n')
            for mount in lines:
                if len(mount) < 2:
                    continue
                m = mount.split(' type')[0].split(' on ')
                m_dev, m_path = m[0], m[1]
                label = os.path.split(m_path)[-1]
                blkid = commands.getoutput('blkid ' + m_dev).split("\"")
                if len(blkid) > 2 and blkid[1]:
                    label = blkid[1]
                if os.path.normpath(m_path) == "/media/hdd" or label in ("DUMBO", "TIMOTHY"):
                    continue
                if not self.movieConfig.isHiddenHotplug(label):
                    service = eServiceReferenceHotplug(eServiceReference.idFile, eServiceReference.flagDirectory, m_path + "/")
                    hdd = Harddisk(m_dev.replace("/dev/", "")[:-1])
                    service.setName(label + " - " + hdd.model() + " - " + hdd.capacity())
                    self.automounts.append(service)
        except Exception, e:
            print e
    
    def unmount(self, service):
        from os import system
        res = system("umount " + service.getPath()) >> 8
        if res == 0:
            self.automounts.remove(service)
        return res

    def connectSelChanged(self, fnc):
        if not fnc in self.onSelectionChanged:
            self.onSelectionChanged.append(fnc)

    def disconnectSelChanged(self, fnc):
        if fnc in self.onSelectionChanged:
            self.onSelectionChanged.remove(fnc)

    def selectionChanged(self):
        for x in self.onSelectionChanged:
            x()

    def setListType(self, type):
        self.list_type = type

    def setDescriptionState(self, val):
        self.descr_state = val

    def setSortType(self, type):
        self.sort_type = type

    def showFolders(self, val):
        self.show_folders = val

    def showProgressbar(self, val):
        self.show_progressbar = val

    def showPercent(self, val):
        self.show_percent = val

    def showStatusIcon(self, val):
        self.show_statusicon = val

    def showStatusColor(self, val):
        self.show_statuscolor = val
        
    def showDate(self, val):
        self.show_date = val
        
    def showTime(self, val):
        self.show_time = val
        
    def showService(self, val):
        self.show_service = val

    def showTags(self, val):
        self.show_tags = val

    def redrawList(self):
        if self.list_type == MovieList.LISTTYPE_ORIGINAL or self.list_type == MovieList.LISTTYPE_EXTENDED:
            self.l.setFont(0, gFont("Regular", 22))
            self.l.setFont(1, gFont("Regular", 19))
            self.l.setFont(2, gFont("Regular", 16))
            self.l.setItemHeight(78)
        elif self.list_type == MovieList.LISTTYPE_COMPACT_DESCRIPTION or self.list_type == MovieList.LISTTYPE_COMPACT:
            self.l.setFont(0, gFont("Regular", 20))
            self.l.setFont(1, gFont("Regular", 14))
            self.l.setItemHeight(39)
        elif self.list_type == MovieList.LISTTYPE_MINIMAL_AdvancedMovieSelection:
            self.l.setFont(0, gFont("Regular", 18))
            self.l.setFont(1, gFont("Regular", 14))
            self.l.setItemHeight(26)
        else:
            self.l.setFont(0, gFont("Regular", 20))
            self.l.setFont(1, gFont("Regular", 16))
            self.l.setItemHeight(26)

    def buildMovieListEntry(self, serviceref, info, begin, len, selection_index= -1):
        width = self.l.getItemSize().width()
        offset = 0
        res = [ None ]
        if self.show_folders:
            if serviceref.flags & eServiceReference.mustDescent:

                if isinstance(serviceref, eServiceReferenceVDir):
                    png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "bookmark.png"))
                elif isinstance(serviceref, eServiceReferenceHotplug):
                    png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "hotplug.png"))
                elif isinstance(serviceref, eServiceReferenceBackDir):
                    png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "back.png"))
                else:
                    png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "directory.png"))

                offset = 30
                if self.list_type == MovieList.LISTTYPE_EXTENDED:
                    if config.AdvancedMovieSelection.usefoldername.value:
                        filename = serviceref.getPath()[:-1] + ".jpg"
                    else:
                        filename = serviceref.getPath() + "folder.jpg"
                    if os.path.exists(filename):
                        offset = 75
                        png = self.picloader.load(filename)
                        res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 0, 2, 75, 76, png))
                    else:
                        res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 5, 2, 20, 20, png))
                    res.append(MultiContentEntryText(pos=(offset, 28), size=(width, 25), font=1, flags=RT_HALIGN_LEFT, text=serviceref.getPath()))
                else:
                    res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 5, 2, 20, 20, png))

                res.append(MultiContentEntryText(pos=(offset, 3), size=(width - 150, 30), font=0, flags=RT_HALIGN_LEFT, text=serviceref.getName()))
                if config.AdvancedMovieSelection.show_dirsize.value:
                    if len < 0: #recalk len when not already done
                        cur_idx = self.l.getCurrentSelectionIndex()
                        if config.usage.load_length_of_movies_in_moviellist.value and serviceref.getName() != "..":
                            if config.AdvancedMovieSelection.show_dirsize_full.value:
                                len = getFolderSize(serviceref.getPath())
                            else:
                                len = getDirSize(serviceref.getPath())
                        else:
                            len = 0 #dont recalc movielist to speedup loading the list
                        self.list[cur_idx] = (serviceref, info, begin, len) #update entry in list... so next time we don't need to recalc
                    cap = float(len / (1024 * 1024))
                    if cap == 0:
                        dir_size = "N/A"
                    elif cap <= 999:
                        dir_size = "%d MB" % (cap)
                    else:
                        if config.AdvancedMovieSelection.dirsize_digits.value == "0":
                            dir_size = "%d GB" % (cap / 1000)
                        elif config.AdvancedMovieSelection.dirsize_digits.value == "1":
                            dir_size = "%s GB" % (round(cap / 1000, 1))
                        elif config.AdvancedMovieSelection.dirsize_digits.value == "2":
                            dir_size = "%s GB" % (round(cap / 1000, 2))
                        else:
                            dir_size = "%s GB" % (round(cap / 1000, 3))
                    if serviceref.getName() != "..":
                        res.append(MultiContentEntryText(pos=(width - 115, 3), size=(110, 30), font=0, flags=RT_HALIGN_RIGHT, text=dir_size))

                return res
            
            if self.list_type != MovieList.LISTTYPE_EXTENDED:
                extension = serviceref.toString().split('.')
                extension = extension[-1].lower()
                offset = 25
                if MEDIAEXTENSIONS.has_key(extension):
                    filename = os.path.realpath(serviceref.getPath())
                    if config.AdvancedMovieSelection.shownew.value and not hasLastPosition(serviceref):
                        png = self.MOVIE_NEW_PNG
                    else:
                        png = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + MEDIAEXTENSIONS[extension] + ".png"))
                else:
                    if isinstance(serviceref, eServiceReferenceDvd) or isinstance(serviceref, eServiceReferenceBludisc):
                        png = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + "dvd_watching.png"))
                    else:
                        png = None

        if info is not None:
            if len < 0: #recalc len when not already done
                cur_idx = self.l.getCurrentSelectionIndex()
                if config.usage.load_length_of_movies_in_moviellist.value:
                    len = info.getLength(serviceref) #recalc the movie length...
                    if len == 0:
                        file_name = serviceref.getPath()
                        if not os.path.isdir(file_name):
                            eit_file = os.path.splitext(file_name)[0] + ".eit"
                        else:
                            eit_file = file_name + ".eit"
                        len = EventInformationTable(eit_file, True).getDuration()
                else:
                    len = 0 #dont recalc movielist to speedup loading the list
                self.list[cur_idx] = (serviceref, info, begin, len) #update entry in list... so next time we don't need to recalc

        length = len
    
        if len > 0:
            len = "%d:%02d" % (len / 60, len % 60)
        else:
            len = ""
        
        if info is not None:
            service_name = info.getName(serviceref)
            if not isinstance(info, Info):
                service = ServiceReference(info.getInfoString(serviceref, iServiceInformation.sServiceref))
            else:
                service = info.getServiceReference()
            description = info.getInfoString(serviceref, iServiceInformation.sDescription)
            tags = info.getInfoString(serviceref, iServiceInformation.sTags)

        color = None 
        recording = False
        if NavigationInstance.instance.getRecordings():
            for timer in NavigationInstance.instance.RecordTimer.timer_list:
                if timer.state == TimerEntry.StateRunning:
                    try:
                        filename = "%s.ts" % timer.Filename
                    except:
                        filename = ""
                    if filename and os.path.realpath(filename) == os.path.realpath(serviceref.getPath()):
                        recording = True
                        break
        if not recording:
            filename = os.path.realpath(serviceref.getPath())
            if os.path.exists("%s.sc" % filename) and not os.path.exists("%s.ap" % filename):
                # double check, sometimes ap file was not created (e.g. after enigma2 crash)
                filestats = os.stat(filename)
                currentTime = time_time()
                mtime = filestats[stat_ST_MTIME]
                if math_fabs(mtime - int(currentTime)) <= 10:
                    recording = True
        
        if recording: 
            if self.show_statuscolor:
                color = self.recording_color
            if self.COLOR_MOVIE_ICON:
                png = self.COLOR_MOVIE_ICON

        if (self.list_type == MovieList.LISTTYPE_EXTENDED) or (self.show_progressbar or self.show_percent) or (self.show_statusicon and self.show_folders) or self.show_statuscolor:
            last = None
            if length <= 0: #Set default file length if is not calculateable
                length = 5400
            cue = None #info.cueSheet()
            if cue is None:
                cut_list = getCutList(serviceref.getPath())
                for (pts, what) in cut_list:
                    if what == 1 and length == 5400:
                        length = pts / 90000
                    if what == 3:
                        last = pts
            elif cue is not None:
                cut_list = cue.getCutList()
                for (pts, what) in cut_list:
                    if what == 1 and length == 5400:
                        length = pts / 90000
                    if what == 3:
                        last = pts
            perc = 0
            if last is not None and length > 0:
                perc = int((float(last) / 90000 / float(length)) * 100);
                if perc > 100:
                    perc = 100
                if perc < 0:
                    perc = 0
                if self.show_statuscolor and not recording:
                    if (perc > 1) and (perc <= config.AdvancedMovieSelection.moviepercentseen.value):
                        color = self.watching_color
                    elif (perc > config.AdvancedMovieSelection.moviepercentseen.value):
                        color = self.finished_color
                if self.show_statusicon and self.show_folders and not recording:
                    if perc > 1 and perc <= config.AdvancedMovieSelection.moviepercentseen.value:
                        png = self.COLOR_PERCENT_1
                    elif perc > config.AdvancedMovieSelection.moviepercentseen.value:
                        png = self.COLOR_PERCENT_2

            if self.list_type != MovieList.LISTTYPE_EXTENDED:
                ''' never enable this - on dvd structures the extension is incorrect and will crash '''
                #if config.AdvancedMovieSelection.shownew.value and self.show_folders and not self.show_statusicon and perc > 0:
                #    png = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, IMAGE_PATH + MEDIAEXTENSIONS[extension] + ".png"))   
                    
                if self.show_progressbar:
                    top = int((self.l.getItemSize().height() - 6) / 2) + 1
                    res.append(MultiContentEntryProgress(pos=(0 + offset, top), size=(50, 6), percent=perc, borderWidth=1, foreColor=color))
                    offset = offset + 55
    
                if self.show_percent:
                    perc_txt = "%d" % (perc) + ' % - '
                    if self.list_type == MovieList.LISTTYPE_MINIMAL_AdvancedMovieSelection:
                        res.append(MultiContentEntryText(pos=(offset, 2), size=(60, 25), font=0, flags=RT_HALIGN_RIGHT, text=perc_txt, color=color))
                        offset = offset + 65
                    else:
                        res.append(MultiContentEntryText(pos=(offset, 2), size=(70, 25), font=0, flags=RT_HALIGN_RIGHT, text=perc_txt, color=color))
                        offset = offset + 75

        begin_string = ""
        if recording:
            if config.AdvancedMovieSelection.dateformat.value == "6":
                begin_string = (_("REC"))
            else:
                if config.AdvancedMovieSelection.dateformat.value == "7":
                    begin_string = (_("REC"))
                else:
                    begin_string = (_("Records"))        
        else:
            if config.AdvancedMovieSelection.dateformat.value == "2" and begin > 0:
                t = FuzzyTime(begin)
                begin_string = t[0] + ", " + t[1]
            else:
                d = datetime.fromtimestamp(begin)
                begin_string = d.strftime(self.DATE_TIME_FORMAT)

        if selection_index > -1:
            txt = "%d - %s" % (selection_index, service_name)
            if self.show_statuscolor:
                color = self.mark_color
        else:
            txt = service_name

        if self.list_type == MovieList.LISTTYPE_EXTENDED:
            filename = os.path.splitext(serviceref.getPath())[0] + ".jpg"
            filesize = float(info.getInfoObject(serviceref, iServiceInformation.sFileSize) / (1024 * 1024))
            prec_text = str(perc) + '%'
            png = None
            series_path = os.path.join(os.path.dirname(serviceref.getPath()), "series.jpg")
            if os.path.exists(series_path):
                png = self.picloader.load(series_path)
            elif os.path.exists(filename):
                png = self.picloader.load(filename)
            elif serviceref.getPath().endswith("ts"):
                # picon, make sure only ts files goes here
                picon = getServiceInfoValue(serviceref, iServiceInformation.sServiceref).rstrip(':').replace(':', '_') + ".png"
                piconpath = os.path.join(config.AdvancedMovieSelection.piconpath.value, picon)
                if os.path.exists(piconpath):
                    png = self.picloader.load(piconpath)
            if not png:
                png = self.picloader.load(self.NO_COVER_PNG_FILE)
            res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 0, 2, 75, 76, png))
            offset = offset + 80
            new_offset = 0
            # new icon
            if config.AdvancedMovieSelection.shownew.value and not hasLastPosition(serviceref):
                res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offset, 0, 20, 20, self.MOVIE_NEW_PNG))
                new_offset = new_offset + 24

            # Line 1: Movie Text, service name
            res.append(MultiContentEntryText(pos=(new_offset + offset, 0), size=(width - 265, 30), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
            res.append(MultiContentEntryText(pos=(width - 185, 0), size=(180, 30), font=2, flags=RT_HALIGN_RIGHT, text=service.getServiceName(), color=color))
            # line 2: description, file size 
            res.append(MultiContentEntryText(pos=(0 + offset, 28), size=(width, 25), font=1, flags=RT_HALIGN_LEFT, text=description, color=color))
            if filesize:
                if filesize <= 999:
                    filesize = "%d MB" % (filesize)
                else:
                    filesize = "%s GB" % (round(filesize / 1000, 2))                
                res.append(MultiContentEntryText(pos=(width - 185, 28), size=(180, 30), font=2, flags=RT_HALIGN_RIGHT, text=filesize, color=color))
            # Line 3: begin_string, progress bar, percent, tags, movie length
            res.append(MultiContentEntryText(pos=(0 + offset, 55), size=(100, 20), font=1, flags=RT_HALIGN_LEFT, text=begin_string, color=color))
            res.append(MultiContentEntryProgress(pos=(130 + offset, 63), size=(50, 6), percent=perc, borderWidth=1, foreColor=color))
            res.append(MultiContentEntryText(pos=(190 + offset, 55), size=(60, 20), font=1, flags=RT_HALIGN_LEFT, text=prec_text, color=color))
            if tags:
                res.append(MultiContentEntryText(pos=(250 + offset, 55), size=(500, 20), font=1, flags=RT_HALIGN_LEFT, text=self.arrangeTags(tags), color=color))
            res.append(MultiContentEntryText(pos=(width - 105, 55), size=(100, 20), font=1, flags=RT_HALIGN_RIGHT, text=len, color=color))

        elif self.list_type == MovieList.LISTTYPE_ORIGINAL:
            if self.show_folders:
                res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 0, 29, 20, 20, png))
            res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 265, 30), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
            if tags and self.show_tags == MovieList.SHOW_TAGS:
                res.append(MultiContentEntryText(pos=(width - 255, 0), size=(250, 30), font=2, flags=RT_HALIGN_RIGHT, text=self.arrangeTags(tags), color=color))
                if service is not None:
                    res.append(MultiContentEntryText(pos=(300, 55), size=(200, 25), font=1, flags=RT_HALIGN_LEFT, text=service.getServiceName(), color=color))
            else:
                if service is not None:
                    res.append(MultiContentEntryText(pos=(width - 185, 0), size=(180, 30), font=2, flags=RT_HALIGN_RIGHT, text=service.getServiceName(), color=color))
                res.append(MultiContentEntryText(pos=(0 + offset, 28), size=(width, 25), font=1, flags=RT_HALIGN_LEFT, text=description, color=color))
            if self.show_date == MovieList.SHOW_DATE:
                res.append(MultiContentEntryText(pos=(0 + offset, 55), size=(200, 20), font=1, flags=RT_HALIGN_LEFT, text=begin_string, color=color))
            if self.show_time == MovieList.SHOW_TIME:
                res.append(MultiContentEntryText(pos=(width - 205, 55), size=(200, 20), font=1, flags=RT_HALIGN_RIGHT, text=len, color=color))

        elif self.list_type == MovieList.LISTTYPE_COMPACT_DESCRIPTION:
            if self.show_folders:
                res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 0, 9, 20, 20, png))
            res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width, 23), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))                
            res.append(MultiContentEntryText(pos=(0 + offset, 22), size=(width - 212, 17), font=1, flags=RT_HALIGN_LEFT, text=description, color=color))
            if self.show_date == MovieList.SHOW_DATE:
                res.append(MultiContentEntryText(pos=(width - 135, 4), size=(130, 20), font=1, flags=RT_HALIGN_RIGHT, text=begin_string, color=color))                
            if self.show_time == MovieList.SHOW_TIME:
                dr = service.getServiceName() + " " + len
                res.append(MultiContentEntryText(pos=(width - 215, 22), size=(210, 17), font=1, flags=RT_HALIGN_RIGHT, text=dr, color=color))
            else:
                res.append(MultiContentEntryText(pos=(width - 155, 22), size=(150, 17), font=1, flags=RT_HALIGN_RIGHT, text=service.getServiceName(), color=color))

        elif self.list_type == MovieList.LISTTYPE_COMPACT:
            if self.show_folders:
                res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 0, 9, 20, 20, png))            
            res.append(MultiContentEntryText(pos=(offset, 0), size=(width, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))            
            if self.show_date == MovieList.SHOW_DATE:
                res.append(MultiContentEntryText(pos=(offset, 22), size=(200, 17), font=1, flags=RT_HALIGN_LEFT, text=begin_string, color=color))            
            if self.show_time == MovieList.SHOW_TIME:
                res.append(MultiContentEntryText(pos=(width - 80, 0), size=(75, 20), font=0, flags=RT_HALIGN_RIGHT, text=len, color=color))            
            if tags and self.show_tags == MovieList.SHOW_TAGS:
                res.append(MultiContentEntryText(pos=(width - 205, 22), size=(200, 17), font=1, flags=RT_HALIGN_RIGHT, text=self.arrangeTags(tags), color=color))
                if service is not None:
                    res.append(MultiContentEntryText(pos=(250, 22), size=(200, 17), font=1, flags=RT_HALIGN_LEFT, text=service.getServiceName(), color=color))
            else:
                if service is not None:
                    res.append(MultiContentEntryText(pos=(width - 205, 22), size=(200, 17), font=1, flags=RT_HALIGN_RIGHT, text=service.getServiceName(), color=color))        

        elif self.list_type == MovieList.LISTTYPE_MINIMAL_AdvancedMovieSelection:
            if selection_index > -1:
                displaytext = "%d - " % (selection_index)
            else:
                displaytext = ""
            if self.show_date == MovieList.SHOW_DATE:
                if not service_name == description and not description == "":
                    displaytext = displaytext + begin_string + " - " + service_name + " - " + description
                else:
                    displaytext = displaytext + begin_string + " - " + service_name
            else:
                if not service_name == description and not description == "":
                    displaytext = displaytext + service_name + " - " + description
                else:
                    displaytext = displaytext + service_name
            if len and self.show_time == MovieList.SHOW_TIME:
                displaytext = displaytext + ' ' + "(" + len + ")"
            
            if self.show_folders:
                res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 0, 3, 20, 20, png))
            offsetServiceName = 0
            if self.show_service == MovieList.SHOW_SERVICE:
                servicename = service.getServiceName()
                res.append(MultiContentEntryText(pos=(width - 175, 2), size=(170, 20), font=0, flags=RT_HALIGN_RIGHT, text=servicename, color=color))
                if servicename:
                    offsetServiceName = 175
            if tags and self.show_tags == MovieList.SHOW_TAGS and self.show_service == MovieList.HIDE_SERVICE:
                res.append(MultiContentEntryText(pos=(width - 255, 2), size=(250, 20), font=0, flags=RT_HALIGN_RIGHT, text=self.arrangeTags(tags, False), color=color))
                offsetServiceName = 255
            res.append(MultiContentEntryText(pos=(0 + offset, 2), size=(width - (0 + offset + offsetServiceName), 25), font=0, flags=RT_HALIGN_LEFT, text=displaytext, color=color))
        else:
            assert(self.list_type == MovieList.LISTTYPE_MINIMAL)
            if self.show_folders:
                res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 0, 3, 20, 20, png))
            
            if len > 0:
                len2 = "- " + len
            else:
                len2 = ""
            
            if self.show_date == MovieList.SHOW_DATE:
                if self.show_time == MovieList.SHOW_TIME:
                    if config.AdvancedMovieSelection.dateformat.value == "1":
                        res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 235, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
                        res.append(MultiContentEntryText(pos=(width - 145, 5), size=(80, 25), font=1, flags=RT_HALIGN_RIGHT, text=begin_string, color=color))
                        res.append(MultiContentEntryText(pos=(width - 65, 5), size=(60, 25), font=1, flags=RT_HALIGN_RIGHT, text=len2, color=color))                                                     
                    elif config.AdvancedMovieSelection.dateformat.value == "2":
                        res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 240, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
                        res.append(MultiContentEntryText(pos=(width - 190, 5), size=(125, 25), font=1, flags=RT_HALIGN_RIGHT, text=begin_string, color=color))
                        res.append(MultiContentEntryText(pos=(width - 65, 5), size=(60, 25), font=1, flags=RT_HALIGN_RIGHT, text=len2, color=color))                                                    
                    elif config.AdvancedMovieSelection.dateformat.value == "3":
                        res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 295, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
                        res.append(MultiContentEntryText(pos=(width - 205, 5), size=(140, 25), font=1, flags=RT_HALIGN_RIGHT, text=begin_string, color=color))
                        res.append(MultiContentEntryText(pos=(width - 65, 5), size=(60, 25), font=1, flags=RT_HALIGN_RIGHT, text=len2, color=color))                           
                    elif config.AdvancedMovieSelection.dateformat.value == "4":
                        res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 235, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
                        res.append(MultiContentEntryText(pos=(width - 145, 5), size=(80, 25), font=1, flags=RT_HALIGN_RIGHT, text=begin_string, color=color))
                        res.append(MultiContentEntryText(pos=(width - 65, 5), size=(60, 25), font=1, flags=RT_HALIGN_RIGHT, text=len2, color=color))                             
                    elif config.AdvancedMovieSelection.dateformat.value == "5":
                        res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 295, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
                        res.append(MultiContentEntryText(pos=(width - 205, 5), size=(140, 25), font=1, flags=RT_HALIGN_RIGHT, text=begin_string, color=color))
                        res.append(MultiContentEntryText(pos=(width - 65, 5), size=(60, 25), font=1, flags=RT_HALIGN_RIGHT, text=len2, color=color))                          
                    elif config.AdvancedMovieSelection.dateformat.value == "6":
                        res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 200, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
                        res.append(MultiContentEntryText(pos=(width - 115, 5), size=(50, 25), font=1, flags=RT_HALIGN_RIGHT, text=begin_string, color=color))
                        res.append(MultiContentEntryText(pos=(width - 65, 5), size=(60, 25), font=1, flags=RT_HALIGN_RIGHT, text=len2, color=color))                            
                    elif config.AdvancedMovieSelection.dateformat.value == "7":
                        res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 200, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
                        res.append(MultiContentEntryText(pos=(width - 115, 5), size=(50, 25), font=1, flags=RT_HALIGN_RIGHT, text=begin_string, color=color))
                        res.append(MultiContentEntryText(pos=(width - 65, 5), size=(60, 25), font=1, flags=RT_HALIGN_RIGHT, text=len2, color=color))             
           
                if self.show_time == MovieList.HIDE_TIME:
                    if config.AdvancedMovieSelection.dateformat.value == "1":
                        res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 175, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
                        res.append(MultiContentEntryText(pos=(width - 95, 4), size=(90, 20), font=1, flags=RT_HALIGN_RIGHT, text=begin_string, color=color))                            
                    elif config.AdvancedMovieSelection.dateformat.value == "2":
                        res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 175, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
                        res.append(MultiContentEntryText(pos=(width - 95, 4), size=(90, 20), font=1, flags=RT_HALIGN_RIGHT, text=begin_string, color=color))                               
                    elif config.AdvancedMovieSelection.dateformat.value == "3":
                        res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 230, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
                        res.append(MultiContentEntryText(pos=(width - 155, 4), size=(150, 20), font=1, flags=RT_HALIGN_RIGHT, text=begin_string, color=color))                              
                    elif config.AdvancedMovieSelection.dateformat.value == "4":
                        res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 175, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
                        res.append(MultiContentEntryText(pos=(width - 95, 4), size=(90, 20), font=1, flags=RT_HALIGN_RIGHT, text=begin_string, color=color))                               
                    elif config.AdvancedMovieSelection.dateformat.value == "5":
                        res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 230, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
                        res.append(MultiContentEntryText(pos=(width - 155, 4), size=(150, 20), font=1, flags=RT_HALIGN_RIGHT, text=begin_string, color=color))              
                    elif config.AdvancedMovieSelection.dateformat.value == "6":
                        res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 130, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
                        res.append(MultiContentEntryText(pos=(width - 55, 4), size=(50, 20), font=1, flags=RT_HALIGN_RIGHT, text=begin_string, color=color))                            
                    elif config.AdvancedMovieSelection.dateformat.value == "7":
                        res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 130, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
                        res.append(MultiContentEntryText(pos=(width - 55, 4), size=(50, 20), font=1, flags=RT_HALIGN_RIGHT, text=begin_string, color=color))             
 
            if self.show_time == MovieList.SHOW_TIME and self.show_date == MovieList.HIDE_DATE:
                res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 150, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))
                res.append(MultiContentEntryText(pos=(width - 75, 2), size=(70, 20), font=0, flags=RT_HALIGN_RIGHT, text=len, color=color))                                    

            if self.show_date == MovieList.HIDE_DATE and self.show_time == MovieList.HIDE_TIME:
                res.append(MultiContentEntryText(pos=(0 + offset, 0), size=(width - 0, 25), font=0, flags=RT_HALIGN_LEFT, text=txt, color=color))

        return res

    def moveToIndex(self, index):
        self.instance.moveSelectionTo(index)

    def getCurrentIndex(self):
        return self.instance.getCurrentIndex()

    def getCurrentInfo(self):
        l = self.l.getCurrentSelection()
        return l and l[1]

    def getCurrentEvent(self):
        l = self.l.getCurrentSelection()
        return l and l[0] and l[1] and l[1].getEvent(l[0])

    def getCurrent(self):
        l = self.l.getCurrentSelection()
        return l and l[0]

    GUI_WIDGET = eListbox

    def postWidgetCreate(self, instance):
        instance.setContent(self.l)
        instance.selectionChanged.get().append(self.selectionChanged)

    def preWidgetRemove(self, instance):
        instance.setContent(None)
        instance.selectionChanged.get().remove(self.selectionChanged)

    def reload(self, root=None, filter_tags=None):
        self.movieConfig.readDMconf()
        if root is not None:
            self.load(root, filter_tags)
        else:
            self.load(self.root, filter_tags)
        self.l.setList(self.list)

    def removeService(self, service):
        try:
            for i, x in enumerate(self.multiSelection):
                if x == service:
                    del self.multiSelection[i]
        except Exception, e:
            print e
        for l in self.list[:]:
            if l[0] == service:
                self.list.remove(l)
        self.l.setList(self.list)

    def __len__(self):
        return len(self.list)

    def load(self, root, filter_tags):
        # this lists our root service, then building a nice list
        self.list = [ ]
        self.multiSelection = []

        self.serviceHandler = ServiceCenter.getInstance()
        
        # TODO: if path of root is set to other path, the gui not show the new path | fix or delete me
        #if not Network.isMountOnline(root.getPath()):
        #    root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + "/media/")
        self.root = root
        list = self.serviceHandler.list(root)
        if list is None:
            print "listing of movies failed"
            list = [ ]    
            return
        tags = set()
        
        dirs = []

        while 1:
            serviceref = list.getNext()
            if not serviceref.valid():
                break
            dvd = None
            #dvd structure
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
                    
            if dvd is None:
                if self.show_folders:
                    # Dr.Best: folder in movielist
                    if serviceref.flags & eServiceReference.mustDescent:
                        tempDir = serviceref.getPath()
                        parts = tempDir.split("/")
                        dirName = parts[-2]
                        if self.movieConfig.isHidden(dirName):
                            continue
                        serviceref.setName(dirName)
                        dirs.append((serviceref, None, -1, -1))
                        continue
                else:
                    if serviceref.flags & eServiceReference.mustDescent:
                        continue

            temp = serviceref.getPath()
            parts = temp.split("/")
            file = parts[-1]
            if self.movieConfig.isHidden(file):
                continue
        
            extension = serviceref.getPath().split(".")[-1].lower()
            if extension == "iso" or extension == "img":
                serviceref = eServiceReferenceDvd(serviceref)

            info = self.serviceHandler.info(serviceref)

            if dvd is not None:
                begin = long(os.stat(dvd).st_mtime)
            else:
                begin = info.getInfo(serviceref, iServiceInformation.sTimeCreate)

            if self.filter_description:
                descr = info.getInfoString(serviceref, iServiceInformation.sDescription)
                if descr != self.filter_description:
                    continue 
            
            # convert space-seperated list of tags into a set
            this_tags = info.getInfoString(serviceref, iServiceInformation.sTags).split(' ')
            if not accessRestriction.isAccessible(this_tags):
                continue
            if this_tags is None or this_tags == ['']:
                this_tags = []
            this_tags = set(this_tags)
            tags |= this_tags
        
            # filter_tags is either None (which means no filter at all), or 
            # a set. In this case, all elements of filter_tags must be present,
            # otherwise the entry will be dropped.            
            if filter_tags is not None and not this_tags.issuperset(filter_tags):
                continue
        
            self.list.append((serviceref, info, begin, -1))
        
        if self.sort_type == MovieList.SORT_ALPHANUMERIC:
            self.list.sort(key=self.buildAlphaNumericSortKey)
        elif self.sort_type == MovieList.SORT_DATE_ASC:
            self.list.sort(self.sortbyDateAsc)
        elif self.sort_type == MovieList.SORT_DESCRIPTION:
            self.list.sort(self.sortbyDescription)
        else:
            self.list.sort(self.sortbyDateDesc)
#            # sort: key is 'begin'
#            self.list.sort(key=lambda x: -x[2])

        if self.show_folders:
            root_path = root.getPath()
            if config.AdvancedMovieSelection.show_bookmarks.value:
                vdirs = []
                for dir in config.movielist.videodirs.value:
                    if dir != root_path and not self.isInList(dir, dirs):
                        parts = dir.split("/")
                        if len(parts) > 2:
                            dirName = parts[-3] + "/" + parts[-2]
                        else: 
                            dirName = parts[-2]
                        if not Network.isMountOnline(dir):
                            continue
                        tt = eServiceReferenceVDir(eServiceReference.idFile, eServiceReference.flagDirectory, dir)
                        tt.setName(self.movieConfig.getRenamedName(dirName))
                        vdirs.append((tt, None, -1, -1))
                vdirs.sort(self.sortFolders)
                for servicedirs in vdirs:
                    self.list.insert(0, servicedirs)

            for tt in self.automounts:
                if tt.getPath() != root_path:
                    self.list.insert(0, (tt, None, -1, -1))

            dirs.sort(self.sortFolders)
            for servicedirs in dirs:
                self.list.insert(0, servicedirs)
            tmp = self.root.getPath()
            if len(tmp) > 1:
                tt = eServiceReferenceBackDir(eServiceReference.idFile, eServiceReference.flagDirectory, "..")
                tt.setName("..")
                tmpRoot = os.path.dirname(tmp[:-1])
                if len(tmpRoot) > 1:
                    tmpRoot = tmpRoot + "/"
                tt.setPath(tmpRoot)
                self.list.insert(0, (tt, None, -1, -1))
            
        # finally, store a list of all tags which were found. these can be presented to the user to filter the list
        self.tags = tags

    def isInList(self, a, b):
        for ref in b:
            if a == ref[0].getPath():
                return True
        return False

    def sortbyDescription(self, a, b):
        d1 = a[1].getInfoString(a[0], iServiceInformation.sDescription)
        d2 = b[1].getInfoString(b[0], iServiceInformation.sDescription)
        return cmp(d1, d2)

    def sortbyDateAsc(self, a, b):
        return cmp(a[2], b[2])

    def sortbyDateDesc(self, a, b):
        return cmp(b[2], a[2])

    def sortFolders(self, a, b):
        return cmp(b[0].getName().lower(), a[0].getName().lower())

    def buildAlphaNumericSortKey(self, x):
        ref = x[0]
        info = self.serviceHandler.info(ref)
        name = info and info.getName(ref)
        return (name and name.lower() or "", -x[2])

    def arrangeTags(self, tags, vsr_left=True):
        tag_list = []
        vsr = None
        for t in tags.split():
            if t.startswith("VSR"):
                vsr = t
            else:
                tag_list.append(t)
        tag_list.sort()
        if vsr:
            vsr = _("VSR") + "-%d" % (accessRestriction.decodeAccess(vsr))
            if vsr_left:
                tag_list.insert(0, vsr)
            else:
                tag_list.append(vsr)
        return ", ".join(tag_list)

    def moveTo(self, serviceref):
        count = 0
        for x in self.list:
            if x[0] == serviceref:
                self.instance.moveSelectionTo(count)
                return True
            count += 1
        return False
    
    def moveUp(self):
        self.instance.moveSelection(self.instance.moveUp)

    def moveDown(self):
        self.instance.moveSelection(self.instance.moveDown)
        
    def updateCurrentSelection(self, dummy=None):
        cur_idx = self.instance.getCurrentIndex()
        self.l.invalidateEntry(cur_idx)

    def find(self, f, seq):
        for item in seq:
            if item == f: 
                return item
        return None        

    def toggleSelection(self):
        x = self.l.getCurrentSelection()
        if not x:
            return False
        service = x[0]
        if service.flags & eServiceReference.mustDescent and not isinstance(service, eServiceReferenceDvd):
            return False
        cur_idx = self.l.getCurrentSelectionIndex()
        f = self.find(service, self.multiSelection)
        if f:
            self.multiSelection.remove(service)
            idx_num = -1
            for index, item in enumerate(self.list):
                if len(item) > 4 and item[4] > x[4]:
                    self.list[index] = (item[0], item[1], item[2], item[3], item[4] - 1)
                    self.l.invalidateEntry(index)
        else:
            self.multiSelection.append(service)
            idx_num = len(self.multiSelection)
        self.list.remove(self.list[cur_idx])
        self.list.insert(cur_idx, (x[0], x[1], x[2], x[3], idx_num))
        self.l.invalidateEntry(cur_idx)
        return True

    def setMovieStatus(self, serviceref, status):
        info = self.serviceHandler.info(serviceref)
        if info is None:
            return
        cur_idx = self.l.getCurrentSelectionIndex()
        cue = info.cueSheet()
        if cue is not None:
            cutList = cue.getCutList()
            for l in cutList:
                if l[1] == 3:
                    cutList.remove(l)
            if status:
                x = self.list[cur_idx]
                length = x[1].getLength(x[0])
                new = (long(length * 90000), 3)
                cutList.append(new)
            cue.setCutList(cutList)
            self.l.invalidateEntry(cur_idx)
            return cutList

    def getMovieStatus(self):
        if len(self.list) == 0:
            return 0
        cur_idx = self.l.getCurrentSelectionIndex()
        x = self.list[cur_idx]
        if not x[1]:
            return 0
        cue = x[1].cueSheet()
        length = x[1].getLength(x[0])
        last = 1
        if cue is not None:
            cutList = cue.getCutList()
            for (pts, what) in cutList:
                if what == 3:
                    last = pts / 90000
                    break
        if length == 0:
            return 0
        perc = int((float(last) / float(length)) * 100);
        return perc

    def updateMetaFromEit(self):
        for item in self.list:
            serviceref = item[0]
            file_name = serviceref.getPath()
            if os.path.isfile(file_name):
                eit_file = os.path.splitext(file_name)[0] + ".eit"
            else:
                eit_file = file_name + ".eit"
            if os.path.exists(eit_file):
                eit = EventInformationTable(eit_file)
                appendShortDescriptionToMeta(serviceref.getPath(), eit.short_description)

    def setAccess(self, access=18):
        accessRestriction.setAccess(access)

    def getAccess(self):
        return accessRestriction.getAccess()

    def setAccessRestriction(self, access=None):
        service = self.getCurrent()
        if service:
            clear = access == None
            if len(self.multiSelection) > 0:
                for service in self.multiSelection:
                    accessRestriction.setToService(service.getPath(), access, clear)
            else:
                accessRestriction.setToService(service.getPath(), access, clear)
