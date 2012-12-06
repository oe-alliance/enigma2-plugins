# -*- coding: utf-8 -*-
##
## Podcast
## by AliAbdul
##
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSelection, ConfigSubsection, ConfigText, ConfigYesNo, getConfigListEntry
from Components.ConfigList import ConfigListScreen

from Components.FileList import FileList
from Components.Label import Label
from Components.Language import language

from Components.MenuList import MenuList
from Components.PluginComponent import plugins
from Components.ProgressBar import ProgressBar

from enigma import eServiceReference, eTimer
from os import system
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Directories import fileExists, resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS
from Tools.Downloader import downloadWithProgress
from twisted.web.client import getPage
from xml.etree.cElementTree import parse
import os, gettext, re

###################################################

PluginLanguageDomain = "Podcast"
PluginLanguagePath = "Extensions/Podcast/locale/"

def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print "[" + PluginLanguageDomain + "] fallback to default translation for " + txt
		return gettext.gettext(txt)

language.addCallback(localeInit())

###################################################

def remove(file):
	system('rm "' + file + '"')

###################################################

class ChangedMoviePlayer(MoviePlayer):
	def __init__(self, session, service):
		MoviePlayer.__init__(self, session, service)
		self.skinName = "MoviePlayer"

	def leavePlayer(self):
		self.session.openWithCallback(self.leavePlayerConfirmed, MessageBox, _("Stop playing this movie?"))

	def leavePlayerConfirmed(self, answer):
		if answer:
			self.close()

	def doEofInternal(self, playing):
		pass

	def getPluginList(self):
		list = []
		for p in plugins.getPlugins(where=PluginDescriptor.WHERE_EXTENSIONSMENU):
			if p.name != _("Podcast"):
				list.append(((boundFunction(self.getPluginName, p.name), boundFunction(self.runPlugin, p), lambda: True), None))
		return list

	def showMovies(self):
		pass

###################################################

config.plugins.Podcast = ConfigSubsection()
config.plugins.Podcast.buffer = ConfigYesNo(default=True)
config.plugins.Podcast.bufferDevice = ConfigText(default="/media/hdd/", fixed_size=False)
config.plugins.Podcast.keepStored = ConfigSelection(choices={"delete": _("delete"), "keep": _("keep on device"), "ask": _("ask me")}, default="delete")

###################################################

def encodeUrl(url):
	url = url.replace("&amp;", "&")
	url = url.replace("&lt;", "<")
	url = url.replace("&gt;", ">")
	url = url.replace("&#39;", "'")
	url = url.replace("&quot;", '"')
	url = url.replace("&#42;", "*")
	url = url.replace("&#124;", "|")
	url = url.replace("&#039;", "'")
	url = url.replace("&#187;", ">>")
	return url

###################################################

class BufferThread():
	def __init__(self):
		self.progress = 0
		self.downloading = False
		self.error = ""
		self.download = None

	def startDownloading(self, url, file):
		self.progress = 0
		self.downloading = True
		self.error = ""
		self.download = downloadWithProgress(url, file)
		self.download.addProgress(self.httpProgress)
		self.download.start().addCallback(self.httpFinished).addErrback(self.httpFailed)

	def httpProgress(self, recvbytes, totalbytes):
		self.progress = int(100 * recvbytes / float(totalbytes))

	def httpFinished(self, string=""):
		self.downloading = False
		if string is not None:
			self.error = str(string)
		else:
			self.error = ""

	def httpFailed(self, failure_instance=None, error_message=""):
		self.downloading = False
		if error_message == "" and failure_instance is not None:
			error_message = failure_instance.getErrorMessage()
			self.error = str(error_message)

	def stop(self):
		self.progress = 0
		self.downloading = False
		self.error = ""
		self.download.stop()

bufferThread = BufferThread()

###################################################

