#!/usr/bin/python
# -*- coding: utf-8 -*-
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  The plugin is developed on the basis from a lot of single plugins (thx for the code @ all)
#  Coded by JackDaniel (c)2011
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
from __init__ import _
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Label import Label
from Components.Button import Button
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from threading import Thread
from enigma import eServiceReference, ePicLoad
from timer import eTimer
from Components.MenuList import MenuList
from Source.ServiceProvider import ServiceCenter
from Source.EventInformationTable import createEIT
from Source.MovieDB import tmdb, downloadCover
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ScrollLabel import ScrollLabel
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_CURRENT_PLUGIN
from Source.Globals import SkinTools, printStackTrace
import os

is_hidden = False
this_session = None
fetchingMovies = None
current = 0
total = 0
movie_title = ""
tmdb_logodir = resolveFilename(SCOPE_PLUGINS) + "Extensions/AdvancedMovieSelection/images"


class DownloadMovies(Screen):
    def __init__(self, session, items, service=None):
        Screen.__init__(self, session)
        self.skinName = SkinTools.appendResolution("AdvancedMovieSelectionDownload")
        self.onShow.append(self.selectionChanged)
        self.service = service
        self["logo"] = Pixmap()
        self["info"] = Label()
        self["title"] = Label()
        self["poster"] = Pixmap()
        self["poster"].hide()
        self["description"] = ScrollLabel()
        self["key_red"] = Button(_("Cancel"))
        self["key_green"] = Button("")
        self["key_yellow"] = Button("")
        self["key_yellow"] = Label(_("Manual search"))
        if self.service is not None:
            self["key_green"] = Label(_("Save infos/cover"))
        else:
            self["key_green"] = Label(_("Background"))
            self["key_yellow"].hide()

        self["ActionsMap"] = ActionMap(["SetupActions", "ColorActions"],
         {
          "ok": self.titleSelected,
          "green": self.titleSelected,
          "red": self.__cancel,
          "yellow": self.editTitle,
          "cancel": self.__cancel,
          "left": self.scrollLabelPageUp,
          "right": self.scrollLabelPageDown
          }, -1)
        self.onShown.append(self.setWindowTitle)

        self.l = []
        self["list"] = MenuList(self.l)
        self["list"].onSelectionChanged.append(self.selectionChanged)

        self.picload = ePicLoad()
        self.picload.PictureData.get().append(self.paintPosterPixmap)
        self.refreshTimer = eTimer()
        self.refreshTimer.callback.append(self.refresh)

        self.tmdb3 = tmdb.init_tmdb3()

        if self.service is not None:
            global movie_title
            movie_title = ServiceCenter.getInstance().info(self.service).getName(self.service).encode("utf-8").split(" - ")[0].strip()
            self.refreshTimer.start(1, True)
            return

        global fetchingMovies, this_session, is_hidden
        if fetchingMovies is None:
            fetchingMovies = FetchingMovies(items)
        else:
            fetchingMovies.cancel = False
        self.progressTimer = eTimer()
        self.progressTimer.callback.append(self.updateProgress)
        self.progressTimer.start(250, False)
        this_session = session
        is_hidden = False

    def setWindowTitle(self):
        self.setTitle(_("Search for %s, please wait...") % (movie_title))
        self["logo"].instance.setPixmapFromFile("%s/tmdb_logo.png" % tmdb_logodir)

    def scrollLabelPageUp(self):
        self["description"].pageUp()

    def scrollLabelPageDown(self):
        self["description"].pageDown()

    def paintPosterPixmap(self, picInfo=None):
        ptr = self.picload.getData()
        if ptr != None:
            self["poster"].instance.setPixmap(ptr)
            self["poster"].show()

    def __cancel(self):
        global fetchingMovies
        if fetchingMovies is not None:
            fetchingMovies.cancel = True
        self.close()

    def __hide(self):
        global is_hidden
        is_hidden = True
        self.close()

    def updateProgress(self):
        self.setTitle(_("Automatic search and save, please wait..."))
        global current, movie_title, total, fetchingMovies
        self["info"].setText(_("Processing: %s") % current + ' ' + (_("/ %s") % total))
        if fetchingMovies is not None:
            self["title"].setText(_("Current Movie: %s") % movie_title)
        else:
            self.setTitle(_("Automatic search and save"))
            self["title"].setText(_("Automatic search and save finished."))
            self["key_green"].setText(_("OK"))
            self.progressTimer.stop()

    def refresh(self):
        global movie_title
        self.refreshMovieTitle(movie_title)

    def refreshMovieTitle(self, title):
        global movie_title
        movie_title = title
        self["title"].setText(_("Searchtitle: %s") % movie_title)
        self["info"].setText(_("Filename: %s") % os.path.basename(self.service.getPath()))
        self.setTitle(_("Search result(s) for %s") % (movie_title))
        try:
            results = self.tmdb3.searchMovie(movie_title)
        except:
            results = []
        if len(results) == 0:
            self.setTitle(_("Nothing found for: %s") % (movie_title))
            self["key_green"].setText(_("OK"))
            print("No info found for: " + movie_title)
            return False

        self.l = []
        for movie in results:
            try:
                self["key_green"].setText(_("Save infos/cover"))
                released = str(movie.releasedate.year)
                if released:
                    self.l.append((movie.title.encode("utf-8") + " - " + released, movie))
                else:
                    self.l.append((movie.title.encode("utf-8"), movie))
            except:
                pass

        self["list"].setList(self.l)

    def titleSelected(self):
        global movie_title
        current = self["list"].l.getCurrentSelection()
        if self.service is not None and current:
            createEIT(self.service.getPath(), movie_title, movie=current[1])
        self.__hide()

    def selectionChanged(self):
        self["poster"].hide()
        current = self["list"].l.getCurrentSelection()
        if current:
            try:
                movie = current[1]
                self["description"].setText("%s - %s\n\n%s" % (str(movie.title.encode('utf-8', 'ignore')), str(movie.releasedate), movie.overview.encode('utf-8', 'ignore')))
                jpg_file = "/tmp/preview.jpg"
                cover_url = movie.poster_url
                if cover_url is not None:
                    downloadCover(cover_url, jpg_file, True)
                else:
                    jpg_file = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/AdvancedMovieSelection/images/nocover_de.png")
                sc = AVSwitch().getFramebufferScale()
                self.picload.setPara((self["poster"].instance.size().width(), self["poster"].instance.size().height(), sc[0], sc[1], False, 1, "#ff000000"))
                self.picload.startDecode(jpg_file)
            except Exception as e:
                print(e)

    def pageUp(self):
        self["description"].pageUp()

    def pageDown(self):
        self["description"].pageDown()

    def editTitle(self):
        global movie_title
        self.session.openWithCallback(self.newTitle, VirtualKeyBoard, title=_("Enter new moviename to search for"), text=movie_title)
        #self.session.openWithCallback(self.newTitle, InputBox, title=_("Enter the new Movie title!"), text=movie_title+" "*80, maxSize=55, type=Input.TEXT)

    def newTitle(self, newTitle):
        if newTitle is not None:
            self.setTitle(_("Search for %s, please wait...") % (newTitle))
            global movie_title
            movie_title = newTitle.strip()
            self.refreshTimer.start(100, True)


class FetchingMovies(Thread):
    def __init__(self, items):
        Thread.__init__(self)
        self.items = items
        self.start()

    def run(self):
        try:
            self.cancel = False
            global current, total, movie_title
            total = len(self.items)
            current = 0
            for item_list in self.items:
                try:
                    if self.cancel:
                        #print "Movie download cancelled"
                        self.finish()
                        return
                    service = item_list[0]
                    if not isinstance(service, eServiceReference):
                        service = service.serviceref
                    if service.flags & eServiceReference.mustDescent:
                        total = total - 1
                        continue
                    current = current + 1
                    movie_title = ServiceCenter.getInstance().info(service).getName(service).encode("utf-8").split(" - ")[0].strip()
                    createEIT(service.getPath(), movie_title)
                except:
                    printStackTrace()
        except:
            printStackTrace()
        finally:
            self.finish()

    def finish(self):
        global fetchingMovies, this_session, is_hidden
        fetchingMovies = None
        current = total
        #print "Movie download finished"
        if is_hidden == True:
            this_session.open(MessageBox, (_("Download and save from movie infos and covers complete.")), MessageBox.TYPE_INFO) # Topfi: removed last parameter
            this_session = None
