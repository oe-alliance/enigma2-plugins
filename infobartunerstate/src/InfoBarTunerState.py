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
from itertools import izip_longest as zip_longest # py3k

# Plugin
from Plugins.Plugin import PluginDescriptor

# Config
from Components.config import *

# Screen
from Screens.Screen import Screen
from Components.Label import Label
from Components.Language import *
from Components.Pixmap import Pixmap, MultiPixmap
from Components.ProgressBar import ProgressBar
from Components.ServiceEventTracker import ServiceEventTracker

from Screens.InfoBar import InfoBar
from Screens.InfoBarGenerics import InfoBarShowHide
from Screens.Screen import Screen
from ServiceReference import ServiceReference
from time import time, localtime, strftime

from enigma import iServiceInformation, ePoint, eSize, getDesktop, iFrontendInformation
from enigma import eTimer
from enigma import iPlayableService, iRecordableService
from enigma import eDVBResourceManager, eActionMap, eListboxPythonMultiContent, eListboxPythonStringContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, eEPGCache, eServiceCenter, eServiceReference

from skin import parseColor, parseFont

# Plugin internal
from netstat import netstat


# Extenal plugins: WebInterface
try:
	from Plugins.Extensions.WebInterface.WebScreens import StreamingWebScreen 
except:
	StreamingWebScreen = None


# Globals
InfoBarShow = None
InfoBarHide = None


# Type Enum
Record, Stream, Finished, INFO = range( 4 )


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
	from Plugins.Extensions.InfoBarTunerState.plugin import NAME, DESCRIPTION, extension
	if plugins:
		for p in plugins.getPlugins( where = PluginDescriptor.WHERE_EXTENSIONSMENU ):
			if p.name == NAME:
				# Plugin is already in menu
				break
		else:
			# Plugin not in menu - add it
			plugin = PluginDescriptor(name = NAME, description = DESCRIPTION, where = PluginDescriptor.WHERE_EXTENSIONSMENU, needsRestart = False, fnc = extension)
			plugins.plugins[PluginDescriptor.WHERE_EXTENSIONSMENU].append(plugin)

def removeExtension():
	# Remove from extension menu
	from Components.PluginComponent import plugins
	from Plugins.Extensions.InfoBarTunerState.plugin import NAME, DESCRIPTION
	for p in plugins.getPlugins( where = PluginDescriptor.WHERE_EXTENSIONSMENU ):
		if p.name == NAME:
			plugins.plugins[PluginDescriptor.WHERE_EXTENSIONSMENU].remove(p)
			break


#######################################################
# Logical background task
class InfoBarTunerState(object):
	def __init__(self, session):
		self.session = session
		
		self.infobar = None
		self.info = None
		
		self.showTimer = eTimer()
		self.showTimer.callback.append(self.tunerShow)
		
		self.hideTimer = eTimer()
		self.hideTimer.callback.append(self.tunerHide)
		
		self.forceBindInfoBarTimer = eTimer()
		self.forceBindInfoBarTimer.callback.append(self.bindInfoBar)
		
		self.entries = defaultdict(list)
		
		# Get Initial Skin parameters
		win = self.session.instantiateDialog(TunerStateBase)
		self.positionx = win.instance.position().x()
		self.positiony = win.instance.position().y()
		self.height = win.instance.size().height()
		self.spacing = win.spacing
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
			if timer.state == timer.StatePrepared:
				pass
			
			elif timer.state == timer.StateRunning:
				id = str( timer )
				if id not in self.entries:
					#channel = timer.service_ref.getServiceName()
					tuner, tunertype = getTuner(timer.record_service)
						
					#TEST Bug Repeating timer blocking tuner and are not marked as finished
					#timer.timeChanged = self.__OnTimeChanged
					
					name = timer.name
					service_ref = timer.service_ref
					
					# Is this really necessary?
					try: timer.Filename
					except: timer.calculateFilename()
					filename = timer.Filename
					
					# Delete references to avoid blocking tuners
					del timer
					
					number = service_ref and getNumber(service_ref.ref)
					channel = service_ref and service_ref.getServiceName()
					
					win = self.session.instantiateDialog(TunerState, Record, tuner, tunertype, name, number, channel, filename)
					self.entries[id] = win
					if config.infobartunerstate.show_events.value:
						self.show(True)
			
			# Finished repeating timer will report the state StateEnded+1 or StateWaiting
			else:
				id = str( timer )
				if id in self.entries:
					win = self.entries[id]
					
					begin = timer.begin
					end = timer.end
					endless = timer.autoincrease
					del timer
					
					win.updateType( Finished )
					win.updateTimes( begin, end, endless )
					
					if config.infobartunerstate.show_events.value:
						self.show(True)

	def __onStreamingEvent(self, event, stream):
		if StreamingWebScreen and stream:
			
			if event == StreamingWebScreen.EVENT_START:
				
				try:
					from Plugins.Extensions.WebInterface.WebScreens import streamingScreens
				except:
					streamingScreens = []
				
				# Extract parameters
				tuner, tunertype = getTuner( stream.getRecordService() ) 
				ref = stream.getRecordServiceRef()
				ip = stream.clientIP
				id = str(stream.screenIndex) + str(ip)
				
				# Delete references to avoid blocking tuners
				del stream
				
				port, host, client = "", "", ""
				
