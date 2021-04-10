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
from __future__ import print_function
from __future__ import absolute_import
from .__init__ import _
from Components.PluginComponent import plugins
from Screens.Screen import Screen
from Components.ActionMap import HelpableActionMap, ActionMap, NumberActionMap
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Screens.HelpMenu import HelpableScreen
from .MovieList import MovieList
from Components.DiskInfo import DiskInfo
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.config import config, ConfigSubsection, ConfigText, ConfigInteger, ConfigLocations, ConfigSet
from Components.UsageConfig import defaultMoviePath
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.LocationBox import MovieLocationBox
from .AdvancedMovieSelectionSetup import AdvancedMovieSelectionSetup, AdvancedMovieSelectionButtonSetup
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, fileExists, SCOPE_HDD, SCOPE_CURRENT_SKIN
from enigma import eServiceReference, eSize, ePoint, eTimer, iServiceInformation
from Screens.Console import eConsoleAppContainer
from .MoveCopy import MovieMove
from .Rename import MovieRetitle
from SearchTMDb import TMDbMain as TMDbMainsave
from .MoviePreview import MoviePreview, VideoPreview
from .DownloadMovies import DownloadMovies
from .Source.ServiceProvider import eServiceReferenceDvd
from .TagEditor import MovieTagEditor
from .QuickButton import QuickButton
from os import path
import os
import NavigationInstance
from timer import TimerEntry
from .Source.Trashcan import Trashcan, AsynchTrash
from RecordTimer import AFTEREVENT
from .ClientSetup import ClientSetup
from time import localtime, strftime
from datetime import datetime
from Tools.FuzzyDate import FuzzyTime
from .MovieSearch import MovieSearch
from .Source.Globals import pluginPresent, SkinTools, printStackTrace
from .Source.ServiceProvider import ServiceEvent, ServiceCenter
from .Source.ServiceProvider import eServiceReferenceHotplug, eServiceReferenceBackDir, eServiceReferenceListAll
from .Source.AutoNetwork import autoNetwork 
from .Source.MovieScanner import movieScanner
from .Source.ServiceDescriptor import DirectoryInfo
from .Source.StopWatch import StopWatch, clockit

if pluginPresent.IMDb:
    from Plugins.Extensions.IMDb.plugin import IMDB
if pluginPresent.OFDb:
    from Plugins.Extensions.OFDb.plugin import OFDB
if pluginPresent.TMDb:
    from Plugins.Extensions.TMDb.plugin import TMDbMain
if pluginPresent.YTTrailer:
    from Plugins.Extensions.YTTrailer.plugin import YTTrailerList
if fileExists("/etc/grautec/dm8000/tft_dm8000.ko"):
    TFT_8000_Present = True
else:
    TFT_8000_Present = False

if "movielist" not in config.content.items:
    print("e2 config.movielist not exists")
    config.movielist = ConfigSubsection()
# all config.entries from Screens.MovieSelection
config.movielist.moviesort = ConfigInteger(default=MovieList.SORT_ALPHANUMERIC)
config.movielist.listtype = ConfigInteger(default=MovieList.LISTTYPE_ORIGINAL)
config.movielist.description = ConfigInteger(default=MovieList.HIDE_DESCRIPTION)
config.movielist.last_videodir = ConfigText(default=resolveFilename(SCOPE_HDD))
config.movielist.last_timer_videodir = ConfigText(default=resolveFilename(SCOPE_HDD))
config.movielist.videodirs = ConfigLocations(default=[resolveFilename(SCOPE_HDD)])
config.movielist.first_tags = ConfigText(default="")
config.movielist.second_tags = ConfigText(default="")
config.movielist.last_selected_tags = ConfigSet([], default=[])
# extra config.entries
config.movielist.showtime = ConfigInteger(default=MovieList.SHOW_TIME)
config.movielist.showdate = ConfigInteger(default=MovieList.SHOW_DATE)
config.movielist.showservice = ConfigInteger(default=MovieList.SHOW_SERVICE)
config.movielist.showtags = ConfigInteger(default=MovieList.HIDE_TAGS)

SHOW_ALL_MOVIES = _("Show all movies")

def getDateString():
    t = localtime()
    if t.tm_wday == 0:
        wday = "Montag"
    elif t.tm_wday == 1:
        wday = "Dienstag"
    elif t.tm_wday == 2:
        wday = "Mittwoch"
    elif t.tm_wday == 3:
        wday = "Donnerstag"
    elif t.tm_wday == 4:
        wday = "Freitag"
    elif t.tm_wday == 5:
        wday = "Samstag"
    elif t.tm_wday == 6:
        wday = "Sonntag"
    else:
        wday = ""
    if config.osd.language.value == "de_DE":
        desc = (("%s.%s.%s\n%s") % (t.tm_mday, t.tm_mon, t.tm_year, wday))
    else:
        desc = strftime("%d.%m.%Y\n%A", t)
    return desc

def getSortDescription():
    text = _("Sorted:") + " "
    if config.movielist.moviesort.value == MovieList.SORT_ALPHANUMERIC:
        return text + _("Alphabetically")
    if config.movielist.moviesort.value == MovieList.SORT_DESCRIPTION:
        return text + _("Description")
    if config.movielist.moviesort.value == MovieList.SORT_DATE_DESC:
        return text + _("Descending")
    if config.movielist.moviesort.value == MovieList.SORT_DATE_ASC:
        return text + _("Ascending")
    return text + _("Unknown")
    
def getBeginTimeString(info, serviceref):
    if not info or not serviceref:
        return ""
    begin = info.getInfo(serviceref, iServiceInformation.sTimeCreate)
    if not begin: 
        return ""
    if config.AdvancedMovieSelection.dateformat.value == "2":
        ft = FuzzyTime(begin)
        desc = ft[0] + ", " + ft[1]
    else:
        d = datetime.fromtimestamp(begin)
        desc = d.strftime("%d.%m.%Y - %H:%M")
    return desc

from Screens.LocationBox import LocationBox
def ScanLocationBox(session, text, dir, minFree=None):
    inhibitDirs = ["/bin", "/boot", "/dev", "/etc", "/lib", "/proc", "/sbin", "/sys", "/usr", "/var"]
    config.AdvancedMovieSelection.videodirs.load()
    return LocationBox(session, text=text, currDir=dir, bookmarks=config.AdvancedMovieSelection.videodirs, autoAdd=False, editDir=False, inhibitDirs=inhibitDirs, minFree=minFree)

