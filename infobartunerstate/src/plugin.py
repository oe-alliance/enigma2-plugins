#######################################################################
#
#    InfoBar Tuner State for Enigma-2
#    Vesion 0.8.1
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
import socket
import sys

from collections import defaultdict
from operator import attrgetter, itemgetter
from itertools import izip_longest as zip_longest # py3k

from Components.ActionMap import ActionMap
from Components.ActionMap import HelpableActionMap
from Components.Button import Button
from Components.config import *
from Components.ConfigList import ConfigListScreen
from Components.GUISkin import GUISkin
from Components.Label import Label
from Components.Language import *
from Components.Pixmap import Pixmap, MultiPixmap
from Components.ProgressBar import ProgressBar
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Sources.StaticText import StaticText

from Screens.InfoBar import InfoBar
from Screens.InfoBarGenerics import InfoBarShowHide
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from ServiceReference import ServiceReference
from Plugins.Plugin import PluginDescriptor
from time import time, localtime, strftime

from enigma import iServiceInformation, ePoint, eSize, getDesktop, iFrontendInformation
from enigma import eTimer
from enigma import iPlayableService, iRecordableService
from enigma import eDVBResourceManager, eActionMap, eListboxPythonMultiContent, eListboxPythonStringContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, eEPGCache, eServiceCenter, eServiceReference

# GUI (Summary)
from Screens.Setup import SetupSummary

from skin import parseColor, parseFont

from netstat import netstat

NAME = _("InfoBar Tuner State") 
DESCRIPTION = _("Show InfoBar Tuner State")
VERSION = "V0.8.1"
INFINITY =  u"\u221E".encode("utf-8")
#TODO About


# Globals
gInfoBarTunerState = None
InfoBarShow = None
InfoBarHide = None

# Type Enum
Record, Stream, Finished, INFO = range( 4 )

# Config choices
field_choices = [	
									("TypeIcon",								_("Type (Icon)")),
									("TypeText",								_("Type (Text)")),
									("Tuner",										_("Tuner")),
									("TunerType",								_("Tuner Type")),
									("Number",									_("Channel Number")),
									("Channel",									_("Channel Name")),
									("Name",										_("Name")),
									("TimeLeftDuration",				_("Time Left / Duration")),
									("TimeLeft",								_("Time Left")),
									("TimeElapsed",							_("Time Elapsed")),
									("Begin",										_("Begin")),
									("End",											_("End")),
									("Duration",								_("Duration")),
									("TimerProgressGraphical",	_("Timer Progress (Graphical)")),  #TODO howto do for file streams
									("TimerProgressText",				_("Timer Progress (Text)")),  #TODO howto do for file streams
									("TimerDestination",				_("Destination")),		#TODO howto do for file streams
									("StreamClient",						_("Stream Client")),
									("DestinationStreamClient",	_("Destination / Client")),
									#Throughput
									#Overall transfer
									("FileSize",								_("File Size")),
									("FreeSpace",								_("Free Space")),
									("None",										_("None")),
								]

date_choices = [	
									("%H:%M",							_("HH:MM")),
									("%d.%m %H:%M",				_("DD.MM HH:MM")),
									("%m/%d %H:%M",				_("MM/DD HH:MM")),
									("%d.%m.%Y %H:%M",		_("DD.MM.YYYY HH:MM")),
									("%Y/%m/%d %H:%M",		_("YYYY/MM/DD HH:MM")),
								]

# Config options
config.infobartunerstate                           = ConfigSubsection()

config.infobartunerstate.about                     = ConfigNothing()
config.infobartunerstate.enabled                   = ConfigEnableDisable(default = True)					#TODO needs a restart
config.infobartunerstate.extensions_menu           = ConfigYesNo(default = True)
#config.infobartunerstate.popup_time                = ConfigSelectionNumber(0, 10, 1, default = 5)
#Todo item enabler
#Show records
#Show streams

config.infobartunerstate.show_infobar              = ConfigYesNo(default = True)
config.infobartunerstate.show_events               = ConfigYesNo(default = True)		#TODO Show on start, end, start/end
config.infobartunerstate.show_overwrite            = ConfigYesNo(default = False)		# Show with MoviePlayer only is actually not possible