class PodcastBuffer(Screen):
	skin = """
		<screen position="center,center" size="520,80" title="%s" >

			<widget name="info" position="5,5" size="510,40" font="Regular;18" halign="center" valign="center" />
			<widget name="progress" position="100,50" size="320,14" pixmap="skin_default/progress_big.png" borderWidth="2" borderColor="#cccccc" />

		</screen>""" % _("Podcast")


	def __init__(self, session, url, file):
		self.session = session
		Screen.__init__(self, session)
		
		self.url = url
		self.file = file
		
		self.infoTimer = eTimer()
		self.infoTimer.timeout.get().append(self.updateInfo)
		
		self["info"] = Label(_("Downloading movie: %s") % self.file)
		self["progress"] = ProgressBar()
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.okClicked, "cancel": self.exit}, -1)
		
		self.onLayoutFinish.append(self.downloadMovie)

	def downloadMovie(self):
		bufferThread.startDownloading(self.url, self.file)
		self.infoTimer.start(300, False)

	def updateInfo(self):
		if bufferThread.error != "":
			self["info"].setText(bufferThread.error)
			self.infoTimer.stop()
		else:
			progress = int(bufferThread.progress)
			self["progress"].setValue(progress)
			if progress == 100:
				self.infoTimer.stop()
				self.close(True)

	def okClicked(self):
		if int(bufferThread.progress) > 0:
			self.infoTimer.stop()
			self.close(True)

	def exit(self):
		bufferThread.download.stop()
		self.close(None)

###################################################

class PodcastMovies(Screen):
	skin = """
		<screen position="center,center" size="420,360" title="%s" >

			<widget name="list" position="5,5" size="410,250" scrollbarMode="showOnDemand" />

			<eLabel position="5,260" size="420,2" backgroundColor="#ffffff" />

			<widget name="info" position="5,265" size="420,90" font="Regular;18" />

		</screen>""" % _("Podcast")


	def __init__(self, session, url):
		self.session = session
		Screen.__init__(self, session)
		
		self.url = url
		self.list = []
		self.movies = []
		self.working = True
		
		self["list"] = MenuList([])
		self["list"].onSelectionChanged.append(self.showInfo)
		self["info"] = Label()
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.ok, "cancel": self.exit}, -1)
		
		self.onLayoutFinish.append(self.downloadMovies)

	def ok(self):
		if self.working == False:
			if len(self.list) > 0:

				idx = self["list"].getSelectionIndex()

				(url, length, type) = self.splitExtraInfo(self.movies[idx][1])
				if config.plugins.Podcast.buffer.value:
					file = url
					while file.__contains__("/"):
						idx = file.index("/")
						file = file[idx+1:]
					self.file = "%s%s" % (config.plugins.Podcast.bufferDevice.value, file)
					self.session.openWithCallback(self.bufferCallback, PodcastBuffer, url, self.file)
				else:
					ref = eServiceReference(4097, 0, url)
					self.session.open(ChangedMoviePlayer, ref)

	def bufferCallback(self, callback):
		if callback is not None:
			ref = eServiceReference(4097, 0, self.file)
			self.session.openWithCallback(self.delete, ChangedMoviePlayer, ref)

	def delete(self, callback=None):
		if bufferThread.downloading: #still downloading?
			bufferThread.stop()
		if config.plugins.Podcast.keepStored.value == "delete":
			remove(self.file)
		elif config.plugins.Podcast.keepStored.value == "ask":
			self.session.openWithCallback(self.deleteCallback, MessageBox, _("Delete this movie?"))

	def deleteCallback(self, callback):
		if callback:
			remove(self.file)

	def exit(self):
		if self.working == False:
			self.close()

	def downloadMovies(self):
		getPage(self.url).addCallback(self.showMovies).addErrback(self.error)

	def showMovies(self, page):
		if '<item>' in page:
			reonecat = re.compile(r'<item>(.+?)</item>', re.DOTALL)
			items = reonecat.findall(page)
		else:
			items = [page]
		for item in items:
			if '<description></description>' in item:
				reonecat2 = re.compile(r'<title>(.+?)</title>.+?<enclosure(.+?)/>.+?', re.DOTALL)

				for title, extra in reonecat2.findall(item):
					if title.startswith("<![CDATA["):
						title = title[9:]
					if title.endswith("]]>"):
						title = title[:-3]

					self.list.append(encodeUrl(title))

					self.movies.append(["", extra])
			else:
				reonecat2 = re.compile(r'<title>(.+?)</title>.+?<description>(.+?)</description>.+?<enclosure(.+?)/>.+?', re.DOTALL)
				for title, description, extra in reonecat2.findall(item):
					if title.startswith("<![CDATA["):
						title = title[9:]
					if title.endswith("]]>"):
						title = title[:-3]
					if description.__contains__("<![CDATA["):
						idx = description.index("<![CDATA[")
						description = description[idx+10:]
					if description.endswith("]]>"):
						description = description[:-3]

					self.list.append(encodeUrl(title))

					self.movies.append([description, extra])

		self["list"].setList(self.list)

		self.showInfo()
		self.working = False

	def error(self, error=""):
		print "[Podcast] Error:", error
		self.instance.setTitle(_("Error getting movies"))
		self.working = False



	def showInfo(self):

		if len(self.list) > 0:

			idx = self["list"].getSelectionIndex()

			description = self.movies[idx][0]

			(url, length, type) = self.splitExtraInfo(self.movies[idx][1])

			self["info"].setText("%s: %s   %s: %s\n%s" % (_("Length"), length, _("Type"), type, encodeUrl(description)))



	def splitExtraInfo(self, info):

		if info.__contains__('url="'):

			idx = info.index('url="')

			url = info[idx+5:]

			idx = url.index('"')

			url = url[:idx]

		else:

			url = "N/A"

		

		length = "N/A"

		if info.__contains__('length="'):

			idx = info.index('length="')

			length = info[idx+8:]

			idx = length.index('"')

			length = length[:idx]
			if length:

				length = str((int(length) / 1024) / 1024) + " MB"

		

		if info.__contains__('type="'):

			idx = info.index('type="')

			type = info[idx+6:]

			idx = type.index('"')

			type = type[:idx]

		else:

			type = "N/A"

		

		return (url, length, type)

