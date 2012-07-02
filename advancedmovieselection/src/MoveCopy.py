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
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.LocationBox import MovieLocationBox
from enigma import eServiceCenter
from Components.config import config
from Components.UsageConfig import defaultMoviePath
from Tools.Directories import createDir
import os
#Topfi start
from threading import Timer
from Tools import Notifications
#Topfi end

class MovieMove(ChoiceBox):
    def __init__(self, session, csel, service):
        self.csel = csel
        serviceHandler = eServiceCenter.getInstance()
        info = serviceHandler.info(service)
        self.sourcepath = service.getPath().rsplit('/', 1)[0]
        if len(self.csel.list.multiSelection) == 0:
            self.name = info.getName(service)
            self.service_list = [service]
        else:
            self.service_list = self.csel.list.multiSelection  
            self.name = _("Selected movies")
        cbkeys = []
        listpath = [] 
        for element in range(len(listpath)):
            if element <= 10:
                cbkeys.append(str(element))
            else:
                cbkeys.append("")
        listpath.append((_("To adjusted move/copy location"), "CALLFUNC", self.selectedLocation))
        cbkeys.append("blue")
        listpath.append((_("Directory Selection"), "CALLFUNC", self.selectDir))
        cbkeys.append("yellow")
        listpath.append((_("Show active move/copy processes"), "CALLFUNC", self.showActive))
        cbkeys.append("green")
        listpath.append((_("Abort"), "CALLFUNC", self.close))
        cbkeys.append("red")        
        if len(os.listdir(config.movielist.last_videodir.value)) == 0 and defaultMoviePath() <> config.movielist.last_videodir.value:
            listpath.append((_("Remove ' %s '") % config.movielist.last_videodir.value, "CALLFUNC", self.remove))
            cbkeys.append("red")
        ChoiceBox.__init__(self, session, list=listpath, keys=cbkeys)
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(_("Move/Copy from: %s") % self.name)

    def selectedLocation(self, arg):
        self.gotFilename(config.AdvancedMovieSelection.movecopydirs.value)

    def selectDir(self, arg):
        self.session.openWithCallback(self.gotFilename, MovieLocationBox, (_("Move/Copy %s") % self.name) + ' ' + _("to:"), config.movielist.last_videodir.value)

    def showActive(self, arg):
#Topfi start
        #tmp_out = os.popen("ps -ef | grep -e \"   [c]p /\" -e \"   [m]v /\"").readlines()
        tmp_out = os.popen("ps | grep -e \"   [c]p /\" -e \"   [m]v /\"").readlines()
#Topfi end
        tmpline = ""
        tmpcount = 0
        for line in tmp_out:
            tmpcount = tmpcount + 1
            tmpline = tmpline + "\n" + line.replace(" cp ", _("|Copy:\n"), 1).replace(" mv ", _("|Move:\n") , 1).split("|", 1)[1].rsplit(".", 1)[0]
        if tmpcount == 0:
            self.session.open(MessageBox, _("There are currently no files are moved or copied."), MessageBox.TYPE_INFO)
        elif tmpcount == 1:
            self.session.open(MessageBox, (_("The following file is being moved or copied currently:\n%s") % tmpline), MessageBox.TYPE_INFO)
        else:
            self.session.open(MessageBox, (_("The following %s") % str(tmpcount) + ' ' + _("files are being moved or copied currently:\n%s") % tmpline), MessageBox.TYPE_INFO)                    

    def remove(self, arg):
        os.rmdir(config.movielist.last_videodir.value)
        self.gotFilename(defaultMoviePath())

    def gotFilename(self, destinationpath, retval=None):
        if destinationpath is None:
            self.skipMoveFile(_("Directory selection has been canceled"))
        else:
            self.destinationpath = destinationpath
            listtmp = [(_("Move (in the background)"), "VH"), (_("Move (in the foreground)"), "VS"), (_("Copy (in the background)"), "KH"), (_("Copy (in the foreground)"), "KS"), (_("Abort"), "AB") ]
            self.session.openWithCallback(self.doMove, ChoiceBox, title=((_("How to proceed '%s'") % self.name) + ' ' + (_("from %s") % self.sourcepath) + ' ' + (_("to %s") % self.destinationpath) + ' ' + _("be moved/copied?")), list=listtmp)
    
    def getMovieFileName(self, service):
        filename = service.getPath().rsplit('/', 1)[1]
        return filename.rsplit(".", 1)[0]
    
    def doMove(self, confirmed):
        if confirmed is not None:
            if confirmed[1] != "AB":
                if os.path.exists(self.destinationpath) is False:
                    os.system("mkdir %s" % self.destinationpath)
                
                for service in self.service_list:
                    if os.path.exists(self.destinationpath + "/%s" % self.getMovieFileName(service)) is True:
                        self.skipMoveFile(_("File already exists"))
                        return
                    
                if confirmed[1] == "VS":
                    for service in self.service_list:
                        os.system("mv \"%s/%s.\"* \"%s\"" % (self.sourcepath, self.getMovieFileName(service), self.destinationpath))
                    self.session.openWithCallback(self.__doClose, MessageBox, _("The move was successful."), MessageBox.TYPE_INFO, timeout=3)
                elif confirmed[1] == "VH":
                    for service in self.service_list:
                        os.system("mv \"%s/%s.\"* \"%s\" &" % (self.sourcepath, self.getMovieFileName(service), self.destinationpath))
                    self.session.openWithCallback(self.__doClose, MessageBox, _("Moving in the background.\n\nThe movie list appears updated after full completion."), MessageBox.TYPE_INFO, timeout=6)
#Topfi start
                    MovieMove.checkAndReportStatus()
#Topfi end
                elif confirmed[1] == "KS":
                    for service in self.service_list:
                        os.system("cp \"%s/%s.\"* \"%s\"" % (self.sourcepath, self.getMovieFileName(service), self.destinationpath))
                    self.session.openWithCallback(self.__doClose, MessageBox, _("The copying was successful."), MessageBox.TYPE_INFO, timeout=3)
                elif confirmed[1] == "KH":
                    for service in self.service_list:
                        os.system("cp \"%s/%s.\"* \"%s\" &" % (self.sourcepath, self.getMovieFileName(service), self.destinationpath))
                    self.session.openWithCallback(self.__doClose, MessageBox, _("Copying in the background.\n\nThe movie list appears updated after full completion."), MessageBox.TYPE_INFO, timeout=6)
#Topfi start
                    MovieMove.checkAndReportStatus()
#Topfi end
            else:
                MovieMove(session=self.session, csel=self.csel, service=self.service_list[0])

    def __doClose(self, confirmed):
        self.csel.reloadList()
        self.close()

    def skipMoveFile(self, reason):
        self.session.open(MessageBox, (_("Move/Copy aborted due to:\n%s") % reason), MessageBox.TYPE_INFO)

#Topfi start
    @staticmethod
    def checkAndReportStatus():
        try:
            cpCount = os.popen("ps | grep -e \"   [c]p /\" -e \"   [m]v /\" | wc -l").readline()
            if int(cpCount) == 0:
                Notifications.AddPopup(text = _("All background move/copy operations completed.\n"), type = MessageBox.TYPE_INFO, timeout = 6)
            else:
                Timer(5, MovieMove.checkAndReportStatus).start()
        except:
            pass
#Topfi end		
