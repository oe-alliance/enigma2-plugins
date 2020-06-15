from __future__ import print_function
#######################################################################
#
#    InfoBar Tuner State for Enigma-2
#    Coded by betonme (c) 2011 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=162629
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

# for localized messages
from . import _

import math
import os
import NavigationInstance
import socket
import sys

from collections import defaultdict
from operator import attrgetter, itemgetter
try:
	from itertools import izip_longest as zip_longest # py2x
except:
	from itertools import zip_longest # py3k

# Plugin
from Plugins.Plugin import PluginDescriptor

# Config
from Components.config import *

# Screen
from Components.Label import Label
from Components.Language import *
from Components.Pixmap import Pixmap, MultiPixmap
from Components.ProgressBar import ProgressBar
from Components.ServiceEventTracker import ServiceEventTracker
from Screens.Screen import Screen
from Screens.InfoBar import InfoBar
from Screens.InfoBarGenerics import InfoBarShowHide
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from ServiceReference import ServiceReference
from time import strftime, time, localtime, mktime
from datetime import datetime, timedelta

from enigma import iServiceInformation, ePoint, eSize, getDesktop, iFrontendInformation
from enigma import eTimer
from enigma import iPlayableService, iRecordableService
from enigma import eDVBResourceManager, eActionMap, eListboxPythonMultiContent, eListboxPythonStringContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, eEPGCache, eServiceCenter, eServiceReference

from skin import parseColor, parseFont

# Plugin internal
from netstat import netstat


import six
from six.moves import range


# Extenal plugins: WebInterface
try:
	from Plugins.Extensions.WebInterface.WebScreens import StreamingWebScreen 
except:
	StreamingWebScreen = None


# Globals
InfoBarShow = None
InfoBarHide = None


# Type Enum
INFO, RECORD, STREAM, FINISHED = list(range(4))


# Constants
INFINITY =  u"\u221E".encode("utf-8")


#######################################################
# InfoBarShowHide for MoviePlayer integration
def overwriteInfoBar():
	global InfoBarShow, InfoBarHide
	if InfoBarShow is None:
		# Backup original function
		InfoBarShow = InfoBarShowHide._InfoBarShowHide__onShow
		# Overwrite function
		InfoBarShowHide._InfoBarShowHide__onShow = InfoBarShowTunerState
	if InfoBarHide is None:
		# Backup original function
		InfoBarHide = InfoBarShowHide._InfoBarShowHide__onHide
		# Overwrite function
		InfoBarShowHide._InfoBarShowHide__onHide = InfoBarHideTunerState

# InfoBar Events
def recoverInfoBar():
	global InfoBarShow, InfoBarHide
	if InfoBarShow:
		InfoBarShowHide._InfoBarShowHide__onShow = InfoBarShow
		InfoBarShow = None
	if InfoBarHide:
		InfoBarShowHide._InfoBarShowHide__onHide = InfoBarHide
		InfoBarHide = None

def InfoBarShowTunerState(self):
	from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
	global gInfoBarTunerState
	global InfoBarShow
	if InfoBarShow:
		InfoBarShow(self)
	if gInfoBarTunerState:
		gInfoBarTunerState.show()

def InfoBarHideTunerState(self):
	from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
	global gInfoBarTunerState
	global InfoBarHide
	if InfoBarHide:
		InfoBarHide(self)
	if gInfoBarTunerState:
		gInfoBarTunerState.hide()


#######################################################
# Extension menu
def addExtension():
	# Add to extension menu
	from Components.PluginComponent import plugins
	from Plugins.Extensions.InfoBarTunerState.plugin import IBTSSHOW, IBTSSETUP, show, setup
	if plugins:
		if config.infobartunerstate.extensions_menu_show.value:
			for p in plugins.getPlugins( where = PluginDescriptor.WHERE_EXTENSIONSMENU ):
				if p.name == IBTSSHOW:
					# Plugin is already in menu
					break
			else:
				# Plugin not in menu - add it
				plugin = PluginDescriptor(name = IBTSSHOW, description = IBTSSHOW, where = PluginDescriptor.WHERE_EXTENSIONSMENU, needsRestart = False, fnc = show)
				plugins.plugins[PluginDescriptor.WHERE_EXTENSIONSMENU].append(plugin)
		if config.infobartunerstate.extensions_menu_setup.value:
			for p in plugins.getPlugins( where = PluginDescriptor.WHERE_EXTENSIONSMENU ):
				if p.name == IBTSSETUP:
					# Plugin is already in menu
					break
			else:
				# Plugin not in menu - add it
				plugin = PluginDescriptor(name = IBTSSETUP, description = IBTSSETUP, where = PluginDescriptor.WHERE_EXTENSIONSMENU, needsRestart = False, fnc = setup)
				plugins.plugins[PluginDescriptor.WHERE_EXTENSIONSMENU].append(plugin)

def removeExtension():
	# Remove from extension menu
	from Components.PluginComponent import plugins
	from Plugins.Extensions.InfoBarTunerState.plugin import IBTSSHOW, IBTSSETUP
	if config.infobartunerstate.extensions_menu_show.value:
		for p in plugins.getPlugins( where = PluginDescriptor.WHERE_EXTENSIONSMENU ):
			if p.name == IBTSSHOW:
				plugins.plugins[PluginDescriptor.WHERE_EXTENSIONSMENU].remove(p)
				break
	if config.infobartunerstate.extensions_menu_setup.value:
		for p in plugins.getPlugins( where = PluginDescriptor.WHERE_EXTENSIONSMENU ):
			if p.name == IBTSSETUP:
				plugins.plugins[PluginDescriptor.WHERE_EXTENSIONSMENU].remove(p)
				break

