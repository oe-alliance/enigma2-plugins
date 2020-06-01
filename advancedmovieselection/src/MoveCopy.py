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
from __init__ import _
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.LocationBox import MovieLocationBox
from Components.config import config
from Source.ServiceUtils import serviceUtil, realSize, diskUsage
from Source.ServiceProvider import ServiceCenter
from enigma import eTimer
import os, time

def openDialog(job, session):
    error = job.getError()
    # abort all if we have no session
    if not session:
        return
    # update movie list to show new copied or moved movies 
    from MovieSelection import MovieSelection
    if isinstance(session.current_dialog, MovieSelection):
        session.current_dialog.updateList(job)
        if not error:
            return
    # show progress dialog
    if not isinstance(session.current_dialog, MoveCopyProgress):
        session.open(MoveCopyProgress)
    # always show error message box
    if error:
        text = _("Job failed") + "\r\n\r\n"
        text += _("Error") + ": " + str(error) + "\r\n"
        session.open(MessageBox, text, MessageBox.TYPE_ERROR)

class MoveCopyNotifier():
    def __init__(self):
        self.timer = eTimer()
        self.timer.callback.append(self.__timeout)
        pass
    
    def __timeout(self):
        print("MoveCopyNotifier", str(serviceUtil.getJobs()))
        for job in serviceUtil.getJobs():
            if job.isFinished():
                openDialog(job, self.session)
                self.timer.stop()
        
    def start(self, session):
        self.session = session
        self.timer.start(10000, False)

moveCopyNotifier = MoveCopyNotifier()

from Components.GUIComponent import GUIComponent
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT
from Components.MultiContent import MultiContentEntryText, MultiContentEntryProgress

