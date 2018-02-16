# -*- coding: ISO-8859-1 -*-
#===============================================================================
# VLC Player Plugin by A. Latsch 2007
#                   modified by Volker Christian 2008
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================


from time import time
from . import _
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
from Screens.InfoBarGenerics import InfoBarNotifications, InfoBarAudioSelection, InfoBarSubtitleSupport
from Components.Sources.Source import Source
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ActionMap import ActionMap
from Components.config import config

from Screens.ChoiceBox import ChoiceBox
from Components.Button import Button
from os import system

def isValidServiceId(id):
	testSRef = eServiceReference(id, 0, "Just a TestReference")
	info = eServiceCenter.getInstance().info(testSRef)
	return info is not None

ENIGMA_SERVICEGS_ID = 0x1001
ENIGMA_SERVICETS_ID = 0x1002

ENIGMA_SERVICE_ID = 0

print "[VLC] Checking for buildin servicets ... ",
if isValidServiceId(ENIGMA_SERVICETS_ID):
	print "yes"
	ENIGMA_SERVICE_ID = ENIGMA_SERVICETS_ID
	STOP_BEFORE_UNPAUSE = False
else:
	print "no"
	print "[VLC] Checking for existing and usable servicets.so ... ",
	try:
		import servicets
	except Exception, e:
		print e
		print "[VLC] Checking for usable gstreamer service ... ",
		if isValidServiceId(ENIGMA_SERVICEGS_ID):
			print "yes"
			ENIGMA_SERVICE_ID = ENIGMA_SERVICEGS_ID
			STOP_BEFORE_UNPAUSE = True
		else:
			print "no"
			print "[VLC] No valid VLC-Service found - VLC-streaming not supported"
	else:
		print "yes"
		ENIGMA_SERVICE_ID = ENIGMA_SERVICETS_ID
		STOP_BEFORE_UNPAUSE = False

DEFAULT_VIDEO_PID = 0x44
DEFAULT_AUDIO_PID = 0x45


def isDvdUrl(url):
	return url.startswith("dvd://") or url.startswith("dvdsimple://")


def splitDvdUrl(url):
	pos = url.rfind("@", len(url)-8)
	if pos > 0:
		track = url[pos+1:]
		url = url[0:pos]
		if track.find(":") >= 0:
			track, chapter = track.split(":")
		else:
			chapter = None
	else:
		track, chapter = (None, None)
	return (url, track, chapter)


class VlcService(Source, iPlayableServicePtr, iSeekableService):
	refreshInterval = 3000

	class Info(iServiceInformation):
		def __init__(self, name=""):
			self.name = name

		def getName(self):
			return self.name

		def getInfoObject(self, *args, **kwargs):
			return { }

		def getInfo(self, what):
			return -1

		def getInfoString(self, *args, **kwargs):
			return self.name

		def isPlayable(self):
			return True

		def getEvent(self, what):
			return None

	def __init__(self, player):
		Source.__init__(self)
		self.__info = VlcService.Info()
		self.server = None
		self.service = self
		self.player = player
		self.lastrefresh = time()
		self.stats = None

	def setName(self, name):
		i = name.rfind("/")
		if i >= 0:
			name = name[i+1:]
		i = name.rfind("\\")
		if i >= 0:
			name = name[i+1:]
		self.__info.name = name
		self.setChanged()

	def setChanged(self):
		self.changed( (self.CHANGED_SPECIFIC, iPlayableService.evStart) )

	def setServer(self, server):
		self.server = server

	def __onRefresh(self):
		if self.server is None:
			self.stats = None
			return
		print "[VLC] refresh"
		try:
			self.stats = self.server.status()
			self.lastrefresh = time()
			if self.stats and self.stats.has_key("time"):
				print "Time: ", self.stats["time"]
		except Exception, e:
			print e

	def refresh(self):
		self.__onRefresh()

	def info(self):
		return self.__info

	# iSeekableService
	def seek(self):
		return self

	def getPlayPosition(self):
		if self.stats and self.stats.has_key("time"):
			pos = float(self.stats["time"])
			if self.player.state == VlcPlayer.STATE_PLAYING:
				pos += time() - self.lastrefresh
			return (False, int(pos*90000))
		else:
			return (True, 0)

	def getLength(self):
		if self.stats and self.stats.has_key("length"):
			return (False, int(self.stats["length"])*90000)
		else:
			return (True, 0)

	# iPlayableService
	def cueSheet(self): return None
	def pause(self): return self.player
	def audioTracks(self):
		return self.player.audioTracks()

	def audioChannel(self): return None
	def subServices(self): return None
	def frontendInfo(self): return None
	def timeshift(self): return None
	def subtitle(self): return None
