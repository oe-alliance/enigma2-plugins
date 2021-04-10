#!/usr/bin/python
# -*- coding: utf-8 -*- 
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  The plugin is developed on the basis from a lot of single plugins (thx for the code @ all)
#  Coded by JackDaniel & cmikula(c)2011
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
from enigma import ePoint
from Screens.Screen import Screen
from .RecordPaths import RecordPathsSettings
from .About import AdvancedMovieSelectionAbout
from Components.Pixmap import Pixmap
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor
from Components.config import config, getConfigListEntry, configfile, ConfigSelection
from Components.Sources.StaticText import StaticText
from Components.Button import Button
from Components import ConfigList as eConfigList
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.LocationBox import MovieLocationBox
from Components.UsageConfig import preferredPath
from Screens.MessageBox import MessageBox
from .MessageBoxEx import MessageBox as MessageBoxEx
from Components.Sources.Boolean import Boolean
from Components.Sources.List import List
from Components.ActionMap import ActionMap, NumberActionMap
from enigma import getDesktop, quitMainloop
from .ClientSetup import ClientSetup
from .Source.Globals import pluginPresent, SkinTools
from .Source.Config import qButtons


class ConfigList(eConfigList.ConfigList):
    def __init__(self, list, session=None):
        eConfigList.ConfigList.__init__(self, list, session=session)
    
    def selectionChanged(self):
        if isinstance(self.current, tuple) and len(self.current) >= 2:
            self.current[1].onDeselect(self.session)
        self.current = self.getCurrent()
        if isinstance(self.current, tuple) and len(self.current) >= 2:
            self.current[1].onSelect(self.session)
        else:
            return
        for x in self.onSelectionChanged:
            x()

    def preWidgetRemove(self, instance):
        if isinstance(self.current, tuple) and len(self.current) >= 2:
            self.current[1].onDeselect(self.session)
        instance.selectionChanged.get().remove(self.selectionChanged)
        instance.setContent(None)


class ConfigListScreen(eConfigList.ConfigListScreen):
    def __init__(self, list, session=None, on_change=None):
        self["config_actions"] = NumberActionMap(["SetupActions", "InputAsciiActions", "KeyboardInputActions"],
        {
            "gotAsciiCode": self.keyGotAscii,
            "ok": self.keyOK,
            "left": self.keyLeft,
            "right": self.keyRight,
            "home": self.keyHome,
            "end": self.keyEnd,
            "deleteForward": self.keyDelete,
            "deleteBackward": self.keyBackspace,
            "toggleOverwrite": self.keyToggleOW,
            "1": self.keyNumberGlobal,
            "2": self.keyNumberGlobal,
            "3": self.keyNumberGlobal,
            "4": self.keyNumberGlobal,
            "5": self.keyNumberGlobal,
            "6": self.keyNumberGlobal,
            "7": self.keyNumberGlobal,
            "8": self.keyNumberGlobal,
            "9": self.keyNumberGlobal,
            "0": self.keyNumberGlobal
        }, -1) # to prevent left/right overriding the listbox

        self["VirtualKB"] = ActionMap(["VirtualKeyboardActions"],
        {
            "showVirtualKeyboard": self.KeyText,
        }, -2)
        self["VirtualKB"].setEnabled(False)
        
        self["config"] = ConfigList(list, session=session)
        
        if on_change is not None:
            self.__changed = on_change
        else:
            self.__changed = lambda: None
        
        if not self.handleInputHelpers in self["config"].onSelectionChanged:
            self["config"].onSelectionChanged.append(self.handleInputHelpers)


from .Source.Globals import SkinResolutionHelper


class BackupRestore(ConfigListScreen, Screen, SkinResolutionHelper):
    def __init__(self, session, csel=None):
        Screen.__init__(self, session)
        SkinResolutionHelper.__init__(self)
        self.csel = csel
        self["setupActions"] = ActionMap(["OkCancelActions", "ColorActions"],
        {
            "ok": self.okPressed,
            "cancel": self.close,
            "red": self.close,
            "green": self.openFilebrowser,
            "yellow": self.backup
        }, -2)
        self.list = []
        self.backup_dirs = config.movielist.videodirs.value[:]
        default = config.usage.default_path.value
        if default not in self.backup_dirs:
            self.backup_dirs.append(default)
        if config.AdvancedMovieSelection.backup_path.value:
            default = config.AdvancedMovieSelection.backup_path.value
            if default not in self.backup_dirs:
                print("path from config:", default)
                self.backup_dirs.append(default)
        print("backup dirs:", self.backup_dirs)
        self.backup_config_path = ConfigSelection(default=default, choices=self.backup_dirs)
        self.list.append(getConfigListEntry(_("Backup directory path:"), self.backup_config_path))
        ConfigListScreen.__init__(self, self.list, session=self.session)
        self["key_red"] = StaticText(_("Close"))
        self["key_green"] = StaticText(_("Restore settings"))
        self["key_yellow"] = StaticText(_("Backup settings"))
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(_("Backup/Restore Advanced Movie Selection settings"))
    
    def getBackupPath(self):
        return self.backup_config_path.getValue()
    
    def backup(self):
        from .Source.Config import createBackup
        path = self.getBackupPath()
        result = createBackup(path)
        if result:
            self.session.open(MessageBox, _("Settings backup successfully created in %s.") % (result), type=MessageBox.TYPE_INFO)
            self.close()
        else:
            self.session.open(MessageBox, _("Error creating settings backup!"), type=MessageBox.TYPE_ERROR)
    
    def openFilebrowser(self):
        from .FileBrowser import FileBrowser
        path = self.getBackupPath()
        self.session.openWithCallback(self.restoreCallback, FileBrowser, path)

    def restoreCallback(self, answer):
        print(answer)
        if answer:
            from .Source.Config import loadBackup
            loadBackup(answer)
            self.session.open(MessageBox, _("Some settings changes require close/reopen the movielist to take effect."), type=MessageBox.TYPE_INFO)
            self.close()
            
    def okPressed(self):
        from Screens.LocationBox import LocationBox
        path = self.getBackupPath()
        from Components.config import ConfigLocations
        locations = ConfigLocations(self.backup_dirs)
        self.session.openWithCallback(self.dirnameSelected, LocationBox, _("Please select backup path here:"), currDir=path, bookmarks=locations)
    
    def dirnameSelected(self, answer):
        if not answer:
            return
        print("backup path:", answer)
        if answer not in self.backup_dirs:
            self.backup_dirs.append(answer)
        self.backup_config_path.setChoices(self.backup_dirs, default=answer)
        self.backup_config_path.setValue(answer)
        config.AdvancedMovieSelection.backup_path.value = answer
        config.AdvancedMovieSelection.backup_path.save()