###################################################

class PodcastPodcasts(Screen):
	skin = """
		<screen position="center,center" size="420,360" title="%s" >

			<widget name="list" position="0,0" size="420,350" scrollbarMode="showOnDemand" />

		</screen>""" % _("Podcast")


	def __init__(self, session, provider):
		self.session = session
		Screen.__init__(self, session)
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.ok, "cancel": self.close}, -1)
		
		self.urls = []
		list = []
		for podcast in provider.findall("podcast"):
			name = podcast.get("name") or None
			name = name.encode("UTF-8") or name
			url = podcast.get("url") or None
			if name and url:
				list.append(name)
				self.urls.append(url)
		self["list"] = MenuList(list)

	def ok(self):
		if len(self.urls) > 0:
			cur = self.urls[self["list"].getSelectedIndex()]
			self.session.open(PodcastMovies, cur)

###################################################

class PodcastProvider(Screen):
	skin = """
		<screen position="center,center" size="420,360" title="%s" >
			<widget name="list" position="0,0" size="420,350" scrollbarMode="showOnDemand" />

		</screen>""" % _("Podcast")


	def __init__(self, session, language):
		self.session = session
		Screen.__init__(self, session)
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.ok, "cancel": self.close}, -1)
		
		self.providers = []
		list = []
		for provider in language.findall("provider"):
			name = provider.get("name") or None
			name = name.encode("UTF-8") or name
			if name:
				list.append(name)
				self.providers.append(provider)
		self["list"] = MenuList(list)

	def ok(self):
		if len(self.providers) > 0:
			cur = self.providers[self["list"].getSelectedIndex()]
			self.session.open(PodcastPodcasts, cur)

###################################################

class PodcastXML(Screen):
	skin = """
		<screen position="center,center" size="420,360" title="%s" >

			<widget name="list" position="0,0" size="420,350" scrollbarMode="showOnDemand" />

		</screen>""" % _("Podcast")


	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.ok, "cancel": self.close}, -1)
		
		self.languages = []
		list = []
		file = "/etc/podcast/podcasts.xml"
		if fileExists(file):
			xml = parse(file).getroot()
			for language in xml.findall("language"):
				name = language.get("name") or None
				name = name.encode("UTF-8") or name
				if name:
					list.append(name)
					self.languages.append(language)
		self["list"] = MenuList(list)

	def ok(self):
		if len(self.languages) > 0:
			cur = self.languages[self["list"].getSelectedIndex()]
			self.session.open(PodcastProvider, cur)

###################################################