#				# Workaround to retrieve the client ip
#				# Change later and use the WebScreens getActiveStreamingClients if implemented
#				ipports = [ (win.ip, win.port) for win in self.entries.itervalues() ]
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
				
				epg = ref and eEPGCache.getInstance()
				event = epg and epg.lookupEventTime(ref, -1, 0)
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
				except socket.herror, x:
					pass
				
				number = service_ref and getNumber(service_ref.ref)
				channel = service_ref and service_ref.getServiceName()
				
				win = self.session.instantiateDialog(TunerState, Stream, tuner, tunertype, name, number, channel, filename, client, ip, port)
				self.entries[id] = win
				if config.infobartunerstate.show_events.value:
					self.show(True)
			
			elif event == StreamingWebScreen.EVENT_END:
				
				# Remove Finished Stream
				id = str(stream.screenIndex) + str(stream.clientIP)
				# Delete references to avoid blocking tuners
				del stream
				
				if id in self.entries:
					win = self.entries[id]
					
					begin = win.begin
					end = time()
					endless = False
					
					win.updateType( Finished )
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

	def show(self, autohide=False):
		if self.showTimer.isActive():
			self.showTimer.stop()
		self.showTimer.start( 10, True )
		if autohide or self.session.current_dialog is None or not issubclass(self.session.current_dialog.__class__, InfoBarShowHide):
			# Start timer to avoid permanent displaying
			# Do not start timer if no timeout is configured
			idx = int(config.usage.infobar_timeout.index)
			if idx > 0:
				if self.hideTimer.isActive():
					self.hideTimer.stop()
				self.hideTimer.startLongTimer( int(idx) )

	def tunerShow(self):
		if self.entries:
			# Close info screen
			if self.info:
				self.info.hide()
				self.session.deleteDialog(self.info)
				self.info = None
			
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
			for id, win in sorted( self.entries.items(), key=lambda x: (x[1].end), reverse=True ):
				if win.type == Finished:
					numberfinished += 1
				if win.toberemoved == True \
					or win.type == Finished and numberfinished > int( config.infobartunerstate.number_finished_records.value ):
					# Delete Stopped Timers
					self.session.deleteDialog(win)
					del self.entries[id]
			
			# Update windows
			# Dynamic column resizing and repositioning
			widths = []
			for id, win in self.entries.items():
				if win.type == Record:
					#TODO Avolid blocking - avoid using getTimer to update the timer times use timer.time_changed if possible
					timer = getTimer( id )
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
						
						win.updateTimes( begin, end, endless )
						win.update()
					else:
						# Should never happen delete
						begin = win.begin
						end = time()
						endless = False
						win.updateType( Finished )
						win.updateTimes( begin, end, endless )
						win.update()
				elif win.type == Stream:
					if config.infobartunerstate.show_streams.value:
						#TODO Avolid blocking - avoid using getStream to update the current name
						stream = getStream( id )
						if stream:
							ref = stream.getRecordServiceRef()
							
							if not win.tuner or not win.tunertype:
								win.tuner, win.tunertype = getTuner(stream.getRecordService())
							
							del stream
							
							epg = eEPGCache.getInstance()
							event = epg and epg.lookupEventTime(ref, -1, 0)
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
							win.toberemoved == True
					else:
						# Should never happen delete
						begin = win.begin
						end = time()
						endless = False
						win.updateType( Finished )
						win.updateTimes( begin, end, endless )
						win.update()
				else:
					# Type Finished
					win.update()
				
				# Calculate field width
				widths = map( lambda (w1, w2): max( w1, w2 ), zip_longest( widths, win.widths ) )
			
			# Calculate field spacing
			spacing = self.spacing + int(config.infobartunerstate.offset_spacing.value)
			widths = [ width+spacing if width>0 else 0 for width in widths ]
			
			# Apply user offsets
			posx = self.positionx + int(config.infobartunerstate.offset_horizontal.value) 
			posy = self.positiony + int(config.infobartunerstate.offset_vertical.value)
			height = self.height
			
			# Resize, move and show windows
			for win in sorted( self.entries.itervalues(), key=lambda x: (x.type, x.timeleft) ):
			#for pos, win in enumerate( sorted( self.entries.itervalues(), key=lambda x: (x.type, x.timeleft) ) ):
				win.reorder( widths )
				win.move( posx, posy )
				posy += height
				# Show windows
				win.show()
	
	def hide(self):
		if self.hideTimer.isActive():
			self.hideTimer.stop()
		self.hideTimer.start( 10, True )

	def tunerHide(self):
		for win in self.entries.itervalues():
			win.hide()

	def close(self):
		recoverInfoBar()
		removeExtension()
		self.unbindInfoBar()
		self.removeEvents()
		self.hide()
		for id, win in self.entries.items():
			self.session.deleteDialog(win)
			del self.entries[id]
		from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
		global gInfoBarTunerState
		gInfoBarTunerState = None


