from __future__ import print_function
from enigma import ePicLoad, eTimer, getDesktop, iPlayableService, eServiceReference
from Components.Label import Label
from Components.Button import Button
from Components.FileList import FileList
from Components.Sources.List import List
from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.Pixmap import Pixmap, MovingPixmap
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigSelection, ConfigEnableDisable, ConfigText, KEY_LEFT, KEY_RIGHT, KEY_0, getConfigListEntry
from Screens.Screen import Screen
from Screens.Setup import Setup
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarNotifications
from Tools.Directories import resolveFilename, pathExists, SCOPE_MEDIA

config.plugins.mc_pp = ConfigSubsection()
config.plugins.mc_pp.slidetime = ConfigInteger(default=10, limits=(5, 60))
config.plugins.mc_pp.resize = ConfigSelection(default="0", choices=[("0", _("simple")), ("1", _("better"))])
config.plugins.mc_pp.cache = ConfigEnableDisable(default=True)
config.plugins.mc_pp.lastDir = ConfigText(default=resolveFilename(SCOPE_MEDIA))
config.plugins.mc_pp.rotate = ConfigSelection(default="0", choices=[("0", _("none")), ("1", _("manual")), ("2", _("by Exif"))])
config.plugins.mc_pp.ThumbWidth = ConfigInteger(default=145, limits=(1, 999))
config.plugins.mc_pp.ThumbHeight = ConfigInteger(default=120, limits=(1, 999))
config.plugins.mc_pp.bgcolor = ConfigSelection(default="#00000000", choices=[("#00000000", _("black")), ("#009eb9ff", _("blue")), ("#00ff5a51", _("red")), ("#00ffe875", _("yellow")), ("#0038FF48", _("green"))])
config.plugins.mc_pp.textcolor = ConfigSelection(default="#0038FF48", choices=[("#00000000", _("black")), ("#009eb9ff", _("blue")), ("#00ff5a51", _("red")), ("#00ffe875", _("yellow")), ("#0038FF48", _("green"))])
config.plugins.mc_pp.framesize = ConfigInteger(default=30, limits=(5, 99))
config.plugins.mc_pp.infoline = ConfigEnableDisable(default=True)
config.plugins.mc_pp.loop = ConfigEnableDisable(default=True)
config.plugins.mc_pp.music = ConfigText(default=resolveFilename(SCOPE_MEDIA))
config.plugins.mc_pp.musicenable = ConfigEnableDisable(default=False)
mcpath = "/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/"


def getAspect():
	val = AVSwitch().getAspectRatioSetting()
	return val / 2


def getScale():
	return (1, 1)