class AdvancedMovieSelectionSetup(ConfigListScreen, Screen):
    def __init__(self, session, csel=None):
        Screen.__init__(self, session)
        self.csel = csel
        self.skinName = SkinTools.appendResolution("AdvancedMovieSelectionSetup")
        self.bouquet_length = 13
        self.needsRestartFlag = False
        self.needsE2restartFlag = False
        self.needsReopenFlag = False
        self["setupActions"] = ActionMap(["ColorActions", "OkCancelActions", "MenuActions", "EPGSelectActions"],
        {
            "ok": self.keySave,
            "cancel": self.keyCancel,
            "red": self.keyCancel,
            "green": self.keySave,
            "yellow": self.buttonsetup,
            "blue": self.RecPathSettings,
            "info": self.about,
            "menu": self.clientsetup,
            "nextBouquet": self.nextBouquet,
            "prevBouquet": self.prevBouquet,
        }, -2)
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session)
        if not self.showHelp in self["config"].onSelectionChanged:
            self["config"].onSelectionChanged.append(self.showHelp)
        self.createSetup()
        self["key_red"] = StaticText(_("Close"))
        self["key_green"] = StaticText(_("Save"))
        self["key_yellow"] = StaticText(_("Color key settings"))
        self["key_blue"] = StaticText(_("Default paths"))
        self["help"] = StaticText("")
        self["Trailertxt"] = StaticText("")
        self["TMDbtxt"] = StaticText("")
        self["IMDbtxt"] = StaticText("")
        self["OFDbtxt"] = StaticText("")
        self["MenuIcon"] = Pixmap()
        self.onShown.append(self.setWindowTitle)
        self.onLayoutFinish.append(self.saveListsize)
        self.pluginsavailable()
        self.onHide.append(self.updateSettings)
        self.setMenubutton()       

    def setMenubutton(self):
        if config.AdvancedMovieSelection.use_wastebasket.value:
            self["MenuIcon"].show()
        else:
            self["MenuIcon"].hide()

    def clientsetup(self):
        if config.AdvancedMovieSelection.use_wastebasket.value:
            self.session.open(ClientSetup)

    def updateSettings(self):
        if self.csel:
            self.csel["list"].updateSettings()
            self.csel["list"].updateHotplugDevices()
            self.csel.reloadList()
        
    def saveListsize(self):
        listsize = self["config"].instance.size()
        self.listWidth = listsize.width()
        self.listHeight = listsize.height()
        self.bouquet_length = int(self.listHeight / 25)

    def nextBouquet(self):
        self["config"].setCurrentIndex(max(self["config"].getCurrentIndex() - self.bouquet_length, 0))

    def prevBouquet(self):
        self["config"].setCurrentIndex(min(self["config"].getCurrentIndex() + self.bouquet_length, len(self.list) - 1))

    def setWindowTitle(self):
        self.setTitle(_("Advanced Movie Selection Setup"))

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.checkListentrys()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.checkListentrys()

    def checkListentrys(self):
        needRefresh = False          
        if config.AdvancedMovieSelection.show_dirsize.isChanged():
            config.AdvancedMovieSelection.show_dirsize.save()
            needRefresh = True
        if config.AdvancedMovieSelection.show_date_shortdesc.isChanged():
            config.AdvancedMovieSelection.show_date_shortdesc.save()
            needRefresh = True
        if config.AdvancedMovieSelection.use_original_movieplayer_summary.isChanged():
            config.AdvancedMovieSelection.use_original_movieplayer_summary.save()
            needRefresh = True
        if not config.AdvancedMovieSelection.use_wastebasket.value:
            config.AdvancedMovieSelection.auto_empty_wastebasket.setValue("-1")
            config.AdvancedMovieSelection.auto_empty_wastebasket.save()
        if config.AdvancedMovieSelection.auto_empty_wastebasket.isChanged():
            config.AdvancedMovieSelection.auto_empty_wastebasket.save()
            needRefresh = True
        if config.AdvancedMovieSelection.show_picon.isChanged():
            config.AdvancedMovieSelection.show_picon.save()
            needRefresh = True
        if config.usage.load_length_of_movies_in_moviellist.isChanged():
            config.usage.load_length_of_movies_in_moviellist.save()
            needRefresh = True
        if config.AdvancedMovieSelection.showpreview.isChanged():
            config.AdvancedMovieSelection.showpreview.save()
            self.needsReopenFlag = True
            needRefresh = True
        if config.AdvancedMovieSelection.showcolorstatusinmovielist.isChanged():
            config.AdvancedMovieSelection.showcolorstatusinmovielist.save()
            needRefresh = True
        if config.AdvancedMovieSelection.exitkey.isChanged():
            config.AdvancedMovieSelection.exitkey.save()
            needRefresh = True
        if config.AdvancedMovieSelection.useseekbar.isChanged():
            config.AdvancedMovieSelection.useseekbar.save()
            self.needsRestartFlag = True
            needRefresh = True
        if config.AdvancedMovieSelection.video_preview.isChanged():
            config.AdvancedMovieSelection.video_preview.save()
            needRefresh = True
        if config.AdvancedMovieSelection.video_preview.isChanged(): 
            if not config.AdvancedMovieSelection.video_preview_fullscreen.value:
                config.AdvancedMovieSelection.video_preview.save()
                needRefresh = True
            else:
                config.AdvancedMovieSelection.video_preview.save()
                needRefresh = True
                self.needsReopenFlag = True 
        if config.AdvancedMovieSelection.minitv.isChanged():
            config.AdvancedMovieSelection.minitv.save()
            if not config.AdvancedMovieSelection.minitv.value:
                config.AdvancedMovieSelection.video_preview.setValue(False)
                config.AdvancedMovieSelection.video_preview.save()
            needRefresh = True
        if config.AdvancedMovieSelection.video_preview_autostart.isChanged():
            config.AdvancedMovieSelection.video_preview_autostart.save()
            needRefresh = True
        if config.AdvancedMovieSelection.video_preview_fullscreen.isChanged():
            config.AdvancedMovieSelection.video_preview_fullscreen.save()
            self.needsReopenFlag = True
        if config.AdvancedMovieSelection.video_preview.value and config.AdvancedMovieSelection.video_preview_fullscreen.isChanged():
            config.AdvancedMovieSelection.video_preview.save()
            config.AdvancedMovieSelection.video_preview_fullscreen.save()
            self.needsReopenFlag = True
        
        if needRefresh:
            self.createSetup()

        if config.AdvancedMovieSelection.use_wastebasket.isChanged():
            config.AdvancedMovieSelection.use_wastebasket.save()
            if config.AdvancedMovieSelection.use_wastebasket.value:
                self["MenuIcon"].show()
            else:
                self["MenuIcon"].hide()
            self.createSetup()
        if config.AdvancedMovieSelection.wastelist_buildtype.isChanged():
            config.AdvancedMovieSelection.wastelist_buildtype.save()
            if config.AdvancedMovieSelection.use_wastebasket.value:
                self["MenuIcon"].show()
            else:
                self["MenuIcon"].hide()            
        if config.AdvancedMovieSelection.debug.isChanged():
            config.AdvancedMovieSelection.debug.save()
            from .Source.Debug import Debug
            if config.AdvancedMovieSelection.debug.value:
                Debug.enable("/tmp/enigma2_stdout.log")
            else:
                Debug.disable()

    def createSetup(self):
        self.list = []
        self.list.append(getConfigListEntry(_("Disable Advanced Movie Selection:"), config.AdvancedMovieSelection.ml_disable, _("Switch on/off the Advanced Movie Selection.")))
        self.list.append(getConfigListEntry(_("Start Advanced Movie Selection with:"), config.AdvancedMovieSelection.movie_launch, _("Select Start button for the Advanced Movie Selection.")))
        self.list.append(getConfigListEntry(_("Start on last movie location:"), config.AdvancedMovieSelection.startdir, _("Opens the film list on the last used location.")))
        self.list.append(getConfigListEntry(_("Start on first position in movielist:"), config.AdvancedMovieSelection.startonfirst, _("Always show selection in the first position in the movie list.")))
        self.list.append(getConfigListEntry(_("Show bookmarks in movielist:"), config.AdvancedMovieSelection.show_bookmarks, _("When enabled all created bookmarks appear in the movie list.")))
        self.list.append(getConfigListEntry(_("Show hotplug devices:"), config.AdvancedMovieSelection.hotplug, _("Enable this option to use USB-Devices.")))
        self.list.append(getConfigListEntry(_("Show plugin config in extensions menu from movielist:"), config.AdvancedMovieSelection.showmenu, _("Displays the Settings option in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show path selection for movie library in extensions menu:"), config.AdvancedMovieSelection.show_location_indexing, _("Here you can select which folders to include in the movie library creation.")))
        self.list.append(getConfigListEntry(_("Show movie library symbol in movielist:"), config.AdvancedMovieSelection.show_movielibrary, _("If enabled the movie library symbol is shown in movie list.")))
        self.list.append(getConfigListEntry(_("Show path marker within movie library movies:"), config.AdvancedMovieSelection.show_videodirslocation, _("If enabled all movies in movie library will be shown with path marker and will be sorted below them.")))
        self.list.append(getConfigListEntry(_("Use movie library path selection as marker within movies in library:"), config.AdvancedMovieSelection.movielibrary_mark, _("If enabled only the movie library path selections will be used as marker otherwise each sub directory will be shown as path marker in movie library view.")))
        self.list.append(getConfigListEntry(_("Minimum movie count to show path marker in movie library view:"), config.AdvancedMovieSelection.movielibrary_show_mark_cnt, _("The minimum selected number of movies must be in one directory to show the path marker in movie library view.")))
        self.list.append(getConfigListEntry(_("Show disk usage in description:"), config.AdvancedMovieSelection.show_diskusage, _("Displays the disk usage in the description. (Leave it disabled if you have performance problems at the start of the movie list)")))
        self.list.append(getConfigListEntry(_("Show directory size in movie list:"), config.AdvancedMovieSelection.show_dirsize, _("Displays the size from directories in movie list.")))
        if config.AdvancedMovieSelection.show_dirsize.value:
            self.list.append(getConfigListEntry(_("Show decimal points:"), config.AdvancedMovieSelection.dirsize_digits, _("Here you can choose how many decimal points for the directory size in the movie list will be displayed.")))
            # TODO: remove
            # self.list.append(getConfigListEntry(_("Show full depth of directories:"), config.AdvancedMovieSelection.show_dirsize_full, _("Displays the full size of all sub directories of directory size.")))
        self.list.append(getConfigListEntry(_("Load Length of Movies in Movielist:"), config.usage.load_length_of_movies_in_moviellist, _("This option is for many of the functions from the Advanced Movie Selection necessary. If this option is disabled are many functions not available.")))
        if config.usage.load_length_of_movies_in_moviellist.value:
            self.list.append(getConfigListEntry(_("Show list options in extensions menu from movielist:"), config.AdvancedMovieSelection.showextras, _("Displays the various list view options in the menu at the movie list (Progressbar,View folders...).")))
            self.list.append(getConfigListEntry(_("Show mark movie in extensions menu from movielist:"), config.AdvancedMovieSelection.showmark, _("Displays mark movie as seen/unseen in the menu at the movie list.")))
            self.list.append(getConfigListEntry(_("Mark movie as seen at position (in percent):"), config.AdvancedMovieSelection.moviepercentseen, _("With this option you can assign as when a film is marked as seen.")))
        self.list.append(getConfigListEntry(_("Show movie plugins in extensions menu from movielist:"), config.AdvancedMovieSelection.pluginmenu_list, _("Displays E2 movie list extensions in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show color key setup in extensions menu from movielist:"), config.AdvancedMovieSelection.showcolorkey, _("Displays color key setup option in the menu at the movie list.")))        
        self.list.append(getConfigListEntry(_("Show sort options in extensions menu from movielist:"), config.AdvancedMovieSelection.showsort, _("Displays sorting function in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show list styles in extensions menu from movielist:"), config.AdvancedMovieSelection.showliststyle, _("Displays various lists typs in the menu at the movie list (Minimal,Compact...).")))        
        self.list.append(getConfigListEntry(_("Show delete option in extensions menu from movielist:"), config.AdvancedMovieSelection.showdelete, _("Displays the movie delete function in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show move/copy option in extensions menu from movielist:"), config.AdvancedMovieSelection.showmove, _("Displays the movie move/copy function in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show move/copy progress on begin/end:"), config.AdvancedMovieSelection.show_move_copy_progress, _("Show the movie move/copy progress on begin and show notification on end of move/copy action.")))
        self.list.append(getConfigListEntry(_("Show movie search in extensions menu from movielist:"), config.AdvancedMovieSelection.showsearch, _("Displays the movie search function in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show covers in movielist:"), config.AdvancedMovieSelection.showpreview, _("Displays the cover in the movie list."))) 
        if config.AdvancedMovieSelection.showpreview.value:
            self.list.append(getConfigListEntry(_("Set coversize:"), config.AdvancedMovieSelection.tmdb_poster_size, _("Here you can determine the coverfile size for the download/save.")))
            self.list.append(getConfigListEntry(_("Download cover from TMDB after timer is finished:"), config.AdvancedMovieSelection.cover_auto_download, _("If this function is enabled the cover is automatically downloaded from TMDB after timer is finished.")))
            self.list.append(getConfigListEntry(_("Show D/L and store info/cover in movielist extensions menu:"), config.AdvancedMovieSelection.showcoveroptions, _("Displays movie info/cover options in the menu at the movie list.")))
            self.list.append(getConfigListEntry(_("Show D/L and store ALL info/cover in movielist extensions menu:"), config.AdvancedMovieSelection.showcoveroptions2, _("Displays download and save movie info/cover for all movies options in the menu at the movie list.")))
            self.list.append(getConfigListEntry(_("Show delete info and cover in extensions menu from movielist:"), config.AdvancedMovieSelection.show_info_cover_del, _("Displays delete movie info and cover function in the menu at the movie list.")))
            self.list.append(getConfigListEntry(_("Show delete cover in extensions menu from movielist:"), config.AdvancedMovieSelection.show_cover_del, _("Displays delete cover function in the menu at the movie list.")))
            self.list.append(getConfigListEntry(_("Show delete movie info in extensions menu from movielist:"), config.AdvancedMovieSelection.show_info_del, _("Displays delete movie info function in the menu at the movie list.")))
            self.list.append(getConfigListEntry(_("Show Provider Logo:"), config.AdvancedMovieSelection.show_picon, _("Displays the Provider Logo when no Cover available.")))
            self.list.append(getConfigListEntry(_("Show update genre in extensions menu from movielist:"), config.AdvancedMovieSelection.show_update_genre, _("Displays Update all genre in meta from eit options in the menu at the movie list.")))     
        if config.AdvancedMovieSelection.show_picon.value:
            self.list.append(getConfigListEntry(_("Show Provider Logo in original size:"), config.AdvancedMovieSelection.piconsize, _("Displays the Provider Logo in original size. Otherwise, the provider logo be displayed zoomed up to cover size.")))    
            self.list.append(getConfigListEntry(_("Provider Logo path:"), config.AdvancedMovieSelection.piconpath, _("Where to look for the provider logos? (Default is /usr/share/enigma2/picon)"))) 
        self.list.append(getConfigListEntry(_("Show rename in extensions menu from movielist:"), config.AdvancedMovieSelection.showrename, _("Displays rename function in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show TMDb Info & D/L in extensions menu from movielist:"), config.AdvancedMovieSelection.showtmdb, _("Displays TMDb Info & D/L in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show TheTVDB Info & D/L in extensions menu from movielist:"), config.AdvancedMovieSelection.showthetvdb, _("Displays TheTVDB Info & D/L in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Jump to first mark when starts playing movie:"), config.AdvancedMovieSelection.jump_first_mark, _("If this option is activated automatically when a movie does not start from the last position, the movie starts at the first marker.")))
        self.list.append(getConfigListEntry(_("Show movie tags in extensions menu from movielist:"), config.AdvancedMovieSelection.showmovietagsinmenu, _("Displays movie tags function in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show filter by tags in extensions menu from movielist:"), config.AdvancedMovieSelection.showfiltertags, _("Displays filter by tags function in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show search trailer on web in extensions menu from movielist:"), config.AdvancedMovieSelection.showtrailer, _("Displays search trailer on web function in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show Set VSR in extensions menu from movielist:"), config.AdvancedMovieSelection.show_set_vsr, _("Displays set VSR function in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show Filter by description in extensions menu from movielist:"), config.AdvancedMovieSelection.show_filter_by_description, _("Displays the Filter by description function in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show backup/restore in extensions menu from movielist:"), config.AdvancedMovieSelection.show_backup_restore, _("Displays the backup/restore function in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Ask before delete:"), config.AdvancedMovieSelection.askdelete, _("With this option you can turn on/off the security question before delete a movie.")))
        if pluginPresent.IMDb and pluginPresent.OFDb and pluginPresent.TMDb:
            self.list.append(getConfigListEntry(_("INFO button function:"), config.AdvancedMovieSelection.Eventinfotyp, _("With this option you can assign what function should have the info button. The selection depends on the installed plugins.")))
        if pluginPresent.IMDb and not pluginPresent.OFDb and not pluginPresent.TMDb:
            self.list.append(getConfigListEntry(_("INFO button function:"), config.AdvancedMovieSelection.Eventinfotyp2, _("With this option you can assign what function should have the info button. The selection depends on the installed plugins.")))
        if pluginPresent.OFDb and not pluginPresent.TMDb and not pluginPresent.IMDb:
            self.list.append(getConfigListEntry(_("INFO button function:"), config.AdvancedMovieSelection.Eventinfotyp3, _("With this option you can assign what function should have the info button. The selection depends on the installed plugins.")))
        if pluginPresent.TMDb and not pluginPresent.OFDb and not pluginPresent.IMDb:
            self.list.append(getConfigListEntry(_("INFO button function:"), config.AdvancedMovieSelection.Eventinfotyp4, _("With this option you can assign what function should have the info button. The selection depends on the installed plugins.")))
        if pluginPresent.TMDb and not pluginPresent.OFDb and pluginPresent.IMDb:
            self.list.append(getConfigListEntry(_("INFO button function:"), config.AdvancedMovieSelection.Eventinfotyp5, _("With this option you can assign what function should have the info button. The selection depends on the installed plugins.")))
        if pluginPresent.TMDb and pluginPresent.OFDb and not pluginPresent.IMDb:
            self.list.append(getConfigListEntry(_("INFO button function:"), config.AdvancedMovieSelection.Eventinfotyp6, _("With this option you can assign what function should have the info button. The selection depends on the installed plugins.")))
        if not pluginPresent.TMDb and pluginPresent.OFDb and pluginPresent.IMDb:
            self.list.append(getConfigListEntry(_("INFO button function:"), config.AdvancedMovieSelection.Eventinfotyp7, _("With this option you can assign what function should have the info button. The selection depends on the installed plugins.")))
        self.list.append(getConfigListEntry(_("Behavior when a movie is started:"), config.usage.on_movie_start, _("With this option you can assign what should happen when a movie start.")))
        self.list.append(getConfigListEntry(_("Behavior when a movie is stopped:"), config.usage.on_movie_stop, _("With this option you can assign what should happen when a movie stop.")))
        self.list.append(getConfigListEntry(_("Behavior when a movie reaches the end:"), config.usage.on_movie_eof, _("With this option you can assign what should happen when the end of the films was achieved.")))
        self.list.append(getConfigListEntry(_("Show Moviebar position setup in extensions menu from movielist:"), config.AdvancedMovieSelection.show_infobar_position, _("Displays the moviebar position setup function in the menu at the movie list.")))
        if config.AdvancedMovieSelection.showcolorstatusinmovielist.value:
            self.list.append(getConfigListEntry(_("Color for not ready seen movies:"), config.AdvancedMovieSelection.color1, _("With this option you can assign what color should displayed for not ready seen movies in movie list.")))
            self.list.append(getConfigListEntry(_("Color for ready seen movies:"), config.AdvancedMovieSelection.color2, _("With this option you can assign what color should displayed for ready seen movies in movie list.")))
            self.list.append(getConfigListEntry(_("Color for recording movies:"), config.AdvancedMovieSelection.color3, _("With this option you can assign what color should displayed for recording movies in movie list.")))
            self.list.append(getConfigListEntry(_("Color for multiple selection:"), config.AdvancedMovieSelection.color4, _("With this option you can assign what color should displayed for multiple selection in movie list.")))
        self.list.append(getConfigListEntry(_("Assign the date format for movielist:"), config.AdvancedMovieSelection.dateformat, _("With this option you can assign the date format in movie list (7 different sizes are available).")))
        if config.AdvancedMovieSelection.showfoldersinmovielist.value:
            self.list.append(getConfigListEntry(_("Show new recordings icon:"), config.AdvancedMovieSelection.shownew, _("With this option you can display a icon for new recordings.")))
        self.list.append(getConfigListEntry(_("Show Mini TV:"), config.AdvancedMovieSelection.minitv, _("With this option you can switch on/off the Mini TV in the movie list.")))
        self.list.append(getConfigListEntry(_("Use folder name for display covers:"), config.AdvancedMovieSelection.usefoldername, _("With this option you can use the foldername instead of folder.jpg to display covers in folders.")))
        self.list.append(getConfigListEntry(_("Close with EXIT key:"), config.AdvancedMovieSelection.exitkey, _("If this option is enabled you can stop play a movie with the EXIT button, and the Advanced Movie Selection plugin will also be closed immediately (if the next option is disabled).")))
        if config.AdvancedMovieSelection.exitkey.value:
            self.list.append(getConfigListEntry(_("Use behavior when a movie is stopped:"), config.AdvancedMovieSelection.exitprompt, _("If this option is activated the behavior when stop a film also will used when you use the EXIT button.")))
        self.list.append(getConfigListEntry(_("Show info messages:"), config.AdvancedMovieSelection.showinfo, _("If this option is activated will be displayed different info message. This should help with the operation of the extension.")))
        self.list.append(getConfigListEntry(_("Use alternative jump function:"), config.AdvancedMovieSelection.useseekbar, _("If this option is activated more jump functions ar available. ATTENTION: Enigma 2 restart is necessary!")))
        if config.AdvancedMovieSelection.useseekbar.value:
            if config.AdvancedMovieSelection.useseekbar.value and not pluginPresent.pipzap:
                self.list.append(getConfigListEntry(_("Change function from left/right buttons:"), config.AdvancedMovieSelection.overwrite_left_right, _("If this option is activated the function of the left/right arrow buttons will changed. Normal you can use the buttons also for winding, if is changed you have quick access to the new jump function. ATTENTION: Enigma 2 restart is necessary!")))
            self.list.append(getConfigListEntry(_("Manual jump sensibility:"), config.AdvancedMovieSelection.sensibility, _("Here you can adjust the manually jump length relative to the film length in percent.")))
        self.list.append(getConfigListEntry(_("Use wastebasket:"), config.AdvancedMovieSelection.use_wastebasket, _("If this option is activated the movie will not be deleted but moved into the wastebasket.")))
        if config.AdvancedMovieSelection.use_wastebasket.value:
            self.list.append(getConfigListEntry(_("Show Wastebasket in extensions menu from movielist:"), config.AdvancedMovieSelection.show_wastebasket, _("Displays wastebasket function in the menu at the movie list.")))
            self.list.append(getConfigListEntry(_("Show Clientbox setup in movielist:"), config.AdvancedMovieSelection.show_remote_setup, _("Displays Clientbox setup function in the menu at the movie list.")))
            self.list.append(getConfigListEntry(_("Wastebasket file(s):"), config.AdvancedMovieSelection.wastelist_buildtype, _("Here you can select which files to Wastebasket are displayed. ATTENTION: All directorys below '/media' will take very long until the list is displayed!")))
            self.list.append(getConfigListEntry(_("Show decimal points:"), config.AdvancedMovieSelection.filesize_digits, _("Here you can choose how many decimal points for the file size in the wastebasket will be displayed.")))
            self.list.append(getConfigListEntry(_("Server enabled:"), config.AdvancedMovieSelection.server_enabled, _("If you enable this feature, all remote functions are enabled.")))
            self.list.append(getConfigListEntry(_("Auto empty wastebasket:"), config.AdvancedMovieSelection.auto_empty_wastebasket, _("If you enable this function the wastebasket will be emptied automatically at the set time.")))
            if not int(config.AdvancedMovieSelection.auto_empty_wastebasket.value) == -1:
                self.list.append(getConfigListEntry(_("Auto empty wastebasket time:"), config.AdvancedMovieSelection.empty_wastebasket_time, _("Here you can define when to empty the wastebasket.")))
                self.list.append(getConfigListEntry(_("Check again in x minutes:"), config.AdvancedMovieSelection.next_empty_check, _("If recordings are active again after the set time is trying to empty the wastebasket.")))
                self.list.append(getConfigListEntry(_("Wastebasket retention period (days):"), config.AdvancedMovieSelection.empty_wastebasket_min_age, _("Defines how long files need to dwell in the wastebasket before auto empty will consider to remove them (0 means no retention).")))
        self.list.append(getConfigListEntry(_("Start at the beginning depends on end (in Minutes):"), config.AdvancedMovieSelection.stop_before_end_time, _("Here you can set off when a movie to play automatically from the beginning when you start again (On settings=0, functions is disabled).")))
        self.list.append(getConfigListEntry(_("Use activ Skin LCD/OLED representation:"), config.AdvancedMovieSelection.use_original_movieplayer_summary, _("If you enable this function, the display summary from aktiv skin will be used.")))
        if config.AdvancedMovieSelection.use_original_movieplayer_summary.value:
            self.list.append(getConfigListEntry(_("Show date:"), config.AdvancedMovieSelection.show_date_shortdesc, _("If this option is activated the date will be displayed on the lcd/oled when no short description is available.")))
            if config.AdvancedMovieSelection.show_date_shortdesc.value:
                self.list.append(getConfigListEntry(_("Use date from timestamp:"), config.AdvancedMovieSelection.show_begintime, _("If this option is activated the date from the file create instead today's date will be displayed on the lcd/oled when no short description is available.")))
        if config.AdvancedMovieSelection.minitv.value:
            self.list.append(getConfigListEntry(_("Use video preview:"), config.AdvancedMovieSelection.video_preview, _("If you enable this function, selected movie in movielist will bring you a preview.")))
        if config.AdvancedMovieSelection.minitv.value and config.AdvancedMovieSelection.video_preview.value:
            getSkin = getDesktop(0).size().width()
            if getSkin >= 1024:
                self.list.append(getConfigListEntry(_("Show video preview in fullscreen:"), config.AdvancedMovieSelection.video_preview_fullscreen, _("If you enable this function, the video preview function will display as full screen in skin.")))
            self.list.append(getConfigListEntry(_("Video preview autostart:"), config.AdvancedMovieSelection.video_preview_autostart, _("If you enable this feature, the movie preview starts automatically after the delay with a change in the movie list.")))
            if config.AdvancedMovieSelection.video_preview_autostart.value:
                self.list.append(getConfigListEntry(_("Video preview delay:"), config.AdvancedMovieSelection.video_preview_delay, _("Setup the delay in seconds to start the video preview.")))
            self.list.append(getConfigListEntry(_("Use last stop mark:"), config.AdvancedMovieSelection.video_preview_marker, _("Preview will start on last stop marker.")))
            self.list.append(getConfigListEntry(_("Video preview jump time (in minutes):"), config.AdvancedMovieSelection.video_preview_jump_time, _("Here you can set the jump time for the movie preview (< > buttons or bouquet +/- buttons).")))
        self.list.append(getConfigListEntry(_("Select keyboard:"), config.AdvancedMovieSelection.keyboard, _("You can select yout prefered keyboard (Virtual, Numerical or both).")))
        self.list.append(getConfigListEntry(_("Show recorded movies in epg:"), config.AdvancedMovieSelection.epg_extension, _("If you enable this function, your recorded movies will be marked in epg list.")))
        self.list.append(getConfigListEntry(_("Enable Enigma2 debug:"), config.AdvancedMovieSelection.debug, _("If you enable this function, all standard output from enigma will be stored to /tmp folder.")))
        self["config"].setList(self.list)

    def showHelp(self):
        current = self["config"].getCurrent()
        if len(current) > 2 and current[2] is not None:
            self["help"].setText(current[2])
        else:
            self["help"].setText(_("No Helptext available!"))
        
    def pluginsavailable(self):
        if pluginPresent.IMDb:
            self["IMDbtxt"].setText(_("IMDb plugin installed. Assign function to info button is possible."))
        else:
            self["IMDbtxt"].setText(_("IMDb plugin NOT installed. Assign function to info button is NOT possible."))
        if pluginPresent.OFDb:
            self["OFDbtxt"].setText(_("OFDb plugin installed. Assign function to info button is possible."))
        else:
            self["OFDbtxt"].setText(_("OFDb plugin NOT installed. Assign function to info button is NOT possible."))
        if pluginPresent.TMDb:
            self["TMDbtxt"].setText(_("TMDb plugin installed. Assign function to info button is possible."))
        else:
            self["TMDbtxt"].setText(_("TMDb plugin NOT installed. Assign function to info button is NOT possible.")) 
        if pluginPresent.YTTrailer:
            self["Trailertxt"].setText(_("YTTrailer plugin installed. Search for trailers on the Web is possible."))
        else:
            self["Trailertxt"].setText(_("YTTrailer plugin NOT installed. Search for trailers on the Web is NOT possible."))           

    def cancelConfirm(self, result):
        if not result:
            return
        for x in self["config"].list:
            x[1].cancel()
        self.close()

    def keyCancel(self):
        if self["config"].isChanged():
            self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
        else:
            self.close()

    def keySave(self):
        from .Wastebasket import configChange
        configChange()
        if not config.AdvancedMovieSelection.use_wastebasket.value:
            config.AdvancedMovieSelection.server_enabled.setValue(False)
        if config.AdvancedMovieSelection.ml_disable.isChanged():
            self.needsRestartFlag = True
        if config.AdvancedMovieSelection.movie_launch.isChanged():
            self.needsRestartFlag = True
        if config.AdvancedMovieSelection.overwrite_left_right.isChanged():
            self.needsRestartFlag = True        
        if config.usage.load_length_of_movies_in_moviellist.isChanged() and config.usage.load_length_of_movies_in_moviellist.value == False:
            config.AdvancedMovieSelection.showprogessbarinmovielist.value = False
            config.AdvancedMovieSelection.showiconstatusinmovielist.value = False
            config.AdvancedMovieSelection.showcolorstatusinmovielist.value = False
            config.AdvancedMovieSelection.showpercentinmovielist.value = False
        if config.AdvancedMovieSelection.use_original_movieplayer_summary.isChanged():
            self.needsE2restartFlag = True
        if config.AdvancedMovieSelection.server_enabled.isChanged():
            from .Source.Remote.MessageServer import serverInstance
            if config.AdvancedMovieSelection.server_enabled.value:
                serverInstance.setPort(config.AdvancedMovieSelection.server_port.value)
                serverInstance.start()
                serverInstance.setSearchRange(config.AdvancedMovieSelection.start_search_ip.value, config.AdvancedMovieSelection.stop_search_ip.value)
                serverInstance.startScanForClients()
            else:
                serverInstance.shutdown()
                serverInstance.active_clients = []
        
        from .Source.EpgListExtension import epgListExtension
        epgListExtension.setEnabled(config.AdvancedMovieSelection.epg_extension.value)
        
        if self.csel:
            self.csel.updateSettings()
        if self.needsRestartFlag == True:
            self.session.openWithCallback(self.exitAnswer, MessageBoxEx, _("Some settings changes require a restart to take effect.\nIf you  use a skin without PiG (Picture in Graphic) you have to restart the box (not only Enigma 2)!\nWith YES only Enigma 2 starts new, with NO the box make a restart."), type=MessageBox.TYPE_YESNO)
        elif self.needsE2restartFlag == True:
            self.session.openWithCallback(self.exitAnswer2, MessageBoxEx, _("Some settings changes require a Enigma 2 restart to take effect.\n\nWould you restart Enigma2 now?"), type=MessageBox.TYPE_YESNO)
        else:
            if self.needsReopenFlag == True:
                self.session.openWithCallback(self.save, MessageBox, _("Some settings changes require close/reopen the movielist to take effect."), type=MessageBox.TYPE_INFO)
            else:
                self.save()

    def exitAnswer(self, result):
        if result is None:
            self.session.open(MessageBox, _("Aborted by user!!"), MessageBox.TYPE_ERROR)
        if result is False:
            self.save()
            quitMainloop(2)
        if result:
            self.save()
            quitMainloop(3)

    def exitAnswer2(self, result):
        if result is None:
            self.session.open(MessageBox, _("Aborted by user!!"), MessageBox.TYPE_ERROR)
        if result is False:
            self.save()
            self.close()
        if result:
            self.save()
            quitMainloop(3)

    def save(self, retval=None):
        ConfigListScreen.keySave(self)
            
    def about(self):
        self.session.open(AdvancedMovieSelectionAbout)
        
    def buttonsetup(self):
        self.session.open(AdvancedMovieSelectionButtonSetup, self.csel)
            
    def RecPathSettings(self):
        self.session.open(RecordPathsSettings)