#######################################################
# Base screen class, contains all skin relevant parts
class TunerStateBase(Screen):
	# Skin will only be read once
	skinfile = "/usr/lib/enigma2/python/Plugins/Extensions/InfoBarTunerState/skin.xml" 
	skin = open(skinfile).read()
	
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "TunerState"
		
		self["Background"] = Pixmap()
		self["Type"] = MultiPixmap()
		self["Progress"] = ProgressBar()
		
		for i in xrange( len( config.infobartunerstate.fields.dict() ) ):
			self[ "Field" + str(i) ] = Label()
		
		self.padding = 0
		self.spacing = 0
		
		self.fields = []
		self.widths = []

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

	def reorder(self, widths):
		# Get initial offset position and apply user offset
		px = self.padding + int(config.infobartunerstate.offset_padding.value)
		py = 0
		sh = self.instance.size().height()
		for field, width in zip( self.fields, widths):
			if field == "Progress":
				# Center the progress field vertically 
				y = int( ( sh - self[field].instance.size().height() ) / 2 )
				self[field].instance.move( ePoint(px, y) )
			else:
				self[field].instance.move( ePoint(px, py) )
			px += width
		
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
		
		self.closeTimer = eTimer()
		self.closeTimer.callback.append(self.close)
		
		self.onLayoutFinish.append(self.popup)

	def popup(self):
		self.onLayoutFinish.remove(self.popup)
		
		fields = []
		widths = []
		
		if not config.infobartunerstate.background_transparency.value:
			self["Background"].show()
		else:
			self["Background"].hide()
		
		self["Type"].setPixmapNum(3)
		fields.append( "Type" )
		widths.append( self["Type"].instance.size().width() )
		
		self["Progress"].hide()
		
		height = self.instance.size().height()
		for i, c in enumerate( config.infobartunerstate.fields.dict().itervalues() ):
			field = "Field"+str(i)
			
			if field == "Field0":
				self[field].setText( str(self.name) )
			
			width = self[field].instance.calculateSize().width()
			self[field].instance.resize( eSize(width, height) )
			
			fields.append(field)
			widths.append( width )
		
		spacing = self.spacing + int(config.infobartunerstate.offset_spacing.value)
		widths = [ width+spacing if width>0 else 0 for width in widths ]
		
		self.fields = fields
		self.widths = widths
		
		posx = self.instance.position().x() + int(config.infobartunerstate.offset_horizontal.value) 
		posy = self.instance.position().y() + int(config.infobartunerstate.offset_vertical.value)
		
		self.reorder( widths )
		self.move( posx, posy )
		
		#self.closeTimer.startLongTimer( int(config.infobartunerstate.popup_time.value) or int(config.usage.infobar_timeout.index) or 5 )
		self.closeTimer.startLongTimer( int(config.usage.infobar_timeout.index) or 5 )

	def close(self):
		self.hide()
		from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
		global gInfoBarTunerState
		gInfoBarTunerState.session.deleteDialog(self)
		gInfoBarTunerState.info = None