config.infobartunerstate.time_format               = ConfigSelection(default = "%H:%M", choices = date_choices)
config.infobartunerstate.number_finished_records   = ConfigSelectionNumber(0, 10, 1, default = 5)
config.infobartunerstate.timeout_finished_records  = ConfigSelectionNumber(0, 600, 10, default = 60)

config.infobartunerstate.fields                    = ConfigSubsection()
config.infobartunerstate.fields.a                  = ConfigSelection(default = "TypeIcon", choices = field_choices)
config.infobartunerstate.fields.b                  = ConfigSelection(default = "Tuner", choices = field_choices)
config.infobartunerstate.fields.c                  = ConfigSelection(default = "Number", choices = field_choices)
config.infobartunerstate.fields.d                  = ConfigSelection(default = "Channel", choices = field_choices)
config.infobartunerstate.fields.e                  = ConfigSelection(default = "Name", choices = field_choices)
config.infobartunerstate.fields.f                  = ConfigSelection(default = "TimerProgressGraphical", choices = field_choices)
config.infobartunerstate.fields.g                  = ConfigSelection(default = "TimeLeftDuration", choices = field_choices)
config.infobartunerstate.fields.h                  = ConfigSelection(default = "StreamClient", choices = field_choices)
config.infobartunerstate.fields.i                  = ConfigSelection(default = "None", choices = field_choices)
config.infobartunerstate.fields.j                  = ConfigSelection(default = "None", choices = field_choices)

config.infobartunerstate.offset_horizontal         = ConfigSelectionNumber(-1000, 1000, 1, default = 0)
config.infobartunerstate.offset_vertical           = ConfigSelectionNumber(-1000, 1000, 1, default = 0)
config.infobartunerstate.offset_content            = ConfigSelectionNumber(-1000, 1000, 1, default = 0)

config.infobartunerstate.background_transparency   = ConfigYesNo(default = False)


#######################################################
# Plugin main function
def Plugins(**kwargs):
	#TODO localeInit()
	
	descriptors = []
	
	if config.infobartunerstate.enabled.value:
		# AutoStart and SessionStart
		descriptors.append( PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, fnc = start, needsRestart = False) )
		descriptors.append( PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = start, needsRestart = False) )
		if config.infobartunerstate.extensions_menu.value:
			descriptors.append( PluginDescriptor(name = NAME, description = DESCRIPTION, where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = extension, needsRestart = False) )
	#TODO Extension List show InfoBarTunerState ?
	
	#TODO icon
	descriptors.append( PluginDescriptor(name = NAME, description = "InfoBar Tuner State " +_("configuration"), where = PluginDescriptor.WHERE_PLUGINMENU, fnc = setup, needsRestart = False) ) #icon = "/EnhancedMovieCenter.png"

	return descriptors


#######################################################
# Plugin menu
def setup(session, **kwargs):
	#TODO config
	# Overwrite Skin Position
	# Show Live TV Tuners PiP LiveStream FileStream
	# alltime permanent display, needs an dynamic update service
	# Always display at least Nothing running
	# show free tuner with dvb-type
	# Used disk size
	# Event popup timeout
	# Feldbreitenbegrenzung fuer Namen ...
	# Streaming amount of data
	# Display next x timers also if deactivated
	try:
		session.open(InfoBarTunerStateMenu)
	except Exception, e:
		print "InfoBarTunerStateMenu exception " + str(e)
		import traceback
		traceback.print_stack(None, file=sys.stdout)


