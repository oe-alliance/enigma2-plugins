#!/usr/bin/python
# -*- coding: utf-8 -*- 
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  The plugin is developed on the basis from a lot of single plugins (thx for the code @ all)
#  Coded by cmikula & JackDaniel (c)2012
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

from LocaleInit import _
from Tools.Directories import resolveFilename, SCOPE_HDD
from Components.config import config, ConfigSubsection, ConfigText, ConfigYesNo, ConfigInteger, ConfigSelection, ConfigClock, ConfigLocations, ConfigBoolean
from Globals import printStackTrace

# configurations from enigma2 /Components/UsageConfig.py !!!don't edit default values from source!!!
config.usage.load_length_of_movies_in_moviellist = ConfigYesNo(default=True)
config.usage.on_movie_start = ConfigSelection(default="ask", choices=[("ask", _("Ask user")), ("resume", _("Resume from last position")), ("beginning", _("Start from the beginning"))])
config.usage.on_movie_stop = ConfigSelection(default="ask", choices=[("ask", _("Ask user")), ("movielist", _("Return to movie list")), ("quit", _("Return to previous service"))])
config.usage.on_movie_eof = ConfigSelection(default="ask", choices=[("ask", _("Ask user")), ("movielist", _("Return to movie list")), ("quit", _("Return to previous service")), ("pause", _("Pause movie at end")), ("standby", _("Standby")), ("shutdown", _("Shutdown"))])