#######################################################
# Logical background task
class InfoBarTunerState(object):
	def __init__(self, session):
		self.session = session
		
		self.infobar = None
		self.info = None
		
		self.epg = eEPGCache.getInstance()
		
		self.showTimer = eTimer()
		self.showTimer.callback.append(self.tunerShow)
		
		self.hideTimer = eTimer()
		self.hideTimer.callback.append(self.tunerHide)
		
		self.updateTimer = eTimer()
		self.updateTimer.callback.append(self.update)
		
		self.forceBindInfoBarTimer = eTimer()
		self.forceBindInfoBarTimer.callback.append(self.bindInfoBar)
		
		self.entries = defaultdict(list)
		
		# Get Initial Skin parameters
		win = self.session.instantiateDialog(TunerStateBase)
		self.positionx = win.instance.position().x()
		self.positiony = win.instance.position().y()
		self.height = win.instance.size().height()
		self.spacing = win.spacing
		self.padding = win.padding
		
		desktopSize = getDesktop(0).size()
		self.desktopwidth = desktopSize.width()
		
		#TODO is it possible to create copies of a screen to avoid recreation
		win.close()
		
		# Bind recording and streaming events
		self.appendEvents()
		
		# Bind InfoBarEvents
		#self.bindInfoBar()
		#self.onLayoutFinish.append(self.bindInfoBar)
		# Workaround
		# The Plugin starts before the InfoBar is instantiated
		# Check every second if the InfoBar instance exists and try to bind our functions
		# Is there an alternative solution?
		if config.infobartunerstate.show_infobar.value:
			self.forceBindInfoBarTimer.start(1000, False)
		
		if config.infobartunerstate.show_overwrite.value:
			overwriteInfoBar()
		
		#TODO PiP
		#self.session.
		#InfoBar.instance.session
		#pip.currentService = service
		#pip.pipservice = iPlayableService
		#Events:
		#eventNewProgramInfo
		#decoder state
				
		# Add current running records / streams
		# We do it right here to ensure the InfoBar is intantiated
		self.updateRecordTimer()
		if config.infobartunerstate.show_streams.value:
			self.updateStreams()

	def appendEvents(self):
		# Recording Events
		# If we append our function, we will never see the timer state StateEnded for repeating timer
		if self.__onRecordingEvent not in self.session.nav.RecordTimer.on_state_change:
			self.session.nav.RecordTimer.on_state_change.insert(0, self.__onRecordingEvent)
		# Streaming Events
		if config.infobartunerstate.show_streams.value:
			if StreamingWebScreen:
				try:
					from Plugins.Extensions.WebInterface.WebScreens import streamingEvents
					if self.__onStreamingEvent not in streamingEvents:
						streamingEvents.append(self.__onStreamingEvent)
				except:
					pass

	def removeEvents(self):
		# Recording Events
		# If we append our function, we will never see the timer state StateEnded for repeating timer
		if self.__onRecordingEvent in self.session.nav.RecordTimer.on_state_change:
			self.session.nav.RecordTimer.on_state_change.remove(self.__onRecordingEvent)
		# Streaming Events
		if StreamingWebScreen:
			try:
				from Plugins.Extensions.WebInterface.WebScreens import streamingEvents
				if self.__onStreamingEvent in streamingEvents:
					streamingEvents.remove(self.__onStreamingEvent)
			except:
				pass

	def bindInfoBar(self):
		# Reimport InfoBar to force update of the class instance variable
		# Rebind only if it isn't done already 
		from Screens.InfoBar import InfoBar
		if InfoBar.instance:
			self.infobar = InfoBar.instance
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

	def unbindInfoBar(self):
		if self.infobar:
			if hasattr(self.infobar, "onShow"):
				if self.__onInfoBarEventShow in self.infobar.onShow:
					self.infobar.onShow.remove(self.__onInfoBarEventShow)
			if hasattr(self.infobar, "onHide"):
				if self.__onInfoBarEventHide in self.infobar.onHide:
					self.infobar.onHide.remove(self.__onInfoBarEventHide)

	def __onInfoBarEventShow(self):
		self.show()

	def __onInfoBarEventHide(self):
		self.hide()

	def __onRecordingEvent(self, timer):
		if not timer.justplay:
			print("IBTS Timer Event "+ str(timer.state) + ' ' + str(timer.repeated))
#TODO
# w.processRepeated()
# w.state = TimerEntry.StateWaiting
			if timer.state == timer.StatePrepared:
				print("IBTS StatePrepared")
				pass
			
			elif timer.state == timer.StateRunning:
				id = getTimerID( timer )
				print("IBTS Timer running ID", id, id in self.entries)
				if id not in self.entries:
					#channel = timer.service_ref.getServiceName()
					tuner, tunertype = getTuner(timer.record_service)
						
					#TEST Bug Repeating timer blocking tuner and are not marked as finished
					#timer.timeChanged = self.__OnTimeChanged
					
					name = timer.name
					service_ref = timer.service_ref
					
					# Is this really necessary?
					try: timer.Filename
					except:
						try: timer.freespace()
						except: pass
						timer.calculateFilename()
					filename = timer.Filename
					
					# Delete references to avoid blocking tuners
					del timer
					
					number = service_ref and getNumber(service_ref.ref)
					channel = service_ref and service_ref.getServiceName()
					
					win = self.session.instantiateDialog(TunerState, RECORD, tuner, tunertype, name, number, channel, filename)
					self.entries[id] = win
					if config.infobartunerstate.show_events.value:
						self.show(True)
			
			# Finished repeating timer will report the state StateEnded+1 or StateWaiting
			else:
				id = getTimerID( timer )
				# The id of a finished repeated timer can be changed
				#RecordTimerEntry(name=How I Met Your Mother, begin=Wed Jul 18 11:37:00 2012, serviceref=1:0:19:EF75:3F9:1:C00000:0:0:0:, justplay=False)
				#RecordTimerEntry(name=How I Met Your Mother, begin=Thu Jul 19 11:37:00 2012, serviceref=1:0:19:EF75:3F9:1:C00000:0:0:0:, justplay=False)
				#print "IBTS Timer finished ID", id, id in self.entries
				if id in self.entries:
					win = self.entries[id]
					
					begin = timer.begin
					end = timer.end
					endless = timer.autoincrease
					del timer
					
					win.updateType( FINISHED )
					win.updateTimes( begin, end, endless )
				
				# Show also if no matching id is found
				if config.infobartunerstate.show_events.value:
					self.show(True)

	def __onStreamingEvent(self, event, stream):
		if StreamingWebScreen and stream:
			print("IBTS Stream Event")
			if event == StreamingWebScreen.EVENT_START:
				
				try:
					from Plugins.Extensions.WebInterface.WebScreens import streamingScreens
				except:
					streamingScreens = []
				
				# Extract parameters
				tuner, tunertype = getTuner( stream.getRecordService() ) 
				ref = stream.getRecordServiceRef()
				ip = stream.clientIP
				id = getStreamID(stream)
				
				# Delete references to avoid blocking tuners
				del stream
				
				port, host, client = "", "", ""
				