class MovieContextMenu(Screen):
    def __init__(self, session, csel, service):
        Screen.__init__(self, session)
        self.csel = csel
        self.service = service
        self["actions"] = ActionMap(["OkCancelActions"],
            {
                "ok": self.okbuttonClick,
                "cancel": self.cancelClick
            })
        menu = []
        if config.AdvancedMovieSelection.use_wastebasket.value and config.AdvancedMovieSelection.show_wastebasket.value:
            menu.append((_("Wastebasket"), self.waste))
        if config.AdvancedMovieSelection.show_filter_by_description.value:
            menu.append((_("Filter by description"), boundFunction(self.openFilterByDescriptionChoice)))
        if config.AdvancedMovieSelection.show_set_vsr.value and not (self.service.flags & eServiceReference.mustDescent):
            menu.append((_("Set VSR"), boundFunction(self.openAccessChoice)))
        if config.AdvancedMovieSelection.hotplug.value and isinstance(service, eServiceReferenceHotplug):
            menu.append((_("Unmount") + " " + service.getName(), boundFunction(self.unmount)))
        if config.AdvancedMovieSelection.showtmdb.value:
            menu.append((_("TMDb Info & D/L"), boundFunction(self.imdbsearch)))
        if config.AdvancedMovieSelection.showthetvdb.value:
            menu.append((_("TheTVDB Info & D/L"), boundFunction(self.thetvdbsearch)))
        if config.AdvancedMovieSelection.showdelete.value and not self.service.flags & eServiceReference.mustDescent:
            menu.append((_("Delete"), self.delete))
        if config.AdvancedMovieSelection.showmove.value and not self.service.flags & eServiceReference.mustDescent:
            menu.append((_("Move/Copy"), self.movecopy))
        if config.AdvancedMovieSelection.showrename.value and self.service.type != eServiceReference.idUser:
            menu.append((_("Rename"), boundFunction(self.retitel, session, service)))
        if config.AdvancedMovieSelection.showsearch.value:
            menu.append((_("Movie search"), boundFunction(self.searchmovie)))
        if config.AdvancedMovieSelection.showmark.value and config.usage.load_length_of_movies_in_moviellist.value and not (self.service.flags & eServiceReference.mustDescent):
            menu.append((_("Mark movie as seen"), boundFunction(self.setMovieStatus, 1)))
            menu.append((_("Mark movie as unseen"), boundFunction(self.setMovieStatus, 0)))
        if config.AdvancedMovieSelection.pluginmenu_list.value and not self.service.flags & eServiceReference.mustDescent:
            menu.extend([(p.description, boundFunction(self.execPlugin, p)) for p in plugins.getPlugins(PluginDescriptor.WHERE_MOVIELIST)])
        if config.AdvancedMovieSelection.showsort.value:
            if config.movielist.moviesort.value != MovieList.SORT_ALPHANUMERIC:
                menu.append((_("Alphabetic sort"), boundFunction(self.sortBy, MovieList.SORT_ALPHANUMERIC)))
            if config.movielist.moviesort.value != MovieList.SORT_DESCRIPTION:
                menu.append((_("Sort by description"), boundFunction(self.sortBy, MovieList.SORT_DESCRIPTION)))
            if config.movielist.moviesort.value != MovieList.SORT_DATE_DESC:
                menu.append((_("Sort by date (descending)"), boundFunction(self.sortBy, MovieList.SORT_DATE_DESC)))
            if config.movielist.moviesort.value != MovieList.SORT_DATE_ASC:
                menu.append((_("Sort by date (ascending)"), boundFunction(self.sortBy, MovieList.SORT_DATE_ASC)))
        if config.AdvancedMovieSelection.showliststyle.value:
            menu.extend((
                (_("List style default"), boundFunction(self.listType, MovieList.LISTTYPE_ORIGINAL)),
                (_("List style extended"), boundFunction(self.listType, MovieList.LISTTYPE_EXTENDED)),
                (_("List style compact"), boundFunction(self.listType, MovieList.LISTTYPE_COMPACT)),
                (_("List style compact with description"), boundFunction(self.listType, MovieList.LISTTYPE_COMPACT_DESCRIPTION)),
                (_("List style single line"), boundFunction(self.listType, MovieList.LISTTYPE_MINIMAL)),
                (_("List style Advanced Movie Selection single line"), boundFunction(self.listType, MovieList.LISTTYPE_MINIMAL_AdvancedMovieSelection)),
            ))
        if config.AdvancedMovieSelection.showliststyle.value and config.movielist.listtype.value == MovieList.LISTTYPE_MINIMAL_AdvancedMovieSelection:
            if config.movielist.showservice.value == MovieList.SHOW_SERVICE:
                menu.append((_("Hide broadcaster"), boundFunction(self.showService, MovieList.HIDE_SERVICE)))
            else:
                menu.append((_("Show broadcaster"), boundFunction(self.showService, MovieList.SHOW_SERVICE)))
        if config.AdvancedMovieSelection.showliststyle.value and config.movielist.listtype.value == MovieList.LISTTYPE_MINIMAL_AdvancedMovieSelection or config.movielist.listtype.value == MovieList.LISTTYPE_ORIGINAL or config.movielist.listtype.value == MovieList.LISTTYPE_COMPACT and config.movielist.showservice.value == MovieList.HIDE_SERVICE:
            if config.movielist.showtags.value == MovieList.SHOW_TAGS:
                menu.append((_("Hide tags in movielist"), boundFunction(self.showTags, MovieList.HIDE_TAGS)))
            else:
                menu.append((_("Show tags in movielist"), boundFunction(self.showTags, MovieList.SHOW_TAGS)))
        if config.AdvancedMovieSelection.showliststyle.value:
            if config.movielist.description.value == MovieList.SHOW_DESCRIPTION:
                menu.append((_("Hide extended description"), boundFunction(self.showDescription, MovieList.HIDE_DESCRIPTION)))
            else:
                menu.append((_("Show extended description"), boundFunction(self.showDescription, MovieList.SHOW_DESCRIPTION)))
            if config.movielist.showdate.value == MovieList.SHOW_DATE:
                menu.append((_("Hide date entry in movielist"), boundFunction(self.showDate, MovieList.HIDE_DATE)))
            else:
                menu.append((_("Show date entry in movielist"), boundFunction(self.showDate, MovieList.SHOW_DATE)))
            if config.movielist.showtime.value == MovieList.SHOW_TIME:
                menu.append((_("Hide runtime entry in movielist"), boundFunction(self.showTime, MovieList.HIDE_TIME)))
            else:
                menu.append((_("Show runtime entry in movielist"), boundFunction(self.showTime, MovieList.SHOW_TIME)))
        if config.AdvancedMovieSelection.showextras.value:
            if config.AdvancedMovieSelection.showfoldersinmovielist.value:
                menu.append((_("Hide folders in movielist"), boundFunction(self.showFolders, False)))
            else:
                menu.append((_("Show folders in movielist"), boundFunction(self.showFolders, True)))
            
            if config.usage.load_length_of_movies_in_moviellist.value:
                if not config.AdvancedMovieSelection.showpercentinmovielist.value:
                    if config.AdvancedMovieSelection.showprogessbarinmovielist.value:
                        menu.append((_("Hide progressbar in movielist"), boundFunction(self.showProgressbar, False)))
                    else:
                        menu.append((_("Show progressbar in movielist"), boundFunction(self.showProgressbar, True)))
                if not config.AdvancedMovieSelection.showprogessbarinmovielist.value:
                    if config.AdvancedMovieSelection.showpercentinmovielist.value:
                        menu.append((_("Hide percent in movielist"), boundFunction(self.showPercent, False)))
                    else:
                        menu.append((_("Show percent in movielist"), boundFunction(self.showPercent, True)))
                if config.AdvancedMovieSelection.showiconstatusinmovielist.value:
                    menu.append((_("Hide movie status icon in movielist"), boundFunction(self.showStatusIcon, False)))
                else:
                    menu.append((_("Show movie status icon in movielist"), boundFunction(self.showStatusIcon, True)))
                if config.AdvancedMovieSelection.showcolorstatusinmovielist.value:
                    menu.append((_("Hide movie color status in movielist"), boundFunction(self.showStatusColor, False)))
                else:
                    menu.append((_("Show movie color status in movielist"), boundFunction(self.showStatusColor, True)))
        if config.AdvancedMovieSelection.showcolorkey.value:        
            menu.append((_("Color key settings"), self.setupbutton))     
        if config.AdvancedMovieSelection.showcoveroptions2.value:
            menu.append((_("Download and save movie info/cover for all movies"), boundFunction(self.downloadMovieInfoAll)))
        if config.AdvancedMovieSelection.showcoveroptions.value and not self.service.flags & eServiceReference.mustDescent:
            menu.append((_("Download and save movie info/cover"), self.downloadMovieInfo))              
        if config.AdvancedMovieSelection.show_update_genre.value:
            menu.append((_("Update all genre in meta from eit"), boundFunction(self.updateMetaFromEit)))
        if config.AdvancedMovieSelection.show_cover_del.value:
            menu.append((_("Delete cover"), boundFunction(self.deleteCover)))
        if config.AdvancedMovieSelection.show_info_del.value:
            menu.append((_("Delete movie info"), boundFunction(self.deleteInfos)))
        if config.AdvancedMovieSelection.show_info_cover_del.value:
            menu.append((_("Delete movie info and cover"), boundFunction(self.deleteInfoCover)))   
        if config.AdvancedMovieSelection.showmovietagsinmenu.value and not service.flags & eServiceReference.mustDescent:
            menu.append((_("Movie tags"), boundFunction(self.movietags)))
        if config.AdvancedMovieSelection.showfiltertags.value:
            menu.append((_("Filter by Tags"), boundFunction(self.filterbytags)))
        if config.AdvancedMovieSelection.showmenu.value and config.AdvancedMovieSelection.show_infobar_position.value:
            menu.append((_("Setup Moviebar position"), self.moviebarsetup))
        if pluginPresent.YTTrailer == True and config.AdvancedMovieSelection.showtrailer.value and not (self.service.flags & eServiceReference.mustDescent): 
            menu.append((_("Search Trailer on web"), boundFunction(self.showTrailer)))
        if config.AdvancedMovieSelection.show_remote_setup.value:
            menu.append((_("Clientbox setup"), boundFunction(self.serversetup)))
        if config.AdvancedMovieSelection.show_backup_restore.value:
            menu.append((_("Backup/Restore"), boundFunction(self.openBackupRestore)))
        if config.AdvancedMovieSelection.show_location_indexing.value:
            menu.append((_("Select scan locations for movie library"), self.selectScanLocations))
        if config.AdvancedMovieSelection.showmenu.value:
            menu.append((_("Setup"), boundFunction(self.menusetup)))
        self["menu"] = MenuList(menu)
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(_("Advanced Movie Selection Menu"))

    def openBackupRestore(self):
        from .AdvancedMovieSelectionSetup import BackupRestore
        self.session.open(BackupRestore)
        self.close()

    def openAccessChoice(self):
        self.csel.openAccessChoice()
        self.close()

    def openFilterByDescriptionChoice(self):
        self.csel.openFilterByDescriptionChoice()
        self.close()

    def thetvdbsearch(self):
        from SearchTVDb import TheTVDBMain
        self.session.openWithCallback(self.closeafterfinish, TheTVDBMain, self.service)

    def updateMetaFromEit(self):
        self.csel.list.updateMetaFromEit()
        self.csel.reloadList()
        self.close()
        
    def unmount(self):
        res = self.csel["list"].unmount(self.service)
        if res == 0:
            self.session.open(MessageBox, _("The device '%s' can now removed!") % (self.service.getName()), MessageBox.TYPE_INFO)
            self.csel.reloadList()
            self.close()        
        else:
            self.session.open(MessageBox, _("Error occurred during unmounting device!"), MessageBox.TYPE_ERROR)

    def serversetup(self):
        self.session.open(ClientSetup)

    def waste(self):
        from .Wastebasket import Wastebasket
        self.session.openWithCallback(self.closeafterfinish, Wastebasket)

    def showTrailer(self):
        if pluginPresent.YTTrailer == True:
            eventname = ServiceCenter.getInstance().info(self.service).getName(self.service)
            self.session.open(YTTrailerList, eventname)
        else:
            pass

    def moviebarsetup(self):
        self.session.open(MoviebarPositionSetup)

    def checkConnection(self):
        try:
            import socket 
            print(socket.gethostbyname('www.google.com'))
            return True
        except:
            self.session.openWithCallback(self.close, MessageBox, _("No internet connection available!"), MessageBox.TYPE_ERROR)
            return False

    def downloadMovieInfo(self):
        if self.checkConnection() == False:
            return
        if len(self.csel.list.multiSelection) == 0:
            self.session.openWithCallback(self.closeafterfinish, DownloadMovies, self.csel.list.list, self.service)
        else:
            self.downloadSelectedMovieInfo()

    def closeafterfinish(self, retval=None):
        self.csel.updateDescription()
        self.csel.reloadList()
        self.close()

    def downloadMovieInfoAll(self):
        if self.checkConnection() == False:
            return
        if len(self.csel.list.multiSelection) == 0:
            self.session.openWithCallback(self.closeafterfinish, DownloadMovies, self.csel.list.list)
        else:
            self.downloadSelectedMovieInfo()

    def downloadSelectedMovieInfo(self):
        items = []
        for item in self.csel.list.multiSelection:
            items.append([item, 0])
        self.session.openWithCallback(self.closeafterfinish, DownloadMovies, items)

    def retitel(self, session, service):
        self.session.openWithCallback(self.closeafterfinish, MovieRetitle, service)

    def imdbsearch(self):
        searchTitle = ServiceCenter.getInstance().info(self.service).getName(self.service)
        self.session.openWithCallback(self.closeafterfinish, TMDbMainsave, searchTitle, service=self.service)

    def menusetup(self):
        self.session.openWithCallback(self.cancelClick, AdvancedMovieSelectionSetup, self.csel)
        
    def setupbutton(self):
        self.session.open(AdvancedMovieSelectionButtonSetup, self.csel)

    def movecopy(self):
        if not (self.service.flags & eServiceReference.mustDescent):
            self.session.openWithCallback(self.close, MovieMove, self.csel, self.service)
        else:
            self.session.open(MessageBox, _("Move/Copy not possible here!"), MessageBox.TYPE_INFO)

    def movietags(self):
        self.session.open(MovieTagEditor, service=self.service, parent=self.session.current_dialog)

    def filterbytags(self):
        self.csel.showTagsSelect()
        self.csel.reloadList()
        self.close()

    def searchmovie(self):
        from .AdvancedKeyboard import AdvancedKeyBoard
        self.session.openWithCallback(self.searchCallback, AdvancedKeyBoard, _("Enter text to search for"))
        
    def searchCallback(self, retval):
        search = retval
        print(search)
        if search == "" or search is None:
            self.closeafterfinish()
            return
        newList = []
        for movie_tuple in self.csel["list"].list:
            mi = movie_tuple[0]
            if search.lower() in mi.name.lower():
                newList.append(movie_tuple)

        self.csel["list"].l.setList(newList)
        self.csel["list"].moveToIndex(0)
        self.closeafterfinish()

    def setMovieStatus(self, status):
        self.csel.setMovieStatus(status)
        self.close()

    def okbuttonClick(self):
        self["menu"].getCurrent()[1]()

    def cancelClick(self):
        #self.csel["list"].updateHotplugDevices()
        #self.csel.reloadList()
        self.close(False)

    def sortBy(self, newType):
        self.csel.setSortType(newType)
        self.csel.reloadList()
        self.close()

    def listType(self, newType):
        config.movielist.listtype.value = newType
        self.csel.setListType(newType)
        self.csel.list.redrawList()
        self.close()

    def showDescription(self, newType):
        config.movielist.description.value = newType
        self.csel.setDescriptionState(newType)
        self.csel.updateDescription()
        self.close()

    def showFolders(self, value):
        config.AdvancedMovieSelection.showfoldersinmovielist.value = value
        config.AdvancedMovieSelection.showfoldersinmovielist.save()
        self.csel.showFolders(value)
        self.csel.reloadList()
        self.close()

    def showProgressbar(self, value):
        config.AdvancedMovieSelection.showprogessbarinmovielist.value = value
        config.AdvancedMovieSelection.showprogessbarinmovielist.save()
        self.csel.showProgressbar(value)
        self.csel.reloadList()
        self.close()

    def showPercent(self, value):
        config.AdvancedMovieSelection.showpercentinmovielist.value = value
        config.AdvancedMovieSelection.showpercentinmovielist.save()        
        self.csel.showPercent(value)
        self.csel.reloadList()
        self.close()

    def showStatusIcon(self, value):
        config.AdvancedMovieSelection.showiconstatusinmovielist.value = value
        config.AdvancedMovieSelection.showiconstatusinmovielist.save()
        self.csel.showStatusIcon(value)
        self.csel.reloadList()
        self.close()

    def showStatusColor(self, value):
        config.AdvancedMovieSelection.showcolorstatusinmovielist.value = value
        config.AdvancedMovieSelection.showcolorstatusinmovielist.save()
        self.csel.showStatusColor(value)
        self.csel.reloadList()
        self.close()
        
    def showDate(self, value):
        config.movielist.showdate.value = value
        config.movielist.showdate.save()
        self.csel.showDate(value)
        self.csel.reloadList()
        self.close()
        
    def showTime(self, value):
        config.movielist.showtime.value = value
        config.movielist.showtime.save()
        self.csel.showTime(value)
        self.csel.reloadList()
        self.close()

    def showTags(self, value):
        config.movielist.showtags.value = value
        config.movielist.showtags.save()
        self.csel.showTags(value)
        self.csel.reloadList()
        self.close()
        
    def showService(self, value):
        config.movielist.showservice.value = value
        config.movielist.showservice.save()
        self.csel.showService(value)
        self.csel.reloadList()
        self.close()

    def execPlugin(self, plugin):
        if not (self.service.flags & eServiceReference.mustDescent):
            print("Starting plugin:", plugin.description)
            import inspect
            params = inspect.getargspec(plugin.__call__)
            print("Params:", params)
            if len(self.csel.list.multiSelection) > 0 and len(params[0]) >= 3:
                plugin(self.session, self.service, self.csel.list.multiSelection)
            else:
                plugin(self.session, self.service)

    def delete(self):
        self.csel.delete()
        self.close()
        
    def checkDeleteable(self):
        serviceHandler = ServiceCenter.getInstance()
        info = serviceHandler.info(self.service)
        name = info and info.getName(self.service)
        if self.service.flags & eServiceReference.mustDescent:
            if self.service.getName() == "..":
                return None
        return name
    
    def deleteInfoCover(self):
        name = self.checkDeleteable()
        if name:
            if config.AdvancedMovieSelection.askdelete.value:
                self.session.openWithCallback(self.deleteInfoCoverConfirmed, MessageBox, _("Do you really want to delete info/cover from:\n%s?") % (name))
            else:
                self.deleteInfoCoverConfirmed(True)
        else:
            self.session.openWithCallback(self.close, MessageBox, _("You cannot delete this!"), MessageBox.TYPE_ERROR)

    def deleteInfoCoverConfirmed(self, confirmed):
        if not confirmed:
            return self.close()
        try:
            path = self.service.getPath()
            if os.path.isfile(path):
                path = os.path.splitext(path)[0]
            eConsoleAppContainer().execute("rm -f \"%s\"" % (path + ".eit"))
            eConsoleAppContainer().execute("rm -f \"%s\"" % (path + ".jpg"))
            self.csel.updateDescription()
            self.csel["freeDiskSpace"].update()
            self.close()
        except:
            printStackTrace()

    def deleteCover(self):
        name = self.checkDeleteable()
        if name:
            if config.AdvancedMovieSelection.askdelete.value:
                self.session.openWithCallback(self.deleteCoverConfirmed, MessageBox, _("Do you really want to delete cover from:\n%s?") % (name))
            else:
                self.deleteCoverConfirmed(True)
        else:
            self.session.openWithCallback(self.close, MessageBox, _("You cannot delete this!"), MessageBox.TYPE_ERROR)

    def deleteCoverConfirmed(self, confirmed):
        if not confirmed:
            return self.close()
        try:
            path = self.service.getPath()
            if os.path.isfile(path):
                path = os.path.splitext(path)[0] + ".jpg"
            elif isinstance(self.service, eServiceReferenceDvd):
                path = path + ".jpg"
            
            cmd = "rm -f \"%s\"" % (path)
            eConsoleAppContainer().execute(cmd)
            self.csel.updateDescription()
            self.csel["freeDiskSpace"].update()
            self.close()
        except:
            pass

    def deleteInfos(self):
        name = self.checkDeleteable()
        if name:
            if config.AdvancedMovieSelection.askdelete.value:
                self.session.openWithCallback(self.deleteInfosConfirmed, MessageBox, _("Do you really want to delete movie info from:\n%s?") % (name))
            else:
                self.deleteInfosConfirmed(True)
        else:
            self.session.openWithCallback(self.close, MessageBox, _("You cannot delete this!"), MessageBox.TYPE_ERROR)

    def deleteInfosConfirmed(self, confirmed):
        if not confirmed:
            return self.close()
        try:
            path = self.service.getPath()
            if os.path.isfile(path):
                path = os.path.splitext(path)[0] + ".eit"
            elif isinstance(self.service, eServiceReferenceDvd):
                path = path + ".eit"

            cmd = "rm -f \"%s\"" % (path)
            eConsoleAppContainer().execute(cmd)
            self.csel.updateDescription()
            self.csel["freeDiskSpace"].update()
            self.close()
        except:
            pass
    
    def selectScanLocations(self):
        self.csel.selectScanLocations()
        self.close()        
        