class MC_PictureViewer(Screen, HelpableScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self["key_green"] = Button("Slide Show")
		self["key_yellow"] = Button("Thumb View")
		self["currentfolder"] = Label("")
		self["currentfavname"] = Label("")
		self["actions"] = HelpableActionMap(self, "MC_PictureViewerActions",
			{
				"ok": (self.KeyOk, "Show Picture"),
				"cancel": (self.Exit, "Exit Picture Viewer"),
				"left": (self.leftUp, "List Top"),
				"right": (self.rightDown, "List Bottom"),
				"up": (self.up, "List up"),
				"down": (self.down, "List down"),
				"info": (self.StartExif, "Show File Info"),
				"green": (self.startslideshow, "Start Slideshow"),
				"yellow": (self.StartThumb, "Thumb View"),
				"blue": (self.Settings, "Settings"),
			}, -2)

		self.aspect = getAspect()
		currDir = config.plugins.mc_pp.lastDir.value
		if not pathExists(currDir):
			currDir = "/"
		self["currentfolder"].setText(str(currDir))
		inhibitDirs = ["/bin", "/boot", "/dev", "/dev.static", "/etc", "/lib", "/proc", "/ram", "/root", "/sbin", "/sys", "/tmp", "/usr", "/var"]
		self.filelist = FileList(currDir, showDirectories=True, showFiles=True, showMountpoints=True, isTop=False, matchingPattern=r"(?i)^.*\.(jpeg|jpg|jpe|png|bmp)", inhibitDirs=inhibitDirs)
		self["filelist"] = self.filelist
		self["filelist"].show()
		self["thumbnail"] = Pixmap()
		self.ThumbTimer = eTimer()
		self.ThumbTimer.callback.append(self.showThumb)
		self.ThumbTimer.start(500, True)

		self.picload = ePicLoad()
		#self.picload.PictureData.get().append(self.showPic)

	def startslideshow(self):
		self.session.openWithCallback(self.returnVal, MC_PicView, self.filelist.getFileList(), self.filelist.getSelectionIndex(), self.filelist.getCurrentDirectory(), True)

	def up(self):
		self["filelist"].up()
		self.ThumbTimer.start(500, True)

	def down(self):
		self["filelist"].down()
		self.ThumbTimer.start(500, True)

	def leftUp(self):
		self["filelist"].pageUp()
		self.ThumbTimer.start(500, True)

	def rightDown(self):
		self["filelist"].pageDown()
		self.ThumbTimer.start(500, True)

	def showPic(self, picInfo=""):
		ptr = self.picload.getData()
		if ptr is not None:
			self["thumbnail"].instance.setPixmap(ptr.__deref__())
			self["thumbnail"].show()

	def showThumb(self):
		return
		if not self.filelist.canDescent():
			if self.picload.getThumbnail(self.filelist.getPath()) == 1:
				ptr = self.picload.getData()
			else:
				ptr = None

			#ptr = loadPic(self.filelist.getPath(), 180, 160, self.aspect, int(config.plugins.mc_pp.resize.value), 0, 0, cachefile)
			if ptr is not None:
				self["thumbnail"].instance.setPixmap(ptr.__deref__())
				self["thumbnail"].show()
		else:
			self["thumbnail"].hide()

	def KeyOk(self):
		if self.filelist.canDescent():
			self.filelist.descent()
		else:
			self.session.openWithCallback(self.returnVal, MC_PicView, self.filelist.getFileList(), self.filelist.getSelectionIndex(), self.filelist.getCurrentDirectory(), False)

	def StartThumb(self):
		self.session.openWithCallback(self.returnVal, MC_PicThumbViewer, self.filelist.getFileList(), self.filelist.getSelectionIndex(), self.filelist.getCurrentDirectory())

	def JumpToFolder(self, jumpto=None):
		if jumpto is None:
			return
		else:
			self["filelist"].changeDir(jumpto)
			self["currentfolder"].setText(("%s") % (jumpto))

	def returnVal(self, val=0):
		if val > 0:
			for x in self.filelist.getFileList():
				if x[0][1] is True:
					val += 1
			self.filelist.moveToIndex(val)

	def StartExif(self):
		if not self.filelist.canDescent():
			#self.session.open(Pic_Exif, self.filelist.getPath(), self.filelist.getFilename())
			#self.session.open(Pic_Exif, self.picload.getInfo(self.filelist.getSelectionIndex()))
			self.session.open(MessageBox, "Oh no, bugged in this version :(", MessageBox.TYPE_ERROR)

	def Settings(self):
		self.session.open(MC_PicSetup)

	def Exit(self):
		directory = self.filelist.getCurrentDirectory()
		config.plugins.mc_pp.lastDir.value = directory if directory else "/"
		config.plugins.mc_pp.save()
		self.close()


#-------------------------------------------------------#
T_INDEX = 0
T_FRAME_POS = 1
T_PAGE = 2
T_NAME = 3
T_FULL = 4


class MC_PicThumbViewer(Screen, HelpableScreen):
	def __init__(self, session, piclist, lastindex, path):
		self["key_red"] = Button("")
		self["key_green"] = Button("Slide Show")
		self["key_yellow"] = Button("File View")
		self["key_blue"] = Button(_("Settings"))
		self.textcolor = config.plugins.mc_pp.textcolor.value
		self.color = config.plugins.mc_pp.bgcolor.value
		textsize = 20
		self.spaceX = 20
		self.spaceY = 28
		self.picX = config.plugins.mc_pp.ThumbWidth.value
		self.picY = config.plugins.mc_pp.ThumbHeight.value
		size_w = getDesktop(0).size().width()
		size_h = getDesktop(0).size().height()
		self.old_index = 0

		if size_w == 1280:
			self.spaceTop = 130
			self.spaceLeft = 50
			self.ButtonPosY = 95
		else:
			self.spaceTop = 120
			self.spaceLeft = 25
			self.ButtonPosY = 72

		thumbsX = int(size_w / (self.spaceX + self.picX))  # thumbnails in X
		self.thumbsY = size_h / (self.spaceY + self.picY)  # thumbnails in Y
		self.thumbsX = int(thumbsX)  # thumbnails in X
		self.thumbsC = int(thumbsX * self.thumbsY)  # all thumbnails
		self.positionlist = []
		skincontent = ""

		posX = -1
		for x in range(self.thumbsC):
			posY = int(x / self.thumbsX)
			posX += 1
			if posX >= self.thumbsX:
				posX = 0
			absX = self.spaceLeft + self.spaceX + (posX * (self.spaceX + self.picX))
			absY = self.spaceTop + self.spaceY + (posY * (self.spaceY + self.picY))
			self.positionlist.append((absX, absY))
			skincontent += "<widget name=\"label" + str(x) + "\" position=\"" + str(absX + 5) + "," + str(absY + self.picY - textsize) + "\" size=\"" + str(self.picX - 10) + "," + str(textsize) + "\" font=\"Regular;14\" zPosition=\"2\" transparent=\"1\" noWrap=\"1\" foregroundColor=\"" + self.textcolor + "\" />"
			skincontent += "<widget name=\"thumb" + str(x) + "\" position=\"" + str(absX + 5) + "," + str(absY + 5) + "\" size=\"" + str(self.picX - 10) + "," + str(self.picY - (textsize * 2)) + "\" zPosition=\"2\" transparent=\"1\" alphatest=\"on\" />"
		# Screen, buttons, backgroundlabel and MovingPixmap
		self.skin = "<screen position=\"0,0\" size=\"" + str(size_w) + "," + str(size_h) + "\" flags=\"wfNoBorder\" > \
			<ePixmap name=\"mb_bg\" position=\"0,0\" zPosition=\"1\" size=\"" + str(size_w) + "," + str(size_h) + "\" pixmap=\"" + mcpath + "skins/defaultHD/images/background.png\" scale=\"1\" /> \
			<ePixmap pixmap=\"" + mcpath + "icons/key_red.png\" position=\"60," + str(self.ButtonPosY) + "\" zPosition=\"2\" size=\"35,35\" transparent=\"1\" alphatest=\"on\" scale=\"1\" /> \
			<ePixmap pixmap=\"" + mcpath + "icons/key_green.png\" position=\"260," + str(self.ButtonPosY) + "\" zPosition=\"2\" size=\"35,35\" transparent=\"1\" alphatest=\"on\" scale=\"1\" /> \
			<ePixmap pixmap=\"" + mcpath + "icons/key_yellow.png\" position=\"460," + str(self.ButtonPosY) + "\" zPosition=\"2\" size=\"35,35\" transparent=\"1\" alphatest=\"on\" scale=\"1\" /> \
			<ePixmap pixmap=\"" + mcpath + "icons/key_blue.png\" position=\"660," + str(self.ButtonPosY) + "\" zPosition=\"2\" size=\"35,35\" transparent=\"1\" alphatest=\"on\" scale=\"1\" /> \
			<widget name=\"key_red\" position=\"100," + str(self.ButtonPosY) + "\" zPosition=\"3\" size=\"180,40\" font=\"Regular;20\" valign=\"center\" halign=\"center\" backgroundColor=\"#000000\" transparent=\"1\" /> \
			<widget name=\"key_green\" position=\"270," + str(self.ButtonPosY) + "\" zPosition=\"3\" size=\"180,35\" font=\"Regular;20\" valign=\"center\" halign=\"center\" backgroundColor=\"#000000\" transparent=\"1\" /> \
			<widget name=\"key_yellow\" position=\"460," + str(self.ButtonPosY) + "\" zPosition=\"3\" size=\"180,35\" font=\"Regular;20\" valign=\"center\" halign=\"center\" backgroundColor=\"#000000\" transparent=\"1\" /> \
			<widget name=\"key_blue\" position=\"680," + str(self.ButtonPosY) + "\" zPosition=\"3\" size=\"180,35\" font=\"Regular;20\" valign=\"center\" halign=\"center\" backgroundColor=\"#000000\" transparent=\"1\" /> \
			<eLabel position=\"0,0\" zPosition=\"0\" size=\"" + str(size_w) + "," + str(size_h) + "\" backgroundColor=\"" + self.color + "\" /> \
			<widget name=\"frame\" position=\"30,25\" size=\"" + str(self.picX + 1) + "," + str(self.picY + 10) + "\" pixmap=\"" + mcpath + "icons/pic_frame.png\" zPosition=\"3\" alphatest=\"on\" scale=\"1\" />" + skincontent + "</screen>"
		Screen.__init__(self, session)

		self["actions"] = HelpableActionMap(self, "MC_PictureViewerActions",
		{
			"ok": (self.KeyOk, "Show Picture"),
			"cancel": (self.Exit, "Exit Picture Viewer"),
			"left": (self.key_left, "List Top"),
			"right": (self.key_right, "List Bottom"),
			"up": (self.key_up, "List up"),
			"down": (self.key_down, "List down"),
			"info": (self.StartExif, "Show File Info"),
			"green": (self.startslideshow, "Start Slideshow"),
			"yellow": (self.close, "File View"),
			"blue": (self.Settings, "Settings"),
		}, -2)
		self["frame"] = MovingPixmap()
		for x in range(self.thumbsC):
			self["label" + str(x)] = Label()
			self["thumb" + str(x)] = Pixmap()
		self.Thumbnaillist = []
		self.filelist = []
		self.currPage = -1
		self.dirlistcount = 0
		self.path = path
		index = 0
		framePos = 0
		Page = 0
		for x in piclist:
			if x[0][1] is False:
				self.filelist.append((index, framePos, Page, x[0][4], x[0][0]))
				index += 1
				framePos += 1
				if framePos > (self.thumbsC - 1):
					framePos = 0
					Page += 1
			else:
				self.dirlistcount += 1

		self.maxentry = len(self.filelist) - 1
		self.index = lastindex - self.dirlistcount
		if self.index < 0:
			self.index = 0

		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.showPic)
		self.onLayoutFinish.append(self.setPicloadConf)
		self.ThumbTimer = eTimer()
		self.ThumbTimer.callback.append(self.showPic)

	def setPicloadConf(self):
		sc = getScale()
		self.picload.setPara([self["thumb0"].instance.size().width(), self["thumb0"].instance.size().height(), sc[0], sc[1], config.plugins.mc_pp.cache.value, int(config.plugins.mc_pp.resize.value), self.color])
		self.paintFrame()

	def paintFrame(self):
		#print "index=" + str(self.index)
		if self.maxentry < self.index or self.index < 0:
			return

		pos = self.positionlist[self.filelist[self.index][T_FRAME_POS]]
		self["frame"].moveTo(pos[0], pos[1], 1)
		self["frame"].startMoving()
		if self.currPage != self.filelist[self.index][T_PAGE]:
			self.currPage = self.filelist[self.index][T_PAGE]
			self.newPage()

	def newPage(self):
		self.Thumbnaillist = []
		#clear Labels and Thumbnail
		for x in range(self.thumbsC):
			self["label" + str(x)].setText("")
			self["thumb" + str(x)].hide()
		#paint Labels and fill Thumbnail-List
		for x in self.filelist:
			if x[T_PAGE] == self.currPage:
				self["label" + str(x[T_FRAME_POS])].setText("(" + str(x[T_INDEX] + 1) + ") " + x[T_NAME])
				self.Thumbnaillist.append([0, x[T_FRAME_POS], x[T_FULL]])
		#paint Thumbnail start
		self.showPic()

	def showPic(self, picInfo=""):
		for x in range(len(self.Thumbnaillist)):
			if self.Thumbnaillist[x][0] == 0:
				if self.picload.getThumbnail(self.Thumbnaillist[x][2]) == 1:  # zu tun probier noch mal
					self.ThumbTimer.start(500, True)
				else:
					self.Thumbnaillist[x][0] = 1
				break
			elif self.Thumbnaillist[x][0] == 1:
				self.Thumbnaillist[x][0] = 2
				ptr = self.picload.getData()
				if ptr is not None:
					self["thumb" + str(self.Thumbnaillist[x][1])].instance.setPixmap(ptr.__deref__())
					self["thumb" + str(self.Thumbnaillist[x][1])].show()

	def key_left(self):
		self.index -= 1
		if self.index < 0:
			self.index = self.maxentry
		self.paintFrame()

	def key_right(self):
		self.index += 1
		if self.index > self.maxentry:
			self.index = 0
		self.paintFrame()

	def key_up(self):
		self.index -= self.thumbsX
		if self.index < 0:
			self.index = self.maxentry
		self.paintFrame()

	def key_down(self):
		self.index += self.thumbsX
		if self.index > self.maxentry:
			self.index = 0
		self.paintFrame()

	def StartExif(self):
		if self.maxentry < 0:
			return
		self.session.open(Pic_Exif, self.picload.getInfo(self.filelist[self.index][T_FULL]))

	def KeyOk(self):
		if self.maxentry < 0:
			return
		self.old_index = self.index
		self.session.openWithCallback(self.callbackView, MC_PicView, self.filelist, self.index, self.path, False)

	def startslideshow(self):
		if self.maxentry < 0:
			return
		self.session.openWithCallback(self.callbackView, MC_PicView, self.filelist, self.index, self.path, True)

	def Settings(self):
		self.session.open(MC_PicSetup)

	def callbackView(self, val=0):
		self.index = val
		if self.old_index != self.index:
			self.paintFrame()

	def Exit(self):
		del self.picload
		self.close(self.index + self.dirlistcount)