class AdvancedMovieSelectionButtonSetup(Screen, ConfigListScreen):
    def __init__(self, session, csel=None):
        Screen.__init__(self, session)
        self.csel = csel
        self.skinName = SkinTools.appendResolution("AdvancedMovieSelectionButtonSetup")
        self["important"] = StaticText() # TODO: deprecated - backward patch for oe1.6 compatibility 
        self["key_red"] = Button(_("Cancel"))
        self["key_green"] = Button(_("Save/Close"))
        self["key_yellow"] = Button(_("Own button description"))
        self["OKIcon"] = Pixmap()
        self["OKIcon"].hide()
        
        ConfigListScreen.__init__(self, [])
        
        self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
        {
            "green": self.keySave,
            "yellow": self.ownname,
            "cancel": self.cancel,
            "ok": self.ok,
        }, -2)
        self.onLayoutFinish.append(self.setCustomTitle)
        self.createConfig()

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.selectionChanged()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.selectionChanged()
        
    def setCustomTitle(self):
        self.setTitle(_("Movie Quick Button Setup"))

    def checkEntry(self, entry, l):
        for x in l:
            if isinstance(x, str) and x == entry:
                return True
            elif x[0] == entry:
                return True

    def createConfig(self):
        self.entryguilist = []
        self.entryguilist.append(("Nothing", _("Nothing")))
        self.entryguilist.append(("Delete", _("Delete")))
        self.entryguilist.append(("Move-Copy", _("Move-Copy")))
        self.entryguilist.append(("Rename", _("Rename")))
        self.entryguilist.append(("Wastebasket", _("Wastebasket")))
        self.entryguilist.append(("Sort", _("Sort")))
        self.entryguilist.append(("Library/Movielist", _("Switch library/movielist")))
        self.entryguilist.append(("Show/Hide library", _("Show/Hide library")))
        self.entryguilist.append(("Show/Hide folders", _("Show/Hide folders")))
        self.entryguilist.append(("Show/Hide seen", _("Show/Hide seen movies")))
        self.entryguilist.append(("Bookmark(s) on/off", _("Bookmark(s) on/off")))
        self.entryguilist.append(("LIB marker on/off", _("Library marker on/off")))
        self.entryguilist.append(("Update library", _("Update library")))
        self.entryguilist.append(("Home", _("Home")))
        self.entryguilist.append(("Bookmark 1", _("Bookmark 1")))
        self.entryguilist.append(("Bookmark 2", _("Bookmark 2")))
        self.entryguilist.append(("Bookmark 3", _("Bookmark 3")))
        self.entryguilist.append(("Bookmark 4", _("Bookmark 4")))
        self.entryguilist.append(("Bookmark 5", _("Bookmark 5")))
        self.entryguilist.append(("Bookmark 6", _("Bookmark 6")))
        self.entryguilist.append(("Bookmark 7", _("Bookmark 7")))
        self.entryguilist.append(("Filter by Tags", _("Filter by Tags")))
        self.entryguilist.append(("Tag Editor", _("Tag Editor")))
        self.entryguilist.append(("TMDb Info & D/L", _("TMDb Info & D/L")))
        self.entryguilist.append(("TheTVDB Info & D/L", _("TheTVDB Info & D/L")))
        self.entryguilist.append(("Toggle seen", _("Toggle seen")))
        self.entryguilist.append(("Mark as seen", _("Mark as seen")))
        self.entryguilist.append(("Mark as unseen", _("Mark as unseen")))
        self.entryguilist.append(("Show Timer", _("Show Timer")))
        self.entryguilist.append(("Show up to VSR-X", _("Show up to VSR-X")))
        self.entryguilist.append(("Filter by description", _("Filter by description")))
        if pluginPresent.YTTrailer == True:
            self.entryguilist.append(("Trailer search", _("Trailer search")))
        self.entryguilist2 = []
        self.entryguilist2.append(("Nothing", _("Nothing")))
        self.entryguilist2.append(("DM-600PVR", _("DM-600PVR")))
        self.entryguilist2.append(("DM-7000", _("DM-7000")))
        self.entryguilist2.append(("DM-7025", _("DM-7025")))
        self.entryguilist2.append(("DM-8000HD", _("DM-8000HD")))
        self.entryguilist2.append(("DM-500HD", _("DM-500HD")))
        self.entryguilist2.append(("DM-800HD", _("DM-800HD")))
        self.entryguilist2.append(("DM-800HDse", _("DM-800HDse")))
        self.entryguilist2.append(("DM-7020HD", _("DM-7020HD")))
        self.entryguilist2.append(("internal HDD", _("internal HDD")))
        self.entryguilist2.append(("NAS", _("NAS")))
        self.entryguilist2.append(("NAS-Movies", _("NAS-Movies")))
        self.entryguilist3 = []
        self.entryguilist3.append(("Display plugin name", _("Display plugin name")))
        self.entryguilist3.append(("Display plugin description", _("Display plugin description")))        

        for p in plugins.getPlugins(where=[PluginDescriptor.WHERE_MOVIELIST]):
            self.entryguilist.append(str(p.name))

        self.qbutton_choicelist = []
        for button, function in qButtons.get():
            print(button, function)
            if function == "" or not self.checkEntry(function, self.entryguilist):
                print("[no config entry]", button, function) 
                function = "Nothing"
            csel = (button, ConfigSelection(default=function, choices=self.entryguilist))
            self.qbutton_choicelist.append(csel)

        #self.redchoice = ConfigSelection(default=config.AdvancedMovieSelection.red.value, choices=self.entryguilist)
        #self.greenchoice = ConfigSelection(default=config.AdvancedMovieSelection.green.value, choices=self.entryguilist)
        #self.yellowchoice = ConfigSelection(default=config.AdvancedMovieSelection.yellow.value, choices=self.entryguilist)
        #self.bluechoice = ConfigSelection(default=config.AdvancedMovieSelection.blue.value, choices=self.entryguilist)
        self.buttoncaptionchoice = ConfigSelection(default=config.AdvancedMovieSelection.buttoncaption.value, choices=self.entryguilist3)

        default = self.checkOwnButtonText(self.entryguilist2, config.AdvancedMovieSelection.hometext.value, config.AdvancedMovieSelection.homeowntext.value)
        self.homebuttontextchoice = ConfigSelection(default=default, choices=self.entryguilist2)
        default = self.checkOwnButtonText(self.entryguilist2, config.AdvancedMovieSelection.bookmark1text.value, config.AdvancedMovieSelection.bookmark1owntext.value)
        self.bookmark1buttontextchoice = ConfigSelection(default=default, choices=self.entryguilist2)
        default = self.checkOwnButtonText(self.entryguilist2, config.AdvancedMovieSelection.bookmark2text.value, config.AdvancedMovieSelection.bookmark2owntext.value)
        self.bookmark2buttontextchoice = ConfigSelection(default=default, choices=self.entryguilist2)
        default = self.checkOwnButtonText(self.entryguilist2, config.AdvancedMovieSelection.bookmark3text.value, config.AdvancedMovieSelection.bookmark3owntext.value)
        self.bookmark3buttontextchoice = ConfigSelection(default=default, choices=self.entryguilist2)
        default = self.checkOwnButtonText(self.entryguilist2, config.AdvancedMovieSelection.bookmark4text.value, config.AdvancedMovieSelection.bookmark4owntext.value)
        self.bookmark4buttontextchoice = ConfigSelection(default=default, choices=self.entryguilist2)
        default = self.checkOwnButtonText(self.entryguilist2, config.AdvancedMovieSelection.bookmark5text.value, config.AdvancedMovieSelection.bookmark5owntext.value)
        self.bookmark5buttontextchoice = ConfigSelection(default=default, choices=self.entryguilist2)
        default = self.checkOwnButtonText(self.entryguilist2, config.AdvancedMovieSelection.bookmark6text.value, config.AdvancedMovieSelection.bookmark6owntext.value)
        self.bookmark6buttontextchoice = ConfigSelection(default=default, choices=self.entryguilist2)
        default = self.checkOwnButtonText(self.entryguilist2, config.AdvancedMovieSelection.bookmark7text.value, config.AdvancedMovieSelection.bookmark7owntext.value)
        self.bookmark7buttontextchoice = ConfigSelection(default=default, choices=self.entryguilist2)
        self.initConfigList()

    def checkOwnButtonText(self, l, text, own_text):
        l1 = [descr[0] for descr in l]
        if own_text and not own_text in l1:
            l.append((own_text, own_text))
            l1.append(own_text)
        if not text in l1:
            l.append((text, text))
        return text

    def initConfigList(self):
        hometmp = config.movielist.videodirs.value
        homedefault = config.AdvancedMovieSelection.homepath.value
        if homedefault not in hometmp:
            hometmp = hometmp[:]
            hometmp.append(homedefault)
        self.homepath_dirname = ConfigSelection(default=homedefault, choices=hometmp)
        hometmp = config.movielist.videodirs.value

        book1tmp = config.movielist.videodirs.value
        book1default = config.AdvancedMovieSelection.bookmark1path.value
        if book1default not in book1tmp:
            book1tmp = book1tmp[:]
            book1tmp.append(book1default)
        self.bookmark1_dirname = ConfigSelection(default=book1default, choices=book1tmp)
        book1tmp = config.movielist.videodirs.value

        book2tmp = config.movielist.videodirs.value
        book2default = config.AdvancedMovieSelection.bookmark2path.value
        if book2default not in book2tmp:
            book2tmp = book2tmp[:]
            book2tmp.append(book2default)
        self.bookmark2_dirname = ConfigSelection(default=book2default, choices=book2tmp)
        book2tmp = config.movielist.videodirs.value

        book3tmp = config.movielist.videodirs.value
        book3default = config.AdvancedMovieSelection.bookmark3path.value
        if book3default not in book3tmp:
            book3tmp = book3tmp[:]
            book3tmp.append(book3default)
        self.bookmark3_dirname = ConfigSelection(default=book3default, choices=book3tmp)
        book3tmp = config.movielist.videodirs.value

        book4tmp = config.movielist.videodirs.value
        book4default = config.AdvancedMovieSelection.bookmark4path.value
        if book4default not in book4tmp:
            book4tmp = book4tmp[:]
            book4tmp.append(book4default)
        self.bookmark4_dirname = ConfigSelection(default=book4default, choices=book4tmp)
        book4tmp = config.movielist.videodirs.value

        book5tmp = config.movielist.videodirs.value
        book5default = config.AdvancedMovieSelection.bookmark5path.value
        if book5default not in book5tmp:
            book5tmp = book5tmp[:]
            book5tmp.append(book5default)
        self.bookmark5_dirname = ConfigSelection(default=book5default, choices=book5tmp)
        book5tmp = config.movielist.videodirs.value

        book6tmp = config.movielist.videodirs.value
        book6default = config.AdvancedMovieSelection.bookmark6path.value
        if book6default not in book6tmp:
            book6tmp = book6tmp[:]
            book6tmp.append(book6default)
        self.bookmark6_dirname = ConfigSelection(default=book6default, choices=book6tmp)
        book6tmp = config.movielist.videodirs.value

        book7tmp = config.movielist.videodirs.value
        book7default = config.AdvancedMovieSelection.bookmark7path.value
        if book7default not in book7tmp:
            book7tmp = book7tmp[:]
            book7tmp.append(book7default)
        self.bookmark7_dirname = ConfigSelection(default=book7default, choices=book7tmp)
        book7tmp = config.movielist.videodirs.value

        self.list = []
        for button, config_sel in self.qbutton_choicelist:
            if button.endswith("_long"):
                text = _(button.split("_")[0]) + " " + _("(long)")
            else:
                text = _(button)
            cle = getConfigListEntry(_("Quickbutton:") + " %s" % (text), config_sel)
            self.list.append(cle)
            
        self.button_caption = getConfigListEntry(_("Button caption"), self.buttoncaptionchoice)
        self.list.append(self.button_caption)
        self.home_button_text = getConfigListEntry(_("Home button text"), self.homebuttontextchoice)
        self.list.append(self.home_button_text)
        self.bookmark_1_button_text = getConfigListEntry(_("Bookmark 1 button text"), self.bookmark1buttontextchoice)
        self.list.append(self.bookmark_1_button_text)
        self.bookmark_2_button_text = getConfigListEntry(_("Bookmark 2 button text"), self.bookmark2buttontextchoice)
        self.list.append(self.bookmark_2_button_text)
        self.bookmark_3_button_text = getConfigListEntry(_("Bookmark 3 button text"), self.bookmark3buttontextchoice)
        self.list.append(self.bookmark_3_button_text)
        self.bookmark_4_button_text = getConfigListEntry(_("Bookmark 4 button text"), self.bookmark4buttontextchoice)
        self.list.append(self.bookmark_4_button_text)
        self.bookmark_5_button_text = getConfigListEntry(_("Bookmark 5 button text"), self.bookmark5buttontextchoice)
        self.list.append(self.bookmark_5_button_text)
        self.bookmark_6_button_text = getConfigListEntry(_("Bookmark 6 button text"), self.bookmark6buttontextchoice)
        self.list.append(self.bookmark_6_button_text)
        self.bookmark_7_button_text = getConfigListEntry(_("Bookmark 7 button text"), self.bookmark7buttontextchoice)
        self.list.append(self.bookmark_7_button_text)
        self.homepath = getConfigListEntry(_("Home path"), self.homepath_dirname)
        self.list.append(self.homepath)
        self.bookmark1 = getConfigListEntry(_("Bookmark 1 path"), self.bookmark1_dirname)
        self.list.append(self.bookmark1)
        self.bookmark2 = getConfigListEntry(_("Bookmark 2 path"), self.bookmark2_dirname)
        self.list.append(self.bookmark2)
        self.bookmark3 = getConfigListEntry(_("Bookmark 3 path"), self.bookmark3_dirname)
        self.list.append(self.bookmark3)
        self.bookmark4 = getConfigListEntry(_("Bookmark 4 path"), self.bookmark4_dirname)
        self.list.append(self.bookmark4)
        self.bookmark5 = getConfigListEntry(_("Bookmark 5 path"), self.bookmark5_dirname)
        self.list.append(self.bookmark5)
        self.bookmark6 = getConfigListEntry(_("Bookmark 6 path"), self.bookmark6_dirname)
        self.list.append(self.bookmark6)
        self.bookmark7 = getConfigListEntry(_("Bookmark 7 path"), self.bookmark7_dirname)
        self.list.append(self.bookmark7)
        self["config"].setList(self.list)
        if not self.selectionChanged in self["config"].onSelectionChanged:
            self["config"].onSelectionChanged.append(self.selectionChanged)
            
    def selectionChanged(self):
        current = self["config"].getCurrent()
        if current == self.homepath:
            self.enableOKIcon()
        elif current == self.bookmark1:
            self.enableOKIcon()
        elif current == self.bookmark2:
            self.enableOKIcon()
        elif current == self.bookmark3:
            self.enableOKIcon()
        elif current == self.bookmark4:
            self.enableOKIcon()
        elif current == self.bookmark5:
            self.enableOKIcon()
        elif current == self.bookmark6:
            self.enableOKIcon()
        elif current == self.bookmark7:
            self.enableOKIcon()    
        elif current[1].getValue() == "Sort":
            self.enableOKIcon()
        else:
            self.disableOKIcon()

    def enableOKIcon(self):
        self["OKIcon"].show()

    def disableOKIcon(self):
        self["OKIcon"].hide()

    def ok(self):
        currentry = self["config"].getCurrent()
        self.lastvideodirs = config.movielist.videodirs.value
        if currentry[1].getValue() == "Sort":
            from .MovieList import MovieList
            sorts = [] 
            sorts.append((str(MovieList.SORT_ALPHANUMERIC), _("Alphabetic sort")))
            sorts.append((str(MovieList.SORT_DATE_ASC), _("Sort by date (ascending)")))
            sorts.append((str(MovieList.SORT_DATE_DESC), _("Sort by date (descending)")))
            sorts.append((str(MovieList.SORT_DESCRIPTION), _("Sort by description")))
            
            sels = config.AdvancedMovieSelection.sort_functions.value.split()
            if len(sels) == 0:
                for s in sorts:
                    sels.append(s[0])
            from .SelectionListScreen import SelectionListScreen
            self.session.openWithCallback(self.sortTypeSelected, SelectionListScreen, _("Select sort functions"), sorts, sels)
        elif currentry == self.homepath:
            self.entrydirname = self.homepath_dirname
            self.session.openWithCallback(self.dirnameSelected, MovieLocationBox, _("Movie Quick Button Home path"), preferredPath(self.homepath_dirname.value))
        elif currentry == self.bookmark1:
            self.entrydirname = self.bookmark1_dirname
            self.session.openWithCallback(self.dirnameSelected, MovieLocationBox, _("Movie Quick Button Bookmark 1 path"), preferredPath(self.bookmark1_dirname.value))
        elif currentry == self.bookmark2:
            self.entrydirname = self.bookmark2_dirname 
            self.session.openWithCallback(self.dirnameSelected, MovieLocationBox, _("Movie Quick Button Bookmark 2 path"), preferredPath(self.bookmark2_dirname.value))     
        elif currentry == self.bookmark3:
            self.entrydirname = self.bookmark3_dirname
            self.session.openWithCallback(self.dirnameSelected, MovieLocationBox, _("Movie Quick Button Bookmark 3 path"), preferredPath(self.bookmark3_dirname.value))
        elif currentry == self.bookmark4:
            self.entrydirname = self.bookmark4_dirname
            self.session.openWithCallback(self.dirnameSelected, MovieLocationBox, _("Movie Quick Button Bookmark 4 path"), preferredPath(self.bookmark4_dirname.value))
        elif currentry == self.bookmark5:
            self.entrydirname = self.bookmark5_dirname 
            self.session.openWithCallback(self.dirnameSelected, MovieLocationBox, _("Movie Quick Button Bookmark 5 path"), preferredPath(self.bookmark5_dirname.value))     
        elif currentry == self.bookmark6:
            self.entrydirname = self.bookmark6_dirname
            self.session.openWithCallback(self.dirnameSelected, MovieLocationBox, _("Movie Quick Button Bookmark 6 path"), preferredPath(self.bookmark6_dirname.value))
        elif currentry == self.bookmark7:
            self.entrydirname = self.bookmark7_dirname
            self.session.openWithCallback(self.dirnameSelected, MovieLocationBox, _("Movie Quick Button Bookmark 7 path"), preferredPath(self.bookmark7_dirname.value))
        else:
            self.keySave()                 

    def sortTypeSelected(self, res):
        if res is not None:
            config.AdvancedMovieSelection.sort_functions.value = " ".join(res)
            config.AdvancedMovieSelection.sort_functions.save()

    def dirnameSelected(self, res):
        if res is not None:
            self.entrydirname.value = res
            if config.movielist.videodirs.value != self.lastvideodirs:
                tmp = config.movielist.videodirs.value
                default = self.homepath_dirname.value
                if default not in tmp:
                    tmp = tmp[:]
                    tmp.append(default)
                self.homepath_dirname.setChoices(tmp, default=default)

                default = self.bookmark1_dirname.value
                if default not in tmp:
                    tmp = tmp[:]
                    tmp.append(default)
                self.bookmark1_dirname.setChoices(tmp, default=default)

                default = self.bookmark2_dirname.value
                if default not in tmp:
                    tmp = tmp[:]
                    tmp.append(default)
                self.bookmark2_dirname.setChoices(tmp, default=default)

                default = self.bookmark3_dirname.value
                if default not in tmp:
                    tmp = tmp[:]
                    tmp.append(default)
                self.bookmark3_dirname.setChoices(tmp, default=default)

                default = self.bookmark4_dirname.value
                if default not in tmp:
                    tmp = tmp[:]
                    tmp.append(default)
                self.bookmark4_dirname.setChoices(tmp, default=default)

                default = self.bookmark5_dirname.value
                if default not in tmp:
                    tmp = tmp[:]
                    tmp.append(default)
                self.bookmark5_dirname.setChoices(tmp, default=default)

                default = self.bookmark6_dirname.value
                if default not in tmp:
                    tmp = tmp[:]
                    tmp.append(default)
                self.bookmark6_dirname.setChoices(tmp, default=default)

                default = self.bookmark7_dirname.value
                if default not in tmp:
                    tmp = tmp[:]
                    tmp.append(default)
                self.bookmark7_dirname.setChoices(tmp, default=default)
                
    def keySave(self):
        for button, config_sel in self.qbutton_choicelist:
            fn = config_sel.getValue()
            qButtons.setFunction(button, fn)
        qButtons.save()

        config.AdvancedMovieSelection.buttoncaption.value = self.buttoncaptionchoice.getValue()
        config.AdvancedMovieSelection.homepath.value = self.homepath_dirname.value
        config.AdvancedMovieSelection.bookmark1path.value = self.bookmark1_dirname.value
        config.AdvancedMovieSelection.bookmark2path.value = self.bookmark2_dirname.value
        config.AdvancedMovieSelection.bookmark3path.value = self.bookmark3_dirname.value
        config.AdvancedMovieSelection.bookmark4path.value = self.bookmark4_dirname.value
        config.AdvancedMovieSelection.bookmark5path.value = self.bookmark5_dirname.value
        config.AdvancedMovieSelection.bookmark6path.value = self.bookmark6_dirname.value
        config.AdvancedMovieSelection.bookmark7path.value = self.bookmark7_dirname.value
        
        config.AdvancedMovieSelection.hometext.value = self.homebuttontextchoice.getValue()
        config.AdvancedMovieSelection.bookmark1text.value = self.bookmark1buttontextchoice.getValue()
        config.AdvancedMovieSelection.bookmark2text.value = self.bookmark2buttontextchoice.getValue()
        config.AdvancedMovieSelection.bookmark3text.value = self.bookmark3buttontextchoice.getValue()
        config.AdvancedMovieSelection.bookmark4text.value = self.bookmark4buttontextchoice.getValue()
        config.AdvancedMovieSelection.bookmark5text.value = self.bookmark5buttontextchoice.getValue()
        config.AdvancedMovieSelection.bookmark6text.value = self.bookmark6buttontextchoice.getValue()
        config.AdvancedMovieSelection.bookmark7text.value = self.bookmark7buttontextchoice.getValue()

        config.AdvancedMovieSelection.save()
        configfile.save()
        if self.csel:
            self.csel.updateHelpText()
            self.csel.updateButtonText()
        self.close()

    def cancel(self):
        self.close()

    def ownname(self):
        self.session.openWithCallback(self.createConfig, AdvancedMovieSelectionOwnButtonName)


