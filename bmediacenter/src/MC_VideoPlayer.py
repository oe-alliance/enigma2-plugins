from datetime import datetime
from re import match, sub, I
from os import system, remove
from os.path import basename, split, splitext, exists
from requests import get, exceptions
from glob import glob
from shutil import move
import tmdbsimple as tmdb
from enigma import getDesktop, eTimer, eServiceCenter
from Components.Label import Label
from Components.config import config, configfile, ConfigSubsection, ConfigSelection, ConfigText, getConfigListEntry, ConfigYesNo
from Components.ConfigList import ConfigListScreen
from Components.FileList import FileList
from Components.ActionMap import NumberActionMap, HelpableActionMap
from Components.Language import language
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.StaticText import StaticText
from Components.ScrollLabel import ScrollLabel
from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.InfoBar import MoviePlayer as OrgMoviePlayer
from Tools.Directories import resolveFilename, pathExists, fileExists, SCOPE_MEDIA
from Screens.MessageBox import MessageBox
from twisted.internet.reactor import callInThread
from .GlobalFunctions import shortname, Showiframe
try:
	from Tools.EITFile import EITFile
except ImportError:
	EITFile = None

config.plugins.mc_vp = ConfigSubsection()
config.plugins.mc_vp.dvd = ConfigSelection(default="dvd", choices=[("dvd", "dvd"), ("movie", "movie")])
config.plugins.mc_vp.lastDir = ConfigText(default=resolveFilename(SCOPE_MEDIA))
config.plugins.mc_vp.themoviedb_coversize = ConfigSelection(default="w185", choices=["w92", "w185", "w500", "original"])
config.plugins.mc_vp.themoviedb_fullinfo = ConfigYesNo(default=True)

choiceList = [
	("0.0", _("Name ascending")),
	("0.1", _("Name descending")),
	("1.0", _("Date ascending")),
	("1.1", _("Date descending")),
	("2.0", _("Size ascending")),
	("2.1", _("Size descending"))
]
config.plugins.mc_vp_sortmode = ConfigSelection(default="0.0", choices=choiceList)

COVERTMP = "/tmp/bmc.jpg"
INFOTMP = "/tmp/bmc.txt"


