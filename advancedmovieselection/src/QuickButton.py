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
from Components.config import config
from Components.ActionMap import HelpableActionMap
from Components.Button import Button
from .MovieList import MovieList, accessRestriction
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor
from .MoveCopy import MovieMove
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from .Rename import MovieRetitle
from .Wastebasket import Wastebasket
from enigma import eServiceReference
from .Source.Config import qButtons


def getPluginCaption(pname):
    if pname and pname != "Nothing":
        if pname == "Home":
            return _(config.AdvancedMovieSelection.hometext.value)
        if pname == "Bookmark 1":
            return _(config.AdvancedMovieSelection.bookmark1text.value)
        if pname == "Bookmark 2":
            return _(config.AdvancedMovieSelection.bookmark2text.value)
        if pname == "Bookmark 3":
            return _(config.AdvancedMovieSelection.bookmark3text.value)
        if pname == "Bookmark 4":
            return _(config.AdvancedMovieSelection.bookmark4text.value)
        if pname == "Bookmark 5":
            return _(config.AdvancedMovieSelection.bookmark5text.value)
        if pname == "Bookmark 6":
            return _(config.AdvancedMovieSelection.bookmark6text.value)
        if pname == "Bookmark 7":
            return _(config.AdvancedMovieSelection.bookmark7text.value)
        if pname == "Show up to VSR-X":
            return (_("Show up to VSR-%d") % accessRestriction.getAccess())
        if pname == "Toggle seen":
            return _("Mark as seen")
        if pname == "Show/Hide folders":
            if not config.AdvancedMovieSelection.showfoldersinmovielist.value:
                return _("Show folders")
            else:
                return _("Hide folders")
        if pname == "Show/Hide seen":
            if config.AdvancedMovieSelection.hide_seen_movies.value:
                return _("Show seen movies")
            else:
                return _("Hide seen movies")
        if pname == "Bookmark(s) on/off":
            if not config.AdvancedMovieSelection.show_bookmarks.value:
                return _("Show bookmarks")
            else:
                return _("Hide bookmarks")
        if pname == "Show/Hide library":
            if not config.AdvancedMovieSelection.show_movielibrary.value:
                return _("Show library")
            else:
                return _("Hide library")
        if pname == "LIB marker on/off":
            if not config.AdvancedMovieSelection.show_videodirslocation.value:
                return _("Show marker")
            else:
                return _("Hide marker")
        if pname == "Library/Movielist":
            if config.AdvancedMovieSelection.movielibrary_show.value:
                return _("To movielist")
            else:
                return _("To library")

        for p in plugins.getPlugins(where=[PluginDescriptor.WHERE_MOVIELIST]):
            if pname == str(p.name):
                if config.AdvancedMovieSelection.buttoncaption.value == config.AdvancedMovieSelection.buttoncaption.default:
                    return p.name
                else:
                    return p.description
        return _(pname)
    return _("Nothing")


toggleSeenButton = None