#		return self.player.subtitle()

	def audioDelay(self): return None
	def rdsDecoder(self): return None
	def stream(self): return None
	def start(self):
		self.player.play()
	def stop(self):
		self.player.stop()


class VlcPlayerSummary(Screen):
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


class VlcPlayer(Screen, InfoBarNotifications, InfoBarAudioSelection, InfoBarSubtitleSupport):
	screen_timeout = 5000

	STATE_IDLE = 0
	STATE_PLAYING = 1
	STATE_PAUSED = 2

	def __init__(self, session, server, currentList):
		Screen.__init__(self, session)
		InfoBarNotifications.__init__(self)
		InfoBarAudioSelection.__init__(self)
		InfoBarSubtitleSupport.__init__(self)
		self.server = server
		self.seek_time = 600
		self.currentList = currentList
		self.skinName = "MoviePlayer"
		self.state = self.STATE_IDLE
		self.oldservice = self.session.screen["CurrentService"]
		self.oldNavService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()
		self.vlcservice = VlcService(self)
		self.session.screen["CurrentService"] = self.vlcservice
		self.hidetimer = eTimer()
		self.hidetimer.timeout.get().append(self.ok)
		self.onClose.append(self.__onClose)

		class VlcPlayerActionMap(ActionMap):
			def __init__(self, player, contexts = [ ], actions = { }, prio=0):
				ActionMap.__init__(self, contexts, actions, prio)
				self.player = player

			def action(self, contexts, action):
				if action[:5] == "seek:":
					time = int(action[5:])
					self.player.seekRelative(time)
					return 1
				elif action[:8] == "seekdef:":
					key = int(action[8:])
					time = [-config.seek.selfdefined_13.value, False, config.seek.selfdefined_13.value,
							-config.seek.selfdefined_46.value, False, config.seek.selfdefined_46.value,
							-config.seek.selfdefined_79.value, False, config.seek.selfdefined_79.value][key-1]
					self.player.seekRelative(time)
					return 1
				else:
					return ActionMap.action(self, contexts, action)

		self["actions"] = VlcPlayerActionMap(self, ["OkCancelActions", "TvRadioActions", "InfobarSeekActions", "MediaPlayerActions", "ChannelSelectEPGActions"],
		{
				"ok": self.ok,
				"cancel": self.stop,
				"keyTV": self.stop,
				"stop": self.stop,
				"pauseService": self.pause,
				"playpauseService": self.pause,
				"unPauseService": self.play,
				"play": self.play,
				"seekFwd": self.seekFwd,
				"seekBack": self.seekBack,
				"seekFwdDown": self.seekFwd,
				"seekBackDown": self.seekBack,
				"seekFwdManual": self.seekManual,
				"seekBackManual": self.seekManual,
				"next": self.playNextFile,
				"previous": self.playPrevFile,
				"menu": self.openVCS,
				"showEPGList": self.choiceJumping,
				"subtitles": self.subtitleSelection
			}, -2)

		print "[VLC] evEOF=%d" % iPlayableService.evEOF
		self.__event_tracker = ServiceEventTracker(screen = self, eventmap =
			{
				iPlayableService.evEOF: self.__evEOF,
				iPlayableService.evSOF: self.__evSOF
			})

	def createSummary(self):
		print "[VLC] createSummary"
		return VlcPlayerSummary

	def __onClose(self):
		self.session.screen["CurrentService"] = self.oldservice
		self.session.nav.playService(self.oldNavService)

	def choiceJumping(self):
		try:
			self.session.openWithCallback(self.choicesCallback, ChoiceBox, title=_("Choice of minutes to jump"), list=[(_("1 minute"), "1"), (_("3 minutes"), "3"),(_("5 minutes"), "5"), (_("10 minutes"), "10"),(_("15 minutes"), "15"), (_("20 minutes"), "20"),(_("30 minutes"), "30"),])
		except:
			pass

	def choicesCallback(self, answer):
		if answer is None:
			return
		if answer[1] == "1":
			self.seek_time = 60
		elif answer[1] == "3":
			self.seek_time = 180
		elif answer[1] == "5":
			self.seek_time = 300
		elif answer[1] == "10":
			self.seek_time = 600
		elif answer[1] == "15":
			self.seek_time = 900
		elif answer[1] == "20":
			self.seek_time = 1200
		elif answer[1] == "30":
			self.seek_time = 1800
		else:
			pass


	def openVCS(self):
		try:
			from Plugins.Extensions.VCS.VCS import VcsChoiseList
			VcsChoiseList(self.session)
		except:
			pass

	def __evEOF(self):
		print "[VLC] Event EOF"
		self.stop()

	def __evSOF(self):
		print "[VLC] Event SOF"
		self.vlcservice.refresh()

	def playfile(self, path, name):
		if self.state != self.STATE_IDLE:
			self.stopCurrent()
		self.filename = path
		self.vlcservice.setName(name)
		self.name = name
		self.play()

	def play(self):
		if self.state == self.STATE_PLAYING:
			return
		if self.state == self.STATE_PAUSED:
			self.unpause()
			return
		print "[VLC] setupStream: " + self.filename
		if ENIGMA_SERVICE_ID == 0:
			self.hide()
			self.session.open(
					MessageBox, _("No valid Enigma-Service to play a VLC-Stream\nCheck your installation and try again!"), MessageBox.TYPE_ERROR
			)
			self.close()
			return
		try:
			url = self.server.playFile(self.filename, DEFAULT_VIDEO_PID, DEFAULT_AUDIO_PID)
			print "[VLC] url: " + url
		except Exception, e:
			self.hide()
			self.session.open(
					MessageBox, (_("Error with VLC server:\n%s") % e), MessageBox.TYPE_ERROR
			)
			self.close()
			return
		if url is not None:
			self.url = url
			if self.server.getUseCachedir():
				self.session.openWithCallback(self.actions, ChoiceBox, title=_("Select method?"), list=[(_("Direct play"), "dirplay"), (_("Save as .ts and play"), "cache"),])
			else:
				self.actions((_("Direct play"), "dirplay"))

	def actions(self, answer):
		if answer is None:
			self.stop()
			return
		if answer[1] == "dirplay":
			url = self.url
			sref = eServiceReference(ENIGMA_SERVICE_ID, 0, url)
			print "sref valid=", sref.valid()
			sref.setData(0, DEFAULT_VIDEO_PID)
			sref.setData(1, DEFAULT_AUDIO_PID)
			self.session.nav.playService(sref)
			self.state = self.STATE_PLAYING
			if self.shown:
				self.__setHideTimer()
			self.vlcservice.setServer(self.server)

		elif answer[1] == "cache":
			svfile = self.server.getCachedir() + "/" + self.name + ".ts"
			pcip = self.server.getHost() + "\n"
			pcport = str(self.server.getHttpPort()) + "\n"
			f = open('/etc/copylast.txt', 'w')
			text = svfile + "\n"
			f.write(text)
			f.write(pcip)
			f.write(pcport)
			f.close()
			url = self.url
			print " svfile  =", svfile
			print " url  =", url
			cmd = "rm " + svfile
			system(cmd)
			cmd1 = "wget -c '" + url + "' -O '" + svfile + "' &"
			system(cmd1)
			url = self.url
			sref = eServiceReference(ENIGMA_SERVICE_ID, 0, url)
			print "sref valid=", sref.valid()
			sref.setData(0, DEFAULT_VIDEO_PID)
			sref.setData(1, DEFAULT_AUDIO_PID)
			self.session.nav.playService(sref)
			self.state = self.STATE_PLAYING
			if self.shown:
				self.__setHideTimer()
			self.vlcservice.setServer(self.server)

	def pause(self):
		print "[VLC] pause"
		if self.state == self.STATE_PLAYING:
			self.session.nav.pause(True)
			self.server.pause()
			self.state = self.STATE_PAUSED
			self.vlcservice.refresh()
			if not self.shown:
				self.hidetimer.stop()
				self.show()
		elif self.state == self.STATE_PAUSED:
			self.unpause()

	def subtitleSelection(self):
		service = self.session.nav.getCurrentService()
		subtitle = service and service.subtitle()
		if subtitle is not None:
			from Screens.AudioSelection import SubtitleSelection
			try:
				self.session.open(SubtitleSelection, self)
			except:
				pass

	def unpause(self):
		print "[VLC] unpause"
		try:
			self.server.seek("-2")
			self.server.unpause()
		except Exception, e:
			self.session.open(
				MessageBox, (_("Error with VLC server:\n%s") % e), MessageBox.TYPE_ERROR
			)
			self.stop()
			return
		if STOP_BEFORE_UNPAUSE:
			self.session.nav.stopService()
			sref = self.session.nav.getCurrentlyPlayingServiceReference()
			sref.setData(0, DEFAULT_VIDEO_PID)
			sref.setData(1, DEFAULT_AUDIO_PID)
			self.session.nav.playService(sref)
		else:
			self.session.nav.pause(False)
		self.state = self.STATE_PLAYING
		self.vlcservice.refresh()
		if self.shown:
			self.__setHideTimer()

	def stopCurrent(self):
		print "[VLC] stopCurrent"
		self.session.nav.stopService()
		if self.state == self.STATE_IDLE:
			self.close()
			return
		try:
			self.server.stop()
			self.server.deleteCurrentTree()
		except Exception, e:
			#self.session.open(
			#	MessageBox, _("Error with VLC server:\n%s" % e), MessageBox.TYPE_ERROR
			#)
			return
		self.state = self.STATE_IDLE
		self.vlcservice.setServer(None)
		self.vlcservice.refresh()

	def stop(self):
		print "[VLC] stop"
		self.stopCurrent()
		self.close()

	def __setHideTimer(self):
		self.hidetimer.start(self.screen_timeout)

	def showInfobar(self):
		self.vlcservice.refresh()
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

	def playNextFile(self):
		print "[VLC] playNextFile"
		if isDvdUrl(self.filename):
			url, track, chapter = splitDvdUrl(self.filename)
			if track is None:
				track = 1
			else:
				track = int(track)
			if chapter is None:
				chapter = 2
			else:
				chapter = int(chapter) + 1
			url = "%s@%d:%d" % (url, track, chapter)
			self.playfile(url, "DVD")
			self.showInfobar()
		else:
			if self.currentList != None:
				media, name = self.currentList.getNextFile()
				if media is None:
					self.session.open(
							MessageBox, _("No more files in this directory"), MessageBox.TYPE_INFO
					)
					self.close()
				else:
					self.playfile(media, name)
					self.showInfobar()

	def playPrevFile(self):
		print "[VLC] playPrevFile"
		if isDvdUrl(self.filename):
			url, track, chapter = splitDvdUrl(self.filename)
			if track is None:
				track = 1
			else:
				track = int(track)
			if chapter is not None and int(chapter) > 1:
				chapter = int(chapter) - 1
			else:
				chapter = 1
			url = "%s@%d:%d" % (url, track, chapter)
			self.playfile(url, "DVD")
			self.showInfobar()
		else:
			if self.currentList != None:
				media, name = self.currentList.getPrevFile()
				if media is None:
					self.session.open(
							MessageBox, _("No previous file in this directory"), MessageBox.TYPE_INFO
					)
					self.close()
				else:
					self.playfile(media, name)
					self.showInfobar()

	def audioTracks(self):
		return self.session.nav.getCurrentService() and self.session.nav.getCurrentService().audioTracks();

	def subtitle(self):
		return self.session.nav.getCurrentService() and self.session.nav.getCurrentService().subtitle();

	def seekRelative(self, delta):
		"""delta is seconds as integer number
		positive=forwards, negative=backwards"""
		if self.state != self.STATE_IDLE:
			if (delta >= 0):
				self.server.seek("+" + str(delta))
			else:
				self.server.seek(str(delta))
		self.showInfobar()

	def seekFwd(self):
		if isDvdUrl(self.filename):
			url, track, chapter = splitDvdUrl(self.filename)
			if track is None:
				track = 2
			else:
				track = int(track) + 1
			url = "%s@%d" % (url, track)
			self.playfile(url, "DVD")
			self.showInfobar()
		else:
			self.seekRelative(self.seek_time)

	def seekBack(self):
		if isDvdUrl(self.filename):
			url, track, chapter = splitDvdUrl(self.filename)
			if track is not None and int(track) > 2:
				track = int(track) - 1
				url = "%s@%d" % (url, track)
			else:
				track = 1
			self.playfile(url, "DVD")
			self.showInfobar()
		else:
			self.seekRelative(-self.seek_time)

	def seekToMinute(self, minutes):
		self.server.seek(str(int(minutes)*60))
		self.showInfobar()

	def seekManual(self):
		self.session.openWithCallback(self.seekToMinute, MinuteInput)