class TMDB():
	def __init__(self):
		self.coverSize = config.plugins.mc_vp.themoviedb_coversize.value
		self.lang = language.getLanguage().split("_", 1)[0]
		if len(self.lang) < 2:
			self.lang = "en"
		self.coverFilename = None
		tmdb.API_KEY = bytes.fromhex("64343265366238323061313534316363363963653738393637316665626133399"[:-1]).decode('utf-8')

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

	def tmdbSearch(self, fileName, serviceref, session, selectCallback):
		text = None
		if serviceref:
			info = eServiceCenter.getInstance().info(serviceref)
			event = info and info.getEvent(serviceref)
			if event:
				text = event.getEventName()
		if not text:
			fileName = splitext(basename(fileName))[0]
			text = self.cleanFile(fileName)
		# splitname year
		m = match(r'^(.*) \((19\d\d|20\d\d)\)$', text)
		year = None
		if m:
			text, year = m.groups()
		res = []
		try:
			search = tmdb.Search()
			if year:
				json_data = search.multi(query=text, language=self.lang, year=year)
			else:
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
					res.append((choice, coverUrl, id, IDs, fileName.endswith('.ts')))

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
		self["key_red"] = StaticText(_("Delete Movie"))
		self["key_green"] = StaticText("")
		self["key_yellow"] = StaticText("Info")
		self["moviedetailsbg"] = StaticText("")
		self["currentfolder"] = Label("")
		self["currentfavname"] = Label("")
		self["moviedetails"] = ScrollLabel()
		self["moviedetails"].hide()
		self.showiframe = Showiframe()
		self.mvion = False
		self.curfavfolder = -1
		self.isTS = False
		system("touch /tmp/bmcmovie")
		self["actions"] = HelpableActionMap(self, "MC_VideoPlayerActions",
		{
			"ok": (self.KeyOk, "Play selected file"),
			"cancel": (self.Exit, "Exit Video Player"),
			"left": (self.leftUp, "List Top"),
			"right": (self.rightDown, "List Bottom"),
			"up": (self.up, "List up"),
			"down": (self.down, "List down"),
			"nextBouquet": (self.NextFavFolder, "Next Favorite Folder"),
			"prevBouquet": (self.PrevFavFolder, "Previous Favorite Folder"),
			"menu": (self.keySettings, _("Settings"))
		}, -2)

		self["moviefileactions"] = HelpableActionMap(self, "MC_VideoPlayerActions",
		{
			"yellow": (self.keyMovieInfo, _("Show Movie Info")),
			"red": (self.keyDeleteMovie, _("Delete Movie"))
		}, -2)
		self["moviefileactions"].setEnabled(True)

		self["movieinfoactions"] = HelpableActionMap(self, "MC_VideoPlayerActions",
		{
			"green": (self.keySave, _("Save Movie Info")),
			"red": (self.keyCloseMovieInfo, _("Close"))
		}, -2)
		self["movieinfoactions"].setEnabled(False)

		currDir = config.plugins.mc_vp.lastDir.value
		if not pathExists(currDir):
			currDir = "/"
		self["currentfolder"].setText(str(currDir))
		inhibitDirs = ["/bin", "/boot", "/dev", "/dev.static", "/etc", "/lib", "/proc", "/ram", "/root", "/sbin", "/sys", "/tmp", "/usr", "/var"]
		self.filelist = FileList(currDir, useServiceRef=True, showDirectories=True, showFiles=True, matchingPattern="(?i)^.*\.(ts|vob|mpg|mpeg|avi|mkv|dat|iso|img|mp4|wmv|flv|divx|mov|ogm|m2ts)", additionalExtensions=None, sortDirs="0.0", sortFiles=config.plugins.mc_vp_sortmode.value, inhibitDirs=inhibitDirs)
		self["filelist"] = self.filelist
		self["filelist"].show()
		self["Service"] = ServiceEvent()
		self.filelist.onSelectionChanged.append(self.__selectionChanged)
		self.detailtimer = eTimer()
		self.detailtimer.callback.append(self.updateEventInfo)

	def __selectionChanged(self):
		if self.filelist.canDescent():
			self["moviefileactions"].setEnabled(False)
			self["key_yellow"].setText("")
			self["key_red"].setText("")
			return
		self["key_yellow"].setText("Info")
		self["key_red"].setText(_("Delete Movie"))
		self["moviefileactions"].setEnabled(True)
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

	def keyCloseMovieInfo(self):
		if self.movieInfo:
			self["movieinfoactions"].setEnabled(False)
			self["moviefileactions"].setEnabled(True)
			self["moviedetails"].setText("")
			self["moviedetails"].hide()
			self["filelist"].show()
			self["filelist"].selectionEnabled(True)
			self["key_red"].setText(_("Delete Movie"))
			self["key_green"].setText("")
			self["key_yellow"].setText(_("Show Movie Info"))
			self["moviedetailsbg"].setText("")
			self.movieInfo = None

	def keyDeleteMovie(self):
		def keyDeleteMovieCallback(ret):
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
				self.refreshList()

		self.filename = self.filelist.getFilename()
		self.session.openWithCallback(keyDeleteMovieCallback, MessageBox, _('Do you really want to delete\n%s ?') % self.filename, MessageBox.TYPE_YESNO)

	def PrevFavFolder(self):
		return

	def keyMovieInfo(self):
		if self["filelist"].canDescent():
			return
		self.movieInfo = None
		self.coverFilename = "%s.jpg" % splitext(self["filelist"].getFilename())[0]
		self.tmdbSearch(self["filelist"].getFilename(), self["filelist"].getServiceRef(), self.session, self.showMovieInfoCallback)

	def showMovieInfoCallback(self, answer):
		if answer is not None:
			if exists(COVERTMP):
				remove(COVERTMP)
			self.isTS = answer[4]
			self.tmdbGetCover(answer[1], self.tmdbGetCoverCallback)
			if config.plugins.mc_vp.themoviedb_fullinfo.value:
				self.tmdbMovie(answer[2], self.showMovieInfoPanel)
			else:
				self.showMovieInfoPanel(answer[3])

	def keySave(self):
		if self.movieInfo:
			try:
				movieInfoFile = "%seit" % self.coverFilename[:-3]
				genres = self.movieInfo.get("genres", [])
				if genres:
					genres = [genre["name"] for genre in genres]
				overview = "%s\n\n%s\n%s\n" % (self.movieInfo["overview"], ",".join(genres), self.movieInfo["release_date"])
				if EITFile and not self.isTS:
					runtime = 60 * int(self.movieInfo.get("runtime", "0"))
					title = self.movieInfo.get("title", "")
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
			self.keyCloseMovieInfo()

	def showMovieInfoPanel(self, movieInfo):
		self.movieInfo = movieInfo
		details = "%s|%s\n" % (_("Overview"), self.movieInfo["overview"])
		details += "\n"
		genres = self.movieInfo.get("genres", [])
		if genres:
			genres = [genre["name"] for genre in genres]
		details += "%s|%s\n" % (_("Genres"), ",".join(genres))
		self["moviedetails"].setText(details)
		self["moviedetails"].show()
		self["movieinfoactions"].setEnabled(True)
		self["moviefileactions"].setEnabled(False)
		self["filelist"].hide()
		self["key_red"].setText(_("Close"))
		self["moviedetailsbg"].setText("_")
		if self.isTS:
			self["key_green"].setText(_("Save as TXT"))
			movieInfoTXTFile = "%stxt" % self.coverFilename[:-3]
			if exists(movieInfoTXTFile):
				self["key_green"].setText(_("Overwrite TXT"))
		else:
			self["key_green"].setText(_("Save as EIT"))
			movieInfoFile = "%seit" % self.coverFilename[:-3]
			if exists(movieInfoFile):
				self["key_green"].setText("Overwrite EIT")
		self["key_yellow"].setText("")
		self["filelist"].selectionEnabled(False)

	def tmdbGetCoverCallback(self):
		if exists(COVERTMP):  # and not exists(self.coverFilename):
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