class PodcastComGenre2(Screen):
	skin = """
		<screen position="center,center" size="420,360" title="%s" >

			<widget name="list" position="0,0" size="420,350" scrollbarMode="showOnDemand" />

		</screen>""" % _("Podcast")


	def __init__(self, session, url):
		self.session = session
		Screen.__init__(self, session)
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.ok, "cancel": self.exit}, -1)
		
		self.url = url
		self.urls = []
		self.working = True
		self["list"] = MenuList([])
		
		self.onLayoutFinish.append(self.downloadGenres)

	def ok(self):
		if self.working == False:
			if len(self.urls) > 0:
				self.working = True
				cur = self.urls[self["list"].getSelectedIndex()]
				getPage(cur).addCallback(self.getRssUrl).addErrback(self.error2)

	def getRssUrl(self, page):
		idx = page.index('">rss feed</a><br>')
		page = page[:idx]
		while page.__contains__("http://"):
			idx = page.index("http://")
			page = page[idx+1:]
		self.working = False
		self.session.open(PodcastMovies, "h%s"%page)

	def exit(self):
		if self.working == False:
			self.close()

	def downloadGenres(self):
		getPage(self.url).addCallback(self.getGenres).addErrback(self.error)

	def getGenres(self, page):
		list = []
		reonecat = re.compile(r'height="19"><a href="(.+?)">(.+?)</a>', re.DOTALL)

		for url, title in reonecat.findall(page):

			list.append(encodeUrl(title))

			self.urls.append(url)

		self["list"].setList(list)
		self.working = False

	def error(self, error=""):
		print "[Podcast] Error:", error
		self.instance.setTitle(_("Error getting genres"))
		self.working = False

	def error2(self, error=""):
		print "[Podcast] Error:", error
		self.instance.setTitle(_("Error getting rss feed"))
		self.working = False

###################################################

class PodcastComGenre(Screen):
	skin = """
		<screen position="center,center" size="420,360" title="%s" >
			<widget name="list" position="0,0" size="420,350" scrollbarMode="showOnDemand" />

		</screen>""" % _("Podcast")


	def __init__(self, session, url):
		self.session = session
		Screen.__init__(self, session)
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.ok, "cancel": self.exit}, -1)
		
		self.url = url
		self.urls = []
		self.working = True
		self["list"] = MenuList([])
		
		self.onLayoutFinish.append(self.downloadSite)

	def ok(self):
		if self.working == False:
			if len(self.urls) > 0:
				cur = self.urls[self["list"].getSelectedIndex()]
				self.session.open(PodcastComGenre2, cur)

	def exit(self):
		if self.working == False:
			self.close()

	def downloadSite(self):
		getPage(self.url).addCallback(self.getUrl).addErrback(self.error)

	def getUrl(self, page):
		reonecat = re.compile(r'Get this podcast channel on your mobile phone:</strong><br><a href="(.+?)"', re.DOTALL)
		list = reonecat.findall(page)
		if len(list) > 0:
			getPage(list[0]).addCallback(self.getGenres).addErrback(self.error)
		else:
			self.error("Error getting movies-url")

	def getGenres(self, page):
		list = []
		reonecat = re.compile(r'height="17"><a title="(.+?)" href="(.+?)">(.+?)</a>', re.DOTALL)

		for title2, url, title in reonecat.findall(page):

			list.append(encodeUrl(title))

			self.urls.append(url)

		self["list"].setList(list)
		self.working = False

	def error(self, error=""):
		print "[Podcast] Error:", error
		self.instance.setTitle(_("Error getting genres"))
		self.working = False

###################################################

