# -*- coding: utf-8 -*-
#
#  AutomaticVolumeAdjustment E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2010
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.config import config
from Components.ServiceEventTracker import ServiceEventTracker
from enigma import iPlayableService, iServiceInformation, eDVBVolumecontrol, eServiceCenter, eServiceReference
from ServiceReference import ServiceReference
from Components.VolumeControl import VolumeControl
from AutomaticVolumeAdjustmentConfig import AutomaticVolumeAdjustmentConfig, getVolumeDict

class AutomaticVolumeAdjustment(Screen):
	instance = None
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		print "[AutomaticVolumeAdjustment] Starting AutomaticVolumeAdjustment..."
		self.__event_tracker = ServiceEventTracker(screen = self, eventmap =
			{
				iPlayableService.evUpdatedInfo: self.__evUpdatedInfo,
				iPlayableService.evStart: self.__evStart,
				iPlayableService.evEnd: self.__evEnd
			})
		self.newService = False # switching flag
		self.pluginStarted = False # is plugin started?
		self.lastAdjustedValue = 0 # remember delta from last automatic volume up/down
		self.currentVolume = 0 # only set when AC3 or DTS is available
		self.enabled = False # AutomaticVolumeAdjustment enabled in setup?
		self.serviceList = { } # values from config
		configVA = AutomaticVolumeAdjustmentConfig() # get config values
		assert not AutomaticVolumeAdjustment.instance, "only one AutomaticVolumeAdjustment instance is allowed!"
		AutomaticVolumeAdjustment.instance = self # set instance
		self.volumeControlInstance = None # VolumeControlInstance
		self.currentAC3DTS = False # current service = AC3||DTS?
		self.initializeConfigValues(configVA, False)
		self.volctrl = eDVBVolumecontrol.getInstance()

	def initializeConfigValues(self, configVA, fromOutside):
		print "[AutomaticVolumeAdjustment] initialize config values..."
		self.serviceList = { }
		self.modus = configVA.config.modus.value # get modus
		if self.modus == "0": # Automatic volume adjust mode
			for c in configVA.config.Entries:
					self.serviceList[c.servicereference.value] = int(c.adjustvalue.value) # adjust volume
		else: # Remember channel volume mode
			self.serviceList = getVolumeDict()
		self.defaultValue = int(configVA.config.adustvalue.value)
		self.enabled = configVA.config.enable.value
		self.maxMPEGVolume = configVA.config.mpeg_max_volume.value
		self.showVolumeBar = configVA.config.show_volumebar.value
		if self.modus == "0": # Automatic volume adjust mode
			VolumeControlInit(self.enabled, self.maxMPEGVolume) # overwrite VolumeControl Class, when max MPEG Volume was set (<> 100)
		if not self.pluginStarted and self.enabled and fromOutside:
			self.newService = True
			self.__evUpdatedInfo()
		
	def __evEnd(self):
		if self.pluginStarted and self.enabled:
			if self.modus == "0": # Automatic volume adjust mode
				# if played service had AC3||DTS audio and volume value was changed with RC, take new delta value from the config
				if self.currentVolume and self.volctrl.getVolume() != self.currentVolume:
					self.lastAdjustedValue = self.serviceList.get(self.session.nav.getCurrentlyPlayingServiceReference().toString(), self.defaultValue)
			else: # Remember channel volume mode
					# save current volume in dict, but for valid ref only
					ref = self.getPlayingServiceReference()
