# -*- coding: ISO-8859-1 -*-
#===============================================================================
# VLC Player Plugin by A. Lätsch 2007
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

from enigma import iPlayableServicePtr
from time import time
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.config import config
from enigma import eServiceReference
from Components.Sources.Source import Source
from Components.ServiceEventTracker import ServiceEventTracker
from enigma import iPlayableService
from enigma import eTimer
from Components.ActionMap import ActionMap
from VlcControlTelnet import VlcControlTelnet
from VlcControlHttp import VlcControlHttp


class VlcService(Source, iPlayableServicePtr):
	refreshInterval = 3000
	
	class Info:
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

	def __init__(self, player):
		Source.__init__(self)
		self.__info = VlcService.Info()
		self.vlccontrol = None
		self.service = self
		self.player = player
		self.lastrefresh = time()
		self.stats = None
		self.refreshTimer = eTimer()
		self.refreshTimer.timeout.get().append(self.__onRefresh)
		self.refreshTimer.start(self.refreshInterval)
	
	def setFilename(self, filename):
		i = filename.rfind("/")
		if i >= 0:
			filename = filename[i+1:]
		i = filename.rfind("\\")
		if i >= 0:
			filename = filename[i+1:]
		self.__info.name = filename
		self.changed( (self.CHANGED_SPECIFIC, iPlayableService.evStart) )
	
	def setControl(self, control):
		self.vlccontrol = control
		
	def __onRefresh(self):
		if self.vlccontrol is None: 
			self.stats = None
			return
		print "[VLC] refresh"
		try:
			self.stats = self.vlccontrol.status()
			self.lastrefresh = time()
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
	def audioTracks(self): return None
	def audioChannel(self): return None
	def subServices(self): return None
	def frontendInfo(self): return None
	def timeshift(self): return None
	def subtitle(self): return None
	def audioDelay(self): return None
	def rdsDecoder(self): return None
	def stream(self): return None
	def start(self):
		self.player.play()
	def stop(self):
		self.player.stop()