class ProgressList(GUIComponent):
    def __init__(self):
        GUIComponent.__init__(self)
        self.list = []
        self.l = eListboxPythonMultiContent()
        self.l.setFont(0, gFont("Regular", 20))
        self.l.setFont(1, gFont("Regular", 16))
        self.l.setItemHeight(155)
        self.l.setBuildFunc(self.buildListEntry)
        
        self.onSelectionChanged = [ ]

    def connectSelChanged(self, fnc):
        if not fnc in self.onSelectionChanged:
            self.onSelectionChanged.append(fnc)

    def disconnectSelChanged(self, fnc):
        if fnc in self.onSelectionChanged:
            self.onSelectionChanged.remove(fnc)

    def selectionChanged(self):
        for x in self.onSelectionChanged:
            x()

    def buildListEntry(self, job):
        res = [ None ]
        try:
            width = self.l.getItemSize().width()
            
            full = job.getSizeTotal()
            copied = job.getSizeCopied()
            if full == 0:
                full = 1
            if copied == 0:
                copied = 1
            elapsed_time = job.getElapsedTime()
            progress = copied * 100 / full
            b_per_sec = elapsed_time != 0 and copied / elapsed_time or 0
            mode = job.getMode() and _("Move") or _("Copy")
            name_info = _("Name:")
            if job.isCancelled():
                mode = _("Cancelled")
            if job.isFinished():
                mode = _("Finished")
                movie_name = ""
                name_info = ""
            else:
                movie_name = job.getMovieName()
            error = job.getError() 
            if error:
                mode = _("Error")
                movie_name = str(error)
                name_info = _("Error:")
            #etime = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
            main_info = "%s  %d/%d (%s)  %d%%" % (mode, job.getMovieIndex(), job.getMovieCount(), realSize(full), progress)
            #file_info = "(%d/%d)" % (job.getFileIndex(), job.getFileCount())
            #speed_info = _("Total files") + file_info + " " + _("Average") + " " + realSize(b_per_sec, 3) + "/" + _("Seconds")
    
            src_p = job.getSourcePath()
            dst_p = job.getDestinationPath()
            from_info = os.path.basename(src_p) + " (%s)" % (src_p)
            to_info = os.path.basename(dst_p) + " (%s)" % (dst_p)
            remaining_bytes = full - copied
            remaining_seconds = b_per_sec != 0 and remaining_bytes / b_per_sec or -1
            remaining_elements = "%d (%s)" % (job.getFileCount() - job.getFileIndex(), realSize(remaining_bytes, 1))
            if job.isFinished():
                remaining_time = mode
            elif remaining_seconds == -1:
                remaining_time = _("Calculating...")
            elif remaining_seconds > 60 * 60:
                remaining_time = time.strftime("%H:%M:%S", time.gmtime(remaining_seconds)) 
            elif remaining_seconds > 120:
                remaining_time = _("Around %d minutes") % (remaining_seconds / 60)
            elif remaining_seconds > 60:
                remaining_time = _("Around %d minute") % (remaining_seconds / 60)
            else:
                remaining_time = "%d %s" % (remaining_seconds, _("Seconds"))
            speed = realSize(b_per_sec, 3) + "/" + _("Second")
            
            res.append(MultiContentEntryProgress(pos=(5, 2), size=(width - 10, 5), percent=progress, borderWidth=1))
            
            info_width = 180
            res.append(MultiContentEntryText(pos=(5, 9), size=(width, 26), font=0, flags=RT_HALIGN_LEFT, text=_("Status:")))
            res.append(MultiContentEntryText(pos=(5, 32), size=(info_width, 22), font=1, flags=RT_HALIGN_LEFT, text=name_info))
            res.append(MultiContentEntryText(pos=(5, 52), size=(info_width, 20), font=1, flags=RT_HALIGN_LEFT, text=_("From:")))
            res.append(MultiContentEntryText(pos=(5, 72), size=(info_width, 20), font=1, flags=RT_HALIGN_LEFT, text=_("To:")))
            if not job.isFinished():
                res.append(MultiContentEntryText(pos=(5, 92), size=(info_width, 20), font=1, flags=RT_HALIGN_LEFT, text=_("Remaining time:")))
            res.append(MultiContentEntryText(pos=(5, 112), size=(info_width, 20), font=1, flags=RT_HALIGN_LEFT, text=_("Remaining elements:")))
            res.append(MultiContentEntryText(pos=(5, 132), size=(info_width, 20), font=1, flags=RT_HALIGN_LEFT, text=_("Speed:")))
    
            res.append(MultiContentEntryText(pos=(info_width, 9), size=(width, 26), font=0, flags=RT_HALIGN_LEFT, text=main_info))
            res.append(MultiContentEntryText(pos=(info_width, 32), size=(width, 22), font=1, flags=RT_HALIGN_LEFT, text=movie_name))
            res.append(MultiContentEntryText(pos=(info_width, 52), size=(width, 20), font=1, flags=RT_HALIGN_LEFT, text=from_info))
            res.append(MultiContentEntryText(pos=(info_width, 72), size=(width, 20), font=1, flags=RT_HALIGN_LEFT, text=to_info))
            if not job.isFinished():
                res.append(MultiContentEntryText(pos=(info_width, 92), size=(width, 20), font=1, flags=RT_HALIGN_LEFT, text=remaining_time))
            res.append(MultiContentEntryText(pos=(info_width, 112), size=(width, 20), font=1, flags=RT_HALIGN_LEFT, text=remaining_elements))
            res.append(MultiContentEntryText(pos=(info_width, 132), size=(width, 20), font=1, flags=RT_HALIGN_LEFT, text=speed))
    
            res.append(MultiContentEntryText(pos=(width - 200, 9), size=(195, 26), font=0, flags=RT_HALIGN_RIGHT, text=realSize(copied)))
            #res.append(MultiContentEntryText(pos=(width - 150, 32), size=(145, 22), font=1, flags=RT_HALIGN_RIGHT, text=etime))
        except Exception as e:
            print(e)
        return res

    def moveToIndex(self, index):
        self.instance.moveSelectionTo(index)

    def getCurrentIndex(self):
        return self.instance.getCurrentIndex()

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

    def load(self, jobs):
        self.list = []
        for job in jobs:
            self.list.append((job,))
        self.l.setList(self.list)

    def updateJobs(self):
        for index, job in enumerate(self.list):
            self.l.invalidateEntry(index)

    def __len__(self):
        return len(self.list)

    def moveTo(self, serviceref):
        count = 0
        for x in self.list:
            if x[0] == serviceref:
                self.instance.moveSelectionTo(count)
                return True
            count += 1
        return False
    
    def moveDown(self):
        self.instance.moveSelection(self.instance.moveDown)

