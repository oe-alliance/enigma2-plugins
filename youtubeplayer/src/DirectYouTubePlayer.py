# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
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

from .YouTubeContextMenu import YouTubeEntryContextMenu, YouTubeEntryContextMenuList


class DirectYouTubePlayerSummary(Screen):
	skin = """
	<screen name="InfoBarMoviePlayerSummary" position="0,0" size="132,64">
		<widget source="session.CurrentService" render="Label" position="6,0" size="120,25" font="Regular;14" halign="center" valign="center" >
			<convert type="ServiceName">Name</convert>
		</widget>
		<widget source="session.CurrentService" render="Progress" position="16,27" size="100,5" borderWidth="1">
			<convert type="ServicePosition">Position</convert>
		</widget>
		<widget source="global.CurrentTime" render="Label" position="6,32" size="120,32" font="Regular;32" halign="center" valign="center">
			<convert type="ClockToText">Format:%H:%M</convert>
		</widget>
		<widget source="session.RecordState" render="FixedLabel" text=" " position="6,32" zPosition="1" size="120,32">
			<convert type="ConfigEntryTest">config.usage.blinking_display_clock_during_recording,True,CheckSourceBoolean</convert>
			<convert type="ConditionalShowHide">Blink</convert>
		</widget>
	</screen>"""

	def __init__(self, session, parent):
		Screen.__init__(self, session)
		self.skinName = "InfoBarMoviePlayerSummary"


class DirectYouTubePlayer(Screen, InfoBarNotifications):
	STATE_IDLE = 0
	STATE_PLAYING = 1
	STATE_PAUSED = 2
	ENABLE_RESUME_SUPPORT = True
	ALLOW_SUSPEND = True

	def __init__(self, session, mrl, title, currentList, contextMenuEntries, infoCallback, name):
		Screen.__init__(self, session)
		InfoBarNotifications.__init__(self)
		self.contextMenuEntries = contextMenuEntries
		self.infoCallback = infoCallback
		self.name = name
		self.skinName = "MoviePlayer"
		self.session = session
		self.service = eServiceReference(4097, 0, mrl)
		self.service.setName(title)
		self.currentList = currentList
		self.infoCallback = infoCallback
		self.screen_timeout = 5000

		class DirectYouTubePlayerActionMap(ActionMap):
			def __init__(self, player, contexts=[], actions={}, prio=0):
				ActionMap.__init__(self, contexts, actions, prio)
				self.player = player

			def action(self, contexts, action):
				if action[:5] == "seek:":
					time = int(action[5:])
					self.player.seekRelative(time * 90000)
					return 1
				elif action[:8] == "seekdef:":
					key = int(action[8:])
					time = [-config.seek.selfdefined_13.value, False, config.seek.selfdefined_13.value,
							-config.seek.selfdefined_46.value, False, config.seek.selfdefined_46.value,
							-config.seek.selfdefined_79.value, False, config.seek.selfdefined_79.value][key - 1]
					self.player.seekRelative(time * 90000)
					return 1
				else:
					return ActionMap.action(self, contexts, action)

		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evSeekableStatusChanged: self.__seekableStatusChanged,
				iPlayableService.evStart: self.__serviceStarted,
				iPlayableService.evEOF: self.__evEOF
			})

		self["actions"] = DirectYouTubePlayerActionMap(self, ["OkCancelActions", "TvRadioActions", "InfobarSeekActions", "MediaPlayerActions", "YouTubePlayerScreenActions"],
		{
				"ok": self.ok,
				"cancel": self.close,
				"keyTV": self.close,
				"pauseService": self.playpauseService,
				"unPauseService": self.playpauseService,
				"play": self.play,
#				"seekFwd": self.seekFwd,
#				"seekBack": self.seekBack,
#				"seekFwdDown": self.seekFwd,
#				"seekBackDown": self.seekBack,
#				"seekFwdManual": self.seekManual,
#				"seekBackManual": self.seekManual,
				"next": self.playNextFile,
				"previous": self.playPrevFile,
				"menu": self.openContextMenu,
				"info": self.showVideoInfo,
			}, -2)

		self.oldservice = self.session.screen["CurrentService"]
		self.oldNavService = session.nav.getCurrentlyPlayingServiceReference()

		self.hidetimer = eTimer()
		self.hidetimer.timeout.get().append(self.ok)
		self.returning = False

		self.state = self.STATE_PLAYING
		self.lastseekstate = self.STATE_PLAYING

		self.onPlayStateChanged = []
		self.__seekableStatusChanged()

		self.onClose.append(self.__onClose)

		self.play()

	def createSummary(self):
		print("[YTB] createSummary")
		return DirectYouTubePlayerSummary

	def __onClose(self):
		self.session.nav.stopService()
		self.session.screen["CurrentService"] = self.oldservice
		self.session.nav.playService(self.oldNavService)

	def __evEOF(self):
		print("evEOF=%d" % iPlayableService.evEOF)
		print("Event EOF")
		self.close()

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

	def playService(self, mrl, name):