class VlcPlayer(Screen):
	screen_timeout = 5000
	
	STATE_IDLE = 0
	STATE_PLAYING = 1
	STATE_PAUSED = 2
	
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "MoviePlayer"
		self.state = self.STATE_IDLE
		self.url = None
		self.vlcservice = VlcService(self)
		self["CurrentService"] = self.vlcservice
		self.hidetimer = eTimer()
		self.hidetimer.timeout.get().append(self.ok)

		class InfoBarSeekActionMap(ActionMap):
			def __init__(self, player, contexts = [ ], actions = { }, prio=0):
				ActionMap.__init__(self, contexts, actions, prio)
				self.player = player
				
			def action(self, contexts, action):
				if action[:5] == "seek:":
					time = int(action[5:])
					self.player.seekRelative(time)
					return 1
				else:
					return ActionMap.action(self, contexts, action)
		
		self["actions"] = InfoBarSeekActionMap(self, ["OkCancelActions", "TvRadioActions", "InfobarSeekActions"],
		{
				"ok": self.ok,
				"cancel": self.cancel,
				"keyTV": self.stop,
				"pauseService": self.pause,
				"unPauseService": self.play,
				"seekFwd": self.seekFwd,
				"seekBack": self.seekBack,
				"seekFwdDown": self.seekFwd,
				"seekBackDown": self.seekBack
			}, -2)

		print "evEOF=%d" % iPlayableService.evEOF
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evEOF: self.__evEOF,
#				iPlayableService.evSOF: self.__evSOF,
			})
	
	def __evEOF(self):
		print "[VLC] Event EOF"
		self.stop()
	
	def playfile(self, servernum, path):
		if self.state != self.STATE_IDLE:
			self.stop()

		cfg = config.plugins.vlcplayer.servers[servernum]
		if cfg.method.value == "telnet":
			self.vlccontrol = VlcControlTelnet(servernum)
			streamName = VlcControlTelnet.defaultStreamName
		else:
			self.vlccontrol = VlcControlHttp(servernum)
			streamName = VlcControlHttp.defaultStreamName
		self.vlcservice.setFilename(path)
		
		self.url = "http://%s:%d/%s.ts" % (cfg.host.value, cfg.httpport.value, streamName)
		self.filename = path
		if config.plugins.vlcplayer.soverlay.value:
			soverlay=",soverlay"
		else:
			soverlay=""
		self.output = "#transcode{vcodec=%s,vb=%d,width=%s,height=%s,fps=%s,scale=1,acodec=%s,ab=%d,channels=%d,samplerate=%s%s}:std{access=http,mux=ts,dst=/%s.ts}" % (
			config.plugins.vlcplayer.vcodec.value, 
			config.plugins.vlcplayer.vb.value, 
			config.plugins.vlcplayer.width.value, 
			config.plugins.vlcplayer.height.value, 
			config.plugins.vlcplayer.fps.value, 
			config.plugins.vlcplayer.acodec.value, 
			config.plugins.vlcplayer.ab.value, 
			config.plugins.vlcplayer.channels.value,
			config.plugins.vlcplayer.samplerate.value,
			soverlay,
			streamName
		)
		self.play()

	def play(self):
		if self.state == self.STATE_PAUSED:
			self.unpause()
			return
		elif self.state == self.STATE_IDLE and self.url is not None:
			print "[VLC] setupStream: " + self.filename + " " + self.output
			try:
				self.vlccontrol.playfile(self.filename, self.output)
			except Exception, e:
				self.session.open(
					MessageBox, _("Error with VLC server:\n%s" % e), MessageBox.TYPE_ERROR)
				return
			self.session.nav.playService(eServiceReference(0x1001, 0, self.url))
			self.state = self.STATE_PLAYING
			if self.shown:
				self.__setHideTimer()
		self.vlcservice.setControl(self.vlccontrol)
		self.vlcservice.refresh()

	def pause(self):
		print "[VLC] pause"
		if self.state == self.STATE_PLAYING:
			self.session.nav.pause(True)
			self.vlccontrol.pause()
			self.state = self.STATE_PAUSED
			self.vlcservice.refresh()
			if not self.shown:
				self.hidetimer.stop()
				self.show()
		elif self.state == self.STATE_PAUSED:
			self.unpause()

	def unpause(self):
		print "[VLC] unpause"
		try:
			self.vlccontrol.seek("-2")
			self.vlccontrol.play()
		except Exception, e:
			self.session.open(
				MessageBox, _("Error with VLC server:\n%s" % e), MessageBox.TYPE_ERROR)
			self.stop()
			return
		self.session.nav.stopService()
		self.session.nav.playService(eServiceReference(0x1001, 0, self.url))
		self.state = self.STATE_PLAYING
		self.vlcservice.refresh()
		if self.shown:
			self.__setHideTimer()
		
	def stop(self):
		print "[VLC] stop"
		self.session.nav.stopService()
		if self.state == self.STATE_IDLE:
			self.close()
			return
		if self.vlccontrol is not None:
			try:
				self.vlccontrol.stop()
				self.vlccontrol.delete()
			except Exception, e:
				self.session.open(
					MessageBox, _("Error with VLC server:\n%s" % e), MessageBox.TYPE_ERROR)
		self.state = self.STATE_IDLE
		self.vlcservice.setControl(None)
		self.vlcservice.refresh()
		self.show()

	def __setHideTimer(self):
		self.hidetimer.start(self.screen_timeout)

	def ok(self):
		if self.shown:
			self.hide()
			self.hidetimer.stop()
			self.vlcservice.refreshTimer.stop()
		else:
			self.vlcservice.refresh()
			self.show()
			if self.state == self.STATE_PLAYING:
				self.__setHideTimer()
			else:
				self.vlcservice.refreshTimer.start(self.vlcservice.refreshInterval)

	def cancel(self):
		self.stop()
		self.close()

	def seekRelative(self, delta):
		"""delta is seconds as integer number
		positive=forwards, negative=backwards"""
		if self.state != self.STATE_IDLE:
			if (delta >= 0):
				self.vlccontrol.seek("+"+str(delta))
			else:
				self.vlccontrol.seek(str(delta))
		self.vlcservice.refresh()
		if not self.shown:
			self.show()
			self.__setHideTimer()

	def seekFwd(self):
		self.seekRelative(600)

	def seekBack(self):
		self.seekRelative(-600)