#######################################################
# Config menu screen
class InfoBarTunerStateMenu(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = [ "InfoBarTunerStateMenu", "Setup" ]
		
		# Summary
		self.setup_title = _("InfoBarTunerStateMenu Configuration ") + VERSION
		self.onChangedEntry = []
		
		# Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		
		# Define Actions
		self["custom_actions"] = ActionMap(["SetupActions", "ChannelSelectBaseActions"],
		{
			"cancel":				self.keyCancel,
			"save":					self.keySave,
			"nextBouquet":	self.pageUp,
			"prevBouquet":	self.pageDown,
		}, -2) # higher priority
		
		# Initialize Configuration part
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)
		
		self.config = []
		self.defineConfig()
		self.createConfig()
		
		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.layoutFinished)

	def defineConfig(self):
		
		separator = "".ljust(250,"-")
		separatorE2Usage = "- E2 "+_("Usage")+" "
		separatorE2Usage = separatorE2Usage.ljust(250-len(separatorE2Usage),"-")
		
#         _config list entry
#         _                                                     , config element
		self.config = [
			#(  _("About")                                             , config.infobartunerstate.about ),
			
			(  _("Enable InfoBarTunerState")                          , config.infobartunerstate.enabled ),
			(  separator                                              , config.infobartunerstate.about ),
			(  _("Add to extension menu")                             , config.infobartunerstate.extensions_menu ),
#			(  _("Pop-Up time in seconds")                            , config.infobartunerstate.popup_time ),
			(  _("Show and hide with InfoBar")                        , config.infobartunerstate.show_infobar ),
			(  _("Show on events")                                    , config.infobartunerstate.show_events ),
			(  _("MoviePlayer integration")                           , config.infobartunerstate.show_overwrite ),
			(  _("Time format")                                       , config.infobartunerstate.time_format ),
			(  _("Number of finished records in list")                , config.infobartunerstate.number_finished_records ),
			(  _("Number of seconds for displaying finished records") , config.infobartunerstate.timeout_finished_records ),
			(  separator                                              , config.infobartunerstate.about ),
		]
		
		for i, configinfobartunerstatefield in enumerate( config.infobartunerstate.fields.dict().itervalues() ):
			self.config.append(
			(  _("Field %d content") % (i)                            , configinfobartunerstatefield )
			)
		
		self.config.extend( [
			(  separator                                              , config.infobartunerstate.about ),
			(  _("Horizontal offset in pixel")                        , config.infobartunerstate.offset_horizontal ),
			(  _("Vertical offset in pixel")                          , config.infobartunerstate.offset_vertical ),
			(  _("Content offset in pixel")                           , config.infobartunerstate.offset_content ),
			(  _("Background transparency")                           , config.infobartunerstate.background_transparency ),
		] )
		
		self.config.extend( [
			(  separatorE2Usage                                       , config.infobartunerstate.about ),
			(  _("Infobar timeout")                                   , config.usage.infobar_timeout ),
			(  _("Show Message when Recording starts")                , config.usage.show_message_when_recording_starts ),
			
		] )

	def createConfig(self):
		list = []
		for conf in self.config:
			# 0 entry text
			# 1 variable
			# 2 validation
			list.append( getConfigListEntry( conf[0], conf[1]) )
		self.list = list
		self["config"].setList(self.list)

	def layoutFinished(self):
		self.setTitle(self.setup_title)

	def changed(self):
		for x in self.onChangedEntry:
			x()
		#self.createConfig()

	def close(self):
		# Check field configuration
		fieldicon = []
		fieldprogress = []
		text = ""
		for i, c in enumerate( config.infobartunerstate.fields.dict().itervalues() ):
			if c.value == "TypeIcon":
				fieldicon.append( i )
			if c.value == "TimerProgressGraphical":
				fieldprogress.append( i )
		
		if len(fieldicon) > 1:
			text += _("Only one Icon field allowed:") + "\n" \
							+ "\n".join(["Field " + (str(f)) for f in fieldicon])
		
		if len(fieldprogress) > 1:
			if text: text += "\n\n"
			text += _("Only one Graphical Progress field allowed:") + "\n" \
							+ "\n".join(["Field " + (str(f)) for f in fieldprogress])
		
		if text:
			self.session.open(MessageBox, text, MessageBox.TYPE_ERROR, 3)
			return
		
		# Overwrite Screen close function to handle new config
		global gInfoBarTunerState
		if config.infobartunerstate.enabled.value:
			# Plugin should be enabled
			#TODO use a separate init function similar to the close
			if not gInfoBarTunerState:
				# Plugin is not active - enable it
				gInfoBarTunerState = InfoBarTunerState(self.session)
			
			if gInfoBarTunerState:
				
				# Handle InfoBar overwrite
				if config.infobartunerstate.show_overwrite.value:
					overwriteInfoBar()
				else:
					recoverInfoBar()
				
				# Handle extension menu integration
				if config.infobartunerstate.extensions_menu.value:
					# Add to extension menu
					addExtension()
				else:
					# Remove from extension menu
					removeExtension()
				
				# Handle show with InfoBar
				if config.infobartunerstate.show_infobar.value:
					gInfoBarTunerState.bindInfoBar()
				else:
					gInfoBarTunerState.unbindInfoBar()
				
				#TODO actually not possible to do this, because these events provides the relevant information
				#if config.infobartunerstate.show_events.value:
				#	gInfoBarTunerState.appendEvents()
				#else:
				#	gInfoBarTunerState.removeEvents()
				
							# Check for actual events
				gInfoBarTunerState.updateRecordTimer()
				gInfoBarTunerState.updateStreams()
		else:
			# Plugin should be disabled
			if gInfoBarTunerState:
				# Plugin is active, disable it
				gInfoBarTunerState.close()
		
		# Call baseclass function
		Screen.close(self)

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def pageUp(self):
		self["config"].instance.moveSelection(self["config"].instance.pageUp)

	def pageDown(self):
		self["config"].instance.moveSelection(self["config"].instance.pageDown)


