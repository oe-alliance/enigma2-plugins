#######################################################################
#
#    InfoBar Tuner State for Enigma-2
#    Vesion 0.1
#    Coded by betonme (c)2011
#    Support: IHAD
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################

import math
import os
import NavigationInstance

from collections import defaultdict

from Components.ActionMap import ActionMap
from Components.config import config
from Components.Label import Label
#from Screens import InfoBarGenerics
from Screens.InfoBar import InfoBar
from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from time import time

from enigma import iServiceInformation, ePoint, eSize, getDesktop, iFrontendInformation

from enigma import eTimer
from Components.ServiceEventTracker import ServiceEventTracker
from enigma import iPlayableService, iRecordableService

from Components.GUIComponent import GUIComponent
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Sources.List import List
from enigma import eDVBResourceManager, eActionMap, eListboxPythonMultiContent, eListboxPythonStringContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, getBestPlayableServiceReference, eServiceCenter, eServiceReference

from skin import parseColor, parseFont

global gInfoBarTunerState
gInfoBarTunerState = None

def Plugins(**kwargs):
	
	#TODO localeInit()
	
	descriptors = []
	
	#AutoStart
	descriptors.append( PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart) ) #needsRestart=False,
	
	#TODO Config Screen
	#descriptors.append( PluginDescriptor(name = "InfoBar Tuner State", description = "Show a Tuner State Dialog", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main) ) #icon = "/EnhancedMovieCenter.png"

	return descriptors

def main(session, **kwargs):
	#TODO config
	# Autostart
	# Overwrite Skin Position
	# Show Live TV Tuners PiP Stream ...
	# Transparent
	# Border
	# Icon or Text for type
	# Order of elements
	# Allow Enable disable of elements 
	# Sort order of entry rows
	# Show on start, end, start/end
	# Show with infobar
	# Blink recording entry one time on finished
	pass

def autostart(reason, **kwargs):
	if reason == 0: # start
		if kwargs.has_key("session"):
			global gInfoBarTunerState
			session = kwargs["session"]
			gInfoBarTunerState = InfoBarTunerState(session)


class InfoBarTunerState(Screen):
	def __init__(self, session):
		
		Screen.__init__(self, session)
		
		self.hideTimer = eTimer()
		self.hideTimer.callback.append(self.tunerHide)
		
		#self.availTimer = eTimer()
		#self.availTimer.callback.append(self.resizeElements)
		
		self.tunerInfo = defaultdict(list)
		
		self.serviceHandler = eServiceCenter.getInstance()
		
		self.posy = getDesktop(0).size().height()
		
		# Recording Events
		self.session.nav.RecordTimer.on_state_change.append(self.__onRecordingEvent)
		# Streaming Events
		self.session.nav.record_event.append(self.__onStreamingEvent)
		# Zapping Events
		self.session.nav.event.append(self.__onPlayableEvent)
		#self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
		#	{
		#		iPlayableService.evStart: self.__onPlayableEvent,
		#		iPlayableService.evStopped: self.__onPlayableEvent,
		#	})
		
		#res_mgr = eDVBResourceManager.getInstance()
		#if res_mgr:
		#	res_mgr.frontendUseMaskChanged.get().append(self.__onTunerUseMaskChanged)
		
		# Bind InfoBarEvents
		self.bindInfoBar()
		
		#TODO Add current running recordings 
		#recordings = NavigationInstance.instance.getRecordings() gives iRecordableServices ?!?
		#timer_list = self.session.nav.RecordTimer.timer_list
		
		#TODO PiP
		#self.session.
		#InfoBar.instance.session
		#pip.currentService = service
		#pip.pipservice = iPlayableService
		#Events:
		#eventNewProgramInfo
		#decoder state
		
	#def test(self, event):
	#	print "InfoBarTuner test " + str(event)
	
	def __onTunerUseMaskChanged(self, mask):
		print "__onTunerUseMaskChanged    " +str(mask)
	
	def bindInfoBar(self):
		# Reimport InfoBar to force update of the class instance variable
		# Rebind only if it isn't done already 
		from Screens.InfoBar import InfoBar
		if InfoBar.instance:
			if hasattr(InfoBar.instance, "onShow"):
				if self.tunerShow not in InfoBar.instance.onShow:
					InfoBar.instance.onShow.append(self.__onInfoBarEventShow)
			if hasattr(InfoBar.instance, "onHide"):
				if self.tunerHide not in InfoBar.instance.onHide:
					InfoBar.instance.onHide.append(self.__onInfoBarEventHide)

	def __onInfoBarEventShow(self):
		#TODO config
		print "__onInfoBarEventShow    "
		#TODO count recordings and compare them - print warning if not equal
		self.tunerShow()

	def __onInfoBarEventHide(self):
		#TODO config
		print "__onInfoBarEventHide    "
		self.tunerHide()

	def __onRecordingEvent(self, timer):
		if timer.state == timer.StatePrepared:
			pass
		elif timer.state == timer.StateRunning:	# timer.isRunning()
			type = "Rec"
			print "__onRecordingEventRun    " +str(timer)
			#print "__onRecordingEventRun    " +str(timer.autoincrease)
			channel = timer.service_ref.getServiceName()
			tuner = self.getTuner(timer.record_service)
			name = timer.name
			number = self.getNumber(timer.service_ref.ref)
			end = not timer.autoincrease and timer.end
			#ts = timer.record_service
			#print "__onRecordingEvent timer.record_service " + str(timer.record_service)
			#print "__onRecordingEvent timer.service_ref.ref " + str(timer.service_ref.ref)
			#try: print "__onRecordingEvent timer.service_ref.ref.name " + str(timer.service_ref.ref.name)
			#except: pass
			if not timer in self.tunerInfo:
				w = self.session.instantiateDialog(TunerState, type, tuner, number, channel, name, end)
				self.tunerInfo[timer] = w
				#TODO config
				self.__startAvailTimer()
			
		else: #timer.state == timer.StateEnded:
			type = "Rec"
			print "__onRecordingEventEnd    " +str(timer)
			#print "__onRecordingEventEnd    " +str(timer.end)
			#print "__onRecordingEvent timer.record_service " + str(timer.record_service)
			#ts = timer.record_service
			if timer in self.tunerInfo:
				print "__onRecordingEvent removed "
				w = self.tunerInfo[timer]
				w.hide()
				self.session.deleteDialog(w)
				del self.tunerInfo[timer]
				#TODO config
				self.__startAvailTimer()

	def __onStreamingEvent(self, rec_service, event):
		print "__onStreamingEvent0    " +str(rec_service)
		#try: 
		#	print "__onStreamingEvent2    " +str(rec_service.)
		#except: pass
		print "__onStreamingEvent2    " +str(event)
		#if event in (iRecordableService.evEnd, iRecordableService.evStart, None):
		#	self.__startAvailTimer()
		#if event == iRecordableService.evStart:
		#try: 
		#	print "__onStreamingEvent3 rec_service.ref " + str(rec_service.ref)
		#	#print "__onStreamingEvent4 ts.stream.getStreamingData " + str(rec_service.stream().getStreamingData())
		#except: pass
