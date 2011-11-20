#######################################################################
#
#    InfoBar Tuner State for Enigma-2
#    Vesion 0.4
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
from operator import attrgetter, itemgetter

from Components.ActionMap import ActionMap
from Components.config import config
from Components.Label import Label
from Components.Pixmap import Pixmap
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
from enigma import eDVBResourceManager, eActionMap, eListboxPythonMultiContent, eListboxPythonStringContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, eEPGCache, eServiceCenter, eServiceReference

from skin import parseColor, parseFont

#try:
#	# try to import EMC module to check for its existence
#	from Plugins.Extensions.EnhancedMovieCenter.EnhancedMovieCenter import EMCMediaCenter 
#except ImportError, ie:
#	class EMCMediaCenter: pass


global gInfoBarTunerState
gInfoBarTunerState = None


def Plugins(**kwargs):
	
	#TODO localeInit()
	
	descriptors = []
	
	# AutoStart and SessionStart
	descriptors.append( PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, fnc = start) ) #needsRestart=False,
	descriptors.append( PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = start) )

	#TODO Config Screen
	#descriptors.append( PluginDescriptor(name = "InfoBar Tuner State", description = "Show a Tuner State Dialog", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main) ) #icon = "/EnhancedMovieCenter.png"

	return descriptors

def main(session, **kwargs):
	#TODO config
	# Autostart
	# Overwrite Skin Position
	# Show Live TV Tuners PiP Stream ...
	# Background: Transparent, Block, Dynamic(Farbverlauf)
	# Width: FullRow, Adapted/Fitting, Symmetrical
	# Icon or Text for type
	# Order of elements
	# Allow Enable disable of elements 
	# Sort order of entry rows
	#		Type: Live pip stream record endedrecords
	#		Tuner A B C D
	#		Number
	#		Channel
	#		Name
	#		Remaining >0 infinite -
	# Show on start, end, start/end
	# Show with infobar
	# Blink recording entry one time on finished
	# Recording Finished show recording duration
	# Show on EMCMovieCenter
	pass

def start(reason, **kwargs):
	#print "InfoBarTunerState autostart "
	#print str(reason)
	#print str(kwargs)
	if reason == 0: # start
		if kwargs.has_key("session"):
			global gInfoBarTunerState
			session = kwargs["session"]
			gInfoBarTunerState = InfoBarTunerState(session)


# Type Enum
RecordStarted, RecordFinished = range(2)


class InfoBarTunerState(Screen):
	def __init__(self, session):
		
		Screen.__init__(self, session)
		
		self.hideTimer = eTimer()
		self.hideTimer.callback.append(self.tunerHide)
		
		#self.availTimer = eTimer()
		#self.availTimer.callback.append(self.tunerShow)
		
		self.forceBindInfoBarTimer = eTimer()
		self.forceBindInfoBarTimer.callback.append(self.bindInfoBar)
		
		self.tunerInfo = defaultdict(list)
		
		self.posy = getDesktop(0).size().height()
		
		# Recording Events
		self.session.nav.RecordTimer.on_state_change.append(self.__onRecordingEvent)
		# Streaming Events
		#self.session.nav.record_event.append(self.__onStreamingEvent)
		# Zapping Events
		#self.session.nav.event.append(self.__onPlayableEvent)
		#self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
		#	{
		#		iPlayableService.evStart: self.bindInfoBar,
		#	})
		
		#res_mgr = eDVBResourceManager.getInstance()
		#if res_mgr:
		#	res_mgr.frontendUseMaskChanged.get().append(self.__onTunerUseMaskChanged)
		
		# Add current running records 
		self.updateRecordTimer()
		
		#self.onLayoutFinish.append(self.bindInfoBar)
		
		# Bind InfoBarEvents
		#self.bindInfoBar()
		# Workaround
		# The Plugin starts before the InfoBar is instantiated
		# Check every second if the InfoBar instance exists and try to bind our functions
		# Is there an alternative solution?
		self.forceBindInfoBarTimer.start(1000, False)
		
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
	
	def bindInfoBar(self):
		# Reimport InfoBar to force update of the class instance variable
		# Rebind only if it isn't done already 
		from Screens.InfoBar import InfoBar
		print "InfoBarTunerState InfoBar.instance " + str(InfoBar.instance)
		if InfoBar.instance:
			bindShow = False
			bindHide = False
			if hasattr(InfoBar.instance, "onShow"):
				if self.__onInfoBarEventShow not in InfoBar.instance.onShow:
					InfoBar.instance.onShow.append(self.__onInfoBarEventShow)
					bindShow = True
			if hasattr(InfoBar.instance, "onHide"):
				if self.__onInfoBarEventHide not in InfoBar.instance.onHide:
					InfoBar.instance.onHide.append(self.__onInfoBarEventHide)
					bindHide = True
			if bindShow and bindHide:
				# Bind was successful
				self.forceBindInfoBarTimer.stop()

	def __onTunerUseMaskChanged(self, mask):
		print "__onTunerUseMaskChanged    " +str(mask)

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
			print "__onRecordingEventPrep    " +str(timer)
		elif timer.state == timer.StateRunning:	# timer.isRunning()
			if not timer.justplay:
				type = RecordStarted
				print "__onRecordingEventRun    " +str(timer)
				channel = timer.service_ref.getServiceName()
				tuner = self.getTuner(timer.record_service)
				name = timer.name
				timer.timeChanged = self.__OnTimeChanged
				#ts = timer.record_service
				#print "__onRecordingEvent timer.record_service " + str(timer.record_service)
				#print "__onRecordingEvent timer.service_ref.ref " + str(timer.service_ref.ref)
				#try: print "__onRecordingEvent timer.service_ref.ref.name " + str(timer.service_ref.ref.name)
				#except: pass
				if not timer in self.tunerInfo:
					win = self.session.instantiateDialog(TunerState, type, tuner, channel, name, timer)
					self.tunerInfo[timer] = win
					#TODO config
					self.__startAvailTimer()
			
		else: #timer.state == timer.StateEnded:
			type = RecordFinished
			print "__onRecordingEventEnd    " +str(timer)
			
			if timer in self.tunerInfo:
				#TODO config 
				#if config.delete_immediately 
