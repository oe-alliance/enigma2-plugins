#######################################################################
#
#    InfoBar Tuner State for Enigma-2
#    Vesion 0.7
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

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import *
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Language import *
from Components.Pixmap import Pixmap
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Sources.StaticText import StaticText

from Screens.InfoBar import InfoBar
from Screens.InfoBarGenerics import InfoBarShowHide
from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from time import time, localtime, strftime

from enigma import iServiceInformation, ePoint, eSize, getDesktop, iFrontendInformation

from enigma import eTimer

from enigma import iPlayableService, iRecordableService

from enigma import eDVBResourceManager, eActionMap, eListboxPythonMultiContent, eListboxPythonStringContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, eEPGCache, eServiceCenter, eServiceReference

# GUI (Summary)
from Screens.Setup import SetupSummary

from skin import parseColor, parseFont

#try:
#	# try to import EMC module to check for its existence
#	from Plugins.Extensions.EnhancedMovieCenter.EnhancedMovieCenter import EMCMediaCenter 
#except ImportError, ie:
#	class EMCMediaCenter: pass

Version = "V0.6.0"
#TODO About


# Globals
gInfoBarTunerState = None
InfoBarShow = None
InfoBarHide = None

field_choices = [	
									("Tuner",							_("Tuner")),
									("ChannelNumber",			_("Channel Number")),
									("ChannelName",				_("Channel Name")),
									("Name",							_("Name")),
									("TimeLeft",					_("Time Left")),
									("TimeElapsed",				_("Time Elapsed")),
									#("TimeLeftDuration",					_("Time Left / Duration")),
									("TimerBegin",				_("Timer Begin")),
									("TimerEnd",					_("Timer End")),
									("TimerDuration",			_("Timer Duration")),
									("Destination",				_("Destination")),
									("FileSize",					_("File Size")),
									("FreeSpace",					_("Free Space")),
									("None",							_("None")),
									#("Percent"						_("Percent")),		#TODO also graphically
								]

date_choices = [	
									("%H:%M",							_("HH:MM")),
									("%d.%m %H:%M",				_("DD.MM HH:MM")),
									("%m/%d %H:%M",				_("MM/DD HH:MM")),
									("%d.%m.%Y %H:%M",		_("DD.MM.YYYY HH:MM")),
									("%Y/%m/%d %H:%M",		_("YYYY/MM/DD HH:MM")),
								]

config.infobartunerstate                           = ConfigSubsection()

config.infobartunerstate.about                     = ConfigNothing()
config.infobartunerstate.enabled                   = ConfigEnableDisable(default = True)					#TODO needs a restart

config.infobartunerstate.show_infobar              = ConfigYesNo(default = True)
config.infobartunerstate.show_events               = ConfigYesNo(default = True)		#TODO Show on start, end, start/end
config.infobartunerstate.show_overwrite            = ConfigYesNo(default = False)

config.infobartunerstate.number_finished_records   = ConfigSelectionNumber(0, 10, 1, default = 5)
config.infobartunerstate.timeout_finished_records  = ConfigSelectionNumber(0, 600, 10, default = 60)

config.infobartunerstate.time_format               = ConfigSelection(default = "%H:%M", choices = date_choices)

#TODO Show Icon but what else should we show : 	text
config.infobartunerstate.fields                    = ConfigSubsection()
config.infobartunerstate.fields.a                  = ConfigSelection(default = "Tuner", choices = field_choices)
config.infobartunerstate.fields.b                  = ConfigSelection(default = "ChannelNumber", choices = field_choices)
config.infobartunerstate.fields.c                  = ConfigSelection(default = "ChannelName", choices = field_choices)
config.infobartunerstate.fields.d                  = ConfigSelection(default = "Name", choices = field_choices)
config.infobartunerstate.fields.e                  = ConfigSelection(default = "TimeLeft", choices = field_choices)
config.infobartunerstate.fields.f                  = ConfigSelection(default = "None", choices = field_choices)
config.infobartunerstate.fields.g                  = ConfigSelection(default = "None", choices = field_choices)
config.infobartunerstate.fields.h                  = ConfigSelection(default = "None", choices = field_choices)
config.infobartunerstate.fields.i                  = ConfigSelection(default = "None", choices = field_choices)
config.infobartunerstate.fields.j                  = ConfigSelection(default = "None", choices = field_choices)