#				# Workaround to retrieve the client ip
#				# Change later and use the WebScreens getActiveStreamingClients if implemented
#				ipports = [ (win.ip, win.port) for win in six.itervalues(self.entries) ]
#				for conn in netstat(getstate='ESTABLISHED', getuid=False, getpid=False, readable=False):
#					# Check if it is a streaming connection
#					if conn[3] == '8001':
#						ip = conn[4]
#						port = conn[5]
#						# Check if ip and port is already known
#						if (ip, port) not in ipports:
#							break
#				else:
#					# No new connection found, leave it empty
#					ip, port, = "", ""
				
				#TODO Port is actually not given
				
				event = ref and self.epg and self.epg.lookupEventTime(ref, -1, 0)
				if event: 
					name = event.getEventName()
				else:
					name = ""
					#TODO check file streaming
				
				service_ref = ServiceReference(ref)
				filename = "" #TODO file streaming - read meta eit
				
				try:
					host = ip and socket.gethostbyaddr( ip )
					client = host and host[0].split('.')[0]
				except socket.herror as x:
					pass
				
				number = service_ref and getNumber(service_ref.ref)
				channel = service_ref and service_ref.getServiceName()
				channel = channel.replace('\xc2\x86', '').replace('\xc2\x87', '')
				
				win = self.session.instantiateDialog(TunerState, STREAM, tuner, tunertype, name, number, channel, filename, client, ip, port)
				self.entries[id] = win
				if config.infobartunerstate.show_events.value:
					self.show(True)
			
			elif event == StreamingWebScreen.EVENT_END:
				
				# Remove Finished Stream
				id = getStreamID(stream)
				
				# Delete references to avoid blocking tuners
				del stream
				
				if id in self.entries:
					win = self.entries[id]
					
					begin = win.begin
					end = time()
					endless = False
					
					win.updateType( FINISHED )
					win.updateTimes( begin, end, endless )
					
					if config.infobartunerstate.show_events.value:
						self.show(True)

	def __OnTimeChanged(self):
		#TODO Config show on timer time changed
		self.show(True)

	def updateRecordTimer(self):
		for timer in NavigationInstance.instance.RecordTimer.timer_list:
			if timer.isRunning() and not timer.justplay:
				self.__onRecordingEvent(timer)

	def updateStreams(self):
		#TODO updateStreams but retrieving IP is not possible
		try:
			from Plugins.Extensions.WebInterface.WebScreens import streamingScreens
		except:
			streamingScreens = []
		
		#TODO file streaming actually not supported
		for stream in streamingScreens:
			# Check if screen exists
			if stream and stream.request and 'file' not in stream.request.args:
				self.__onStreamingEvent(StreamingWebScreen.EVENT_START, stream)

	def updateNextTimer(self):
		number_pending_records = int( config.infobartunerstate.number_pending_records.value )
		print("IBTS updateNextTimer", number_pending_records)
		
		nextwins = [ id for id in list(self.entries.keys()) if id.startswith('next')]
		
		if number_pending_records:
			timer_list = getNextPendingRecordTimers()[:number_pending_records]
			
			if timer_list:
				timer_list.reverse()
				
				for i, (timer, begin, end) in enumerate(timer_list):
					id = 'next'+str(i)
					if timer:
						name = timer.name
						service_ref = timer.service_ref
						
						# Is this really necessary?
						try: timer.Filename
						except:
							try: timer.freespace()
							except: pass
							timer.calculateFilename()
						filename = timer.Filename
						
						# Delete references to avoid blocking tuners
						del timer
						
						number = service_ref and getNumber(service_ref.ref)
						channel = service_ref and service_ref.getServiceName()
						
						# Only add timer if not recording
						#if not self.entries.has_key(str( timer ):
						if id in self.entries:
							nextwins.remove(id)
							win = self.entries[id]
							win.updateName(name)
							win.updateNumberChannel(number, channel)
							win.updateFilename(filename)
						else:
							win = self.session.instantiateDialog(TunerState, INFO, '', '', name, number, channel, filename)
						win.updateTimes( begin, end, win.endless )
						self.entries[id] = win
					else:
						if id in self.entries:
							del self.entries[id]
			
			# Close all not touched next windows
			if nextwins:
				for id in nextwins:
					if id in self.entries:
						del self.entries[id]

	def show(self, autohide=False, forceshow=False):
		print("IBTS show")
		allowclosing = True
		if self.updateTimer.isActive() and autohide:
			# Avoid closing if the update timer is active
			allowclosing = False
		if self.showTimer.isActive():
			self.showTimer.stop()
		if forceshow:
			self.tunerShow(forceshow=forceshow)
		else:
			self.showTimer.start( 10, True )
			self.updateTimer.start( 60 * 1000 )
		if allowclosing:
			if autohide or self.session.current_dialog is None or not issubclass(self.session.current_dialog.__class__, InfoBarShowHide):
				# Start timer to avoid permanent displaying
				# Do not start timer if no timeout is configured
				timeout = int(config.infobartunerstate.infobar_timeout.value) or int(config.usage.infobar_timeout.index)
				if timeout > 0:
					if self.hideTimer.isActive():
						self.hideTimer.stop()
					self.hideTimer.startLongTimer( timeout )
				if self.updateTimer.isActive():
					self.updateTimer.stop()
		else:
			if self.hideTimer.isActive():
				self.hideTimer.stop()

	def tunerShow(self, forceshow=False):
		print("IBTS tunerShow")
		
		self.updateNextTimer()
		
		if self.entries:
			# There are active entries
			
			# Close info screen
			if self.info:
				self.info.hide()
			
			# Rebind InfoBar Events
			#self.bindInfoBar()
			
			# Only show the Tuner information dialog,
			# if no screen is displayed or the InfoBar is visible
			#TODO Info can also be showed if info.rectangle is outside currentdialog.rectangle
	#		if self.session.current_dialog is None \
	#			or isinstance(self.session.current_dialog, InfoBar):
			#MAYBE Tuner Informationen werden zusammen mit der EMCMediaCenter InfoBar angezeigt
			#or isinstance(self.session.current_dialog, EMCMediaCenter):
			
			# Delete entries:
			#  if entry reached timeout
			#  if number of entries is reached
			numberfinished = 0
			for id, win in sorted( list(self.entries.items()), key=lambda x: (x[1].end), reverse=True ):
				if win.type == FINISHED:
					numberfinished += 1
				if win.toberemoved == True \
					or win.type == FINISHED and numberfinished > int( config.infobartunerstate.number_finished_records.value ):
					# Delete Stopped Timers
					self.session.deleteDialog(win)
					del self.entries[id]
			
			# Update windows
			# Dynamic column resizing and repositioning
			widths = []
			for id, win in list(self.entries.items()):
				if win.type == RECORD:
					#TODO Avolid blocking - avoid using getTimer to update the timer times use timer.time_changed if possible
					timer = getTimer( id )
					#print id, timer
					if timer:
						begin = timer.begin
						end = timer.end
						endless = timer.autoincrease
						
						if not win.tuner or not win.tunertype:
							win.tuner, win.tunertype = getTuner(timer.record_service)
						service_ref = None
						if not win.channel or not win.number:
							service_ref = timer.service_ref
							
						del timer
						
						if service_ref:
							win.number = win.number or service_ref and getNumber(service_ref.ref)
							win.channel = win.channel or service_ref and service_ref.getServiceName()
							win.channel = win.channel.replace('\xc2\x86', '').replace('\xc2\x87', '')
						
						win.updateTimes( begin, end, endless )
						win.update()
					else:
						# This can happen, if the time has been changed or if the timer does not exist anymore
						begin = win.begin
						end = win.end
						if end < begin or end > time():
							end = time()
						endless = False
						win.updateType( FINISHED )
						win.updateTimes( begin, end, endless )
						win.update()
						#TEST
						del self.entries[id]
						self.updateRecordTimer()
				elif win.type == STREAM:
					if config.infobartunerstate.show_streams.value:
						#TODO Avolid blocking - avoid using getStream to update the current name
						stream = getStream( id )
						if stream:
							ref = stream.getRecordServiceRef()
							
							if not win.tuner or not win.tunertype:
								win.tuner, win.tunertype = getTuner(stream.getRecordService())
							
							del stream
							
							event = ref and self.epg and self.epg.lookupEventTime(ref, -1, 0)
							if event: 
								name = event.getEventName()
							else:
								name = ""
							
							begin = win.begin
							end = None
							endless = True
							
							service_ref = None
							if not win.number:
								service_ref = ServiceReference(ref)
								win.number = service_ref and getNumber(service_ref.ref)
							if not win.channel:
								service_ref = service_ref or ServiceReference(ref)
								win.channel = win.channel or service_ref and service_ref.getServiceName()
							
							win.updateName( name )
							win.updateTimes( begin, end, endless )
							win.update()
						else:
							win.toberemoved = True
					else:
						# Should never happen delete
						begin = win.begin
						end = time()
						endless = False
						win.updateType( FINISHED )
						win.updateTimes( begin, end, endless )
						win.update()
				else:
					# Type INFO / FINISHED
					win.update()
				
				# Calculate field width
				widths = [max( w1_w2[0], w1_w2[1] ) for w1_w2 in zip_longest( widths, win.widths )]
		
		#if self.entries:
			# Get initial padding / offset position and apply user offset
			padding = self.padding + int(config.infobartunerstate.offset_padding.value)
			#print "IBTS px, self.padding, config.padding", px, self.padding, int(config.infobartunerstate.offset_padding.value)
			
			# Calculate field spacing
			spacing = self.spacing + int(config.infobartunerstate.offset_spacing.value)
			#print "IBTS spacing, self.spaceing, config.spacing", spacing, self.spacing, int(config.infobartunerstate.offset_spacing.value)
			#widths = [ width+spacing if width>0 else 0 for width in widths ]
			
			# Apply user offsets
			posx = self.positionx + int(config.infobartunerstate.offset_horizontal.value)
			#print "IBTS posx, self.positionx, config.offset_horizontal", posx, self.positionx, int(config.infobartunerstate.offset_horizontal.value)
			posy = self.positiony + int(config.infobartunerstate.offset_vertical.value)
			height = self.height
			#print "IBTS widths", widths
			
			# Handle maximum width
			overwidth = posx + sum(widths) + len([w for w in widths if w]) * spacing + padding - self.desktopwidth + int(config.infobartunerstate.offset_rightside.value)
			#print "IBTS overwidth", overwidth
			
			# Order windows
			#wins = sorted( six.itervalues(self.entries), key=lambda x: (x.type, x.endless, x.timeleft, x.begin), reverse=False )
			
			#TEST 1
			#wins = sorted( six.itervalues(self.entries), key=lambda x: (x.type, x.endless, x.timeleft, x.begin), reverse=config.infobartunerstate.list_goesup.value )
			
			#TEST 2
			#wins = []
			#wins =       sorted( [ w for w in self.entries.values() if w.type == INFO ],     key=lambda x: (x.type, x.endless, x.begin), reverse=False )
			#wins.extend( sorted( [ w for w in self.entries.values() if w.type == RECORD ],   key=lambda x: (x.type, x.endless, x.timeleft, x.begin), reverse=False ) )
			#wins.extend( sorted( [ w for w in self.entries.values() if w.type == FINISHED ], key=lambda x: (x.type, x.endless, x.timeleft, x.begin), reverse=False ) )
			#wins.extend( sorted( [ w for w in self.entries.values() if w.type == STREAM ],   key=lambda x: (x.type, x.endless, x.timeleft, x.begin), reverse=False ) )
			#if config.infobartunerstate.list_goesup.value:
			#	wins.reverse()
			
			#TEST 3
			wins = sorted( six.itervalues(self.entries), key=lambda x: (x.type, x.endless, x.begin), reverse=config.infobartunerstate.list_goesup.value )
			
			# Resize, move and show windows
			for win in wins:
				win.move( posx, posy )
				win.reorder( widths, overwidth )
				posy += height
				# Show windows
				win.show()
			
		elif forceshow:
			# No entries available
			try:
				if not self.info:
					self.info = self.session.instantiateDialog( TunerStateInfo, _("Nothing running") )
				self.info.show()
				print("IBTS self.info.type", self.info.type)
			except Exception as e:
				print("InfoBarTunerState show exception " + str(e))

	def update(self):
		print("IBTS updating")
		#for win in six.itervalues(self.entries):
		#	#TODO Update also names, width, order, type ...
		#	win.update()
		self.tunerShow()

	def hide(self):
		print("IBTS hide")
		if self.updateTimer.isActive():
			self.updateTimer.stop()
		if self.hideTimer.isActive():
			self.hideTimer.stop()
		self.hideTimer.start( 10, True )

	def tunerHide(self):
		print("IBTS tunerHide")
		for win in six.itervalues(self.entries):
			win.hide()
		if self.info:
			self.info.hide()

	def close(self):
		print("IBTS close")
		recoverInfoBar()
		removeExtension()
		self.unbindInfoBar()
		self.removeEvents()
		self.hide()
		for id, win in list(self.entries.items()):
			self.session.deleteDialog(win)
			del self.entries[id]
		from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
		global gInfoBarTunerState
		gInfoBarTunerState = None