#######################################################
# Autostart and Sessionstart
def start(reason, **kwargs):
	#print "InfoBarTunerState autostart "
	#print str(reason)
	#print str(kwargs)
	if reason == 0: # start
		if kwargs.has_key("session"):
			if config.infobartunerstate.enabled.value:
				global gInfoBarTunerState
				session = kwargs["session"]
				gInfoBarTunerState = InfoBarTunerState(session)


#######################################################
# Extension Menu
def extension(session, **kwargs):
	global gInfoBarTunerState
	if gInfoBarTunerState:
		if gInfoBarTunerState.entries:
			# There are active entries
			gInfoBarTunerState.show(True)
		else:
			# No entries available
			#session.open( TunerStateInfo, INFO, _("Nothing running") )
			#gInfoBarTunerState.session.open( TunerStateInfo, INFO, _("Nothing running") )
			gInfoBarTunerState.info = gInfoBarTunerState.session.instantiateDialog( TunerStateInfo, INFO, _("Nothing running") )
			gInfoBarTunerState.info.show()
	else:
		# No InfoBarTunerState Instance running
		session.open(MessageBox, _("InfoBarTunerState is disabled"), MessageBox.TYPE_INFO, 3)


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

def recoverInfoBar():
	global InfoBarShow, InfoBarHide
	if InfoBarShow:
		InfoBarShowHide._InfoBarShowHide__onShow = InfoBarShow
		InfoBarShow = None
	if InfoBarHide:
		InfoBarShowHide._InfoBarShowHide__onHide = InfoBarHide
		InfoBarHide = None

def InfoBarShowTunerState(self):
	global gInfoBarTunerState, InfoBarShow
	if InfoBarShow:
		InfoBarShow(self)
	if gInfoBarTunerState:
		gInfoBarTunerState.show()

def InfoBarHideTunerState(self):
	global gInfoBarTunerState, InfoBarHide
	if InfoBarHide:
		InfoBarHide(self)
	if gInfoBarTunerState:
		gInfoBarTunerState.tunerHide()


