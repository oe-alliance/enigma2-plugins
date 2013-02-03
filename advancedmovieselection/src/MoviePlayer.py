#!/usr/bin/python
# -*- coding: utf-8 -*- 
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  The plugin is developed on the basis from a lot of single plugins (thx for the code @ all)
#  Coded by JackDaniel and cmikula (c)2012
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

import Screens.Standby
from Components.config import config
from Screens.Screen import Screen
from Components.ActionMap import HelpableActionMap
from MovieSelection import MovieSelection, Current, getBeginTimeString, getDateString
from MovieList import eServiceReferenceDvd
from ServiceProvider import DVDCutListSupport, CutListSupport, ServiceCenter, eServiceReferenceBludisc
from Screens.MessageBox import MessageBox
from Screens.InfoBar import MoviePlayer
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
try:
	from Tools.Directories import SCOPE_ACTIVE_SKIN
except:
	pass	
from enigma import ePoint, eTimer, iPlayableService
from Tools import Notifications
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.StaticText import StaticText
from MoviePreview import MoviePreview
from Components.Label import Label
from Components.ServiceEventTracker import ServiceEventTracker
from Globals import pluginPresent

PlayerInstance = None

def showMovies(self):
    global PlayerInstance
    PlayerInstance = None
    if config.AdvancedMovieSelection.startonfirst.value:
        self.session.openWithCallback(self.movieSelected, MovieSelection)
    else:
        self.session.openWithCallback(self.movieSelected, MovieSelection, Current.selection)

def stopPlayingService(self):
    try:
        global PlayerInstance
        if PlayerInstance is not None:
            PlayerInstance.playerClosed()
            self.session.nav.stopService()
            PlayerInstance.close()
            PlayerInstance = None
    except Exception, e:
        print "Player instance closed exception: " + str(e) 