#######################################################
# Base screen class, contains all skin relevant parts
class TunerStateBase(Screen):
	# Skin will only be read once
	skinfile = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/InfoBarTunerState/skin.xml" )
	skin = open(skinfile).read()

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "TunerState"
		
		self["Background"] = Pixmap()
		self["Type"] = MultiPixmap()
		self["Progress"] = ProgressBar()
		
		for i in list(range( len( config.infobartunerstate.fields.dict() ) )):
		#for i, c in enumerate( six.itervalues(config.infobartunerstate.fields.dict()) ):
			label = Label()
			#fieldid = "Field"+str(i)
			self[ "Field"+str(i) ] = label
		
		self.padding = 0
		self.spacing = 0
		
		self.widths = []
		
		self.typewidth = 0
		self.progresswidth = 0
		
		self.onLayoutFinish.append(self.layoutFinished)

	def applySkin(self):
		attribs = [ ] 
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "padding":
					self.padding = int(value)
				elif attrib == "spacing":
					self.spacing = int(value)
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs
		return Screen.applySkin(self)

	def layoutFinished(self):
		#TODO Possible to read in applySkin
		self.typewidth = self["Type"].instance.size().width()
		self.progresswidth = self["Progress"].instance.size().width()

	def reorder(self, widths, overwidth=0):
		# Get initial padding / offset position and apply user offset
		padding = self.padding + int(config.infobartunerstate.offset_padding.value)
		#print "IBTS px, self.padding, config.padding", px, self.padding, int(config.infobartunerstate.offset_padding.value)
		
		# Calculate field spacing
		spacing = self.spacing + int(config.infobartunerstate.offset_spacing.value)
		#print "IBTS spacing, self.spaceing, config.spacing", spacing, self.spacing, int(config.infobartunerstate.offset_spacing.value)
		
		px = padding
		py = 0
		sh = self.instance.size().height()
		#print(self.widths)
		
		fieldwidths = list(config.infobartunerstate.fieldswidth.dict().values())
		
		for i, (c, width) in enumerate( zip( list(config.infobartunerstate.fields.dict().values()), widths ) ):
			fieldid = "Field"+str(i)
			field = c.value
			if field == "TypeIcon":
				self["Type"].instance.move( ePoint(px, py) )
			
			elif field == "TimerProgressGraphical":
				#self[field].instance.resize( eSize(width, sh) )
				# Center the progress field vertically
				y = int( ( sh - self["Progress"].instance.size().height() ) / 2 )
				self["Progress"].instance.move( ePoint(px, y) )
			
			elif field == "Name":
				if config.infobartunerstate.variable_field_width.value:
					width -= max(0, overwidth)
				else:
					width -= overwidth
				self[fieldid].instance.resize( eSize(width, sh) )
				self[fieldid].instance.move( ePoint(px, py) )
			
			#elif field == "None":
			#	pass
			
			else:
				self[fieldid].instance.resize( eSize(width, sh) )
				self[fieldid].instance.move( ePoint(px, py) )
			
			#TODO I think we could simplify this
			# Avoid unnecesarry resize and move operations
			#for j, fieldwidth in enumerate( config.infobartunerstate.fieldswidth.dict().values() ):
			#	if i == j and int(fieldwidth.value) > 0 and not (field == "TimerProgressGraphical" or field == "TypeIcon" or field == "None"):
			if fieldwidths:
				fieldwidth = int( fieldwidths[i].value )
				if fieldwidth > 0 and not (field == "TimerProgressGraphical" or field == "TypeIcon" or field == "None"):
					# Handle new maximum width
					if width > 0:
						overwidth +=  fieldwidth - width
					else:		
						overwidth +=  fieldwidth - width + spacing
					width = fieldwidth
					self[fieldid].instance.resize( eSize(width, sh) )
					self[fieldid].instance.move( ePoint(px, py) )
					
			if width:
				px += width + spacing
			
		# Set background
		bw = self["Background"].instance.size().width()
		# Avoid background start position is within our window
		bw = px-bw if px-bw<0 else 0
		self["Background"].instance.move( ePoint(bw, py) )
		self.instance.resize( eSize(px, sh) )

	def move(self, posx, posy):
		self.instance.move(ePoint(posx, posy))


