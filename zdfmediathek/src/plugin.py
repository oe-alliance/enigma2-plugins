# -*- coding: UTF-8 -*-
# ZDF Mediathek by AliAbdul
from Components.ActionMap import HelpableActionMap
from Components.AVSwitch import AVSwitch
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap
from Components.PluginComponent import plugins
from enigma import eListboxPythonMultiContent, ePicLoad, eServiceReference, eTimer, getDesktop, gFont
from os import listdir, popen
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from time import sleep
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.HardwareInfo import HardwareInfo
from Tools.LoadPixmap import LoadPixmap
from twisted.web.client import downloadPage, getPage
import htmlentitydefs, re, urllib2

###################################################

MAIN_PAGE = "http://www.zdf.de"

PNG_PATH = resolveFilename(SCOPE_PLUGINS)+"/Extensions/ZDFMediathek/"

TYPE_NOTHING = 0
TYPE_MOVIE = 1
TYPE_PODCAST = 2
TYPE_MOVIELIST_CATEGORY = 3

LIST_LEFT = 0
LIST_RIGHT = 1
LIST_NONE = 2

deviceName = HardwareInfo().get_device_name()

PLAY_MP4 = False

if not deviceName.startswith("dm7025"):
	try:
		#FIXMEE add better check ! ? !
		for line in popen("opkg info gst-plugin-rtsp").readlines():
			if line.find("Version: ") != -1:
				if line[9:] >= "0.10.23-r7.1":
					PLAY_MP4 = True
	except:
		pass

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

def decode(line):
	pat = re.compile(r'\\u(....)')
	def sub(mo):
		return unichr(fromHex(mo.group(1)))
	return pat.sub(sub, unicode(line))

def decode2(line):
	pat = re.compile(r'&#(\d+);')
	def sub(mo):
		return unichr(int(mo.group(1)))
	return decode3(pat.sub(sub, unicode(line)))

def decode3(line):
	dic = htmlentitydefs.name2codepoint
	for key in dic.keys():
		entity = "&" + key + ";"
		line = line.replace(entity, unichr(dic[key]))
	return line

def fromHex(h):
	return int(h, 16)

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
			if p.name != "ZDF Mediathek":
				list.append(((boundFunction(self.getPluginName, p.name), boundFunction(self.runPlugin, p), lambda: True), None))
		return list

	def showMovies(self):
		pass

###################################################

def getMovieDetails(div):
	list = []
	# Lese Sendung...
	reonecat = re.compile(r'<p class="grey"><a href="(.+?)">(.+?)</a></p>', re.DOTALL)
	content = reonecat.findall(div)
	if len(content):
		broadcast = decode2(decode(content[0][1])).encode("UTF-8")
		list.append(content[0][0])
		if broadcast.startswith("<"):
			broadcast = ""
		list.append(broadcast)
	# Lese Titel...
	reonecat = re.compile(r'<p><b><a href=".+?">(.+?)</a></b></p>', re.DOTALL)
	titles = reonecat.findall(div)
	if len(titles):
		title = titles[0]
		if '<br/>' in title:
			idx = title.index('<br/>')
			title = title[:idx]
		if '<br />' in title:
			idx = title.index('<br />')
			title = title[:idx]
		title = decode2(decode(title)).encode("UTF-8")
		list.append(title)
	# Lese Thumbnail-URL...
	reonecat = re.compile(r'<img src="(.+?)"', re.DOTALL)
	thumbnails = reonecat.findall(div)
	if len(thumbnails):
		list.append(thumbnails[0])
	# Lese Videolänge...
	if ('VIDEO, ' in div):
		reonecat = re.compile(r'>VIDEO, (.+?)</a></p>', re.DOTALL)
		lengths = reonecat.findall(div)
		if len(lengths):
			list.append(lengths[0])
	else:
		list.append("Live")
	# Alles gefunden?
	if len(list) == 5:
		return list
	else:
		return None

