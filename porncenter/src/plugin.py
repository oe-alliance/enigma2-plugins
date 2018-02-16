# -*- coding: utf-8 -*-
# Porn Center by AliAbdul
from Additions.Plugin import cache, getPlugins
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSelection, ConfigSubsection, ConfigText, ConfigYesNo, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from Components.FileList import FileList
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaBlend, MultiContentEntryText
from Components.PluginComponent import plugins
from Components.ProgressBar import ProgressBar
from enigma import eListboxPythonMultiContent, eServiceReference, eTimer, getDesktop, gFont
from os import remove
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.ParentalControlSetup import ProtectedScreen
from Screens.Screen import Screen
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS
from Tools.Downloader import downloadWithProgress
from Tools.LoadPixmap import LoadPixmap
import os, gettext

##################################################

desktop = getDesktop(0)
size = desktop.size()
WIDTH = size.width()
HEIGHT = size.height()

##################################################

PluginLanguageDomain = "PornCenter"
PluginLanguagePath = "Extensions/PornCenter/locale/"

def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print "[" + PluginLanguageDomain + "] fallback to default translation for " + txt
		return gettext.gettext(txt)

language.addCallback(localeInit())

##################################################

config.plugins.PornCenter = ConfigSubsection()
config.plugins.PornCenter.name = ConfigText(default=_("Porn Center"), fixed_size=False)
config.plugins.PornCenter.description = ConfigText(default=_("Adult streaming plugins for dm800/dm8000"), fixed_size=False)
config.plugins.PornCenter.buffer = ConfigYesNo(default=True)
config.plugins.PornCenter.bufferDevice = ConfigText(default="/media/hdd/", fixed_size=False)
config.plugins.PornCenter.keepStored = ConfigSelection(choices={"delete": _("delete"), "keep": _("keep on device"), "ask": _("ask me")}, default="delete")

##################################################

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

##################################################

class PornCenterBuffer(Screen):
	skin = """
		<screen position="center,center" size="520,80" title="%s" >
			<widget name="info" position="5,5" size="510,40" font="Regular;18" halign="center" valign="center" />
			<widget name="progress" position="100,50" size="320,14" pixmap="skin_default/progress_big.png" borderWidth="2" borderColor="#cccccc" />
		</screen>""" % _("Porn Center")

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

##################################################

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
			if (p.name != _("Porn Center")) and (p.name != config.plugins.PornCenter.name.value):
				list.append(((boundFunction(self.getPluginName, p.name), boundFunction(self.runPlugin, p), lambda: True), None))
		return list

	def showMovies(self):
		pass

##################################################

class PornCenterLocationSelection(Screen):
	skin = """
	<screen position="center,center" size="560,300" title="%s">
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
		<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="filelist" position="10,45" size="550,255" scrollbarMode="showOnDemand" />
	</screen>""" % _("Porn Center")

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

##################################################

