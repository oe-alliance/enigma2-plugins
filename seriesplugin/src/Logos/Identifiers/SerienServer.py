# -*- coding: utf-8 -*-
# by betonme @2012

# Imports
import re

from Components.config import config

from Tools.BoundFunction import boundFunction

from time import time, mktime
from datetime import datetime

# Internal
from Plugins.Extensions.SeriesPlugin import _
from Plugins.Extensions.SeriesPlugin.IdentifierBase import IdentifierBase2
from Plugins.Extensions.SeriesPlugin.Logger import logDebug, logInfo
from Plugins.Extensions.SeriesPlugin.Channels import lookupChannelByReference
from Plugins.Extensions.SeriesPlugin.TimeoutServerProxy import TimeoutServerProxy


class SerienServer(IdentifierBase2):
	def __init__(self):
		IdentifierBase2.__init__(self)
		
		self.server = TimeoutServerProxy()
	
	@classmethod
	def knowsElapsed(cls):
		return True

	@classmethod
	def knowsToday(cls):
		return True

	@classmethod
	def knowsFuture(cls):
		return True

	def getName(self, future=True):
		if future:
			return "Wunschliste"
		else:
			return "Fernsehserien"

	def getEpisode(self, name, begin, end=None, service=None):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or String or None
		
		
		# Check preconditions
		if not name:
			msg =_("Skip: No show name specified")
			logInfo(msg)
			return msg
		if not begin:
			msg = _("Skip: No begin timestamp specified")
			logInfo(msg)
			return msg
		if not service:
			msg = _("Skip: No service specified")
			logInfo(msg)
			return msg
		
		
		self.name = name
		self.begin = begin
		self.end = end
		self.service = service
		
		self.knownids = []
		
		logInfo("SerienServer getEpisode, name, begin, end=None, service", name, begin, end, service)
		
		# Prepare parameters
		webChannels = lookupChannelByReference(service)
		if not webChannels:
			msg = _("Check the channel name")
			logInfo(msg)
			return msg
		
		unixtime = str(int(mktime(begin.timetuple())))
		max_time_drift = self.max_time_drift
		
		# Lookup
		for webChannel in webChannels:
			logDebug("SerienServer getSeasonEpisode(): [\"%s\",\"%s\",\"%s\",%s]" % (name, webChannel, unixtime, max_time_drift))
			
			result = self.server.sp.cache.getSeasonEpisode( name, webChannel, unixtime, max_time_drift )
			logDebug("SerienServer getSeasonEpisode result:", result)
			
			if result:
				return ( result['season'], result['episode'], result['title'], result['series'] )

		else:
			return ( _("No match found") )
