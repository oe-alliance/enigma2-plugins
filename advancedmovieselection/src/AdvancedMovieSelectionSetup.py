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
from __init__ import _
from enigma import ePoint
from Screens.Screen import Screen
from RecordPaths import RecordPathsSettings
from About import AdvancedMovieSelectionAbout
from Components.Pixmap import Pixmap
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor
from Components.config import config, getConfigListEntry, configfile, ConfigSelection as eConfigSelection
from Components.Sources.StaticText import StaticText
from Components.Button import Button
from Components import ConfigList as eConfigList
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.LocationBox import MovieLocationBox
from Components.UsageConfig import preferredPath
from Screens.MessageBox import MessageBox
from MessageBoxEx import MessageBox as MessageBoxEx
from Components.Sources.List import List
from Components.ActionMap import ActionMap, NumberActionMap
from enigma import getDesktop, quitMainloop
from ClientSetup import ClientSetup
from Globals import pluginPresent, SkinTools

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

from Globals import SkinResolutionHelper
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
        self.list = [ ]
        self.backup_dirs = config.movielist.videodirs.value[:]
        print self.backup_dirs
        default = config.usage.default_path.value
        if default not in self.backup_dirs:
            self.backup_dirs.append(default)
        self.backup_config_path = ConfigSelection(default=default, choices=self.backup_dirs)
        self.list.append(getConfigListEntry(_("Backup directory path:"), self.backup_config_path))
        ConfigListScreen.__init__(self, self.list, session=self.session)
        self["key_red"] = StaticText(_("Close"))
        self["key_green"] = StaticText(_("Restore settings"))
        self["key_yellow"] = StaticText(_("Backup settings"))
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(_("Backup/Restore Advanced Movie Selection settings"))
    
    def getCurrent(self):
        current = self["config"].getCurrent()
        return current and current[1].value
    
    def backup(self):
        from Config import createBackup
        path = self.getCurrent()
        result = createBackup(path)
        if result:
            self.session.open(MessageBox, _("Settings backup successfully created in %s.") % (result), type=MessageBox.TYPE_INFO)
            self.close()
        else:
            self.session.open(MessageBox, _("Error creating settings backup!"), type=MessageBox.TYPE_ERROR)
    
    def openFilebrowser(self):
        from FileBrowser import FileBrowser
        path = self.getCurrent()
        self.session.openWithCallback(self.restoreCallback, FileBrowser, path)

    def restoreCallback(self, answer):
        print answer
        if answer:
            from Config import loadBackup
            loadBackup(answer)
            self.session.open(MessageBox, _("Some settings changes require close/reopen the movielist to take effect."), type=MessageBox.TYPE_INFO)
            self.close()
            
    def okPressed(self):
        from Screens.LocationBox import LocationBox
        path = self.getCurrent()
        from Components.config import ConfigLocations
        locations = ConfigLocations(self.backup_dirs)
        self.session.openWithCallback(self.dirnameSelected, LocationBox, _("Please select backup path here:"), currDir=path, bookmarks=locations)
    
    def dirnameSelected(self, answer):
        if not answer:
            return
        if answer not in self.backup_dirs:
            self.backup_dirs.append(answer)
        self.backup_config_path.setChoices(self.backup_dirs, default=answer)
        self.backup_config_path.setValue(answer)

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
        self.list = [ ]
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
            from Debug import Debug
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
        self.list.append(getConfigListEntry(_("Show plugin config in extensions menu from movielist:"), config.AdvancedMovieSelection.showmenu, _("Displays the Settings option in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show color key setup in extensions menu from movielist:"), config.AdvancedMovieSelection.showcolorkey, _("Displays color key setup option in the menu at the movie list.")))        
        self.list.append(getConfigListEntry(_("Show movie plugins in extensions menu from movielist:"), config.AdvancedMovieSelection.pluginmenu_list, _("Displays E2 movie list extensions in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Load Length of Movies in Movielist:"), config.usage.load_length_of_movies_in_moviellist, _("This option is for many of the functions from the Advanced Movie Selection necessary. If this option is disabled are many functions not available.")))
        if config.usage.load_length_of_movies_in_moviellist.value:
            self.list.append(getConfigListEntry(_("Show directory size in movie list:"), config.AdvancedMovieSelection.show_dirsize, _("Displays the size from directories in movie list.")))
            if config.AdvancedMovieSelection.show_dirsize.value:
                self.list.append(getConfigListEntry(_("Show decimal points:"), config.AdvancedMovieSelection.dirsize_digits, _("Here you can choose how many decimal points for the directory size in the movie list will be displayed.")))
                self.list.append(getConfigListEntry(_("Show full depth of directories:"), config.AdvancedMovieSelection.show_dirsize_full, _("Displays the full size of all sub directories of directory size.")))
            self.list.append(getConfigListEntry(_("Show list options in extensions menu from movielist:"), config.AdvancedMovieSelection.showextras, _("Displays the various list view options in the menu at the movie list (Progressbar,View folders...).")))
            self.list.append(getConfigListEntry(_("Show mark movie in extensions menu from movielist:"), config.AdvancedMovieSelection.showmark, _("Displays mark movie as seen/unseen in the menu at the movie list.")))
            self.list.append(getConfigListEntry(_("Mark movie as seen at position (in percent):"), config.AdvancedMovieSelection.moviepercentseen, _("With this option you can assign as when a film is marked as seen.")))
        self.list.append(getConfigListEntry(_("Show sort options in extensions menu from movielist:"), config.AdvancedMovieSelection.showsort, _("Displays sorting function in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show list styles in extensions menu from movielist:"), config.AdvancedMovieSelection.showliststyle, _("Displays various lists typs in the menu at the movie list (Minimal,Compact...).")))        
        self.list.append(getConfigListEntry(_("Show delete option in extensions menu from movielist:"), config.AdvancedMovieSelection.showdelete, _("Displays the movie delete function in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show move/copy option in extensions menu from movielist:"), config.AdvancedMovieSelection.showmove, _("Displays the movie move/copy function in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show movie search in extensions menu from movielist:"), config.AdvancedMovieSelection.showsearch, _("Displays the movie search function in the menu at the movie list.")))
        self.list.append(getConfigListEntry(_("Show covers in movielist:"), config.AdvancedMovieSelection.showpreview, _("Displays the cover in the movie list."))) 
        if config.AdvancedMovieSelection.showpreview.value:
            self.list.append(getConfigListEntry(_("Set coversize:"), config.AdvancedMovieSelection.coversize, _("Here you can determine the coverfile size for the download/save.")))
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
        self.list.append(getConfigListEntry(_("Show hotplug devices:"), config.AdvancedMovieSelection.hotplug, _("Enable this option to use USB-Devices.")))
        self.list.append(getConfigListEntry(_("Show bookmarks in movielist:"), config.AdvancedMovieSelection.show_bookmarks, _("When enabled all created bookmarks appear in the movie list.")))
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
        if  pluginPresent.YTTrailer:
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
        from Wastebasket import waste_timer
        if waste_timer:
            waste_timer.configChange()
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
            from MessageServer import serverInstance
            if config.AdvancedMovieSelection.server_enabled.value:
                serverInstance.setPort(config.AdvancedMovieSelection.server_port.value)
                serverInstance.start()
                serverInstance.setSearchRange(config.AdvancedMovieSelection.start_search_ip.value, config.AdvancedMovieSelection.stop_search_ip.value)
                serverInstance.startScanForClients()
            else:
                serverInstance.shutdown()
                serverInstance.active_clients = []
        
        from EpgListExtension import epgListExtension
        epgListExtension.enabled(config.AdvancedMovieSelection.epg_extension.value)
        
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

