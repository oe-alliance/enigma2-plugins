from __future__ import print_function
from __future__ import absolute_import
from Screens.Screen import Screen
from Screens.ServiceInfo import ServiceInfoList, ServiceInfoListEntry
from enigma import iPlayableService, eRect, eServiceReference, iServiceInformation
from Screens.HelpMenu import HelpableScreen
from Components.ActionMap import ActionMap, NumberActionMap, HelpableActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.Button import Button
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import *
from Screens.InfoBar import MoviePlayer as OrgMoviePlayer
from Tools.Directories import resolveFilename, pathExists, fileExists, SCOPE_MEDIA
from .MC_Filelist import FileList
from .GlobalFunctions import shortname, MC_VideoInfoView, Showiframe
import re
import os
config.plugins.mc_vp = ConfigSubsection()
config.plugins.mc_vp_sortmode = ConfigSubsection()
sorts = [('default', _("default")), ('alpha', _("alphabet")), ('alphareverse', _("alphabet backward")), ('date', _("date")), ('datereverse', _("date backward")), ('size', _("size")), ('sizereverse', _("size backward"))]
config.plugins.mc_vp_sortmode.enabled = ConfigSelection(sorts)
config.plugins.mc_vp.dvd = ConfigSelection(default="dvd", choices=[("dvd", "dvd"), ("movie", "movie")])
config.plugins.mc_vp.lastDir = ConfigText(default=resolveFilename(SCOPE_MEDIA))


class MoviePlayer(OrgMoviePlayer):
	def __init__(self, session, service, slist=None, lastservice=None):
		self.session = session
		OrgMoviePlayer.__init__(self, session, service, slist=None, lastservice=None)
		self.skinName = "MoviePlayer"
		OrgMoviePlayer.WithoutStopClose = True

	def doEofInternal(self, playing):
		self.leavePlayer()

	def leavePlayer(self):
		self.close()


