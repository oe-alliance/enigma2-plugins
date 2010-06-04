# -*- coding: iso-8859-1 -*-
from time import time

from enigma import iPlayableServicePtr
from enigma import iPlayableService
from enigma import iServiceInformation
from enigma import iSeekableService
from enigma import eServiceReference
from enigma import eServiceCenter
from enigma import eTimer
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.MinuteInput import MinuteInput
from Screens.InfoBarGenerics import InfoBarNotifications, InfoBarAudioSelection
from Screens.ChoiceBox import ChoiceBox
from Components.Sources.Source import Source
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ActionMap import ActionMap
from Components.config import config


class DirectYouTubePlayer(Screen, InfoBarNotifications):
	STATE_IDLE = 0
	STATE_PLAYING = 1
	STATE_PAUSED = 2
	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, mrl, title, currentList, infoCallback = None):
		Screen.__init__(self, session)
		InfoBarNotifications.__init__(self)
		self.skinName = "MoviePlayer"
		self.session = session
		self.service = eServiceReference(4097, 0, mrl)
		self.service.setName(title)
		self.currentList = currentList
		self.infoCallback = infoCallback
		self.screen_timeout = 5000

		print "evEOF=%d" % iPlayableService.evEOF
		self.__event_tracker = ServiceEventTracker(screen = self, eventmap =
			{
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

		self.oldservice = self.session.screen["CurrentService"]
		self.oldNavService = session.nav.getCurrentlyPlayingServiceReference()

		self.hidetimer = eTimer()
		self.hidetimer.timeout.get().append(self.ok)
		self.returning = False

		self.state = self.STATE_PLAYING
		self.lastseekstate = self.STATE_PLAYING

		self.onPlayStateChanged = [ ]
		self.__seekableStatusChanged()

		self.play()
		self.onClose.append(self.__onClose)

	def __onClose(self):
		self.session.nav.stopService()
		self.session.screen["CurrentService"] = self.oldservice
		self.session.nav.playService(self.oldNavService)

	def __evEOF(self):
		print "evEOF=%d" % iPlayableService.evEOF
		print "Event EOF"
		self.handleLeave(config.plugins.mytube.general.on_movie_stop.value)

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
		mrl, name = self.currentList.getNextFile()
		if mrl is None:
			self.handleLeave(config.plugins.mytube.general.on_movie_stop.value, True)
		else:
			self.playService(mrl, name)
			self.showInfobar()

	def playPrevFile(self):
		print "playPrevFile"
		mrl, name = self.currentList.getPrevFile()
		if mrl is None:
			self.handleLeave(config.plugins.mytube.general.on_movie_stop.value, True)
		else:
			self.playService(mrl, name)
			self.showInfobar()

	def playagain(self):
		print "playagain"
		if self.state != self.STATE_IDLE:
			self.stopCurrent()
		self.play()

	def playService(self, mrl, name):
		if self.state != self.STATE_IDLE:
			self.stopCurrent()
		self.service = eServiceReference(4097, 0, mrl)
		self.service.setName(name)
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
			print "trying to switch to Pause- state:",self.STATE_PAUSED
		elif wantstate == self.STATE_PLAYING:
			print "trying to switch to playing- state:",self.STATE_PLAYING
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

	def handleLeave(self, how, error = False):
		self.is_closing = True
		if how == "ask":
			list = (
				(_("Yes"), "quit"),
				(_("No, but play video again"), "playagain"),
				(_("Yes, but play next video"), "playnext"),
				(_("Yes, but play previous video"), "playprev"),
			)
			if error is False:
				self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Stop playing this movie?"), list = list)
			else:
				self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("No playable video found! Stop playing this movie?"), list = list)
		else:
			self.leavePlayerConfirmed([True, how])

	def leavePlayer(self):
		self.handleLeave(config.plugins.mytube.general.on_movie_stop.value)

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
		if not playing :
			return
		self.handleLeave(config.usage.on_movie_eof.value)