class PodcastCom(Screen):
	skin = """
		<screen position="center,center" size="420,360" title="%s" >
			<widget name="list" position="0,0" size="420,350" scrollbarMode="showOnDemand" />

		</screen>""" % _("Podcast")


	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		
		self.working = True
		self.urls = []
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.ok, "cancel": self.exit}, -1)
		
		self["list"] = MenuList([])
		
		self.onLayoutFinish.append(self.downloadMovies)

	def ok(self):
		if self.working == False:
			if len(self.urls) > 0:
				cur = self.urls[self["list"].getSelectedIndex()]
				self.session.open(PodcastComGenre, cur)

	def exit(self):
		if self.working == False:
			self.close()

	def downloadMovies(self):
		getPage("http://podcast.com/home.php?subpage=_pages/channels_home.php").addCallback(self.showGenres).addErrback(self.error)

	def showGenres(self, page):
		list = []
		reonecat = re.compile(r'<li><a href="(.+?)" title="(.+?)">(.+?)</a></li>', re.DOTALL)

		for url, title2, title in reonecat.findall(page):
			if not title.startswith("<"):

				list.append(encodeUrl(title))

				self.urls.append(url)

		self["list"].setList(list)
		self.working = False

	def error(self, error=""):
		print "[Podcast] Error:", error
		self.instance.setTitle(_("Error getting genres"))
		self.working = False

###################################################

class LocationSelection(Screen):
	skin = """
	<screen position="center,center" size="560,300" title="%s">
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
		<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="filelist" position="10,45" size="550,255" scrollbarMode="showOnDemand" />
	</screen>""" % _("Podcast")



	def __init__(self, session, dir="/"):

		Screen.__init__(self, session)

		

		self["key_green"] = Label(_("Select"))

		

		try: self["filelist"] = FileList(dir, showDirectories=True, showFiles=False)

		except: self["filelist"] = FileList("/", showDirectories, showFiles)

		

		self["actions"] = ActionMap(["ColorActions", "OkCancelActions"],

			{

				"ok": self.okClicked,

				"cancel": self.exit,

				"green": self.select

			}, -1)
		
		self.onLayoutFinish.append(self.updateDirectoryName)

		

	def okClicked(self):

		if self["filelist"].canDescent():

			self["filelist"].descent()

			self["filelist"].instance.moveSelectionTo(0)

			self.updateDirectoryName()



	def exit(self):

		self.close(None)



	def select(self):

		dir = self["filelist"].getCurrentDirectory()

		if dir is not None:

			self.close(dir)

		else:

			self.close(None)



	def updateDirectoryName(self):
		try:
			dir = self["filelist"].getCurrentDirectory()
			self.instance.setTitle(dir)
		except:
			self.instance.setTitle("?")

###################################################