#				print "__onRecordingEvent removed "
				win = self.tunerInfo[timer]
#				win.hide()
#				self.session.deleteDialog(win)
#				del self.tunerInfo[timer]
#				#TODO config
				win.changeType(type)
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
		#TODO Filter events
		#self.__startAvailTimer()
		# Rebind InfoBar Events
		#self.bindInfoBar()
		
	def __OnTimeChanged(self):
		#TODO Config show on timer time changed
		self.tunerShow()

	def onExternShow(self):
		#TODO Config extern
		self.tunerShow()

	def onExternHide(self):
		#TODO Config extern
		self.tunerHide()

	def updateRecordTimer(self):
		for timer in NavigationInstance.instance.RecordTimer.timer_list:
			if timer.isRunning() and not timer.justplay:
				self.__onRecordingEvent(timer)

	def __startAvailTimer(self):
		#if self.availTimer.isActive():
		#	self.availTimer.stop()
		#self.availTimer.startLongTimer( 10 )
		# Show windows
		self.tunerShow()

	#TODO Howto move this function to the window ?!?
	def getTuner(self, service):
		# service must be an instance of iPlayableService or iRecordableService
		feinfo = service and service.frontendInfo()
		frontendData = feinfo and feinfo.getAll(False)
		return chr( frontendData.get("tuner_number", -1) + ord('A') )
	
	def tunerShow(self):
		# Rebind InfoBar Events
		#self.bindInfoBar()
		
		# Only show the Tuner information dialog,
		# if no screen is displayed or the InfoBar is visible
		#TODO Info can also be showed if info.rectangle is outside currentdialog.rectangle
		if self.session.current_dialog is None \
			or isinstance(self.session.current_dialog, InfoBar):
			#MAYBE Tuner Informationen werden zusammen mit der EMCMediaCenter InfoBar angezeigt
			#or isinstance(self.session.current_dialog, EMCMediaCenter):
			
			# Delete old entries
			for timer, win in self.tunerInfo.items():
				if win.tobedeleted == True:
					# Delete Stopped Timers
					self.session.deleteDialog(win)
					del self.tunerInfo[timer]
					
			# Dynamic column resizing and repositioning
			#TODO get Initial Position and Size from skin
			posy = self.posy
			posx, sizeh = 0, 0
			lentuner, lennumber, lenchannel, lenname, lenremaining = 0, 0, 0, 0, 0
			for win in self.tunerInfo.itervalues():
				win.updateContent()
				if posx == 0:
					posx = win.instance.position().x()
					sizeh = win.instance.size().height()
				posy       = min( win.instance.position().y(), posy )
				lentuner   = max( win["Tuner"].instance.calculateSize().width(), lentuner )
				lennumber  = max( win["Number"].instance.calculateSize().width(), lennumber )
				lenchannel = max( win["Channel"].instance.calculateSize().width(), lenchannel )
				lenname    = max( win["Name"].instance.calculateSize().width(), lenname )
				lenremaining = max( win["Remaining"].instance.calculateSize().width(), lenremaining )
			
			self.posy = posy
			
			# Spacing between the column entries
			lentuner   += 15
			lennumber  += 15
			lenchannel += 15
			lenname    += 15
			print lenname
			lenremaining += 15
			
			# Resize, move and show windows
			for win in sorted( self.tunerInfo.itervalues(), key=lambda x: (x.type, x.remaining) ):
				win.resize(lentuner, lennumber, lenchannel, lenname, lenremaining)
				win.instance.move(ePoint(posx, posy))
				posy += sizeh
				# Show windows
				win.show()
				
			# Start timer to avoid permanent displaying
			# Do not start timer if no timeout is configured
			idx = config.usage.infobar_timeout.index
			if idx:
				if self.hideTimer.isActive():
					self.hideTimer.stop()
				self.hideTimer.startLongTimer( config.usage.infobar_timeout.index or 1 )
	
	def tunerHide(self):
		if self.hideTimer.isActive():
			self.hideTimer.stop()
		for win in self.tunerInfo.itervalues():
			win.hide()


