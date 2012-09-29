from enigma import iPlayableService, eTimer, eWidget, eRect, eServiceReference, iServiceInformation
from Screens.Screen import Screen
from Screens.ServiceInfo import ServiceInfoList, ServiceInfoListEntry
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap, NumberActionMap, HelpableActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.Button import Button
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import *
from Tools.Directories import resolveFilename, fileExists, pathExists, createDir, SCOPE_MEDIA
from Components.FileList import FileList
from Components.AVSwitch import AVSwitch
from Screens.InfoBarGenerics import InfoBarMenu, InfoBarExtensions, InfoBarPiP, InfoBarPlugins, InfoBarSubserviceSelection, InfoBarSeek, InfoBarAudioSelection, InfoBarCueSheetSupport, InfoBarNotifications, \
	InfoBarShowHide, InfoBarServiceErrorPopupSupport, InfoBarPVRState, InfoBarSimpleEventView, delResumePoint, setResumePoint, \
	InfoBarServiceNotifications, InfoBarMoviePlayerSummarySupport, InfoBarAspectSelection, InfoBarSubtitleSupport, InfoBarTeletextPlugin
from GlobalFunctions import MC_FolderOptions, MC_FavoriteFolders, MC_FavoriteFolderAdd, MC_FavoriteFolderEdit, MC_VideoInfoView
import os
from os import system

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
		inhibitDirs = ["/bin", "/boot", "/dev", "/dev.static", "/etc", "/lib" , "/proc", "/ram", "/root" , "/sbin", "/sys", "/tmp", "/usr", "/var"]
		self.filelist = FileList(currDir, useServiceRef = True, showDirectories = True, showFiles = True, matchingPattern = "(?i)^.*\.(ts|vob|mpg|mpeg|avi|mkv|dat|iso|mp4|flv|divx|mov|wmv|m2ts)", inhibitDirs = inhibitDirs,)
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
class BonkelPlayer(InfoBarBase, InfoBarShowHide, \
		InfoBarMenu, \
		InfoBarSeek, InfoBarAudioSelection, HelpableScreen, InfoBarNotifications,
		InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, InfoBarSimpleEventView,
		InfoBarMoviePlayerSummarySupport, InfoBarSubtitleSupport, Screen, InfoBarTeletextPlugin,
		InfoBarAspectSelection, InfoBarSubserviceSelection,
		InfoBarServiceErrorPopupSupport, InfoBarExtensions, InfoBarPlugins, InfoBarPiP):
	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True
	def __init__(self, session, service, slist = None, lastservice = None):
		Screen.__init__(self, session)
		InfoBarAspectSelection.__init__(self)
		self["actions"] = HelpableActionMap(self, "MoviePlayerActions",
			{
				"leavePlayer": (self.leavePlayer, _("leave movie player...")),
				"leavePlayerOnExit": (self.leavePlayerOnExit, _("leave movie player..."))
			})
		self["DirectionActions"] = HelpableActionMap(self, "DirectionActions",
			{
				"left": self.left,
				"right": self.right
			}, prio = -2)
		self.allowPiP = True
		for x in HelpableScreen, InfoBarShowHide, InfoBarMenu, \
				InfoBarBase, InfoBarSeek, \
				InfoBarAudioSelection, InfoBarNotifications, InfoBarSimpleEventView, \
				InfoBarServiceNotifications, InfoBarPVRState, InfoBarCueSheetSupport, \
				InfoBarMoviePlayerSummarySupport, InfoBarSubtitleSupport, \
				InfoBarTeletextPlugin, InfoBarServiceErrorPopupSupport, InfoBarExtensions, \
				InfoBarPlugins, InfoBarPiP:
			x.__init__(self)
		self.servicelist = slist
		self.lastservice = lastservice or session.nav.getCurrentlyPlayingServiceReference()
		session.nav.playService(service)
		self.cur_service = service
		self.returning = False
		self.onClose.append(self.__onClose)
	def __onClose(self):
		from Screens.MovieSelection import Playlist
		Playlist.clearPlayList()
		self.session.nav.playService(self.lastservice)
	def handleLeave(self, how):
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
					(_("No"), "continue"),
					(_("No, but restart from begin"), "restart")
				)
			from Screens.ChoiceBox import ChoiceBox
			self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Stop playing this movie?"), list = list)
		else:
			self.leavePlayerConfirmed([True, how])
	def leavePlayer(self):
		setResumePoint(self.session)
		self.close()
	def leavePlayerOnExit(self, answer = None):
		if answer == True:
			setResumePoint(self.session)
			self.handleLeave("quit")
		elif self.shown:
			self.hide()
		elif answer is None:
			self.session.openWithCallback(self.leavePlayerOnExit, MessageBox, _("Exit Movieplayer?"), MessageBox.TYPE_YESNO, simple = True)
	def leavePlayerConfirmed(self, answer):
		answer = answer and answer[1]
		if answer == "restart":
			self.doSeek(0)
			self.setSeekState(self.SEEK_STATE_PLAY)
		elif answer in ("playlist","playlistquit","loop"):
			( next_service, item , lenght ) = self.nextPlaylistService(self.cur_service)
			if next_service is not None:
				if config.usage.next_movie_msg.value:
					self.displayPlayedName(next_service, item, lenght)
				self.session.nav.playService(next_service)
				self.cur_service = next_service
			else:
				if answer == "playlist":
					self.leavePlayerConfirmed([True,"movielist"])
				elif answer == "loop" and lenght > 0:
					self.leavePlayerConfirmed([True,"loop"])
				else:
					self.leavePlayerConfirmed([True,"quit"])
	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing :
			return
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
		if ref:
			delResumePoint(ref)
		self.handleLeave(config.usage.on_movie_eof.value)
	def up(self):
		slist = self.servicelist
		if slist and slist.dopipzap:
			slist.moveUp()
			self.session.execDialog(slist)
	def down(self):
		slist = self.servicelist
		if slist and slist.dopipzap:
			slist.moveDown()
			self.session.execDialog(slist)
	def right(self):
		# XXX: gross hack, we do not really seek if changing channel in pip :-)
		slist = self.servicelist
		if slist and slist.dopipzap:
			# XXX: We replicate InfoBarChannelSelection.zapDown here - we shouldn't do that
			if slist.inBouquet():
				prev = slist.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value and slist.atEnd():
							slist.nextBouquet()
						else:
							slist.moveDown()
						cur = slist.getCurrentSelection()
						if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
							break
			else:
				slist.moveDown()
			slist.zap(enable_pipzap = True)
		else:
			InfoBarSeek.seekFwd(self)
	def left(self):
		slist = self.servicelist
		if slist and slist.dopipzap:
			# XXX: We replicate InfoBarChannelSelection.zapUp here - we shouldn't do that
			if slist.inBouquet():
				prev = slist.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value:
							if slist.atBegin():
								slist.prevBouquet()
						slist.moveUp()
						cur = slist.getCurrentSelection()
						if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
							break
			else:
				slist.moveUp()
			slist.zap(enable_pipzap = True)
		else:
			InfoBarSeek.seekBack(self)
	def showPiP(self):
		slist = self.servicelist
		if self.session.pipshown:
			if slist and slist.dopipzap:
				slist.togglePipzap()
			del self.session.pip
			self.session.pipshown = False
		else:
			from Screens.PictureInPicture import PictureInPicture
			self.session.pip = self.session.instantiateDialog(PictureInPicture)
			self.session.pip.show()
			self.session.pipshown = True
			self.session.pip.playService(slist.getCurrentSelection())
	def swapPiP(self):
		pass
	def nextPlaylistService(self, service):
		from MovieSelection import Playlist
		playlist = Playlist.getPlayList()
		for i, item in enumerate(playlist):
			if item == service:
				i += 1
				if i < len(playlist):
					return (playlist[i], i+1, len(playlist))
				elif config.usage.on_movie_eof.value == "loop":
					return (playlist[0], 1, len(playlist))
		return ( None, 0, 0 )
	def displayPlayedName(self, ref, index, n):
		from Tools import Notifications
		Notifications.AddPopup(text = _("%s/%s: %s") % (index, n, self.ref2HumanName(ref)), type = MessageBox.TYPE_INFO, timeout = 5)
	def ref2HumanName(self, ref):
		from enigma import eServiceCenter
		return eServiceCenter.getInstance().info(ref).getName(ref)
	def sleepTimer(self):
		from Screens.SleepTimerEdit import SleepTimerEdit
		self.session.open(SleepTimerEdit)
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
		self.list.append(getConfigListEntry(_("Autoplay Enable:"), config.plugins.mc_vp.showPreview))
		self.list.append(getConfigListEntry(_("Autoplay Delay:"), config.plugins.mc_vp.preview_delay))
		ConfigListScreen.__init__(self, self.list, session)
	def keyOK(self):
		config.plugins.mc_vp.save()
		self.close()