#######################################################
# Displaying screen class, show nothing running
class TunerStateInfo(TunerStateBase):
	#TODO reuse TunerState and avoid a clone class
	def __init__(self, session, name):
		TunerStateBase.__init__(self, session)
		
		self.type = INFO
		self.name = name
		
		if not config.infobartunerstate.background_transparency.value:
			self["Background"].show()
		else:
			self["Background"].hide()
		
		self["Progress"].hide()
		
		#for i, c in enumerate( six.itervalues(config.infobartunerstate.fields.dict()) ):
		for i in list(range( len( config.infobartunerstate.fields.dict() ) )):
			fieldid = "Field"+str(i)
			
			if fieldid == "Field0":
				#self[field].setText( str(self.name).encode("utf-8") )
				self[fieldid].setText( str(self.name) )
		
		self.onLayoutFinish.append(self.popup)

	def popup(self):
		print("IBTS popup")
		
		self["Type"].setPixmapNum(3)
		
		widths = []
		widths.append( self.typewidth )
		
		height = self.instance.size().height()
		
		#for i, c in enumerate( six.itervalues(config.infobartunerstate.fields.dict()) ):
		for i in list(range( len( config.infobartunerstate.fields.dict() ) )):
			fieldid = "Field"+str(i)
			
			#Workaround#1 Set default size
			self[fieldid].instance.resize( eSize(1000, height) )
			
			width = max(self[fieldid].instance.calculateSize().width(), 0)
			#print(width)
			
			#Workaround#2 Expand the calculate size
			width = int( width * 1.10 )
			
			#self[field].instance.resize( eSize(width, height) )
			
			widths.append( width )
		
		self.widths = widths
		
		#spacing = self.spacing + int(config.infobartunerstate.offset_spacing.value)
		#widths = [ width+spacing if width>0 else 0 for width in widths ]
		
		posx = self.instance.position().x() + int(config.infobartunerstate.offset_horizontal.value) 
		posy = self.instance.position().y() + int(config.infobartunerstate.offset_vertical.value)
		
		self.move( posx, posy )
		self.reorder(widths)


