# -*- coding: utf-8 -*-
#######################################################################
#
#    Series Plugin for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=TBD
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

import os
import re


# for localized messages
from . import _
#from time import time
from datetime import datetime

# Config
from Components.config import config

from Screens.Screen import Screen
from Screens.Setup import SetupSummary
from Screens.MessageBox import MessageBox
from Screens.ChannelSelection import ChannelSelectionBase

from Components.AVSwitch import AVSwitch
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap

from enigma import eEPGCache, eServiceReference, eServiceCenter, iServiceInformation, ePicLoad, eServiceEvent
from ServiceReference import ServiceReference

from RecordTimer import RecordTimerEntry, parseEvent, AFTEREVENT
from Screens.TimerEntry import TimerEntry
from Components.UsageConfig import preferredTimerPath
from Screens.TimerEdit import TimerSanityConflict

from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS


# Plugin internal
from SeriesPlugin import getInstance
from Logger import splog


# Constants
PIXMAP_PATH = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/Logos/" )

instance = None


#######################################################
# Info screen
class SeriesPluginInfoScreen(Screen):
	
	skinfile = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/skin.xml" )
	skin = open(skinfile).read()
	
	def __init__(self, session, service=None, event=None):
		Screen.__init__(self, session)
		
		global instance
		instance = self
		
		self.session = session
		self.skinName = [ "SeriesPluginInfoScreen" ]
		
		self["logo"] = Pixmap()
		self["cover"] = Pixmap()
		self["state"] = Pixmap()
		
		self["event_title"] = Label()
		self["event_episode"] = Label()
		self["event_description"] = ScrollLabel()
		self["datetime"] = Label()
		self["channel"] = Label()
		self["duration"] = Label()
		
		self["key_red"] = Button("")				# Rename or Record
		self["key_green"] = Button("")			# Trakt Seen / Not Seen
		self["key_yellow"] = Button("")			# Show all Episodes of current season
		self["key_blue"] = Button("")				# Show all Seasons
		
		self.redButtonFunction = None
		
		#TODO HelpableActionMap
		self["actions"] = ActionMap(["OkCancelActions", "EventViewActions", "DirectionActions", "ColorActions"],
		{
			"cancel":    self.close,
			"ok":        self.close,
			"up":        self["event_description"].pageUp,
			"down":      self["event_description"].pageDown,
			"red":       self.redButton,
			"prevEvent": self.prevEpisode,
			"nextEvent": self.nextEpisode,
			
			#TODO
			#"pageUp":    self.pageUp,
			#"pageDown":  self.pageDown,
			#"openSimilarList": self.openSimilarList
		})
		
		splog("SPI: SeriesPluginInfo", service, event)
		self.service = service
		self.event = event
		
		self.name = ""
		self.short = ""
		self.data = None
		
		self.path = None
		self.eservice = None
		
		self.epg = eEPGCache.getInstance()
		self.serviceHandler = eServiceCenter.getInstance()
		self.seriesPlugin = getInstance()
		
		self.onLayoutFinish.append( self.layoutFinished )

	def layoutFinished(self):
		self.setTitle( _("SeriesPlugin Info") )
		
		self.getEpisode()

	def getEpisode(self):
		self.name = ""
		self.short = ""
		self.data = None
		begin, end, duration = 0, 0, 0
		ext, channel = "", ""
		
		today = True #OR future
		elapsed = False
		
		service = self.service
		
		ref = None
		
		if isinstance(service, eServiceReference):
			#ref = service  #Problem EPG
			self.eservice = service
			self.path = service.getPath()
			if self.path:
				# Service is a movie reference
				info = self.serviceHandler.info(service)
				ref = info.getInfoString(service, iServiceInformation.sServiceref)
				sref = ServiceReference(ref)
				ref = sref.ref
				channel = sref.getServiceName()
				if not channel:
					ref = str(ref)
					ref = re.sub('::.*', ':', ref)
					sref = ServiceReference(ref)
					ref = sref.ref
					channel = sref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
				#ref = eServiceReference(str(service))
				#ref = service
				# Get information from record meta files
				self.event = info and info.getEvent(service)
				today = False
				elapsed = True
				splog("SPI: eServiceReference movie", str(ref))
			else:
				# Service is channel reference
				#ref = eServiceReference(str(service))
				ref = service
				#channel = ServiceReference(ref).getServiceName() or ""
				channel = ServiceReference(str(service)).getServiceName() or ""
				#ref = eServiceReference(service.toString())#
				# Get information from event
				splog("SPI: eServiceReference channel", str(ref))
		
		elif isinstance(service, ServiceReference):
			ref = service.ref
			channel = service.getServiceName()
			splog("SPI: ServiceReference", str(ref))
		
		elif isinstance(service, ChannelSelectionBase):
			ref = service.getCurrentSelection()
			channel = ServiceReference(ref).getServiceName() or ""
			splog("SPI: ChannelSelectionBase", str(ref))
		
		# Fallbacks
		if ref is None:
			#ref = self.session and self.session.nav.getCurrentService()
			#ref = eServiceReference(ref.info().getInfoString(iServiceInformation.sServiceref))
			#ref = eServiceReference(str(ref))

			#service = self.session.nav.getCurrentService()
			#info = service and service.info()
			#event = info and info.getEvent(0)
			
			sref = self.session and self.session.nav.getCurrentlyPlayingServiceReference().toString()
			ref = eServiceReference(sref)
			channel = ServiceReference(str(ref)).getServiceName() or ""
			
			splog("SPI: Fallback ref", ref, str(ref), channel)
		
		if not isinstance(self.event, eServiceEvent):
			try:
				self.event = ref.valid() and self.epg.lookupEventTime(ref, -1)
			except:
				# Maybe it is an old reference
				# Has the movie been renamed earlier?
				# Refresh / reload the list?
				self["event_episode"].setText( "No valid selection!" )
				splog("SPI: No valid selection", str(ref))
				return
			#num = event and event.getNumOfLinkageServices() or 0
			#for cnt in range(num):
			#	subservice = event.getLinkageService(sref, cnt)
			# Get information from epg
			today = True
			elapsed = False
			splog("SPI: Fallback event", self.event)
		
		self.service = ref
		
		if self.event:
			self.name = self.event.getEventName() or ""
			begin = self.event.getBeginTime() or 0
			duration = self.event.getDuration() or 0
			end = begin + duration or 0
			# We got the exact margins, no need to adapt it
			self.short = self.event.getShortDescription() or ""
			ext = self.event.getExtendedDescription() or ""
			splog("SPI: event")
		
		if not begin:
			info = self.serviceHandler.info(eServiceReference(str(ref)))
			#splog("SPI: info")
			if info:
				#splog("SPI: if info")
				begin = info.getInfo(ref, iServiceInformation.sTimeCreate) or 0
				if begin:
					duration = info.getLength(ref) or 0
					end = begin + duration or 0
					#splog("SPI: sTimeCreate")
				else:
					end = os.path.getmtime(ref.getPath()) or 0
					duration = info.getLength(ref) or 0
					begin = end - duration or 0
					#splog("SPI: sTimeCreate else")
			elif ref:
				path = ref.getPath()
				#splog("SPI: getPath")
				if path and os.path.exists(path):
					begin = os.path.getmtime(path) or 0
					#splog("SPI: getctime")
			#else:
				#MAYBE we could also try to parse the filename
			# We don't know the exact margins, we will assume the E2 default margins
			begin = begin + (config.recording.margin_before.value * 60)
			end = end - (config.recording.margin_after.value * 60)
		
		self.updateScreen(self.name, _("Retrieving Season, Episode and Title..."), self.short, ext, begin, duration, channel)
		
		identifier = self.seriesPlugin.getIdentifier(False, today, elapsed)
		if identifier:
			path = os.path.join(PIXMAP_PATH, identifier+".png")
			if os.path.exists(path):
				self.loadPixmap("logo", path )
		try:
			identifier = self.seriesPlugin.getEpisode(
					self.episodeCallback, 
					#self.name, begin, end, channel, today=today, elapsed=elapsed
					#self.name, begin, end, self.service, today=today, elapsed=elapsed
					self.name, begin, end, ref, today=today, elapsed=elapsed
				)
		except Exception as e:
			splog("SPI: exception:", str(e))

	def episodeCallback(self, data=None):
		#TODO episode list handling
		#store the list and just open the first one
		
		splog("SPI: episodeCallback", data)
		#splog(data)
		if data and len(data) == 4:
			# Episode data available
			season, episode, title, series = self.data = data
		
			if season == 0 and episode == 0:
				custom = _("{title:s}").format( 
							**{'season': season, 'episode': episode, 'title': title} )
			elif season == 0:
				custom = _("Episode: {episode:d}\n{title:s}").format( 
							**{'season': season, 'episode': episode, 'title': title} )
			elif episode == 0:
				custom = _("Season: {season:d}\n{title:s}").format( 
							**{'season': season, 'episode': episode, 'title': title} )
			else:
				custom = _("Season: {season:d}  Episode: {episode:d}\n{title:s}").format( 
							**{'season': season, 'episode': episode, 'title': title} )
			
			try:
				self.setColorButtons()
			except Exception as e:
				# Screen already closed
				splog("SPI: exception:", str(e))
		elif data:
			custom = str( data )
		else:
			custom = _("No matching episode found")
		
		# Check if the dialog is already closed
		try:
			self["event_episode"].setText( custom )
		except Exception as e:
			# Screen already closed
			#splog("SPI: exception:", str(e))
			pass


	def updateScreen(self, name, episode, short, ext, begin, duration, channel):
		# Adapted from EventView
		self["event_title"].setText( name )
		self["event_episode"].setText( episode )
		
		text = ""
		if short and short != name:
			text = short
		if ext:
			if text:
				text += '\n'
			text += ext
		self["event_description"].setText(text)
		
		self["datetime"].setText( datetime.fromtimestamp(begin).strftime("%d.%m.%Y, %H:%M") )
		self["duration"].setText(_("%d min")%((duration)/60))
		self["channel"].setText(channel)

	# Handle pixmaps
	def loadPixmap(self, widget, path):
		sc = AVSwitch().getFramebufferScale()
		size = self[widget].instance.size()
		self.picload = ePicLoad()
		self.picload_conn = None
		try:
			self.picload_conn = self.picload.PictureData.connect( boundFunction(self.loadPixmapCallback, widget) )
		except:
			self.picload_conn = True
			self.picload.PictureData.get().append( boundFunction(self.loadPixmapCallback, widget) )
		if self.picload and self.picload_conn:
			self.picload.setPara((size.width(), size.height(), sc[0], sc[1], False, 1, "#00000000")) # Background dynamically
			if self.picload.startDecode(path) != 0:
				del self.picload

	def loadPixmapCallback(self, widget, picInfo=None):
		if self.picload and picInfo:
			ptr = self.picload.getData()
			if ptr != None:
				self[widget].instance.setPixmap(ptr)
				self[widget].show()
			del self.picload
			self.picload_conn = None

	# Overwrite Screen close function
	def close(self):
		
		global instance
		instance = None
		
		# Call baseclass function
		Screen.close(self)


	def setColorButtons(self):
		splog("SPI: event eit", self.event and self.event.getEventId())
		if self.service and self.data:
			
			if self.path and os.path.exists(self.path):
				# Record file exists
				self["key_red"].setText(_("Rename"))
				self.redButtonFunction = self.rename
			elif self.event and self.event.getEventId():
				# Event exists
				#if (not self.service.flags & eServiceReference.isGroup) and self.service.getPath() and self.service.getPath()[0] == '/'
				#for timer in self.session.nav.RecordTimer.timer_list:
				#	if timer.eit == eventid and timer.service_ref.ref.toString() == refstr:
				#		cb_func = lambda ret : not ret or self.removeTimer(timer)
				self["key_red"].setText(_("Record"))
				self.redButtonFunction = self.record
			else:
				self["key_red"].setText("")
				self.redButtonFunction = None
		else:
			self["key_red"].setText("")
			self.redButtonFunction = None

	def redButton(self):
		if callable(self.redButtonFunction):
			self.redButtonFunction()

	def prevEpisode(self):
		if self.service and self.data:
			pass

	def nextEpisode(self):
		if self.service and self.data:
			pass

	def rename(self):
		ref = self.eservice
		if ref and self.data:
			path = ref.getPath()
			if path and os.path.exists(path):
				from SeriesPluginRenamer import rename
				if rename(path, self.name, self.short, self.data) is True:
					self["key_red"].setText("")
					self.redButtonFunction = None
					self.session.open( MessageBox, _("Successfully renamed"), MessageBox.TYPE_INFO )
				else:
					self.session.open( MessageBox, _("Renaming failed"), MessageBox.TYPE_INFO )

	# Adapted from EventView
	def record(self):
		if self.event and self.service:
			event = self.event
			ref = self.service
			if event is None:
				return
			eventid = event.getEventId()
			refstr = eServiceReference(str(self.service)).toString()
			for timer in self.session.nav.RecordTimer.timer_list:
				if timer.eit == eventid and timer.service_ref.ref.toString() == refstr:
					cb_func = lambda ret : not ret or self.removeTimer(timer)
					self.session.openWithCallback(cb_func, MessageBox, _("Do you really want to delete %s?") % event.getEventName())
					break
			else:
				#newEntry = RecordTimerEntry(ServiceReference(ref), checkOldTimers = True, dirname = preferredTimerPath(), *parseEvent(self.event))
				begin, end, name, description, eit = parseEvent(self.event)
				
				from SeriesPlugin import refactorTitle, refactorDescription
				if self.data:
					name = refactorTitle(name, self.data)
					description = refactorDescription(description, self.data)
				
				newEntry = RecordTimerEntry(ServiceReference(ref), begin, end, name, description, eit, dirname = preferredTimerPath())
				self.session.openWithCallback(self.finishedAdd, TimerEntry, newEntry)

	def removeTimer(self, timer):
		splog("SPI: remove Timer")
		timer.afterEvent = AFTEREVENT.NONE
		self.session.nav.RecordTimer.removeEntry(timer)
		#self["key_green"].setText(_("Add timer"))
		#self.key_green_choice = self.ADD_TIMER

	def finishedAdd(self, answer):
		splog("SPI: finished add")
		if answer[0]:
			entry = answer[1]
			simulTimerList = self.session.nav.RecordTimer.record(entry)
			if simulTimerList is not None:
				for x in simulTimerList:
					if x.setAutoincreaseEnd(entry):
						self.session.nav.RecordTimer.timeChanged(x)
				simulTimerList = self.session.nav.RecordTimer.record(entry)
				if simulTimerList is not None:
					self.session.openWithCallback(self.finishSanityCorrection, TimerSanityConflict, simulTimerList)
			#self["key_green"].setText(_("Remove timer"))
			#self.key_green_choice = self.REMOVE_TIMER
		else:
			#self["key_green"].setText(_("Add timer"))
			#self.key_green_choice = self.ADD_TIMER
			splog("SPI: Timeredit aborted")

	def finishSanityCorrection(self, answer):
		self.finishedAdd(answer)