from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from enigma import eTimer
from Components.ActionMap import HelpableActionMap
from Components.Button import Button
from Source.Globals import SkinResolutionHelper

class MoveCopyProgress(Screen, HelpableScreen, SkinResolutionHelper):
    def __init__(self, session):
        Screen.__init__(self, session)
        HelpableScreen.__init__(self)
        SkinResolutionHelper.__init__(self)
        self.timer = eTimer()
        self.timer.callback.append(self.update)
        self["ColorActions"] = HelpableActionMap(self, "ColorActions",
            {
                "red": (self.abort, _("Abort selected job")),
                "green": (self.close, _("Close")),
            })
        self["key_red"] = Button(_("Cancel"))
        self["key_green"] = Button(_("Close"))
        self["list"] = ProgressList()
        self["list"].connectSelChanged(self.selectionChanged)
        self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
            {
                "cancel": (self.close, _("Close")),
                "ok": (self.ok, _("Show detail of selected job"))
            })
        self.onShown.append(self.setWindowTitle)
    
    def setWindowTitle(self):
        self["list"].load(serviceUtil.getJobs())
        self.selectionChanged()
        self.timer.start(1000, False)
        
    def ok(self):
        job = self["list"].getCurrent()
        if job:
            l = []
            l.append("%s %s" % (_("From:"), job.getSourcePath()))
            l.append("%s %s" % (_("To:"), job.getDestinationPath()))
            l.append("")
            for si in job.list:
                if si.getStatus() == si.STAT_WAITING and job.getError():
                    info = _("Aborted")
                elif si.getStatus() == si.STAT_WAITING:
                    info = _("Waiting")
                elif si.getStatus() == si.STAT_FINISHED:
                    info = _("Finished")
                elif si.getStatus() == si.STAT_STARTED and job.getError():
                    info = _("Error")
                else:
                    info = job.getMode() and _("Move") or _("Copy")
                l.append(info + ": \"%s\"" % (si.getName()))
            self.session.open(MessageBox, "\r\n".join(l), MessageBox.TYPE_INFO)
    
    def abort(self):
        job = self["list"].getCurrent()
        if not job or job and job.isFinished():
            return
        if job and job.isCancelled():
            text = _("Job already cancelled!") + "\r\n"
            if job.getMode():
                text += _("Please wait until current movie is moved to the end!")
            else:
                text += _("Please wait until current movie is copied to the end!")
            self.session.openWithCallback(self.abortCallback, MessageBox, text, MessageBox.TYPE_INFO)
            return
        text = _("Would you really abort current job?") + "\r\n"
        if job.getMode():
            text += _("Movies began to be moved until they are finished!")
        else:
            text += _("Movies began to be copied until they are finished!")
        self.session.openWithCallback(self.abortCallback, MessageBox, text, MessageBox.TYPE_YESNO)
    
    def abortCallback(self, result):
        if result == True:
            job = self["list"].getCurrent()
            if job:
                job.cancel()
    
    def update(self):
        self["list"].updateJobs()

    def selectionChanged(self):
        job = self["list"].getCurrent()
        if job:
            movie_count = job.getMovieCount()
            app_info = job.getMode() and _("Move of") or _("Copy of")
            app_info += " %d " % (movie_count)
            app_info += movie_count == 1 and _("movie") or _("movies")
            app_info += " (%s)" % (realSize(job.getSizeTotal()))
            self.setTitle(app_info)
        else:
            self.setTitle(_("Move/Copy progress"))