#######################################################
# Displaying screen class, every entry is an instance of this class
class TunerState(TunerStateBase):
	def __init__(self, session, type, tuner, tunertype, name="", number="", channel="", filename="", client="", ip="", port=""):
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

	def updateType(self, type):
		if self.type != type:
			self.type = type
			if self.type == Finished:
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
		# Time and progress
		now = time()
		begin = self.begin
		
		timeelapsed = now - begin
		self.timeelapsed = math.ceil( ( timeelapsed ) / 60.0 )
		
		if not self.endless and self.end:
			end = self.end
			
			timeleft = end - now
			if timeleft < 0:
				timeleft = None
				
			duration = end - begin
			if duration > 0:
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
				duration = None
				progress = None
			
			self.duration = duration and math.ceil( ( duration ) / 60.0 )
			
			self.timeleft = timeleft and math.ceil( ( timeleft ) / 60.0 )
			self.progress = int( progress )
		
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
		fields = []
		widths = []
		
		# Set background transparency
		if not config.infobartunerstate.background_transparency.value:
			self["Background"].show()
		else:
			self["Background"].hide()
		
		self["Type"].hide()
		self["Progress"].hide()
		
		for i, c in enumerate( config.infobartunerstate.fields.dict().itervalues() ):
			field = "Field"+str(i)
			content = c.value
			text = ""
			
			if content == "TypeIcon":
				self["Type"].show()
				if self.type == Record:
					self["Type"].setPixmapNum(0)
				elif self.type == Stream:
					self["Type"].setPixmapNum(1)
				elif self.type == Finished:
					self["Type"].setPixmapNum(2)
				
				# No resize necessary
				fields.append( "Type" )
				widths.append( self["Type"].instance.size().width() )
			
			elif content == "TypeText":
				if self.type == Record:
					text = _("Record")
				elif self.type == Stream:
					text = _("Stream")
				elif self.type == Finished:
					text = _("Finished")
			
			elif content == "Tuner":
				if self.tuner:
					text = self.tuner
			
			elif content == "TunerType":
				if self.tunertype:
					text = self.tunertype
			
			elif content == "Number":
				if self.number is not None:
					text = _("%d") % ( self.number )
			
			elif content == "Channel":
				text = self.channel
			
			elif content == "Name":
				text = self.name
				#TODO update name for streams
			
			elif content == "TimeLeft":
				if not self.endless:
					if self.timeleft is not None:
						# Show timeleft recording time
						text = _("%d Min") % ( self.timeleft )
				else: 
					# Add infinity symbol for indefinitely recordings
					text = INFINITY
			
			elif content == "TimeElapsed":
				if self.timeelapsed is not None:
					text = _("%d Min") % ( self.timeelapsed )
			
			elif content == "TimeLeftDuration":
				# Calculate timeleft minutes
				if not self.endless:
					if self.type == Finished:
						if self.duration is not None:
							# Show recording length
							text = _("%d Min") % ( self.duration )
					elif self.timeleft is not None:
						# Show timeleft recording time
						text = _("%d Min") % ( self.timeleft )
				else: 
					# Add infinity symbol for indefinitely recordings
					text = INFINITY
			
			elif content == "Begin":
				lbegin = self.begin and localtime( self.begin )
				text = lbegin and strftime( config.infobartunerstate.time_format.value, lbegin )
			
			elif content == "End":
				lend = self.end and localtime( self.end )
				text = lend and strftime( config.infobartunerstate.time_format.value, lend )
			
			elif content == "Duration":
				if self.duration is not None:
					text = _("%d Min") % ( self.duration )
			
			elif content == "TimerProgressText":
				if self.progress is not None:
					text = _("%d %%") % ( self.progress )
			
			elif content == "TimerProgressGraphical":
				if self.progress is not None:
					self["Progress"].setValue( self.progress )
					self["Progress"].show()
					
				# No resize necessary
				fields.append( "Progress" )
				if not self.endless:
					widths.append( self["Progress"].instance.size().width() )
				else:
					widths.append( 0 )
			
			elif content == "TimerDestination":
				text = self.destination
			
			elif content == "StreamClient":
				text = self.client or self.ip
			
			elif content == "StreamClientPort":
				if self.port:
					text = self.client or self.ip
					text += ":" + str(self.port)
			
			elif content == "DestinationStreamClient":
				text = self.destination or self.client or self.ip
			
			elif content == "FileSize":
				if self.filesize  is not None:
					text = _("%d MB") % ( self.filesize )
			
			elif content == "FreeSpace":
				if self.freespace is not None:
					text = _("%d GB") % ( self.freespace )
			
			elif content == "None":
				# text is already initialized with ""
				pass
			
			# Set text, append field, resize field and append width
			self[field].setText( text )
			fields.append( field )
			
			width = self[field].instance.calculateSize().width()
			self[field].instance.resize( eSize(width, height) )
			
			widths.append( width )
			
		self.fields = fields
		self.widths = widths

	def remove(self):
		self.toberemoved = True 


#######################################################
# Global helper functions
def getTimer(strtimer):
	#for timer in self.session.nav.RecordTimer.timer_list + self.session.nav.RecordTimer.processed_timers:
	for timer in NavigationInstance.instance.RecordTimer.timer_list + NavigationInstance.instance.RecordTimer.processed_timers:
		if str(timer) == strtimer:
			return timer
	return None

def getStream(id):
	try:
		from Plugins.Extensions.WebInterface.WebScreens import streamingScreens 
	except:
		streamingScreens = []
	
	for stream in streamingScreens:
		if stream:
			if id == str(stream.screenIndex) + str(stream.clientIP):
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
