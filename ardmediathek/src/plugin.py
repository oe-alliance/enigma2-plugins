# -*- coding: UTF-8 -*-
# ARD Mediathek by AliAbdul
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap
from Components.PluginComponent import plugins
from enigma import eListboxPythonMultiContent, ePicLoad, eServiceReference, eTimer, getDesktop, gFont
from os import listdir
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from time import sleep
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap
from twisted.web.client import downloadPage, getPage
import re, urllib2

###################################################

MAIN_PAGE = "http://www.ardmediathek.de"

PNG_PATH = resolveFilename(SCOPE_PLUGINS)+"/Extensions/ARDMediathek/"

try:
	from LT.LTStreamPlayer import streamplayer
except ImportError:
	try:
		from Plugins.Extensions.LTMediaCenter.LTStreamPlayer import streamplayer
	except ImportError:
		streamplayer = None

try:
	from Plugins.Extensions.VlcPlayer.VlcServerConfig import vlcServerConfig
except ImportError:
	vlcServerConfig = None

###################################################

def encodeHtml(html):
	html = html.replace("&amp;", "&")
	html = html.replace("&lt;", "<")
	html = html.replace("&gt;", ">")
	html = html.replace("&#39;", "'")
	html = html.replace("&quot;", '"')
	html = html.replace("&#42;", "*")
	html = html.replace("&#124;", "|")
	html = html.replace("&#034;", '"')
	html = html.replace("&#039;", "'")
	return html

###################################################

class ChangedMoviePlayer(MoviePlayer):
	def __init__(self, session, service):
		MoviePlayer.__init__(self, session, service)
		self.skinName = "MoviePlayer"

	def leavePlayer(self):
		self.session.openWithCallback(self.leavePlayerConfirmed, MessageBox, "Abspielen beenden?")

	def leavePlayerConfirmed(self, answer):
		if answer:
			self.close()

	def doEofInternal(self, playing):
		pass

	def getPluginList(self):
		list = []
		for p in plugins.getPlugins(where=PluginDescriptor.WHERE_EXTENSIONSMENU):
			if p.name != "ARD Mediathek":
				list.append(((boundFunction(self.getPluginName, p.name), boundFunction(self.runPlugin, p), lambda: True), None))
		return list

	def showMovies(self):
		pass

###################################################

def getCategories(html):
	list = []
	start = """<div class="mt-reset mt-categories">"""
	end = '</div>'
	if start and end in html:
		idx = html.index(start)
		html = html[idx:]
		idx = html.index(end)
		html = html[:idx]
		reonecat = re.compile(r'<li><a href="(.+?)" title="">(.+?)</a></li>', re.DOTALL)
		for url, name in reonecat.findall(html):
			list.append([MAIN_PAGE + url, encodeHtml(name)])
	return list

def getMovies(html):
	list = []
	start = '<li class="zelle'
	end = '</li>'
	if (start in html) and (end in html):
		while (start in html) and (end in html):
			idx = html.index(start)
			html = html[idx:]
			idx = html.index(end)
			div = html[:idx]
			html = html[idx:]
			reonecat = re.compile(r'<img src="(.+?)"', re.DOTALL)
			thumbs = reonecat.findall(div)
			if len(thumbs):
				thumb = MAIN_PAGE + thumbs[0]
				if thumb.endswith("drop.jpg") and len(thumbs) > 1:
					thumb = MAIN_PAGE + thumbs[1]
			else:
				thumb = None
			reonecat = re.compile(r'<a href="(.+?)"', re.DOTALL)
			urls = reonecat.findall(div)
			if len(urls):
				url = MAIN_PAGE + urls[0]
			else:
				url = None
			reonecat = re.compile(r'<span class="beitragstitel"><strong>(.+?)</strong></span>', re.DOTALL)
			titles = reonecat.findall(div)
			if len(titles):
				title = encodeHtml(titles[0])
			else:
				title = None
			reonecat = re.compile(r'<span class="infotext">(.+?)</span><br />', re.DOTALL)
			infos = reonecat.findall(div)
			if len(infos):
				info = encodeHtml(infos[0])
			else:
				info = None
			reonecat = re.compile(r'<span class="cliplaenge">(.+?)</span>', re.DOTALL)
			lengths = reonecat.findall(div)
			if len(lengths):
				length = lengths[0]
			else:
				length = None
			if title and info and length and url and thumb:
				list.append([title, info, length, url, thumb])
	return list