class PornCenterConfig(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="520,150" title="%s" >
			<widget name="config" position="0,0" size="520,150" scrollbarMode="showOnDemand" />
		</screen>""" % _("Porn Center")

	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self.session = session
		
		ConfigListScreen.__init__(self, [])
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.change, "cancel": self.exit}, -2)
		
		self.onLayoutFinish.append(self.createConfig)

	def createConfig(self):
		self.deviceEntry = ConfigSelection(choices=[config.plugins.PornCenter.bufferDevice.value], default=config.plugins.PornCenter.bufferDevice.value)
		self["config"].list = [
			getConfigListEntry(_("Name:"), config.plugins.PornCenter.name),
			getConfigListEntry(_("Description:"), config.plugins.PornCenter.description),
			getConfigListEntry(_("Buffer:"), config.plugins.PornCenter.buffer),
			getConfigListEntry(_("Buffer device:"), self.deviceEntry),
			getConfigListEntry(_("Buffer file handling:"), config.plugins.PornCenter.keepStored)]

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.handleKeysLeftAndRight()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.handleKeysLeftAndRight()

	def handleKeysLeftAndRight(self):
		sel = self["config"].getCurrent()[1]
		if sel == self.deviceEntry:
			self.session.openWithCallback(self.locationSelected, PornCenterLocationSelection, config.plugins.PornCenter.bufferDevice.value)

	def locationSelected(self, dir):
		if dir is not None and dir != "?":
			config.plugins.PornCenter.bufferDevice.value = dir
			config.plugins.PornCenter.bufferDevice.save()
			self.createConfig()

	def change(self):
		for x in self["config"].list:
			x[1].save()
		self.close()

	def exit(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

##################################################

class PinChecker:
	def __init__(self):
		self.pin_entered = False
		self.timer = eTimer()
		self.timer.callback.append(self.lock)

	def pinEntered(self):
		self.pin_entered = True
		self.timer.start(60000*10, 1)

	def lock(self):
		self.pin_entered = False
pinchecker = PinChecker()

##################################################

class PornCenterList(MenuList):
	def __init__(self):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		self.l.setItemHeight(75)
		if WIDTH == 720:
			self.l.setFont(0, gFont("Regular", 30))
			self.center_up = 22
		else:
			self.l.setFont(0, gFont("Regular", 40))
			self.center_up = 15

	def SetList(self, entries):
		list = []
		for entry in entries:
			res = [(entry)]
			if entry.thumb:
				res.append(MultiContentEntryPixmapAlphaBlend(pos=(0, 0), size=(150, 75), png=entry.thumb))
			else:
				res.append(MultiContentEntryPixmapAlphaBlend(pos=(0, 0), size=(150, 75), png=LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS)+"/Extensions/PornCenter/nopreview.png")))
			res.append(MultiContentEntryText(pos=(155, self.center_up), size=(WIDTH-270, 45), font=0, text=entry.name))
			list.append(res)
		self.setList(list)

##################################################

class PornCenterSub(Screen, ProtectedScreen):
	def __init__(self, session, plugin=None):
		Screen.__init__(self, session)
		if pinchecker.pin_entered == False:
			ProtectedScreen.__init__(self)
		
		self.session = session
		self.plugin = plugin
		self.list = []
		
		self["list"] = PornCenterList()
		
		self["actions"] = ActionMap(["InfobarActions", "MenuActions", "OkCancelActions"],
			{
				"ok": self.ok,
				"cancel": self.exit,
				"menu": self.config,
				"showMovies": self.showMore
			}, -1)
		
		self.onLayoutFinish.append(self.getEntries)

	def isProtected(self):
		return config.ParentalControl.setuppinactive.value
	
	def pinEntered(self, result):
		if result is None:
			self.close()
		elif not result:
			self.close()
		else:
			pinchecker.pinEntered()

	def ok(self):
		curr = self["list"].getCurrent()
		if curr:
			curr = curr[0]
			if curr.type == "Plugin":
				self.session.open(PornCenterMain, curr)
			elif curr.type == "Movie":
				url = curr.getVideoUrl()
				if url:
					if config.plugins.PornCenter.buffer.value:
						file = url
						while file.__contains__("/"):
							idx = file.index("/")
							file = file[idx+1:]
						self.file = "%s%s" % (config.plugins.PornCenter.bufferDevice.value, file)
						self.session.openWithCallback(self.bufferCallback, PornCenterBuffer, url, self.file)
					else:
						self.session.open(ChangedMoviePlayer, eServiceReference(4097, 0, url))
				else:
					self.session.open(MessageBox, _("Error while getting video url!"), MessageBox.TYPE_ERROR)

	def bufferCallback(self, callback):
		if callback is not None:
			ref = eServiceReference(4097, 0, self.file)
			self.session.openWithCallback(self.delete, ChangedMoviePlayer, ref)

	def delete(self, callback=None):
		if bufferThread.downloading: #still downloading?
			bufferThread.stop()
		if config.plugins.PornCenter.keepStored.value == "delete":
			remove(self.file)
		elif config.plugins.PornCenter.keepStored.value == "ask":
			self.session.openWithCallback(self.deleteCallback, MessageBox, _("Delete this movie?"))

	def deleteCallback(self, callback):
		if callback:
			remove(self.file)

	def exit(self):
		cache.finishCallback = None
		for x in self.list:
			del x
		self.close()

	def getEntries(self):
		if not self.plugin:
			self.gotEntries(getPlugins())
		else:
			cache.finishCallback = self.listChanged
			self.plugin.getEntries(self.gotEntries)

	def gotEntries(self, entries=None):
		if entries:
			for entry in entries:
				self.list.append(entry)
			self["list"].SetList(self.list)

	def listChanged(self):
		self["list"].SetList(self.list)

	def config(self):
		self.session.open(PornCenterConfig)

	def showMore(self):
		if self.plugin:
			if self.plugin.type == "Plugin":
				self.plugin.getMoreEntries()

##################################################

class PornCenterMain(PornCenterSub):
	if HEIGHT == 576:
		LISTHEIGHT = 450
	else:
		LISTHEIGHT = HEIGHT - 100
		if LISTHEIGHT > 600:
			LISTHEIGHT = 600
	skin = """
		<screen position="0,0" size="%d,%d" flags="wfNoBorder" backgroundColor="#000000" >
			<widget name="list" position="50,50" size="%d,%d" transparent="1" scrollbarMode="showOnDemand" />
		</screen>""" % (WIDTH, HEIGHT, WIDTH - 100, LISTHEIGHT)

	def __init__(self, *x):
		PornCenterSub.__init__(self, *x)

##################################################

def main_closed(callback=None):
	cache.session.nav.playService(cache.oldService)

def main(session, **kwargs):
	cache.session = session
	cache.oldService = session.nav.getCurrentlyPlayingServiceReference()
	session.nav.stopService()
	session.openWithCallback(main_closed, PornCenterMain)

def Plugins(**kwargs):
	return PluginDescriptor(name=config.plugins.PornCenter.name.value, description=config.plugins.PornCenter.description.value, where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], fnc=main, icon="plugin.png")