#######################################################
# Displaying screen class, every entry is an instance of this class
class TunerState(TunerStateBase):
	def __init__(self, session, type, tuner, tunertype, name="", number="", channel="", filename="", client="", ip="", port=""):
		#TODO use parameter ref instead of number and channel
		TunerStateBase.__init__(self, session)
		
		self.toberemoved = False
		self.removeTimer = eTimer()
		self.removeTimer.callback.append(self.remove)
		
		self.type = type
		self.tuner = tuner
		self.tunertype = tunertype
		
		self.name = name
		
		self.number = number
		self.channel = channel
		
		self.filename = filename + ".ts"
		self.destination = filename and os.path.dirname( filename )
		
		self.filesize = None
		self.freespace = None
		
		self.client = client
		self.ip = ip
		self.port = port
		
		self.begin = time()
		self.end = 0
		self.timeleft = None
		self.timeelapsed = None
		self.duration = None
		self.progress = None
		self.endless = False
	
	def updateName(self, name):
		self.name = name

	def updateNumberChannel(self, number, channel):
		self.number = number
		self.channel = channel

	def updateFilename(self, filename):
		self.filename = filename + ".ts"

	def updateType(self, type):
		if self.type != type:
			self.type = type
		if self.type == FINISHED:
			print("IBTS updateType FINISHED")
			self.tuner = _("-")
			self.tunertype = _("-")
			# Check if timer is already started
			if not self.removeTimer.isActive():
				# Check if timeout is configured
				timeout = int(config.infobartunerstate.timeout_finished_records.value)
				if timeout > 0:
					self.removeTimer.startLongTimer( timeout )

	def updateTimes(self, begin, end, endless):
		self.begin = begin
		self.end = end
		self.endless = endless

	def updateDynamicContent(self):
		#TODO cleanup this function
		
		# Time and progress
		now = time()
		begin = self.begin
		end = self.end
		
		duration = None
		timeleft = None
		timeelapsed = None
		progress = None
		
		duration = begin and end and end - begin
		if duration and duration < 0:
			duration = None
		
		if self.type == FINISHED:
			# Finished events
			timeelapsed = None #duration
		elif begin and end and begin < now:
			timeelapsed = min(now - begin, duration)
		else:
			# Future event
			timeelapsed = None
		
		if not self.endless and self.end:
			
			if self.type == FINISHED:
				# Finished events
				timeleft = None #0
			elif begin and end and begin < now:
				timeleft = max(end - now, 0)
			else:
				# Future event
				timeleft = None
			
			if timeelapsed and duration:
				# Adjust the watched movie length (98% of movie length) 
				# else we will never see the 100%
				# Alternative using math.ceil but then we won't see 0
				length = duration / 100.0 * 98.0
				# Calculate progress and round up
				progress = timeelapsed / length * 100.0
				# Normalize progress
				if progress < 0: progress = 0
				elif progress > 100: progress = 100
			else:
				progress = None
			
		self.duration = duration and duration is not None and math.ceil( ( duration ) / 60.0 )
		self.timeleft = timeleft and timeleft is not None and math.ceil( ( timeleft ) / 60.0 )
		self.timeelapsed = timeelapsed and timeelapsed is not None and math.ceil( ( timeelapsed ) / 60.0 )
		self.progress = progress and progress is not None and int( progress )
		#print "IBTS duration, timeleft, timeelapsed, progress", self.duration, self.timeleft, self.timeelapsed, self.progress
		
		# File site and free disk space
		filename = self.filename
		if filename and os.path.exists( filename ):
			filesize = os.path.getsize( filename ) 
			self.filesize = filesize / (1024*1024)
			
			try:
				stat = os.statvfs( filename )
				self.freespace = ( stat.f_bfree / 1000 * stat.f_bsize / 1000 ) / 1024
				#free = os.stat(path).st_size/1048576)
			except OSError:
				pass

	def update(self):
		#TODO Handle Live / Stream Entries - Update several Labels
		self.updateDynamicContent()
		height = self.instance.size().height()
		widths = []
		
		# Set background transparency
		if not config.infobartunerstate.background_transparency.value:
			self["Background"].show()
		else:
			self["Background"].hide()
		
		self["Type"].hide()
		self["Progress"].hide()
		
		for i, c in enumerate( six.itervalues(config.infobartunerstate.fields.dict()) ):
			fieldid = "Field"+str(i)
			field = c.value
			text = ""
			
			if field == "TypeIcon":
				self["Type"].show()
				if self.type == RECORD:
					self["Type"].setPixmapNum(0)
				elif self.type == STREAM:
					self["Type"].setPixmapNum(1)
				elif self.type == FINISHED:
					self["Type"].setPixmapNum(2)
				elif self.type == INFO:
					self["Type"].setPixmapNum(3)
				else:
					widths.append( 0 )
					continue
				# No resize necessary
				widths.append( self.typewidth )
				continue
			
			elif field == "TypeText":
				if self.type == RECORD:
					text = _("Record")
				elif self.type == STREAM:
					text = _("Stream")
				elif self.type == FINISHED:
					text = _("Finished")
			
			elif field == "Tuner":
				if self.tuner:
					text = self.tuner
			
			elif field == "TunerType":
				if self.tunertype:
					text = self.tunertype
			
			elif field == "Number":
				if self.number is not None:
					text = _("%d") % ( self.number )
			
			elif field == "Channel":
				text = self.channel
			
			elif field == "Name":
				text = self.name
				#TODO update name for streams
			
			elif field == "TimeLeft":
				if not self.endless:
					if self.timeleft is not None:
						# Show timeleft recording time
						text = _("%d Min") % ( self.timeleft )
				else: 
					# Add infinity symbol for indefinitely recordings
					text = INFINITY
			
			elif field == "TimeElapsed":
				if self.timeelapsed is not None:
					text = _("%d Min") % ( self.timeelapsed )
			
			elif field == "TimeLeftDuration":
				# Calculate timeleft minutes
				if not self.endless:
					if self.type is not FINISHED and self.timeleft is not None:
					#if self.timeleft is not None:
						# Show timeleft recording time
						text = _("%d Min") % ( self.timeleft )
					elif self.duration is not None:
						# Fallback show recording length
						text = _("%d Min") % ( self.duration )
				else: 
					# Add infinity symbol for indefinitely recordings
					text = INFINITY
			
			elif field == "Begin":
				lbegin = self.begin and localtime( self.begin )
				text = lbegin and strftime( config.infobartunerstate.time_format_begin.value, lbegin )
			
			elif field == "End":
				lend = self.end and localtime( self.end )
				text = lend and strftime( config.infobartunerstate.time_format_end.value, lend )
			
			elif field == "Duration":
				if self.duration is not None:
					text = _("%d Min") % ( self.duration )
			
			elif field == "TimerProgressText":
				if self.progress is not None:
					text = _("%d %%") % ( self.progress )
			
			elif field == "TimerProgressGraphical":
				if self.progress is not None:
					self["Progress"].setValue( self.progress )
					self["Progress"].show()
					# No resize necessary
					widths.append( self.progresswidth )
				else:
					if not config.infobartunerstate.placeholder_pogressbar.value:
						widths.append( 0 )
					else:	
						widths.append( self.progresswidth )
				continue
			
			elif field == "TimerDestination":
				text = self.destination
			
			elif field == "StreamClient":
				text = self.client or self.ip
			
			elif field == "StreamClientPort":
				if self.port:
					text = self.client or self.ip
					text += ":" + str(self.port)
			
			elif field == "DestinationStreamClient":
				text = self.destination or self.client or self.ip
			
			elif field == "FileSize":
				if self.filesize  is not None:
					text = _("%d MB") % ( self.filesize )
			
			elif field == "FreeSpace":
				if self.freespace is not None:
					text = _("%d GB") % ( self.freespace )
			
			elif field == "None":
				# text is already initialized with ""
				pass
			
			# Set text, append field, resize field and append width
			self[fieldid].setText( text )
			
			# Set horizontal alignment
			if field == 'Number' or field == 'TimeLeftDuration' or field == 'TimeLeft' or field == 'TimeElapsed' or field == 'Duration' or field == 'TimerProgressText' or field == 'FileSize' or field == 'FreeSpace':
				self[fieldid].instance.setHAlign(2) # import _enigma # alignRight = _enigma.eLabel_alignRight
			
			#Workaround#1
			self[fieldid].instance.resize( eSize(1000, height) )
			
			width = max(self[fieldid].instance.calculateSize().width(), 0)
			#print(width)
			
			#Workaround#2
			width = int( width * 1.10 )
			
			#self[fieldid].instance.resize( eSize(width, height) )
			
			widths.append( width )
		
		self.widths = widths

	def remove(self):
		self.toberemoved = True 


