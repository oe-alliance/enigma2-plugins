##
## ORF.at IPTV
## by AliAbdul
##
from Components.ActionMap import ActionMap
from Components.Pixmap import MovingPixmap, Pixmap
from enigma import ePoint, eServiceReference, eSize, eTimer
from os import listdir
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from time import sleep
from Tools.BoundFunction import boundFunction
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap
from twisted.web.client import downloadPage, getPage
import re
import urllib2

##########################################################

PNG_PATH = resolveFilename(SCOPE_PLUGINS)+"/Extensions/ORFat/"

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

##########################################################

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
			if p.name != "ORF.at IPTV":
				list.append(((boundFunction(self.getPluginName, p.name), boundFunction(self.runPlugin, p), lambda: True), None))
		return list

	def showMovies(self):
		pass

##########################################################

class ORFatCache(Screen):
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
		self.Shown = False
		
		self.timer = eTimer()
		self.timer.callback.append(self.showNextSpinner)

	def start(self):
		self.show()
		self.Shown = True
		self.timer.start(200, False)

	def stop(self):
		self.hide()
		self.Shown = False
		self.timer.stop()

	def showNextSpinner(self):
		self.curr += 1
		if self.curr > 10:
			self.curr = 0
		png = LoadPixmap(cached=True, path=PNG_PATH + str(self.curr) + ".png")
		self["spinner"].instance.setPixmap(png)

##########################################################

class ORFMain(Screen):
	skin = """
	<screen position="center,center" size="550,450" title="ORF.at IPTV - Server:" backgroundColor="#6699cc" >
		<ePixmap pixmap="skin_default/arrowup.png" position="256,10" size="37,70" alphatest="blend" />
		<widget name="pic" position="0,0" size="0,0" />
		<ePixmap pixmap="skin_default/arrowdown.png" position="256,370" size="37,70" alphatest="blend" />
	</screen>"""
	
	def __init__(self, session):
		Screen.__init__(self, session)
		
		self.session = session
		self.movies = []
		self.pics = []
		self.names = []
		self.selectedEntry = 0
		self.mainUrl = "http://iptv.orf.at"
		self.pic = "/tmp/orf.jpg"
		self.working = False
		self.cacheDialog = self.session.instantiateDialog(ORFatCache)
		self.cacheTimer = eTimer()
		self.cacheTimer.callback.append(self.chechCachedFile)
		self.transcodeServer = None
		
		self["pic"] = MovingPixmap()
		self["actions"] = ActionMap(["WizardActions", "MenuActions"],
			{
				"ok": self.okClicked,
				"back": self.exit,
				"up": self.up,
				"down": self.down,
				"menu": self.selectServer
			}, -1)
		
		self.onLayoutFinish.append(self.downloadList)

	def getVideoUrl(self, url):
		try:
			f = urllib2.urlopen(url)
			txt = f.read()
			f.close()
		except:
			txt = ""
		ret = None
		if 'flashVars="vidUrl=' in txt:
			reonecat = re.compile(r'flashVars="vidUrl=(.+?).flv', re.DOTALL)
			urls = reonecat.findall(txt)
			if len(urls):
				ret = urls[0] + ".flv"
		return ret

	def okClicked(self):
		if self.working == False:
			if len(self.movies) > 0:
				if self.cacheDialog.Shown:
					self.playCachedFile()
				else:
					url = self.movies[self.selectedEntry]
					url = self.getVideoUrl(url)
					if url:
						if self.transcodeServer is not None:
							if self.transcodeServer == "LT Stream2Dream":
								r = streamplayer.play(url)
								if r == "ok":
									sleep(6)
									self.cacheDialog.start()
									self.cacheTimer.start(1000, False)
							else:
								self.transcodeServer.play(self.session, url, self.names[self.selectedEntry])
						else:
							self.session.open(MessageBox, "Es wurde kein Server ausgewaehlt!", MessageBox.TYPE_ERROR)
					else:
						self.session.open(MessageBox, "Fehler beim Ermitteln der Video URL!", MessageBox.TYPE_ERROR)

	def exit(self):
		if not self.working:
			if self.cacheDialog.Shown:
				if streamplayer:
					if streamplayer.connected:
						streamplayer.stop()
						sleep(4)
				self.deactivateCacheDialog()
			else:
				if streamplayer:
					if streamplayer.connected:
						streamplayer.logout()
				self.session.deleteDialog(self.cacheDialog)
				self.close()

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
					self.setTitle("ORF.at IPTV - Server: LT Stream2Dream")
					self.connectToStream2Dream()
			else:
				if streamplayer:
					if streamplayer.connected:
						streamplayer.logout()
				self.transcodeServer = server
				self.setTitle("ORF.at IPTV - Server: %s"%server.getName())

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
			self.setTitle("ORF.at IPTV - Server:")

	def chechCachedFile(self):
		try:
			f = open("/tmp/mpstream/progress.txt")
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

	def downloadList(self):
		self.working = True
		getPage(self.mainUrl).addCallback(self.downloadListCallback).addErrback(self.downloadListError)

	def downloadListError(self, error=""):
		print "[ORF.at] Fehler beim Verbindungsversuch:", str(error)
		self.working = False
		self.session.open(MessageBox, "Fehler beim Verbindungsversuch!", MessageBox.TYPE_ERROR)

	def downloadListCallback(self, page=""):
		if '<div class="griditem' in page:
			reonecat = re.compile(r'<div class="griditem(.+?)</div>', re.DOTALL)
			divs = reonecat.findall(page)
			for div in divs:
				if ('href="' in div) and ('<img src="' in div):
					reonecat = re.compile(r'href="(.+?)">.+?<img src="(.+?)".+?alt="(.+?)"', re.DOTALL)
					for url, picUrl, name in reonecat.findall(div):
						self.movies.append(self.mainUrl + url)
						self.pics.append(self.mainUrl + picUrl)
						self.names.append(name)
		self.selectionChanged(0)

	def up(self):
		if self.working == False:
			self.selectionChanged(-1)

	def down(self):
		if self.working == False:
			self.selectionChanged(1)

	def selectionChanged(self, direction):
		if len(self.movies) > 0:
			self.working = True
			self.selectedEntry += direction
			if self.selectedEntry < 0:
				self.selectedEntry = len(self.movies) - 1
			elif self.selectedEntry > len(self.movies) - 1:
				self.selectedEntry = 0
			downloadPage(self.pics[self.selectedEntry], self.pic).addCallback(self.downloadPicCallback).addErrback(self.downloadPicError)
		else:
			self.downloadListError()

	def downloadPicCallback(self, page=""):
		picture = LoadPixmap(self.pic)
		size = picture.size()
		width = size.width()
		height = size.height()
		self["pic"].instance.setPixmap(picture)
		self["pic"].instance.resize(eSize(width, height))
		left = int((550 / 2) - (width / 2))
		top = int((450 / 2) - (height / 2))
		self["pic"].moveTo(left, top, 1)
		self["pic"].startMoving()
		self["pic"].show()
		self.working = False

	def downloadPicError(self, error=""):
		print str(error)
		self["pic"].hide()
		self.working = False
		self.session.open(MessageBox, "Fehler beim Herunterladen des Eintrags!", MessageBox.TYPE_ERROR)

####################################################

def main(session, **kwargs):
	session.open(ORFMain)

def Plugins(**kwargs):
	return PluginDescriptor(name="ORF.at IPTV", description="IPTV-Sendungen von ORF.at anschauen", where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], icon="orf.png", fnc=main)