def getCategoryDetails(div):
	list = []
	# Lese Rubrik...
	reonecat = re.compile(r'<p class="grey"><a href="(.+?)">(.+?)</a></p>', re.DOTALL)
	content = reonecat.findall(div)
	if len(content):
		broadcast = decode2(decode(content[0][1])).encode("UTF-8")
		list.append(content[0][0])
		if broadcast.startswith("<"):
			broadcast = ""
		list.append(broadcast)
	# Lese Titel...
	reonecat = re.compile(r'<p><b><a href=".+?">(.+?)</a></b></p>', re.DOTALL)
	titles = reonecat.findall(div)
	if len(titles):
		title = titles[0]
		if '<br/>' in title:
			idx = title.index('<br/>')
			title = title[:idx]
		if '<br />' in title:
			idx = title.index('<br />')
			title = title[:idx]
		title = decode2(decode(title)).encode("UTF-8")
		list.append(title)
	# Lese Thumbnail-URL...
	reonecat = re.compile(r'<img src="(.+?)"', re.DOTALL)
	thumbnails = reonecat.findall(div)
	if len(thumbnails):
		list.append(thumbnails[0])
	# Lese Beitragsanzahl...
	reonecat = re.compile(r'">(.+?)BEITR&Auml;GE ZUR SENDUNG</a></p>', re.DOTALL)
	counts = reonecat.findall(div)
	if len(counts):
		count = counts[0]
		if '">' in count:
			while '">' in count:
				idx = count.index('">')
				count = count[idx+2:]
		if '"/>' in count:
			while '"/>' in count:
				idx = count.index('"/>')
				count = count[idx+3:]
		list.append("%sBeitraege"%count)
	else:
		reonecat = re.compile(r'">(.+?)BEITR&Auml;GE ZUM THEMA</a></p>', re.DOTALL)
		counts = reonecat.findall(div)
		if len(counts):
			count = counts[0]
			if '">' in count:
				while '">' in count:
					idx = count.index('">')
					count = count[idx+2:]
			if '"/>' in count:
				while '"/>' in count:
					idx = count.index('"/>')
					count = count[idx+3:]
			list.append("%sBeitraege"%count)
		else:
			reonecat = re.compile(r'">(.+?)BEITR&Auml;GE ZUR RUBRIK</a></p>', re.DOTALL)
			counts = reonecat.findall(div)
			if len(counts):
				count = counts[0]
				if '">' in count:
					while '">' in count:
						idx = count.index('">')
						count = count[idx+2:]
				if '"/>' in count:
					while '"/>' in count:
						idx = count.index('"/>')
						count = count[idx+3:]
				list.append("%sBeitraege"%count)
	# Alles gefunden?
	if len(list) == 5:
		return list
	else:
		return None

###################################################

def getMovieUrl(url):
	try:
		f = urllib2.urlopen(url)
		txt = f.read()
		f.close()
	except:
		txt = ""
	if ('rtsp' in txt) and ('.mp4' in txt):
		idx = txt.index('rtsp')
		idx2 = txt.index('.mp4')
		return txt[idx:idx2+4]
	else:
		return None

def getTitleLinks(html):
	links = []
	start = '<div id="breadcrumbContainer">'
	end = '</div>'
	if start in html:
		idx = html.index(start)
		html = html[idx:]
		idx = html.index(end)
		html = html[:idx]
		reonecat = re.compile(r'<a href="(.+?)">(.+?)</a>', re.DOTALL)
		for url, name in reonecat.findall(html):
			name = decode2(decode(name)).encode("UTF-8")
			links.append([url, name])
	return links

def getLeftMenu(html):
	list = []
	reonecat = re.compile(r'<div id="navigationContainer">(.+?)</div>', re.DOTALL)
	leftMenu = reonecat.findall(html)
	if len(leftMenu):
		reonecat = re.compile(r'<li><a href="(.+?)"(.+?)</a>', re.DOTALL)
		for url, name in reonecat.findall(leftMenu[0]):
			if name.startswith(' class="active">'):
				active = True
				name = name[16:]
			else:
				active = False
				name = name[1:]
			if (name != "Hilfe") and (not 'Podcasts' in name): # TODO: Podcasts brauchen noch etwas Arbeit... derzeit deaktiviert
				list.append([url, name, active])
	return list