#######################################################
# Global helper functions
def getTimerID(timer):
	#return str( timer.name ) + str( timer.repeatedbegindate ) + str( timer.service_ref ) + str( timer.justplay )
	return str( timer )

def getTimer(id):
	#for timer in self.session.nav.RecordTimer.timer_list + self.session.nav.RecordTimer.processed_timers:
	for timer in NavigationInstance.instance.RecordTimer.timer_list + NavigationInstance.instance.RecordTimer.processed_timers:
		#print "timerlist:", getTimerID( timer )
		if getTimerID( timer ) == id:
			return timer
	return None

def getStreamID(stream):
	#TEST_MULTIPLESTREAMS
	#if id == str(stream.getRecordServiceRef()) + str(stream.clientIP):
	##if(id == str(stream.getRecordServiceRef().toString()) + str(stream.clientIP)):
	return str(stream.screenIndex) + str(stream.clientIP)

def getStream(id):
	try:
		from Plugins.Extensions.WebInterface.WebScreens import streamingScreens 
	except:
		streamingScreens = []
	
	for stream in streamingScreens:
		if stream:
			if getStreamID(stream) == id:
				return stream
	return None

def getTuner(service):
	# service must be an instance of iPlayableService or iRecordableService
	#TODO detect stream of HDD
	feinfo = service and service.frontendInfo()
	data = feinfo and feinfo.getAll(False)
	if data:
		number = data.get("tuner_number", -1)
		type = data.get("tuner_type", "")
		if number is not None and number > -1:
			return ( chr( int(number) + ord('A') ), type)
	return "", ""