class AdvancedMovieSelectionOwnButtonName(Screen, ConfigListScreen):        
    def __init__(self, session):
        Screen.__init__(self, session)
        self.skinName = SkinTools.appendResolution("AdvancedMovieSelectionOwnButtonName")
        self.homebutton = None
        self.bookmark1button = None
        self.bookmark2button = None
        self.bookmark3button = None
        self.bookmark4button = None
        self.bookmark5button = None
        self.bookmark6button = None 
        self.bookmark7button = None                
        self["setupActions"] = ActionMap(["ColorActions", "OkCancelActions"],
        {
            "red": self.keySave,
            "cancel": self.keyCancel
        }, -2) 
        self["VirtualKB"] = ActionMap(["VirtualKeyboardActions"],
        {
            "showVirtualKeyboard": self.KeyText,
        }, -1)
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session)
        self["menu"] = List(self.list)
        self["help"] = StaticText()
        self["key_red"] = StaticText(_("Save/Close"))
        self["VKeyIcon"] = Boolean(False)
        self["HelpWindow"] = Pixmap()
        self["VirtualKB"].setEnabled(False)
        self.onShown.append(self.setWindowTitle)
        self.createSetup()

    def setWindowTitle(self, retval=None):
        self.setTitle(_("Movie Quick Button Name Setup"))

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.createSetup()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.createSetup()

    def KeyText(self):
        if self["config"].getCurrent() == self.homebutton:
            self.session.openWithCallback(self.homebuttonCallback, VirtualKeyBoard, title=(_("Enter Home button descrition:")), text=config.AdvancedMovieSelection.homeowntext.value)
        if self["config"].getCurrent() == self.bookmark1button:
            self.session.openWithCallback(self.bookmark1buttonCallback, VirtualKeyBoard, title=(_("Enter Bookmark 1 button descrition:")), text=config.AdvancedMovieSelection.bookmark1owntext.value)
        if self["config"].getCurrent() == self.bookmark2button:
            self.session.openWithCallback(self.bookmark2buttonCallback, VirtualKeyBoard, title=(_("Enter Bookmark 2 button descrition:")), text=config.AdvancedMovieSelection.bookmark2owntext.value)
        if self["config"].getCurrent() == self.bookmark3button:
            self.session.openWithCallback(self.bookmark3buttonCallback, VirtualKeyBoard, title=(_("Enter Bookmark 3 button descrition:")), text=config.AdvancedMovieSelection.bookmark3owntext.value)
        if self["config"].getCurrent() == self.bookmark4button:
            self.session.openWithCallback(self.bookmark4buttonCallback, VirtualKeyBoard, title=(_("Enter Bookmark 4 button descrition:")), text=config.AdvancedMovieSelection.bookmark4owntext.value)
        if self["config"].getCurrent() == self.bookmark5button:
            self.session.openWithCallback(self.bookmark5buttonCallback, VirtualKeyBoard, title=(_("Enter Bookmark 5 button descrition:")), text=config.AdvancedMovieSelection.bookmark5owntext.value)
        if self["config"].getCurrent() == self.bookmark6button:
            self.session.openWithCallback(self.bookmark6buttonCallback, VirtualKeyBoard, title=(_("Enter Bookmark 6 button descrition:")), text=config.AdvancedMovieSelection.bookmark6owntext.value)
        if self["config"].getCurrent() == self.bookmark7button:
            self.session.openWithCallback(self.bookmark7buttonCallback, VirtualKeyBoard, title=(_("Enter Bookmark 7 button descrition:")), text=config.AdvancedMovieSelection.bookmark7owntext.value)

    def homebuttonCallback(self, callback=None):
        if callback is not None and len(callback):
            config.AdvancedMovieSelection.homeowntext.setValue(callback)
            self["config"].invalidate(self.homebutton)

    def bookmark1buttonCallback(self, callback=None):
        if callback is not None and len(callback):
            config.AdvancedMovieSelection.bookmark1owntext.setValue(callback)
            self["config"].invalidate(self.bookmark1button)

    def bookmark2buttonCallback(self, callback=None):
        if callback is not None and len(callback):
            config.AdvancedMovieSelection.bookmark2owntext.setValue(callback)
            self["config"].invalidate(self.bookmark2button)

    def bookmark3buttonCallback(self, callback=None):
        if callback is not None and len(callback):
            config.AdvancedMovieSelection.bookmark3owntext.setValue(callback)
            self["config"].invalidate(self.bookmark3button)

    def bookmark4buttonCallback(self, callback=None):
        if callback is not None and len(callback):
            config.AdvancedMovieSelection.bookmark4owntext.setValue(callback)
            self["config"].invalidate(self.bookmark4button)

    def bookmark5buttonCallback(self, callback=None):
        if callback is not None and len(callback):
            config.AdvancedMovieSelection.bookmark5owntext.setValue(callback)
            self["config"].invalidate(self.bookmark5button)

    def bookmark6buttonCallback(self, callback=None):
        if callback is not None and len(callback):
            config.AdvancedMovieSelection.bookmark6owntext.setValue(callback)
            self["config"].invalidate(self.bookmark6button)

    def bookmark7buttonCallback(self, callback=None):
        if callback is not None and len(callback):
            config.AdvancedMovieSelection.bookmark7owntext.setValue(callback)
            self["config"].invalidate(self.bookmark7button)
        
    def createSetup(self, retval=None):
        self.list = []
        self.homebutton = getConfigListEntry(_("Home button description:"), config.AdvancedMovieSelection.homeowntext)
        self.bookmark1button = getConfigListEntry(_("Bookmark 1 button description:"), config.AdvancedMovieSelection.bookmark1owntext)
        self.bookmark2button = getConfigListEntry(_("Bookmark 2 button description:"), config.AdvancedMovieSelection.bookmark2owntext)
        self.bookmark3button = getConfigListEntry(_("Bookmark 3 button description:"), config.AdvancedMovieSelection.bookmark3owntext)
        self.bookmark4button = getConfigListEntry(_("Bookmark 4 button description:"), config.AdvancedMovieSelection.bookmark4owntext)
        self.bookmark5button = getConfigListEntry(_("Bookmark 5 button description:"), config.AdvancedMovieSelection.bookmark5owntext)
        self.bookmark6button = getConfigListEntry(_("Bookmark 6 button description:"), config.AdvancedMovieSelection.bookmark6owntext)
        self.bookmark7button = getConfigListEntry(_("Bookmark 7 button description:"), config.AdvancedMovieSelection.bookmark7owntext)
        self.list.append(self.homebutton)
        self.list.append(self.bookmark1button)
        self.list.append(self.bookmark2button)
        self.list.append(self.bookmark3button)
        self.list.append(self.bookmark4button)
        self.list.append(self.bookmark5button)
        self.list.append(self.bookmark6button)
        self.list.append(self.bookmark7button)
        self["config"].list = self.list
        self["config"].l.setList(self.list)
        if not self.selectionChanged in self["config"].onSelectionChanged:
            self["config"].onSelectionChanged.append(self.selectionChanged)

    def selectionChanged(self):
        current = self["config"].getCurrent()
        if current == self.homebutton:
            self["help"].setText(_("Here you can give the home button a special name."))
            self.enableVKeyIcon()
            self.showKeypad()
        elif current == self.bookmark1button:
            self["help"].setText(_("Here you can give the bookmark 1 button a special name."))
            self.enableVKeyIcon()
            self.showKeypad()
        elif current == self.bookmark2button:
            self["help"].setText(_("Here you can give the bookmark 2 button a special name."))
            self.enableVKeyIcon()
            self.showKeypad()
        elif current == self.bookmark3button:
            self["help"].setText(_("Here you can give the bookmark 3 button a special name."))
            self.enableVKeyIcon()
            self.showKeypad()
        elif current == self.bookmark4button:
            self["help"].setText(_("Here you can give the bookmark 4 button a special name."))
            self.enableVKeyIcon()
            self.showKeypad()
        elif current == self.bookmark5button:
            self["help"].setText(_("Here you can give the bookmark 5 button a special name."))
            self.enableVKeyIcon()
            self.showKeypad()
        elif current == self.bookmark6button:
            self["help"].setText(_("Here you can give the bookmark 6 button a special name."))
            self.enableVKeyIcon()
            self.showKeypad()
        elif current == self.bookmark7button:
            self["help"].setText(_("Here you can give the bookmark 7 button a special name."))
            self.enableVKeyIcon()
            self.showKeypad()

    def enableVKeyIcon(self):
        self["VKeyIcon"].boolean = True
        self["VirtualKB"].setEnabled(True)

    def disableVKeyIcon(self):
        self["VKeyIcon"].boolean = False
        self["VirtualKB"].setEnabled(False)

    def showKeypad(self, retval=None):
        current = self["config"].getCurrent()
        helpwindowpos = self["HelpWindow"].getPosition()
        if hasattr(current[1], 'help_window'):
            if current[1].help_window.instance is not None:
                current[1].help_window.instance.show()
                current[1].help_window.instance.move(ePoint(helpwindowpos[0], helpwindowpos[1]))

    def hideKeypad(self):
        current = self["config"].getCurrent()
        if hasattr(current[1], 'help_window'):
            if current[1].help_window.instance is not None:
                current[1].help_window.instance.hide()

    def cancelConfirm(self, result):
        if not result:
            self.showKeypad()
            return
        for x in self["config"].list:
            x[1].cancel()
        self.close()

    def keyCancel(self):
        print("cancel")
        if self["config"].isChanged():
            self.hideKeypad()
            self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
        else:
            self.close()

    def keySave(self):
        print("saving")
        ConfigListScreen.keySave(self)