class TunerState(Screen):
	skinfile = "/usr/lib/enigma2/python/Plugins/Extensions/InfoBarTunerState/skin.xml" 
	skin = open(skinfile).read()

	def __init__(self, session, type, tuner, channel, name, timer=None):
		
		Screen.__init__(self, session)
		
		self.closeTimer = eTimer()
		self.closeTimer.callback.append(self.deleteEntry)
		self.tobedeleted = False
		
		self.timer = timer
		
		self.type = type
		self["Background"] = Pixmap()
		self["Record"] = Pixmap()
		self["Stopped"] = Pixmap()
		self.updateType()
		
		self["Tuner"] = Label(tuner)
		self["Number"] = Label()
		self["Channel"] = Label(channel)
		
		self["Name"] = Label(name)
		
		self.remaining = 0
		self["Remaining"] = Label()
		
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

	def changeType(self, type):
		self.type = type
		self.updateType()

	def updateType(self):
		if self.type == RecordStarted:
			self["Record"].show()
			self["Stopped"].hide()
		elif self.type == RecordFinished:
			self["Record"].hide()
			self["Stopped"].show()
			self["Tuner"].setText( "-" )
			#TODO config
			if not self.closeTimer.isActive():
				self.closeTimer.startLongTimer( 60 )

	def updateContent(self):
		#self.updateType()
		# Calculate remaining minutes
		if self.timer:
			if not self.timer.autoincrease:
				if self.type == RecordFinished:
					self.remaining = 0
					self["Remaining"].setText( "-" )
				elif self.timer.end > 0:
					self.remaining = int( math.ceil( ( self.timer.end - time() ) / 60.0 ) )
					self["Remaining"].setText( str(self.remaining) + _(" Min") )
				else:
					self.remaining = 0
					self["Remaining"].setText( "" )
			else: 
				# Add infinity symbol for indefinitely recordings
				self.remaining = 0xFFFFFFFFFFFFFFFF
				self["Remaining"].setText( u"\u221E".encode("utf-8") )
				#TODO config update name of infinite recordings
				epg = eEPGCache.getInstance()
				event = epg and epg.lookupEventTime(self.timer.service_ref.ref, -1, 0)
				if event: 
					self["Name"].setText( event.getEventName() )
		else:
			# No timer available
			self.remaining = 0
			self["Remaining"].setText( "" )
		
		if not self["Number"].getText():
			number = self.getNumber(self.timer.service_ref.ref)
			if number > 0:
				self["Number"].setText( str(number) )
		
		#TODO Handle Live Entry - Update all Labels

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
			serviceHandler = eServiceCenter.getInstance()
			for name, bouquet in bouquets:
				if not bouquet.valid(): #check end of list
					break
				if bouquet.flags & eServiceReference.isDirectory:
					servicelist = serviceHandler.list(bouquet)
					if not servicelist is None:
						while True:
							service = servicelist.getNext()
							if not service.valid(): #check end of list
								break
							playable = not (service.flags & mask)
							if playable:
								number += 1
							if actbouquet == bouquet and actservice == service:
								return number
		return -1

	def resize(self, lentuner, lennumber, lenchannel, lenname, lenremaining):
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
		
		self["Remaining"].instance.resize( eSize(lenremaining, sh) )
		self["Remaining"].instance.move( ePoint(px, py) )
		px += lenremaining
		
		#TODO config width and style
		
		#if background dynamic
		#self["Background"].instance.resize( eSize(px, sh) )
		#self.instance.resize( eSize(px, sh) )
		
		#if background color gradiant
		bw = self["Background"].instance.size().width()
		self["Background"].instance.move( ePoint(px-bw, py) )
		self.instance.resize( eSize(px, sh) )

	def deleteEntry(self):
		self.tobedeleted = True 