class PodcastConfig(ConfigListScreen, Screen):
	skin = """
	<screen position="center,center" size="560,180" title="%s">
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
		<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="config" position="10,45" size="550,125" scrollbarMode="showOnDemand" />
	</screen>""" % _("Podcast")

	def __init__(self, session):
		Screen.__init__(self, session)
		
		self["key_green"] = Label(_("Save"))
		
		ConfigListScreen.__init__(self, [])
			
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {"green": self.save, "cancel": self.exit}, -1)
		
		self.onLayoutFinish.append(self.createConfig)

	def createConfig(self):
		self.deviceEntry = ConfigSelection(choices=[config.plugins.Podcast.bufferDevice.value], default=config.plugins.Podcast.bufferDevice.value)
		self["config"].list = [
			getConfigListEntry(_("Buffer:"), config.plugins.Podcast.buffer),
			getConfigListEntry(_("Buffer device:"), self.deviceEntry),
			getConfigListEntry(_("Buffer file handling:"), config.plugins.Podcast.keepStored)]

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.handleKeysLeftAndRight()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.handleKeysLeftAndRight()

	def handleKeysLeftAndRight(self):
		sel = self["config"].getCurrent()[1]
		if sel == self.deviceEntry:
			self.session.openWithCallback(self.locationSelected, LocationSelection, config.plugins.Podcast.bufferDevice.value)

	def locationSelected(self, dir):
		if dir is not None and dir != "?":
			config.plugins.Podcast.bufferDevice.value = dir
			config.plugins.Podcast.bufferDevice.save()
			self.createConfig()

	def save(self):
		for x in self["config"].list:
			x[1].save()
		self.close()

	def exit(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

###################################################

class PodcastDeEpisodes(Screen):
	skin = """
		<screen position="center,center" size="420,360" title="%s" >
			<widget name="list" position="0,0" size="420,350" scrollbarMode="showOnDemand" />

		</screen>""" % _("Podcast")

	def __init__(self, session, url):
		self.session = session
		Screen.__init__(self, session)
		
		self.working = True
		self.url = url
		self.urls = []
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.ok, "cancel": self.exit}, -1)
		
		self["list"] = MenuList([])
		
		self.onLayoutFinish.append(self.downloadMovies)

	def ok(self):
		if self.working == False:
			self.instance.setTitle(_("Podcast"))
			if len(self.urls) > 0:
				cur = self.urls[self["list"].getSelectedIndex()]
				self.working = True
				getPage(cur).addCallback(self.playPodcast).addErrback(self.error2)

	def playPodcast(self, url):
		if url.__contains__('" id="control_download"'):
			self.working = False
			idx = url.index('" id="control_download"')
			url = url[:idx]
			while url.__contains__("http://"):
				idx = url.index("http://")
				url = url[idx+1:]
			url = "h%s"%url
			
			if config.plugins.Podcast.buffer.value:
				file = url
				while file.__contains__("/"):
					idx = file.index("/")
					file = file[idx+1:]
				self.file = "%s%s" % (config.plugins.Podcast.bufferDevice.value, file)
				self.session.openWithCallback(self.bufferCallback, PodcastBuffer, url, self.file)
			else:
				ref = eServiceReference(4097, 0, url)
				self.session.open(ChangedMoviePlayer, ref)
		else:
			self.error2()

	def bufferCallback(self, callback):
		if callback is not None:
			ref = eServiceReference(4097, 0, self.file)
			self.session.openWithCallback(self.delete, ChangedMoviePlayer, ref)

	def delete(self, callback=None):
		if bufferThread.downloading: #still downloading?
			bufferThread.stop()
		if config.plugins.Podcast.keepStored.value == "delete":
			remove(self.file)
		elif config.plugins.Podcast.keepStored.value == "ask":
			self.session.openWithCallback(self.deleteCallback, MessageBox, _("Delete this movie?"))

	def deleteCallback(self, callback):
		if callback:
			remove(self.file)

	def exit(self):
		if self.working == False:
			self.close()

	def downloadMovies(self):
		getPage(self.url).addCallback(self.showEpisodes).addErrback(self.error)

	def showEpisodes(self, page):
		list = []
		idx = page.index('<h3>')
		page = page[idx:]
		idx = page.index('</div></div>')
		page = page[:idx]
		reonecat = re.compile(r'<a href="(.+?)" title="(.+?)">', re.DOTALL)

		for url, title in reonecat.findall(page):
			if title.startswith("Episode: "):
				title = title[9:]

			list.append(encodeUrl(title))

			self.urls.append(url)

		self["list"].setList(list)
		self.working = False

	def error(self, error=""):
		print "[Podcast] Error:", error
		self.instance.setTitle(_("Error getting episodes"))
		self.working = False

	def error2(self, error=""):
		print "[Podcast] Error: Error getting podcast url"
		self.instance.setTitle(_("Error getting podcast url"))
		self.working = False

###################################################

class PodcastDePodcasts(Screen):
	skin = """
		<screen position="center,center" size="420,360" title="%s" >
			<widget name="list" position="0,0" size="420,350" scrollbarMode="showOnDemand" />

		</screen>""" % _("Podcast")

	def __init__(self, session, url):
		self.session = session
		Screen.__init__(self, session)
		
		self.working = True
		self.url = url
		self.urls = []
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.ok, "cancel": self.exit}, -1)
		
		self["list"] = MenuList([])
		
		self.onLayoutFinish.append(self.downloadMovies)

	def ok(self):
		if self.working == False:
			if len(self.urls) > 0:
				cur = self.urls[self["list"].getSelectedIndex()]
				self.session.open(PodcastDeEpisodes, cur)

	def exit(self):
		if self.working == False:
			self.close()

	def downloadMovies(self):
		getPage(self.url).addCallback(self.showPodcasts).addErrback(self.error)

	def showPodcasts(self, page):
		list = []
		idx = page.index('<h4>Podcasts</h4>')
		page = page[idx:]
		idx = page.index('</div>')
		page = page[:idx]
		reonecat = re.compile(r'alt="(.+?)" class="(.+?)<a href="(.+?)" title="(.+?)">(.+?)<span class="(.+?)"></span>', re.DOTALL)

		for title, x, url, x2, x3, type in reonecat.findall(page):
			if type.__contains__("content_type_1_icon"):
				text = _(" (Audio)")
			else:
				text = _(" (Video)")

			list.append(encodeUrl(title+text))

			self.urls.append(url)

		self["list"].setList(list)
		self.working = False

	def error(self, error=""):
		print "[Podcast] Error:", error
		self.instance.setTitle(_("Error getting podcasts"))
		self.working = False