# Check it is not None before using it!
					if ref and ref.valid():
						self.serviceList[ref.toString()] = self.volctrl.getVolume()
		
	def __evStart(self):
		self.newService = True

	def __evUpdatedInfo(self):
		if self.newService and self.session.nav.getCurrentlyPlayingServiceReference() and self.enabled:
			print "[AutomaticVolumeAdjustment] service changed"
			self.newService = False
			self.currentVolume = 0 # init
			if self.modus == "0": # Automatic volume adjust mode
				self.currentAC3DTS = self.isCurrentAudioAC3DTS()
				if self.pluginStarted:
					if self.currentAC3DTS: # ac3 dts?
						vol = self.volctrl.getVolume()
						currentvol = vol # remember current vol
						vol -= self.lastAdjustedValue # go back to origin value first
						ref = self.getPlayingServiceReference()
						ajvol = self.serviceList.get(ref.toString(), self.defaultValue) # get delta from config
						if ajvol < 0: # adjust vol down
							if vol + ajvol < 0:
								ajvol = (-1) * vol
						else: # adjust vol up
							if vol >= 100 - ajvol: # check if delta + vol < 100
								ajvol = 100 - vol # correct delta value
						self.lastAdjustedValue = ajvol # save delta value
						if (vol + ajvol != currentvol):
							if ajvol == 0:
								ajvol = vol - currentvol # correction for debug -print only
							self.setVolume(vol+self.lastAdjustedValue)
							print "[AutomaticVolumeAdjustment] Change volume for service: %s (+%d) to %d"%(ServiceReference(ref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''), ajvol, self.volctrl.getVolume())
						self.currentVolume = self.volctrl.getVolume() # ac3||dts service , save current volume
					else:
						# mpeg or whatever audio
						if self.lastAdjustedValue != 0:
							# go back to origin value
							vol = self.volctrl.getVolume()
							ajvol = vol-self.lastAdjustedValue
							if ajvol > self.maxMPEGVolume:
									ajvol = self.maxMPEGVolume
							self.setVolume(ajvol)
							print "[AutomaticVolumeAdjustment] Change volume for service: %s (-%d) to %d"%(ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference()).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''), vol-ajvol, self.volctrl.getVolume())
							self.lastAdjustedValue = 0 # mpeg audio, no delta here
					return # get out of here, nothing to do anymore
			else: # modus = Remember channel volume
				if self.pluginStarted:
					ref = self.getPlayingServiceReference()
					if ref.valid():
						# get value from dict
						lastvol = self.serviceList.get(ref.toString(), -1)
						if lastvol != -1 and lastvol != self.volctrl.getVolume():
							# set volume value
							self.setVolume(lastvol)
							print "[AutomaticVolumeAdjustment] Set last used volume value for service %s to %d"%(ServiceReference(ref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''), self.volctrl.getVolume())
					return # get out of here, nothing to do anymore
			if not self.pluginStarted:
				if self.modus == "0": # Automatic volume adjust mode
					# starting plugin, if service audio is ac3 or dts --> get delta from config...volume value is set by enigma2-system at start
					if self.currentAC3DTS:
						self.lastAdjustedValue = self.serviceList.get(self.session.nav.getCurrentlyPlayingServiceReference().toString(), self.defaultValue)
						self.currentVolume = self.volctrl.getVolume() # ac3||dts service , save current volume
				# only images >= 05.08.2010, must use try/except
				try: self.volumeControlInstance = VolumeControl.instance
				except:	pass
				self.pluginStarted = True # plugin started...

	def isCurrentAudioAC3DTS(self):
		service = self.session.nav.getCurrentService()
		audio = service.audioTracks()
		if audio:
			try: # uhh, servicemp3 leads sometimes to OverflowError Error
				tracknr = audio.getCurrentTrack()
				i = audio.getTrackInfo(tracknr)
				description = i.getDescription();
				if "AC3" in description or "DTS" in description:
					return True
			except:
				return False
		return False
		
	def getPlayingServiceReference(self):
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
# Check it is not None before using it!
		if ref and ref.getPath(): # check if a movie is playing
			# it is , get the eServicereference if available
			self.serviceHandler = eServiceCenter.getInstance()
			info = self.serviceHandler.info(ref)
			if info:
				# no need here to know if eServiceReference is valid...
				ref = eServiceReference(info.getInfoString(ref, iServiceInformation.sServiceref)) # get new eServicereference from meta file
		return ref
		
	def setVolume(self, value):
		# set new volume 
		self.volctrl.setVolume(value, value)
		if self.volumeControlInstance is not None:
			self.volumeControlInstance.volumeDialog.setValue(value) # update progressbar value
			if self.showVolumeBar: 
				# show volume bar 
				self.volumeControlInstance.volumeDialog.show()
				self.volumeControlInstance.hideVolTimer.start(3000, True)
		# save new volume value in E2-settings
		config.audio.volume.value = self.volctrl.getVolume()
		config.audio.volume.save()


# VolumeControl Class --> overwrite setVolume
# only for max. mpeg-volume restriction
baseVolumeControl_setVolume = None
		
def VolumeControlInit(enabled, maxVolume):
	global baseVolumeControl_setVolume
	if baseVolumeControl_setVolume is None:
		baseVolumeControl_setVolume = VolumeControl.setVolume
	if enabled and maxVolume <> 100:
		VolumeControl.setVolume = AVA_setVolume
		VolumeControl.maxVolume = maxVolume
	else:
		VolumeControl.setVolume = baseVolumeControl_setVolume
		baseVolumeControl_setVolume = None

def AVA_setVolume(self, direction):
	ok = True
	if direction > 0:
		oldvol = self.volctrl.getVolume()
		if not AutomaticVolumeAdjustment.instance.currentAC3DTS:	
			if oldvol+1 > self.maxVolume:
				ok = False
				self.volumeDialog.setValue(oldvol)
				self.volumeDialog.show()
				self.hideVolTimer.start(3000, True)
	if ok:
		baseVolumeControl_setVolume(self, direction)