#-------------------------------------------------------#


class MC_PicView(Screen, InfoBarBase, InfoBarSeek, InfoBarNotifications, HelpableScreen):
	def __init__(self, session, filelist, index, path, startslide):
		self.textcolor = config.plugins.mc_pp.textcolor.value
		self.bgcolor = config.plugins.mc_pp.bgcolor.value
		space = config.plugins.mc_pp.framesize.value
		size_w = getDesktop(0).size().width()
		size_h = getDesktop(0).size().height()

		self.skin = "<screen position=\"0,0\" size=\"" + str(size_w) + "," + str(size_h) + "\" flags=\"wfNoBorder\" > \
			<eLabel position=\"0,0\" zPosition=\"0\" size=\"" + str(size_w) + "," + str(size_h) + "\" backgroundColor=\"" + self.bgcolor + "\" /><widget name=\"pic\" position=\"" + str(space) + "," + str(space) + "\" size=\"" + str(size_w - (space * 2)) + "," + str(size_h - (space * 2)) + "\" zPosition=\"1\" alphatest=\"on\" /> \
			<widget name=\"point\" position=\"" + str(space + 30) + "," + str(space + 5) + "\" size=\"24,15\" zPosition=\"3\"  pixmap=\"" + mcpath + "icons/BlinkingPoint-fs8.png\" alphatest=\"on\" scale=\"1\" /> \
			<widget name=\"play_icon\" position=\"" + str(space + 25) + "," + str(space + 2) + "\" size=\"24,24\" zPosition=\"2\" pixmap=\"" + mcpath + "icons/ico_mp_play.png\"  alphatest=\"on\" scale=\"1\" /> \
            <ePixmap name=\"info\" position=\"e-80,e-60\" zPosition=\"6\" size=\"60,36\" pixmap=\"" + mcpath + "icons/key_info.png\" scale=\"1\" /> \
            <ePixmap name=\"bg_file\" position=\"50,15\" zPosition=\"1\" size=\"600,50\"  pixmap=\"" + mcpath + "skins/defaultHD/images/BG_file.png\" alphatest=\"on\" scale=\"1\" /> \
			<widget name=\"file\" position=\"" + str(space + 65) + "," + str(space) + "\" size=\"" + str(size_w - (space * 2) - 50) + ",25\" font=\"Regular;20\" halign=\"left\" foregroundColor=\"" + self.textcolor + "\" zPosition=\"2\" noWrap=\"1\" transparent=\"1\" /></screen>"

		Screen.__init__(self, session)
		InfoBarBase.__init__(self)
		InfoBarSeek.__init__(self, actionmap="MediaPlayerSeekActions")
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "InfoActions"],
		{
			"cancel": self.Exit,
			"green": self.PlayPause,
			"yellow": self.PlayPause,
			"blue": self.nextPic,
			"red": self.prevPic,
			"left": self.prevPic,
			"right": self.nextPic,
			"info": self.StartExif,
		}, -1)
		self["point"] = Pixmap()
		self["pic"] = Pixmap()
		self["play_icon"] = Pixmap()
		self["file"] = Label(_("please wait, loading picture..."))

		self.old_index = 0
		self.filelist = []
		self.lastindex = index
		self.currPic = []
		self.shownow = True
		self.dirlistcount = 0

		for x in filelist:
			if len(filelist[0]) == 3:  # orig. filelist
				if x[0][1] is False:
					self.filelist.append(x[0][0])
				else:
					self.dirlistcount += 1
			else:  # thumbnaillist
				self.filelist.append(x[T_FULL])

		self.maxentry = len(self.filelist) - 1
		self.index = index - self.dirlistcount
		if self.index < 0:
			self.index = 0

		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.finish_decode)

		self.slideTimer = eTimer()
		self.slideTimer.callback.append(self.slidePic)

		if self.maxentry >= 0:
			self.onLayoutFinish.append(self.setPicloadConf)
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evEOF: self.doEOF,
			})
		if startslide is True:
			self.PlayPause()
			if config.plugins.mc_pp.musicenable.value is True and config.plugins.mc_pp.music.value != "none":
				if pathExists(config.plugins.mc_pp.music.value):
					self.session.nav.playService(eServiceReference(4097, 0, config.plugins.mc_pp.music.value))

	def setPicloadConf(self):
		sc = getScale()
		self.picload.setPara([self["pic"].instance.size().width(), self["pic"].instance.size().height(), sc[0], sc[1], 0, int(config.plugins.mc_pp.resize.value), self.bgcolor])
		self["play_icon"].hide()
		if config.plugins.mc_pp.infoline.value is False:
			self["file"].hide()
		self.start_decode()

	def checkSkipShowHideLock(self):
		self.updatedSeekState()

	def updatedSeekState(self):
		return  # TODO
		if self.seekstate == self.SEEK_STATE_PAUSE:
			self.playlist.pauseFile()
		elif self.seekstate == self.SEEK_STATE_PLAY:
			self.playlist.playFile()
		elif self.isStateForward(self.seekstate):
			self.playlist.forwardFile()
		elif self.isStateBackward(self.seekstate):
			self.playlist.rewindFile()

	def doEOF(self):
		self.session.nav.stopService()
		if config.plugins.mc_pp.musicenable.value is True and config.plugins.mc_pp.music.value != "none":
			if pathExists(config.plugins.mc_pp.music.value):
				self.session.nav.playService(eServiceReference(4097, 0, config.plugins.mc_pp.music.value))

	def ShowPicture(self):
		if self.shownow and len(self.currPic):
			self.shownow = False
			self["file"].setText(self.currPic[0])
			self.lastindex = self.currPic[1]
			self["pic"].instance.setPixmap(self.currPic[2].__deref__())
			self.currPic = []
			self.next()
			self.start_decode()

	def finish_decode(self, picInfo=""):
		self["point"].hide()
		ptr = self.picload.getData()
		if ptr is not None:
			text = ""
			try:
				text = picInfo.split('\n', 1)
				text = "(" + str(self.index + 1) + "/" + str(self.maxentry + 1) + ") " + text[0].split('/')[-1]
			except:
				pass
			self.currPic = []
			self.currPic.append(text)
			self.currPic.append(self.index)
			self.currPic.append(ptr)
			self.ShowPicture()

	def start_decode(self):
		self.picload.startDecode(self.filelist[self.index])
		self["point"].show()

	def next(self):
		self.index += 1
		if self.index > self.maxentry:
			self.index = 0

	def prev(self):
		self.index -= 1
		if self.index < 0:
			self.index = self.maxentry

	def slidePic(self):
		print("slide to next Picture index=" + str(self.lastindex))
		if config.plugins.mc_pp.loop.value is False and self.lastindex == self.maxentry:
			self.PlayPause()
		self.shownow = True
		self.ShowPicture()

	def PlayPause(self):
		if self.slideTimer.isActive():
			self.slideTimer.stop()
			self["play_icon"].hide()
		else:
			self.slideTimer.start(config.plugins.mc_pp.slidetime.value * 1000)
			self["play_icon"].show()
			self.nextPic()

	def prevPic(self):
		self.currPic = []
		self.index = self.lastindex
		self.prev()
		self.start_decode()
		self.shownow = True

	def nextPic(self):
		self.shownow = True
		self.ShowPicture()

	def StartExif(self):
		if self.maxentry < 0:
			return
		self.session.open(Pic_Exif, self.picload.getInfo(self.filelist[self.lastindex]))

	def Exit(self):
		del self.picload
		self.session.nav.stopService()
		self.close(self.lastindex + self.dirlistcount)
