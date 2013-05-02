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
from __init__ import _
from Tools.Directories import fileExists
from Screens.Screen import Screen
from Screens.InputBox import InputBox
from Screens.ChoiceBox import ChoiceBox
from MessageBoxEx import MessageBox as MessageBoxEx
from Components.config import config
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.SelectionList import SelectionList
from enigma import eServiceReference, iServiceInformation
from os import path as os_path
from Screens.Console import eConsoleAppContainer
from Screens.TimerEntry import TimerEntry
from Source.ServiceProvider import ServiceCenter
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN, SCOPE_CONFIG
from Source.Globals import SkinTools

class TagEditor(Screen):
    def __init__(self, session, tags, txt=None, parent=None):
        Screen.__init__(self, session, parent=parent)
        self.skinName = SkinTools.appendResolution("AdvancedMovieSelectionTagEditor")
        self["key_red"] = StaticText(_("Cancel"))
        self["key_green"] = StaticText(_("Save/Close"))
        self["key_yellow"] = StaticText(_("Create new Tag"))
        self["key_blue"] = StaticText("")
        self["key_blue"] = StaticText(_("Load Tag(s) from movies"))
        self["info"] = StaticText(_("Use the OK Button for the selection."))
        self["list"] = SelectionList()
        self.TimerEntry = TimerEntry
        allTags = self.loadTagsFile()
        self.joinTags(allTags, tags)
        self.updateMenuList(allTags, tags)
        self.ghostlist = tags[:]
        self.ghosttags = allTags[:]
        self.origtags = allTags[:]
        self.tags = allTags
        self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "MenuActions"],
        {
            "ok": self["list"].toggleSelection,
            "cancel": self.cancel,
            "red": self.cancel,
            "green": self.accept,
            "yellow": self.addCustom,
            "blue": self.loadFromHdd,
            "menu": self.showMenu
        }, -1)
        self.defaulttaglist(tags)
        self.setCustomTitle(tags)

    def setCustomTitle(self, tags):
        if  tags == []:
            self.setTitle(_("Add Tag(s) for Recordings/Timer or AutoTimer"))
        else:
            try:
                Title = ServiceCenter.getInstance().info(self.service).getName(self.service)
                self.setTitle(_("Edit Tag(s) for: %s") % (Title))
            except:
                self.setTitle(_("Edit Tag(s)"))

    def defaulttaglist(self, tags):
        if not fileExists(resolveFilename(SCOPE_CONFIG, "movietags")):
            sourceDir = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/AdvancedMovieSelection/movietags")
            targetDir = resolveFilename(SCOPE_CONFIG)
            eConsoleAppContainer().execute("cp \"" + sourceDir + "\" \"" + targetDir + "\"")
            self.loadTagsFile()
            self.updateMenuList(tags)

    def addCustom(self):
        self.session.openWithCallback(self.addCustomCallback, InputBox, title=_("Please enter here the new tag:"))

    def addCustomCallback(self, ret):
        if ret:
            ret = ret and ret.strip().replace(" ", "_").capitalize()
            tags = self.tags
            if ret and ret not in tags:
                tags.append(ret)
                self.updateMenuList(tags, [ret])
        else:
            self.session.open(MessageBoxEx, _("Aborted by user!!"), MessageBoxEx.TYPE_ERROR)

    def loadTagsFile(self):
        try:
            file = open(resolveFilename(SCOPE_CONFIG, "movietags"))
            tags = [x.rstrip() for x in file]
            #tags = [x.rstrip() for x in file.readlines()]
            while "" in tags:
                tags.remove("")
            file.close()
        except IOError: #, ioe:
            tags = []
        return tags

    def saveTagsFile(self, tags):
        try:
            file = open(resolveFilename(SCOPE_CONFIG, "movietags"), "w")
            file.write("\n".join(tags) + "\n")
            file.close()
        except IOError: #, ioe:
            pass

    def joinTags(self, taglist, newtags):
        for tag in newtags:
            if not tag in taglist:
                taglist.append(tag)

    def setTimerTags(self, timer, tags):
        if timer.tags != tags:
            timer.tags = tags
            self.timerdirty = True

    def setMovieTags(self, ref, tags):
        file = ref.getPath()
        if file.endswith(".ts"):
            file = file + ".meta"
        else:
            file = file + ".ts.meta"
        if os_path.exists(file):
            metafile = open(file + ".ts.meta", "r")
            sid = metafile.readline().strip("\r\n")
            title = metafile.readline().strip("\r\n")
            descr = metafile.readline().strip("\r\n")
            time = metafile.readline().strip("\r\n")
            oldtags = metafile.readline().rstrip("\r\n")
            rest = metafile.read()
            metafile.close()
            tags = " ".join(tags)
            if tags != oldtags:
                metafile = open(file + ".ts.meta", "w")
                metafile.write("%s\n%s\n%s\n%s\n%s\n%s" % (sid, title, descr, time, tags, rest))
                metafile.close()

    def foreachTimerTags(self, func):
        self.timerdirty = False
        for timer in self.session.nav.RecordTimer.timer_list + self.session.nav.RecordTimer.processed_timers:
            if timer.tags:
                func(timer, timer.tags[:])
        if self.timerdirty:
            self.session.nav.RecordTimer.saveTimer()

    def foreachMovieTags(self, func):
        serviceHandler = ServiceCenter.getInstance()
        for dir in config.movielist.videodirs.value:
            if os_path.isdir(dir):
                root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + dir)
                list = serviceHandler.list(root)
                if list is None:
                    continue
                while 1:
                    serviceref = list.getNext()
                    if not serviceref.valid():
                        break
                    if (serviceref.flags & eServiceReference.mustDescent):
                        continue
                    info = serviceHandler.info(serviceref)
                    if info is None:
                        continue
                    tags = info.getInfoString(serviceref, iServiceInformation.sTags).split(' ')
                    if not tags or tags == ['']:
                        continue
                    func(serviceref, tags)

    def getTagDescription(self, tag):
        from Source.AccessRestriction import VSR
        if tag in VSR:
            return _(tag)
        return tag

    def updateMenuList(self, tags, extrasel=[]):
        seltags = [x[1] for x in self["list"].getSelectionsList()] + extrasel
        tags.sort()
        self["list"].setList([])
        for tag in tags:
            self["list"].addSelection(self.getTagDescription(tag), tag, 0, tag in seltags)

    def loadFromHdd(self):
        tags = self.tags[:]
        self.foreachTimerTags(lambda t, tg: self.joinTags(tags, tg))
        self.foreachMovieTags(lambda r, tg: self.joinTags(tags, tg))
        self.updateMenuList(tags)
        self.tags = tags

    def removeUnused(self):
        self.session.openWithCallback(
            self.removeUnusedCallback, MessageBoxEx, _("Do you really want to delete unused tags from default taglist?\n(Note that 'Cancel' will not undo this!)"))

    def removeUnusedCallback(self, result):
        if result is None:
            self.session.open(MessageBoxEx, _("Aborted by user!!"), MessageBoxEx.TYPE_ERROR)
        if result:
            tags = [x[1] for x in self["list"].getSelectionsList()]
            self.foreachTimerTags(lambda t, tg: self.joinTags(tags, tg))
            self.foreachMovieTags(lambda r, tg: self.joinTags(tags, tg))
            self.updateMenuList(tags)
            self.tags = tags
        else:
            pass

    def listReplace(self, lst, fr, to=None):
        if fr in lst:
            lst.remove(fr)
            if to != None and not to in lst:
                lst.append(to)
                lst.sort()
        return lst

    def renameTag(self):
        self.thistag = self["list"].list[self["list"].getSelectedIndex()][0]
        self.session.openWithCallback(
            self.renameTagCallback, InputBox, title=_("Rename tag \"%s\" in movies and default taglist?\n(Note that 'Cancel' will not undo this!)") % (self.thistag[1]), text=self.thistag[1])

    def renameTagCallback(self, res):
        res = res and res.strip().replace(" ", "_").capitalize()
        if res and len(res) and res != self.thistag[1]:
            thistag = self.thistag[1]
            self.foreachTimerTags(lambda t, tg: (thistag in tg) and self.setTimerTags(t, self.listReplace(tg, thistag, res)))
            self.foreachMovieTags(lambda r, tg: (thistag in tg) and self.setMovieTags(r, self.listReplace(tg, thistag, res)))
            self.listReplace(self.tags, thistag, res)
            self.listReplace(self.ghosttags, thistag, res)
            self.listReplace(self.ghostlist, thistag, res)
            self.updateMenuList(self.tags, self.thistag[3] and [res] or [])

    def removeTag(self):
        self.thistag = self["list"].list[self["list"].getSelectedIndex()][0]
        self.session.openWithCallback(
            self.removeTagCallback, MessageBoxEx, _("Do you really want to delete tag \"%s\" from movies and default taglist?\n(Caution can not be undone!)") % (self.thistag[1]))

    def removeTagCallback(self, result):
        if result is None:
            self.session.open(MessageBoxEx, _("Aborted by user!!"), MessageBoxEx.TYPE_ERROR)
        if result:
            thistag = self.thistag[1]
            self.foreachTimerTags(lambda t, tg: (thistag in tg) and self.setTimerTags(t, self.listReplace(tg, thistag)))
            self.foreachMovieTags(lambda r, tg: (thistag in tg) and self.setMovieTags(r, self.listReplace(tg, thistag)))
            self.listReplace(self.tags, thistag)
            self.listReplace(self.ghosttags, thistag)
            self.listReplace(self.ghostlist, thistag)
            self.updateMenuList(self.tags)
        else:
            pass

    def removeAll(self):
        self.session.openWithCallback(
            self.removeAllCallback, MessageBoxEx, _("Do you really want to delete all tags from movies and default taglist?\n(Caution can not be undone!)"))

    def removeAllCallback(self, result):
        if result is None:
            self.session.open(MessageBoxEx, _("Aborted by user!!"), MessageBoxEx.TYPE_ERROR)
        if result:
            self.foreachTimerTags(lambda t, tg: tg and self.setTimerTags(t, []))
            self.foreachMovieTags(lambda r, tg: tg and self.setMovieTags(r, []))
            self.tags = []
            self.ghosttags = []
            self.ghostlist = []
            self.updateMenuList(self.tags)
        else:
            pass

    def showMenu(self):
        menu = [
            (_("Add new tag"), self.addCustom),
            (_("Rename this tag"), self.renameTag),
            (_("Delete this tag"), self.removeTag),
            (_("Delete unused tags from default taglist"), self.removeUnused),
            (_("Delete all tags"), self.removeAll)
        ]
        self.session.openWithCallback(self.menuCallback, ChoiceBox, title="", list=menu)

    def menuCallback(self, choice):
        if choice:
            choice[1]()

    def cancel(self):
        if not self.origtags == self.ghosttags:
            self.saveTagsFile(self.ghosttags)
            self.close(self.ghostlist)
        else:
            self.close(None)

    def accept(self):
        list = [x[1] for x in self["list"].getSelectionsList()]
        if not self.origtags == self.tags:
            self.saveTagsFile(self.tags)
        self.close(list)