class SelectionEventInfo:
    def __init__(self):
        self["Service"] = ServiceEvent()
        self.list.connectSelChanged(self.__selectionChanged)
        self.timer = eTimer()
        self.timer.callback.append(self.updateEventInfo)
        self.onShown.append(self.__selectionChanged)

    def __selectionChanged(self):
        self.timer.start(300, True)

    def updateEventInfo(self):
        self.updateGUI()
        if self.execing and config.movielist.description.value == MovieList.SHOW_DESCRIPTION or config.AdvancedMovieSelection.showpreview.value or config.AdvancedMovieSelection.video_preview.value:
            evt = self["list"].getCurrentEvent()
            serviceref = self.getCurrent()
            if serviceref is not None and isinstance(self["list"].root, eServiceReferenceListAll):
                self.updateTitle(os.path.dirname(serviceref.getPath()))
            if config.movielist.description.value == MovieList.SHOW_DESCRIPTION:
                if evt:
                    self["Service"].newService(serviceref)
                else:
                    self["Service"].newService(None)
                self.updateName(serviceref, evt)
            if config.AdvancedMovieSelection.showpreview.value:
                self.loadPreview(serviceref)
            if config.AdvancedMovieSelection.video_preview_autostart.value:
                self.preparePlayMovie(serviceref, evt)
            if not config.AdvancedMovieSelection.showpreview.value and config.AdvancedMovieSelection.video_preview.value:
                self.loadPreview(serviceref)        
        
