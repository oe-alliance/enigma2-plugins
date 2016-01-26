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

# for localized messages
from . import _

from time import time
from enigma import eEPGCache
from ServiceReference import ServiceReference

# Config
from Components.config import *

from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup
from Tools.BoundFunction import boundFunction

# Plugin internal
from SeriesPlugin import getInstance, refactorTitle, refactorDescription, refactorDirectory
from Logger import logDebug, logInfo

TAG = "SeriesPlugin"

#######################################################
# Label timer
class SeriesPluginTimer(object):

	data = []
	counter = 0;
	
	def __init__(self, timer, name, begin, end, block=False):
		
		logDebug("SPT: SeriesPluginTimer: name, timername, begin, end:", name, timer.name, begin, end)
		
		if block:
			# We do not want to execute the blocking code here
			return
		
		self.getSeasonAndEpisode(timer, name, begin, end, block)

	def getSeasonAndEpisode(self, timer, name, begin, end, block=True):
		
		logInfo("SeriesPluginTimer: timername, service, name, begin, end:", timer.name, str(timer.service_ref.ref), name, begin, end)
		
		if hasattr(timer, 'sp_in_queue'):
			if timer.sp_in_queue:
				logDebug("SPT: SeriesPluginTimer: Skip timer is already in queue:", timer.name)
				timer.log(601, "[SeriesPlugin] Skip timer is already in queue %s" % (timer.name) )
				return
		
		# We have to compare the length,
		# because of the E2 special chars handling for creating the filenames
		#if timer.name == name:
		# Mad Men != Mad_Men
		
		if TAG in timer.tags:
			logDebug("SPT: SeriesPluginTimer: Skip timer is already handled %s", timer.name)
			timer.log(607, "[SeriesPlugin] Skip timer is already handled %s" % (timer.name) )
			return
		
		if config.plugins.seriesplugin.timer_eit_check.value:
			
			event = None
			epgcache = eEPGCache.getInstance()
			
			if timer.eit:
				#logDebug("SPT: Timer Eit is set", timer.service_ref.ref, timer.eit)
				event = epgcache.lookupEventId(timer.service_ref.ref, timer.eit)
				logDebug("SPT: LookupEventId", timer.eit, event)
			if not(event):
				#logDebug("Lookup EventTime", timer.service_ref.ref, end, begin)
				event = epgcache.lookupEventTime( timer.service_ref.ref, begin + ((end - begin) /2) );
				logDebug("SPT: lookupEventTime", event )
			#if not(event):
			#	logDebug("Lookup Event", timer.service_ref.ref, end, begin)
			#	events = epgcache.lookupEvent( [ "T" , ( timer.service_ref.ref, 0, begin + ((end - begin) /2) ) ] );
			#	logDebug("LookupEvent event(s) found", len(events), events )
			#	event = events and events[0]
			
			if event:
				#logDebug("EPG event found")
				if not ( len(timer.name) == len(name) == len(event.getEventName()) ):
					logDebug("SPT: Skip timer because it is already modified", timer.name, name, event and event.getEventName(), len(timer.name), len(name), len(event.getEventName()) )
					timer.log(602, "[SeriesPlugin] Skip timer because it is already modified")
					return
			else:
				if ( len(timer.name) == len(name) ):
					logDebug("SPT: Skip timer because no event was found", timer.name, name, len(timer.name), len(name))
					timer.log(603, "[SeriesPlugin] Skip timer because no event was found")
					return
		
		if timer.begin < time() + 60:
			logDebug("SPT: Skipping timer because it starts in less than 60 seconds", timer.name )
			timer.log(604, "[SeriesPlugin] Skip timer because it starts in less than 60 seconds")
			return
		
		if timer.isRunning():
			logDebug("SPT: Skipping timer because it is already running", timer.name )
			timer.log(605, "[SeriesPlugin] Skip timer because it is already running")
			return
		
		if timer.justplay:
			logDebug("SPT: Skipping justplay timer", timer.name )
			timer.log(606, "[SeriesPlugin] Skip justplay timer")
			return
		
		timer.log(600, "[SeriesPlugin] Try to find infos for %s" % (timer.name) )
		
		seriesPlugin = getInstance()
		
		if timer.service_ref:
			#channel = timer.service_ref.getServiceName()
			#logDebug(channel)
			
			logDebug("SPT: getEpisode:", name, begin, end, block)
			
			timer.sp_in_queue = True
			
			if block:
				result = seriesPlugin.getEpisodeBlocking(
					name, begin, end, timer.service_ref, future=True
				)
				return self.timerCallback(timer, result)
			else:
				seriesPlugin.getEpisode(
					boundFunction(self.timerCallback, timer),
					#name, begin, end, channel, future=True
					name, begin, end, timer.service_ref, future=True
				)
				return None
		else:
			logDebug("SPT: SeriesPluginTimer: No channel specified")
			self.timerCallback(timer, "No channel specified")
			return None

	def timerCallback(self, timer, data=None):
		logDebug("SPT: timerCallback", data)
		logDebug(data)
		
		if data and len(data) == 4 and timer:
			
			# Episode data available, refactor name and description
			#from SeriesPluginRenamer import newLegacyEncode
			timer.name = str(refactorTitle(timer.name, data))
			#timer.name = newLegacyEncode(refactorTitle(timer.name, data))
			timer.description = str(refactorDescription(timer.description, data))
			
			#try: timer.Filename
			#except: timer.calculateFilename()
			if not hasattr(timer, 'Filename'):
				timer.calculateFilename()
			
			if not timer.dirname:
				logDebug("SPT: SeriesPluginTimer: No dirname")
				timer.dirname  = str(refactorDirectory(config.usage.default_path.value, data))
			else:
				timer.dirname  = str(refactorDirectory(timer.dirname, data))
			
			timer.log(610, "[SeriesPlugin] Success: Changed name: %s." % (timer.name))
			
			timer.tags.append(TAG)
		
		elif data:
			timer.log(611, "[SeriesPlugin] Failed: %s." % ( str( data ) ))
			SeriesPluginTimer.data.append(
				str(timer.name) + " " + str( data )
			)
		
		else:
			timer.log(612, "[SeriesPlugin] Failed." )
			SeriesPluginTimer.data.append(
				str(timer.name) + " " + _("No data available")
			)
		
		timer.sp_in_queue = False
		
		if config.plugins.seriesplugin.timer_popups.value or config.plugins.seriesplugin.timer_popups_success.value:
			
			SeriesPluginTimer.counter = SeriesPluginTimer.counter +1
			
			if SeriesPluginTimer.data or config.plugins.seriesplugin.timer_popups_success.value:
				
				# Maybe there is a better way to avoid multiple Popups
				from SeriesPlugin import getInstance
				
				instance = getInstance()
				
				if instance.thread.empty() and instance.thread.finished():
				
					if SeriesPluginTimer.data:
						AddPopup(
							"SeriesPlugin:\n" + _("Timer rename has been finished with %d errors:\n") % (len(SeriesPluginTimer.data)) +"\n" +"\n".join(SeriesPluginTimer.data),
							MessageBox.TYPE_ERROR,
							int(config.plugins.seriesplugin.timer_popups_timeout.value),
							'SP_PopUp_ID_TimerFinished'
						)
					else:
						AddPopup(
							"SeriesPlugin:\n" + _("%d timer renamed successfully") % (SeriesPluginTimer.counter),
							MessageBox.TYPE_INFO,
							int(config.plugins.seriesplugin.timer_popups_timeout.value),
							'SP_PopUp_ID_TimerFinished'
						)
					SeriesPluginTimer.data = []
					SeriesPluginTimer.counter = 0
		
		return timer
