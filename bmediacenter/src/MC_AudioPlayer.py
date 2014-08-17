from enigma import eTimer, iServiceInformation, iPlayableService, ePicLoad, RT_VALIGN_CENTER, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, gFont, eListbox, ePoint, eListboxPythonMultiContent, eServiceCenter
from Components.MenuList import MenuList
from Screens.Screen import Screen
from Screens.ServiceInfo import ServiceInfoList, ServiceInfoListEntry
from Components.ActionMap import ActionMap, NumberActionMap, HelpableActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Screens.ChoiceBox import ChoiceBox
from ServiceReference import ServiceReference
from Components.Button import Button
from Components.ScrollLabel import ScrollLabel
from Components.Sources.List import List
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen
from twisted.internet import reactor, defer
from twisted.web import client
from twisted.web.client import HTTPClientFactory, downloadPage
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Playlist import PlaylistIOInternal, PlaylistIOM3U, PlaylistIOPLS
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import *
from Tools.Directories import resolveFilename, fileExists, pathExists, createDir, SCOPE_MEDIA, SCOPE_PLAYLIST, SCOPE_SKIN_IMAGE
from MC_Filelist import FileList
from Screens.InfoBarGenerics import InfoBarSeek
import os
from os import path as os_path, remove as os_remove, listdir as os_listdir
from __init__ import _
config.plugins.mc_ap = ConfigSubsection()
sorts = [('default',_("default")),('alpha',_("alphabet")), ('alphareverse',_("alphabet backward")),('date',_("date")),('datereverse',_("date backward")),('size',_("size")),('sizereverse',_("size backward"))]
config.plugins.mc_ap_sortmode = ConfigSubsection()
config.plugins.mc_ap_sortmode.enabled = ConfigSelection(sorts)
config.plugins.mc_ap.showJpg = ConfigYesNo(default=True)
config.plugins.mc_ap.jpg_delay = ConfigInteger(default=10, limits=(5, 999))
config.plugins.mc_ap.repeat = ConfigSelection(default="off", choices = [("off", "off"),("single", "single"),("all", "all")])
config.plugins.mc_ap.lastDir = ConfigText(default=resolveFilename(SCOPE_MEDIA))
screensaverlist = [('default',_("default"))]
hddpath="/hdd/saver/"
if pathExists(hddpath):
	files = os_listdir(hddpath)
	for x in files:
		if pathExists(hddpath + x):
			screensaverlist += [(hddpath +'%s/' % (x),_("%s") % (x))]
config.plugins.mc_ap.whichjpg = ConfigSelection(screensaverlist)
playlist = []
#try:
#	from enigma import evfd
#except Exception, e:
#	print "Media Center: Import evfd failed"
radirl = "http://ipkserver.hdmedia-universe.com/bmcradio/"
#for lyrics
def getEncodedString(value):
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
class myHTTPClientFactory(HTTPClientFactory):
	def __init__(self, url, method='GET', postdata=None, headers=None,
	agent="SHOUTcast", timeout=0, cookies=None,
	followRedirect=1, lastModified=None, etag=None):
		HTTPClientFactory.__init__(self, url, method=method, postdata=postdata,
		headers=headers, agent=agent, timeout=timeout, cookies=cookies,followRedirect=followRedirect)
def sendUrlCommand(url, contextFactory=None, timeout=50, *args, **kwargs):
	if hasattr(client, '_parse'):
		scheme, host, port, path = client._parse(url)
	else:
			from twisted.web.client import _URI
			uri = _URI.fromBytes(url)
			scheme = uri.scheme
			host = uri.host
			port = uri.port
			path = uri.path
	factory = myHTTPClientFactory(url, *args, **kwargs)
	reactor.connectTCP(host, port, factory, timeout=timeout)
	return factory.deferred
mcpath = "/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/"
def PlaylistEntryComponent(serviceref):
	res = [ serviceref ]
	text = serviceref.getName()
	if text is "":
		text = os_path.split(serviceref.getPath().split('/')[-1])[1]
	res.append((eListboxPythonMultiContent.TYPE_TEXT,25, 1, 470, 22, 0, RT_VALIGN_CENTER, text))
	return res
