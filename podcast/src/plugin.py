# -*- coding: utf-8 -*-
##
## Podcast
## by AliAbdul
##
from __future__ import print_function
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSelection, ConfigSubsection, ConfigText, ConfigYesNo, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.FileList import FileList
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.PluginComponent import plugins
from Components.ProgressBar import ProgressBar
from enigma import eServiceReference, eTimer, eEnv
from os import environ, system
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.TextBox import TextBox
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Directories import fileExists, resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS
from Tools.Downloader import downloadWithProgress
from twisted.web.client import getPage
from xml.etree.cElementTree import parse
from xml.dom.minidom import parseString as xmlparseString, parse as xmlparse
import gettext
import re
from six.moves.urllib.request import urlopen
import six
###################################################

configDir = eEnv.resolve("${sysconfdir}") + "/podcast/"

PluginLanguageDomain = "Podcast"
PluginLanguagePath = "Extensions/Podcast/locale/"


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print("[" + PluginLanguageDomain + "] fallback to default translation for " + txt)
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


def getText(nodelist):
	rc = []
	for node in nodelist:
		if node.nodeType == node.TEXT_NODE:
			rc.append(node.data)
	return ''.join(rc)

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
		<screen position="center,center" size="520,180" title="%s" >
			<widget name="info" position="5,5" size="510,140" font="Regular;18" halign="center" valign="center" />
			<widget name="progress" position="100,150" size="320,14" pixmap="skin_default/progress_big.png" borderWidth="2" borderColor="#cccccc" />
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
		<screen position="center,center" size="600,460" title="%s" >
			<widget name="list" position="5,5" size="590,250" scrollbarMode="showOnDemand" />
			<eLabel position="5,260" size="600,2" backgroundColor="#ffffff" />
			<widget name="info" position="5,265" size="600,190" font="Regular;18" />
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
				(url, length, type) = self.movies[idx][1]
				if config.plugins.Podcast.buffer.value:
					file = url
					while file.__contains__("/"):
						idx = file.index("/")
						file = file[idx + 1:]
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
		getPage(six.ensure_binary(self.url)).addCallback(self.showMovies).addErrback(self.error)

	def showMovies(self, page):
		if '<item>' in page:
			dom = xmlparseString(page)
			items = dom.getElementsByTagName("item")
		else:
			item = xmlparseString(page)
			items = [item]	
		
		for item in items:
			title = getText(item.getElementsByTagName("title")[0].childNodes).encode('utf8')
			description = getText(item.getElementsByTagName("description")[0].childNodes).encode('utf8')
			url = item.getElementsByTagName("enclosure")[0].getAttribute("url").encode('utf8')
			if url == "":
				url = "N/A"
			length = item.getElementsByTagName("enclosure")[0].getAttribute("length").encode('utf8')
			if length == "":
				length = "N/A" 
			type = item.getElementsByTagName("enclosure")[0].getAttribute("type").encode('utf8')
			if type == "":
				type = "N/A"
			self.list.append(encodeUrl(title))
			self.movies.append([description, (url, length, type)])
			
		self["list"].setList(self.list)
		self.showInfo()
		self.working = False

	def error(self, error=""):
		print("[Podcast] Error:", error)
		self.instance.setTitle(_("Error getting movies"))
		self.working = False

	def showInfo(self):
		if len(self.list) > 0:
			idx = self["list"].getSelectionIndex()
			description = self.movies[idx][0]
			(url, length, type) = self.movies[idx][1]
			self["info"].setText("%s: %s   %s: %s\n%s" % (_("Length"), length, _("Type"), type, encodeUrl(description)))

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
		file = None
		source = None

		# try user defined list, else fall back to default
		if fileExists(configDir + "podcasts_local.xml"):
			fileName = configDir + "podcasts_local.xml"
		else:
			fileName = configDir + "podcasts.xml"
				
		try:
			file = open(fileName)
		except:
			pass
		
		if file:
			# check if file is just a proxy to an external XML
			head = file.readline()
			print(head)
			if head.startswith("http"):
				print("open url")
				file.close
				try:
					source = urlopen(head)
				except:
					pass
			else:
				file.close
				source = open(fileName)
			
			if source:
				try:
					xml = parse(source).getroot()
					for language in xml.findall("language"):
						name = language.get("name") or None
						name = name.encode("UTF-8") or name
						if name:
							list.append(name)
							self.languages.append(language)
				except:
					pass
				source.close()
			
		self["list"] = MenuList(list)

	def ok(self):
		if len(self.languages) > 0:
			cur = self.languages[self["list"].getSelectedIndex()]
			self.session.open(PodcastProvider, cur)

