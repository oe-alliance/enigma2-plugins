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
from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import HelpableActionMap
from MovieSelection import MovieSelection, Current, getBeginTimeString, getDateString
from MovieList import eServiceReferenceDvd
from ServiceProvider import DVDCutListSupport, CutListSupport, ServiceCenter
from Screens.MessageBox import MessageBox
from Screens.InfoBar import InfoBar, MoviePlayer
from Tools.Directories import fileExists, resolveFilename, SCOPE_HDD, SCOPE_CURRENT_SKIN
from Components.config import config, ConfigSubsection, ConfigText, ConfigYesNo, ConfigInteger, ConfigSelection, ConfigClock
from AdvancedMovieSelectionSetup import AdvancedMovieSelectionSetup
from enigma import ePoint, eTimer, iPlayableService
from TagEditor import TagEditor
import Screens.Standby
from Tools import Notifications
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.StaticText import StaticText
from MoviePreview import MoviePreview
from Components.Label import Label
from Components.ServiceEventTracker import ServiceEventTracker
from time import time, localtime, mktime
from datetime import datetime, timedelta

if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/IMDb/plugin.pyo"):
    IMDbPresent = True
else:
    IMDbPresent = False
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/OFDb/plugin.pyo"):
    OFDbPresent = True
else:
    OFDbPresent = False
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/AdvancedProgramGuide/plugin.pyo"):
    from Plugins.Extensions.AdvancedProgramGuide.plugin import AdvancedProgramGuideII, AdvancedProgramGuide
    AdvancedProgramGuidePresent = True
else:
    AdvancedProgramGuidePresent = False
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MerlinEPG/plugin.pyo"):
    from Plugins.Extensions.MerlinEPG.plugin import Merlin_PGII, Merlin_PGd
    MerlinEPGPresent = True
else:
    MerlinEPGPresent = False
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/CoolTVGuide/plugin.pyo"):
    CoolTVGuidePresent = True
else:
    CoolTVGuidePresent = False
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/YTTrailer/plugin.pyo"):
    from Plugins.Extensions.YTTrailer.plugin import YTTrailerList
    YTTrailerPresent = True
else:
    YTTrailerPresent = False
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MerlinEPGCenter/plugin.pyo"):
    MerlinEPGCenterPresent = True
else:
    MerlinEPGCenterPresent = False