class PlayList(MenuList):
	def __init__(self, enableWrapAround = False):
		MenuList.__init__(self, playlist, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 15))
		self.l.setItemHeight(23)
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
	def getCurrentIndex(self):
		return MC_AudioPlayer.currPlaying
	def getCurrentEvent(self):
		l = self.l.getCurrentSelection()
		return l and self.serviceHandler.info(l[0]).getEvent(l[0])
	def getCurrent(self):
		l = self.l.getCurrentSelection()
		return l and l[0]
	def getServiceRefList(self):
		return [ x[0] for x in self.list ]
	def __len__(self):
		return len(self.list)
class MC_AudioPlayer(Screen, HelpableScreen, InfoBarSeek):
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		InfoBarSeek.__init__(self, actionmap = "MediaPlayerSeekActions")
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
		try:
			if config.av.downmix_ac3.value == False:
				config.av.downmix_ac3.value = True
				config.av.downmix_ac3.save()
				os.system("touch /tmp/.ac3on")
		except Exception, e:
			print "Media Center: no ac3"
		self["play"] = Pixmap()
		self["green"] = Pixmap()
		self["screensaver"] = MediaPixmap()
		self.PlaySingle = 0
		MC_AudioPlayer.STATE = "NONE"
		lstdir = []
		self.playlist = PlayList()
		MC_AudioPlayer.playlistplay = 0
		MC_AudioPlayer.currPlaying = -1
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evEOF: self.doEOF,
				iPlayableService.evStopped: self.StopPlayback,
				iPlayableService.evUser+11: self.__evDecodeError,
				iPlayableService.evUser+12: self.__evPluginError,
				iPlayableService.evUser+13: self["coverArt"].embeddedCoverArt,
				iPlayableService.evUser+14: self["screensaver"].screensaver
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
		sort = config.plugins.mc_ap_sortmode.enabled.value
		self["currentfolder"].setText(str(currDir))
		self.filelist = []
		self["filelist"] = []
		inhibitDirs = ["/bin", "/boot", "/dev", "/dev.static", "/etc", "/lib" , "/proc", "/ram", "/root" , "/sbin", "/sys", "/tmp", "/usr", "/var"]
		self.filelist = FileList(currDir, useServiceRef = True, showDirectories = True, showFiles = True, matchingPattern = "(?i)^.*\.(mp2|mp3|wav|wave|wma|m4a|ogg|ra|flac|m3u|pls|e2pls)", inhibitDirs = inhibitDirs, sort = sort)
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
			self["green"].instance.setPixmapFromFile(mcpath +"icons/repeatonegreen.png")
		elif config.plugins.mc_ap.repeat.getValue() == "single":
			config.plugins.mc_ap.repeat.value = "all"
			self["green"].instance.setPixmapFromFile(mcpath +"icons/repeatallgreen.png")
		else:
			config.plugins.mc_ap.repeat.value = "off"
			self["green"].instance.setPixmapFromFile(mcpath +"icons/repeatoffgreen.png")
		config.plugins.mc_ap.save()
	def updategreen(self):
		if config.plugins.mc_ap.repeat.getValue() == "all":
			self["green"].instance.setPixmapFromFile(mcpath +"icons/repeatallgreen.png")
		elif config.plugins.mc_ap.repeat.getValue() == "single":
			self["green"].instance.setPixmapFromFile(mcpath +"icons/repeatonegreen.png")
		else:
			return
	def unlockShow(self):
		return
	def lockShow(self):
		return
	def up(self):
		self["filelist"].up()
#		if config.plugins.mc_global.vfd.value == "on":
#			evfd.getInstance().vfd_write_string(self["filelist"].getName())
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()
	def down(self):
		self["filelist"].down()
#		if config.plugins.mc_global.vfd.value == "on":
#			evfd.getInstance().vfd_write_string(self["filelist"].getName())
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()
	def leftUp(self):
		self["filelist"].pageUp()
#		if config.plugins.mc_global.vfd.value == "on":
#			evfd.getInstance().vfd_write_string(self["filelist"].getName())
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()
	def rightDown(self):
		self["filelist"].pageDown()
