from datetime import datetime
from re import sub, I
from os import system, remove
from os.path import basename, split, splitext, exists
from requests import get, exceptions
from glob import glob
from shutil import move
from . import tmdbsimple as tmdb
from enigma import getDesktop, eTimer
from Components.Label import Label
from Components.Button import Button
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigText, getConfigListEntry, ConfigYesNo
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import NumberActionMap, HelpableActionMap
from Components.Language import language
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.InfoBar import MoviePlayer as OrgMoviePlayer
from Tools.Directories import resolveFilename, pathExists, fileExists, SCOPE_MEDIA
from Components.Sources.ServiceEvent import ServiceEvent
from Screens.MessageBox import MessageBox
from twisted.internet.reactor import callInThread
from .MC_Filelist import FileList
from .GlobalFunctions import shortname, Showiframe
try:
	from Tools.EITFile import EITFile
except ImportError:
	EITFile = None

config.plugins.mc_vp = ConfigSubsection()
config.plugins.mc_vp_sortmode = ConfigSubsection()
sorts = [('default', _("default")), ('alpha', _("alphabet")), ('alphareverse', _("alphabet backward")), ('date', _("date")), ('datereverse', _("date backward")), ('size', _("size")), ('sizereverse', _("size backward"))]
config.plugins.mc_vp_sortmode.enabled = ConfigSelection(sorts)
config.plugins.mc_vp.dvd = ConfigSelection(default="dvd", choices=[("dvd", "dvd"), ("movie", "movie")])
config.plugins.mc_vp.lastDir = ConfigText(default=resolveFilename(SCOPE_MEDIA))
config.plugins.mc_vp.themoviedb_coversize = ConfigSelection(default="w185", choices=["w92", "w185", "w500", "original"])
config.plugins.mc_vp.themoviedb_fullinfo = ConfigYesNo(default=True)

tmdb.API_KEY = 'd42e6b820a1541cc69ce789671feba39'
COVERTMP = "/tmp/bmc.jpg"
INFOTMP = "/tmp/bmc.txt"


class TMDB():
	def __init__(self):
		self.coverSize = config.plugins.mc_vp.themoviedb_coversize.value
		self.lang = language.getLanguage().split("_", 1)[0]
		if len(self.lang) < 2:
			self.lang = "en"
		self.coverFilename = None

	def cleanFile(self, text):
		cutlist = ['x264', '720p', '1080p', '1080i', 'PAL', 'GERMAN', 'ENGLiSH', 'WS', 'DVDRiP', 'UNRATED', 'RETAIL', 'Web-DL', 'DL', 'LD', 'MiC', 'MD', 'DVDR', 'BDRiP', 'BLURAY', 'DTS', 'UNCUT', 'ANiME',
					'AC3MD', 'AC3', 'AC3D', 'TS', 'DVDSCR', 'COMPLETE', 'INTERNAL', 'DTSD', 'XViD', 'DIVX', 'DUBBED', 'LINE.DUBBED', 'DD51', 'DVDR9', 'DVDR5', 'h264', 'AVC',
					'WEBHDTVRiP', 'WEBHDRiP', 'WEBRiP', 'WEBHDTV', 'WebHD', 'HDTVRiP', 'HDRiP', 'HDTV', 'ITUNESHD', 'REPACK', 'SYNC']
		#text = text.replace('.wmv', '').replace('.flv', '').replace('.ts', '').replace('.m2ts', '').replace('.mkv', '').replace('.avi', '').replace('.mpeg', '').replace('.mpg', '').replace('.iso', '')

		for word in cutlist:
			text = sub('(\_|\-|\.|\+)' + word + '(\_|\-|\.|\+)', '+', text, flags=I)
		text = text.replace('.', ' ').replace('-', ' ').replace('_', ' ').replace('+', '')
		return text

	def threadDownloadPage(self, link, getCoverCallback):
		try:
			response = get(link)
			response.raise_for_status()
			with open(COVERTMP, "wb") as f:
				f.write(response.content)
			getCoverCallback()
		except exceptions.RequestException as error:
			print("[TMDb] Download cover Error: %s" % str(error))

	def tmdbGetCover(self, coverUrl, getCoverCallback):
		callInThread(self.threadDownloadPage, coverUrl, getCoverCallback)

	def tmdbMovie(self, movieID, callback):
		try:
			movie = tmdb.Movies(int(movieID))
			callback(movie.info(language=self.lang))
		except Exception as error:
			print("[TMDb] Movies Error: %s" % str(error))

	def tmdbSearch(self, fileName, session, selectCallback):
		fileName = splitext(basename(fileName))[0]
		text = self.cleanFile(fileName)
		res = []
		try:
			search = tmdb.Search()
			json_data = search.multi(query=text, language=self.lang)
			for IDs in json_data['results']:
				try:
					media = str(IDs['media_type'])
				except:
					media = ""
				try:
					id = str(IDs['id'])
				except:
					id = ""

				title = ""
				try:
					title = str(IDs['title'])
				except:
					pass
				try:
					title = str(IDs['name'])
				except:
					pass

				date = ""
				try:
					date = str(IDs['release_date'])[:4]
				except:
					pass

				coverUrl = ""
				try:
					coverPath = str(IDs['poster_path'])
					coverUrl = "http://image.tmdb.org/t/p/%s/%s" % (self.coverSize, coverPath)
				except:
					pass

				if id and title and media:
					if media == "movie":
						mediasubst = _("Movie")
					else:
						mediasubst = _("Series")
					choice = "%s: %s (%s)" % (mediasubst, title, date)
					res.append((choice, coverUrl, id, IDs))

			if len(res) > 1:
				title = _("Please select")
				session.openWithCallback(selectCallback, ChoiceBox, title=title, list=res)
			elif len(res) == 0:
				session.open(MessageBox, "Nothing found", MessageBox.TYPE_INFO, windowTitle="")
			else:
				selectCallback(res[0])
				# show info
		except Exception as error:
			import traceback
			traceback.print_exc()
			session.open(MessageBox, "[TMDb] Error: %s" % str(error), MessageBox.TYPE_ERROR, windowTitle="")


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