class MovieMove(ChoiceBox):
    def __init__(self, session, csel, service):
        self.csel = csel
        serviceHandler = ServiceCenter.getInstance()
        info = serviceHandler.info(service)
        self.sourcepath = service.getPath().rsplit('/', 1)[0]
        if len(self.csel.list.multiSelection) == 0:
            self.name = info.getName(service)
            self.service_list = [service]
        else:
            self.name = _("Selected movies")
            self.service_list = self.csel.list.multiSelection  
        
        for s in self.service_list:
            info = serviceHandler.info(s)
            name = info.getName(s)
            s.setName(name)

        cbkeys = []
        listpath = []
        listpath.append((_("To adjusted move/copy location"), "CALLFUNC", self.selectedLocation))
        cbkeys.append("blue")
        listpath.append((_("Directory Selection"), "CALLFUNC", self.selectDir))
        cbkeys.append("yellow")
        listpath.append((_("Show active move/copy processes"), "CALLFUNC", self.showActive))
        cbkeys.append("green")
        listpath.append((_("Close"), "CALLFUNC", self.close))
        cbkeys.append("red")

        ChoiceBox.__init__(self, session, list=listpath, keys=cbkeys)
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(_("Move/Copy from: %s") % self.name)

    def selectedLocation(self, arg):
        self.checkLocation(config.AdvancedMovieSelection.movecopydirs.value)

    def selectDir(self, arg):
        self.session.openWithCallback(self.checkLocation, MovieLocationBox, (_("Move/Copy %s") % self.name) + ' ' + _("to:"), config.movielist.last_videodir.value)

    def showActive(self, arg):
        self.session.open(MoveCopyProgress)

    def checkLocation(self, destinationpath):
        if self.csel.getCurrentPath() == destinationpath:
            self.session.open(MessageBox, _("Source and destination path must be different."), MessageBox.TYPE_INFO)
            return
        if destinationpath:
            self.gotFilename(destinationpath)

    def gotFilename(self, destinationpath):
        if destinationpath:
            self.destinationpath = destinationpath
            listtmp = [(_("Move"), "move"), (_("Copy"), "copy"), (_("Abort"), "abort") ]
            self.session.openWithCallback(self.doAction, ChoiceBox, title=((_("How to proceed '%s'") % self.name) + ' ' + (_("from %s") % self.sourcepath) + ' ' + (_("to %s") % self.destinationpath) + ' ' + _("be moved/copied?")), list=listtmp)
    
    def doAction(self, confirmed):
        if not confirmed or confirmed[1] == "abort":
            return
        action = confirmed[1]
        serviceUtil.setServices(self.service_list, self.destinationpath)
        total, used, free = diskUsage(self.destinationpath)
        job = serviceUtil.prepareJob()
        services = job.prepare()
        required = job.getSizeTotal()
        if required > free:
            serviceUtil.clear()
            text = []
            text = _("On destination data carrier is not enough space available.")
            if action == "move":
                text += " " + _("Another %s are required to move the data.") % (realSize(required - free))
            else:
                text += " " + _("Another %s are required to copy the data.") % (realSize(required - free))
            text += "\r\n\r\n" + _("Destination carrier")
            text += "\r\n" + _("Free space:") + " " + realSize(free)
            text += "\r\n" + _("Total size:") + " " + realSize(total)
            self.session.open(MessageBox, text, MessageBox.TYPE_ERROR)
            return
        if len(services) != 0:
            serviceUtil.clear()
            text = []
            for s in services:
                print(s.getName())
                text.append(s.getName())
            self.session.open(MessageBox, _("Movie(s) are already in the destination directory. Operation cancelled!") + "\r\n\r\n" + "\r\n".join(text), MessageBox.TYPE_INFO)
            return
        if action == "copy":
            serviceUtil.copy()
        elif action == "move":
            serviceUtil.move()
        if config.AdvancedMovieSelection.show_move_copy_progress.value:
            moveCopyNotifier.start(self.session)
            self.session.openWithCallback(self.__doClose, MoveCopyProgress)
        else:
            self.__doClose()

    def __doClose(self, dummy=None):
        self.csel.reloadList()
        self.close()