def getRightMenu(html):
	list = []
	# Suche Filme...
	if '" class="play" target="_blank">Abspielen</a></li>' in html:
		reonecat = re.compile(r'<li>(.+?)<a href="(.+?)" class="play" target="_blank">Abspielen</a></li>', re.DOTALL)
		for speed, movie in reonecat.findall(html):
			list.append([speed, movie])
		if len(list):
			return [TYPE_MOVIE, list]
	# Suche podcasts...
	if '<!-- Start:Podcasts -->' in html:
		reonecat = re.compile(r'<!-- Start:Podcasts -->(.+?)<!-- Ende:Podcasts -->', re.DOTALL)
		tmp = reonecat.findall(html)
		if len(tmp):
			reonecat = re.compile(r'<p><b><a href="(.+?)".+?">(.+?)</a></b></p>', re.DOTALL)
			podcasts = reonecat.findall(tmp[0])
			for podcast in podcasts:
				list.append([podcast[0], podcast[1]])
		if len(list):
			return [TYPE_PODCAST, list]
	# Suche Videos und Rubriken...
	start = '<div class="beitragListe">'
	if '<div class="beitragFooterSuche">' in html:
		end = '<div class="beitragFooterSuche">'
	else:
		end = '<div class="beitragFooter">'
	if (start in html) and (end in html):
		while (start in html) and (end in html):
			idx = html.index(start)
			html = html[idx:]
			reonecat = re.compile(r'%s(.+?)%s'%(start, end), re.DOTALL)
			blocks = reonecat.findall(html)
			if blocks:
				reonecat = re.compile(r'<div class="image">(.+?)</li>', re.DOTALL)
				divs = reonecat.findall(blocks[0])
				for div in divs:
					details = None
					if ('VIDEO, ' in div) or ('>LIVE<' in div):
						details = getMovieDetails(div)
					elif 'BEITR&Auml;GE ZU' in div:
						details = getCategoryDetails(div)
					if details:
						list.append([details[0], details[1], details[2], details[3], details[4]])
			html = html[1:]
		reonecat = re.compile(r'<a href="(.+?)" class="weitereBeitraege"', re.DOTALL)
		more = reonecat.findall(html)
		if len(more):
			more = more[0]
			if 'href="' in more:
				while 'href="' in more:
					idx = more.index('href="')
					more = more[idx+6:]
			list.append([more, "", "", "", "Weitere  Beitraege laden."])
	if len(list):
		return [TYPE_MOVIELIST_CATEGORY, list]
	# Nichts :(
	return [TYPE_NOTHING, list]

###################################################

class LeftMenuList(MenuList):
	def __init__(self):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		self.l.setItemHeight(20)
		self.l.setFont(0, gFont("Regular", 18))
		self.menu = []
		self.active = True
		self.current = 0

	def setActive(self, active):
		self.active = active
		self.SetList(self.menu, True)

	def entry(self, text, active, selected):
		res = [(text)]
		if text.startswith("- Heute"):
			text = "- Heute"
		elif text.startswith("- Gestern"):
			text = "- Gestern"
		elif text.startswith("- Morgen"):
			text = "- Morgen"
		if selected:
			res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(20, 20), png=LoadPixmap(cached=True, path=PNG_PATH+"active.png")))
		if active:
			res.append(MultiContentEntryText(pos=(25, 0), size=(175, 20), font=0, text=text, color=0xf47d19))
		else:
			res.append(MultiContentEntryText(pos=(25, 0), size=(175, 20), font=0, text=text, color=0xffffff))
		return res

	def SetList(self, l, moveCursor=False):
		del self.menu
		self.menu = l
		if moveCursor:
			idx = 0
			for x in l:
				if x[2]:
					self.current = idx
				idx += 1
		list = []
		idx = 0
		for x in l:
			if (idx == self.current) and self.active:
				selected = True
			else:
				selected = False
			list.append(self.entry(x[1], x[2], selected))
			idx += 1
		self.setList(list)

	def getCurrentUrl(self):
		if len(self.menu):
			return self.menu[self.current][0]
		else:
			return None

	def select(self, index):
		if len(self.menu):
			if (index > -1) and (index < len(self.menu)):
				self.current = index
				self.SetList(self.menu)

	def first(self):
		self.select(0)

	def last(self):
		self.select(len(self.menu)-1)

	def previous(self):
		if len(self.menu):
			self.select(self.current-1)

	def next(self):
		if len(self.menu):
			self.select(self.current+1)

###################################################