#######################################################
# Extension menu
def addExtension():
	# Add to extension menu
	from Components.PluginComponent import plugins
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
		
	#def test(self, event):
	#	print "InfoBarTuner test " + str(event)

	def appendEvents(self):
		# Recording Events
		#TEST If we append our function, we will never see the timer state StateEnded for repeating timer
		#self.session.nav.RecordTimer.on_state_change.insert(0, self.__onRecordingEvent)
		self.session.nav.RecordTimer.on_state_change.append(self.__onRecordingEvent)
		# Streaming Events
		self.session.nav.record_event.append(self.__onStreamingEvent)
		# Zapping Events
		#self.session.nav.event.append(self.__onPlayableEvent)
		#res_mgr = eDVBResourceManager.getInstance()
		#if res_mgr:
		#	res_mgr.frontendUseMaskChanged.get().append(self.__onTunerUseMaskChanged)

	def removeEvents(self):
		# Recording Events
		# If we append our function, we will never see the timer state StateEnded for repeating timer
		if self.__onRecordingEvent in self.session.nav.RecordTimer.on_state_change:
			self.session.nav.RecordTimer.on_state_change.remove(self.__onRecordingEvent)
		# Streaming Events
		if self.__onStreamingEvent in self.session.nav.record_event:
			self.session.nav.record_event.remove(self.__onStreamingEvent)

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
				
				# Add current running records / streams
				# We do it right here to ensure the InfoBar is intantiated
				self.updateRecordTimer()
				self.updateStreams()

	def unbindInfoBar(self):
		if self.infobar:
			if hasattr(self.infobar, "onShow"):
				if self.__onInfoBarEventShow in self.infobar.onShow:
					self.infobar.onShow.remove(self.__onInfoBarEventShow)
			if hasattr(self.infobar, "onHide"):
				if self.__onInfoBarEventHide in self.infobar.onHide:
					self.infobar.onHide.remove(self.__onInfoBarEventHide)

	def __onTunerUseMaskChanged(self, mask):
		#print "__onTunerUseMaskChanged    " +str(mask)
		pass

	def __onInfoBarEventShow(self):
		#TODO check recordings streams ...
		if self.hideTimer.isActive():
			self.hideTimer.stop()
		self.show()

	def __onInfoBarEventHide(self):
		self.tunerHide()

	def __onRecordingEvent(self, timer):
		if not timer.justplay:
			if timer.state == timer.StatePrepared:
				pass
			
			elif timer.state == timer.StateRunning:
				id = str( timer )
				if id not in self.entries:
					#channel = timer.service_ref.getServiceName()
					tuner, tunertype = getTuner(timer.record_service)
					#name = timer.name		# No EPG data available: name = instant record
						
					#TEST Bug Repeating timer blocking tuner and are not marked as finished
					#timer.timeChanged = self.__OnTimeChanged
					
					name = timer.name
					service_ref = timer.service_ref
					# Is this really necessary?
					try: timer.Filename
					except: timer.calculateFilename()
					filename = timer.Filename
					
					del timer
					win = self.session.instantiateDialog(TunerState, Record, tuner, tunertype, name, service_ref, filename)
					self.entries[id] = win
					if config.infobartunerstate.show_events.value:
						self.show(True)
			
			# Finished repeating timer will report the state StateEndend+1 
			elif timer.state >= timer.StateEnded:
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

	def __onStreamingEvent(self, rec_service, event, getip=True):
		if event == iRecordableService.evStart:
			#TODO Test objects
			print "iRecordableService.evStart "
			#print "iRecordableService.evStart " + str(event)
			# Delete references to avoid blocking tuners
			#del rec_service
			del event
			
			try:
				from Plugins.Extensions.WebInterface.WebScreens import streamingScreens
			except:
				streamingScreens = []
			
			#TODO file streaming actually not working - getting no event
			for stream in streamingScreens:
				# Check if screen exists
				if stream:
					
					#TODO find a filestream identifier