#-------------------------------------------------------#


class Pic_Exif(Screen):
	def __init__(self, session, exiflist):
		self.skin = """<screen position="80,120" size="560,360" title="Info" >
				<widget source="menu" render="Listbox" position="0,0" size="560,360" scrollbarMode="showOnDemand" selectionDisabled="1" >
				<convert type="TemplatedMultiContent">
					{"template": [  MultiContentEntryText(pos = (5, 5), size = (250, 30), flags = RT_HALIGN_LEFT, text = 0), MultiContentEntryText(pos = (260, 5), size = (290, 30), flags = RT_HALIGN_LEFT, text = 1)], "fonts": [gFont("Regular", 20)], "itemHeight": 30 }
				</convert>
				</widget>
			</screen>"""
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["OkCancelActions"],
		{
			"cancel": self.close
		}, -1)

		exifdesc = [_("filename") + ':', "EXIF-Version:", "Make:", "Camera:", "Date/Time:", "Width / Height:", "Flash used:", "Orientation:", "User Comments:", "Metering Mode:", "Exposure Program:", "Light Source:", "CompressedBitsPerPixel:", "ISO Speed Rating:", "X-Resolution:", "Y-Resolution:", "Resolution Unit:", "Brightness:", "Exposure Time:", "Exposure Bias:", "Distance:", "CCD-Width:", "ApertureFNumber:"]
		list = []

		for x in range(len(exiflist)):
			if x > 0:
				list.append((exifdesc[x], exiflist[x]))
			else:
				name = exiflist[x].split('/')[-1]
				list.append((exifdesc[x], name))
		self["menu"] = List(list)