def Plugins(**kwargs):
	
	#TODO localeInit()
	
	descriptors = []
	
	if config.infobartunerstate.enabled.value:
		# AutoStart and SessionStart
		descriptors.append( PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, fnc = start) )
		descriptors.append( PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = start) )
	
	#TODO Extension List show InfoBarTunerState ?
	
	#TODO icon
	descriptors.append( PluginDescriptor(name = "InfoBar Tuner State", description = "InfoBar Tuner State " +_("configuration"), where = PluginDescriptor.WHERE_PLUGINMENU, fnc = setup) ) #icon = "/EnhancedMovieCenter.png"

	return descriptors


def setup(session, **kwargs):
	#TODO config
	# Overwrite Skin Position
	# Show Live TV Tuners PiP Stream ...
	# Background: Transparent, Block, Dynamic(Farbverlauf)
	# Width: FullRow, Adapted/Fitting, Symmetrical
	#Rec A 2 RTL blabla 10min to /media/hdd/serien 
	#Rec A 2 RTL /media/hdd/serien/blabla 10min
	#alltime permanent display
	# destination ip only streams
	# show free tuner with dvb-type
	# Used disk size
	# Feldbreitenbegrenzung fuer Namen ...
	try:
		session.open(InfoBarTunerStateMenu)
	except Exception, e:
		print "InfoBarTunerStateMenu exception " + str(e)
		import traceback
		traceback.print_stack(None, file=sys.stdout)