class ConfigSelection(eConfigSelection):
    def getMulti(self, selected):
        sel = eConfigSelection.getMulti(self, selected)
        return (sel[0], _(sel[1]))

__dummy1__ = (_("Nothing"), _("Delete"), _("Wastebasket"), _("Sort"), _("Filter by description"), _("Home"), _("Bookmark 1"), _("Bookmark 2"), _("Bookmark 3"), _("Bookmark(s) on/off"), _("Filter by Tags"), _("Tag Editor"), _("Move-Copy"), _("Rename"),
            _("TMDb Info & D/L"), _("Mark as seen"), _("Mark as unseen"), _("Show/Hide folders"), _("Trailer search"), _("Toggle seen"), _("Show Timer"), _("TheTVDB Info & D/L"))
__dummy2__ = (_("DM-600PVR"), _("DM-7000"), _("DM-7025"), _("DM-8000HD"), _("DM-500HD"), _("DM-800HD"), _("DM-800HDse"), _("DM-7020HD"), _("internal HDD"), _("NAS"), _("NAS-Movies"))
__dummy3__ = (_("Display plugin name"), _("Display plugin description"), _("Show up to VSR-X"))

class AdvancedMovieSelectionButtonSetup(Screen, ConfigListScreen):
    def __init__(self, session, csel=None):
        Screen.__init__(self, session)
        self.csel = csel
        self.skinName = SkinTools.appendResolution("AdvancedMovieSelectionButtonSetup")
        self["important"] = StaticText(_("IMPORTANT: If changes are made here the Advanced Movie Selection must be completely closed so the changes can be adopted!!"))
        self["key_red"] = Button(_("Cancel"))
        self["key_green"] = Button(_("Save/Close"))
        self["key_yellow"] = Button(_("Own button description"))
        self["OKIcon"] = Pixmap()
        self["OKIcon"].hide()
        self.entryguilist = []
        self.entryguilist.append(("0", "Nothing"))
        self.entryguilist.append(("1", "Delete"))
        self.entryguilist.append(("2", "Wastebasket"))
        self.entryguilist.append(("3", "Sort"))
        self.entryguilist.append(("4", "Home"))
        self.entryguilist.append(("5", "Bookmark 1"))
        self.entryguilist.append(("6", "Bookmark 2"))
        self.entryguilist.append(("7", "Bookmark 3"))
        self.entryguilist.append(("8", "Bookmark(s) on/off"))
        self.entryguilist.append(("9", "Filter by Tags"))
        self.entryguilist.append(("10", "Tag Editor"))
        self.entryguilist.append(("11", "Move-Copy"))
        self.entryguilist.append(("12", "Rename"))
        self.entryguilist.append(("13", "TMDb Info & D/L"))
        self.entryguilist.append(("14", "TheTVDB Info & D/L"))
        self.entryguilist.append(("15", "Toggle seen"))
        self.entryguilist.append(("16", "Mark as seen"))
        self.entryguilist.append(("17", "Mark as unseen"))
        self.entryguilist.append(("18", "Show/Hide folders"))
        self.entryguilist.append(("19", "Show Timer"))
        self.entryguilist.append(("20", "Show up to VSR-X"))
        self.entryguilist.append(("21", "Filter by description"))
        if pluginPresent.YTTrailer == True:
            self.entryguilist.append(("22", "Trailer search"))
        self.entryguilist2 = []
        self.entryguilist2.append(("0", "Nothing"))
        self.entryguilist2.append(("1", "DM-600PVR"))
        self.entryguilist2.append(("2", "DM-7000"))
        self.entryguilist2.append(("3", "DM-7025"))
        self.entryguilist2.append(("4", "DM-8000HD"))
        self.entryguilist2.append(("5", "DM-500HD"))
        self.entryguilist2.append(("6", "DM-800HD"))
        self.entryguilist2.append(("7", "DM-800HDse"))
        self.entryguilist2.append(("8", "DM-7020HD"))
        self.entryguilist2.append(("9", "internal HDD"))
        self.entryguilist2.append(("10", "NAS"))
        self.entryguilist2.append(("11", "NAS-Movies"))
        self.entryguilist2.append(("12", config.AdvancedMovieSelection.homeowntext.value))
        self.entryguilist2.append(("13", config.AdvancedMovieSelection.bookmark1owntext.value))
        self.entryguilist2.append(("14", config.AdvancedMovieSelection.bookmark2owntext.value))
        self.entryguilist2.append(("15", config.AdvancedMovieSelection.bookmark3owntext.value))
        self.entryguilist3 = []
        self.entryguilist3.append(("0", "Display plugin name"))
        self.entryguilist3.append(("1", "Display plugin description"))        

        red_selectedindex = self.getStaticName(self.entryguilist, config.AdvancedMovieSelection.red.value)
        green_selectedindex = self.getStaticName(self.entryguilist, config.AdvancedMovieSelection.green.value)
        yellow_selectedindex = self.getStaticName(self.entryguilist, config.AdvancedMovieSelection.yellow.value)
        blue_selectedindex = self.getStaticName(self.entryguilist, config.AdvancedMovieSelection.blue.value)
        hometext_selectedindex = self.getStaticName(self.entryguilist2, config.AdvancedMovieSelection.hometext.value)
        bookmark1buttontext_selectedindex = self.getStaticName(self.entryguilist2, config.AdvancedMovieSelection.bookmark1text.value)
        bookmark2buttontext_selectedindex = self.getStaticName(self.entryguilist2, config.AdvancedMovieSelection.bookmark2text.value)
        bookmark3buttontext_selectedindex = self.getStaticName(self.entryguilist2, config.AdvancedMovieSelection.bookmark3text.value)
        buttoncaptionchoice_selectedindex = self.getStaticName(self.entryguilist3, config.AdvancedMovieSelection.buttoncaption.value)

        index = len(self.entryguilist)        
        for p in plugins.getPlugins(where=[PluginDescriptor.WHERE_MOVIELIST]):
            self.entryguilist.append((str(index), str(p.name)))
            if config.AdvancedMovieSelection.red.value == str(p.name):
                red_selectedindex = str(index)
            if config.AdvancedMovieSelection.green.value == str(p.name):
                green_selectedindex = str(index)
            if config.AdvancedMovieSelection.yellow.value == str(p.name):
                yellow_selectedindex = str(index)
            if config.AdvancedMovieSelection.blue.value == str(p.name):
                blue_selectedindex = str(index)
            index = index + 1
        
        self.redchoice = ConfigSelection(default=red_selectedindex, choices=self.entryguilist)
        self.greenchoice = ConfigSelection(default=green_selectedindex, choices=self.entryguilist)
        self.yellowchoice = ConfigSelection(default=yellow_selectedindex, choices=self.entryguilist)
        self.bluechoice = ConfigSelection(default=blue_selectedindex, choices=self.entryguilist)
        self.buttoncaptionchoice = ConfigSelection(default=buttoncaptionchoice_selectedindex, choices=self.entryguilist3)
        self.homebuttontextchoice = ConfigSelection(default=hometext_selectedindex, choices=self.entryguilist2)
        self.bookmark1buttontextchoice = ConfigSelection(default=bookmark1buttontext_selectedindex, choices=self.entryguilist2)
        self.bookmark2buttontextchoice = ConfigSelection(default=bookmark2buttontext_selectedindex, choices=self.entryguilist2)
        self.bookmark3buttontextchoice = ConfigSelection(default=bookmark3buttontext_selectedindex, choices=self.entryguilist2)
        
        ConfigListScreen.__init__(self, [])
        self.initConfigList()
        
        self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
        {
            "green": self.keySave,
            "yellow": self.ownname,
            "cancel": self.cancel,
            "ok": self.ok,
        }, -2)
        self.onLayoutFinish.append(self.setCustomTitle)
        
    def setCustomTitle(self):
        self.setTitle(_("Movie Quick Button Setup"))

    def initConfigList(self):
        hometmp = config.movielist.videodirs.value
        homedefault = config.AdvancedMovieSelection.homepath.value
        if homedefault not in hometmp:
            hometmp = hometmp[:]
            hometmp.append(homedefault)
        self.homepath_dirname = ConfigSelection(default=homedefault, choices=hometmp)
        hometmp = config.movielist.videodirs.value
        homedefault = config.AdvancedMovieSelection.homepath.value

        book1tmp = config.movielist.videodirs.value
        book1default = config.AdvancedMovieSelection.bookmark1path.value
        if book1default not in book1tmp:
            book1tmp = book1tmp[:]
            book1tmp.append(book1default)
        self.bookmark1_dirname = ConfigSelection(default=book1default, choices=book1tmp)
        book1tmp = config.movielist.videodirs.value
        book1default = config.AdvancedMovieSelection.bookmark1path.value

        book2tmp = config.movielist.videodirs.value
        book2default = config.AdvancedMovieSelection.bookmark2path.value
        if book2default not in book2tmp:
            book2tmp = book2tmp[:]
            book2tmp.append(book2default)
        self.bookmark2_dirname = ConfigSelection(default=book2default, choices=book2tmp)
        book2tmp = config.movielist.videodirs.value
        book2default = config.AdvancedMovieSelection.bookmark2path.value

        book3tmp = config.movielist.videodirs.value
        book3default = config.AdvancedMovieSelection.bookmark3path.value
        if book3default not in book3tmp:
            book3tmp = book3tmp[:]
            book3tmp.append(book3default)
        self.bookmark3_dirname = ConfigSelection(default=book3default, choices=book3tmp)
        book3tmp = config.movielist.videodirs.value
        book3default = config.AdvancedMovieSelection.bookmark3path.value

        self.list = []
        self.redkey = getConfigListEntry(_("Assigned to red key"), self.redchoice)
        self.list.append(self.redkey)
        self.greenkey = getConfigListEntry(_("Assigned to green key"), self.greenchoice)
        self.list.append(self.greenkey)
        self.yellowkey = getConfigListEntry(_("Assigned to yellow key"), self.yellowchoice)
        self.list.append(self.yellowkey)
        self.bluekey = getConfigListEntry(_("Assigned to blue key"), self.bluechoice)
        self.list.append(self.bluekey)
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
        self.homepath = getConfigListEntry(_("Home path"), self.homepath_dirname)
        self.list.append(self.homepath)
        self.bookmark1 = getConfigListEntry(_("Bookmark 1 path"), self.bookmark1_dirname)
        self.list.append(self.bookmark1)
        self.bookmark2 = getConfigListEntry(_("Bookmark 2 path"), self.bookmark2_dirname)
        self.list.append(self.bookmark2)
        self.bookmark3 = getConfigListEntry(_("Bookmark 3 path"), self.bookmark3_dirname)
        self.list.append(self.bookmark3)
        self["config"].setList(self.list)
        if not self.selectionChanged in self["config"].onSelectionChanged:
            self["config"].onSelectionChanged.append(self.selectionChanged)
            
    def selectionChanged(self):
        current = self["config"].getCurrent()
        if current == self.bookmark_3_button_text:
            self.disableOKIcon()
        elif current == self.homepath:
            self.enableOKIcon()
        elif current == self.bookmark1:
            self.enableOKIcon()
        elif current == self.bookmark2:
            self.enableOKIcon()
        elif current == self.bookmark3:
            self.enableOKIcon()
        elif current == self.redkey:
            self.disableOKIcon()

    def enableOKIcon(self):
        self["OKIcon"].show()

    def disableOKIcon(self):
        self["OKIcon"].hide()

    def ok(self):
        currentry = self["config"].getCurrent()
        self.lastvideodirs = config.movielist.videodirs.value
        if currentry == self.homepath:
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
        else:
            self.keySave()                 

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
                
    def keySave(self):
        self["config"].getCurrent()
        config.AdvancedMovieSelection.buttoncaption.value = self.entryguilist3[int(self.buttoncaptionchoice.value)][1]
        config.AdvancedMovieSelection.homepath.value = self.homepath_dirname.value
        config.AdvancedMovieSelection.bookmark1path.value = self.bookmark1_dirname.value
        config.AdvancedMovieSelection.bookmark2path.value = self.bookmark2_dirname.value
        config.AdvancedMovieSelection.bookmark3path.value = self.bookmark3_dirname.value            
        config.AdvancedMovieSelection.red.value = self.entryguilist[int(self.redchoice.value)][1]
        config.AdvancedMovieSelection.green.value = self.entryguilist[int(self.greenchoice.value)][1]
        config.AdvancedMovieSelection.yellow.value = self.entryguilist[int(self.yellowchoice.value)][1]
        config.AdvancedMovieSelection.blue.value = self.entryguilist[int(self.bluechoice.value)][1]
        config.AdvancedMovieSelection.hometext.value = self.entryguilist2[int(self.homebuttontextchoice.value)][1]
        config.AdvancedMovieSelection.bookmark1text.value = self.entryguilist2[int(self.bookmark1buttontextchoice.value)][1]
        config.AdvancedMovieSelection.bookmark2text.value = self.entryguilist2[int(self.bookmark2buttontextchoice.value)][1]
        config.AdvancedMovieSelection.bookmark3text.value = self.entryguilist2[int(self.bookmark3buttontextchoice.value)][1]
        config.AdvancedMovieSelection.buttoncaption.save()
        config.AdvancedMovieSelection.homepath.save()
        config.AdvancedMovieSelection.bookmark1path.save()
        config.AdvancedMovieSelection.bookmark2path.save()
        config.AdvancedMovieSelection.bookmark3path.save()
        config.AdvancedMovieSelection.red.save()
        config.AdvancedMovieSelection.green.save()
        config.AdvancedMovieSelection.yellow.save()
        config.AdvancedMovieSelection.blue.save()
        config.AdvancedMovieSelection.hometext.save()
        config.AdvancedMovieSelection.bookmark1text.save()
        config.AdvancedMovieSelection.bookmark2text.save()
        config.AdvancedMovieSelection.bookmark3text.save()
        config.AdvancedMovieSelection.save()
        configfile.save()
        if self.csel:
            self.csel.updateButtonText()
        self.close()

    def getStaticName(self, list, value):
        for index, text in list:
            if text == value:
                return index
        return "0"

    def cancel(self):
        self.close()

    def ownname(self):
        self.session.openWithCallback(self.cancel, AdvancedMovieSelectionOwnButtonName)