#					print stream.request.path
#					print stream.request.uri
#					print stream.request.site
#					print stream.request.content
#					print str('file' in stream.request.args) 
					
					# Check if screen is not a filestream and not marked as known
					if 'file' not in stream.request.args and not ( hasattr(stream, 'streamid') ):
						# Extract parameters
						tuner, tunertype = getTuner( stream.getRecordService() ) 
						ref = stream.getRecordServiceRef()
						
						ip, port, id, host, client = "", "", "", "", ""
						
						# Workaround to retrieve the client ip
						# Change later and use the WebScreens getActiveStreamingClients if implemented
						for conn in netstat(getstate='ESTABLISHED', getuid=False, getpid=False, readable=False):
							# Check if it is a streaming connection
							if conn[3] == '8001':
								ip = conn[4]
								port = conn[5]
								# Check if ip and port is already known
								id = str(ip) + ":" + str(port)
								if id not in self.entries:
									stream.streamid = id
									#stream.ip = ip
									#stream.port = port
									#rec_service.id = id not working
									break
						else:
							# No new connection found
							del rec_service
							del stream
							return
						if not getip:
							## Dummy id
							##id = "UnknownStream" + str(stream.screenIndex)
							ip = ""
							port = ""
						del rec_service
						del stream
						epg = eEPGCache.getInstance()
						event = epg and epg.lookupEventTime(ref, -1, 0)
						if event: 
							name = event.getEventName()
						else:
							name = ""
							#TODO check file streaming
						
						service_ref = ServiceReference(ref)
						filename = "" #TODO file streaming - read meta eit
						
						if getip:
							try:
								host = socket.gethostbyaddr( ip )
								client = host and host[0].split('.')[0]
							except socket.herror, x:
								pass
							
						win = self.session.instantiateDialog(TunerState, Stream, tuner, tunertype, name, service_ref, filename, client, ip, port)
						self.entries[id] = win
						if config.infobartunerstate.show_events.value:
							self.show(True)
						break
						
				#print stream.getRecordService()  # iRecordableService
				
				#print stream.getRecordServiceRef()  # eServiceReference
				
#				if hasattr( stream, 'request' ):
#http://twistedmatrix.com/documents/current/api/twisted.web.http.Request.html
#					print stream.request
#					#print "request TODO dir info " + str(dir(stream.request))
#					#print "request TODO vars info " + str(vars(stream.request))
#				print stream.request.getRequestHostname()
#				print stream.request.getHost() #.host or .getHost()
#				print stream.request.getClientIP()	#.client
#				print stream.request.getClient()	#.client
#				print stream.request.args
					##self.transport.getPeer()
					##mind.broker.transport.getPeer()
#					#print str(stream.request.host.port)
#					print stream.request.method
#					print stream.request.path
#					print stream.request.uri
#					print stream.request.client
#					print stream.request.requestHeaders
#					print stream.request.site
#					print stream.request.content
#				if stream.has_key( 'StreamService' ):
#					print stream["StreamService"]

			#TEST3 if filestream
			#http://schwerkraft.elitedvb.net/plugins/scmgit/cgi-bin/gitweb.cgi?p=enigma2-plugins/enigma2-plugins.git;a=blob;f=webinterface/src/WebChilds/FileStreamer.py#l10