def readBouquetList(self):
	serviceHandler = eServiceCenter.getInstance()
	refstr = '1:134:1:0:0:0:0:0:0:0:FROM BOUQUET \"bouquets.tv\" ORDER BY bouquet'
	bouquetroot = eServiceReference(refstr)
	self.bouquetlist = {}
	list = serviceHandler.list(bouquetroot)
	if list is not None:
		self.bouquetlist = list.getContent("CN", True)

def getNumber(actservice):
	# actservice must be an instance of eServiceReference
	from Screens.InfoBar import InfoBar
	Servicelist = None
	if InfoBar and InfoBar.instance:
		Servicelist = InfoBar.instance.servicelist
	mask = (eServiceReference.isMarker | eServiceReference.isDirectory)
	number = 0
	bouquets = Servicelist and Servicelist.getBouquetList()
	if bouquets:
		#TODO get alternative for actbouquet
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
						if actbouquet:
							if actbouquet == bouquet and actservice == service:
								return number
						else:
							if actservice == service:
								return number
	return None

def getNextPendingRecordTimers():
	timer_list = []
	now = time()
	for timer in NavigationInstance.instance.RecordTimer.timer_list:
		next_act = timer.getNextActivation()
		if timer.justplay or (timer.isRunning() and not timer.repeated) or next_act < now:
			continue
		if timer.begin:
			if not timer.isRunning():
				begin = timer.begin
				end = timer.end
			else:
				begin, end = processRepeated(timer)
			timer_list.append( (timer, begin, end) )
	return sorted( timer_list, key=lambda x: (x[1]) )


# Adapted from TimerEntry
def processRepeated(timer, findRunningEvent = False):
	print("ProcessRepeated")
	
	def addOneDay(timedatestruct):
		oldHour = timedatestruct.tm_hour
		newdate =  (datetime(timedatestruct.tm_year, timedatestruct.tm_mon, timedatestruct.tm_mday, timedatestruct.tm_hour, timedatestruct.tm_min, timedatestruct.tm_sec) + timedelta(days=1)).timetuple()
		if localtime(mktime(newdate)).tm_hour != oldHour:
			return (datetime(timedatestruct.tm_year, timedatestruct.tm_mon, timedatestruct.tm_mday, timedatestruct.tm_hour, timedatestruct.tm_min, timedatestruct.tm_sec) + timedelta(days=2)).timetuple()
		return newdate
	
	begin = timer.begin
	end = timer.end
		
	if (timer.repeated != 0):
		now = int(time()) + 1

		#to avoid problems with daylight saving, we need to calculate with localtime, in struct_time representation
		localrepeatedbegindate = localtime(timer.repeatedbegindate)
		localbegin = localtime(begin)
		localend = localtime(end)
		localnow = localtime(now)

		print("localrepeatedbegindate:", strftime("%c", localrepeatedbegindate))
		print("localbegin:", strftime("%c", localbegin))
		print("localend:", strftime("%c", localend))
		print("localnow:", strftime("%c", localnow))

		day = []
		flags = timer.repeated
		for x in (0, 1, 2, 3, 4, 5, 6):
			if (flags & 1 == 1):
				day.append(0)
				print("Day: " + str(x))
			else:
				day.append(1)
			flags = flags >> 1

		# if day is NOT in the list of repeated days
		# OR if the day IS in the list of the repeated days, check, if event is currently running... then if findRunningEvent is false, go to the next event
		while ((day[localbegin.tm_wday] != 0) or (mktime(localrepeatedbegindate) > mktime(localbegin))  or
			((day[localbegin.tm_wday] == 0) and ((findRunningEvent and localend < localnow) or ((not findRunningEvent) and localbegin < localnow)))):
			localbegin = addOneDay(localbegin)
			localend = addOneDay(localend)
			print("localbegin after addOneDay:", strftime("%c", localbegin))
			print("localend after addOneDay:", strftime("%c", localend))
			
		#we now have a struct_time representation of begin and end in localtime, but we have to calculate back to (gmt) seconds since epoch
		begin = int(mktime(localbegin))
		end = int(mktime(localend))
		if begin == end:
			end += 1
		
		print("ProcessRepeated result")
		print(strftime("%c", localtime(begin)))
		print(strftime("%c", localtime(end)))
	
	return begin, end