#		if self.state != self.STATE_IDLE:
#			self.stopCurrent()
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

#	def stopCurrent(self):
#		print "stopCurrent"
#		self.session.nav.stopService()
#		self.state = self.STATE_IDLE

	def playpauseService(self):
		print("playpauseService")
		if self.state == self.STATE_PLAYING:
			self.pauseService()
		elif self.state == self.STATE_PAUSED:
			self.unPauseService()

	def pauseService(self):
		print("pauseService")
		if self.state == self.STATE_PLAYING:
			self.setSeekState(self.STATE_PAUSED)

	def unPauseService(self):
		print("unPauseService")
		if self.state == self.STATE_PAUSED:
			self.setSeekState(self.STATE_PLAYING)

	def playNextFile(self):
		print("[YTB] playNextFile")
		if self.currentList is not None:
			media, name = self.currentList.getNextFile()
			if media is None:
				self.session.open(
						MessageBox, _("No more files in this directory"), MessageBox.TYPE_INFO
				)
				self.close()
			else:
				self.playService(media, name)
				self.showInfobar()

	def playPrevFile(self):
		print("[YTB] playPrevFile")
		if self.currentList is not None:
			media, name = self.currentList.getPrevFile()
			if media is None:
				self.session.open(
						MessageBox, _("No previous file in this directory"), MessageBox.TYPE_INFO
				)
				self.close()
			else:
				self.playService(media, name)
				self.showInfobar()

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
		print("seekable status changed!")
		if not self.isSeekable():
			self.setSeekState(self.STATE_PLAYING)
		else:
			print("seekable")

	def __serviceStarted(self):
		self.state = self.STATE_PLAYING
		self.__seekableStatusChanged()

	def setSeekState(self, wantstate):
		print("setSeekState")
		if wantstate == self.STATE_PAUSED:
			print("trying to switch to Pause- state:", self.STATE_PAUSED)
		elif wantstate == self.STATE_PLAYING:
			print("trying to switch to playing- state:", self.STATE_PLAYING)
		service = self.session.nav.getCurrentService()
		if service is None:
			print("No Service found")
			return False
		pauseable = service.pause()
		if pauseable is None:
			print("not pauseable.")
			self.state = self.STATE_PLAYING

		if pauseable is not None:
			print("service is pausable")
			if wantstate == self.STATE_PAUSED:
				print("WANT TO PAUSE")
				pauseable.pause()
				self.state = self.STATE_PAUSED
				if not self.shown:
					self.hidetimer.stop()
					self.show()
			elif wantstate == self.STATE_PLAYING:
				print("WANT TO PLAY")
				pauseable.unpause()
				self.state = self.STATE_PLAYING
				if self.shown:
					self.__setHideTimer()

		for c in self.onPlayStateChanged:
			c(self.state)

		return True

	def seekRelative(self, pts):
		seekable = self.getSeek()
		if seekable is None:
			return
#		prevstate = self.seekstate

#		if self.seekstate == self.STATE_EOF:
#			if prevstate == self.STATE_PAUSE:
#				self.setSeekState(self.STATE_PAUSE)
#			else:
#				self.setSeekState(self.STATE_PLAY)
		seekable.seekRelative(pts < 0 and -1 or 1, abs(pts))
		if abs(pts) > 100 and config.usage.show_infobar_on_skip.value:
			self.showInfobar()

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing:
			return
		self.close()

	def showVideoInfo(self):
		if self.shown:
			self.hideInfobar()
		self.infoCallback()

	def openContextMenu(self):
		if self.shown:
			self.hideInfobar()
		contextMenuList = YouTubeEntryContextMenuList()
		for entry in self.contextMenuEntries:
			contextMenuList.appendEntry(entry)
		self.session.openWithCallback(self.menuActionCoosen, YouTubeEntryContextMenu, contextMenuList, self.name)

	def menuActionCoosen(self, cookie):
		if cookie is not None:
			if cookie[1]:
				self.close()
			cookie[0]()
