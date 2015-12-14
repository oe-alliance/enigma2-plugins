# -*- coding: utf-8 -*-
# by betonme @2012

# Imports
import re

from Components.config import config

from Tools.BoundFunction import boundFunction

from urllib import urlencode

from time import time, mktime
from datetime import datetime

# Internal
from Plugins.Extensions.SeriesPlugin.IdentifierBase import IdentifierBase
from Plugins.Extensions.SeriesPlugin.Logger import logDebug, logInfo
from Plugins.Extensions.SeriesPlugin import _

# Constants
SERIEN_SERVER_URL = 'http://176.9.54.54/serienserver/cache/cache.php'

CompiledRegexpReplaceChars = re.compile("[^a-zA-Z0-9-\*]")

try:
	import xmlrpclib
except ImportError as ie:
	xmlrpclib = None


class SerienServer(IdentifierBase):
	def __init__(self):
		IdentifierBase.__init__(self)
		
		# Check dependencies
		if xmlrpclib is not None:
			from Plugins.Extensions.SeriesPlugin.plugin import REQUEST_PARAMETER
			self.server = xmlrpclib.ServerProxy(SERIEN_SERVER_URL + REQUEST_PARAMETER, verbose=False)
	
	@classmethod
	def knowsElapsed(cls):
		return True

	@classmethod
	def knowsToday(cls):
		return True

	@classmethod
	def knowsFuture(cls):
		return True

	def getName(self):
		return "Wunschliste"

	def getEpisode(self, name, begin, end=None, service=None):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or String or None
		
		
		# Check dependencies
		if xmlrpclib is None:
			msg = _("Error install")  + " python-xmlrpclib"
			logInfo(msg)
			return msg
		
		
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
		name = CompiledRegexpReplaceChars.sub(" ", name.lower())
		webChannels = self.lookupChannelByReference(service)
		unixtime = str(int(mktime(begin.timetuple())))
		max_time_drift = self.max_time_drift
		
		# Lookup
		for webChannel in webChannels:
			logInfo("SerienServer getSeasonEpisode():", name, webChannel, unixtime)
			
			result = self.server.sp.cache.getSeasonEpisode( name, webChannel, unixtime, max_time_drift )
			logDebug("SerienServer getSeasonEpisode result:", result)
			
			if result:
				return ( result['season'], result['episode'], result['title'], result['series'] )

		else:
			if unixtime < time():
				return ( _("Please try Fernsehserien.de") )
			else:
				return ( _("No matching series found") )