# 			if 'dir' in request.args:
# 				dir = unquote(request.args['dir'][0])
# 			elif 'root' in request.args:
# 				dir = unquote(request.args['root'][0])
# 			else:
# 				dir = ''
# 			if 'file' in request.args:                      
# 				filename = unquote(request.args["file"][0])
# 					path = dir + filename
# 					if not os_path.exists(path):
# 						path = "/hdd/movie/%s" % (filename)
				#TODO start eTimer handleEvent, id, type, tuner
		
		elif event == iRecordableService.evEnd:
			print "iRecordableService.evEnd"
			# Delete references to avoid blocking tuners
			#del rec_service
			del event
			del rec_service
			#if hasattr(rec_service, 'streamid') and rec_service.streamid:
			#	print rec_service.streamid
			#	id = rec_service.streamid
			#	del rec_service
			#	if id in self.entries:
			#		win = self.entries[id]
			#		if win.type == Stream:
			
			try:
				from Plugins.Extensions.WebInterface.WebScreens import streamingScreens 
			except:
				streamingScreens = []
			
			# Remove Finished Streams
			streamingIds = [ stream.streamid for stream in streamingScreens if stream and hasattr(stream, 'streamid') and stream.streamid]
			for id, win in self.entries.items():
				if win.type == Stream:
					if id not in streamingIds:
						
						begin = win.begin
						end = time()
						endless = False
						
						win.updateType( Finished )
						win.updateTimes( begin, end, endless )
						
						if config.infobartunerstate.show_events.value:
							self.show(True)

	def __onPlayableEvent(self, event):
		#TEST PiP
		#print "__onPlayableEvent    " + str(event)
		#TODO Filter events
		#self.show(True)
		# Rebind InfoBar Events
		#self.bindInfoBar()
		pass

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
		
		#TODO file streaming actually not working - getting no event
		for stream in streamingScreens:
			# Check if screen exists
			if stream:
				self.__onStreamingEvent(rec_service=stream.getRecordService(), event=iRecordableService.evStart, getip=False)

	def show(self, autohide=False):
		if self.showTimer.isActive():
			self.showTimer.stop()
		self.showTimer.start( 100, True )
		
		if autohide:
			# Start timer to avoid permanent displaying
			# Do not start timer if no timeout is configured
			idx = config.usage.infobar_timeout.index
			if idx:
				if self.hideTimer.isActive():
					self.hideTimer.stop()
				self.hideTimer.startLongTimer( int(idx) or 5 )

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
					#TODO Avolid blocking - do not use getTimer to update the timer times use timer.time_changed if possible
					timer = getTimer( id )
					if timer:
						#TODO Problem we don't find the finished timer anymore because it will be moved to the processed timers list ????
						begin = timer.begin
						end = timer.end
						endless = timer.autoincrease
						del timer
						
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
					#TODO Avolid blocking - do not use getStream to update the current name
					stream = getStream( id )
					if stream:
						ref = stream.getRecordServiceRef()
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
						
						win.updateName( name )
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
				else:
					# Type Finished
					win.update()
				
				# Calculate field width
				widths = map( lambda (w1, w2): max( w1, w2 ), zip_longest( widths, win.widths ) )
			
			# Calculate field spacing
			spacing  = self.spacing
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
	
	def tunerHide(self):
		if self.hideTimer.isActive():
			self.hideTimer.stop()
		for win in self.entries.itervalues():
			win.hide()

	def close(self):
		recoverInfoBar()
		removeExtension()
		self.unbindInfoBar()
		self.removeEvents()
		self.tunerHide()
		for id, win in self.entries.items():
			self.session.deleteDialog(win)
			del self.entries[id]
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
		px = self.padding + int(config.infobartunerstate.offset_content.value)
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
	def __init__(self, session, type, name):
		TunerStateBase.__init__(self, session)
		
		self.type = type
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
		
		spacing = self.spacing
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
		global gInfoBarTunerState
		gInfoBarTunerState.session.deleteDialog(self)
		gInfoBarTunerState.info = None

#######################################################
# Displaying screen class, every entry is an instance of this class
class TunerState(TunerStateBase):
	def __init__(self, session, type, tuner, tunertype, name="", service_ref=None, filename="", client="", ip="", port=""):
		TunerStateBase.__init__(self, session)
		
		self.toberemoved = False
		self.removeTimer = eTimer()
		self.removeTimer.callback.append(self.remove)
		
		self.type = type
		self.tuner = tuner
		self.tunertype = tunertype
		
		self.name = name
		
		self.number = service_ref and getNumber(service_ref.ref)
		self.channel = service_ref and service_ref.getServiceName()
		
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
					timeout = config.infobartunerstate.timeout_finished_records.value
					if timeout:
						self.removeTimer.startLongTimer( int( timeout ) or 5 )

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
		if stream and hasattr(stream, 'streamid') and stream.streamid:
			if id == stream.streamid:
				return stream
	return None

def getTuner(service):
	# service must be an instance of iPlayableService or iRecordableService
	feinfo = service and service.frontendInfo()
	data = feinfo and feinfo.getAll(False)
	number = data and data.get("tuner_number", -1)
	type = data and data.get("tuner_type", "")
	if number > -1:
		return ( chr( number + ord('A') ), type)
	else:
		return "", ""
	#TODO detect stream of HDD

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
		actbouquet = Servicelist.getRoot()
		#TODO get alternative for actbouquet
		if actbouquet:
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
	return None