config.AdvancedMovieSelection = ConfigSubsection()
config.AdvancedMovieSelection.last_selected_service = ConfigText(default="")
config.AdvancedMovieSelection.wastelist_buildtype = ConfigSelection(default="listMovies", choices=[("listMovies", _("Only current location")), ("listAllMovies", _("Current location and all subdirectories")), ("listAllMoviesMedia", _("All directorys below '/media'"))])
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
config.AdvancedMovieSelection.dateformat = ConfigSelection(default="6", choices=[("6", _("German (without Year)")), ("1", _("German (with Year)")), ("3", _("German (with Starttime)")), ("2", _("Enigma 2 default")), ("7", _("English (without Year)")), ("4", _("English (with Year)")), ("5", _("English (with Starttime)"))])
config.AdvancedMovieSelection.color1 = ConfigSelection(default="yellow", choices=[("yellow", _("Yellow")), ("blue", _("Blue")), ("red", _("Red")), ("black", _("Black")), ("green", _("Green"))])
config.AdvancedMovieSelection.color2 = ConfigSelection(default="green", choices=[("green", _("Green")), ("blue", _("Blue")), ("red", _("Red")), ("black", _("Black")), ("yellow", _("Yellow"))])
config.AdvancedMovieSelection.color3 = ConfigSelection(default="red", choices=[("red", _("Red")), ("blue", _("Blue")), ("green", _("Green")), ("black", _("Black")), ("yellow", _("Yellow"))])
config.AdvancedMovieSelection.color4 = ConfigSelection(default="grey", choices=[("grey", _("Grey")), ("red", _("Red")), ("blue", _("Blue")), ("green", _("Green")), ("black", _("Black")), ("yellow", _("Yellow")), ("orange", _("Orange")), ])
config.AdvancedMovieSelection.moviepercentseen = ConfigInteger(default=80, limits=(50, 100))
config.AdvancedMovieSelection.showfoldersinmovielist = ConfigYesNo(default=False)
config.AdvancedMovieSelection.showprogessbarinmovielist = ConfigYesNo(default=False)
config.AdvancedMovieSelection.showiconstatusinmovielist = ConfigYesNo(default=False)
config.AdvancedMovieSelection.showcolorstatusinmovielist = ConfigYesNo(default=False)
config.AdvancedMovieSelection.about = ConfigSelection(default="1", choices=[("1", " ")])
config.AdvancedMovieSelection.ml_disable = ConfigYesNo(default=False)
config.AdvancedMovieSelection.showmenu = ConfigYesNo(default=True)
config.AdvancedMovieSelection.pluginmenu_list = ConfigYesNo(default=False)
config.AdvancedMovieSelection.red = ConfigText(default="Delete", visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.green = ConfigText(default="Nothing", visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.yellow = ConfigText(default="Nothing", visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.blue = ConfigText(default="Nothing", visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark1text = ConfigText(default="Bookmark 1", visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark2text = ConfigText(default="Bookmark 2", visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark3text = ConfigText(default="Bookmark 3", visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark4text = ConfigText(default="Bookmark 4", visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark5text = ConfigText(default="Bookmark 5", visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark6text = ConfigText(default="Bookmark 6", visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark7text = ConfigText(default="Bookmark 7", visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.hometext = ConfigText(default="Home", visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.homepath = ConfigText(default="/hdd/movie/")
config.AdvancedMovieSelection.bookmark1path = ConfigText(default="/hdd/movie/")
config.AdvancedMovieSelection.bookmark2path = ConfigText(default="/hdd/movie/")
config.AdvancedMovieSelection.bookmark3path = ConfigText(default="/hdd/movie/")
config.AdvancedMovieSelection.bookmark4path = ConfigText(default="/hdd/movie/")
config.AdvancedMovieSelection.bookmark5path = ConfigText(default="/hdd/movie/")
config.AdvancedMovieSelection.bookmark6path = ConfigText(default="/hdd/movie/")
config.AdvancedMovieSelection.bookmark7path = ConfigText(default="/hdd/movie/")
config.AdvancedMovieSelection.buttoncaption = ConfigText(default="Display plugin name")
config.AdvancedMovieSelection.homeowntext = ConfigText(default=_("Homebutton"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark1owntext = ConfigText(default=_("Own text 1"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark2owntext = ConfigText(default=_("Own text 2"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark3owntext = ConfigText(default=_("Own text 3"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark4owntext = ConfigText(default=_("Own text 4"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark5owntext = ConfigText(default=_("Own text 5"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark6owntext = ConfigText(default=_("Own text 6"), visible_width=50, fixed_size=False)
config.AdvancedMovieSelection.bookmark7owntext = ConfigText(default=_("Own text 7"), visible_width=50, fixed_size=False)
launch_choices = [("None", _("No override")),
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
config.AdvancedMovieSelection.description = ConfigYesNo(default=True)
poster_sizes = (u'w92', u'w154', u'w185', u'w342', u'w500', u'original')
from MovieDB.tmdb import poster_sizes, setPosterSize
poster_choices = [
                  (poster_sizes[0], _("Thumb (92x138)")),
                  (poster_sizes[2], _("Cover (185x278)")),
                  (poster_sizes[4], _("Mid (500x750)")),
                  (poster_sizes[5], _("Original (1400x2100)"))
                  ]
config.AdvancedMovieSelection.tmdb_poster_size = ConfigSelection(default=poster_sizes[2], choices=poster_choices)
config.AdvancedMovieSelection.tmdb_poster_size.addNotifier(setPosterSize)
config.AdvancedMovieSelection.showtmdb = ConfigYesNo(default=True)
config.AdvancedMovieSelection.show_info_cover_del = ConfigYesNo(default=True)
config.AdvancedMovieSelection.show_info_del = ConfigYesNo(default=True)
config.AdvancedMovieSelection.show_cover_del = ConfigYesNo(default=True)
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
config.AdvancedMovieSelection.empty_wastebasket_min_age = ConfigInteger(default=0, limits=(0, 999))
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
config.AdvancedMovieSelection.show_diskusage = ConfigYesNo(default=False)
# TODO: remove
# config.AdvancedMovieSelection.show_dirsize_full = ConfigYesNo(default=False)
config.AdvancedMovieSelection.dirsize_digits = ConfigSelection(default="0", choices=[("0", _("0")), ("1", _("1")), ("2", _("2")), ("3", _("3"))])
config.AdvancedMovieSelection.showpercentinmovielist = ConfigYesNo(default=False)
config.AdvancedMovieSelection.filesize_digits = ConfigSelection(default="1", choices=[("0", _("0")), ("1", _("1")), ("2", _("2")), ("3", _("3"))])
config.AdvancedMovieSelection.showthetvdb = ConfigYesNo(default=False)
config.AdvancedMovieSelection.video_preview = ConfigYesNo(default=False)
config.AdvancedMovieSelection.video_preview_delay = ConfigInteger(default=1, limits=(0, 10))
config.AdvancedMovieSelection.video_preview_marker = ConfigYesNo(default=False)
config.AdvancedMovieSelection.video_preview_jump_time = ConfigInteger(default=5, limits=(1, 60))
config.AdvancedMovieSelection.video_preview_autostart = ConfigYesNo(default=True)
config.AdvancedMovieSelection.video_preview_fullscreen = ConfigYesNo(default=True)
config.AdvancedMovieSelection.epg_extension = ConfigYesNo(default=False)
config.AdvancedMovieSelection.show_set_vsr = ConfigYesNo(default=False)
config.AdvancedMovieSelection.keyboard = ConfigSelection(default="virtual_numerical", choices=[("virtual_numerical", _("Virtual and Numerical")), ("virtual", _("Virtual")), ("numerical", _("Numerical"))])
config.AdvancedMovieSelection.show_filter_by_description = ConfigYesNo(default=False)
config.AdvancedMovieSelection.show_backup_restore = ConfigYesNo(default=True)
config.AdvancedMovieSelection.cover_auto_download = ConfigYesNo(default=True)
config.AdvancedMovieSelection.version = ConfigText()
config.AdvancedMovieSelection.backup_path = ConfigText()
config.AdvancedMovieSelection.sort_functions = ConfigText()
config.AdvancedMovieSelection.show_move_copy_progress = ConfigYesNo(default=True)
config.AdvancedMovieSelection.videodirs = ConfigLocations()
config.AdvancedMovieSelection.show_location_indexing = ConfigYesNo(default=True)
config.AdvancedMovieSelection.show_videodirslocation = ConfigYesNo(default=True)
config.AdvancedMovieSelection.show_movielibrary = ConfigYesNo(default=True)
config.AdvancedMovieSelection.movielibrary_sort = ConfigInteger(default=1)
config.AdvancedMovieSelection.movielibrary_show = ConfigBoolean()
config.AdvancedMovieSelection.movielibrary_mark = ConfigYesNo(default=True)
config.AdvancedMovieSelection.movielibrary_show_mark_cnt = ConfigInteger(default=2, limits=(1, 10))
config.AdvancedMovieSelection.hide_seen_movies = ConfigYesNo(default=False)
config.AdvancedMovieSelection.qButtons = ConfigText()


class QuickButtons():
    def __init__(self):
        self.qlist = [('red', ''), ('red_long', ''), ('green', ''), ('green_long', ''), ('yellow', ''), ('yellow_long', ''), ('blue', ''), ('blue_long', '')]
        self.load()

    def getFunction(self, key):
        for button, function in self.qlist:
            if button == key:
                return function
    
    def setFunction(self, button, function):
        for index, item in enumerate(self.qlist):
            if item[0] == button:
                self.qlist[index] = (button, function)
    
    def get(self):
        return self.qlist
    
    def load(self):
        if config.AdvancedMovieSelection.qButtons.value:
            l = eval(config.AdvancedMovieSelection.qButtons.value)
            if isinstance(l, list):
                self.qlist = l
        else:
            self.updateOldVersion()
    
    def save(self):
        config.AdvancedMovieSelection.qButtons.value = str(self.qlist)
        config.AdvancedMovieSelection.qButtons.save()
        
    def updateOldVersion(self):
        try:
            print "update older config version"
            self.setFunction('red', config.AdvancedMovieSelection.red.value)
            self.setFunction('green', config.AdvancedMovieSelection.green.value)
            self.setFunction('yellow', config.AdvancedMovieSelection.yellow.value)
            self.setFunction('blue', config.AdvancedMovieSelection.blue.value)
            print self.qlist
        except:
            printStackTrace()
    

qButtons = QuickButtons()


def initializeConfig():
    pass


CONFIG_BACKUP = ("AdvancedMovieSelection", "movielist")
BACKUP_FILE_NAME = "AMS.settings.backup"


def getChanges(config_entry, changes):
    print "get changes for:", config_entry
    entry = config.content.items[config_entry]
    for item in entry.dict():
        conf = entry.__getattr__(item)
        if conf.default != conf.value: 
            txt = "config.%s.%s=%s" % (config_entry, item, conf.saved_value)
            print txt
            changes.append(txt)


def createBackup(path="/media/hdd/"):
    changes = []
    for item in CONFIG_BACKUP:
        getChanges(item, changes)

    import os
    file_name = os.path.join(path, BACKUP_FILE_NAME)
    print "create backup", file_name
    try: 
        backup = open(file_name, 'wb')
        backup.write("\n".join(changes))
        backup.close()
    except:
        printStackTrace()
        return
    return file_name


def loadBackup(file_name):
    print "load backup", file_name 
    backup = open(file_name, 'rb')
    for line in backup.readlines():
        try:
            config_entry = line.split(".")[1]
            config_item = line.split(".")[2].split("=")[0]
            value = line.split("=")[-1].strip()
            print config_entry, config_item, value
            entry = config.content.items[config_entry]
            conf = entry.__getattr__(config_item)
            conf.saved_value = conf._value = value
            conf.load()
        except:
            printStackTrace()
    backup.close()
