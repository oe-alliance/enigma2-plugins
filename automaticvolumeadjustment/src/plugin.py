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
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.config import config
from setup import AutomaticVolumeAdjustmentConfigScreen, AutomaticVolumeAdjustmentConfig
from Components.ServiceEventTracker import ServiceEventTracker
from enigma import iPlayableService, iServiceInformation, eDVBVolumecontrol, eServiceCenter, eServiceReference
from ServiceReference import ServiceReference

automaticvolumeadjustment = None # global, so setup can use method initializeConfigValues and enable/disable the plugin without gui restart

class AutomaticVolumeAdjustment(Screen):
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
		configVA = AutomaticVolumeAdjustmentConfig()
		self.initializeConfigValues(configVA, False)
		self.volctrl = eDVBVolumecontrol.getInstance()

	def initializeConfigValues(self, configVA, fromOutside):
		print "[AutomaticVolumeAdjustment] initialize config values..."
		self.serviceList = { }
		for c in configVA.config.Entries:
			self.serviceList[c.servicereference.value] = int(c.adjustvalue.value)
		self.defaultValue = int(configVA.config.adustvalue.value)
		self.enabled = configVA.config.enable.value
		if not self.pluginStarted and self.enabled and fromOutside:
			self.newService = True
			self.__evUpdatedInfo()
		
	def __evEnd(self):
		if self.pluginStarted and self.enabled:
			# if played service had AC3||DTS audio and volume value was changed with RC, take new delta value from the config
			if self.currentVolume and self.volctrl.getVolume() != self.currentVolume:
				self.lastAdjustedValue = self.serviceList.get(self.session.nav.getCurrentlyPlayingServiceReference().toString(), self.defaultValue)
					
	def __evStart(self):
		self.newService = True

	def __evUpdatedInfo(self):
		if self.newService and self.session.nav.getCurrentlyPlayingServiceReference() and self.enabled:
			print "[AutomaticVolumeAdjustment] service changed"
			self.newService = False
			self.currentVolume = 0 # init
			currentAC3DTS = self.isCurrentAudioAC3DTS()
			if self.pluginStarted:
				if currentAC3DTS: # ac3 dts?
					vol = self.volctrl.getVolume()
					currentvol = vol # remember current vol
					vol -= self.lastAdjustedValue # go back to origin value first
					ref = self.session.nav.getCurrentlyPlayingServiceReference()
					if ref.getPath(): # check if a moving is playing
						# it is , get the eServicereference if available
						self.serviceHandler = eServiceCenter.getInstance()
						info = self.serviceHandler.info(ref)
						if info:
							ref = eServiceReference(info.getInfoString(ref, iServiceInformation.sServiceref)) # set new eServicereference
					ajvol = self.serviceList.get(ref.toString(), self.defaultValue) # get delta from config
					if vol >= 100 - ajvol: # check if delta + vol < 100
						ajvol = 100 - vol # correct delta value
					self.lastAdjustedValue = ajvol # save delta value
					if ajvol !=0 and (vol+ajvol != currentvol): # only adjust volume when delta != 0 or current vol != new volume
						self.volctrl.setVolume(vol+self.lastAdjustedValue, vol+self.lastAdjustedValue)
						print "[AutomaticVolumeAdjustment] Change volume for service: %s (+%d) to %d"%(ServiceReference(ref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''), ajvol, self.volctrl.getVolume())
					self.currentVolume = self.volctrl.getVolume() # ac3||dts service , save current volume
				else:
					# mpeg or whatever audio
					if self.lastAdjustedValue != 0:
						# go back to origin value
						vol = self.volctrl.getVolume()
						self.volctrl.setVolume(vol-self.lastAdjustedValue, vol-self.lastAdjustedValue)
						print "[AutomaticVolumeAdjustment] Change volume for service: %s (-%d) to %d"%(ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference()).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''), self.lastAdjustedValue, self.volctrl.getVolume())
						self.lastAdjustedValue = 0 # mpeg audio, no delta here
				# save new volume in config
				config.audio.volume.value = self.volctrl.getVolume()
				config.audio.volume.save()
			else:
				# starting plugin, if service audio is ac3 or dts --> get delta from config...volume value is set by enigma2-system at start
				if currentAC3DTS:
					self.lastAdjustedValue = self.serviceList.get(self.session.nav.getCurrentlyPlayingServiceReference().toString(), self.defaultValue)
					self.currentVolume = self.volctrl.getVolume() # ac3||dts service , save current volume
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

def autostart(reason, **kwargs):
	if "session" in kwargs and automaticvolumeadjustment is None:
		global automaticvolumeadjustment
		session = kwargs["session"]
		automaticvolumeadjustment = AutomaticVolumeAdjustment(session)
	
def setup(session, **kwargs):
	session.open(AutomaticVolumeAdjustmentConfigScreen) # start setup

def startSetup(menuid):
	if menuid != "system": # show setup only in system level menu
		return []
	return [(_("Automatic Volume Adjustment"), setup, "AutomaticVolumeAdjustment", 46)]
	
def Plugins(**kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart), PluginDescriptor(name="Automatic Volume Adjustment", description=_("Automatic Volume Adjustment"), where = PluginDescriptor.WHERE_MENU, fnc=startSetup) ]

