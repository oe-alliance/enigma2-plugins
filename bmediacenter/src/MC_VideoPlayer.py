from enigma import iPlayableService, eTimer, eWidget, eRect, eServiceReference, iServiceInformation
from Screens.Screen import Screen
from Screens.ServiceInfo import ServiceInfoList, ServiceInfoListEntry
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap, NumberActionMap, HelpableActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.Button import Button
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import *

from Tools.Directories import resolveFilename, fileExists, pathExists, createDir, SCOPE_MEDIA
from Components.FileList import FileList
from Components.AVSwitch import AVSwitch
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarAudioSelection, InfoBarCueSheetSupport, InfoBarNotifications, InfoBarShowHide, InfoBarServiceErrorPopupSupport, InfoBarPVRState, InfoBarSimpleEventView, InfoBarServiceNotifications, InfoBarMoviePlayerSummarySupport, InfoBarSubtitleSupport, InfoBarTeletextPlugin
from GlobalFunctions import MC_FolderOptions, MC_FavoriteFolders, MC_FavoriteFolderAdd, MC_FavoriteFolderEdit, MC_VideoInfoView
import os
from os import path as os_path

config.plugins.mc_vp = ConfigSubsection()
config.plugins.mc_vp.showPreview = ConfigYesNo(default=True)
config.plugins.mc_vp.preview_delay = ConfigInteger(default=5, limits=(1, 99))
config.plugins.mc_vp.lastDir = ConfigText(default=resolveFilename(SCOPE_MEDIA))

def getAspect():
	val = AVSwitch().getAspectRatioSetting()
	return val/2