class QuickButton:
    def __init__(self):
        self["key_red"] = Button()
        self["key_green"] = Button()
        self["key_yellow"] = Button()
        self["key_blue"] = Button()
        self["ColorActions"] = HelpableActionMap(self, "ColorActionsLong",
        {
            "red": (self.redpressed, ""),
            "green": (self.greenpressed, ""),
            "yellow": (self.yellowpressed, ""),
            "blue": (self.bluepressed, ""),
            "red_long": (self.redpressedlong, ""),
            "green_long": (self.greenpressedlong, ""),
            "yellow_long": (self.yellowpressedlong, ""),
            "blue_long": (self.bluepressedlong, ""),
        })
        self.updateButtonText()
        self.updateHelpText()

    def updateHelpText(self):
        for (actionmap, context, actions) in self.helpList:
            if context == "ColorActionsLong":
                for index, item in enumerate(actions):
                    func = qButtons.getFunction(item[0])
                    text = getPluginCaption(func)
                    actions[index] = (item[0], text)

    def updateButtonText(self):
        global toggleSeenButton
        toggleSeenButton = None
        fn = ('red', 'green', 'yellow', 'blue')
        for key in fn:
            key_text = 'key_%s' % (key)
            function = qButtons.getFunction(key)
            text = getPluginCaption(function)
            self[key_text].setText(text)
            if function == "Toggle seen":
                toggleSeenButton = self[key_text]

    def getNextFromList(self, items, current):
        for index, item in enumerate(items):
            if str(item) == str(current):
                index += 1
                return index >= len(items) and items[0] or items[index]
        return items[0]

    def getNextSortType(self):
        sort = config.AdvancedMovieSelection.sort_functions.value.split()
        # TODO: remove printout after beta tests
        if len(sort) < 1:
            print("default sort list")
            sort = [MovieList.SORT_ALPHANUMERIC, MovieList.SORT_DESCRIPTION, MovieList.SORT_DATE_DESC, MovieList.SORT_DATE_ASC]
        print("sorting:", sort)
        print("current:", str(config.movielist.moviesort.value))
        newType = int(self.getNextFromList(sort, config.movielist.moviesort.value))
        print("next:", str(newType))
        return newType

    def findButton(self, function):
        fn = ('red', 'green', 'yellow', 'blue')
        for key in fn:
            func = qButtons.getFunction(key)
            if func == function:
                key_text = 'key_%s' % (key)
                return self[key_text]

    def getSortButtonCaption(self, mode):
        if mode == MovieList.SORT_ALPHANUMERIC:
            return _("Sort alphabetically")
        if mode == MovieList.SORT_DESCRIPTION:
            return _("Sort by Description")
        if mode == MovieList.SORT_DATE_DESC:
            return _("Sort by Date (9->1)")
        if mode == MovieList.SORT_DATE_ASC:
            return _("Sort by Date (1->9)")
        return _("Unknown")

    def updateSortButtonText(self):
        key_number = self.findButton("Sort")
        if key_number:
            mode = self.getNextSortType()
            key_number.setText(self.getSortButtonCaption(mode))

    def updateDBButtonText(self):
        key_number = self.findButton("Library/Movielist")
        if key_number:
            key_number.setText(getPluginCaption("Library/Movielist"))

    def redpressed(self):
        self.startPlugin(qButtons.getFunction("red"), self["key_red"])

    def greenpressed(self):
        self.startPlugin(qButtons.getFunction("green"), self["key_green"])

    def yellowpressed(self):
        self.startPlugin(qButtons.getFunction("yellow"), self["key_yellow"])

    def bluepressed(self):
        self.startPlugin(qButtons.getFunction("blue"), self["key_blue"])

    def redpressedlong(self):
        print("red long")
        self.startPlugin(qButtons.getFunction("red_long"), None)

    def greenpressedlong(self):
        print("green long")
        self.startPlugin(qButtons.getFunction("green_long"), None)

    def yellowpressedlong(self):
        print("yellow long")
        self.startPlugin(qButtons.getFunction("yellow_long"), None)

    def bluepressedlong(self):
        print("blue long")
        self.startPlugin(qButtons.getFunction("blue_long"), None)

    def updateGUI(self):
        if toggleSeenButton:
            perc = self.list.getMovieStatus()
            if perc > 50:
                toggleSeenButton.setText(_("Mark as unseen"))
            else:
                toggleSeenButton.setText(_("Mark as seen"))

    def setButtonText(self, key_number, caption):
        if key_number:
            key_number.setText(caption)

    def startPlugin(self, pname, key_number):
        print("qButtonFX:", str(pname))
        # notify action map
        self["ColorActions"].execEnd()
        self["ColorActions"].execBegin()
        errorText = None
        if pname and pname != "Nothing":
            # all functions with no service is needed
            if pname == "Wastebasket":
                if config.AdvancedMovieSelection.use_wastebasket.value:
                    self.session.openWithCallback(self.reloadList, Wastebasket)
            elif pname == "Home":
                self.gotFilename(config.AdvancedMovieSelection.homepath.value)
            elif pname == "Bookmark 1":
                self.gotFilename(config.AdvancedMovieSelection.bookmark1path.value)
            elif pname == "Bookmark 2":
                self.gotFilename(config.AdvancedMovieSelection.bookmark2path.value)
            elif pname == "Bookmark 3":
                self.gotFilename(config.AdvancedMovieSelection.bookmark3path.value)
            elif pname == "Bookmark 4":
                self.gotFilename(config.AdvancedMovieSelection.bookmark4path.value)
            elif pname == "Bookmark 5":
                self.gotFilename(config.AdvancedMovieSelection.bookmark5path.value)
            elif pname == "Bookmark 6":
                self.gotFilename(config.AdvancedMovieSelection.bookmark6path.value)
            elif pname == "Bookmark 7":
                self.gotFilename(config.AdvancedMovieSelection.bookmark7path.value)
            elif pname == "Bookmark(s) on/off":
                config.AdvancedMovieSelection.show_bookmarks.value = not config.AdvancedMovieSelection.show_bookmarks.value
                self.saveconfig()
                self.reloadList()
                newCaption = getPluginCaption(pname)
                self.setButtonText(key_number, newCaption)
            elif pname == "Library/Movielist":
                config.AdvancedMovieSelection.movielibrary_show.value = not config.AdvancedMovieSelection.movielibrary_show.value
                self.saveconfig()
                self.reloadList()
                newCaption = getPluginCaption(pname)
                self.setButtonText(key_number, newCaption)
            elif pname == "Show/Hide library":
                config.AdvancedMovieSelection.show_movielibrary.value = not config.AdvancedMovieSelection.show_movielibrary.value
                self.saveconfig()
                self.reloadList()
                newCaption = getPluginCaption(pname)
                self.setButtonText(key_number, newCaption)
            elif pname == "LIB marker on/off":
                config.AdvancedMovieSelection.show_videodirslocation.value = not config.AdvancedMovieSelection.show_videodirslocation.value
                self.saveconfig()
                self.reloadList()
                newCaption = getPluginCaption(pname)
                self.setButtonText(key_number, newCaption)
            elif pname == "Show/Hide folders":
                config.AdvancedMovieSelection.showfoldersinmovielist.value = not config.AdvancedMovieSelection.showfoldersinmovielist.value
                newCaption = getPluginCaption(pname)
                self.showFolders(config.AdvancedMovieSelection.showfoldersinmovielist.value)
                config.AdvancedMovieSelection.showfoldersinmovielist.save()
                self.reloadList()
                self.setButtonText(key_number, newCaption)
            elif pname == "Show/Hide seen":
                config.AdvancedMovieSelection.hide_seen_movies.value = not config.AdvancedMovieSelection.hide_seen_movies.value
                newCaption = getPluginCaption(pname)
                config.AdvancedMovieSelection.hide_seen_movies.save()
                self.reloadList()
                self.setButtonText(key_number, newCaption)
            elif pname == "Sort":
                newType = self.getNextSortType()
                self.setSortType(newType)
                self.reloadList()
            elif pname == "Filter by description":
                self.openFilterByDescriptionChoice()
            elif pname == "Show Timer":
                from Screens.TimerEdit import TimerEditList
                self.session.open(TimerEditList)
            elif pname == "Update library":
                self.rescan(True)
            else:
                # all functions that require a service
                service = self.getCurrent()
                if not service:
                    return
                if pname == "Delete":
                    self.delete()
                elif pname == "Filter by Tags":
                    self.showTagsSelect()
                elif pname == "Tag Editor":
                    if not service.flags & eServiceReference.mustDescent:
                        self.movietags()
                    else:
                        if config.AdvancedMovieSelection.showinfo.value:
                            self.session.open(MessageBox, _("Set tag here not possible, please select a movie for!"), MessageBox.TYPE_INFO)
                elif pname == "Trailer search":
                    if not service.flags & eServiceReference.mustDescent:
                        self.showTrailer()
                    else:
                        if config.AdvancedMovieSelection.showinfo.value:
                            self.session.open(MessageBox, _("Trailer search here not possible, please select a movie!"), MessageBox.TYPE_INFO)
                elif pname == "Move-Copy":
                    if not service.flags & eServiceReference.mustDescent:
                        self.session.open(MovieMove, self, service)
                    else:
                        if config.AdvancedMovieSelection.showinfo.value:
                            self.session.open(MessageBox, _("Move/Copy from complete directory/symlink not possible, please select a single movie!"), MessageBox.TYPE_INFO)
                elif pname == "Rename":
                    if service.type != eServiceReference.idUser:
                        self.session.openWithCallback(self.reloadList, MovieRetitle, service)
                    else:
                        if config.AdvancedMovieSelection.showinfo.value:
                            self.session.open(MessageBox, _("Rename here not possible, please select a movie!"), MessageBox.TYPE_INFO)
                elif pname == "TheTVDB Info & D/L":
                    # TODO: search?
                    if True or not service.flags & eServiceReference.mustDescent:
                        from .SearchTVDb import TheTVDBMain
                        self.session.open(TheTVDBMain, service)
                elif pname == "TMDb Info & D/L":
                    # TODO: search?
                    if True or not service.flags & eServiceReference.mustDescent:
                        from .SearchTMDb import TMDbMain as TMDbMainsave
                        from .Source.ServiceProvider import ServiceCenter
                        searchTitle = ServiceCenter.getInstance().info(service).getName(service)
                        if len(self.list.multiSelection) == 0:
                            self.session.openWithCallback(self.updateCurrentSelection, TMDbMainsave, searchTitle, service)
                        else:
                            from .DownloadMovies import DownloadMovies
                            items = []
                            for item in self.list.multiSelection:
                                items.append([item, 0])
                            self.session.openWithCallback(self.updateCurrentSelection, DownloadMovies, items)
                    else:
                        if config.AdvancedMovieSelection.showinfo.value:
                            self.session.open(MessageBox, _("TMDb search here not possible, please select a movie!"), MessageBox.TYPE_INFO)
                elif pname == "Toggle seen":
                    if not service.flags & eServiceReference.mustDescent:
                        perc = self.list.getMovieStatus()
                        if perc > 50:
                            self.setMovieStatus(0)
                            self.setButtonText(key_number, _("Mark as seen"))
                        else:
                            self.setMovieStatus(1)
                            self.setButtonText(key_number, _("Mark as unseen"))
                elif pname == "Show up to VSR-X":
                    from .Source.AccessRestriction import VSR
                    access = "VSR-%d" % (self.list.getAccess())
                    for index, item in enumerate(VSR):
                        if item == access:
                            if len(VSR) - 1 == index:
                                access = VSR[0]
                            else:
                                access = VSR[index + 1]
                            break
                    self.list.setAccess(int(access[4:]))
                    self.reloadList()
                    self.setButtonText(key_number, _("Show up to") + ' ' + _("VSR") + '-%d' % (self.list.getAccess()))
                elif pname == "Mark as seen":
                    if not service.flags & eServiceReference.mustDescent:
                        self.setMovieStatus(status=1)
                    else:
                        if config.AdvancedMovieSelection.showinfo.value:
                            self.session.open(MessageBox, _("This may not be marked as seen!"), MessageBox.TYPE_INFO)
                elif pname == "Mark as unseen":
                    if not service.flags & eServiceReference.mustDescent:
                        self.setMovieStatus(status=0)
                    else:
                        if config.AdvancedMovieSelection.showinfo.value:
                            self.session.open(MessageBox, _("This may not be marked as unseen!"), MessageBox.TYPE_INFO)
                else:
                    plugin = None
                    for p in plugins.getPlugins(where=[PluginDescriptor.WHERE_MOVIELIST]):
                        if pname == str(p.name):
                            plugin = p
                    if plugin is not None:
                        try:
                            plugin(self.session, service)
                        except:
                            errorText = _("Unknown error!")
                    else:
                        errorText = _("Plugin not found!")
        else:
            errorText = _("No plugin assigned!")
        if errorText:
            self.session.open(MessageBox, errorText, MessageBox.TYPE_INFO)

    def openAccessChoice(self):
        vsr = []
        vsr.append((_("Clear"), None))
        vsr.append((_("VSR-0 (General Audience)"), "VSR-0"))
        vsr.append((_("VSR-6 (Parental Guidance Suggested)"), "VSR-6"))
        vsr.append((_("VSR-12 (Parents Strongly Cautioned)"), "VSR-12"))
        vsr.append((_("VSR-16 (Restricted)"), "VSR-16"))
        vsr.append((_("VSR-18 (No One 17 And Under Admitted)"), "VSR-18"))
        self.session.openWithCallback(self.setAccessChoice, ChoiceBox, title=_("Please select the VSR here:"), list=vsr)

    def setAccessChoice(self, answer):
        if answer:
            answer = answer[1]
            self.list.setAccessRestriction(answer)
            self.reloadList()

    def openFilterByDescriptionChoice(self):
        from .Source.ServiceProvider import ServiceCenter, detectDVDStructure, detectBludiscStructure, eServiceReferenceDvd, eServiceReferenceBludisc, eServiceReferenceListAll
        from .Source.MovieScanner import movieScanner
        from enigma import iServiceInformation
        from .MovieSelection import SHOW_ALL_MOVIES
        serviceHandler = ServiceCenter.getInstance()
        descr = []
        if isinstance(self.list.root, eServiceReferenceListAll):
            l = movieScanner.movielibrary.getMovieList(self.list.sort_type)
            for movie_tuple in l:
                movie_info = movie_tuple[0]
                info = movie_info.info
                if not info:
                    continue
                serviceref = movie_info.serviceref
                description = (info.getInfoString(serviceref, iServiceInformation.sDescription),)
                if description[0] != "" and not description in descr:
                    descr.append(description)
        else:
            l = serviceHandler.list(self.list.root)
            if not l:
                print("list movies for filter failed")
                return
            while True:
                serviceref = l.getNext()
                if not serviceref.valid():
                    break
                if serviceref.flags & eServiceReference.mustDescent:
                    dvd = detectDVDStructure(serviceref.getPath())
                    if dvd is not None:
                        serviceref = eServiceReferenceDvd(serviceref, True)
                    bludisc = detectBludiscStructure(serviceref.getPath())
                    if bludisc is not None:
                        serviceref = eServiceReferenceBludisc(serviceref, True)
                    if not dvd and not bludisc:
                        continue
                info = serviceHandler.info(serviceref)
                if not info:
                    continue
                description = (info.getInfoString(serviceref, iServiceInformation.sDescription),)
                if description[0] != "" and not description in descr:
                    descr.append(description)

        descr = sorted(descr)
        descr.insert(0, (_(SHOW_ALL_MOVIES),))

        current = self.list.filter_description
        selection = 0
        for index, item in enumerate(descr):
            if item[0] == current:
                selection = index
                break
        print("open filter choice", str(selection), str(descr))
        self.session.openWithCallback(self.filterByDescription, ChoiceBox, title=_("Select movie by description:"), list=descr, selection=selection)

    def filterByDescription(self, answer):
        from .MovieSelection import SHOW_ALL_MOVIES
        if not answer:
            return
        if answer[0] == _(SHOW_ALL_MOVIES):
            self.list.filter_description = None
            print("clear filter choice")
        else:
            self.list.filter_description = answer[0]
            print("set filter choice", str(answer[0]))
        self.reloadList()