class RightMenuList(MenuList):
	def __init__(self):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 18))
		self.l.setFont(1, gFont("Regular", 16))
		self.listCompleted = []
		self.callback = None
		self.idx = 0
		self.thumb = ""

	def buildEntries(self):
		if self.type == TYPE_PODCAST:
			list = []
			for x in self.list:
				title = x[1]
				if '<br/>' in title:
					idx = title.index('<br/>')
					title = title[:idx]
				title = decode2(decode(title)).encode("UTF-8")
				res = [(x[0], title)]
				res.append(MultiContentEntryText(pos=(0, 0), size=(430, 20), font=0, text=title))
				list.append(res)
			self.setList(list)
			if self.callback:
				self.callback()
		elif self.type == TYPE_MOVIELIST_CATEGORY:
			if self.idx == len(self.list):
				self.setList(self.listCompleted)
				if self.callback:
					self.callback()
			else:
				self.downloadThumbnail()

	def downloadThumbnail(self):
		thumbUrl = self.list[self.idx][3]
		if not thumbUrl.startswith("http://"):
			thumbUrl = "%s%s"%(MAIN_PAGE, thumbUrl)
		try:
			req = urllib2.Request(thumbUrl)
			url_handle = urllib2.urlopen(req)
			headers = url_handle.info()
			contentType = headers.getheader("content-type")
		except:
			contentType = None
		if contentType:
			if 'image/jpeg' in contentType:
				self.thumb = "/tmp/zdf.jpg"
			elif 'image/gif' in contentType:
				self.thumb = "/tmp/zdf.gif"
			elif 'image/png' in contentType:
				self.thumb = "/tmp/zdf.png"
			else:
				print "[ZDF Mediathek] Unknown thumbnail content-type:", contentType
				self.thumb = None
		else:
			self.thumb = None
		if self.thumb:
			downloadPage(thumbUrl, self.thumb).addCallback(self.downloadThumbnailCallback).addErrback(self.downloadThumbnailError)
		else:
			self.buildEntry(None)

	def downloadThumbnailError(self, err):
		print "[ZDF Mediathek] Error:", err
		self.buildEntry(None)

	def downloadThumbnailCallback(self, txt=""):
		sc = AVSwitch().getFramebufferScale()
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.buildEntry)
		self.picload.setPara((94, 60, sc[0], sc[1], False, 1, "#00000000"))
		self.picload.startDecode(self.thumb)

	def buildEntry(self, picInfo=None):
		x = self.list[self.idx]
		res = [(x[0], x[2])]
		if picInfo:
			ptr = self.picload.getData()
			if ptr != None:
				res.append(MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(94, 60), png=ptr))
		res.append(MultiContentEntryText(pos=(100, 0), size=(430, 20), font=0, text=x[2]))
		res.append(MultiContentEntryText(pos=(100, 20), size=(430, 20), font=0, text=x[4]))
		res.append(MultiContentEntryText(pos=(100, 40), size=(430, 20), font=1, text=x[1]))
		self.listCompleted.append(res)
		self.idx += 1
		self.buildEntries()

	def SetList(self, l):
		self.type = l[0]
		self.list = l[1]
		if self.type == TYPE_PODCAST:
			self.l.setItemHeight(20)
			self.buildEntries()
		elif self.type == TYPE_MOVIELIST_CATEGORY:
			self.l.setItemHeight(60)
			del self.listCompleted
			self.listCompleted = []
			self.idx = 0
			self.buildEntries()
		else:
			self.setList([])
			if self.callback:
				self.callback()

###################################################

class ZDFMediathekCache(Screen):
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
		
		self.timer = eTimer()
		self.timer.callback.append(self.showNextSpinner)

	def start(self):
		self.show()
		self.timer.start(200, False)

	def stop(self):
		self.hide()
		self.timer.stop()

	def showNextSpinner(self):
		self.curr += 1
		if self.curr > 10:
			self.curr = 0
		png = LoadPixmap(cached=True, path=PNG_PATH + str(self.curr) + ".png")
		self["spinner"].instance.setPixmap(png)

###################################################

