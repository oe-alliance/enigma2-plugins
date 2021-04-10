# -*- coding: UTF-8 -*-
from Plugins.Plugin import PluginDescriptor
from Tools.BoundFunction import boundFunction
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List
from Components.AVSwitch import AVSwitch
from Components.config import config, Config, ConfigSelection, ConfigSubsection, ConfigText, getConfigListEntry, ConfigYesNo, ConfigIP, ConfigNumber, ConfigLocations
from Components.config import KEY_DELETE, KEY_BACKSPACE, KEY_LEFT, KEY_RIGHT, KEY_HOME, KEY_END, KEY_TOGGLEOW, KEY_ASCII, KEY_TIMEOUT
from Components.ConfigList import ConfigListScreen
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase

from Tools.Directories import pathExists, fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE, SCOPE_HDD, SCOPE_CURRENT_PLUGIN, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
from enigma import eTimer, quitMainloop, eListbox, ePoint, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, eListboxPythonMultiContent, eListbox, gFont, getDesktop, ePicLoad, eServiceCenter, iServiceInformation, eServiceReference, iSeekableService, iServiceInformation, iPlayableService, iPlayableServicePtr
from os import path as os_path, system as os_system, unlink, stat, mkdir, popen, makedirs, listdir, access, rename, remove, W_OK, R_OK, F_OK
from twisted.web import client
from twisted.internet import reactor
from time import time

from Screens.InfoBarGenerics import InfoBarShowHide, InfoBarSeek, InfoBarNotifications, InfoBarServiceNotifications

from ServiceXML import iWebTVStations

config.plugins.dreamMediathek = ConfigSubsection()
config.plugins.dreamMediathek.general = ConfigSubsection()
config.plugins.dreamMediathek.general.on_movie_stop = ConfigSelection(default="ask", choices=[
	("ask", _("Ask user")), ("quit", _("Return to movie list")), ("playnext", _("Play next video")), ("playagain", _("Play video again"))])
config.plugins.dreamMediathek.general.on_exit = ConfigSelection(default="ask", choices=[
	("ask", _("Ask user")), ("quit", _("Return to movie list"))])