def getMovieUrls(url):
	try:
		f = urllib2.urlopen(url)
		html = f.read()
		f.close()
	except:
		html = ""
	list = []
	if 'player.avaible_url' in html:
		content = html.split("\n")
		for line in content:
			if 'player.avaible_url' in line:
				reonecat = re.compile(r'player.avaible_url(.+?) = "(.+?)";', re.DOTALL)
				for tmp, url in reonecat.findall(line):
					if 'flashmedia' in tmp:
						type = "flv"
					elif 'microsoftmedia' in tmp:
						type = "wmv"
					else:
						type = "n/a"
					if not url.startswith("rtmpt"):
						list.append([type, url])
	return list

def getPageNavigation(html):
	list = []
	start = '<!-- ANFANG navigation folge seiten -->'
	end = '<!-- ENDE navigation folgeseiten -->'
	if (start in html) and (end in html):
		idx = html.index(start)
		idx2 = html.index(end)
		lines = html[idx:idx2].split("\n")
		for line in lines:
			if ('<strong>' in line) and ('</strong>' in line):
				reonecat = re.compile(r'<strong>(.+?)</strong>', re.DOTALL)
				pages = reonecat.findall(line)
				if len(pages):
					page = pages[0]
					if 'left aktiv' in line:
						list.append([page, None])
					else:
						reonecat = re.compile(r'<a href="(.+?)"><strong>', re.DOTALL)
						urls = reonecat.findall(line)
						if len(urls):
							list.append([page, urls[0]])
	return list

###################################################