class MoviePlayerExtended_summary(Screen):
    def __init__(self, session, parent):
        self.skinName = ["MoviePlayerExtended_summary"]
        Screen.__init__(self, session, parent)
        self["Title"] = Label("")
        self["ShortDesc"] = Label("")
        self["Seperator"] = StaticText("")

    def updateShortDescription(self, desc):
        self["ShortDesc"].setText(desc)

    def updateTitle(self, title):
        self["Title"].setText(title)

    def showSeperator(self):
        try:
            self["Seperator"].setText(resolveFilename(SCOPE_ACTIVE_SKIN, "images/sep_lcd_oled.png"))
        except:
            self["Seperator"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/images/sep_lcd_oled.png"))
    
    def hideSeperator(self):
        self["Seperator"].setText("")   
    
class SelectionEventInfo:
    def __init__(self):
        self["ServiceEvent"] = ServiceEvent()
        self["ShortDesc"] = Label("")
        self.timer = eTimer()
        self.timer.callback.append(self.updateEventInfo)
        self.onShow.append(self.__selectionChanged)

    def __selectionChanged(self):
        if self.execing:
            self.timer.start(100, True)

    def updateEventInfo(self):
        serviceref = self.session.nav.getCurrentlyPlayingServiceReference()
        if serviceref:
            self.loadPreview(serviceref)
            info = ServiceCenter.getInstance().info(serviceref)
            event = info.getEvent(serviceref)
            name = info.getName(serviceref)
            if not name or name == "":
                return
            desc = ""
            if event:
                desc = event.getShortDescription()              
            if name == desc or desc == "":
                if config.AdvancedMovieSelection.show_date_shortdesc.value and config.AdvancedMovieSelection.show_begintime.value:
                    desc = getBeginTimeString(info, serviceref)
                    self["ShortDesc"].setText(desc)
                    self["ServiceEvent"].newService(serviceref)
                else:
                    desc = ""
                    self["ShortDesc"].setText(desc)
                    self["ServiceEvent"].newService(serviceref)  
            self["ShortDesc"].setText(desc)
            self["ServiceEvent"].newService(serviceref)

class MoviePlayerExtended(CutListSupport, MoviePlayer, SelectionEventInfo, MoviePreview, MoviePlayerExtended_summary):
    def __init__(self, session, service):
        CutListSupport.__init__(self, service)
        MoviePlayer.__init__(self, session, service)
        MoviePreview.__init__(self, session)
        SelectionEventInfo.__init__(self)
        self.skinName = ["MoviePlayerExtended", "MoviePlayer"]
        global PlayerInstance
        PlayerInstance = self
        self["EPGActions"] = HelpableActionMap(self, "InfobarEPGActions",
            {
                "showEventInfo": (self.openInfoView, _("Show event details")),
                "showEventInfoPlugin": (self.openServiceList, _("Open servicelist"))
            })
        if config.AdvancedMovieSelection.exitkey.value and config.AdvancedMovieSelection.exitprompt.value:
            self["closeactions"] = HelpableActionMap(self, "WizardActions",
                {
                    "back": (self.leavePlayer, _("Leave movie player"))
                })
        if config.AdvancedMovieSelection.exitkey.value and not config.AdvancedMovieSelection.exitprompt.value: 
            self["closeactions"] = HelpableActionMap(self, "WizardActions",
                {
                    "back": (self.close, _("Leave movie player"))
                })
        if config.AdvancedMovieSelection.use_original_movieplayer_summary.value == True: 
            self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
                {
                        iPlayableService.evUpdatedInfo: self.__updateInfo
                })
        self.firstime = True
        self.onExecBegin.append(self.__onExecBegin)

    def createSummary(self):
        if config.AdvancedMovieSelection.use_original_movieplayer_summary.value == True:
            return MoviePlayerExtended_summary
        return MoviePlayer.createSummary(self)

    def __updateInfo(self):
        serviceref = self.session.nav.getCurrentlyPlayingServiceReference()
        if serviceref:
            info = ServiceCenter.getInstance().info(serviceref)
            name = info.getName(serviceref)
            if not name or name == "":
                return
            event = info.getEvent(serviceref)
            desc = ""
            if event:
                desc = event.getShortDescription()
            if not event or name == desc or desc == "":
                if config.AdvancedMovieSelection.show_date_shortdesc.value and config.AdvancedMovieSelection.show_begintime.value:
                    desc = getBeginTimeString(info, serviceref)
                    self.summaries.showSeperator()
                    self.summaries.updateTitle(name)
                    self.summaries.updateShortDescription(desc)                    
                elif config.AdvancedMovieSelection.show_date_shortdesc.value and not config.AdvancedMovieSelection.show_begintime.value:
                    desc = getDateString()
                    self.summaries.showSeperator()
                    self.summaries.updateTitle(name)
                    self.summaries.updateShortDescription(desc)
                else:
                    desc = ""
                    self.summaries.hideSeperator()
                    self.summaries.updateTitle(name)
                    self.summaries.updateShortDescription(desc)
            else:
                self.summaries.showSeperator()
                self.summaries.updateTitle(name)
                self.summaries.updateShortDescription(desc)

    def __onExecBegin(self):
        if self.firstime:
            orgpos = self.instance.position()    
            self.instance.move(ePoint(orgpos.x() + config.AdvancedMovieSelection.movieplayer_infobar_position_offset_x.value, orgpos.y() + config.AdvancedMovieSelection.movieplayer_infobar_position_offset_y.value))
            self.firstime = False
    
    def standbyCounterChanged(self, configElement):
        pass # prevent merlin crash, Select last played movie is disabled

    def openServiceList(self):
        if pluginPresent.AdvancedProgramGuide:
            from Plugins.Extensions.AdvancedProgramGuide.plugin import AdvancedProgramGuideII, AdvancedProgramGuide
            if config.plugins.AdvancedProgramGuide.StartFirst.value and config.plugins.AdvancedProgramGuide.Columns.value:
                self.session.open(AdvancedProgramGuideII)
            else:
                if config.plugins.AdvancedProgramGuide.StartFirst.value and not config.plugins.AdvancedProgramGuide.Columns.value:
                    self.session.open(AdvancedProgramGuide)
                else:
                    if not config.plugins.AdvancedProgramGuide.StartFirst.value and config.plugins.AdvancedProgramGuide.Columns.value:
                        from Screens.InfoBar import InfoBar
                        if InfoBar.instance:
                            servicelist = InfoBar.instance.servicelist
                            self.session.open(AdvancedProgramGuideII, servicelist)
                    else:
                        if not config.plugins.AdvancedProgramGuide.StartFirst.value and not config.plugins.AdvancedProgramGuide.Columns.value:
                            from Screens.InfoBar import InfoBar
                            if InfoBar.instance:
                                servicelist = InfoBar.instance.servicelist
                                self.session.open(AdvancedProgramGuide, servicelist)
        
        elif pluginPresent.MerlinEPGCenter and not pluginPresent.AdvancedProgramGuide and not pluginPresent.CoolTVGuide and not pluginPresent.MerlinEPGCenter:
            from Plugins.Extensions.MerlinEPG.plugin import Merlin_PGII, Merlin_PGd
            if config.plugins.MerlinEPG.StartFirst.value and config.plugins.MerlinEPG.Columns.value:
                self.session.open(Merlin_PGII)
            else:
                if config.plugins.MerlinEPG.StartFirst.value and not config.plugins.MerlinEPG.Columns.value:
                    self.session.open(Merlin_PGd)
                else:
                    if not config.plugins.MerlinEPG.StartFirst.value and config.plugins.MerlinEPG.Columns.value:
                        from Screens.InfoBar import InfoBar
                        if InfoBar.instance:
                            servicelist = InfoBar.instance.servicelist
                            self.session.open(Merlin_PGII, servicelist)
                    else:
                        if not config.plugins.MerlinEPG.StartFirst.value and not config.plugins.MerlinEPG.Columns.value:
                            from Screens.InfoBar import InfoBar
                            if InfoBar.instance:
                                servicelist = InfoBar.instance.servicelist
                                self.session.open(Merlin_PGd, servicelist)
        
        elif pluginPresent.CoolTVGuide and not pluginPresent.AdvancedProgramGuide and not pluginPresent.MerlinEPGCenter and not pluginPresent.MerlinEPGCenter:
            from Plugins.Extensions.CoolTVGuide.plugin import main as ctvmain
            ctvmain(self.session)
        
        elif pluginPresent.MerlinEPGCenter and not pluginPresent.CoolTVGuide and not pluginPresent.AdvancedProgramGuide and not pluginPresent.MerlinEPGCenter:
            from Plugins.Extensions.MerlinEPGCenter.plugin import MerlinEPGCenterStarter
            MerlinEPGCenterStarter.instance.openMerlinEPGCenter()
        else:
            self.session.open(MessageBox, _("Not possible!\nMerlinEPG and CoolTVGuide or/and MerlinEPGCenter present or neither installed from this three plugins."), MessageBox.TYPE_INFO)
            
    def openInfoView(self):
        from AdvancedMovieSelectionEventView import EventViewSimple
        serviceref = self.session.nav.getCurrentlyPlayingServiceReference()
        info = ServiceCenter.getInstance().info(serviceref)
        evt = info.getEvent(serviceref)
        if evt:
            self.session.open(EventViewSimple, evt, serviceref)

    def showMovies(self):
        ref = self.session.nav.getCurrentlyPlayingServiceReference()
        self.session.openWithCallback(self.movieSelected, MovieSelection, ref, True)

    def handleLeave(self, how):
        self.playerClosed()
        self.is_closing = True
        if how == "ask":
            if config.usage.setup_level.index < 2: # -expert
                list = (
                    (_("Yes"), "quit"),
                    (_("No"), "continue")
                )
            else:
                list = (
                    (_("Yes"), "quit"),
                    (_("Yes, returning to movie list"), "movielist"),
                    (_("Yes, and delete this movie"), "quitanddelete"),
                    (_("Yes, and after deleting return to movie list"), "returnanddelete"),
                    (_("No"), "continue"),
                    (_("No, but restart from begin"), "restart")
                )

            from Screens.ChoiceBox import ChoiceBox
            self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Stop playing this movie?"), list=list)
        else:
            self.leavePlayerConfirmed([True, how])

    def returnanddeleteConfirmed(self, answer):
        if answer:
            self.leavePlayerConfirmed((True, "returnanddeleteconfirmed"))

    def leavePlayerConfirmed(self, answer):
        answer = answer and answer[1]
        if answer in ("quitanddelete", "quitanddeleteconfirmed", "returnanddelete", "returnanddeleteconfirmed"):
            ref = self.session.nav.getCurrentlyPlayingServiceReference()
            from enigma import eServiceCenter
            serviceHandler = eServiceCenter.getInstance()
            info = serviceHandler.info(ref)
            name = info and info.getName(ref) or _("this recording")

            if answer == "quitanddelete":
                if config.AdvancedMovieSelection.askdelete.value:
                    from Screens.MessageBox import MessageBox
                    self.session.openWithCallback(self.deleteConfirmed, MessageBox, _("Do you really want to delete %s?") % name)
                    return
                else:
                    self.deleteConfirmed(True)
            elif answer == "returnanddelete":
                if config.AdvancedMovieSelection.askdelete.value:
                    from Screens.MessageBox import MessageBox
                    self.session.openWithCallback(self.returnanddeleteConfirmed, MessageBox, _("Do you really want to delete %s?") % name)
                    return
                else:
                    self.returnanddeleteConfirmed(True)
            elif answer in("quitanddeleteconfirmed", "returnanddeleteconfirmed"):
                self.delete(ref)