class dreamMediathekPlayer(Screen, InfoBarNotifications):
	STATE_IDLE = 0
	STATE_PLAYING = 1
	STATE_PAUSED = 2
	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	skin = """<screen name="dreamMediathekPlayer" flags="wfNoBorder" position="0,380" size="720,160" title="dreamMediathekPlayer" backgroundColor="transparent">
		<ePixmap position="0,0" pixmap="skin_default/info-bg_mp.png" zPosition="-1" size="720,160" />
		<ePixmap position="29,40" pixmap="skin_default/screws_mp.png" size="665,104" alphatest="on" />
		<ePixmap position="48,70" pixmap="skin_default/icons/mp_buttons.png" size="108,13" alphatest="on" />
		<ePixmap pixmap="skin_default/icons/icon_event.png" position="207,78" size="15,10" alphatest="on" />
		<widget source="session.CurrentService" render="Label" position="230,73" size="360,40" font="Regular;20" backgroundColor="#263c59" shadowColor="#1d354c" shadowOffset="-1,-1" transparent="1">
			<convert type="ServiceName">Name</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="580,73" size="90,24" font="Regular;20" halign="right" backgroundColor="#4e5a74" transparent="1">
			<convert type="ServicePosition">Length</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="205,129" size="100,20" font="Regular;18" halign="center" valign="center" backgroundColor="#06224f" shadowColor="#1d354c" shadowOffset="-1,-1" transparent="1">
			<convert type="ServicePosition">Position</convert>
		</widget>
		<widget source="session.CurrentService" render="PositionGauge" position="300,133" size="270,10" zPosition="2" pointer="skin_default/position_pointer.png:540,0" transparent="1" foregroundColor="#20224f">
			<convert type="ServicePosition">Gauge</convert>
		</widget>
		<widget source="session.CurrentService" render="Label" position="576,129" size="100,20" font="Regular;18" halign="center" valign="center" backgroundColor="#06224f" shadowColor="#1d354c" shadowOffset="-1,-1" transparent="1">
			<convert type="ServicePosition">Remaining</convert>
		</widget>
		</screen>"""

	def __init__(self, session, service, lastservice, infoCallback=None, nextCallback=None, prevCallback=None):
		Screen.__init__(self, session)
		InfoBarNotifications.__init__(self)
		self.session = session
		self.service = service
		self.infoCallback = infoCallback
		self.nextCallback = nextCallback
		self.prevCallback = prevCallback
		self.screen_timeout = 5000
		self.nextservice = None

		print "evEOF=%d" % iPlayableService.evEOF
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evSeekableStatusChanged: self.__seekableStatusChanged,
				iPlayableService.evStart: self.__serviceStarted,
				iPlayableService.evEOF: self.__evEOF,
			})

		self["actions"] = ActionMap(["OkCancelActions", "InfobarSeekActions", "MediaPlayerActions", "MovieSelectionActions"],
		{
				"ok": self.ok,
				"cancel": self.leavePlayer,
				"stop": self.leavePlayer,
				"playpauseService": self.playpauseService,
				"seekFwd": self.playNextFile,
				"seekBack": self.playPrevFile,
				"showEventInfo": self.showVideoInfo,
			}, -2)

		self.lastservice = lastservice

		self.hidetimer = eTimer()
		self.hidetimer.timeout.get().append(self.ok)
		self.returning = False

		self.state = self.STATE_PLAYING
		self.lastseekstate = self.STATE_PLAYING

		self.onPlayStateChanged = []
		self.__seekableStatusChanged()

		self.play()
		self.onClose.append(self.__onClose)

	def __onClose(self):
		self.session.nav.stopService()

	def __evEOF(self):
		print "evEOF=%d" % iPlayableService.evEOF
		print "Event EOF"
		self.handleLeave(config.plugins.dreamMediathek.general.on_movie_stop.value)

	def __setHideTimer(self):
		self.hidetimer.start(self.screen_timeout)

	def showInfobar(self):
		self.show()
		if self.state == self.STATE_PLAYING:
			self.__setHideTimer()
		else:
			pass

	def hideInfobar(self):
		self.hide()
		self.hidetimer.stop()

	def ok(self):
		if self.shown:
			self.hideInfobar()
		else:
			self.showInfobar()

	def showVideoInfo(self):
		if self.shown:
			self.hideInfobar()
		if self.infoCallback is not None:
			self.infoCallback()

	def playNextFile(self):
		print "playNextFile"
		if self.nextCallback() is not None:
			nextservice, error = self.nextCallback()
			print "nextservice--->", nextservice
			if nextservice is None:
				self.handleLeave(config.plugins.dreamMediathek.general.on_movie_stop.value, error)
			else:
				self.playService(nextservice)
				self.showInfobar()

	def playPrevFile(self):
		print "playPrevFile"
		if self.prevCallback() is not None:
			prevservice, error = self.prevCallback()
			if prevservice is None:
				self.handleLeave(config.plugins.dreamMediathek.general.on_movie_stop.value, error)
			else:
				self.playService(prevservice)
				self.showInfobar()

	def playagain(self):
		print "playagain"
		if self.state != self.STATE_IDLE:
			self.stopCurrent()
		self.play()

	def playService(self, newservice):
		if self.state != self.STATE_IDLE:
			self.stopCurrent()
		self.service = newservice
		self.play()

	def play(self):
		if self.state == self.STATE_PAUSED:
			if self.shown:
				self.__setHideTimer()
		self.state = self.STATE_PLAYING
		self.session.nav.playService(self.service)
		if self.shown:
			self.__setHideTimer()

	def stopCurrent(self):
		print "stopCurrent"
		self.session.nav.stopService()
		self.state = self.STATE_IDLE

	def playpauseService(self):
		print "playpauseService"
		if self.state == self.STATE_PLAYING:
			self.pauseService()
		elif self.state == self.STATE_PAUSED:
			self.unPauseService()

	def pauseService(self):
		print "pauseService"
		if self.state == self.STATE_PLAYING:
			self.setSeekState(self.STATE_PAUSED)

	def unPauseService(self):
		print "unPauseService"
		if self.state == self.STATE_PAUSED:
			self.setSeekState(self.STATE_PLAYING)

	def getSeek(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return None

		seek = service.seek()

		if seek is None or not seek.isCurrentlySeekable():
			return None

		return seek

	def isSeekable(self):
		if self.getSeek() is None:
			return False
		return True

	def __seekableStatusChanged(self):
		print "seekable status changed!"
		if not self.isSeekable():
			self.setSeekState(self.STATE_PLAYING)
		else:
			print "seekable"

	def __serviceStarted(self):
		self.state = self.STATE_PLAYING
		self.__seekableStatusChanged()

	def setSeekState(self, wantstate):
		print "setSeekState"
		if wantstate == self.STATE_PAUSED:
			print "trying to switch to Pause- state:", self.STATE_PAUSED
		elif wantstate == self.STATE_PLAYING:
			print "trying to switch to playing- state:", self.STATE_PLAYING
		service = self.session.nav.getCurrentService()
		if service is None:
			print "No Service found"
			return False
		pauseable = service.pause()
		if pauseable is None:
			print "not pauseable."
			self.state = self.STATE_PLAYING

		if pauseable is not None:
			print "service is pausable"
			if wantstate == self.STATE_PAUSED:
				print "WANT TO PAUSE"
				pauseable.pause()
				self.state = self.STATE_PAUSED
				if not self.shown:
					self.hidetimer.stop()
					self.show()
			elif wantstate == self.STATE_PLAYING:
				print "WANT TO PLAY"
				pauseable.unpause()
				self.state = self.STATE_PLAYING
				if self.shown:
					self.__setHideTimer()

		for c in self.onPlayStateChanged:
			c(self.state)

		return True

	def handleLeave(self, how, error=False):
		self.is_closing = True
		if how == "ask":
			list = (
				(_("Yes"), "quit"),
				(_("No, but play video again"), "playagain"),
				(_("Yes, but play next video"), "playnext"),
				(_("Yes, but play previous video"), "playprev"),
			)
			if error is False:
				self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Stop playing this movie?"), list=list)
			else:
				self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("No playable video found! Stop playing this movie?"), list=list)
		else:
			self.leavePlayerConfirmed([True, how])

	def leavePlayer(self):
		self.handleLeave(config.plugins.dreamMediathek.general.on_movie_stop.value)

	def leavePlayerConfirmed(self, answer):
		answer = answer and answer[1]
		if answer == "quit":
			self.close()
		elif answer == "playnext":
			self.playNextFile()
		elif answer == "playprev":
			self.playPrevFile()
		elif answer == "playagain":
			self.playagain()

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing:
			return
		self.handleLeave(config.usage.on_movie_eof.value)