#-------------------------------------------------------#
class MC_VideoPlayer(Screen, HelpableScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
#		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
#		self.session.nav.stopService()
		self["key_red"] = Button(_("Favorites"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button(_("Settings"))
		self["currentfolder"] = Label("")
		self["currentfavname"] = Label("")
		self.curfavfolder = -1
		
		self["actions"] = HelpableActionMap(self, "MC_VideoPlayerActions", 
			{
				"ok": (self.KeyOk, "Play selected file"),
				"cancel": (self.Exit, "Exit Video Player"),
				"left": (self.leftUp, "List Top"),
				"right": (self.rightDown, "List Bottom"),
				"up": (self.up, "List up"),
				"down": (self.down, "List down"),
				"menu": (self.KeyMenu, "File / Folder Options"),
				"info": (self.showFileInfo, "Show File Info"),
				"nextBouquet": (self.NextFavFolder, "Next Favorite Folder"),
				"prevBouquet": (self.PrevFavFolder, "Previous Favorite Folder"),
				"red": (self.FavoriteFolders, "Favorite Folders"),
				"blue": (self.KeySettings, "Settings"),
			}, -2)
		self.aspect = getAspect()
		currDir = config.plugins.mc_vp.lastDir.value
		if not pathExists(currDir):
			currDir = "/"
		self["currentfolder"].setText(str(currDir))
		self.filelist = FileList(currDir, useServiceRef = True, showDirectories = True, showFiles = True, matchingPattern = "(?i)^.*\.(ts|vob|mpg|mpeg|avi|mkv|dat|iso|mp4|flv|divx)")
		self["filelist"] = self.filelist
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evUser+11: self.__evDecodeError,
				iPlayableService.evUser+12: self.__evPluginError
			})
	def up(self):
		self["filelist"].up()
	def down(self):
		self["filelist"].down()
	def leftUp(self):
		self["filelist"].pageUp()
	def rightDown(self):
		self["filelist"].pageDown()
	def NextFavFolder(self):
		if self.curfavfolder + 1 < config.plugins.mc_favorites.foldercount.value:
			self.curfavfolder += 1
			self.favname = config.plugins.mc_favorites.folders[self.curfavfolder].name.value
			self.folder = config.plugins.mc_favorites.folders[self.curfavfolder].basedir.value
			self["currentfolder"].setText(("%s") % (self.folder))
			self["currentfavname"].setText(("%s") % (self.favname))
			if os.path.exists(self.folder) == True:
				self["filelist"].changeDir(self.folder)
		else:
			return
	def PrevFavFolder(self):
		if self.curfavfolder <= 0:
			return
		else:
			self.curfavfolder -= 1
			self.favname = config.plugins.mc_favorites.folders[self.curfavfolder].name.value
			self.folder = config.plugins.mc_favorites.folders[self.curfavfolder].basedir.value
			self["currentfolder"].setText(("%s") % (self.folder))
			self["currentfavname"].setText(("%s") % (self.favname))
			if os.path.exists(self.folder) == True:
				self["filelist"].changeDir(self.folder)
	def showFileInfo(self):
		if self["filelist"].canDescent():
			return
		else:
			self.session.open(MC_VideoInfoView, self["filelist"].getCurrentDirectory() + self["filelist"].getFilename() , self["filelist"].getFilename(), self["filelist"].getServiceRef())
	def KeyOk(self):
		if self.filelist.canDescent():
			self.filelist.descent()
		else:
			self.session.open(BonkelPlayer, self["filelist"].getServiceRef())
			# screen adjustment
			os.system("echo " + hex(config.plugins.mc_globalsettings.dst_top.value)[2:] + " > /proc/stb/vmpeg/0/dst_top")
			os.system("echo " + hex(config.plugins.mc_globalsettings.dst_left.value)[2:] + " > /proc/stb/vmpeg/0/dst_left")
			os.system("echo " + hex(config.plugins.mc_globalsettings.dst_width.value)[2:] + " > /proc/stb/vmpeg/0/dst_width")
			os.system("echo " + hex(config.plugins.mc_globalsettings.dst_height.value)[2:] + " > /proc/stb/vmpeg/0/dst_height")
	def KeyMenu(self):
		if self["filelist"].canDescent():
			if self.filelist.getCurrent()[0][1]:
				self.currentDirectory = self.filelist.getCurrent()[0][0]
				if self.currentDirectory is not None:
					foldername = self.currentDirectory.split('/')
					foldername = foldername[-2]
					self.session.open(MC_FolderOptions,self.currentDirectory, foldername)
	def returnVal(self, val=0):
		if val > 0:
			for x in self.filelist.getFileList():
				if x[0][1] == True:
					val += 1
			self.filelist.moveToIndex(val)
	def JumpToFolder(self, jumpto = None):
		if jumpto is None:
			return
		else:
			self["filelist"].changeDir(jumpto)
			self["currentfolder"].setText(("%s") % (jumpto))
	def FavoriteFolders(self):
		self.session.openWithCallback(self.JumpToFolder, MC_FavoriteFolders)
	def KeySettings(self):
		self.session.open(VideoPlayerSettings)
	def __evDecodeError(self):
		currPlay = self.session.nav.getCurrentService()
		sVideoType = currPlay.info().getInfoString(iServiceInformation.sVideoType)
		print "[__evDecodeError] video-codec %s can't be decoded by hardware" % (sVideoType)
		self.session.open(MessageBox, _("This Dreambox can't decode %s video streams!") % sVideoType, type = MessageBox.TYPE_INFO,timeout = 10 )
	def __evPluginError(self):
		currPlay = self.session.nav.getCurrentService()
		message = currPlay.info().getInfoString(iServiceInformation.sUser+12)
		print "[__evPluginError]" , message
		self.session.open(MessageBox, ("GStreamer Error: missing %s") % message, type = MessageBox.TYPE_INFO,timeout = 20 )
	def Exit(self):
		if self.filelist.getCurrentDirectory() is None:
			config.plugins.mc_vp.lastDir.value = "/"
		else:
			config.plugins.mc_vp.lastDir.value = self.filelist.getCurrentDirectory()
		config.plugins.mc_vp.save()
		self.close()
class BonkelPlayer(InfoBarShowHide, InfoBarSeek, InfoBarAudioSelection, HelpableScreen, InfoBarNotifications, InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, InfoBarSimpleEventView, InfoBarMoviePlayerSummarySupport, InfoBarSubtitleSupport, Screen, InfoBarTeletextPlugin, InfoBarServiceErrorPopupSupport):
	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True
	def __init__(self, session, service, slist = None, lastservice = None):
		Screen.__init__(self, session)
		InfoBarSubtitleSupport.__init__(self)
		InfoBarAudioSelection.__init__(self)
		InfoBarSeek.__init__(self, actionmap = "MediaCenterSeekActions")
		self["actions"] = HelpableActionMap(self, "MoviePlayerActions",
			{
				"leavePlayer": (self.leavePlayer, "leave movie player...")
			})
		self["MediaPlayerActions"] = HelpableActionMap(self, "MediaPlayerActions",
			{
				"subtitles": (self.subtitleSelection, "Subtitle selection"),
				"prevBouquet": (self.previousMarkOrEntry, "play from previous mark or playlist entry"),
				"nextBouquet": (self.nextMarkOrEntry, "play from next mark or playlist entry"),
				"play": (self.showPlaylist, "show playlist"),
			}, -2)
		self["actions"] = HelpableActionMap(self, "MC_BonkelPlayerActions", 
			{
				"leavePlayer": (self.leavePlayer, "leave movie player..."),
			}, -2)
		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
			{
				"yellow": (self.audioSelection, "Audio Menu"),				
			})
		for x in HelpableScreen, InfoBarShowHide, InfoBarSeek, InfoBarAudioSelection, InfoBarNotifications, InfoBarSimpleEventView, InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, InfoBarMoviePlayerSummarySupport, InfoBarSubtitleSupport, InfoBarTeletextPlugin, InfoBarServiceErrorPopupSupport:
			x.__init__(self)
		self.session.nav.playService(service)
		self.returning = False
	def showPlaylist(self):
		self.setSeekState(self.SEEK_STATE_PLAY)
	def nextMarkOrEntry(self):
		return
	def previousMarkOrEntry(self):
		return
	def leavePlayer(self):
		self.is_closing = True
		self.session.nav.stopService()
		self.close(0)
	def doEofInternal(self, playing):
		self.session.nav.playService(None)
		self.is_closing = True
		self.close(1)
	def audioSelection(self):
		from Screens.AudioSelection import AudioSelection
		self.session.openWithCallback(self.audioSelected, AudioSelection)
	def subtitleSelection(self):
		from Screens.AudioSelection import SubtitleSelection
		self.session.open(SubtitleSelection, self)
#-------------------------------------------------------#
class VideoPlayerSettings(Screen, ConfigListScreen):
	skin = """
		<screen position="160,220" size="400,120" title="Media Center - VideoPlayer Settings" >
			<widget name="config" position="10,10" size="380,100" />
		</screen>"""
	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = NumberActionMap(["SetupActions","OkCancelActions"],
		{
			"ok": self.keyOK,
			"cancel": self.keyOK
		}, -1)
		self.list = []
		self.list.append(getConfigListEntry(_("Autoplay Enable"), config.plugins.mc_vp.showPreview))
		self.list.append(getConfigListEntry(_("Autoplay Delay"), config.plugins.mc_vp.preview_delay))
		ConfigListScreen.__init__(self, self.list, session)
	def keyOK(self):
		config.plugins.mc_vp.save()
		self.close()