#		if config.plugins.mc_global.vfd.value == "on":
#			evfd.getInstance().vfd_write_string(self["filelist"].getName())
		if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
			self.screensavercheckup()
	def KeyOK(self):
		if self["filelist"].canDescent():
			if MC_AudioPlayer.STATE != "NONE" and config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
			self.filelist.descent()
			self["currentfolder"].setText(str(self.filelist.getCurrentDirectory()))
		else:
			if self.filelist.getServiceRef().type == 4098: # playlist
				ServiceRef = self.filelist.getServiceRef()
				extension = ServiceRef.getPath()[ServiceRef.getPath().rfind('.') + 1:]
				if self.playlistparsers.has_key(extension):
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
			self["play"].instance.setPixmapFromFile(mcpath +"icons/pause_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
		elif MC_AudioPlayer.STATE == "PAUSED":
			service = self.session.nav.getCurrentService()
			pausable = service.pause()
			pausable.unpause()
			MC_AudioPlayer.STATE = "PLAY"
			self["play"].instance.setPixmapFromFile(mcpath +"icons/play_enabled.png")
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
		if self.isVisible == True:
			self.isVisible = False
			self.hide()
		else:
			self.isVisible = True
			self.show()
	def Playlists(self):
		self.session.openWithCallback(self.updd, MC_AudioPlaylist)
	def updd(self):
		self.updateFileInfo()
		sort = config.plugins.mc_ap_sortmode.enabled.value
		self.filelist.refresh(sort)
		if MC_AudioPlayer.STATE == "PLAY":
			self["play"].instance.setPixmapFromFile(mcpath +"icons/play_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():	
				self.screensavercheckup()
		elif MC_AudioPlayer.STATE == "PAUSED":
			self["play"].instance.setPixmapFromFile(mcpath +"icons/pause_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():	
				self.screensavercheckup()
		elif MC_AudioPlayer.STATE == "NONE":
			self["play"].instance.setPixmapFromFile(mcpath +"icons/stop_enabled.png")
		else:
			return
	def PlayService(self):
		playlistplay = 0
		self.JpgTimer.stop()
		self.session.nav.playService(self["filelist"].getServiceRef())
		MC_AudioPlayer.STATE = "PLAY"
		self.FileInfoTimer.start(2000, True)
		self["play"].instance.setPixmapFromFile(mcpath +"icons/play_enabled.png")
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
		self["play"].instance.setPixmapFromFile(mcpath +"icons/play_enabled.png")
		if config.plugins.mc_ap.showJpg.getValue():
			time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
			self.JpgTimer.start(time, True)
		#path = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
		#self["coverArt"].updateCoverArt(path)
	def StopPlayback(self):
		if self.isVisible == False:
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
			self["play"].instance.setPixmapFromFile(mcpath +"icons/stop_enabled.png")
	def JumpToFolder(self, jumpto = None):
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
		elif self.filelist.getServiceRef().type == 4098: # playlist
			ServiceRef = self.filelist.getServiceRef()
			extension = ServiceRef.getPath()[ServiceRef.getPath().rfind('.') + 1:]
			if self.playlistparsers.has_key(extension):
				playlist = self.playlistparsers[extension]()
				list = playlist.open(ServiceRef.getPath())
				for x in list:
					self.playlist.addFile(x.ref)
				self.playlist.updateList()
		else:
			self.playlist.addFile(self.filelist.getServiceRef())
			self.playlist.updateList()
	def addDirtoPls(self, directory, recursive = True):
		if directory == '/':
			return
		filelist = FileList(directory, useServiceRef = True, showMountpoints = False, isTop = True)
		for x in filelist.getFileList():
			if x[0][1] == True: #isDir
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
			os.remove(delfile)
			sort = config.plugins.mc_ap_sortmode.enabled.value
			self.filelist.refresh(sort)
	def deleteDir(self):
		self.session.openWithCallback(self.deleteDirConfirmed, MessageBox, _("Do you really want to delete this directory and it's content ?"))
	def deleteDirConfirmed(self, confirmed):
		if confirmed:
			import shutil
			deldir = self.filelist.getSelection()[0]
			shutil.rmtree(deldir)
			sort = config.plugins.mc_ap_sortmode.enabled.value
			self.filelist.refresh(sort)
	def getJPG(self):
		if config.plugins.mc_ap.whichjpg.value == "default":
			path = mcpath +"saver/"
		else:
			path = config.plugins.mc_ap.whichjpg.value
		for root, dirs, files in os.walk(path):
			for name in files:
				if name.endswith(".jpg"):
					self.jpgList.append(name)
	def showBackgroundJPG(self):
		if len(self.jpgList) > 0:
			if self.jpgIndex < len(self.jpgList) -1:
				self.jpgIndex += 1
			else:
				self.jpgIndex = 0
			print "MediaCenter: Last JPG Index: " + str(self.jpgLastIndex)
			if self.jpgLastIndex != self.jpgIndex or self.jpgLastIndex == -1:
				if config.plugins.mc_ap.whichjpg.value == "default":
					path = mcpath +"saver/" + self.jpgList[self.jpgIndex]
				else:
					path = config.plugins.mc_ap.whichjpg.value + self.jpgList[self.jpgIndex]
				self["screensaver"].screensaver(path)
				self.jpgLastIndex = self.jpgIndex
				time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
				self.JpgTimer.start(time, True)
		else:
			print "MediaCenter: No Background Files found ..."
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
		self.session.open(MessageBox, _("This Dreambox can't decode %s video streams!") % sVideoType, type = MessageBox.TYPE_INFO,timeout = 20 )
	def __evPluginError(self):
		currPlay = self.session.nav.getCurrentService()
		message = currPlay.info().getInfoString(iServiceInformation.sUser+12)
		self.session.open(MessageBox, message, type = MessageBox.TYPE_INFO,timeout = 20 )
	def addPlaylistParser(self, parser, extension):
		self.playlistparsers[extension] = parser
	def Shuffle(self):
		if self.currPlaying == 1:
			return
		sort = "shuffle"
		self.filelist.refresh(sort)
	def showMenu(self):
		menu = []
		menu.append((_("shuffle"), "shuffle"))
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
			self.addDirtoPls(os_path.dirname(self.filelist.getSelection()[0].getPath()) + "/", recursive = False)
		elif choice[1] == "deletefile":
			self.deleteFile()
		elif choice[1] == "shuffle":
			self.Shuffle()
	def Settings(self):
		self.session.openWithCallback(self.updd, AudioPlayerSettings)
	def Exit(self):
		if self.isVisible == False:
			self.visibility()
			return
		if self.filelist.getCurrentDirectory() is None:
			config.plugins.mc_ap.lastDir.value = "devicelist"
		else:
			config.plugins.mc_ap.lastDir.value = self.filelist.getCurrentDirectory()
		self.FileInfoTimer.stop()
		del self["coverArt"].picload
		del self["screensaver"].picload
		if os.path.isfile("/tmp/.ac3on"):
			config.av.downmix_ac3.value = False
			config.av.downmix_ac3.save()
			os.remove("/tmp/.ac3on")
		config.plugins.mc_ap.save()
		if self.session.nav.getCurrentService() is not None:
			self.session.nav.stopService()
		MC_AudioPlayer.STATE = "NONE"
#		if config.plugins.mc_global.vfd.value == "on":
#			evfd.getInstance().vfd_write_string(_("My Music"))
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
		try:
			if config.av.downmix_ac3.value == False:
				config.av.downmix_ac3.value = True
				config.av.downmix_ac3.save()
				os.system("touch /tmp/.ac3on")
		except Exception, e:
			print "Media Center: no ac3"
		self["play"] = Pixmap()
		self["screensaver"] = MediaPixmap()
		MC_AudioPlayer.STATE = "NONE"
		lstdir = []
		self.playlist = PlayList()
		MC_AudioPlayer.playlistplay = 0
		MC_AudioPlayer.currPlaying = -1
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evEOF: self.doEOF,
				iPlayableService.evStopped: self.StopPlayback,
				iPlayableService.evUser+11: self.__evDecodeError,
				iPlayableService.evUser+12: self.__evPluginError,
				iPlayableService.evUser+14: self["screensaver"].screensaver
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
		currDir = mcpath +"radio/"
		if not pathExists(currDir):
			currDir = "/"
		self.filelist = []
		self["filelist"] = []
		inhibitDirs = ["/bin", "/boot", "/dev", "/dev.static", "/etc", "/lib" , "/proc", "/ram", "/root" , "/sbin", "/sys", "/tmp", "/usr", "/var"]
		self.filelist = FileList(currDir, useServiceRef = True, showDirectories = False, showFiles = True, matchingPattern = "(?i)^.*\.(m3u|pls|e2pls)", additionalExtensions = "4098:m3u 4098:e2pls 4098:pls")

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
		if self.playlistparsers.has_key(extension):
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
			self["play"].instance.setPixmapFromFile(mcpath +"icons/pause_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
		elif MC_AudioPlayer.STATE == "PAUSED":
			service = self.session.nav.getCurrentService()
			pausable = service.pause()
			pausable.unpause()
			MC_AudioPlayer.STATE = "PLAY"
			self["play"].instance.setPixmapFromFile(mcpath +"icons/play_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():
				self.screensavercheckup()
		else:
			self.KeyOK()
	def visibility(self, force=1):
		if self.isVisible == True:
			self.isVisible = False
			self.hide()
		else:
			self.isVisible = True
			self.show()
	def updd(self):
		self.updateFileInfo()
		sort = config.plugins.mc_ap_sortmode.enabled.value
		self.filelist.refresh(sort)
		if MC_AudioPlayer.STATE == "PLAY":
			self["play"].instance.setPixmapFromFile(mcpath +"icons/play_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():	
				self.screensavercheckup()
		elif MC_AudioPlayer.STATE == "PAUSED":
			self["play"].instance.setPixmapFromFile(mcpath +"icons/pause_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():	
				self.screensavercheckup()
		elif MC_AudioPlayer.STATE == "NONE":
			self["play"].instance.setPixmapFromFile(mcpath +"icons/stop_enabled.png")
		else:
			return
	def PlayServicepls(self):
		MC_AudioPlayer.playlistplay = 1
		x = self.playlist.getCurrentIndex()
		x = len(self.playlist)
		self.session.nav.playService(self.playlist.getServiceRefList()[self.playlist.getCurrentIndex()])
		MC_AudioPlayer.STATE = "PLAY"
		self.FileInfoTimer.start(2000, True)
		self["play"].instance.setPixmapFromFile(mcpath +"icons/play_enabled.png")
		if config.plugins.mc_ap.showJpg.getValue():
			time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
			self.JpgTimer.start(time, True)
		self.playlist.clear()
	def StopPlayback(self):
		if self.isVisible == False:
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
			self["play"].instance.setPixmapFromFile(mcpath +"icons/stop_enabled.png")
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
			os.remove(delfile)
			sort = config.plugins.mc_ap_sortmode.enabled.value
			self.filelist.refresh(sort)
	def getJPG(self):
		if config.plugins.mc_ap.whichjpg.value == "default":
			path = mcpath +"saver/"
		else:
			path = config.plugins.mc_ap.whichjpg.value
		for root, dirs, files in os.walk(path):
			for name in files:
				if name.endswith(".jpg"):
					self.jpgList.append(name)
	def showBackgroundJPG(self):
		if len(self.jpgList) > 0:
			if self.jpgIndex < len(self.jpgList) -1:
				self.jpgIndex += 1
			else:
				self.jpgIndex = 0
			if self.jpgLastIndex != self.jpgIndex or self.jpgLastIndex == -1:
				if config.plugins.mc_ap.whichjpg.value == "default":
					path = mcpath +"saver/" + self.jpgList[self.jpgIndex]
				else:
					path = config.plugins.mc_ap.whichjpg.value + self.jpgList[self.jpgIndex]
				self["screensaver"].screensaver(path)
				self.jpgLastIndex = self.jpgIndex
				time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
				self.JpgTimer.start(time, True)
		else:
			print "MediaCenter: No Background Files found ..."
	def doEOF(self):
		self.StopPlayback()
		if config.plugins.mc_ap.showJpg.getValue():
			self.JpgTimer.stop()
			self["screensaver"].showDefaultCover()
	def __evDecodeError(self):
		currPlay = self.session.nav.getCurrentService()
		sVideoType = currPlay.info().getInfoString(iServiceInformation.sVideoType)
		self.session.open(MessageBox, _("This Dreambox can't decode %s video streams!") % sVideoType, type = MessageBox.TYPE_INFO,timeout = 20 )
	def __evPluginError(self):
		currPlay = self.session.nav.getCurrentService()
		message = currPlay.info().getInfoString(iServiceInformation.sUser+12)
		self.session.open(MessageBox, message, type = MessageBox.TYPE_INFO,timeout = 20 )
	def addPlaylistParser(self, parser, extension):
		self.playlistparsers[extension] = parser
	def Settings(self):
		self.session.openWithCallback(self.updd, AudioPlayerSettings)
	def Exit(self):
		if self.isVisible == False:
			self.visibility()
			return
		self.FileInfoTimer.stop()
		del self["screensaver"].picload
		if os.path.isfile("/tmp/.ac3on"):
			config.av.downmix_ac3.value = False
			config.av.downmix_ac3.save()
			os.remove("/tmp/.ac3on")
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
		if fileExists("/tmp/index.html"):
			os.remove("/tmp/index.html")
		menu = []
		menu.append((_("70-80er"), "70-80er/"))
		menu.append((_("Alternative"), "Alternative/"))
		menu.append((_("Ambient"), "Ambient/"))
		menu.append((_("Artist"), "Artist/"))
		menu.append((_("Big Band"), "Big%20Band/"))
		menu.append((_("Blues"), "Blues/"))
		menu.append((_("Bluegrass"), "Bluegrass/"))
		menu.append((_("Chillout"), "Chillout/"))
		menu.append((_("Classic"), "classical/"))
		menu.append((_("Classic Rock"), "classic%20rock/"))
		menu.append((_("Countrymusic"), "Countrymusik/"))
		menu.append((_("Hip Hop"), "HipHop/"))
		menu.append((_("Hits"), "Hits/"))
		menu.append((_("Moviemusic"), "Moviemusik/"))
		menu.append((_("Oldies"), "Oldies/"))
		menu.append((_("Party"), "Party/"))
		menu.append((_("Reggae"), "Reggae/"))
		menu.append((_("Rock"), "Rock/"))
		menu.append((_("Rundfunk"), "Rundfunk/"))
		menu.append((_("Smooth"), "Smooth/"))
		menu.append((_("Soul"), "Soul/"))
		menu.append((_("Techno/House"), "Techno/"))		
		menu.append((_("Worldmusic"), "Worldmusik/"))
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title="", list=menu)
	def menuCallback(self, choice):
		if choice is None:
			return
		os.system("echo "+ choice[1] +" > /tmp/.webselect | wget -O /tmp/index.html "+ radirl +""+ choice[1])
		self.session.openWithCallback(self.updd, MC_WebDown)
class MC_WebDown(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		list = []
		if fileExists("/tmp/index.html"):
			names = open("/tmp/index.html").read().split('\n')
			for x in names:
				list.append((x, _(x)))
		self["menu"] = List(list)
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"],
		{
			"cancel": self.exit,
			"ok": self.okbuttonClick
		}, -1)
	def okbuttonClick(self):
		selection = self["menu"].getCurrent()
		if selection is not None:
			gen = open("/tmp/.webselect").read().split('\n')
			os.system("wget -O '"+ mcpath +"radio/"+ selection[1] +"' '"+ radirl +""+ gen[0] +""+ selection[1].replace(" ", "%20") +"'")
			os.remove("/tmp/index.html")
			self.close()
	def exit(self):
		os.remove("/tmp/index.html")
		self.close()
class MC_AudioPlaylist(Screen, InfoBarSeek):
	def __init__(self, session):
		Screen.__init__(self, session)
		InfoBarSeek.__init__(self, actionmap = "MediaPlayerSeekActions")
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
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evEOF: self.fileupdate,
				#iPlayableService.evStopped: self.StopPlayback,
				#iPlayableService.evUser+13: self["coverArt"].embeddedCoverArt,
				iPlayableService.evUser+14: self["screensaver"].screensaver
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
				"stop": (self.StopPlayback, "Stop"),
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
		self["play"].instance.setPixmapFromFile(mcpath +"icons/play_enabled.png")
		if config.plugins.mc_ap.showJpg.getValue():
			time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
			self.JpgTimer.start(time, True)
	#	path = self["filelist"].getCurrentDirectory()
	#	self["coverArt"].updateCoverArt(path)
	def StopPlayback(self):
		if self.isVisible == False:
			self.show()
			self.isVisible = True
		if self.session.nav.getCurrentService() is None:
			return
		else:
			self.session.nav.stopService()
			MC_AudioPlayer.STATE = "NONE"
			self["play"].instance.setPixmapFromFile(mcpath +"icons/stop_enabled.png")
			if config.plugins.mc_ap.showJpg.getValue():
				self.JpgTimer.stop()
				self["screensaver"].showDefaultCover()
	def visibility(self, force=1):
		if self.isVisible == True:
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
		self.session.openWithCallback(self.save_pls,InputBox, title=_("Please enter filename (empty = use current date)"),windowTitle = _("Save Playlist"))
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
			for i in os_listdir(playlistdir):
				listpath.append((i,playlistdir + i))
		except IOError,e:
			print "Error while scanning subdirs ",e
		self.session.openWithCallback(self.load_pls, ChoiceBox, title=_("Please select a playlist..."), list = listpath)
	def load_pls(self,path):
		if path is not None:
			self.playlist.clear()
			extension = path[0].rsplit('.',1)[-1]
			if self.playlistparsers.has_key(extension):
				playlist = self.playlistparsers[extension]()
				list = playlist.open(path[1])
				for x in list:
					self.playlist.addFile(x.ref)
			self.playlist.updateList()
	def delete_saved_playlist(self):
		listpath = []
		playlistdir = resolveFilename(SCOPE_PLAYLIST)
		try:
			for i in os_listdir(playlistdir):
				listpath.append((i,playlistdir + i))
		except IOError,e:
			print "Error while scanning subdirs ",e
		self.session.openWithCallback(self.delete_saved_pls, ChoiceBox, title=_("Please select a playlist to delete..."), list = listpath)
	def delete_saved_pls(self,path):
		if path is not None:
			self.delname = path[1]
			self.session.openWithCallback(self.delete_saved_pls_conf, MessageBox, _("Do you really want to delete %s?") % (path[1]))
	def delete_saved_pls_conf(self, confirmed):
		if confirmed:
			try:
				os_remove(self.delname)
			except OSError,e:
				self.session.open(MessageBox, _("Delete failed!"), MessageBox.TYPE_ERROR)
	def addPlaylistParser(self, parser, extension):
		self.playlistparsers[extension] = parser
	def showMenu(self):
		menu = []
		menu.append((_("delete from playlist"), "deleteentry"))
		menu.append((_("clear playlist"), "clear"))
		menu.append((_("load playlist"), "loadplaylist"));
		menu.append((_("save playlist"), "saveplaylist"));
		menu.append((_("delete saved playlist"), "deleteplaylist"));
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
			path = mcpath +"saver/"
		else:
			path = config.plugins.mc_ap.whichjpg.value
		for root, dirs, files in os.walk(path):
			for name in files:
				if name.endswith(".jpg"):
					self.jpgList.append(name)
	def showBackgroundJPG(self):
		if len(self.jpgList) > 0:
			if self.jpgIndex < len(self.jpgList) -1:
				self.jpgIndex += 1
			else:
				self.jpgIndex = 0
			if self.jpgLastIndex != self.jpgIndex or self.jpgLastIndex == -1:
				path = mcpath +"saver/" + self.jpgList[self.jpgIndex]
				self["screensaver"].screensaver(path)
				self.jpgLastIndex = self.jpgIndex
				time = config.plugins.mc_ap.jpg_delay.getValue() * 1000
				self.JpgTimer.start(time, True)
		else:
			print "MediaCenter: No Background Files found ..."
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
		<widget name="coverly" position="700,120" size="160,133" zPosition="9" valign="center" halign="center" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/skins/defaultHD/images/no_coverArt.png" transparent="1" alphatest="blend" />
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
		if curPlay is not None:
			title = curPlay.info().getInfoString(iServiceInformation.sTagTitle)
			os.system("echo '"+ str(title) +"' > /tmp/.oldplaying | echo '"+ str(title) +"' > /tmp/.curplaying ")
		self.RFTimer = eTimer()
		self.RFTimer.callback.append(self.refresh)
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evUser+11: self["coverly"].coverlyrics
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
		os.system("echo '"+ str(title) +"' > /tmp/.curplaying")
		old = open("/tmp/.oldplaying").read()
		oldtitle = old.split('\r\n')
		tit = open("/tmp/.curplaying").read()
		titlee = tit.split('\r\n')
		if oldtitle == titlee:
			return
		else:
			self.startRun()
			os.system("echo '"+ str(title) +"' > /tmp/.oldplaying")
	def startRun(self):
		text = getEncodedString(self.getLyricsFromID3Tag()).replace("\r\n","\n")
		text = text.replace("\r","\n")
		self["lyric_text"].setText(text)
	def getLyricsFromID3Tag(self):
		curPlay = self.session.nav.getCurrentService()
		if curPlay is not None:
			titlely = curPlay.info().getInfoString(iServiceInformation.sTagTitle)
			artistly = curPlay.info().getInfoString(iServiceInformation.sTagArtist)
			if titlely == "":
				titlely = curPlay.info().getName().split('/')[-1]
			if artistly == "":
				artistly = titlely
		from urllib import quote
		url = "http://api.chartlyrics.com/apiv1.asmx/SearchLyricDirect?artist=%s&song=%s" % (quote(artistly), quote(titlely))
		sendUrlCommand(url, None,10).addCallback(self.gotLyrics).addErrback(self.urlError)
		return "No lyrics found in id3-tag, trying api.chartlyrics.com..."
	def urlError(self, error = None):
		if error is not None:
			self["resulttext"].setText(str(error.getErrorMessage()))
			self["lyric_text"].setText("")
	def gotLyrics(self, xmlstring):
		from xml.etree.cElementTree import fromstring as cet_fromstring
		root = cet_fromstring(xmlstring)
		lyrictext = ""
		lyrictext = root.findtext("{http://api.chartlyrics.com/}Lyric").encode("utf-8", 'ignore')
		self["lyric_text"].setText(lyrictext)
		title = root.findtext("{http://api.chartlyrics.com/}LyricSong").encode("utf-8", 'ignore')
		artist = root.findtext("{http://api.chartlyrics.com/}LyricArtist").encode("utf-8", 'ignore')
		coverly = root.findtext("{http://api.chartlyrics.com/}LyricCovertArtUrl").encode("utf-8", 'ignore')
		os.system("wget -O /tmp/.onlinecover "+ coverly +"")
		self["coverly"].coverlyrics()
		result = _("Response -> lyrics for: %s (%s)") % (title,artist)
		self["resulttext"].setText(result)
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
			os.remove("/tmp/.onlinecover")
		if fileExists("/tmp/.curplaying") and fileExists("/tmp/.oldplaying"):
			os.system("rm -rf /tmp/.*playing")
		self.RFTimer.stop()
		self.close()
class MediaPixmap(Pixmap):
	def __init__(self):
		Pixmap.__init__(self)
		self.coverArtFileName = ""
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.paintCoverArtPixmapCB)
		self.coverFileNames = ["cover.jpg", "folder.png", "folder.jpg"]
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
		from Components.AVSwitch import AVSwitch
		sc = AVSwitch().getFramebufferScale()
		#0=Width 1=Height 2=Aspect 3=use_cache 4=resize_type 5=Background(#AARRGGBB)
		self.picload.setPara((self.instance.size().width(), self.instance.size().height(), sc[0], sc[1], False, 1, "#00000000"))
	def paintCoverArtPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr != None:
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
		self.list.append(getConfigListEntry(_("Filelist Sorting:"), config.plugins.mc_ap_sortmode.enabled))
	def keyLeft(self):
		self["configlist"].handleKey(KEY_LEFT)
	def keyRight(self):
		self["configlist"].handleKey(KEY_RIGHT)
	def keyNumber(self, number):
		self["configlist"].handleKey(KEY_0 + number)