#		try: 
#			subser = rec_service.subServices()
#			print subser.getNumberOfSubservices()
#			ser =  subser.getSubservice(0)
#			print ser
#			print "__onStreamingEvent6 sername " + str(ser.name)
#		except: pass

	def __onPlayableEvent(self, event):
		#TEST PiP
		print "__onPlayableEvent    " + str(event)
		#self.__startAvailTimer()

	def __startAvailTimer(self):
		#if self.availTimer.isActive():
		#	self.availTimer.stop()
		###if not self.shown:
		#self.availTimer.start(2500, True)
		self.resizeElements()
		# Show windows
		self.tunerShow()

	def getTuner(self, service):
		# service must be an instance of iPlayableService or iRecordableService
		feinfo = service and service.frontendInfo()
		frontendData = feinfo and feinfo.getAll(False)
		return chr( frontendData.get("tuner_number", -1) + ord('A') )
	
	def getNumber(self, actservice):
		# actservice must be an instance of eServiceReference
		from Screens.InfoBar import InfoBar
		Servicelist = None
		if InfoBar and InfoBar.instance:
			Servicelist = InfoBar.instance.servicelist
		mask = (eServiceReference.isMarker | eServiceReference.isDirectory)
		number = 0
		bouquets = Servicelist and Servicelist.getBouquetList()
		if bouquets:
			actbouquet = Servicelist.getRoot()
			for name, bouquet in bouquets:
				if not bouquet.valid(): #check end of list
					break
				if bouquet.flags & eServiceReference.isDirectory:
					servicelist = self.serviceHandler.list(bouquet)
					if not servicelist is None:
						while True:  #TODO
							service = servicelist.getNext()
							if not service.valid(): #check end of list
								break
							playable = not (service.flags & mask)
							if playable:
								number += 1;
							if actbouquet == bouquet and actservice == service:
								return number
		return -1

	def resizeElements(self):
		# Rebind InfoBar Events
		self.bindInfoBar()
		
		# Dynamic column resizing and repositioning
		posy = self.posy
		posx, sizeh = 0, 0
		lentuner, lennumber, lenchannel, lenname = 0, 0, 0, 0
		for w in self.tunerInfo.itervalues():
			if posx == 0:
				posx = w.instance.position().x()
				sizeh = w.instance.size().height()
			posy       = min( w.instance.position().y(), posy )
			lentuner   = max( w["Tuner"].instance.calculateSize().width(), lentuner )
			lennumber  = max( w["Number"].instance.calculateSize().width(), lennumber )
			lenchannel = max( w["Channel"].instance.calculateSize().width(), lenchannel )
			lenname    = max( w["Name"].instance.calculateSize().width(), lenname )
		self.posy = posy
		
		# Spacing between the column entries
		lentuner   += 10
		lennumber  += 10
		lenchannel += 10
		lenname    += 10
		
		# Set window positions
		for w in self.tunerInfo.itervalues():
			w.instance.move(ePoint(posx, posy))
			w.resize(lentuner, lennumber, lenchannel, lenname)
			posy += sizeh
	
	def tunerShow(self):
		# Only show the Tuner information dialog,
		# if no screen is displayed or the InfoBar is visible
		if self.session.current_dialog is None or isinstance(self.session.current_dialog, InfoBar):
			#TODO current_dialog is None: Show Info only if changed
			for w in self.tunerInfo.itervalues():
				w.show()
				
			# Start timer to avoid permanent displaying
			self.hideTimer.start((config.usage.infobar_timeout.index or 1)*1000, True)
	
	def tunerHide(self):
		for w in self.tunerInfo.itervalues():
			w.hide()