#                offline = serviceHandler.offlineOperations(ref)
#                if offline.deleteFromDisk(0):
#                    self.session.openWithCallback(self.close, MessageBox, _("You cannot delete this!"), MessageBox.TYPE_ERROR)
#                    return
                
        if answer in ("quit", "quitanddeleteconfirmed"):
            self.close()
        elif answer == "standby":
            self.session.openWithCallback(self.standby, MessageBox, _("End of the movie is reached, the box now go to standby. Do that now?"), timeout=20)
            self.close()
        elif answer == "shutdown":
            self.session.openWithCallback(self.shutdown, MessageBox, _("End of the movie is reached, the box now go to shut down. Shutdown now?"), timeout=20)
            self.close()
        elif answer in ("movielist", "returnanddeleteconfirmed"):
            ref = self.session.nav.getCurrentlyPlayingServiceReference()
            self.returning = True
            self.session.openWithCallback(self.movieSelected, MovieSelection, ref, True)
            self.session.nav.stopService()
            self.session.nav.playService(self.lastservice) # Fix busy tuner after stby with playing service
        elif answer == "restart":
            self.doSeek(0)
            self.setSeekState(self.SEEK_STATE_PLAY)

    def delete(self, service):
        from Trashcan import Trashcan
        if config.AdvancedMovieSelection.use_wastebasket.value:
            Trashcan.trash(service.getPath())
        else:
            Trashcan.delete(service.getPath())

    def standby(self, answer):
        if answer is not None:
            if answer and not Screens.Standby.inStandby:
                Notifications.AddNotification(Screens.Standby.Standby)
            else:
                self.close()

    def shutdown(self, answer):
        if answer is not None:
            if answer and not Screens.Standby.inTryQuitMainloop:
                Notifications.AddNotification(Screens.Standby.TryQuitMainloop, 1)
            else:
                self.close()