###################################################

# Sadly Feedly OPML URL is not stable, seems to change after a while :(
# Deactivated in selection


class PodcastFeedly(Screen):
	skin = """
		<screen position="center,center" size="420,360" title="%s" >
			<widget name="list" position="0,0" size="420,350" scrollbarMode="showOnDemand" />
		</screen>""" % _("Podcast")
		
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.ok, "cancel": self.close}, -1)
		self.urls = []
		list = []
		file = None
		
		fileName = configDir + "feedly.opml"

		try:
			if fileExists(fileName):
				file = open(fileName)
			else:
				list.append(_("No Feedly configuration"))
		except:
			pass

		if file:
			# check if file is just a proxy to an external XML
			head = file.readline()

			try:
				if head.startswith("http"):
					file.close
					source = urlopen(head)
				else:
					file.close
					source = open(fileName)
			except:
				pass
			
			if source:	
				dom = xmlparse(source)
				for item in dom.getElementsByTagName("outline"):
					if str(item.getAttribute("title")) == "PodcastPlugin":
						for podcast in item.getElementsByTagName("outline"):
							list.append(str(podcast.getAttribute("title")))
							self.urls.append(str(podcast.getAttribute("xmlUrl")))

		self["list"] = MenuList(list)

	def ok(self):
		if len(self.urls) > 0:
			cur = self.urls[self["list"].getSelectedIndex()]
			self.session.open(PodcastMovies, cur)

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
		
		try:
			self["filelist"] = FileList(dir, showDirectories=True, showFiles=False)
		except:
			self["filelist"] = FileList("/", showDirectories, showFiles)
		
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


class Podcast(Screen):
	skin = """
		<screen position="center,center" size="560,360" title="%s" >
                	<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
                        <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
                        <ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
                        <ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
                        <widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="list" position="0,45" size="560,305" scrollbarMode="showOnDemand" />
		</screen>""" % _("Podcast")

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		
		self["key_blue"] = Label(_("Help"))
		
		self["actions"] = ActionMap(["ColorActions", "OkCancelActions"], {"ok": self.ok, "cancel": self.close, "blue": self.help}, -1)
		
		# Feedly removed until found a way to get a stable source URL
		self["list"] = MenuList([
			_("from xml"),
			_("configuration")])

	def ok(self):
		cur = self["list"].getCurrent()
		if cur == _("from xml"):
			self.session.open(PodcastXML)
		elif cur == _("Feedly OPML"):
			self.session.open(PodcastFeedly)
		else:
			self.session.open(PodcastConfig)

	def help(self):
		localehelpfile = "%s/Extensions/Podcast/help/help_%s" % (resolveFilename(SCOPE_PLUGINS), language.getLanguage()[:2])
		fallbackhelpfile = "%s/Extensions/Podcast/help/help_en" % resolveFilename(SCOPE_PLUGINS)
		if fileExists(localehelpfile):
			helpfile = localehelpfile
		else:
			helpfile = fallbackhelpfile
		h = open(helpfile)
		helptext = h.read()
		h.close
		self.session.open(TextBox, helptext)

###################################################


def main(session, **kwargs):
	session.open(Podcast)


def Plugins(**kwargs):
	return PluginDescriptor(name=_("Podcast"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)
