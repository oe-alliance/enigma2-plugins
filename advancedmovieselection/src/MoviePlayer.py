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
from __init__ import _
from Components.config import config
from Screens.Screen import Screen
from Components.ActionMap import HelpableActionMap
from MovieSelection import MovieSelection, getBeginTimeString, getDateString
from MovieList import eServiceReferenceDvd
from Source.ServiceProvider import ServiceCenter, eServiceReferenceBludisc
from Source.CueSheetSupport import DVDCutListSupport, CutListSupport
from Screens.MessageBox import MessageBox
from Screens.InfoBar import MoviePlayer
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN, fileExists
# Andy Blackburn [add support for SCOPE_ACTIVE_SKIN] begin
try:
	from Tools.Directories import SCOPE_ACTIVE_SKIN
except:
	pass	
# Andy Blackburn [add support for SCOPE_ACTIVE_SKIN] end
from enigma import ePoint, eTimer, iPlayableService
from Tools import Notifications
from Components.Sources.ServiceEvent import ServiceEvent
#from ServiceProvider import ServiceEvent
from Components.Sources.StaticText import StaticText
from MoviePreview import MoviePreview
from Components.Label import Label
from Components.ServiceEventTracker import ServiceEventTracker
from Source.Globals import pluginPresent
from Version import __version__

playerChoice = None
if fileExists("/etc/grautec/dm8000/tft_dm8000.ko"):
    TFT_8000_Present = True
else:
    TFT_8000_Present = False

def cutlist_changed(self):
    if playerChoice and playerChoice.isPlaying():
        self.cutlist = [] # we need to update the property 
    self.cutlist = self.source.cutlist or [ ]

from Components.Renderer.PositionGauge import PositionGauge
PositionGauge.cutlist_changed = cutlist_changed


def showMovies(self):
    initPlayerChoice(self.session)
    self.lastservice = self.session.nav.getCurrentlyPlayingServiceReference()
    self.session.openWithCallback(playerChoice.playService, MovieSelection)
    if config.AdvancedMovieSelection.version.value != __version__:
        from About import AboutDetails
        self.session.open(AboutDetails)
        config.AdvancedMovieSelection.version.value = __version__
        config.AdvancedMovieSelection.version.save()

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
        if TFT_8000_Present:
            self["Seperator"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "images/sep_tft.png"))
        else:
            # Andy Blackburn [add support for SCOPE_ACTIVE_SKIN] begin
            #self["Seperator"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "images/sep_lcd_oled.png"))
            try:
                self["Seperator"].setText(resolveFilename(SCOPE_ACTIVE_SKIN, "images/sep_lcd_oled.png"))
            except:
                self["Seperator"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/images/sep_lcd_oled.png"))
            # Andy Blackburn [add support for SCOPE_ACTIVE_SKIN] end

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

class PlayerBase(MoviePreview, SelectionEventInfo):
    def __init__(self, session):
        MoviePreview.__init__(self, session)
        SelectionEventInfo.__init__(self)
        self["EPGActions"] = HelpableActionMap(self, "InfobarEPGActions",
            {
                "showEventInfo": (self.openInfoView, _("Show event details")),
                "showEventInfoPlugin": (self.openServiceList, _("Open servicelist"))
            })
        self.endless_loop = False
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
            {
                iPlayableService.evEnd: self.__evServiceEnd
            })
    
    def __evServiceEnd(self):
        if not self.is_closing and not self.new_service_started:
            print "Close on timer switch!!!"
            self.close()
    
    def openServiceList(self):
        pass

    def openInfoView(self):
        from AdvancedMovieSelectionEventView import EventViewSimple
        serviceref = self.session.nav.getCurrentlyPlayingServiceReference()
        info = ServiceCenter.getInstance().info(serviceref)
        evt = info.getEvent(serviceref)
        if evt:
            self.session.open(EventViewSimple, evt, serviceref)