#	def KeyMenu(self):
#		if self["filelist"].canDescent():
#			if self.filelist.getCurrent()[0][1]:
#				self.currentDirectory = self.filelist.getCurrent()[0][0]
#				if self.currentDirectory is not None:
#					foldername = self.currentDirectory.split('/')
#					foldername = foldername[-2]
#					self.session.open(MC_FolderOptions,self.currentDirectory, foldername)
#		return

	def refreshList(self):
		self.filelist.setSortBy("0.0,%s" % config.plugins.mc_vp_sortmode.value)
		self.filelist.refresh()

	def keySettings(self):
		self.session.openWithCallback(self.refreshList, VideoPlayerSettings)

	def Exit(self):
		directory = self.filelist.getCurrentDirectory()
		config.plugins.mc_vp.lastDir.value = directory if directory else "/"
		config.plugins.mc_vp.save()
		configfile.save()
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
		self["actions"] = NumberActionMap(["ColorActions", "OkCancelActions"],
		{
			"ok": self.keyOK,
			"green": self.keyOK,
			"cancel": self.keyCancel,
			"red": self.keyCancel
		}, -1)
		self.list = []
		self.list.append(getConfigListEntry(_("Play DVD as:"), config.plugins.mc_vp.dvd))
		self.list.append(getConfigListEntry(_("Filelist Sorting:"), config.plugins.mc_vp_sortmode))
		ConfigListScreen.__init__(self, self.list, session)

	def keyCancel(self):
		for item in self["config"].list:
			if len(item) > 1:
				item[1].cancel()
		self.close()

	def keyOK(self):
		for item in self["config"].list:
			if len(item) > 1:
				item[1].save()
		configfile.save()
		self.close()