class ZDFMediathek(Screen, HelpableScreen):
	def __init__(self, session):
		self.session = session
		
		desktop = getDesktop(0)
		size = desktop.size()
		width = size.width()
		
		if width == 720:
			self.skin = """<screen position="0,0" size="720,576" flags="wfNoBorder" backgroundColor="#252525" >"""
		else:
			self.skin = """<screen position="center,center" size="720,576" title="ZDF Mediathek" backgroundColor="#252525" >"""
		self.skin += """<ePixmap position="40,30" size="133,40" pixmap="%s" />
				<widget name="navigationTitle" position="250,40" size="430,25" font="Regular;18" backgroundColor="#252525" foregroundColor="#f47d19" noWrap="1" />
				<widget name="leftList" position="40,70" size="200,440" transparent="1" selectionDisabled="1" />
				<widget name="rightList" position="250,70" size="430,480" backgroundColor="#3d3c3c" backgroundColorSelected="#565656" selectionDisabled="1" scrollbarMode="showOnDemand" />
				<ePixmap pixmap="skin_default/buttons/key_menu.png" position="40,520" size="35,25" transparent="1" alphatest="on" />
				<widget name="serverName" position="80,520" size="160,20" font="Regular;18" backgroundColor="#252525" foregroundColor="#f47d19" />
				<widget name="fakeList" position="0,0" size="0,0" />
			</screen>""" % (PNG_PATH+"logo.png")
		
		Screen.__init__(self, session)
		
		self["navigationTitle"] = Label(" ")
		self["leftList"] = LeftMenuList()
		self["rightList"] = RightMenuList()
		self["fakeList"] = MenuList([])
		self["serverName"] = Label("Server")
		
		HelpableScreen.__init__(self)
		
		self["actions"] = HelpableActionMap(self, "ZDFMediathekActions",
			{
				"back": (self.exit, "Beenden"),
				"ok": (self.ok, "Selektieren"),
				"left": (self.left, "Seite hoch"),
				"right": (self.right, "Seite runter"),
				"up": (self.up, "Hoch"),
				"down": (self.down, "Runter"),
				"previousList": (self.toggleList, "Liste umschalten"),
				"nextList": (self.toggleList, "Liste umschalten"),
				"menu": (self.selectServer, "Selektiere Server"),
				"search": (self.search, "Suche"),
				"previousPage": (self.previousPage, "Vorherige Seite")
			}, -2)
		
		self.cacheDialog = self.session.instantiateDialog(ZDFMediathekCache)
		self["rightList"].callback = self.deactivateCacheDialog
		self.working = False
		self.currentList = LIST_RIGHT
		self.linkPreviousPage = ""
		
		self.transcodeServer = None
		self.cacheTimer = eTimer()
		self.cacheTimer.callback.append(self.chechCachedFile)
		
		self.onLayoutFinish.append(self.getPage)

	def getPage(self, page=None):
		self.working = True
		if not page:
			page = "/ZDFmediathek/hauptnavigation/startseite?flash=off"
		url = "%s%s"%(MAIN_PAGE, page)
		getPage(url).addCallback(self.gotPage).addErrback(self.error)

	def error(self, err=""):
		print "[ZDF Mediathek] Error:", err
		self.working = False
		self.deactivateCacheDialog()

	def gotPage(self, html=""):
		rightMenu = getRightMenu(html)
		if rightMenu[0] == TYPE_MOVIE:
			list = []
			for x in rightMenu[1]:
				list.append(("%s %s"%(x[0], x[1].split(".")[-1]), x[1]))
			if len(list):
				self.session.openWithCallback(self.play, ChoiceBox, title="Selektiere...", list=list)
			else:
				self.working = False
		else:
			self.cacheDialog.start()
			self.currentList = LIST_NONE
			links = getTitleLinks(html)
			txt = ""
			for x in links:
				txt = txt + x[1] + " / "
			if len(txt) > 1:
				txt = txt[:-3]
				if (len(links) > 1):
					self.linkPreviousPage = links[-2][0]
				else:
					self.linkPreviousPage = ""
			else:
				self.linkPreviousPage = ""
			self["navigationTitle"].setText(txt)
			self["leftList"].SetList(getLeftMenu(html), True)
			self["rightList"].SetList(rightMenu)
			self["leftList"].selectionEnabled(0)
			self["rightList"].selectionEnabled(1)
			self["fakeList"].selectionEnabled(0)
			self["leftList"].setActive(False)

	def previousPage(self):
		self.getPage(self.linkPreviousPage)

	def search(self):
		self.session.openWithCallback(self.searchCallback, VirtualKeyBoard, title="Suche nach:")

	def searchCallback(self, callback):
		if callback and (callback != ""):
			self.getPage("/ZDFmediathek/suche?sucheText=%s&offset=0&flash=off"%(callback.replace(" ", "+")))

	def play(self, callback):
		self.working = False
		if callback is not None:
			url = callback[1]
			if url.endswith(".mov"):
				url = getMovieUrl(url)
			if url:
				if PLAY_MP4 and url.endswith(".mp4"):
					ref = eServiceReference(4097, 0, url)
					self.session.open(ChangedMoviePlayer, ref)
				else: # Die Hardware kann das Format nicht direkt abspielen, mit Stream2Dream oder vlc Server probieren...
					if self.transcodeServer is not None:
						if self.transcodeServer == "LT Stream2Dream":
							r = streamplayer.play(url)
							if r == "ok":
								sleep(6)
								self.currentList = LIST_NONE
								self.cacheDialog.start()
								self.cacheTimer.start(1000, False)
						else:
							self.transcodeServer.play(self.session, url, self["rightList"].getCurrent()[0][1])
					else:
						self.session.open(MessageBox, "Es wurde kein Server ausgewählt!", MessageBox.TYPE_ERROR)
			else:
				self.session.open(MessageBox, "Fehler beim Ermitteln der Film-URL!", MessageBox.TYPE_ERROR)

	def chechCachedFile(self):
		try:
			f = open ("/tmp/mpstream/progress.txt")
			content = f.read()
			f.close()
			list = content.split("-")
			cacheMB = int(list[0])
			if cacheMB > 10: # Starte nach 10 MB Bufferung
				self.cacheTimer.stop()
				self.playCachedFile()
		except:
			pass

	def deactivateCacheDialog(self):
		self.cacheDialog.stop()
		self.currentList = LIST_RIGHT
		self.working = False

	def playCachedFile(self):
		self.deactivateCacheDialog()
		ref = eServiceReference(1, 0, "/tmp/mpstream/MPStream.ts")
		self.session.openWithCallback(self.stopStream2Dream, ChangedMoviePlayer, ref)

	def stopStream2Dream(self, callback=None):
		streamplayer.stop()
		sleep(4)

	def toggleList(self):
		if not self.working:
			if self.currentList == LIST_LEFT:
				self.currentList = LIST_RIGHT
				self["leftList"].setActive(False)
				self["fakeList"].selectionEnabled(0)
				self["rightList"].selectionEnabled(1)
			elif self.currentList == LIST_RIGHT:
				self.currentList = LIST_LEFT
				self["leftList"].setActive(True)
				self["rightList"].selectionEnabled(0)
				self["fakeList"].selectionEnabled(1)

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
			if self.currentList == LIST_LEFT:
				self.toggleList()
			elif self.currentList == LIST_RIGHT:
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
			if self.currentList == LIST_LEFT:
				self.getPage(self["leftList"].getCurrentUrl())
			elif self.currentList == LIST_RIGHT:
				curr = self["rightList"].getCurrent()
				if curr:
					self.getPage(curr[0][0])
			elif streamplayer:
				if streamplayer.connected:
					if streamplayer.caching or streamclient.streaming:
						self.playCachedFile()

	def left(self):
		if not self.working:
			if self.currentList == LIST_LEFT:
				self["leftList"].first()
			elif self.currentList == LIST_RIGHT:
				self["rightList"].pageUp()

	def right(self):
		if not self.working:
			if self.currentList == LIST_LEFT:
				self["leftList"].last()
			elif self.currentList == LIST_RIGHT:
				self["rightList"].pageDown()

	def up(self):
		if not self.working:
			if self.currentList == LIST_LEFT:
				self["leftList"].previous()
			elif self.currentList == LIST_RIGHT:
				self["rightList"].up()

	def down(self):
		if not self.working:
			if self.currentList == LIST_LEFT:
				self["leftList"].next()
			elif self.currentList == LIST_RIGHT:
				self["rightList"].down()

###################################################

def start(session, **kwargs):
	session.open(ZDFMediathek)

def Plugins(**kwargs):
	return PluginDescriptor(name="ZDF Mediathek", description="Streame von der ZDF Mediathek", where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], fnc=start)