class AdvancedMovieSelection_summary(Screen):
    def __init__(self, session, parent):
        self.skinName = ["AdvancedMovieSelection_summary"]
        Screen.__init__(self, session, parent)
        self["ShortDesc"] = Label("")
        self["Seperator1"] = StaticText("")
        self["Seperator2"] = StaticText("")
        self.hideSeperator()
       
    def updateShortDescription(self, desc):
        self["ShortDesc"].setText(desc)

    def showSeperator(self):
        if TFT_8000_Present:
            self["Seperator1"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "images/sep_tft.png"))
            self["Seperator2"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "images/sep_tft.png"))
        else:
            self["Seperator1"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "images/sep_lcd_oled.png"))
            self["Seperator2"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "images/sep_lcd_oled.png"))
    
    def hideSeperator(self):
        self["Seperator1"].setText("")    
        self["Seperator2"].setText("")    

class MovieSelection(Screen, HelpableScreen, SelectionEventInfo, MoviePreview, QuickButton, VideoPreview, MovieSearch):
    LIB_UPDATE_INTERVAL = 250
    def __init__(self, session, selectedmovie=None, showLastDir=False):
        print("enter movieselection")
        self.stopwatch = StopWatch()
        Screen.__init__(self, session)
        HelpableScreen.__init__(self)
        MoviePreview.__init__(self, session)
        VideoPreview.__init__(self)
        self.skinName = ["AdvancedMovieSelection"]
        if config.AdvancedMovieSelection.showpreview.value and config.AdvancedMovieSelection.minitv.value:
            self.skinName.insert(0, SkinTools.appendResolution("AdvancedMovieSelection"))
        if not config.AdvancedMovieSelection.showpreview.value and config.AdvancedMovieSelection.minitv.value:
            self.skinName.insert(0, SkinTools.appendResolution("AdvancedMovieSelection1"))
        if config.AdvancedMovieSelection.showpreview.value and not config.AdvancedMovieSelection.minitv.value:
            self.skinName.insert(0, SkinTools.appendResolution("AdvancedMovieSelection_noMiniTV_"))
        if not config.AdvancedMovieSelection.showpreview.value and not config.AdvancedMovieSelection.minitv.value:
            self.skinName.insert(0, SkinTools.appendResolution("AdvancedMovieSelection1_noMiniTV_"))
        if config.AdvancedMovieSelection.showpreview.value and config.AdvancedMovieSelection.video_preview.value and config.AdvancedMovieSelection.video_preview_fullscreen.value and config.movielist.description.value == MovieList.SHOW_DESCRIPTION:
            self.skinName.insert(0, SkinTools.appendResolution("AdvancedMovieSelection_Preview_"))
        if config.AdvancedMovieSelection.showpreview.value and config.AdvancedMovieSelection.video_preview.value and config.AdvancedMovieSelection.video_preview_fullscreen.value and config.movielist.description.value == MovieList.HIDE_DESCRIPTION:
            self.skinName.insert(0, SkinTools.appendResolution("AdvancedMovieSelection_Preview_noDescription_"))
        if not config.AdvancedMovieSelection.showpreview.value and config.AdvancedMovieSelection.video_preview.value and config.AdvancedMovieSelection.video_preview_fullscreen.value and config.movielist.description.value == MovieList.SHOW_DESCRIPTION:
            self.skinName.insert(0, SkinTools.appendResolution("AdvancedMovieSelection_Preview_noCover_"))
        if not config.AdvancedMovieSelection.showpreview.value and config.AdvancedMovieSelection.video_preview.value and config.AdvancedMovieSelection.video_preview_fullscreen.value and config.movielist.description.value == MovieList.HIDE_DESCRIPTION:
            self.skinName.insert(0, SkinTools.appendResolution("AdvancedMovieSelection_Preview_noDescription_noCover_"))
        self.tags = []
        self.showLastDir = showLastDir
        if not config.AdvancedMovieSelection.startonfirst.value and not selectedmovie:
            if config.AdvancedMovieSelection.last_selected_service.value != "":
                selectedmovie = eServiceReference(config.AdvancedMovieSelection.last_selected_service.value)
        if selectedmovie:
            self.selected_tags = config.movielist.last_selected_tags.value
        else:
            self.selected_tags = None
        self.selected_tags_ele = None

        self.movemode = False
        self.bouquet_mark_edit = False

        self.delayTimer = eTimer()
        self.delayTimer.callback.append(self.updateHDDData)

        self["waitingtext"] = Label(_("Please wait... Loading list..."))
        self["DescriptionBorder"] = Pixmap()
        self["DescriptionBorder"].hide()
        self["warning"] = Label()
        if not config.AdvancedMovieSelection.askdelete.value and config.AdvancedMovieSelection.showinfo.value:
            self["warning"].setText(_("ATTENTION: Ask before delete is disabled!"))
            
        self["list"] = MovieList(None,
            config.movielist.listtype.value,
            config.movielist.moviesort.value,
            config.movielist.description.value,
            config.AdvancedMovieSelection.showfoldersinmovielist.value,
            config.AdvancedMovieSelection.showprogessbarinmovielist.value,
            config.AdvancedMovieSelection.showpercentinmovielist.value,
            config.AdvancedMovieSelection.showiconstatusinmovielist.value,
            config.AdvancedMovieSelection.showcolorstatusinmovielist.value,
            config.movielist.showdate.value,
            config.movielist.showtime.value,
            config.movielist.showservice.value,
            config.movielist.showtags.value)
        self.list = self["list"]
        self.selectedmovie = selectedmovie
        SelectionEventInfo.__init__(self)
        self["MovieService"] = ServiceEvent()
        self["MovieSize"] = ServiceEvent()
        self["Movietitle"] = StaticText()
        # TODO: ???self["Movielocation"] = StaticText()
        self["freeDiskSpace"] = self.diskinfo = DiskInfo(config.movielist.last_videodir.value, DiskInfo.FREE, update=False)
        self["InfobarActions"] = HelpableActionMap(self, "InfobarActions",
            {
                "showMovies": (self.doPathSelect, _("Select the movie path")),
                "showRadio": (self.radioButton, _("Multiselection")),
            })
        self["MovieSelectionActions"] = HelpableActionMap(self, "MovieSelectionActions",
            {
                "contextMenu": (self.doContext, _("Advanced movielist menu")),
                "showEventInfo": (self.showEventInformation, _("Show event details")),
            })
        self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
            {
                "cancel": (self.abort, _("Exit movielist")),
                "ok": (self.movieSelected, _("Select movie")),
            })
        self["EPGSelectActions"] = HelpableActionMap(self, "EPGSelectActions",
            {
                "nextBouquet": (self.nextBouquet, _("Video preview jump forward")),
                "prevBouquet": (self.prevBouquet, _("Video preview jump backward")),
            })
        
        self["ChannelSelectBaseActions"] = HelpableActionMap(self, "ChannelSelectBaseActions",
            {
                "nextMarker": (self.nextMarker, _("Jump to next marker")),
                "prevMarker": (self.prevMarker, _("Jump to previous marker")),
            })
        self["MediaPlayerActions"] = HelpableActionMap(self, "MediaPlayerActions",
            {
                "stop": (self.stopButton, _("Start/Stop video preview")),
            })
        
        QuickButton.__init__(self)
        self.onShow.append(self.go)
        self.onLayoutFinish.append(self.saveListsize)
        self.inited = False
        MovieSearch.__init__(self)
        self.__dbUpdate = eTimer()
        self.__dbUpdate.callback.append(self.libraryUpdateTimerEvent)
        print("end constructor", str(self.stopwatch.elapsed))
    
    def createSummary(self):
        return AdvancedMovieSelection_summary
        
    def radioButton(self):
        if self.list.toggleSelection():
            #self.list.moveDown()
            idx = self.list.getCurrentIndex()
            self.list.moveToIndex(min(idx + 1, len(self.list.list) - 1))

    def getTrashMessage(self, qty, waste, recording, name=""):
        if qty == 1:
            if waste:
                if recording:
                    return (_("%s is currently recording!") % (name) + _("\n\nThe timer for %s will be delete for stop the recording and after this the movie will be move to trashcan.\n\nDo you really want to continue?") % (name))
                else:
                    return _("Do you really want to move %s to trashcan?") % (name)
            else:
                if recording:
                    return (_("%s is currently recording!") % (name) + _("\n\nThe timer for %s will be delete for stop the recording and after this the movie will be deleted.\n\nDo you really want to continue?") % (name))
                else:
                    return _("Do you really want to delete %s?") % (name)
        else:
            timer_text = recording and _("Recordings are active, the timer(s) will also be deleted!\n") or ""
            if waste: 
                return timer_text + _("Do you really want to move selected movies to trashcan?")
            else:
                return timer_text + _("Do you really want to delete selected movies?")

    def delete(self):
        self.service = self.getCurrent()
        if self.service.flags & eServiceReference.mustDescent:
            self.session.open(MessageBox, _("This cannot deleted, please select a movie for!"), MessageBox.TYPE_INFO)
            return

        if len(self.list.multiSelection) > 0:
            self.to_delete = self.list.multiSelection[:]
        else:
            self.to_delete = [self.service]
        
        serviceHandler = ServiceCenter.getInstance()
        info = serviceHandler.info(self.service)
        name = info and info.getName(self.service) or _("this recording")

        recording = False
        if NavigationInstance.instance.getRecordings():
            for timer in NavigationInstance.instance.RecordTimer.timer_list:
                if timer.state == TimerEntry.StateRunning:
                    try:
                        filename = "%s.ts" % timer.Filename
                    except:
                        filename = ""
                    for serviceref in self.to_delete:
                        if filename and os.path.realpath(filename) == os.path.realpath(serviceref.getPath()):
                            recording = True
                            continue
  
        if not config.AdvancedMovieSelection.askdelete.value:
            self.deleteConfirmed(True)
        else:
            text = self.getTrashMessage(len(self.to_delete), config.AdvancedMovieSelection.use_wastebasket.value, recording, name)
            self.session.openWithCallback(self.deleteConfirmed, MessageBox, text)

    def stopRemoveTimer(self, file_path):
        if NavigationInstance.instance.getRecordings():
            for timer in NavigationInstance.instance.RecordTimer.timer_list:
                if timer.isRunning():
                    try:
                        filename = "%s.ts" % timer.Filename
                    except:
                        filename = ""
                    if filename and os.path.realpath(filename) == os.path.realpath(file_path):
                        timer.afterEvent = AFTEREVENT.NONE
                        timer.abort()
                        if timer.repeated == 0:
                            self.session.nav.RecordTimer.removeEntry(timer)
                        return
        
    def deleteTrashConfirmed(self, confirmed):
        if not confirmed:
            return
        try:
            for item in self.to_delete:
                self.stopRemoveTimer(item.getPath())
                Trashcan.trash(item.getPath())
                self["list"].removeService(item)
        except Exception as e:
            print(e)
            self.session.open(MessageBox, _("Delete failed!"), MessageBox.TYPE_ERROR)

    def deleteConfirmed(self, confirmed):
        if not confirmed:
            return

        # remove from scanner
        movieScanner.removeMovie(self.to_delete)
        self.list.updateMovieLibraryEntry()
        if config.AdvancedMovieSelection.use_wastebasket.value:
            self.deleteTrashConfirmed(confirmed)
            return
        
        for item in self.to_delete:
            self.stopRemoveTimer(item.getPath())
            self["list"].removeService(item)

        AsynchTrash(self.to_delete, 100)            

    def updateCurrentSelection(self, dummy=None):
        self.list.updateCurrentSelection()

    def updateName(self, serviceref, event):
        # TODO: ???location = (_("Movie location: %s") % config.movielist.last_videodir.value)
        # TODO: ???self["Movielocation"].setText(location)
        if event:
            moviename = event.getEventName()
            self["Movietitle"].setText(moviename)
            self["MovieService"].newService(serviceref)
            self["MovieSize"].newService(serviceref)
            desc = event.getShortDescription()        
            if moviename == desc or desc == "":
                if config.AdvancedMovieSelection.show_date_shortdesc.value and config.AdvancedMovieSelection.show_begintime.value:
                    info = self["list"].getCurrentInfo()
                    desc = getBeginTimeString(info, serviceref)
                    self.summaries.showSeperator()
                    self.summaries.updateShortDescription(desc)
                elif config.AdvancedMovieSelection.show_date_shortdesc.value and not config.AdvancedMovieSelection.show_begintime.value:
                    desc = getDateString()
                    self.summaries.showSeperator()
                    self.summaries.updateShortDescription(desc)
                else:
                    desc = ""
                    self.summaries.hideSeperator()
                    self.summaries.updateShortDescription(desc)
            else:
                self.summaries.showSeperator()
                self.summaries.updateShortDescription(desc)
        else:
            desc = ""
            self.summaries.hideSeperator()
            self.summaries.updateShortDescription(desc)
            self["Movietitle"].setText(_("Advanced Movie Selection"))
            self["MovieService"].newService(None)
            self["MovieSize"].newService(None)

    def updateDescription(self):
        if config.movielist.description.value == MovieList.SHOW_DESCRIPTION:
            self["DescriptionBorder"].show()
            self["list"].instance.resize(eSize(self.listWidth, self.listHeight - self["DescriptionBorder"].instance.size().height()))
        else:
            self["Service"].newService(None)
            self["DescriptionBorder"].hide()
            self["list"].instance.resize(eSize(self.listWidth, self.listHeight))
        if config.AdvancedMovieSelection.video_preview_fullscreen.value and config.movielist.description.isChanged():
            self.session.open(MessageBox, _("Some settings changes require close/reopen the movielist to take effect."), type=MessageBox.TYPE_INFO)

    def updateSettings(self):
        self.updateVideoPreviewSettings()
    
    def nextBouquet(self):
        self.jumpForward()

    def prevBouquet(self):
        self.jumpBackward()

    def nextMarker(self):
        self["list"].moveToNextMarker()

    def prevMarker(self):
        self["list"].moveToPrevMarker()

    def stopButton(self):
        self.togglePreviewStatus(self.getCurrent())
    
    def showEventInformation(self):
        if pluginPresent.IMDb and pluginPresent.OFDb and pluginPresent.TMDb and config.AdvancedMovieSelection.Eventinfotyp.value == "Ei":
            self.showConfirmedInfo([None, "Ei"])
        elif pluginPresent.IMDb and pluginPresent.OFDb and pluginPresent.TMDb and config.AdvancedMovieSelection.Eventinfotyp.value == "Ti":
            self.showConfirmedInfo([None, "Ti"])
        elif pluginPresent.IMDb and pluginPresent.OFDb and pluginPresent.TMDb and config.AdvancedMovieSelection.Eventinfotyp.value == "Ii":
            self.showConfirmedInfo([None, "Ii"])
        elif pluginPresent.IMDb and pluginPresent.OFDb and pluginPresent.TMDb and config.AdvancedMovieSelection.Eventinfotyp.value == "Oi":
            self.showConfirmedInfo([None, "Oi"])
        else:
            if pluginPresent.IMDb and not pluginPresent.OFDb and not pluginPresent.TMDb and config.AdvancedMovieSelection.Eventinfotyp2.value == "Ei":
                self.showConfirmedInfo([None, "Ei"])
            elif pluginPresent.IMDb and not pluginPresent.OFDb and not pluginPresent.TMDb and config.AdvancedMovieSelection.Eventinfotyp2.value == "Ii":
                self.showConfirmedInfo([None, "Ii"])
            else:
                if pluginPresent.OFDb and not pluginPresent.IMDb and not pluginPresent.TMDb and config.AdvancedMovieSelection.Eventinfotyp3.value == "Ei":
                    self.showConfirmedInfo([None, "Ei"])
                elif pluginPresent.OFDb and not pluginPresent.IMDb and not pluginPresent.TMDb and config.AdvancedMovieSelection.Eventinfotyp3.value == "Oi":
                    self.showConfirmedInfo([None, "Oi"])
                else:
                    if pluginPresent.TMDb and not pluginPresent.OFDb and not pluginPresent.IMDb and config.AdvancedMovieSelection.Eventinfotyp4.value == "Ei":
                        self.showConfirmedInfo([None, "Ei"])
                    elif pluginPresent.TMDb and not pluginPresent.OFDb and not pluginPresent.IMDb and config.AdvancedMovieSelection.Eventinfotyp4.value == "Ti":
                        self.showConfirmedInfo([None, "Ti"])
                    else:
                        if pluginPresent.TMDb and not pluginPresent.OFDb and pluginPresent.IMDb and config.AdvancedMovieSelection.Eventinfotyp5.value == "Ei":
                            self.showConfirmedInfo([None, "Ei"])
                        elif pluginPresent.TMDb and not pluginPresent.OFDb and pluginPresent.IMDb and config.AdvancedMovieSelection.Eventinfotyp5.value == "Ti":
                            self.showConfirmedInfo([None, "Ti"])
                        elif pluginPresent.TMDb and not pluginPresent.OFDb and pluginPresent.IMDb and config.AdvancedMovieSelection.Eventinfotyp5.value == "Ii":
                            self.showConfirmedInfo([None, "Ii"])
                        else:
                            if pluginPresent.TMDb and pluginPresent.OFDb and not pluginPresent.IMDb and config.AdvancedMovieSelection.Eventinfotyp6.value == "Ei":
                                self.showConfirmedInfo([None, "Ei"])
                            elif pluginPresent.TMDb and pluginPresent.OFDb and not pluginPresent.IMDb and config.AdvancedMovieSelection.Eventinfotyp6.value == "Ti":
                                self.showConfirmedInfo([None, "Ti"])
                            elif pluginPresent.TMDb and pluginPresent.OFDb and not pluginPresent.IMDb and config.AdvancedMovieSelection.Eventinfotyp6.value == "Oi":
                                self.showConfirmedInfo([None, "Oi"])
                            else:
                                if not pluginPresent.TMDb and pluginPresent.OFDb and pluginPresent.IMDb and config.AdvancedMovieSelection.Eventinfotyp7.value == "Ei":
                                    self.showConfirmedInfo([None, "Ei"])
                                elif not pluginPresent.TMDb and pluginPresent.OFDb and pluginPresent.IMDb and config.AdvancedMovieSelection.Eventinfotyp7.value == "Ii":
                                    self.showConfirmedInfo([None, "Ii"])
                                elif not pluginPresent.TMDb and pluginPresent.OFDb and pluginPresent.IMDb and config.AdvancedMovieSelection.Eventinfotyp7.value == "Oi":
                                    self.showConfirmedInfo([None, "Oi"])
                                else:
                                    self.showConfirmedInfo([None, "Ei"])

    def showConfirmedInfo(self, answer):
        event = self["list"].getCurrentEvent()
        answer = answer and answer[1]
        if answer == "Ei":
            if event is not None:
                from .AdvancedMovieSelectionEventView import EventViewSimple
                from ServiceReference import ServiceReference
                serviceref = self.getCurrent()
                evt = self["list"].getCurrentEvent()
                if evt:
                    self.session.open(EventViewSimple, evt, serviceref, self.eventViewCallback)
        if answer == "Ii":
            if event is not None:
                IeventName = event.getEventName()
                self.session.open(IMDB, IeventName)
        if answer == "Oi":
            if event is not None:
                IeventName = event.getEventName()
                self.session.open(OFDB, IeventName)
        if answer == "Ti":
            if event is not None:
                eventName = event.getEventName()
                self.session.open(TMDbMain, eventName) 

    def eventViewCallback(self, setEvent, setService, val):
        l = self["list"]
        old = (l.getCurrentEvent(), l.getCurrent())
        if val == -1:
            self.moveUp()
        elif val == +1:
            self.moveDown()
        cur = (l.getCurrentEvent(), l.getCurrent())
        if cur[0] is None and cur[1] != old[1]:
            self.eventViewCallback(setEvent, setService, val)
        else:
            setService(cur[1])
            setEvent(cur[0])

    def moveUp(self):
        self.list.moveUp()

    def moveDown(self):
        self.list.moveDown()

    def updateList(self, job):
        if os.path.normpath(self.current_ref.getPath()) != job.getDestinationPath():
            return 
        self["waitingtext"].visible = True
        self.inited = False
        self.selectedmovie = self.getCurrent()
        self.go()

    def getCurrentPath(self):
        return self.current_ref.getPath()

    def go(self):
        if not self.inited:
            print("on first show", str(self.stopwatch.elapsed))
            self.delayTimer.start(10, True)
            self.inited = True

    def saveListsize(self):
        listsize = self["list"].instance.size()
        self.listWidth = listsize.width()
        self.listHeight = listsize.height()

    def updateHDDData(self):
        print("updateHDDData", str(self.stopwatch.elapsed))
        autoNetwork.updateAutoNetwork()
        if not autoNetwork.isMountOnline(config.movielist.last_videodir.value):
            config.movielist.last_videodir.value = "/media/"

        if not config.AdvancedMovieSelection.startdir.value and not self.showLastDir:
            if path.exists(config.movielist.last_videodir.value):
                config.movielist.last_videodir.value = defaultMoviePath()
        if not path.exists(config.movielist.last_videodir.value):
            config.movielist.last_videodir.value = "/media/"

        if not config.AdvancedMovieSelection.movielibrary_show.value or not config.AdvancedMovieSelection.startdir.value:
            self.current_ref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + config.movielist.last_videodir.value)
        else:            
            self.current_ref = eServiceReferenceListAll(config.movielist.last_videodir.value)
        self["list"].onFirstStart()
        self.updateFolderSortType()
        self.reloadList(self.selectedmovie)
        self.updateDescription()
        if movieScanner.isWorking:
            self.__dbUpdate.start(self.LIB_UPDATE_INTERVAL, False)
        self.stopwatch.stop()
        self["waitingtext"].visible = False
        print("movielist started in", str(self.stopwatch.elapsed))

    def moveTo(self):
        self["list"].moveTo(self.selectedmovie)

    def getCurrent(self):
        service = self["list"].getCurrent()
        return service

    def setMovieStatus(self, status):
        current = self.getCurrent()
        if current is not None:
            cut_list = self["list"].setMovieStatus(current, status)
            if isinstance(cut_list, str):
                self.session.open(MessageBox, _("Error") + "\n" + cut_list, MessageBox.TYPE_ERROR)
                return
            if cut_list:
                self.setNewCutList(cut_list)

    def movieSelected(self):
        current = self.getCurrent()
        if current is not None:
            if current.flags & eServiceReference.mustDescent:
                self.gotFilename(current.getPath())
            else:
                self.saveconfig()
                self.close(current)

    def doContext(self, retval=None):
        current = self.getCurrent()
        if not current:
            # create dummy service
            current = eServiceReferenceBackDir("..")
        if current is not None:
            if not config.usage.load_length_of_movies_in_moviellist.value:
                self.session.open(MovieContextMenu, self, current)
            else:
                self.session.openWithCallback(self.checkchanges, MovieContextMenu, self, current)

    def checkchanges(self, retval=None):
        if not config.usage.load_length_of_movies_in_moviellist.value:
            self.session.openWithCallback(self.abort, MessageBox, _("Load Length of Movies in Movielist has been disabled.\nClose and reopen Movielist is required to apply the setting."), MessageBox.TYPE_INFO)

    def abort(self, retval=None):
        if self.clearSearch():
            return
        self.saveconfig()
        self.close(None)

    def saveconfig(self):
        config.movielist.last_selected_tags.value = self.selected_tags
        config.movielist.moviesort.save()
        config.movielist.listtype.save()
        config.movielist.description.save()
        config.movielist.showdate.save()
        config.movielist.showtime.save()
        config.movielist.showservice.save()
        config.movielist.showtags.save()
        config.movielist.last_videodir.save()
        config.AdvancedMovieSelection.show_bookmarks.save()
        config.AdvancedMovieSelection.movielibrary_show.save()
        config.AdvancedMovieSelection.movielibrary_sort.save()
        service = self.getCurrent()
        if service is not None:
            config.AdvancedMovieSelection.last_selected_service.value = service.toString()
        else:
            config.AdvancedMovieSelection.last_selected_service.value = ""
        config.AdvancedMovieSelection.last_selected_service.save()        

    def showTrailer(self):
        if pluginPresent.YTTrailer == True:
            event = self["list"].getCurrentEvent()
            if event is not None:
                eventname = event.getEventName()
                self.session.open(YTTrailerList, eventname)
            else:
                pass
        else:
            pass

    def getTagDescription(self, tag):
        from .Source.AccessRestriction import accessRestriction
        if tag.startswith("VSR"):
            vsr = _("VSR") + "-%d" % (accessRestriction.decodeAccess(tag))
            return vsr, tag
        # TODO: access the tag database
        return tag, tag

    def updateTags(self):
        # get a list of tags available in this list
        self.tags = list(self["list"].tags)
        # insert text for selecting all movies
        self.tags.insert(0, _(SHOW_ALL_MOVIES))
        
        if not self.tags:
            # by default, we do not display any filtering options
            self.tag_first = ""
            self.tag_second = ""
        else:
            tmp = config.movielist.first_tags.value
            if tmp in self.tags:
                self.tag_first = tmp
            else:
                self.tag_first = "<" + _("Tag 1") + ">"
            tmp = config.movielist.second_tags.value
            if tmp in self.tags:
                self.tag_second = tmp
            else:
                self.tag_second = "<" + _("Tag 2") + ">"

        #self["key_green"].text = self.tag_first
        #self["key_yellow"].text = self.tag_second
        
        # the rest is presented in a list, available on the
        # fourth ("blue") button
        #if self.tags:
        #    self["key_blue"].text = _("Tags") + "..."
        #else:
        #    self["key_blue"].text = ""

    def setListType(self, type):
        self["list"].setListType(type)

    def setDescriptionState(self, val):
        self["list"].setDescriptionState(val)

    def writeSortType(self, sort_type):
        if isinstance(self.current_ref, eServiceReferenceListAll):
            config.AdvancedMovieSelection.movielibrary_sort.value = sort_type
        else:
            movieScanner.movielibrary.setSortType(config.movielist.last_videodir.value, sort_type)
            di = DirectoryInfo(config.movielist.last_videodir.value)
            di.sort_type = sort_type
            di.write()

    def updateFolderSortType(self):
        sort_type = config.AdvancedMovieSelection.movielibrary_sort.value
        if not isinstance(self.current_ref, eServiceReferenceListAll):
            di = DirectoryInfo(config.movielist.last_videodir.value)
            sort_type = di.sort_type
        if sort_type != -1:
            print("[AdvancedMovieSelection] Set new sort type:", str(sort_type))
            config.movielist.moviesort.value = sort_type
            self["list"].setSortType(sort_type)
            self.updateSortButtonText()

    def setSortType(self, type):
        config.movielist.moviesort.value = type
        self.writeSortType(type)
        self["list"].setSortType(type)
        self.updateSortButtonText()

    def showFolders(self, val):
        self["list"].showFolders(val)

    def showProgressbar(self, value):
        self["list"].showProgressbar(value)

    def showPercent(self, value):
        self["list"].showPercent(value)

    def showStatusIcon(self, value):
        self["list"].showStatusIcon(value)

    def showStatusColor(self, value):
        self["list"].showStatusColor(value)
        
    def showDate(self, value):
        self["list"].showDate(value)
        
    def showTime(self, value):
        self["list"].showTime(value)
        
    def showService(self, value):
        self["list"].showService(value)

    def showTags(self, value):
        self["list"].showTags(value)

    def updateTitle(self, current_path):
        if current_path and current_path[-1] != '/':
            current_path += '/' 
        #if config.usage.setup_level.index >= 2: # expert+
        title = getSortDescription()
        if self.list.getAccess() < 18:
            title += " [%s-%d]" % (_("VSR"), self.list.getAccess())
        title += " | "
        if not isinstance(self.current_ref, eServiceReferenceListAll):
            title += _("Movie location:") + " "
        else:
            title += _("Movie library") + ": "
        title += current_path
        
        extra_info = []
        if self.selected_tags:
            extra_info.append(self["list"].arrangeTags(" ".join(self.selected_tags)))
        if self.list.filter_description is not None:
            extra_info.append(self.list.filter_description)
        
        if len(extra_info) > 0:
            #title += " - " + ','.join(self.selected_tags)
            title += " (" + ", ".join(extra_info) + ")"
        if not movieScanner.isWorking:
            self.setTitle(title)
        else:
            self.setTitle(title + " " + _("[Library update in progress]"))

    @clockit
    def reloadList(self, sel=None, home=False):
        if not fileExists(config.movielist.last_videodir.value):
            path = defaultMoviePath()
            config.movielist.last_videodir.value = path
            self.current_ref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + path)
            self["freeDiskSpace"].path = path
        if sel is None:
            sel = self.getCurrent()
            movieScanner.updateServiceInfo(sel)
        self["list"].reload(self.current_ref, self.selected_tags)
        self.updateTitle(config.movielist.last_videodir.value)
        if not (sel and self["list"].moveTo(sel)):
            if home:
                self["list"].moveToIndex(0)
        self.updateTags()
        self["freeDiskSpace"].update()

    def doPathSelect(self):
        self.session.openWithCallback(
            self.gotFilename,
            MovieLocationBox,
            _("Please select the movie path..."),
            config.movielist.last_videodir.value
        )

    def gotFilename(self, res):
        if res is not None:# and res is not config.movielist.last_videodir.value:
            if fileExists(res):           
                selection = None
                current = self.getCurrent()
                if current is not None:
                    if current.flags & eServiceReference.mustDescent:                
                        if current.getName() == "..":
                            selection = eServiceReference("2:47:1:0:0:0:0:0:0:0:" + self["list"].root.getPath())
                if isinstance(current, eServiceReferenceListAll):
                    self.current_ref = current
                    config.AdvancedMovieSelection.movielibrary_show.value = True
                else:
                    config.AdvancedMovieSelection.movielibrary_show.value = False
                    if isinstance(self.current_ref, eServiceReferenceListAll):
                        selection = self.current_ref
                    self.current_ref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + res)
                config.movielist.last_videodir.value = res
                self["freeDiskSpace"].path = res
                self.updateFolderSortType()
                self.updateDBButtonText()
                self.reloadList(sel=selection, home=True)
            else:
                self.session.open(
                    MessageBox,
                    _("Directory %s nonexistent.") % (res),
                    type=MessageBox.TYPE_ERROR,
                    timeout=5
                    )

    def showAll(self):
        self.selected_tags_ele = None
        self.selected_tags = None
        self.reloadList(home=True)

    def showTagsN(self, tagele):
        if not self.tags:
            self.showTagWarning()
        elif not tagele or (self.selected_tags and tagele.value in self.selected_tags) or not tagele.value in self.tags:
            self.showTagsMenu(tagele)
        else:
            self.selected_tags_ele = tagele
            self.selected_tags = set([tagele.value])
            self.reloadList(home=True)

    def showTagsFirst(self):
        self.showTagsN(config.movielist.first_tags)

    def showTagsSecond(self):
        self.showTagsN(config.movielist.second_tags)

    def showTagsSelect(self):
        self.showTagsN(None)

    def tagChosen(self, tag):
        if tag and tag[0] == _(SHOW_ALL_MOVIES):
            self.showAll()
            return
        if tag is not None:
            self.selected_tags = set([tag[1]])
            if self.selected_tags_ele:
                self.selected_tags_ele.value = tag[1]
                self.selected_tags_ele.save()
            self.reloadList(home=True)

    def showTagsMenu(self, tagele):
        self.selected_tags_ele = tagele
        list = [(self.getTagDescription(tag)) for tag in self.tags]
        selection = 0
        current = self.selected_tags and "".join(self.selected_tags)
        for index, item in enumerate(list):
            if item[1] == current:
                selection = index
                break
        self.session.openWithCallback(self.tagChosen, ChoiceBox, title=_("Please select tag to filter..."), list=list, selection=selection)

    def showTagWarning(self):
        self.session.open(MessageBox, _("No tags are set on these movies."), MessageBox.TYPE_ERROR)
        
    def movietags(self):
        service = self.getCurrent()
        self.session.openWithCallback(self.reloadList, MovieTagEditor, service, parent=self.session.current_dialog)

    def selectScanLocations(self):
        self.session.openWithCallback(self.rescan, ScanLocationBox, _("Please select the search path(s) for movies..."), config.movielist.last_videodir.value)
        
    def rescan(self, retval):
        if retval:
            self.__dbUpdate.start(self.LIB_UPDATE_INTERVAL, False)
            movieScanner.reloadMoviesAsync()

    def libraryUpdateTimerEvent(self):
        print("libraryUpdateTimerEvent")
        if not movieScanner.isWorking:
            print("update movie list")
            self.reloadList()
            if not movieScanner.isWorking:
                self.__dbUpdate.stop()
        else:
            self.updateTitle("")
            self.list.updateMovieLibraryEntry()
            
        