#-------------------------------------------------------#


class MC_PicSetup(Setup):
	def __init__(self, session):
		Setup.__init__(self, session, "MC_PicSetup", plugin="Extensions/BMediaCenter", PluginLanguageDomain="BMediaCenter")

	def keySelect(self):
		if self.getCurrentItem() == config.plugins.mc_pp.music:
			self.session.open(Selectmusic)
		else:
			Setup.keySelect(self)


class Selectmusic(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = HelpableActionMap(self, "MC_AudioPlayerActions",
			{
				"ok": (self.KeyOk, "Play selected file"),
				"left": (self.leftUp, "List Top"),
				"right": (self.rightDown, "List Bottom"),
				"up": (self.up, "List up"),
				"down": (self.down, "List down"),
			}, -2)
		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
				"cancel": self.close
			}, -2)
		currDir = config.plugins.mc_ap.lastDir.value
		if not pathExists(currDir):
			currDir = "/"
		inhibitDirs = ["/bin", "/boot", "/dev", "/dev.static", "/etc", "/lib", "/proc", "/ram", "/root", "/sbin", "/sys", "/tmp", "/usr", "/var"]
		self.filelist = FileList(currDir, useServiceRef=True, showDirectories=True, showFiles=True, matchingPattern=r"(?i)^.*\.(m3u|mp2|mp3|wav|wave|pls|wma|m4a|ogg|ra|flac)", inhibitDirs=inhibitDirs)
		self["filelist"] = self.filelist
		self["currentfolder"] = Label()
		self["currentfolder"].setText(str(currDir))

	def up(self):
		self["filelist"].up()

	def down(self):
		self["filelist"].down()

	def leftUp(self):
		self["filelist"].pageUp()

	def rightDown(self):
		self["filelist"].pageDown()

	def KeyOk(self):
		self.filename = self.filelist.getFilename()
		self["currentfolder"].setText(str(self.filelist.getCurrentDirectory()))
		if self.filelist.getFilename() is not None:
			if self.filelist.canDescent():
				self.filelist.descent()
			else:
				config.plugins.mc_pp.music.value = self.filename
				config.plugins.mc_pp.save()
				self.close()
		else:
			if self.filelist.canDescent():
				self.filelist.descent()
			else:
				config.plugins.mc_pp.music.value = self.filename
				config.plugins.mc_pp.save()
				self.close()