if pluginPresent.DVDPlayer:
    from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer as eDVDPlayer
    class DVDPlayer(DVDCutListSupport, eDVDPlayer):
        def __init__(self, session, service):
            DVDCutListSupport.__init__(self, service)
            eDVDPlayer.__init__(self, session, dvd_filelist=service.getDVD())
            self.addPlayerEvents()

if pluginPresent.BludiscPlayer:
    from Plugins.Extensions.BludiscPlayer.plugin import BludiscPlayer as eBludiscPlayer, BludiscMenu as eBludiscMenu
    from enigma import eServiceReference
    from ServiceProvider import BludiscCutListSupport
    class BludiscPlayer(BludiscCutListSupport, eBludiscPlayer):
        def __init__(self, session, service, file_name, is_main_movie):
            s = eServiceReferenceBludisc(service)
            if file_name:
                s.setPath(file_name)
            BludiscCutListSupport.__init__(self, s, is_main_movie)
            eBludiscPlayer.__init__(self, session, service)
            self.addPlayerEvents()

        def handleLeave(self, how):
            self.is_closing = True
            if how == "ask":
                list = (
                    (_("Yes"), "quit"),
                    (_("No"), "continue")
                )
                from Screens.ChoiceBox import ChoiceBox
                self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Stop playing this movie?"), list = list)
            else:
                self.leavePlayerConfirmed([True, "quit"])
    
    class BludiscMenu(eBludiscMenu):
        def __init__(self, session, bd_mountpoint = None, file_name = None):
            eBludiscMenu.__init__(self, session, bd_mountpoint)
            self.file_name = file_name
        
        def getMainMovieIndex(self):
            index = -1
            dur = 0
            if isinstance(self.discinfo, dict):
                for idx, duration, chapters, angels, clips, title_no, title_name in self.discinfo["titles"]:
                    if dur < duration:
                        dur = duration
                        index = idx
            return index
 
        def ok(self):
            if type(self["menu"].getCurrent()) is type(None):
                self.exit()
                return
            name = self["menu"].getCurrent()[0]
            idx = self["menu"].getCurrent()[1]
            newref = eServiceReference(0x04, 0, "%s:%03d" % (self.bd_mountpoint, idx))
            newref.setData(1,1)
            newref.setName("Bludisc title %d" % idx)
            print "[Bludisc] play: ", name, newref.toString()
            main_movie = idx == self.getMainMovieIndex()
            self.session.openWithCallback(self.moviefinished, BludiscPlayer, newref, self.file_name, main_movie)
        
        def exit(self):
            from ServiceProvider import ISOInfo
            ISOInfo().umount()
            self.close()