class MoviebarPositionSetupText(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.skinName = SkinTools.appendResolution("AdvancedMovieSelectionMoviebarPositionSetup")
        self["howtotext"] = StaticText(_("Use direction keys to move the Moviebar.\nPress OK button for save or the EXIT button to cancel.\nUse the red button for reset to the original position."))

class MoviebarPositionSetup(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self["actions"] = NumberActionMap(["WizardActions", "InputActions", "ColorActions"],
        {
            "ok": self.go,
            "back": self.cancel,
            "up": self.up,
            "down": self.down,
            "left": self.left,
            "right": self.right,
            "red": self.red,
        }, -1)
        self.skinName = "MoviePlayer"
        self.onExecBegin.append(self.__onExecBegin)

    def __onExecBegin(self):
        self.orgpos = self.instance.position()
        offsetX = config.AdvancedMovieSelection.movieplayer_infobar_position_offset_x.value
        offsetY = config.AdvancedMovieSelection.movieplayer_infobar_position_offset_y.value
        self.instance.move(ePoint(self.orgpos.x() + offsetX, self.orgpos.y() + offsetY))
        self.screenMoviebarPositionSetupText = self.session.instantiateDialog(MoviebarPositionSetupText)
        self.screenMoviebarPositionSetupText.show()


    def red(self):
        self.instance.move(ePoint(self.orgpos.x(), self.orgpos.y()))
        print("[InfobarPositionSetup] New skin position: x = %d, y = %d" % (self.instance.position().x(), self.instance.position().y()))
        
    def go(self):
        config.AdvancedMovieSelection.movieplayer_infobar_position_offset_x.value = self.instance.position().x() - self.orgpos.x()
        config.AdvancedMovieSelection.movieplayer_infobar_position_offset_x.save()
        config.AdvancedMovieSelection.movieplayer_infobar_position_offset_y.value = self.instance.position().y() - self.orgpos.y()
        config.AdvancedMovieSelection.movieplayer_infobar_position_offset_y.save()
        self.screenMoviebarPositionSetupText.doClose()
        self.close()
    
    def cancel(self):
        self.screenMoviebarPositionSetupText.doClose()
        self.close()
    
    def moveRelative(self, x=0, y=0):
        self.instance.move(ePoint(self.instance.position().x() + x, self.instance.position().y() + y))
        print("[InfobarPositionSetup] New skin position: x = %d, y = %d" % (self.instance.position().x() + x, self.instance.position().y() + y))
    
    def up(self):
        self.moveRelative(y=-2)

    def down(self):
        self.moveRelative(y=2)
    
    def left(self):
        self.moveRelative(x=-2)
    
    def right(self):
        self.moveRelative(x=2)