class MC_VideoPlayer(Screen, HelpableScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self["key_red"] = Button(_("Favorites"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button(_("Settings"))
		self["currentfolder"] = Label("")
		self["currentfavname"] = Label("")
		self.showiframe = Showiframe()
		self.mvion = False
		self.curfavfolder = -1
		os.system("touch /tmp/bmcmovie")
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
#				"red": (self.FavoriteFolders, "Favorite Folders"),
				"blue": (self.KeySettings, "Settings"),
			}, -2)

		currDir = config.plugins.mc_vp.lastDir.value
		if not pathExists(currDir):
			currDir = "/"
		self["currentfolder"].setText(str(currDir))
		sort = config.plugins.mc_vp_sortmode.enabled.value
		self.filelist = []
		self["filelist"] = []
		inhibitDirs = ["/bin", "/boot", "/dev", "/dev.static", "/etc", "/lib", "/proc", "/ram", "/root", "/sbin", "/sys", "/tmp", "/usr", "/var"]
		self.filelist = FileList(currDir, useServiceRef=True, showDirectories=True, showFiles=True, matchingPattern="(?i)^.*\.(ts|vob|mpg|mpeg|avi|mkv|dat|iso|img|mp4|wmv|flv|divx|mov|ogm|m2ts)", additionalExtensions=None, sort=sort)
		self["filelist"] = self.filelist
		self["filelist"].show()

	def up(self):
		self["filelist"].up()
		if self.mvion == True:
			self.showiframe.finishStillPicture()
		if self["filelist"].canDescent():
			return
		else:
			self.cover()

	def down(self):
		self["filelist"].down()
		if self.mvion == True:
			self.showiframe.finishStillPicture()
		if self["filelist"].canDescent():
			return
		else:
			self.cover()

	def leftUp(self):
		self["filelist"].pageUp()
		if self.mvion == True:
			self.showiframe.finishStillPicture()
		if self["filelist"].canDescent():
			return
		else:
			if self.mvion == True:
				self.showiframe.finishStillPicture()
			self.cover()

	def rightDown(self):
		self["filelist"].pageDown()
		if self.mvion == True:
			self.showiframe.finishStillPicture()
		if self["filelist"].canDescent():
			if self.mvion == True:
				self.showiframe.finishStillPicture()
		else:
			self.cover()

	def NextFavFolder(self):
		return

	def PrevFavFolder(self):
		return

	def showFileInfo(self):
		if self["filelist"].canDescent():
			return
		else:
			self.session.open(MC_VideoInfoView, self["filelist"].getCurrentDirectory() + self["filelist"].getFilename(), self["filelist"].getFilename(), self["filelist"].getServiceRef())

	def KeyOk(self):
		self.filename = self.filelist.getFilename()
		print(self.filename)
		try:
			if self.filename.endswith('.img') or self.filename.endswith('.iso') or self.filename.endswith('VIDEO_TS/') and config.plugins.mc_vp.dvd.value == "dvd":
				self.showiframe.finishStillPicture()
				from Screens import DVD
				if self.filename.endswith('VIDEO_TS/'):
					path = os.path.split(self.filename.rstrip('/'))[0]
				else:
					path = self.filename
				self.session.open(DVD.DVDPlayer, dvd_filelist=[path])
				return
		except Exception as e:
			print("DVD Player error:", e)
		if self.filelist.canDescent():
			self.filelist.descent()
		else:
			self.showiframe.finishStillPicture()
			self.session.open(MoviePlayer, self["filelist"].getServiceRef(), slist=None, lastservice=None)

	def cover(self):
		filename = self["filelist"].getName()
		short = shortname(filename)
		newshort = short.lower()
		newshort = newshort.replace(" ", "")
		movienameserie = re.sub("e[0-9]{2}", "", newshort.lower())
		covername = "/hdd/bmcover/" + str(movienameserie) + "/backcover.mvi"
		if fileExists(covername):
			self.showiframe.showStillpicture(covername)
			self.mvion = True
		else:
			if self.mvion == True:
				self.showiframe.showStillpicture("/usr/share/enigma2/black.mvi")
				self.mvion = False

	def KeyMenu(self):
#		if self["filelist"].canDescent():
#			if self.filelist.getCurrent()[0][1]:
#				self.currentDirectory = self.filelist.getCurrent()[0][0]
#				if self.currentDirectory is not None:
#					foldername = self.currentDirectory.split('/')
#					foldername = foldername[-2]
#					self.session.open(MC_FolderOptions,self.currentDirectory, foldername)
		return

	def updd(self):
		sort = config.plugins.mc_vp_sortmode.enabled.value
		self.filelist.refresh(sort)

	def KeySettings(self):
		self.session.openWithCallback(self.updd, VideoPlayerSettings)

	def Exit(self):
		if self.filelist.getCurrentDirectory() is None:
			config.plugins.mc_vp.lastDir.value = "/"
		else:
			config.plugins.mc_vp.lastDir.value = self.filelist.getCurrentDirectory()
		config.plugins.mc_vp.save()
		try:
			os.remove("/tmp/bmcmovie")
		except:
			pass
		self.showiframe.finishStillPicture()
		self.close()


class VideoPlayerSettings(Screen, ConfigListScreen):
	skin = """
		<screen position="160,220" size="400,120" title="Media Center - VideoPlayer Settings" >
			<widget name="config" position="10,10" size="380,100" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = NumberActionMap(["SetupActions", "OkCancelActions"],
		{
			"ok": self.keyOK,
			"cancel": self.keyOK
		}, -1)
		self.list = []
		self.list.append(getConfigListEntry(_("Play DVD as:"), config.plugins.mc_vp.dvd))
		self.list.append(getConfigListEntry(_("Filelist Sorting:"), config.plugins.mc_vp_sortmode.enabled))
		ConfigListScreen.__init__(self, self.list, session)

	def keyOK(self):
		config.plugins.mc_vp.save()
		self.close()