def movieSelected(self, service):
    if service is not None:
        if isinstance(service, eServiceReferenceDvd) and service.isIsoImage():
            from ServiceProvider import ISOInfo
            iso = ISOInfo()
            if iso.getFormatISO9660(service) != ISOInfo.DVD:
                iso_format = iso.getFormat(service)
                if iso_format == ISOInfo.ERROR:
                    self.session.open(MessageBox, _("Error loading ISO image!"), MessageBox.TYPE_ERROR)
                    return
                if iso_format == ISOInfo.UNKNOWN:
                    self.session.open(MessageBox, _("Selected ISO image is not playable!"), MessageBox.TYPE_ERROR)
                    return
                if iso_format == ISOInfo.BLUDISC:
                    service = iso.getService(service)
        if isinstance(service, eServiceReferenceDvd):
            if pluginPresent.DVDPlayer:
                stopPlayingService(self)
                self.session.open(DVDPlayer, service)
            else:
                self.session.open(MessageBox, _("No DVD-Player found!"), MessageBox.TYPE_ERROR, 10)
        elif isinstance(service, eServiceReferenceBludisc):
            if pluginPresent.BludiscPlayer:
                stopPlayingService(self)
                self.session.open(BludiscMenu, service.getBludisc(), service.getPath())
            else:
                self.session.open(MessageBox, _("No BludiscPlayer found!"), MessageBox.TYPE_ERROR, 10)
        else:
            self.session.open(MoviePlayerExtended, service)