class MoviePlayerExtended(CutListSupport, MoviePlayer, PlayerBase):
    def __init__(self, session, service):
        CutListSupport.__init__(self, service)
        MoviePlayer.__init__(self, session, service)
        PlayerBase.__init__(self, session)
        self.skinName = ["MoviePlayerExtended", "MoviePlayer"]
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

    def showMovies(self):
        ref = self.session.nav.getCurrentlyPlayingServiceReference()
        self.playingservice = ref # movie list may change the currently playing
        self.session.openWithCallback(self.newServiceSelected, MovieSelection, ref, True)
    
    def newServiceSelected(self, service):
        if service:
            self.new_service_started = True
            s = playerChoice.getBestPlayableService(service)
            p = playerChoice.getPlayerForService(s)
            if not isinstance(self, p):
                self.playerClosed()
                self.close(service)
            else:
                self.playNewService(service)

    def doEofInternal(self, playing): # Override method in MoviePlayer
        if not self.endless_loop:
            return MoviePlayer.doEofInternal(self, playing)

        if not self.execing:
            return
        if not playing:
            return
        self.leavePlayerConfirmed([True, "restart"])
    
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
                loop_msg = self.endless_loop and _("No, but stop endless loop") or _("No, but start endless loop") 
                list = (
                    (_("Yes"), "quit"),
                    (_("Yes, returning to movie list"), "movielist"),
                    (_("Yes, and delete this movie"), "quitanddelete"),
                    (_("Yes, and after deleting return to movie list"), "returnanddelete"),
                    (_("No"), "continue"),
                    (_("No, but restart from begin"), "restart"),
                    (loop_msg, "toggle_loop")
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
            self.session.nav.stopService()
            self.session.nav.playService(self.lastservice) # Fix busy tuner after stby with playing service
            playerChoice.playing = False
            self.session.openWithCallback(playerChoice.playService, MovieSelection, ref, True)
        elif answer == "restart":
            self.doSeek(0)
            self.setSeekState(self.SEEK_STATE_PLAY)
        elif answer == "toggle_loop":
            self.endless_loop = not self.endless_loop

    def delete(self, service):
        from Source.Trashcan import Trashcan
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
    class DVDPlayer(DVDCutListSupport, eDVDPlayer, PlayerBase):
        def __init__(self, session, service):
            DVDCutListSupport.__init__(self, service)
            eDVDPlayer.__init__(self, session, dvd_filelist=service.getDVD())
            PlayerBase.__init__(self, session)
            self.skinName = ["DVDPlayerExtended", "DVDPlayer"]
            self.addPlayerEvents()

        def askLeavePlayer(self):
            if config.AdvancedMovieSelection.exitkey.value:
                self.exitCB([None, "exit"])
            else:
                eDVDPlayer.askLeavePlayer(self)
        
        def exitCB(self, answer):
            if answer is not None:
                if answer[1] == "browser":
                    #TODO check here if a paused dvd playback is already running... then re-start it...
                    #else
                    if self.service:
                        self.service = None
                    from MovieSelection import MovieSelection
                    ref = self.session.nav.getCurrentlyPlayingServiceReference()
                    self.session.openWithCallback(self.newServiceSelected, MovieSelection, ref, True)
                    return
            eDVDPlayer.exitCB(self, answer)

        def newServiceSelected(self, service):
            if service:
                s = playerChoice.getBestPlayableService(service)
                p = playerChoice.getPlayerForService(s)
                if not isinstance(self, p):
                    self.close(service)
                elif self.currentService != service: 
                    self.playerClosed(service)
                    self.FileBrowserClosed(service.getDVD()[0])

if pluginPresent.BludiscPlayer:
    from Plugins.Extensions.BludiscPlayer.plugin import BludiscPlayer as eBludiscPlayer, BludiscMenu as eBludiscMenu
    from enigma import eServiceReference
    from Source.CueSheetSupport import BludiscCutListSupport
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
        def __init__(self, session, service):
            eBludiscMenu.__init__(self, session, service.getBludisc())
            self.file_name = service.getPath()
        
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
            print "[Bludisc] playService: ", name, newref.toString()
            main_movie = idx == self.getMainMovieIndex()
            self.session.openWithCallback(self.moviefinished, BludiscPlayer, newref, self.file_name, main_movie)
        
        def exit(self):
            from Source.ISOInfo import ISOInfo
            ISOInfo().umount()
            self.close()

class PlayerChoice():
    def __init__(self, session):
        self.session = session
        self.playing = False
        self.dialog = None

    def getBestPlayableService(self, service):
        if isinstance(service, eServiceReferenceDvd) and service.isIsoImage():
            from Source.ISOInfo import ISOInfo
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
        return service
    
    def getPlayerForService(self, service):
        player = None
        if service is not None:
            if isinstance(service, eServiceReferenceDvd):
                if pluginPresent.DVDPlayer:
                    player = DVDPlayer
                else:
                    self.session.open(MessageBox, _("No DVD-PlayerChoice found!"), MessageBox.TYPE_ERROR) # Topfi: removed last parameter
            elif isinstance(service, eServiceReferenceBludisc):
                if pluginPresent.BludiscPlayer:
                    player = BludiscMenu
                else:
                    self.session.open(MessageBox, _("No BludiscPlayer found!"), MessageBox.TYPE_ERROR) # Topfi: removed last parameter
            else:
                player = MoviePlayerExtended
        return player

    def playService(self, service):
        if service is not None:
            service = self.getBestPlayableService(service)
            player = self.getPlayerForService(service)
            if player:
                self.playing = True
                dlg = self.dialog
                self.dialog = self.session.openWithCallback(self.playerClosed, player, service)
                if dlg:
                    dlg.close()
        elif self.dialog:
            self.dialog.close()
            self.dialog = None
    
    def playerClosed(self, service=None):
        self.playing = False
        if service:
            self.playService(service)
    
    def isPlaying(self):
        return self.playing

    def stopPlaying(self):
        self.playing = False

def initPlayerChoice(session):
    global playerChoice
    if playerChoice:
        return
    playerChoice = PlayerChoice(session)
