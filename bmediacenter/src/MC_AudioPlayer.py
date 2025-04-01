from os import system, remove, remove, listdir, walk
from os.path import split, dirname
from re import sub
from requests import get, exceptions
from six import ensure_str
from time import strftime
from twisted.internet.reactor import callInThread
from urllib.parse import quote
from xml.etree.ElementTree import fromstring as cet_fromstring

from enigma import eTimer, iServiceInformation, iPlayableService, ePicLoad, RT_VALIGN_CENTER, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, gFont, eListbox, ePoint, eListboxPythonMultiContent, eServiceCenter, getDesktop
from Components.Label import Label
from Components.Button import Button
from Components.Pixmap import Pixmap
from Components.MenuList import MenuList
from Components.Sources.List import List
from Components.ConfigList import ConfigList
from Components.FileList import FileList
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigYesNo, ConfigInteger, ConfigText, KEY_LEFT, KEY_RIGHT, KEY_0, getConfigListEntry
from Components.ScrollLabel import ScrollLabel
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ActionMap import ActionMap, NumberActionMap, HelpableActionMap
from Components.Playlist import PlaylistIOInternal, PlaylistIOM3U, PlaylistIOPLS
from ServiceReference import ServiceReference
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen
from Screens.InfoBarGenerics import InfoBarSeek
from Tools.Directories import resolveFilename, fileExists, pathExists, SCOPE_MEDIA, SCOPE_PLAYLIST, SCOPE_SKIN_IMAGE
from .__init__ import _  # for localized messages

config.plugins.mc_ap = ConfigSubsection()
config.plugins.mc_ap.showJpg = ConfigYesNo(default=True)
config.plugins.mc_ap.jpg_delay = ConfigInteger(default=10, limits=(5, 999))
config.plugins.mc_ap.repeat = ConfigSelection(default="off", choices=[("off", "off"), ("single", "single"), ("all", "all")])
config.plugins.mc_ap.lastDir = ConfigText(default=resolveFilename(SCOPE_MEDIA))

choiceList = [
	("0.0", _("Name ascending")),
	("0.1", _("Name descending")),
	("1.0", _("Date ascending")),
	("1.1", _("Date descending"))
]
choiceList = choiceList + [
	("2.0", _("Size ascending")),
	("2.1", _("Size descending"))
]
config.plugins.mc_ap_sortmode = ConfigSelection(default="0.0", choices=choiceList)


screensaverlist = [('default', _("default"))]
hddpath = "/hdd/saver/"
if pathExists(hddpath):
	files = listdir(hddpath)
	for x in files:
		if pathExists(hddpath + x):
			screensaverlist += [(hddpath + '%s/' % (x), _("%s") % (x))]
config.plugins.mc_ap.whichjpg = ConfigSelection(screensaverlist)
playlist = []
radirl = "http://radio.pervii.com/top_radio_"

FHD = getDesktop(0).size().width() == 1920

STATE_PLAY = 0
STATE_PAUSE = 1
STATE_STOP = 2
STATE_REWIND = 3
STATE_FORWARD = 4
STATE_NONE = 5


def getEncodedString(value):
	print("getEncodedString")
	print(value)
	returnValue = ""
	try:
		returnValue = value.encode("utf-8", 'ignore')
	except UnicodeDecodeError:
		try:
			returnValue = value.encode("iso8859-1", 'ignore')
		except UnicodeDecodeError:
			try:
				returnValue = value.decode("cp1252").encode("utf-8")
			except UnicodeDecodeError:
				returnValue = "n/a"
	return returnValue


mcpath = "/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/"


def PlaylistEntryComponent(serviceref, state=None):
	res = [serviceref]
	text = serviceref.getName()
	if text == "":
		text = split(serviceref.getPath().split('/')[-1])[1]
	if FHD:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 5, 3, 760, 32, 0, RT_VALIGN_CENTER, text))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 5, 2, 510, 22, 0, RT_VALIGN_CENTER, text))
	return res


class PlayList(MenuList):
	def __init__(self, enableWrapAround=False):
		MenuList.__init__(self, playlist, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont('Regular', 28 if FHD else 15))
		self.l.setItemHeight(40 if FHD else 23)
		MC_AudioPlayer.currPlaying = -1
		self.oldCurrPlaying = -1
		self.serviceHandler = eServiceCenter.getInstance()

	def clear(self):
		del self.list[:]
		self.l.setList(self.list)
		MC_AudioPlayer.currPlaying = -1
		self.oldCurrPlaying = -1

	def getSelection(self):
		return self.l.getCurrentSelection()[0]

	def addFile(self, serviceref):
		self.list.append(PlaylistEntryComponent(serviceref))

	def updateFile(self, index, newserviceref):
		if index < len(self.list):
			self.list[index] = PlaylistEntryComponent(newserviceref, STATE_NONE)

	def deleteFile(self, index):
		if MC_AudioPlayer.currPlaying >= index:
			MC_AudioPlayer.currPlaying -= 1
		del self.list[index]

	def setCurrentPlaying(self, index):
		self.oldCurrPlaying = MC_AudioPlayer.currPlaying
		MC_AudioPlayer.currPlaying = index
		self.moveToIndex(index)

	def updateState(self, state):
		if len(self.list) > self.oldCurrPlaying and self.oldCurrPlaying != -1:
			self.list[self.oldCurrPlaying] = PlaylistEntryComponent(self.list[self.oldCurrPlaying][0], STATE_NONE)
		if MC_AudioPlayer.currPlaying != -1 and MC_AudioPlayer.currPlaying < len(self.list):
			self.list[MC_AudioPlayer.currPlaying] = PlaylistEntryComponent(self.list[MC_AudioPlayer.currPlaying][0], state)
		self.updateList()

	def playFile(self):
		self.updateState(STATE_PLAY)

	def pauseFile(self):
		self.updateState(STATE_PAUSE)

	def stopFile(self):
		self.updateState(STATE_STOP)

	def rewindFile(self):
		self.updateState(STATE_REWIND)

	def forwardFile(self):
		self.updateState(STATE_FORWARD)
	GUI_WIDGET = eListbox

	def updateList(self):
		self.l.setList(self.list)

#	def getCurrentIndex(self):
#		return MC_AudioPlayer.currPlaying

	def getCurrentEvent(self):
		l = self.l.getCurrentSelection()
		return l and self.serviceHandler.info(l[0]).getEvent(l[0])

	def getCurrent(self):
		l = self.l.getCurrentSelection()
		return l and l[0]

	def getServiceRefList(self):
		return [x[0] for x in self.list]

	def __len__(self):
		return len(self.list)