class TunerState(Screen):
	skin = """
		<screen name="TunerState" flags="wfNoBorder" position="50,50" size="1000,32" title="Tuner State" zPosition="-1">
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InfoBarTunerState/bg.png" position="0,0" size="1000,32" zPosition="-1" alphatest="off" transparent="1"/>
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InfoBarTunerState/record.png" position="0,0" size="42,32" zPosition="1" alphatest="blend"/>
			<widget name="Type"      font="Regular;22" noWrap="1" position="0,0"   size="42,32" halign="center" valign="center" foregroundColor="#bbbbbf" backgroundColor="#141415" transparent="1"/>
			<widget name="Tuner"     font="Regular;22" noWrap="1" position="42,0"  size="50,32" halign="left"   valign="center" foregroundColor="#ffffff" backgroundColor="#141415" transparent="1"/>
			<widget name="Number"    font="Regular;22" noWrap="1" position="100,0" size="50,32" halign="left"   valign="center" foregroundColor="#bbbbbf" backgroundColor="#141415" transparent="1"/>
			<widget name="Channel"   font="Regular;22" noWrap="1" position="200,0" size="50,32" halign="left"   valign="center" foregroundColor="#ffffff" backgroundColor="#141415" transparent="1"/>
			<widget name="Name"      font="Regular;22" noWrap="1" position="300,0" size="50,32" halign="left"   valign="center" foregroundColor="#bbbbbf" backgroundColor="#141415" transparent="1"/>
			<widget name="Remaining" font="Regular;22" noWrap="1" position="400,0" size="50,32" halign="left"   valign="center" foregroundColor="#ffffff" backgroundColor="#141415" transparent="1"/>
		</screen>"""

	def __init__(self, session, type, tuner, number, channel, name, end):
		
		Screen.__init__(self, session)
		
		#if config... = text
			#self["Type"] = Label(type)
		#else:
		self["Type"] = Label("")
		self["Tuner"] = Label(tuner)
		if number > 0:
			self["Number"] = Label( str(number) )
		else:
			self["Number"] = Label("")
		self["Channel"] = Label(channel)
		
		self["Name"] = Label(name)
		
		if end > 0:
			self["Remaining"] = Label("")
			self.timerend = end
			self.onShow.append(self.updateRemaining)
		else: 
			# Add infinity symbol for indefinitely recordings
			self["Remaining"] = Label(u" \u221E ".encode("utf-8"))
		
#		skin = None
#		CoolWide = getDesktop(0).size().width()
#		if CoolWide == 720:
#			skin = "/usr/lib/enigma2/python/Plugins/Extensions/EnhancedMovieCenter/CoolSkin/EMCSelection_720.xml"
#		elif CoolWide == 1024:
#			skin = "/usr/lib/enigma2/python/Plugins/Extensions/EnhancedMovieCenter/CoolSkin/EMCSelection_1024.xml"
#		elif CoolWide == 1280:
#			skin = "/usr/lib/enigma2/python/Plugins/Extensions/EnhancedMovieCenter/CoolSkin/EMCSelection_1280.xml"
#		if skin:
#			Cool = open(skin)
#			self.skin = Cool.read()
#			Cool.close()

	def resize(self, lentuner, lennumber, lenchannel, lenname):
		sh = self.instance.size().height()

		self["Tuner"].instance.resize( eSize(lentuner, sh) )
		px = self["Tuner"].instance.position().x()
		py = self["Tuner"].instance.position().y()
		px += lentuner
		
		self["Number"].instance.resize( eSize(lennumber, sh) )
		self["Number"].instance.move( ePoint(px, py) )
		px += lennumber

		self["Channel"].instance.resize( eSize(lenchannel, sh) )
		self["Channel"].instance.move( ePoint(px, py) )
		px += lenchannel
		
		self["Name"].instance.resize( eSize(lenname, sh) )
		self["Name"].instance.move( ePoint(px, py) )
		px += lenname
		
		#lenremaining = max(self.instance.size().width()-px, 0)
		#self["Remaining"].instance.resize( eSize(lenremaining, sh) )
		self["Remaining"].instance.move( ePoint(px, py) )
	
	def updateRemaining(self):
		# Calculate remaining minutes 
		remaining = int( math.ceil( ( self.timerend - time() ) / 60.0 ) )
		self["Remaining"].setText( str(remaining) + _(" Min") )
		w = self["Remaining"].instance.calculateSize().width()
		h = self["Remaining"].instance.size().height()
		self["Remaining"].instance.resize( eSize(w, h) )
		#TODO resize background equal for all windows ?
		#TODO Handle Live Entry - Update all Labels