class MovieTagEditor(TagEditor):
    def __init__(self, session, service, parent):
        self.service = service
        serviceHandler = ServiceCenter.getInstance()
        info = serviceHandler.info(service)
        path = service.getPath()
        if path.endswith(".ts"):
            path = path[:-3]
        self.path = path
        tags = info.getInfoString(service, iServiceInformation.sTags)
        if tags:
            tags = tags.split(' ')
        else:
            tags = []
        TagEditor.__init__(self, session, tags, parent=parent)

    def saveTags(self, file, tags):
        try:
            meta_file = file + ".ts.meta"
            print "saveTags", meta_file
            if os_path.exists(meta_file):
                metafile = open(meta_file, "r")
                sid = metafile.readline().strip("\r\n")
                title = metafile.readline().strip("\r\n")
                descr = metafile.readline().strip("\r\n")
                time = metafile.readline().strip("\r\n")
                oldtags = metafile.readline().rstrip("\r\n")
                rest = metafile.read()
                metafile.close()
                tags = " ".join(tags)
                if tags != oldtags:
                    metafile = open(meta_file, "w")
                    metafile.write("%s\n%s\n%s\n%s\n%s\n%s" % (sid, title, descr, time, tags, rest))
                    metafile.close()
        except:
            from Source.Globals import printStackTrace
            printStackTrace()

    def cancel(self):
        if not self.origtags == self.ghosttags:
            self.saveTagsFile(self.ghosttags)
            self.exitDialog()
        else:
            self.close()

    def accept(self):
        list = [x[1] for x in self["list"].getSelectionsList()]
        if not self.origtags == self.tags:
            self.saveTagsFile(self.tags)
        self.saveTags(self.path, list)
        self.exitDialog()

    def exitDialog(self):
        self.close()
        # This will try to get back to an updated movie list.
        # A proper way to do this should be provided in enigma2.
        try:
            parentscreen = self.parent
            # TODO: this only works if parent is MovieContextMenu. 
            # FIXME: if TagEditor is opened with quick button, parent is MovieSelection and update will be failed 
            parentscreen.csel.reloadList()
            parentscreen.close()
        except AttributeError:
            pass