class InfoBarTunerStateMenu(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = [ "InfoBarTunerStateMenu", "Setup" ]
		
		# Summary
		self.setup_title = _("InfoBarTunerStateMenu Configuration ") + Version
		self.onChangedEntry = []
		
		# Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		
		# Define Actions
		self["custom_actions"] = ActionMap(["SetupActions", "ChannelSelectBaseActions"],
		{
			"cancel": self.keyCancel,
			"save": self.keySave,
			"nextBouquet": self.pageUp,
			"prevBouquet": self.pageDown,
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
		seperatorE2Usage = "- E2 "+_("Usage")+" "
		seperatorE2Usage = seperatorE2Usage.ljust(250-len(seperatorE2Usage),"-")
		
#         _config list entry
#         _                                                     , config element
		self.config = [
			#(  _("About")                                             , config.infobartunerstate.about ),
			
			(  _("Enable InfoBarTunerState")                          , config.infobartunerstate.enabled ),
			(  separator                                              , config.infobartunerstate.about ),
			
			(  _("Show and hide with InfoBar")                        , config.infobartunerstate.show_infobar ),
			(  _("Show on Events")                                    , config.infobartunerstate.show_events ),
			(  _("MoviePlayer integration")                           , config.infobartunerstate.show_overwrite ),
			
			(  _("Number of finished records in list")                , config.infobartunerstate.number_finished_records ),
			(  _("Number of seconds for displaying finished records") , config.infobartunerstate.timeout_finished_records ),
			
			(  _("Time format")                                       , config.infobartunerstate.time_format ),
		]
		for i, configinfobartunerstatefield in enumerate( config.infobartunerstate.fields.dict().itervalues() ):
			self.config.append(
			(  _("Field %d content") % (i)                            , configinfobartunerstatefield )
			)
			
		self.config.extend( [	
			(  seperatorE2Usage                                       , config.infobartunerstate.about ),
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
		global gInfoBarTunerState
		# Overwrite Screen close function to handle new config
		if config.infobartunerstate.enabled.value:
			if not gInfoBarTunerState:
				# Plugin is not active, enable it
				gInfoBarTunerState = InfoBarTunerState(self.session)
			if gInfoBarTunerState:
				if config.infobartunerstate.show_overwrite.value:
					overwriteInfoBar()
				else:
					recoverInfoBar()
				if config.infobartunerstate.show_infobar.value:
					gInfoBarTunerState.bindInfoBar()
				else:
					gInfoBarTunerState.unbindInfoBar()
				#TODO actually not possible to do this
				#if config.infobartunerstate.show_events.value:
				#	gInfoBarTunerState.appendEvents()
				#else:
				#	gInfoBarTunerState.removeEvents()
				gInfoBarTunerState.updateRecordTimer()
				gInfoBarTunerState.updateStreams()
		else:
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
		gInfoBarTunerState.tunerShow()

def InfoBarHideTunerState(self):
	global gInfoBarTunerState, InfoBarHide
	if InfoBarHide:
		InfoBarHide(self)
	if gInfoBarTunerState:
		gInfoBarTunerState.tunerHide()


# Type Enum
RecordStarted, RecordFinished, Stream = range(3)


class InfoBarTunerState(Screen):		#DO I really have to use the Sceen class or is object enough
	def __init__(self, session):
		Screen.__init__(self, session)
		
		self.infobar = None
		
		self.hideTimer = eTimer()
		self.hideTimer.callback.append(self.tunerHide)
		
		#self.availTimer = eTimer()
		#self.availTimer.callback.append(self.tunerShow)
		
		self.forceBindInfoBarTimer = eTimer()
		self.forceBindInfoBarTimer.callback.append(self.bindInfoBar)
		
		self.tunerInfo = defaultdict(list)
		
		self.posy = getDesktop(0).size().height()
		
		self.appendEvents()
		
		#self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
		#	{
		#		iPlayableService.evStart: self.__onPlayableEvent,
		#		#iPlayableService.evEnd: self.bindInfoBar,
		#	})
		
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
		
		# Add current running records / streams
		self.updateRecordTimer()
		self.updateStreams()
		
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
		# If we append our function, we will never see the timer state StateEnded for repeating timer
		self.session.nav.RecordTimer.on_state_change.insert(0, self.__onRecordingEvent)
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
		print "InfoBarTunerState InfoBar.instance " + str(InfoBar.instance)
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
		#TODO not tested yet
		if self.infobar:
			if hasattr(self.infobar, "onShow"):
				if self.__onInfoBarEventShow in self.infobar.onShow:
					self.infobar.onShow.remove(self.__onInfoBarEventShow)
			if hasattr(self.infobar, "onHide"):
				if self.__onInfoBarEventHide in self.infobar.onHide:
					self.infobar.onHide.remove(self.__onInfoBarEventHide)

	def __onTunerUseMaskChanged(self, mask):
		print "__onTunerUseMaskChanged    " +str(mask)

	def __onInfoBarEventShow(self):
		#TODO check recordings streams ...
		if self.hideTimer.isActive():
			self.hideTimer.stop()
		self.tunerShow()

	def __onInfoBarEventHide(self):
		self.tunerHide()

	def __onRecordingEvent(self, timer):
		if timer.state == timer.StatePrepared:
			print "__onRecordingEventPrep    " +str(timer)
		elif timer.state == timer.StateRunning:	# timer.isRunning()
			if not timer.justplay:
				type = RecordStarted
				
				#TEST find unique record identifier
				print "__onRecordingEventRun    " +str(timer)
				print "__onRecordingEventRun    " +str(timer.eit)
				print "__onRecordingEventRun    " +str(timer.service_ref)
				print "__onRecordingEventRun    " +str(timer.service_ref.ref)
				#channel = timer.service_ref.getServiceName()
				tuner = getTuner(timer.record_service)
				#name = timer.name		# No EPG data available: name = instant record
					
				#TEST Bug Repeating timer blocking tuner and are not marked as finished
				#timer.timeChanged = self.__OnTimeChanged
				
				id = str(timer)
				if not id in self.tunerInfo:
					win = self.session.instantiateDialog(TunerState, type, tuner)
					self.tunerInfo[id] = win
					self.showWithTimer()
			
		#elif timer.state == timer.StateEnded:
		else:
			print "__onRecordingEventEnd    " +str(timer.state)  # Check state of finished repeating timers !!!!!!
			id = str(timer)
			if id in self.tunerInfo:
				win = self.tunerInfo[id]
				win.change( RecordFinished )
				self.showWithTimer()

	def __onStreamingEvent(self, rec_service, event):
		print "__onStreamingEvent2    " +str(event)
		print "__onStreamingEvent2    " +str(rec_service)
		if event == iRecordableService.evStart:
			type = Stream
			try:
				from Plugins.Extensions.WebInterface.WebScreens import streamingScreens
				#from Plugins.Extensions.WebInterface.WebComponents.Sources.RequestData import RequestData
			except:
				streamingScreens = []
			print streamingScreens
			print len(streamingScreens)
			for stream in streamingScreens:
				print stream.getRecordService()  # iRecordableService
				tuner = getTuner(stream.getRecordService())
				print tuner
				print stream.getRecordServiceRef()  # eServiceReference
				
				#TEST streamauth ON !!!!!

#				if hasattr( stream, 'request' ):
#http://twistedmatrix.com/documents/current/api/twisted.web.http.Request.html
#					print stream.request
#					#print "request TODO dir info " + str(dir(stream.request))
#					#print "request TODO vars info " + str(vars(stream.request))
##TODO Howto resolve hostname from ip
				print stream.request.getRequestHostname()
				print stream.request.getHost() #.host or .getHost()
				print stream.request.getClientIP()	#.client
				print stream.request.getClient()	#.client
				print stream.request.args
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
				#ServiceReference(stream.getRecordServiceRef())
#			#TEST1
#			print([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][0])
#			#TEST2
#			try:
#			    host=socket.gethostbyaddr("66.249.71.15")
#			    print "Primary hostname:"
#			    print "  " + host[0]
#			    print "Addresses:"
#			    for i in host[2]:
#			        print i
#			except socket.herror, x:
#			    print "Cann't find name:", x 
			#http://python.about.com/od/pythonstandardlibrary/qt/dnscheck.htm
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
		elif event == iRecordableService.evEnd:
			type = Stream
			try:
				from Plugins.Extensions.WebInterface.WebScreens import streamingScreens 
			except:
				streamingScreens = []
			for stream in streamingScreens:
				#Delete first second any difference !?
				print stream.getRecordService()  # iRecordableService
				tuner = getTuner(stream.getRecordService())
				print tuner
				print stream.getRecordServiceRef()  # eServiceReference

	def __onPlayableEvent(self, event):
		#TEST PiP
		print "__onPlayableEvent    " + str(event)
		#TODO Filter events
		#self.showWithTimer()
		# Rebind InfoBar Events
		#self.bindInfoBar()
		
	def __OnTimeChanged(self):
		#TODO Config show on timer time changed
		self.showWithTimer()

	def updateRecordTimer(self):
		for timer in NavigationInstance.instance.RecordTimer.timer_list:
			if timer.isRunning() and not timer.justplay:
				self.__onRecordingEvent(timer)

	def updateStreams(self):
		#TODO
		pass

	def showWithTimer(self):
		if config.infobartunerstate.show_events.value:
			#if self.availTimer.isActive():
			#	self.availTimer.stop()
			#self.availTimer.startLongTimer( 10 )
			
			# Start timer to avoid permanent displaying
			# Do not start timer if no timeout is configured
			idx = config.usage.infobar_timeout.index
			if idx:
				if self.hideTimer.isActive():
					self.hideTimer.stop()
				self.hideTimer.startLongTimer( config.usage.infobar_timeout.index or 1 )
			
			# Show windows
			self.tunerShow()
	
	def tunerShow(self):
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
		for id, win in sorted( self.tunerInfo.items(), key=lambda x: (x[1].end), reverse=True ):
			if win.type == RecordFinished:
				numberfinished += 1
			if win.toberemoved == True \
				or win.type == RecordFinished and numberfinished > int( config.infobartunerstate.number_finished_records.value ):
				# Delete Stopped Timers
				self.session.deleteDialog(win)
				del self.tunerInfo[id]
		
		# Update windows
		# Dynamic column resizing and repositioning
		#TODO get Initial Position and Size from skin
		posy = self.posy
		posx, sizeh = 0, 0
		width = [0] * len( config.infobartunerstate.fields.dict() )
		for id, win in self.tunerInfo.items():
			timer = getTimer( id )
			if timer:
				win.update( timer )
			else:
				print "InfoBarTunerState Warning no timer found"
				#TODO Update without timer ???
			if posx == 0:
				posx = win.instance.position().x()
				sizeh = win.instance.size().height()
			posy = min( win.instance.position().y(), posy )
				
			#TODO width icon as pos offset ?
			width = map(lambda (i, w): max( win[ "Field"+str(i) ].instance.calculateSize().width(), w ), enumerate( width ) )
		
		self.posy = posy
		
		# Spacing between the column entries
		width = [w+15 if w>0 else 0 for w in width]
		
		# Resize, move and show windows
		for win in sorted( self.tunerInfo.itervalues(), key=lambda x: (x.type, x.timeleft) ):
			win.resize(width)
			win.instance.move(ePoint(posx, posy))
			posy += sizeh
			# Show windows
			win.show()
	
	def tunerHide(self):
		if self.hideTimer.isActive():
			self.hideTimer.stop()
		for win in self.tunerInfo.itervalues():
			win.hide()

	def close(self):
		#TODO not tested yet it will be used for dynamic disabling the plugin
		recoverInfoBar()
		self.unbindInfoBar()
		self.removeEvents()
		self.tunerHide()
		for id, win in self.tunerInfo.items():
			self.session.deleteDialog(win)
			del self.tunerInfo[id]
		Screen.close(self)
		#TODO before or after Screen.close ????
		global gInfoBarTunerState
		gInfoBarTunerState = None


class TunerState(Screen):
	skinfile = "/usr/lib/enigma2/python/Plugins/Extensions/InfoBarTunerState/skin.xml" 
	skin = open(skinfile).read()

	def __init__(self, session, type, tuner):
		
		Screen.__init__(self, session)
		
		self.toberemoved = False
		self.removeTimer = eTimer()
		self.removeTimer.callback.append(self.remove)
		
		self["Background"] = Pixmap()
		self["Record"] = Pixmap()
		self["Finished"] = Pixmap()
		self["Stream"] = Pixmap()
		
		for i in xrange( len( config.infobartunerstate.fields.dict() ) ):
			self[ "Field" + str(i) ] = Label()
		
		#TODO Avoid multiple data storin, but these are needed for the sorting and performance reasons
		self.type = type
		self.tuner = tuner
		self.channelnumber = -1
		
		self.timeleft = 0
		self.duration = 0
		self.end = 0
		
		#self.channelname = ""
		#self.name = ""
		#self.destination = ""
		
		self.updateType()
		
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

	def change(self, type):
		if self.type != type:
			self.type = type
			self.updateType()

	def updateType(self):
		if self.type == RecordStarted:
			self["Record"].show()
			self["Finished"].hide()
			self["Stream"].hide()
		elif self.type == RecordFinished:
			self["Record"].hide()
			self["Finished"].show()
			self["Stream"].hide()
			self.tuner = _("-")
			# Check if timer is already started
			if not self.removeTimer.isActive():
				# Check if timeout is configured
				if config.infobartunerstate.timeout_finished_records.value:
					self.removeTimer.startLongTimer( int( config.infobartunerstate.timeout_finished_records.value ) )
		elif self.type == Stream:
			self["Record"].hide()
			self["Finished"].hide()
			self["Stream"].show()

	def update(self, timer):
		if timer:
			# Is this really necessary?
			try: timer.Filename
			except: timer.calculateFilename()
			# Update sorting parameters
			self.timeleft = int( math.ceil( ( timer.end - time() ) / 60.0 ) )
			self.duration = int( math.ceil( ( timer.end - timer.begin ) / 60.0 ) )
			self.end = timer.end
			self.filename = timer.Filename + ".ts"
		
		#TODO Handle Live / Stream Entries - Update several Labels
		for i, c in enumerate( config.infobartunerstate.fields.dict().itervalues() ):
			field = "Field"+str(i)
			content = c.value
			text = ""
			
			if content == "Tuner":
				if self.tuner:
					text = self.tuner
			
			elif content == "ChannelNumber":
				if self.channelnumber > -1:
					text = str( self.channelnumber )
				elif timer and timer.service_ref and timer.service_ref.ref:
					number = getNumber(timer.service_ref.ref)
					if number >= 0:
						text = str( number )
			
			elif content == "ChannelName":
				if timer and timer.service_ref:
					text = timer.service_ref.getServiceName()
			
			elif content == "Name":
				if timer:
					text = timer.name
			
			elif content == "TimeLeft":
				# Calculate timeleft minutes
				if timer:
					if not timer.autoincrease:
						if self.type == RecordFinished:
							# Show recording length
							text = _("%d Min") % (self.duration)
						elif timer.end > 0:
							# Show timeleft recording time
							text = _("%d Min") % (self.timeleft)
					else: 
						# Add infinity symbol for indefinitely recordings
						text = u"\u221E".encode("utf-8")
						#TODO update name of infinite recordings ??? E2 doesn't
						#epg = eEPGCache.getInstance()
						#event = epg and epg.lookupEventTime(timer.service_ref.ref, -1, 0)
						#if event: 
						#	name = event.getEventName() )
			
			elif content == "TimeElapsed":
				if timer:
					elapsed = int( math.ceil( ( time() - timer.begin ) / 60.0 ) )
					text = _("%d Min") % (elapsed)
			
			elif content == "TimerBegin":
				if timer:
					begin = localtime( timer.begin )  #TODO maybe int() is needed
					text = strftime( config.infobartunerstate.time_format.value, begin )
			
			elif content == "TimerEnd":
				if timer:
					end = localtime( timer.end )  #TODO maybe int() is needed
					text = strftime( config.infobartunerstate.time_format.value, end )
			
			elif content == "TimerDuration":
				if timer:
					text = _("%d Min") % (self.duration)
			
			elif content == "Destination":
				if timer and self.filename:
					text = os.path.dirname( self.filename )
				#TODO if stream display Hostname or IP
			
			elif content == "FileSize":
				if timer and self.filename:
					if os.path.exists( self.filename ):
						filesize = os.path.getsize( self.filename ) 
						text = _("%d MB") % ( filesize / (1024*1024) )
			
			elif content == "FreeSpace":
				if timer and self.filename:
					try:
						if os.path.exists( self.filename ):
							stat = os.statvfs( self.filename )
							free = ( stat.f_bfree / 1000 * stat.f_bsize / 1000 ) / 1024
							#free = os.stat(path).st_size/1048576)
							text = _("%d GB") % (free)
					except OSError:
						pass
			
			elif content == "None":
				pass
			
			self[field].setText( text )
	
	def resize(self, width):
		sh = self.instance.size().height()
		py = self["Background"].instance.position().y()
		#TODO config or skin get offset x position
		px = self["Record"].instance.position().x()
		px += self["Record"].instance.size().width() + 15
		
		for i, w in enumerate( width ):
			field = "Field"+str(i)
			self[field].instance.resize( eSize(w, sh) )
			self[field].instance.move( ePoint(px, py) )
			px += w
		
		#TODO config width and style
		
		#if background dynamic
		#self["Background"].instance.resize( eSize(px, sh) )
		#self.instance.resize( eSize(px, sh) )
		
		#if background color gradiant
		bw = self["Background"].instance.size().width()
		# Avoid background start position is within our window
		bw = px-bw if px-bw<0 else 0
		self["Background"].instance.move( ePoint(bw, py) )
		self.instance.resize( eSize(px, sh) )

	def remove(self):
		self.toberemoved = True 


# Global helper functions
def getTimer(strtimer):
	#for timer in self.session.nav.RecordTimer.timer_list + self.session.nav.RecordTimer.processed_timers:
	for timer in NavigationInstance.instance.RecordTimer.timer_list + NavigationInstance.instance.RecordTimer.processed_timers:
		if str(timer) == strtimer:
			return timer
	return None

def getTuner(service):
	# service must be an instance of iPlayableService or iRecordableService
	feinfo = service and service.frontendInfo()
	frontendData = feinfo and feinfo.getAll(False)
	tuner = frontendData.get("tuner_number", -1)
	if tuner > -1:
		return chr( tuner + ord('A') )
	else:
		return ""
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
	return -1