class ARDMediathekCache(Screen):
	skin = """
		<screen position="center,center" size="76,76" flags="wfNoBorder" backgroundColor="#ffffff" >
			<eLabel position="2,2" zPosition="1" size="72,72" font="Regular;18" backgroundColor="#252525" />
			<widget name="spinner" position="14,14" zPosition="2" size="48,48" alphatest="on" />
		</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		
		self["spinner"] = Pixmap()
		self.curr = 0
		self.__shown = False
		
		self.timer = eTimer()
		self.timer.callback.append(self.showNextSpinner)

	def start(self):
		self.__shown = True
		self.show()
		self.timer.start(200, False)

	def stop(self):
		self.hide()
		self.timer.stop()
		self.__shown = False

	def isShown(self):
		return self.__shown

	def showNextSpinner(self):
		self.curr += 1
		if self.curr > 10:
			self.curr = 0
		png = LoadPixmap(cached=True, path=PNG_PATH + str(self.curr) + ".png")
		self["spinner"].instance.setPixmap(png)

###################################################

class ARDMenuList(MenuList):
	def __init__(self):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		self.l.setItemHeight(25)
		self.l.setFont(0, gFont("Regular", 20))

def ARDMenuListEntry(url, name):
	res = [(url, name)]
	res.append(MultiContentEntryText(pos=(0, 0), size=(580, 20), font=0, text=name, color=0xffffff))
	return res

def ARDMenuListSubEntry(movie, thumb):
	res = [(movie[3], movie)]
	if thumb:
		res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(75, 50), png=thumb))
	res.append(MultiContentEntryText(pos=(80, 0), size=(500, 25), font=0, text=movie[2] + " - " + movie[0]))
	res.append(MultiContentEntryText(pos=(80, 25), size=(500, 25), font=0, text=movie[1]))
	return res

###################################################

class ARDMediathek(Screen):
	def __init__(self, session):
		self.session = session
		
		desktop = getDesktop(0)
		size = desktop.size()
		width = size.width()
		
		if width == 720:
			self.skin = """<screen position="0,0" size="720,576" flags="wfNoBorder" >"""
		else:
			self.skin = """<screen position="center,center" size="720,576" title="ARD Mediathek" >"""
		self.skin += """<ePixmap position="0,0" zPosition="-1" size="720,576" pixmap="%s" />
				<widget name="list" position="70,100" size="580,400" backgroundColor="#064b99" backgroundColorSelected="#003579" scrollbarMode="showOnDemand" />
				<ePixmap pixmap="skin_default/buttons/key_menu.png" position="70,520" size="35,25" transparent="1" alphatest="on" />
				<widget name="pageNavigation" position="260,520" size="380,400" halign="right" font="Regular;20" backgroundColor="#2666ad" foregroundColor="#ffffff" />
				<widget name="serverName" position="120,520" size="250,20" font="Regular;20" backgroundColor="#2666ad" foregroundColor="#ffffff" />
			</screen>""" % (PNG_PATH+"background.png")
		
		Screen.__init__(self, session)
		
		self["list"] = ARDMenuList()
		self["pageNavigation"] = Label()
		self["serverName"] = Label("Server")
		
		self["actions"] = ActionMap(["ARDMediathekActions"],
			{
				"back": self.exit,
				"ok": self.ok,
				"left": self.left,
				"right": self.right,
				"up": self.up,
				"down": self.down,
				"menu": self.selectServer,
				"mainpage": self.mainpage,
				"previousPage": self.previousPage,
				"nextPage": self.nextPage
			}, -1)
		
		self.cacheDialog = self.session.instantiateDialog(ARDMediathekCache)
		
		self.working = False
		self.mainpage = True
		self.pages = None
		self.transcodeServer = None
		self.movies = []
		self.listMovies = []
		
		self.cacheTimer = eTimer()
		self.cacheTimer.callback.append(self.chechCachedFile)
		
		self.onLayoutFinish.append(self.getPage)

	def mainpage(self):
		self.getPage()

	def getPage(self, url=None):
		self.working = True
		self.cacheDialog.start()
		self.mainpage = False
		if not url:
			self.mainpage = True
			url = MAIN_PAGE + "/ard/servlet/"
		getPage(url).addCallback(self.gotPage).addErrback(self.error)

	def error(self, err=""):
		print "[ARD Mediathek] Error:", err
		self.working = False
		self.deactivateCacheDialog()

	def gotPage(self, html=""):
		list = []
		if not self.mainpage:
			del self.movies
			del self.listMovies
			self.listMovies = []
			self.movies = getMovies(html)
			self["list"].l.setItemHeight(50)
			self.pages = getPageNavigation(html)
			txt = ""
			for page in self.pages:
				if page[1]:
					txt = txt + page[0] + " "
				else:
					txt = txt + "|" + page[0] + "| "
			self["pageNavigation"].setText(txt)
			self["pageNavigation"].show()
			self.buildList()
		else:
			categories = getCategories(html)
			for category in categories:
				list.append(ARDMenuListEntry(category[0], category[1]))
			self["list"].l.setItemHeight(25)
			self["list"].setList(list)
			self.pages = None
			self["pageNavigation"].setText("")
			self["pageNavigation"].hide()
			self.deactivateCacheDialog()

	def buildList(self):
		if len(self.movies):
			movie = self.movies[0]
			thumbUrl = movie[4]
			try:
				req = urllib2.Request(thumbUrl)
				url_handle = urllib2.urlopen(req)
				headers = url_handle.info()
				contentType = headers.getheader("content-type")
			except:
				contentType = None
			if contentType:
				if 'image/jpeg' in contentType:
					self.thumb = "/tmp/ard.jpg"
				elif 'image/gif' in contentType:
					self.thumb = "/tmp/ard.gif"
				elif 'image/png' in contentType:
					self.thumb = "/tmp/ard.png"
				else:
					print "[ARD Mediathek] Unknown thumbnail content-type:", contentType
					self.thumb = None
			else:
				self.thumb = None
			if self.thumb:
				downloadPage(thumbUrl, self.thumb).addCallback(self.downloadThumbnailCallback).addErrback(self.downloadThumbnailError)
			else:
				self.buildEntry(None)
		else:
			self["list"].setList(self.listMovies)
			self.deactivateCacheDialog()

	def downloadThumbnailError(self, err):
		print "[ARD Mediathek] Error:", err
		self.buildEntry(None)

	def downloadThumbnailCallback(self, txt=""):
		sc = AVSwitch().getFramebufferScale()
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.buildEntry)
		self.picload.setPara((75, 50, sc[0], sc[1], False, 1, "#00000000"))
		self.picload.startDecode(self.thumb)

	def buildEntry(self, picInfo=None):
		movie = self.movies[0]
		self.listMovies.append(ARDMenuListSubEntry(movie, self.picload.getData()))
		del self.movies[0]
		self.buildList()

	def chechCachedFile(self):
		try:
			f = open ("/tmp/mpstream/progress.txt")
			content = f.read()
			f.close()
			list = content.split("-")
			cacheMB = int(list[0])
			if cacheMB > 5: # Starte nach 5 MB Bufferung
				self.cacheTimer.stop()
				self.playCachedFile()
		except:
			pass

	def deactivateCacheDialog(self):
		self.cacheDialog.stop()
		self.working = False

	def playCachedFile(self):
		self.deactivateCacheDialog()
		ref = eServiceReference(1, 0, "/tmp/mpstream/MPStream.ts")
		self.session.openWithCallback(self.stopStream2Dream, ChangedMoviePlayer, ref)

	def stopStream2Dream(self, callback=None):
		streamplayer.stop()
		sleep(4)

	def selectServer(self):
		list = []
		if streamplayer:
			list.append(("LT Stream2Dream", "LT Stream2Dream"))
		if vlcServerConfig:
			serverList = vlcServerConfig.getServerlist()
			for x in serverList:
				list.append((x.getName(), x))
		if len(list):
			self.session.openWithCallback(self.serverChosen, ChoiceBox, title="Waehle den Server...", list=list)

	def serverChosen(self, callback):
		if callback:
			server = callback[1]
			if server == "LT Stream2Dream":
				if not streamplayer.connected:
					self.transcodeServer = "LT Stream2Dream"
					self["serverName"].setText("LT Stream2Dream")
					self.connectToStream2Dream()
			else:
				if streamplayer:
					if streamplayer.connected:
						streamplayer.logout()
				self.transcodeServer = server
				self["serverName"].setText(server.getName())

	def connectToStream2Dream(self):
		streamplayer.login()
		try:
			list = listdir("/tmp/mp")
		except:
			list = []
		if len(list) < 2:
			self.session.open(MessageBox, "Die Verbindung zu LT Stream2Dream konnte nicht hergestellt werden!", MessageBox.TYPE_ERROR)
			streamplayer.logout()
			self.transcodeServer = None
			self["serverName"].setText("Server")

	def exit(self):
		if not self.working:
			if self.cacheDialog.isShown() == False:
				if streamplayer:
					if streamplayer.connected:
						streamplayer.logout()
				self.session.deleteDialog(self.cacheDialog)
				self.close()
			else:
				if streamplayer:
					if streamplayer.connected:
						streamplayer.stop()
						sleep(4)
				self.deactivateCacheDialog()

	def ok(self):
		if not self.working:
			if self.cacheDialog.isShown() == False:
				curr = self["list"].getCurrent()
				if curr:
					if not self.mainpage:
						movies = getMovieUrls(curr[0][0])
						list = []
						for x in movies:
							list.append((x[0], x[1]))
						if len(list):
							self.session.openWithCallback(self.play, ChoiceBox, title="Selektiere...", list=list)
					else:
						self.getPage(curr[0][0])
			else:
				if streamplayer:
					if streamplayer.connected:
						if streamplayer.caching or streamclient.streaming:
							self.playCachedFile()

	def play(self, callback):
		if callback is not None:
			url = callback[1]
			if self.transcodeServer is not None:
				if self.transcodeServer == "LT Stream2Dream":
					r = streamplayer.play(url)
					if r == "ok":
						sleep(6)
						self.cacheDialog.start()
						self.cacheTimer.start(1000, False)
					else:
						self.session.open(MessageBox, "LT Stream2Dream konnte den Stream nicht starten!", MessageBox.TYPE_ERROR)
				else:
					self.transcodeServer.play(self.session, url, self["list"].getCurrent()[0][1][1])
			else:
				self.session.open(MessageBox, "Es wurde kein Server ausgewählt!", MessageBox.TYPE_ERROR)

	def left(self):
		if not self.working:
			self["list"].pageUp()

	def right(self):
		if not self.working:
			self["list"].pageDown()

	def up(self):
		if not self.working:
			self["list"].up()

	def down(self):
		if not self.working:
			self["list"].down()

	def removeSessionId(self, url):
		ret = url
		start = ';jsessionid='
		if start in url:
			idx = url.index(start)
			ret = url[:idx]
			url = url[idx:]
			idx = url.index("?")
			url = url[idx:]
			ret += url
		return encodeHtml(ret)

	def previousPage(self):
		if not self.working:
			page = None
			if self.pages:
				for x in self.pages:
					if not x[1]:
						break
					else:
						page = x
			if page:
				self.getPage(self.removeSessionId(MAIN_PAGE + page[1]))

	def nextPage(self):
		if not self.working:
			page = None
			if self.pages:
				curPage = False
				for x in self.pages:
					if not x[1]:
						curPage = True
					else:
						if curPage:
							page = x
							break
			if page:
				self.getPage(self.removeSessionId(MAIN_PAGE + page[1]))

###################################################

def start(session, **kwargs):
	session.open(ARDMediathek)

def Plugins(**kwargs):
	return PluginDescriptor(name="ARD Mediathek", description="Streame von der ARD Mediathek", where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], fnc=start)