class MC_AudioPlayer(Screen, HelpableScreen, InfoBarSeek):
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		InfoBarSeek.__init__(self, actionmap="MediaPlayerSeekActions")
		self.jpgList = []
		self.jpgIndex = 0
		self.jpgLastIndex = -1
		self.isVisible = True
		self.coverArtFileName = ""
		self["fileinfo"] = Label()
		self["text"] = Label(_("Lyrics"))
		self["coverArt"] = MediaPixmap()
		self["currentfolder"] = Label()
		self["currentfavname"] = Label()
		self.standardInfoBar = False
		self.ac3ON = False
		try:
			if config.av.downmix_ac3.value is False:
				config.av.downmix_ac3.value = True
				config.av.downmix_ac3.save()
				self.ac3ON = True
		except Exception as e:
			print("Media Center: no ac3")
		self["play"] = Pixmap()
		self["green"] = Pixmap()
		self["screensaver"] = MediaPixmap()
		self.PlaySingle = 0
		MC_AudioPlayer.STATE = "NONE"
		lstdir = []
		self.playlist = PlayList()
		MC_AudioPlayer.playlistplay = 0
		MC_AudioPlayer.currPlaying = -1
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evEOF: self.doEOF,
				iPlayableService.evStopped: self.StopPlayback,
				iPlayableService.evUser + 11: self.__evDecodeError,
				iPlayableService.evUser + 12: self.__evPluginError,
				iPlayableService.evUser + 13: self["coverArt"].embeddedCoverArt,
				iPlayableService.evUser + 14: self["screensaver"].screensaver
			})
		self["actions"] = HelpableActionMap(self, "MC_AudioPlayerActions",
			{
				"ok": (self.KeyOK, "Play selected file"),
				"playpause": (self.PlayPause, "Play / Pause"),
				"cancel": (self.Exit, "Exit Audio Player"),
				"left": (self.leftUp, "List Top"),
				"right": (self.rightDown, "List Bottom"),
				"up": (self.up, "List up"),
				"down": (self.down, "List down"),
				"menu": (self.showMenu, "File / Folder Options"),
				"video": (self.visibility, "Show / Hide Player"),
				"info": (self.showLyrics, "Lyrics"),
				"stop": (self.StopPlayback, "Stop Playback"),
				"red": (self.Playlists, "Playlists"),
				"green": (self.Repeat, "Repeat"),
				"yellow": (self.addFiletoPls, "Add file to playlist"),
				"blue": (self.Settings, "Settings"),
				"next": (self.KeyNext, "Next song"),
				"previous": (self.KeyPrevious, "Previous song"),
			}, -2)

		self.playlistparsers = {}
		self.addPlaylistParser(PlaylistIOM3U, "m3u")
		self.addPlaylistParser(PlaylistIOPLS, "pls")
		self.addPlaylistParser(PlaylistIOInternal, "e2pls")
		currDir = config.plugins.mc_ap.lastDir.value
		if not pathExists(currDir):
			currDir = "/"
		self["currentfolder"].setText(str(currDir))
		self.filelist = []
		self["filelist"] = []
		inhibitDirs = ["/bin", "/boot", "/dev", "/dev.static", "/etc", "/lib", "/proc", "/ram", "/root", "/sbin", "/sys", "/tmp", "/usr", "/var"]
		self.filelist = FileList(currDir, useServiceRef=True, showDirectories=True, showFiles=True, matchingPattern="(?i)^.*\.(mp2|mp3|wav|wave|wma|m4a|ogg|ra|flac|m3u|pls|e2pls)", additionalExtensions=None, sortDirs="0.0", sortFiles=config.plugins.mc_ap_sortmode.value, inhibitDirs=inhibitDirs)
		self["filelist"] = self.filelist
		self["filelist"].show()
		self.JpgTimer = eTimer()
		self.JpgTimer.callback.append(self.showBackgroundJPG)
		self.getJPG()
		self.FileInfoTimer = eTimer()
		self.FileInfoTimer.callback.append(self.updateFileInfo)
		self.onLayoutFinish.append(self.updategreen)

	def Repeat(self):
		if config.plugins.mc_ap.repeat.getValue() == "off":
			config.plugins.mc_ap.repeat.value = "single"
			self["green"].instance.setPixmapFromFile(mcpath + "icons/repeatonegreen.png")
		elif config.plugins.mc_ap.repeat.getValue() == "single":
			config.plugins.mc_ap.repeat.value = "all"
			self["green"].instance.setPixmapFromFile(mcpath + "icons/repeatallgreen.png")
		else:
			config.plugins.mc_ap.repeat.value = "off"
			self["green"].instance.setPixmapFromFile(mcpath + "icons/repeatoffgreen.png")
		config.plugins.mc_ap.save()

	def updategreen(self):
		if config.plugins.mc_ap.repeat.getValue() == "all":
			self["green"].instance.setPixmapFromFile(mcpath + "icons/repeatallgreen.png")
		elif config.plugins.mc_ap.repeat.getValue() == "single":
			self["green"].instance.setPixmapFromFile(mcpath + "icons/repeatonegreen.png")
		else:
			return

	def unlockShow(self):
		return

	def lockShow(self):
		return

	def up(self):
		self["filelist"].up()
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()

	def down(self):
		self["filelist"].down()
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()

	def leftUp(self):
		self["filelist"].pageUp()
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()

	def rightDown(self):
		self["filelist"].pageDown()
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()

	def KeyOK(self):
		if self["filelist"].canDescent():
			if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
			self.filelist.descent()
			self["currentfolder"].setText(str(self.filelist.getCurrentDirectory()))
		else:
			if self.filelist.getServiceRef().type == 4098:  # playlist
				ServiceRef = self.filelist.getServiceRef()
				extension = ServiceRef.getPath()[ServiceRef.getPath().rfind('.') + 1:]
				if extension in self.playlistparsers:
					self.playlist.clear()
					playlist = self.playlistparsers[extension]()
					list = playlist.open(ServiceRef.getPath())
					for x in list:
						self.playlist.addFile(x.ref)
				self.playlist.updateList()
				MC_AudioPlayer.currPlaying = 0
				self.PlayServicepls()
			else:
				self.PlaySingle = 1
				self.PlayService()

	def PlayPause(self):
		if MC_AudioPlayer.STATE == "PLAY":
			service = self.session.nav.getCurrentService()
			pausable = service.pause()
			pausable.pause()
			MC_AudioPlayer.STATE = "PAUSED"
			self["play"].instance.setPixmapFromFile(mcpath + "icons/pause_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
		elif MC_AudioPlayer.STATE == "PAUSED":
			service = self.session.nav.getCurrentService()
			pausable = service.pause()
			pausable.unpause()
			MC_AudioPlayer.STATE = "PLAY"
			self["play"].instance.setPixmapFromFile(mcpath + "icons/play_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
		else:
			self.KeyOK()

	def KeyNext(self):
		if MC_AudioPlayer.STATE != "NONE":
			if config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
			if MC_AudioPlayer.playlistplay == 1:
				next = self.playlist.getCurrentIndex() + 1
				if next < len(self.playlist):
					MC_AudioPlayer.currPlaying = MC_AudioPlayer.currPlaying + 1
				else:
					MC_AudioPlayer.currPlaying = 0
				self.PlayServicepls()
			else:
				self.down()
				self.PlayService()

	def KeyPrevious(self):
		if MC_AudioPlayer.STATE != "NONE":
			if config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
			if MC_AudioPlayer.playlistplay == 1:
				next = self.playlist.getCurrentIndex() - 1
				if next != -1:
					MC_AudioPlayer.currPlaying = MC_AudioPlayer.currPlaying - 1
				else:
					MC_AudioPlayer.currPlaying = 0
				self.PlayServicepls()
			else:
				self.up()
				self.PlayService()

	def visibility(self, force=1):
		if self.isVisible is True:
			self.isVisible = False
			self.hide()
		else:
			self.isVisible = True
			self.show()

	def Playlists(self):
		self.session.openWithCallback(self.updd, MC_AudioPlaylist)

	def updd(self):
		self.updateFileInfo()
		self.filelist.refresh()
		if MC_AudioPlayer.STATE == "PLAY":
			self["play"].instance.setPixmapFromFile(mcpath + "icons/play_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
		elif MC_AudioPlayer.STATE == "PAUSED":
			self["play"].instance.setPixmapFromFile(mcpath + "icons/pause_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
		elif MC_AudioPlayer.STATE == "NONE":
			self["play"].instance.setPixmapFromFile(mcpath + "icons/stop_enabled.png")
		else:
			return

	def PlayService(self):
		playlistplay = 0
		self.JpgTimer.stop()
		self.session.nav.playService(self["filelist"].getServiceRef())
		MC_AudioPlayer.STATE = "PLAY"
		self.FileInfoTimer.start(2000, True)
		self["play"].instance.setPixmapFromFile(mcpath + "icons/play_enabled.png")
		path = self["filelist"].getCurrentDirectory()
		self["coverArt"].updateCoverArt(path)
		if config.plugins.mc_ap.showJpg.getValue():
			time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
			self.JpgTimer.start(time, True)

	def PlayServicepls(self):
		MC_AudioPlayer.playlistplay = 1
		x = self.playlist.getCurrentIndex()
		x = len(self.playlist)
		self.session.nav.playService(self.playlist.getServiceRefList()[self.playlist.getCurrentIndex()])
		MC_AudioPlayer.STATE = "PLAY"
		self.FileInfoTimer.start(2000, True)
		self["play"].instance.setPixmapFromFile(mcpath + "icons/play_enabled.png")
		if config.plugins.mc_ap.showJpg.getValue():
			time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
			self.JpgTimer.start(time, True)
		#path = self["filelist"].getFilename()
		#self["coverArt"].updateCoverArt(path)

	def StopPlayback(self):
		if self.isVisible is False:
			self.show()
			self.isVisible = True
		if self.session.nav.getCurrentService() is None:
			return
		else:
			self.session.nav.stopService()
			if config.plugins.mc_ap.showJpg.getValue():
				self.JpgTimer.stop()
				self["screensaver"].showDefaultCover()
			MC_AudioPlayer.STATE = "NONE"
			self["play"].instance.setPixmapFromFile(mcpath + "icons/stop_enabled.png")

	def JumpToFolder(self, jumpto=None):
		if jumpto is None:
			return
		else:
			self["filelist"].changeDir(jumpto)
			self["currentfolder"].setText(("%s") % (jumpto))

	def updateFileInfo(self):
		currPlay = self.session.nav.getCurrentService()
		if currPlay is not None:
			sTitle = currPlay.info().getInfoString(iServiceInformation.sTagTitle)
			sArtist = currPlay.info().getInfoString(iServiceInformation.sTagArtist)
			sAlbum = currPlay.info().getInfoString(iServiceInformation.sTagAlbum)
			sGenre = currPlay.info().getInfoString(iServiceInformation.sTagGenre)
			sComment = currPlay.info().getInfoString(iServiceInformation.sTagComment)
			sYear = currPlay.info().getInfoString(iServiceInformation.sTagDate)
			if sTitle == "":
				sTitle = currPlay.info().getName().split('/')[-1]
			self["fileinfo"].setText(_("Title: ") + sTitle + _("\nArtist: ") + sArtist + _("\nAlbum: ") + sAlbum + _("\nYear: ") + sYear + _("\nGenre: ") + sGenre + _("\nComment: ") + sComment)

	def addFiletoPls(self):
		if self.filelist.canDescent():
			x = self.filelist.getName()
			if x == "..":
				return
			self.addDirtoPls(self.filelist.getSelection()[0])
		elif self.filelist.getServiceRef().type == 4098:  # playlist
			ServiceRef = self.filelist.getServiceRef()
			extension = ServiceRef.getPath()[ServiceRef.getPath().rfind('.') + 1:]
			if extension in self.playlistparsers:
				playlist = self.playlistparsers[extension]()
				list = playlist.open(ServiceRef.getPath())
				for x in list:
					self.playlist.addFile(x.ref)
				self.playlist.updateList()
		else:
			self.playlist.addFile(self.filelist.getServiceRef())
			self.playlist.updateList()

	def addDirtoPls(self, directory, recursive=True):
		if directory == '/':
			return
		filelist = FileList(directory, useServiceRef=True, showMountpoints=False, isTop=True)
		for x in filelist.getFileList():
			if x[0][1] is True:  # isDir
				#if recursive:
				#	if x[0][0] != directory:
				#		self.playlist.addFile(x[0][1])
				return
			elif filelist.getServiceRef() and filelist.getServiceRef().type == 4097:
				self.playlist.addFile(x[0][0])
		self.playlist.updateList()

	def deleteFile(self):
		self.service = self.filelist.getServiceRef()
		if self.service.type != 4098 and self.session.nav.getCurrentlyPlayingServiceOrGroup() is not None:
			if self.service == self.session.nav.getCurrentlyPlayingServiceOrGroup():
				self.StopPlayback()
		self.session.openWithCallback(self.deleteFileConfirmed, MessageBox, _("Do you really want to delete this file ?"))

	def deleteFileConfirmed(self, confirmed):
		if confirmed:
			delfile = self["filelist"].getFilename()
			remove(delfile)
			self.filelist.refresh()

	def deleteDir(self):
		self.session.openWithCallback(self.deleteDirConfirmed, MessageBox, _("Do you really want to delete this directory and it's content ?"))

	def deleteDirConfirmed(self, confirmed):
		if confirmed:
			import shutil
			deldir = self.filelist.getSelection()[0]
			shutil.rmtree(deldir)
			self.filelist.refresh()

	def getJPG(self):
		if config.plugins.mc_ap.whichjpg.value == "default":
			path = mcpath + "saver/"
		else:
			path = config.plugins.mc_ap.whichjpg.value
		for root, dirs, files in walk(path):
			for name in files:
				if name.endswith(".jpg"):
					self.jpgList.append(name)

	def showBackgroundJPG(self):
		if len(self.jpgList) > 0:
			if self.jpgIndex < len(self.jpgList) - 1:
				self.jpgIndex += 1
			else:
				self.jpgIndex = 0
			print("MediaCenter: Last JPG Index: %s" % str(self.jpgLastIndex))
			if self.jpgLastIndex != self.jpgIndex or self.jpgLastIndex == -1:
				if config.plugins.mc_ap.whichjpg.value == "default":
					path = mcpath + "saver/" + self.jpgList[self.jpgIndex]
				else:
					path = config.plugins.mc_ap.whichjpg.value + self.jpgList[self.jpgIndex]
				self["screensaver"].screensaver(path)
				self.jpgLastIndex = self.jpgIndex
				time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
				self.JpgTimer.start(time, True)
		else:
			print("MediaCenter: No Background Files found ...")

	def doEOF(self):
		if MC_AudioPlayer.playlistplay == 1:
			next = self.playlist.getCurrentIndex() + 1
			if next < len(self.playlist):
				MC_AudioPlayer.currPlaying = MC_AudioPlayer.currPlaying + 1
				self.PlayServicepls()
		elif config.plugins.mc_ap.repeat.getValue() == "single":
			self.StopPlayback()
			self.PlayService()
		elif config.plugins.mc_ap.repeat.getValue() == "all":
			self.down()
			if self.filelist.getName() == "..":
				self.down()
				self.checkisdir()
			self.PlayService()
		else:
			self.down()
			self.PlayService()

	def checkisdir(self):
		if self["filelist"].canDescent():
			self.down()
			self.checkisdir()
		else:
			self.PlayService()

	def __evDecodeError(self):
		currPlay = self.session.nav.getCurrentService()
		sVideoType = currPlay.info().getInfoString(iServiceInformation.sVideoType)
		self.session.open(MessageBox, _("This Dreambox can't decode %s video streams!") % sVideoType, type=MessageBox.TYPE_INFO, timeout=20)

	def __evPluginError(self):
		currPlay = self.session.nav.getCurrentService()
		message = currPlay.info().getInfoString(iServiceInformation.sUser + 12)
		self.session.open(MessageBox, message, type=MessageBox.TYPE_INFO, timeout=20)

	def addPlaylistParser(self, parser, extension):
		self.playlistparsers[extension] = parser

	def showMenu(self):
		menu = []
		#menu.append((_("shuffle"), "shuffle")) # TOOD
		if self.filelist.canDescent():
			x = self.filelist.getName()
			if x == "..":
				return
			menu.append((_("add directory to playlist"), "copydir"))
			menu.append((_("delete directory"), "deletedir"))
		else:
			menu.append((_("add file to playlist"), "copyfile"))
			menu.append((_("add file to playlist and play"), "copyandplay"))
			menu.append((_("add all files in directory to playlist"), "copyfiles"))
			menu.append((_("delete file"), "deletefile"))
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title="", list=menu)

	def menuCallback(self, choice):
		if choice is None:
			return
		if choice[1] == "copydir":
			self.addDirtoPls(self.filelist.getSelection()[0])
		elif choice[1] == "deletedir":
			self.deleteDir()
		elif choice[1] == "copyfile":
			self.addFiletoPls()
		elif choice[1] == "copyandplay":
			self.addFiletoPls()
			MC_AudioPlayer.currPlaying = len(self.playlist) - 1
			self.PlayServicepls()
		elif choice[1] == "copyfiles":
			self.addDirtoPls(dirname(self.filelist.getSelection()[0].getPath()) + "/", recursive=False)
		elif choice[1] == "deletefile":
			self.deleteFile()
#		elif choice[1] == "shuffle":
#			self.Shuffle()

	def Settings(self):
		self.session.openWithCallback(self.updd, AudioPlayerSettings)

	def Exit(self):
		if self.isVisible is False:
			self.visibility()
			return
		if self.filelist.getCurrentDirectory() is None:
			config.plugins.mc_ap.lastDir.value = "devicelist"
		else:
			config.plugins.mc_ap.lastDir.value = self.filelist.getCurrentDirectory()
		self.FileInfoTimer.stop()
		del self["coverArt"].picload
		del self["screensaver"].picload
		if self.ac3ON:
			config.av.downmix_ac3.value = False
			config.av.downmix_ac3.save()
		config.plugins.mc_ap.save()
		if self.session.nav.getCurrentService() is not None:
			self.session.nav.stopService()
		MC_AudioPlayer.STATE = "NONE"
		self.close()

	def screensavercheckup(self):
		self.JpgTimer.stop()
		self["screensaver"].showDefaultCover()
		time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
		self.JpgTimer.start(time, True)

	def showLyrics(self):
		if MC_AudioPlayer.STATE == "PLAY":
			self.session.openWithCallback(self.updd, Lyrics)


class MC_WebRadio(Screen, HelpableScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.jpgList = []
		self.jpgIndex = 0
		self.jpgLastIndex = -1
		self.isVisible = True
		self["key_blue"] = Button(_("Settings"))
		self["fileinfo"] = Label()
		self.ac3ON = False
		try:
			if config.av.downmix_ac3.value is False:
				config.av.downmix_ac3.value = True
				config.av.downmix_ac3.save()
				self.ac3ON = True
		except Exception as e:
			print("Media Center: no ac3")
		self["play"] = Pixmap()
		self["screensaver"] = MediaPixmap()
		MC_AudioPlayer.STATE = "NONE"
		lstdir = []
		self.playlist = PlayList()
		MC_AudioPlayer.playlistplay = 0
		MC_AudioPlayer.currPlaying = -1
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evEOF: self.doEOF,
				iPlayableService.evStopped: self.StopPlayback,
				iPlayableService.evUser + 11: self.__evDecodeError,
				iPlayableService.evUser + 12: self.__evPluginError,
				iPlayableService.evUser + 14: self["screensaver"].screensaver
			})
		self["actions"] = HelpableActionMap(self, "MC_AudioPlayerActions",
			{
				"ok": (self.KeyOK, "Play selected file"),
				"playpause": (self.PlayPause, "Play / Pause"),
				"cancel": (self.Exit, "Exit Audio Player"),
				"left": (self.leftUp, "List Top"),
				"right": (self.rightDown, "List Bottom"),
				"up": (self.up, "List up"),
				"down": (self.down, "List down"),
				"video": (self.visibility, "Show / Hide Player"),
				"green": (self.showMenu, "Menu"),
				"stop": (self.StopPlayback, "Stop Playback"),
				"red": (self.deleteFile, "Delete"),
				"blue": (self.Settings, "Settings"),
			}, -2)

		self.playlistparsers = {}
		self.addPlaylistParser(PlaylistIOM3U, "m3u")
		self.addPlaylistParser(PlaylistIOPLS, "pls")
		self.addPlaylistParser(PlaylistIOInternal, "e2pls")
		currDir = mcpath + "radio/"
		if not pathExists(currDir):
			currDir = "/"
		self.filelist = []
		self["filelist"] = []
		inhibitDirs = ["/bin", "/boot", "/dev", "/dev.static", "/etc", "/lib", "/proc", "/ram", "/root", "/sbin", "/sys", "/tmp", "/usr", "/var"]
		self.filelist = FileList(currDir, useServiceRef=True, showDirectories=False, showFiles=True, matchingPattern="(?i)^.*\.(m3u|pls|e2pls)", additionalExtensions="4098:m3u 4098:e2pls 4098:pls")

		self["filelist"] = self.filelist
		self["filelist"].show()
		self.JpgTimer = eTimer()
		self.JpgTimer.callback.append(self.showBackgroundJPG)
		self.getJPG()
		self.FileInfoTimer = eTimer()
		self.FileInfoTimer.callback.append(self.updateFileInfo)

	def unlockShow(self):
		return

	def lockShow(self):
		return

	def up(self):
		self["filelist"].up()
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()

	def down(self):
		self["filelist"].down()
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()

	def leftUp(self):
		self["filelist"].pageUp()
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()

	def rightDown(self):
		self["filelist"].pageDown()
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()

	def KeyOK(self):
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()
		ServiceRef = self.filelist.getServiceRef()
		extension = ServiceRef.getPath()[ServiceRef.getPath().rfind('.') + 1:]
		if extension in self.playlistparsers:
			self.playlist.clear()
			playlist = self.playlistparsers[extension]()
			list = playlist.open(ServiceRef.getPath())
			for x in list:
				self.playlist.addFile(x.ref)
		self.playlist.updateList()
		MC_AudioPlayer.currPlaying = 0
		self.PlayServicepls()

	def PlayPause(self):
		if MC_AudioPlayer.STATE == "PLAY":
			service = self.session.nav.getCurrentService()
			pausable = service.pause()
			pausable.pause()
			MC_AudioPlayer.STATE = "PAUSED"
			self["play"].instance.setPixmapFromFile(mcpath + "icons/pause_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
		elif MC_AudioPlayer.STATE == "PAUSED":
			service = self.session.nav.getCurrentService()
			pausable = service.pause()
			pausable.unpause()
			MC_AudioPlayer.STATE = "PLAY"
			self["play"].instance.setPixmapFromFile(mcpath + "icons/play_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
		else:
			self.KeyOK()

	def visibility(self, force=1):
		if self.isVisible is True:
			self.isVisible = False
			self.hide()
		else:
			self.isVisible = True
			self.show()

	def updd(self):
		self.updateFileInfo()
		self.filelist.refresh()
		if MC_AudioPlayer.STATE == "PLAY":
			self["play"].instance.setPixmapFromFile(mcpath + "icons/play_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
		elif MC_AudioPlayer.STATE == "PAUSED":
			self["play"].instance.setPixmapFromFile(mcpath + "icons/pause_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
		elif MC_AudioPlayer.STATE == "NONE":
			self["play"].instance.setPixmapFromFile(mcpath + "icons/stop_enabled.png")
		else:
			return

	def PlayServicepls(self):
		MC_AudioPlayer.playlistplay = 1
		x = self.playlist.getCurrentIndex()
		x = len(self.playlist)
		self.session.nav.playService(self.playlist.getServiceRefList()[self.playlist.getCurrentIndex()])
		MC_AudioPlayer.STATE = "PLAY"
		self.FileInfoTimer.start(2000, True)
		self["play"].instance.setPixmapFromFile(mcpath + "icons/play_enabled.png")
		if config.plugins.mc_ap.showJpg.getValue():
			time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
			self.JpgTimer.start(time, True)
		self.playlist.clear()

	def StopPlayback(self):
		if self.isVisible is False:
			self.show()
			self.isVisible = True
		if self.session.nav.getCurrentService() is None:
			return
		else:
			self.session.nav.stopService()
			if config.plugins.mc_ap.showJpg.getValue():
				self.JpgTimer.stop()
				self["screensaver"].showDefaultCover()
			MC_AudioPlayer.STATE = "NONE"
			self["play"].instance.setPixmapFromFile(mcpath + "icons/stop_enabled.png")

	def updateFileInfo(self):
		currPlay = self.session.nav.getCurrentService()
		if currPlay is not None:
			sTitle = currPlay.info().getInfoString(iServiceInformation.sTagTitle)
			sArtist = currPlay.info().getInfoString(iServiceInformation.sTagArtist)
			sAlbum = currPlay.info().getInfoString(iServiceInformation.sTagAlbum)
			sGenre = currPlay.info().getInfoString(iServiceInformation.sTagGenre)
			sComment = currPlay.info().getInfoString(iServiceInformation.sTagComment)
			sYear = currPlay.info().getInfoString(iServiceInformation.sTagDate)
			if sTitle == "":
				sTitle = currPlay.info().getName().split('/')[-1]
			self["fileinfo"].setText(_("Title: ") + sTitle + _("\nArtist: ") + sArtist + _("\nAlbum: ") + sAlbum + _("\nYear: ") + sYear + _("\nGenre: ") + sGenre + _("\nComment: ") + sComment)
		self.FileInfoTimer.start(10000, True)

	def deleteFile(self):
		self.service = self.filelist.getServiceRef()
		if self.service.type != 4098 and self.session.nav.getCurrentlyPlayingServiceOrGroup() is not None:
			if self.service == self.session.nav.getCurrentlyPlayingServiceOrGroup():
				self.StopPlayback()
		self.session.openWithCallback(self.deleteFileConfirmed, MessageBox, _("Do you really want to delete this file ?"))

	def deleteFileConfirmed(self, confirmed):
		if confirmed:
			delfile = self["filelist"].getFilename()
			remove(delfile)
			self.filelist.refresh()

	def getJPG(self):
		if config.plugins.mc_ap.whichjpg.value == "default":
			path = mcpath + "saver/"
		else:
			path = config.plugins.mc_ap.whichjpg.value
		for root, dirs, files in walk(path):
			for name in files:
				if name.endswith(".jpg"):
					self.jpgList.append(name)

	def showBackgroundJPG(self):
		if len(self.jpgList) > 0:
			if self.jpgIndex < len(self.jpgList) - 1:
				self.jpgIndex += 1
			else:
				self.jpgIndex = 0
			if self.jpgLastIndex != self.jpgIndex or self.jpgLastIndex == -1:
				if config.plugins.mc_ap.whichjpg.value == "default":
					path = mcpath + "saver/" + self.jpgList[self.jpgIndex]
				else:
					path = config.plugins.mc_ap.whichjpg.value + self.jpgList[self.jpgIndex]
				self["screensaver"].screensaver(path)
				self.jpgLastIndex = self.jpgIndex
				time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
				self.JpgTimer.start(time, True)
		else:
			print("MediaCenter: No Background Files found ...")

	def doEOF(self):
		self.StopPlayback()
		if config.plugins.mc_ap.showJpg.getValue():
			self.JpgTimer.stop()
			self["screensaver"].showDefaultCover()

	def __evDecodeError(self):
		currPlay = self.session.nav.getCurrentService()
		sVideoType = currPlay.info().getInfoString(iServiceInformation.sVideoType)
		self.session.open(MessageBox, _("This Dreambox can't decode %s video streams!") % sVideoType, type=MessageBox.TYPE_INFO, timeout=20)

	def __evPluginError(self):
		currPlay = self.session.nav.getCurrentService()
		message = currPlay.info().getInfoString(iServiceInformation.sUser + 12)
		self.session.open(MessageBox, message, type=MessageBox.TYPE_INFO, timeout=20)

	def addPlaylistParser(self, parser, extension):
		self.playlistparsers[extension] = parser

	def Settings(self):
		self.session.openWithCallback(self.updd, AudioPlayerSettings)

	def Exit(self):
		if self.isVisible is False:
			self.visibility()
			return
		self.FileInfoTimer.stop()
		del self["screensaver"].picload
		if self.ac3ON:
			config.av.downmix_ac3.value = False
			config.av.downmix_ac3.save()
		if self.session.nav.getCurrentService() is not None:
			self.session.nav.stopService()
		MC_AudioPlayer.STATE = "NONE"
		self.close()

	def screensavercheckup(self):
		self.JpgTimer.stop()
		self["screensaver"].showDefaultCover()
		time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
		self.JpgTimer.start(time, True)

	def showMenu(self):
		if fileExists("/tmp/pl.m3u"):
			remove("/tmp/pl.m3u")
		menu = []
		menu.append((_("Top_40"), "top_40"))
		menu.append((_("Pop"), "pop"))
		menu.append((_("Rock"), "rock"))
		menu.append((_("60s"), "60s"))
		menu.append((_("70s"), "70s"))
		menu.append((_("80s"), "80s"))
		menu.append((_("90s"), "90s"))
		menu.append((_("Acid_jazz"), "acid_jazz"))
		menu.append((_("African"), "african"))
		menu.append((_("Alternative"), "alternative"))
		menu.append((_("Ambient"), "ambient"))
		menu.append((_("Americana"), "americana"))
		menu.append((_("Anime"), "anime"))
		menu.append((_("Arabic"), "arabic"))
		menu.append((_("Asian"), "asian"))
		menu.append((_("Bigband"), "big_band"))
		menu.append((_("Bluegrass"), "bluegrass"))
		menu.append((_("Blues"), "blues"))
		menu.append((_("Breakbeat"), "breakbeat"))
		menu.append((_("Chillout"), "chillout"))
		menu.append((_("Christian"), "christian"))
		menu.append((_("Classical"), "classical"))
		menu.append((_("Club"), "club"))
		menu.append((_("College"), "college"))
		menu.append((_("Comedy"), "comedy"))
		menu.append((_("Country"), "country"))
		menu.append((_("Dance"), "dance"))
		menu.append((_("Deutsch"), "deutsch"))
		menu.append((_("Disco"), "disco"))
		menu.append((_("Discofox"), "discofox"))
		menu.append((_("Downtempo"), "downtempo"))
		menu.append((_("Drum'n'bass"), "drum_and_bass"))
		menu.append((_("Easylistening"), "easy_listening"))
		menu.append((_("Ebm"), "ebm"))
		menu.append((_("Electronic"), "electronic"))
		menu.append((_("Eurodance"), "eurodance"))
		menu.append((_("Film"), "film"))
		menu.append((_("Folk"), "folk"))
		menu.append((_("France"), "france"))
		menu.append((_("Funk"), "funk"))
		menu.append((_("Gay"), "gay"))
		menu.append((_("Goa"), "goa"))
		menu.append((_("Gospel"), "gospel"))
		menu.append((_("Gothic"), "gothic"))
		menu.append((_("Greek"), "greek"))
		menu.append((_("Hardcore"), "hardcore"))
		menu.append((_("Hardrock"), "hardrock"))
		menu.append((_("Hiphop"), "hip_hop"))
		menu.append((_("House"), "house"))
		menu.append((_("India"), "india"))
		menu.append((_("Indie"), "indie"))
		menu.append((_("Industrial"), "industrial"))
		menu.append((_("Instrumental"), "instrumental"))
		menu.append((_("Italian"), "italian"))
		menu.append((_("Jazz"), "jazz"))
		menu.append((_("Jpop"), "jpop"))
		menu.append((_("Jungle"), "jungle"))
		menu.append((_("Latin"), "latin"))
		menu.append((_("Lounge"), "lounge"))
		menu.append((_("Metal"), "metal"))
		menu.append((_("Mixed"), "mixed"))
		menu.append((_("Musical"), "musical"))
		menu.append((_("Oldies"), "oldies"))
		menu.append((_("Opera"), "opera"))
		menu.append((_("Polish"), "polish"))
		menu.append((_("Polka"), "polka"))
		menu.append((_("Portugal"), "portugal"))
		menu.append((_("Progressive"), "progressive"))
		menu.append((_("Punk"), "punk"))
		menu.append((_("Quran"), "quran"))
		menu.append((_("Rap"), "rap"))
		menu.append((_("Reggae"), "reggae"))
		menu.append((_("Retro"), "retro"))
		menu.append((_("Rnb"), "rnb"))
		menu.append((_("Romanian"), "romanian"))
		menu.append((_("Salsa"), "salsa"))
		menu.append((_("Schlager"), "schlager"))
		menu.append((_("Ska"), "ska"))
		menu.append((_("Smooth_jazz"), "smooth_jazz"))
		menu.append((_("Soul"), "soul"))
		menu.append((_("Soundtrack"), "soundtrack"))
		menu.append((_("Spain"), "spain"))
		menu.append((_("Spiritual"), "spiritual"))
		menu.append((_("Sport"), "sport"))
		menu.append((_("Swing"), "swing"))
		menu.append((_("Symphonic"), "symphonic"))
		menu.append((_("Talk"), "talk"))
		menu.append((_("Techno"), "techno"))
		menu.append((_("Trance"), "trance"))
		menu.append((_("Turk"), "turk"))
		menu.append((_("Urban"), "urban"))
		menu.append((_("Usa"), "usa"))
		menu.append((_("Various"), "various"))
		menu.append((_("Wave"), "wave"))
		menu.append((_("Worldmusic"), "world"))
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title="", list=menu)

	def menuCallback(self, choice):
		if choice is None:
			return
		system("wget -O /tmp/pl.m3u " + radirl + choice[1] + ".m3u")
		self.session.openWithCallback(self.updd, MC_WebDown)


class MC_WebDown(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		channels = []
		if fileExists("/tmp/pl.m3u"):
			names = open("/tmp/pl.m3u").read().split('\n')
			lnk = ""
			name = ""
			for x in names:
				if x.startswith("#EXTINF:"):
					name = x.split("radio.pervii.com\", ")[1]
				elif x.startswith("http"):
					lnk = x
				if name and lnk:
					channels.append((name, lnk))
					name = ""
					lnk = ""
		self["menu"] = List(channels)
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"],
		{
			"cancel": self.exit,
			"ok": self.okbuttonClick
		}, -1)

	def okbuttonClick(self):
		selection = self["menu"].getCurrent()
		if selection is not None:
			fn = sub("[^a-zA-Z0-9\n\.]", "_", selection[0])
			with open(mcpath + "radio/" + fn + ".m3u", "w") as f:
				f.write(selection[1])
			if fileExists("/tmp/pl.m3u"):
				remove("/tmp/pl.m3u")
			self.close()

	def exit(self):
		if fileExists("/tmp/pl.m3u"):
			remove("/tmp/pl.m3u")
		self.close()


class MC_AudioPlaylist(Screen, InfoBarSeek):
	def __init__(self, session):
		Screen.__init__(self, session)
		InfoBarSeek.__init__(self, actionmap="MediaPlayerSeekActions")
		self["key_red"] = Button("Back")
		self["key_green"] = Button(" ")
		self["key_yellow"] = Button(" ")
		self["key_blue"] = Button(_("File Browser"))
		self.jpgList = []
		self.jpgIndex = 0
		self.jpgLastIndex = -1
		self["play"] = Pixmap()
		self.isVisible = True
		self["fileinfo"] = Label()
		#self["coverArt"] = MediaPixmap()
		self["screensaver"] = MediaPixmap()
		self.FileInfoTimer = eTimer()
		self.FileInfoTimer.callback.append(self.updateFileInfo)
		self.PlaySingle = 0
		self.playlist = PlayList()
		self["playlist"] = self.playlist
		self.playlistIOInternal = PlaylistIOInternal()
		self.playlistparsers = {}
		self.addPlaylistParser(PlaylistIOM3U, "m3u")
		self.addPlaylistParser(PlaylistIOPLS, "pls")
		self.addPlaylistParser(PlaylistIOInternal, "e2pls")
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evEOF: self.fileupdate,
				#iPlayableService.evStopped: self.StopPlayback,
				#iPlayableService.evUser+13: self["coverArt"].embeddedCoverArt,
				iPlayableService.evUser + 14: self["screensaver"].screensaver
			})
		self["actions"] = HelpableActionMap(self, "MC_AudioPlayerActions",
			{
				"ok": (self.KeyOK, "Play from selected file"),
				"cancel": (self.Exit, "Exit Audio Player"),
				"left": (self.leftUp, "List Top"),
				"right": (self.rightDown, "List Bottom"),
				"up": (self.up, "List up"),
				"down": (self.down, "List down"),
				"menu": (self.showMenu, "File / Folder Options"),
				"video": (self.visibility, "Show / Hide Player"),
				"info": (self.showLyrics, "Lyrics"),
				"stop": (self.StopPlayback, "Stop Playback"),
				"red": (self.Exit, "Close Playlist"),
				#"green": (self.close, "Play All"),
				#"yellow": (self.Exit, "Playlists"),
				"blue": (self.Exit, "Close Playlist"),
				"next": (self.KeyNext, "Next song"),
				"previous": (self.KeyPrevious, "Previous song"),
				"playpause": (self.PlayPause, "Play / Pause"),
			}, -2)
		self.JpgTimer = eTimer()
		self.JpgTimer.callback.append(self.showBackgroundJPG)
		self.getJPG()
		if MC_AudioPlayer.STATE != "NONE":
			self.updateFileInfo()
			if config.plugins.mc_ap.showJpg.getValue():
				time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
				self.JpgTimer.start(time, True)

	def unlockShow(self):
		return

	def lockShow(self):
		return

	def up(self):
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()
		self["playlist"].up()

	def down(self):
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()
		self["playlist"].down()

	def leftUp(self):
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()
		self["playlist"].pageUp()

	def rightDown(self):
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()
		self["playlist"].pageDown()

	def KeyOK(self):
		if len(self.playlist.getServiceRefList()):
			print(self.playlist.getSelectionIndex())
			x = self.playlist.getSelectionIndex()
			self.playlist.setCurrentPlaying(self.playlist.getSelectionIndex())
			x = self.playlist.getCurrentIndex()
			x = len(self.playlist)
			self.PlayService()

	def PlayPause(self):
		if MC_AudioPlayer.STATE != "NONE":
			if MC_AudioPlayer.STATE == "PLAY":
				service = self.session.nav.getCurrentService()
				pausable = service.pause()
				pausable.pause()
				MC_AudioPlayer.STATE = "PAUSED"
			elif MC_AudioPlayer.STATE == "PAUSED":
				service = self.session.nav.getCurrentService()
				pausable = service.pause()
				pausable.unpause()
				MC_AudioPlayer.STATE = "PLAY"
			else:
				self.KeyOK()

	def KeyNext(self):
		if MC_AudioPlayer.STATE != "NONE":
			if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
			if MC_AudioPlayer.playlistplay == 1:
				next = self.playlist.getCurrentIndex() + 1
				if next < len(self.playlist):
					MC_AudioPlayer.currPlaying = MC_AudioPlayer.currPlaying + 1
				else:
					MC_AudioPlayer.currPlaying = 0
				self.PlayService()
			else:
				self.session.open(MessageBox, _("You have to close playlist before you can go to the next song while playing from file browser."), MessageBox.TYPE_ERROR)

	def KeyPrevious(self):
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
		if MC_AudioPlayer.playlistplay == 1:
			next = self.playlist.getCurrentIndex() - 1
			if next != -1:
				MC_AudioPlayer.currPlaying = MC_AudioPlayer.currPlaying - 1
			else:
				MC_AudioPlayer.currPlaying = 0
			self.PlayService()
		else:
			self.session.open(MessageBox, _("You have to close playlist before you can go to the previous song while playing from file browser."), MessageBox.TYPE_ERROR)

	def PlayService(self):
		MC_AudioPlayer.playlistplay = 1
		self.session.nav.playService(self.playlist.getServiceRefList()[self.playlist.getCurrentIndex()])
		MC_AudioPlayer.STATE = "PLAY"
		self.FileInfoTimer.start(2000, True)
		self["play"].instance.setPixmapFromFile(mcpath + "icons/play_enabled.png")
		if config.plugins.mc_ap.showJpg.getValue():
			time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
			self.JpgTimer.start(time, True)
	#	path = self["filelist"].getCurrentDirectory()
	#	self["coverArt"].updateCoverArt(path)

	def StopPlayback(self):
		if self.isVisible is False:
			self.show()
			self.isVisible = True
		if self.session.nav.getCurrentService() is None:
			return
		else:
			self.session.nav.stopService()
			MC_AudioPlayer.STATE = "NONE"
			self["play"].instance.setPixmapFromFile(mcpath + "icons/stop_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():
				self.JpgTimer.stop()
				self["screensaver"].showDefaultCover()

	def visibility(self, force=1):
		if self.isVisible is True:
			self.isVisible = False
			self.hide()
		else:
			self.isVisible = True
			self.show()

	def Settings(self):
		self.session.openWithCallback(self.updd, MC_AudioPlaylist)

	def updd(self):
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
		else:
			return

	def Exit(self):
		del self["screensaver"].picload
		if config.plugins.mc_ap.showJpg.getValue():
			self.JpgTimer.stop()
		self.close()

	def fileupdate(self):
		self.FileInfoTimer.start(2000, True)
		if config.plugins.mc_ap.showJpg.getValue():
			time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
			self.JpgTimer.start(time, True)

	def updateFileInfo(self):
		currPlay = self.session.nav.getCurrentService()
		if currPlay is not None:
			sTitle = currPlay.info().getInfoString(iServiceInformation.sTagTitle)
			sArtist = currPlay.info().getInfoString(iServiceInformation.sTagArtist)
			sAlbum = currPlay.info().getInfoString(iServiceInformation.sTagAlbum)
			sGenre = currPlay.info().getInfoString(iServiceInformation.sTagGenre)
			sComment = currPlay.info().getInfoString(iServiceInformation.sTagComment)
			sYear = currPlay.info().getInfoString(iServiceInformation.sTagDate)
			if sTitle == "":
				sTitle = currPlay.info().getName().split('/')[-1]
			self["fileinfo"].setText("Title: " + sTitle + "\nArtist: " + sArtist + "\nAlbum: " + sAlbum + "\nYear: " + sYear + "\nGenre: " + sGenre + "\nComment: " + sComment)

	def save_playlist(self):
		from Screens.InputBox import InputBox
		self.session.openWithCallback(self.save_pls, InputBox, title=_("Please enter filename (empty = use current date)"), windowTitle=_("Save Playlist"))

	def save_pls(self, name):
		if name is not None:
			name = name.strip()
			if name == "":
				name = strftime("%y%m%d_%H%M%S")
			name += ".e2pls"
			self.playlistIOInternal.clear()
			for x in self.playlist.list:
				self.playlistIOInternal.addService(ServiceReference(x[0]))
			self.playlistIOInternal.save(resolveFilename(SCOPE_PLAYLIST) + name)

	def load_playlist(self):
		listpath = []
		playlistdir = resolveFilename(SCOPE_PLAYLIST)
		try:
			for i in listdir(playlistdir):
				listpath.append((i, playlistdir + i))
		except OSError as e:
			print("Error while scanning subdirs: %s" % str(e))
		self.session.openWithCallback(self.load_pls, ChoiceBox, title=_("Please select a playlist..."), list=listpath)

	def load_pls(self, path):
		if path is not None:
			self.playlist.clear()
			extension = path[0].rsplit('.', 1)[-1]
			if extension in self.playlistparsers:
				playlist = self.playlistparsers[extension]()
				list = playlist.open(path[1])
				for x in list:
					self.playlist.addFile(x.ref)
			self.playlist.updateList()

	def delete_saved_playlist(self):
		listpath = []
		playlistdir = resolveFilename(SCOPE_PLAYLIST)
		try:
			for i in listdir(playlistdir):
				listpath.append((i, playlistdir + i))
		except OSError as e:
			print("Error while scanning subdirs: %s" % str(e))
		self.session.openWithCallback(self.delete_saved_pls, ChoiceBox, title=_("Please select a playlist to delete..."), list=listpath)

	def delete_saved_pls(self, path):
		if path is not None:
			self.delname = path[1]
			self.session.openWithCallback(self.delete_saved_pls_conf, MessageBox, _("Do you really want to delete %s?") % (path[1]))

	def delete_saved_pls_conf(self, confirmed):
		if confirmed:
			try:
				remove(self.delname)
			except OSError as e:
				self.session.open(MessageBox, _("Delete failed!"), MessageBox.TYPE_ERROR)

	def addPlaylistParser(self, parser, extension):
		self.playlistparsers[extension] = parser

	def showMenu(self):
		menu = []
		menu.append((_("delete from playlist"), "deleteentry"))
		menu.append((_("clear playlist"), "clear"))
		menu.append((_("load playlist"), "loadplaylist"))
		menu.append((_("save playlist"), "saveplaylist"))
		menu.append((_("delete saved playlist"), "deleteplaylist"))
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title="", list=menu)

	def menuCallback(self, choice):
		if choice is None:
			return
		if choice[1] == "deleteentry":
			self.playlist.deleteFile(self.playlist.getSelectionIndex())
			self.playlist.updateList()
		elif choice[1] == "clear":
			self.playlist.clear()
		elif choice[1] == "loadplaylist":
			self.load_playlist()
		elif choice[1] == "saveplaylist":
			self.save_playlist()
		elif choice[1] == "deleteplaylist":
			self.delete_saved_playlist()

	def getJPG(self):
		if config.plugins.mc_ap.whichjpg.value == "default":
			path = mcpath + "saver/"
		else:
			path = config.plugins.mc_ap.whichjpg.value
		for root, dirs, files in walk(path):
			for name in files:
				if name.endswith(".jpg"):
					self.jpgList.append(name)

	def showBackgroundJPG(self):
		if len(self.jpgList) > 0:
			if self.jpgIndex < len(self.jpgList) - 1:
				self.jpgIndex += 1
			else:
				self.jpgIndex = 0
			if self.jpgLastIndex != self.jpgIndex or self.jpgLastIndex == -1:
				path = mcpath + "saver/" + self.jpgList[self.jpgIndex]
				self["screensaver"].screensaver(path)
				self.jpgLastIndex = self.jpgIndex
				time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
				self.JpgTimer.start(time, True)
		else:
			print("MediaCenter: No Background Files found ...")

	def showLyrics(self):
		if MC_AudioPlayer.STATE == "PLAY":
			self.session.openWithCallback(self.updd, Lyrics)

	def screensavercheckup(self):
		self.JpgTimer.stop()
		self["screensaver"].showDefaultCover()
		time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
		self.JpgTimer.start(time, True)


class Lyrics(Screen):
	skin = """
		<screen name="Lyrics" position="0,0" size="720,576" flags="wfNoBorder" backgroundColor="#00000000" title="Lyrics">
		<eLabel backgroundColor="#999999" position="50,50" size="620,2" zPosition="1"/>
		<widget name="headertext" position="50,73" zPosition="1" size="620,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
		<widget name="coverly" position="700,120" size="160,200" zPosition="9" valign="center" halign="center" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/skins/defaultHD/images/no_cover.png" transparent="1" alphatest="blend" />
		<widget name="resulttext" position="50,100" zPosition="1" size="620,20" font="Regular;16" transparent="1"   backgroundColor="#00000000"/>
		<widget name="lyric_text" position="50,150" zPosition="2" size="620,350" font="Regular;18" transparent="0"  backgroundColor="#00000000"/>
		</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self["headertext"] = Label(_("Lyrics"))
		self["resulttext"] = Label()
		self["coverly"] = MediaPixmap()
		curPlay = self.session.nav.getCurrentService()
		self.oldplaying = ""
		self.curplaying = ""
		if curPlay is not None:
			title = curPlay.info().getInfoString(iServiceInformation.sTagTitle)
			self.oldplaying = str(title)
			self.curplaying = str(title)
#			system("echo '" + str(title) + "' > /tmp/.oldplaying | echo '" + str(title) + "' > /tmp/.curplaying ")

		self.RFTimer = eTimer()
		self.RFTimer.callback.append(self.refresh)
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evUser + 11: self["coverly"].coverlyrics
			})
		self["actions"] = HelpableActionMap(self, "MC_AudioPlayerActions",
			{
				"cancel": self.Exit,
				"up": self.pageUp,
				"left": self.pageUp,
				"down": self.pageDown,
				"right": self.pageDown
			}, -2)
		self["lyric_text"] = ScrollLabel()
		self.refresh()
		self.onLayoutFinish.append(self.startRun)

	def refresh(self):
		time = 10000
		self.RFTimer.start(time, True)
		curPlay = self.session.nav.getCurrentService()
		title = curPlay.info().getInfoString(iServiceInformation.sTagTitle)
		self.curplaying = str(title)
		#system("echo '" + str(title) + "' > /tmp/.curplaying")
		#old = open("/tmp/.oldplaying").read()
		#oldtitle = old.split('\r\n')
		#tit = open("/tmp/.curplaying").read()
		#titlee = tit.split('\r\n')
		if self.oldplaying == self.curplaying:
			return
		else:
			self.startRun()
			self.oldplaying = str(title)
			#system("echo '" + str(title) + "' > /tmp/.oldplaying")

	def startRun(self):
		text = "No lyrics found in id3-tag, trying api.chartlyrics.com..."
		self["lyric_text"].setText(text)
		self.getLyricsFromID3Tag()

	def getLyricsFromID3Tag(self):
		curPlay = self.session.nav.getCurrentService()
		if curPlay is not None:
			titlely = curPlay.info().getInfoString(iServiceInformation.sTagTitle)
			artistly = curPlay.info().getInfoString(iServiceInformation.sTagArtist)
			if titlely == "":
				titlely = curPlay.info().getName().split('/')[-1]
			if artistly == "":
				artistly = titlely
		url = "http://api.chartlyrics.com/apiv1.asmx/SearchLyricDirect?artist=%s&song=%s" % (quote(artistly), quote(titlely))
		url = url.replace("%21", "%13")  # . dont ask me why
		callInThread(self.threadGetPage, url, self.gotLyrics, self.urlError)

	def threadGetPage(self, link, success, fail=None):
		try:
			response = get(link)
			response.raise_for_status()
			success(ensure_str(response.content))
		except exceptions.RequestException as error:
			if fail is not None:
				fail(error)

	def urlError(self, error=None):
		if error is not None:
			self["resulttext"].setText(str(error.getErrorMessage()))
			self["lyric_text"].setText("")

	def gotLyrics(self, xmlstring):
		root = cet_fromstring(xmlstring)
		try:
			lyrictext = root.findtext("{http://api.chartlyrics.com/}Lyric")
			self["lyric_text"].setText(lyrictext)
			title = root.findtext("{http://api.chartlyrics.com/}LyricSong")
			artist = root.findtext("{http://api.chartlyrics.com/}LyricArtist")
			coverly = root.findtext("{http://api.chartlyrics.com/}LyricCovertArtUrl")
			system("wget -O /tmp/.onlinecover " + coverly + "")
			self["coverly"].coverlyrics()
			result = _("Response -> lyrics for: %s (%s)") % (title, artist)
			self["resulttext"].setText(result)
		except:
			pass
		if not lyrictext:
			self["resulttext"].setText(_("No lyrics found"))
			self["lyric_text"].setText("")
			self["coverly"].showDefaultCover()

	def pageUp(self):
		self["lyric_text"].pageUp()

	def pageDown(self):
		self["lyric_text"].pageDown()

	def Exit(self):
		del self["coverly"].picload
		if fileExists("/tmp/.onlinecover"):
			remove("/tmp/.onlinecover")
		#if fileExists("/tmp/.curplaying") and fileExists("/tmp/.oldplaying"):
		#	system("rm -rf /tmp/.*playing")
		self.RFTimer.stop()
		self.close()


class MediaPixmap(Pixmap):
	def __init__(self):
		Pixmap.__init__(self)
		self.coverArtFileName = ""
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.paintCoverArtPixmapCB)
		self.coverFileNames = ['cover.jpg',
			'folder.png',
			'folder.jpg',
			'Cover.jpg',
			'Folder.png',
			'Folder.jpg']

	def applySkin(self, desktop, screen):
		from Tools.LoadPixmap import LoadPixmap
		noCoverFile = None
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "pixmap":
					noCoverFile = value
					break
		if noCoverFile is None:
			noCoverFile = resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/no_coverArt.png")
		self.noCoverPixmap = LoadPixmap(noCoverFile)
		return Pixmap.applySkin(self, desktop, screen)

	def onShow(self):
		Pixmap.onShow(self)
		#0=Width 1=Height 2=Aspect 3=use_cache 4=resize_type 5=Background(#AARRGGBB)
		self.picload.setPara((self.instance.size().width(), self.instance.size().height(), 1, 1, False, 1, "#00000000"))

	def paintCoverArtPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr is not None:
			self.instance.setPixmap(ptr.__deref__())

	def updateCoverArt(self, path):
		while not path.endswith("/"):
			path = path[:-1]
		new_coverArtFileName = None
		for filename in self.coverFileNames:
			if fileExists(path + filename):
				new_coverArtFileName = path + filename
		if self.coverArtFileName != new_coverArtFileName:
			self.coverArtFileName = new_coverArtFileName
			if new_coverArtFileName:
				self.picload.startDecode(self.coverArtFileName)
			else:
				self.showDefaultCover()

	def showDefaultCover(self):
		self.instance.setPixmap(self.noCoverPixmap)

	def embeddedCoverArt(self):
		self.coverArtFileName = "/tmp/.id3coverart"
		self.picload.startDecode(self.coverArtFileName)

	def coverlyrics(self):
		self.coverArtFileName = "/tmp/.onlinecover"
		self.picload.startDecode(self.coverArtFileName)

	def screensaver(self, path):
		self.picload.startDecode(path)


class AudioPlayerSettings(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = NumberActionMap(["SetupActions"],
		{
			"ok": self.close,
			"cancel": self.close,
			"left": self.keyLeft,
			"right": self.keyRight,
			"0": self.keyNumber,
			"1": self.keyNumber,
			"2": self.keyNumber,
			"3": self.keyNumber,
			"4": self.keyNumber,
			"5": self.keyNumber,
			"6": self.keyNumber,
			"7": self.keyNumber,
			"8": self.keyNumber,
			"9": self.keyNumber
		}, -1)

		self.list = []
		self["configlist"] = ConfigList(self.list)
		self.list.append(getConfigListEntry(_("Screensaver Enable:"), config.plugins.mc_ap.showJpg))
		self.list.append(getConfigListEntry(_("Screensaver Interval"), config.plugins.mc_ap.jpg_delay))
		self.list.append(getConfigListEntry(_("Screensaver Style:"), config.plugins.mc_ap.whichjpg))
		self.list.append(getConfigListEntry(_("Filelist Sorting:"), config.plugins.mc_ap_sortmode))

	def keyLeft(self):
		self["configlist"].handleKey(KEY_LEFT)

	def keyRight(self):
		self["configlist"].handleKey(KEY_RIGHT)

	def keyNumber(self, number):
		self["configlist"].handleKey(KEY_0 + number)