class AdvancedMovieSelectionOwnButtonName(Screen, ConfigListScreen):        
    def __init__(self, session):
        Screen.__init__(self, session)
        self.skinName = SkinTools.appendResolution("AdvancedMovieSelectionOwnButtonName")
        self.homebutton = None
        self.bookmark1button = None
        self.bookmark2button = None
        self.bookmark3button = None
        self["setupActions"] = ActionMap(["ColorActions", "OkCancelActions"],
        {
            "red": self.keySave,
            "cancel": self.keyCancel
        }, -2) 
        self["VirtualKB"] = ActionMap(["VirtualKeyboardActions" ],
        {
            "showVirtualKeyboard": self.KeyText,
        }, -1)
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session)
        self["menu"] = List(self.list)
        self["help"] = StaticText()
        self["key_red"] = StaticText(_("Save/Close"))
        self["VKeyIcon"] = Pixmap()
        self["HelpWindow"] = Pixmap()
        self["VKeyIcon"].hide()
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
        
    def createSetup(self, retval=None):
        self.list = []
        self.homebutton = getConfigListEntry(_("Home button description:"), config.AdvancedMovieSelection.homeowntext)
        self.bookmark1button = getConfigListEntry(_("Bookmark 1 button description:"), config.AdvancedMovieSelection.bookmark1owntext)
        self.bookmark2button = getConfigListEntry(_("Bookmark 2 button description:"), config.AdvancedMovieSelection.bookmark2owntext)
        self.bookmark3button = getConfigListEntry(_("Bookmark 3 button description:"), config.AdvancedMovieSelection.bookmark3owntext)
        self.list.append(self.homebutton)
        self.list.append(self.bookmark1button)
        self.list.append(self.bookmark2button)
        self.list.append(self.bookmark3button)
        self["config"].list = self.list
        self["config"].l.setList(self.list)
        if not self.selectionChanged in self["config"].onSelectionChanged:
            self["config"].onSelectionChanged.append(self.selectionChanged)

    def selectionChanged(self):
        current = self["config"].getCurrent()
        if current == self.homebutton:
            self["help"].setText(_("Here you can give the home button a special name. After saving the changes color key settings will be closed, reopen it then the changes is to selection."))
            self.enableVKeyIcon()
            self.showKeypad()
        elif current == self.bookmark1button:
            self["help"].setText(_("Here you can give the bookmark 1 button a special name. After saving the changes color key settings will be closed, reopen it then the changes is to selection."))
            self.enableVKeyIcon()
            self.showKeypad()
        elif current == self.bookmark2button:
            self["help"].setText(_("Here you can give the bookmark 2 button a special name. After saving the changes color key settings will be closed, reopen it then the changes is to selection."))
            self.enableVKeyIcon()
            self.showKeypad()
        elif current == self.bookmark3button:
            self["help"].setText(_("Here you can give the bookmark 3 button a special name. After saving the changes color key settings will be closed, reopen it then the changes is to selection."))
            self.enableVKeyIcon()
            self.showKeypad()

    def enableVKeyIcon(self):
        self["VKeyIcon"].show()
        self["VirtualKB"].setEnabled(True)

    def disableVKeyIcon(self):
        self["VKeyIcon"].hide()
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
        print "cancel"
        if self["config"].isChanged():
            self.hideKeypad()
            self.session.openWithCallback(self.cancelConfirm, MessageBox, _("Really close without saving settings?"))
        else:
            self.close()

    def keySave(self):
        print "saving"
        ConfigListScreen.keySave(self)