class MC_VideoPlayer(Screen, HelpableScreen, TMDB):
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		TMDB.__init__(self)
		self["key_red"] = Button(_("Delete Movie"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button(_("Settings"))
		self["currentfolder"] = Label("")
		self["currentfavname"] = Label("")
		self.showiframe = Showiframe()
		self.mvion = False
		self.curfavfolder = -1
		system("touch /tmp/bmcmovie")
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
				"red": (self.SelDelete, "Delete Movie"),
				"blue": (self.KeySettings, "Settings"),
			}, -2)

		currDir = config.plugins.mc_vp.lastDir.value
		if not pathExists(currDir):
			currDir = "/"
		self["currentfolder"].setText(str(currDir))
		sort = config.plugins.mc_vp_sortmode.enabled.value
		inhibitDirs = ["/bin", "/boot", "/dev", "/dev.static", "/etc", "/lib", "/proc", "/ram", "/root", "/sbin", "/sys", "/tmp", "/usr", "/var"]
		self.filelist = FileList(currDir, useServiceRef=True, showDirectories=True, showFiles=True, matchingPattern="(?i)^.*\.(ts|vob|mpg|mpeg|avi|mkv|dat|iso|img|mp4|wmv|flv|divx|mov|ogm|m2ts)", additionalExtensions=None, sort=sort)
		self["filelist"] = self.filelist
		self["filelist"].show()
		self["Service"] = ServiceEvent()
		self.filelist.onSelectionChanged.append(self.__selectionChanged)
		self.detailtimer = eTimer()
		self.detailtimer.callback.append(self.updateEventInfo)

	def __selectionChanged(self):
		self.detailtimer.start(500, True)

	def updateEventInfo(self):
		if self.filelist.canDescent():
			return
		serviceref = self.filelist.getServiceRef()
		if serviceref:
			self["Service"].newService(serviceref)

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
		pass

	def SelDelete(self):
		self.filename = self.filelist.getFilename()
		path = self.filename
		self.session.openWithCallback(self.selremove, MessageBox, _('Do you really want to delete\n%s ?') % path, MessageBox.TYPE_YESNO)

	def selremove(self, ret):
		if ret is True:
			self.filename = self.filelist.getFilename()
			if self.filename.endswith('.ts'):
				path = self.filename.replace('.ts', '')
				for fdelete in glob(path + '.*'):
					remove(fdelete)

			elif self.filename.endswith('.vob'):
				path = self.filename.replace('.vob', '')
				print('path: %s' % path)
				for fdelete in glob(path + '.*'):
					print('fdelete: %s' % fdelete)
					remove(fdelete)

			else:
				path = self.filename
				remove(path)
			self.updd()

	def PrevFavFolder(self):
		return

	def showFileInfo(self):
		if self["filelist"].canDescent():
			return
		self.coverFilename = "%s.jpg" % splitext(self["filelist"].getFilename())[0]
		self.tmdbSearch(self["filelist"].getFilename(), self.session, self.showFileInfoCallback)

	def showFileInfoCallback(self, answer):
		if answer is not None:
			if exists(COVERTMP):
				remove(COVERTMP)
			self.tmdbGetCover(answer[1], self.tmdbGetCoverCallback)
			movieInfoFile = "%seit" % self.coverFilename[:-3]
			if EITFile and exists(movieInfoFile):
				print("'%s' already exists" % movieInfoFile)
				return
			if config.plugins.mc_vp.themoviedb_fullinfo.value:
				self.tmdbMovie(answer[2], self.tmdbSaveMovieInfo)
			else:
				self.tmdbSaveMovieInfo(answer[3])

	def tmdbSaveMovieInfo(self, movieInfo):
		try:
			movieInfoFile = "%seit" % self.coverFilename[:-3]
			genres = movieInfo.get("genres", [])
			if genres:
				genres = [genre["name"] for genre in genres]
			overview = "%s\n\n%s\n%s\n" % (movieInfo["overview"], ",".join(genres), movieInfo["release_date"])
			if EITFile:
				runtime = 60 * int(movieInfo.get("runtime", "0"))
				title = movieInfo.get("title", "")
				lang = "DEU" if self.lang == "de" else "ENG"  # TODO LANG
				eitFile = EITFile(INFOTMP, lang, 0, datetime.now(), runtime, title, "", overview)
				eitFile.save()
			else:
				with open(INFOTMP, "w", encoding="utf-8") as f:
					f.write(overview)
				movieInfoFile = "%stxt" % self.coverFilename[:-3]
			move(INFOTMP, movieInfoFile)
		except:
			import traceback
			traceback.print_exc()
			print("Error write movie info file")
		self.updateEventInfo()

	def tmdbGetCoverCallback(self):
		if exists(COVERTMP) and not exists(self.coverFilename):
			try:
				move(COVERTMP, self.coverFilename)
			except:
				print("Error move cover file")
				pass
			self.updateEventInfo()

	def KeyOk(self):
		self.filename = self.filelist.getFilename()
		try:
			if self.filename.endswith('.img') or self.filename.endswith('.iso') or self.filename.endswith('VIDEO_TS/') and config.plugins.mc_vp.dvd.value == "dvd":
				self.showiframe.finishStillPicture()
				from Screens import DVD
				if self.filename.endswith('VIDEO_TS/'):
					filepath = split(self.filename.rstrip('/'))[0]
				else:
					filepath = self.filename
				self.session.open(DVD.DVDPlayer, dvd_filelist=[filepath])
				return
		except Exception as e:
			print("DVD Player error: %s" % str(e))
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
		movienameserie = sub("e[0-9]{2}", "", newshort.lower())
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
		directory = self.filelist.getCurrentDirectory()
		config.plugins.mc_vp.lastDir.value = directory if directory else "/"
		config.plugins.mc_vp.save()
		try:
			remove("/tmp/bmcmovie")
		except:
			pass
		self.showiframe.finishStillPicture()
		self.close()


class VideoPlayerSettings(Screen, ConfigListScreen):
	if getDesktop(0).size().width() == 1920:
		skin = """
			<screen position="160,220" size="800,240" title="Media Center - VideoPlayer Settings" >
				<widget name="config" position="10,10" size="760,200" />
			</screen>"""
	else:
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