###################################################

class PodcastDeCategories(Screen):
	skin = """
		<screen position="center,center" size="420,360" title="%s" >
			<widget name="list" position="0,0" size="420,350" scrollbarMode="showOnDemand" />

		</screen>""" % _("Podcast")

	def __init__(self, session, url):
		self.session = session
		Screen.__init__(self, session)
		
		self.working = True
		self.url = url
		self.urls = []
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.ok, "cancel": self.exit}, -1)
		
		self["list"] = MenuList([])
		
		self.onLayoutFinish.append(self.downloadMovies)

	def ok(self):
		if self.working == False:
			if len(self.urls) > 0:
				cur = self.urls[self["list"].getSelectedIndex()]
				self.session.open(PodcastDePodcasts, cur)

	def exit(self):
		if self.working == False:
			self.close()

	def downloadMovies(self):
		getPage(self.url).addCallback(self.showCategories).addErrback(self.error)

	def showCategories(self, page):
		list = []
		idx = page.index('<h3>')
		page = page[idx:]
		idx = page.index('</div>')
		page = page[:idx]
		reonecat = re.compile(r'<a href="(.+?)" title="(.+?)">', re.DOTALL)

		for url, title in reonecat.findall(page):

			list.append(encodeUrl(title))

			self.urls.append(url)

		self["list"].setList(list)
		self.working = False

	def error(self, error=""):
		print "[Podcast] Error:", error
		self.instance.setTitle(_("Error getting categories"))
		self.working = False

###################################################

class PodcastDe(Screen):
	skin = """
		<screen position="center,center" size="420,360" title="%s" >
			<widget name="list" position="0,0" size="420,350" scrollbarMode="showOnDemand" />

		</screen>""" % _("Podcast")

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		
		self.working = True
		self.urls = []
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.ok, "cancel": self.exit}, -1)
		
		self["list"] = MenuList([])
		
		self.onLayoutFinish.append(self.downloadMovies)

	def ok(self):
		if self.working == False:
			if len(self.urls) > 0:
				cur = self.urls[self["list"].getSelectedIndex()]
				self.session.open(PodcastDeCategories, cur)

	def exit(self):
		if self.working == False:
			self.close()

	def downloadMovies(self):
		getPage("http://m.podcast.de/kategorien").addCallback(self.showCategories).addErrback(self.error)

	def showCategories(self, page):
		list = []
		idx = page.index('<h3>')
		page = page[idx:]
		idx = page.index('</div>')
		page = page[:idx]
		reonecat = re.compile(r'<a href="(.+?)" title="(.+?)">', re.DOTALL)

		for url, title in reonecat.findall(page):

			list.append(encodeUrl(title))

			self.urls.append(url)

		self["list"].setList(list)
		self.working = False

	def error(self, error=""):
		print "[Podcast] Error:", error
		self.instance.setTitle(_("Error getting categories"))
		self.working = False

###################################################

class Podcast(Screen):
	skin = """
		<screen position="center,center" size="420,360" title="%s" >
			<widget name="list" position="0,0" size="420,350" scrollbarMode="showOnDemand" />

		</screen>""" % _("Podcast")


	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.ok, "cancel": self.close}, -1)
		
		self["list"] = MenuList([
			_("podcast.de"),
			_("podcast.com"),
			_("from xml"),
			_("configuration")])

	def ok(self):
		cur = self["list"].getCurrent()
		if cur == _("podcast.de"):
			self.session.open(PodcastDe)
		elif cur == _("podcast.com"):
			self.session.open(PodcastCom)
		elif cur == _("from xml"):
			self.session.open(PodcastXML)
		else:
			self.session.open(PodcastConfig)

###################################################

def main(session, **kwargs):
	session.open(Podcast)

def Plugins(**kwargs):
	return PluginDescriptor(name=_("Podcast"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)