config.AdvancedMovieSelection = ConfigSubsection()
config.AdvancedMovieSelection.wastelist_buildtype = ConfigSelection(default="listMovies" , choices=[("listMovies", _("Only current location")), ("listAllMovies", _("Current location and all subdirectories")), ("listAllMoviesMedia", _("All directorys below '/media'")) ])
config.AdvancedMovieSelection.use_wastebasket = ConfigYesNo(default=False)
config.AdvancedMovieSelection.overwrite_left_right = ConfigYesNo(default=True)
config.AdvancedMovieSelection.sensibility = ConfigInteger(default=10, limits=(1, 100))
config.AdvancedMovieSelection.useseekbar = ConfigYesNo(default=False)
config.AdvancedMovieSelection.showinfo = ConfigYesNo(default=True)
config.AdvancedMovieSelection.showcoveroptions2 = ConfigYesNo(default=False)
config.AdvancedMovieSelection.exitprompt = ConfigYesNo(default=False)
config.AdvancedMovieSelection.exitkey = ConfigYesNo(default=False)
config.AdvancedMovieSelection.showtrailer = ConfigYesNo(default=False)
config.AdvancedMovieSelection.jump_first_mark = ConfigYesNo(default=False)
config.AdvancedMovieSelection.showfiltertags = ConfigYesNo(default=False)
config.AdvancedMovieSelection.showmovietagsinmenu = ConfigYesNo(default=False)
config.AdvancedMovieSelection.usefoldername = ConfigYesNo(default=True)
config.AdvancedMovieSelection.minitv = ConfigYesNo(default=True)
config.AdvancedMovieSelection.shownew = ConfigYesNo(default=True)
config.AdvancedMovieSelection.dateformat = ConfigSelection(default="6" , choices=[("6" , _("German (without Year)")), ("1" , _("German (with Year)")), ("3" , _("German (with Starttime)")), ("2" , _("Enigma 2 default")), ("7" , _("English (without Year)")), ("4" , _("English (with Year)")), ("5" , _("English (with Starttime)"))])
config.AdvancedMovieSelection.color1 = ConfigSelection(default="yellow" , choices=[("yellow" , _("Yellow")), ("blue" , _("Blue")), ("red" , _("Red")), ("black" , _("Black")), ("green" , _("Green"))])
config.AdvancedMovieSelection.color2 = ConfigSelection(default="green" , choices=[("green" , _("Green")), ("blue" , _("Blue")), ("red" , _("Red")), ("black" , _("Black")), ("yellow" , _("Yellow"))])
config.AdvancedMovieSelection.color3 = ConfigSelection(default="red" , choices=[("red" , _("Red")), ("blue" , _("Blue")), ("green" , _("Green")), ("black" , _("Black")), ("yellow" , _("Yellow"))])
config.AdvancedMovieSelection.color4 = ConfigSelection(default="grey" , choices=[("grey" , _("Grey")), ("red" , _("Red")), ("blue" , _("Blue")), ("green" , _("Green")), ("black" , _("Black")), ("yellow" , _("Yellow")), ("orange" , _("Orange")), ])
config.AdvancedMovieSelection.moviepercentseen = ConfigInteger(default=80, limits=(50, 100))
config.AdvancedMovieSelection.showfoldersinmovielist = ConfigYesNo(default=False)
config.AdvancedMovieSelection.showprogessbarinmovielist = ConfigYesNo(default=False)
config.AdvancedMovieSelection.showiconstatusinmovielist = ConfigYesNo(default=False)
config.AdvancedMovieSelection.showcolorstatusinmovielist = ConfigYesNo(default=False)
config.AdvancedMovieSelection.about = ConfigSelection(default="1", choices=[("1", " ")])
config.AdvancedMovieSelection.ml_disable = ConfigYesNo(default=False)
config.AdvancedMovieSelection.showmenu = ConfigYesNo(default=True)
config.AdvancedMovieSelection.pluginmenu_list = ConfigYesNo(default=False)
config.AdvancedMovieSelection.red = ConfigText(default=_("Delete"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.green = ConfigText(default=_("Nothing"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.yellow = ConfigText(default=_("Nothing"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.blue = ConfigText(default=_("Nothing"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark1text = ConfigText(default=_("Bookmark 1"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark2text = ConfigText(default=_("Bookmark 2"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark3text = ConfigText(default=_("Bookmark 3"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.hometext = ConfigText(default=_("Home"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.homepath = ConfigText(default="/hdd/movie/")
config.AdvancedMovieSelection.bookmark1path = ConfigText(default="/hdd/movie/")
config.AdvancedMovieSelection.bookmark2path = ConfigText(default="/hdd/movie/")
config.AdvancedMovieSelection.bookmark3path = ConfigText(default="/hdd/movie/")
config.AdvancedMovieSelection.buttoncaption = ConfigText(default="Display plugin name")
config.AdvancedMovieSelection.homeowntext = ConfigText(default=_("Homebutton"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark1owntext = ConfigText(default=_("Own text 1"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark1owntext = ConfigText(default=_("Own text 2"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark2owntext = ConfigText(default=_("Own text 3"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark3owntext = ConfigText(default=_("Own text 4"), visible_width=50, fixed_size=False)
launch_choices = [    ("None", _("No override")),
                            ("showMovies", _("Video-button")),
                            ("showTv", _("TV-button")),
                            ("showRadio", _("Radio-button")),
                            ("timeshiftStart", _("Timeshift-button"))]
config.AdvancedMovieSelection.movie_launch = ConfigSelection(default="showMovies", choices=launch_choices)
config.AdvancedMovieSelection.askdelete = ConfigYesNo(default=True)
config.AdvancedMovieSelection.moviepercentseen = ConfigInteger(default=85, limits=(50, 100))
config.AdvancedMovieSelection.AskEventinfo = ConfigYesNo(default=True)
config.AdvancedMovieSelection.Eventinfotyp = ConfigSelection(choices=[("Ei", _("Advanced Movie Selection info")), ("Ti", _("TMDb info")), ("Ii", _("IMDb info")), ("Oi", _("OFDb info"))], default="Ei")
config.AdvancedMovieSelection.Eventinfotyp2 = ConfigSelection(choices=[("Ei", _("Advanced Movie Selection info")), ("Ii", _("IMDb info"))], default="Ei")
config.AdvancedMovieSelection.Eventinfotyp3 = ConfigSelection(choices=[("Ei", _("Advanced Movie Selection info")), ("Oi", _("OFDb info"))], default="Ei")
config.AdvancedMovieSelection.Eventinfotyp4 = ConfigSelection(choices=[("Ei", _("Advanced Movie Selection info")), ("Ti", _("TMDb info"))], default="Ei")
config.AdvancedMovieSelection.Eventinfotyp5 = ConfigSelection(choices=[("Ei", _("Advanced Movie Selection info")), ("Ti", _("TMDb info")), ("Ii", _("IMDb info"))], default="Ei")
config.AdvancedMovieSelection.Eventinfotyp6 = ConfigSelection(choices=[("Ei", _("Advanced Movie Selection info")), ("Ti", _("TMDb info")), ("Oi", _("OFDb info"))], default="Ei")
config.AdvancedMovieSelection.Eventinfotyp7 = ConfigSelection(choices=[("Ei", _("Advanced Movie Selection info")), ("Ii", _("IMDb info")), ("Oi", _("OFDb info"))], default="Ei")
config.AdvancedMovieSelection.showcolorkey = ConfigYesNo(default=True)
config.AdvancedMovieSelection.showliststyle = ConfigYesNo(default=True)
config.AdvancedMovieSelection.showextras = ConfigYesNo(default=True)
config.AdvancedMovieSelection.showsort = ConfigYesNo(default=True)
config.usage.load_length_of_movies_in_moviellist = ConfigYesNo(default=True)
config.AdvancedMovieSelection.showmark = ConfigYesNo(default=True)
config.AdvancedMovieSelection.startdir = ConfigYesNo(default=False)
config.AdvancedMovieSelection.showdelete = ConfigYesNo(default=True)
config.AdvancedMovieSelection.showmove = ConfigYesNo(default=True)
config.AdvancedMovieSelection.startonfirst = ConfigYesNo(default=True)
config.AdvancedMovieSelection.movecopydirs = ConfigText(default=resolveFilename(SCOPE_HDD))
config.AdvancedMovieSelection.showsearch = ConfigYesNo(default=True)
config.AdvancedMovieSelection.showcoveroptions = ConfigYesNo(default=True)
config.AdvancedMovieSelection.showpreview = ConfigYesNo(default=True)
config.AdvancedMovieSelection.showrename = ConfigYesNo(default=True)
config.AdvancedMovieSelection.coversize = ConfigSelection(default="cover", choices=[("original", _("Original (1000x1500)")), ("mid", _("Mid (500x750)")), ("cover", _("Cover (185x278)")), ("thumb", _("Thumb (92x138)"))])
config.AdvancedMovieSelection.description = ConfigYesNo(default=True)
config.AdvancedMovieSelection.showtmdb = ConfigYesNo(default=True)
config.AdvancedMovieSelection.show_info_cover_del = ConfigYesNo(default=True)
config.AdvancedMovieSelection.show_info_del = ConfigYesNo(default=True)
config.AdvancedMovieSelection.show_cover_del = ConfigYesNo(default=True)
config.usage.on_movie_start = ConfigSelection(default="ask", choices=[("ask", _("Ask user")), ("resume", _("Resume from last position")), ("beginning", _("Start from the beginning"))])
config.usage.on_movie_stop = ConfigSelection(default="movielist", choices=[("ask", _("Ask user")), ("movielist", _("Return to movie list")), ("quit", _("Return to previous service"))])
config.usage.on_movie_eof = ConfigSelection(default="quit", choices=[("ask", _("Ask user")), ("movielist", _("Return to movie list")), ("quit", _("Return to previous service")), ("pause", _("Pause movie at end")), ("standby", _("Standby")), ("shutdown", _("Shutdown"))])
config.AdvancedMovieSelection.movieplayer_infobar_position_offset_x = ConfigInteger(default=0)
config.AdvancedMovieSelection.movieplayer_infobar_position_offset_y = ConfigInteger(default=0)
config.AdvancedMovieSelection.show_infobar_position = ConfigYesNo(default=True)
config.AdvancedMovieSelection.show_bookmarks = ConfigYesNo(default=True)
config.AdvancedMovieSelection.stop_before_end_time = ConfigInteger(default=5, limits=(0, 30))
config.AdvancedMovieSelection.debug = ConfigYesNo(default=False)
config.AdvancedMovieSelection.hotplug = ConfigYesNo(default=True)
config.AdvancedMovieSelection.show_picon = ConfigYesNo(default=True)
config.AdvancedMovieSelection.piconsize = ConfigYesNo(default=True)
config.AdvancedMovieSelection.piconpath = ConfigText(default=("/usr/share/enigma2/picon"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.show_wastebasket = ConfigYesNo(default=True)
config.AdvancedMovieSelection.use_original_movieplayer_summary = ConfigYesNo(default=False)
config.AdvancedMovieSelection.auto_empty_wastebasket = ConfigSelection(default="-1", choices=[("-1", _("Disabled")), ("1", _("Daily")), ("2", _("Every second day")), ("7", _("Weekly")), ("14", _("Every two weeks")), ("30", _("Monthly"))])
config.AdvancedMovieSelection.empty_wastebasket_time = ConfigClock(default=10800)
config.AdvancedMovieSelection.last_auto_empty_wastebasket = ConfigInteger(default=0)
config.AdvancedMovieSelection.next_auto_empty_wastebasket = ConfigInteger(default=0)
config.AdvancedMovieSelection.next_empty_check = ConfigInteger(default=30, limits=(01, 60))
config.AdvancedMovieSelection.show_update_genre = ConfigYesNo(default=False)
config.AdvancedMovieSelection.show_begintime = ConfigYesNo(default=False)
config.AdvancedMovieSelection.show_date_shortdesc = ConfigYesNo(default=False)
config.AdvancedMovieSelection.server_enabled = ConfigYesNo(default=False)
config.AdvancedMovieSelection.start_search_ip = ConfigInteger(default=1, limits=(1, 254))
config.AdvancedMovieSelection.stop_search_ip = ConfigInteger(default=254, limits=(1, 254))
config.AdvancedMovieSelection.server_port = ConfigInteger(default=20000, limits=(1, 65535))
config.AdvancedMovieSelection.show_remote_setup = ConfigYesNo(default=False)
config.AdvancedMovieSelection.show_dirsize = ConfigYesNo(default=False)
config.AdvancedMovieSelection.show_dirsize_full = ConfigYesNo(default=False)
config.AdvancedMovieSelection.dirsize_digits = ConfigSelection(default="0", choices=[("0", _("0")), ("1", _("1")), ("2", _("2")), ("3", _("3"))])
config.AdvancedMovieSelection.showpercentinmovielist = ConfigYesNo(default=False)
config.AdvancedMovieSelection.filesize_digits = ConfigSelection(default="1", choices=[("0", _("0")), ("1", _("1")), ("2", _("2")), ("3", _("3"))])
config.AdvancedMovieSelection.showthetvdb = ConfigYesNo(default=False)
config.AdvancedMovieSelection.video_preview = ConfigYesNo(default=False)
config.AdvancedMovieSelection.video_preview_delay = ConfigInteger(default=1, limits=(0, 10))
config.AdvancedMovieSelection.video_preview_marker = ConfigYesNo(default=False)
config.AdvancedMovieSelection.video_preview_jump_time = ConfigInteger(default=5, limits=(1, 60))
config.AdvancedMovieSelection.video_preview_autostart = ConfigYesNo(default=True)

PlayerInstance = None

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
        self["Seperator"].setText(resolveFilename(SCOPE_CURRENT_SKIN, "images/sep_lcd_oled.png"))
    
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
        if AdvancedProgramGuidePresent:
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
        else:
            if MerlinEPGPresent and not AdvancedProgramGuidePresent and not CoolTVGuidePresent and not MerlinEPGCenterPresent:
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
            else:
                if CoolTVGuidePresent and not AdvancedProgramGuidePresent and not MerlinEPGPresent and not MerlinEPGCenterPresent:
                    from Plugins.Extensions.CoolTVGuide.plugin import main as ctvmain
                    ctvmain(self.session)
                else:
                    if MerlinEPGCenterPresent and not CoolTVGuidePresent and not AdvancedProgramGuidePresent and not MerlinEPGPresent:
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
            self.session.nav.playService(self.lastservice)
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

def showMovies(self):
    global PlayerInstance
    PlayerInstance = None
    if config.AdvancedMovieSelection.startonfirst.value:
        self.session.openWithCallback(self.movieSelected, MovieSelection)
    else:
        self.session.openWithCallback(self.movieSelected, MovieSelection, Current.selection)

def movieSelected(self, service):
    if service is not None:
        if isinstance(service, eServiceReferenceDvd):
			from Screens import DVD
			self.session.open(DVD.DVDPlayer, dvd_filelist=service.getDVD())
        else:
            self.session.open(MoviePlayerExtended, service)

from Components.UsageConfig import defaultMoviePath
from Trashcan import Trashcan
class WastebasketTimer():
    def __init__(self, session):
        self.session = session
        self.recTimer = eTimer()
        self.recTimer.callback.append(self.autoDeleteAllMovies)
        self.wastebasketTimer = eTimer()
        self.wastebasketTimer.callback.append(self.autoDeleteAllMovies)
        self.startTimer()
        config.AdvancedMovieSelection.empty_wastebasket_time.addNotifier(self.startTimer, initial_call=False)
    
    def stopTimer(self):
        self.wastebasketTimer.stop()
    
    def startTimer(self, dummy=None):
        if self.wastebasketTimer.isActive():
            self.wastebasketTimer.stop()
        value = int(config.AdvancedMovieSelection.auto_empty_wastebasket.value)
        if value != -1:
            nowSec = int(time())           
            now = localtime(nowSec)
            w_h = config.AdvancedMovieSelection.empty_wastebasket_time.value[0]
            w_m = config.AdvancedMovieSelection.empty_wastebasket_time.value[1]
            dt = datetime(now.tm_year, now.tm_mon, now.tm_mday, w_h, w_m)
            if value == 1:
                nextUpdateSeconds = int(mktime(dt.timetuple()))
                if nowSec > nextUpdateSeconds:
                    dt += timedelta(value)
                    nextUpdateSeconds = int(mktime(dt.timetuple()))
            else:
                dt += timedelta(value)
                nextUpdateSeconds = int(mktime(dt.timetuple()))
            config.AdvancedMovieSelection.next_auto_empty_wastebasket.value = nextUpdateSeconds
            config.AdvancedMovieSelection.next_auto_empty_wastebasket.save()
            self.wastebasketTimer.startLongTimer(nextUpdateSeconds - nowSec)
            print "[AdvancedMovieSelection] Next wastebasket auto empty at", dt.strftime("%c")
        else:
            if self.wastebasketTimer.isActive():
                self.wastebasketTimer.stop()
            if self.recTimer.isActive():
                self.recTimer.stop()

    def configChange(self):
        if self.wastebasketTimer.isActive():
            self.wastebasketTimer.stop()
        print "[AdvancedMovieSelection] Setup values have changed"
        self.startTimer()
        
    def autoDeleteAllMovies(self):
        from Client import isAnyRecording
        remote_recordings = isAnyRecording()
        
        retryvalue = "%s minutes" % int(config.AdvancedMovieSelection.next_empty_check.value)

        if self.recTimer.isActive():
            self.recTimer.stop()

        if remote_recordings:
            print "[AdvancedMovieSelection] Start automated deleting all movies but remote recordings activ, retry at", retryvalue
            self.recTimer.start(config.AdvancedMovieSelection.next_empty_check.value * 60000)
            return
        
        if not Screens.Standby.inStandby:
            print "[AdvancedMovieSelection] Start automated deleting all movies but box not in standby, retry in", retryvalue
            self.recTimer.start(config.AdvancedMovieSelection.next_empty_check.value * 60000)
        else:
            recordings = self.session.nav.getRecordings()
            next_rec_time = -1
            if not recordings:
                next_rec_time = self.session.nav.RecordTimer.getNextRecordingTime()    
            if config.movielist.last_videodir.value == "/hdd/movie/" and recordings or (next_rec_time > 0 and (next_rec_time - time()) < 360):           
                print "[AdvancedMovieSelection] Start automated deleting all movies but recordings activ, retry at", retryvalue
                self.recTimer.start(config.AdvancedMovieSelection.next_empty_check.value * 60000)
            else:
                if self.recTimer.isActive():
                    self.recTimer.stop()
                self.list = [ ]
                
                path = config.movielist.last_videodir.value
                if not fileExists(path):
                    path = defaultMoviePath()
                    config.movielist.last_videodir.value = path
                    config.movielist.last_videodir.save()
                    
                if config.AdvancedMovieSelection.wastelist_buildtype.value == 'listMovies':
                    trash = Trashcan.listMovies(path)
                elif config.AdvancedMovieSelection.wastelist_buildtype.value == 'listAllMovies':
                    trash = Trashcan.listAllMovies(path)
                else:
                    trash = Trashcan.listAllMovies("/media")
                
                print "[AdvancedMovieSelection] Start automated deleting all movies in trash list"
                Trashcan.deleteAsynch(trash)
                config.AdvancedMovieSelection.last_auto_empty_wastebasket.value = int(time())
                config.AdvancedMovieSelection.last_auto_empty_wastebasket.save()
                self.configChange()

waste_timer = None

def autostart(reason, **kwargs):
    if reason == 0:
        session = kwargs["session"]
        if not config.AdvancedMovieSelection.ml_disable.value:
            try:
                InfoBar.movieSelected = movieSelected
                value = config.AdvancedMovieSelection.movie_launch.value
                if value == "showMovies": InfoBar.showMovies = showMovies
                elif value == "showTv": InfoBar.showTv = showMovies
                elif value == "showRadio": InfoBar.showRadio = showMovies
                elif value == "timeshiftStart": InfoBar.startTimeshift = showMovies
                global waste_timer
                waste_timer = WastebasketTimer(session)
                value = int(config.AdvancedMovieSelection.auto_empty_wastebasket.value)
                if value != -1:
                    print "[AdvancedMovieSelection] Auto empty from wastebasket enabled..."
                else:
                    waste_timer.stopTimer()
                    print "[AdvancedMovieSelection] Auto empty from wastebasket disabled..."
                from MessageServer import serverInstance
                if config.AdvancedMovieSelection.server_enabled.value:
                    serverInstance.setPort(config.AdvancedMovieSelection.server_port.value)
                    serverInstance.start()
                    serverInstance.setSearchRange(config.AdvancedMovieSelection.start_search_ip.value, config.AdvancedMovieSelection.stop_search_ip.value)
                    serverInstance.startScanForClients()
                
                from Components.Language import language
                language.addCallback(updateLocale)
                updateLocale()
            except:
                pass

def updateLocale():
    # set locale for tmdb search
    import tmdb, tvdb, AboutParser
    from Components.Language import language
    ln = language.lang[language.activeLanguage][1]
    tmdb.setLocale(ln)
    tvdb.setLocale(ln)
    AboutParser.setLocale(ln)

def pluginOpen(session, **kwargs):
    session.open(AdvancedMovieSelectionSetup)

def Setup(menuid, **kwargs):
    if menuid == "system":
        return [(_("Setup Advanced Movie Selection"), pluginOpen, "SetupAdvancedMovieSelection", None)]
    return []

def nostart(reason, **kwargs):
    print"[Advanced Movie Selection] -----> Disabled"
    pass

def Plugins(**kwargs):
    try:
        if config.AdvancedMovieSelection.debug.value:
            config.AdvancedMovieSelection.debug.value = False
            config.AdvancedMovieSelection.debug.save() 
        if not config.AdvancedMovieSelection.ml_disable.value:
            from Screens.MovieSelection import setPreferredTagEditor
            setPreferredTagEditor(TagEditor)
        if not config.AdvancedMovieSelection.ml_disable.value and config.AdvancedMovieSelection.useseekbar.value:
            from Seekbar import Seekbar
    except Exception, e:
        print e
    if not config.AdvancedMovieSelection.ml_disable.value:
        descriptors = [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=autostart)]
        descriptors.append(PluginDescriptor(where=PluginDescriptor.WHERE_MENU, fnc=Setup))
    else:
        descriptors = [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=nostart)]
        descriptors.append(PluginDescriptor(where=PluginDescriptor.WHERE_MENU, fnc=Setup))
    return descriptors
