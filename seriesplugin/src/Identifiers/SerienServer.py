# -*- coding: utf-8 -*-
# by betonme @2012

# Imports
from Components.config import config

from Tools.BoundFunction import boundFunction

from urllib import urlencode

from time import time, mktime
from datetime import datetime

import re

# Internal
from Plugins.Extensions.SeriesPlugin.IdentifierBase import IdentifierBase
from Plugins.Extensions.SeriesPlugin.Logger import logDebug, logInfo
from Plugins.Extensions.SeriesPlugin import _

# Constants
SERIEN_SERVER_URL = 'http://serienrecorder.lima-city.de/cache.php'

try:
	import xmlrpclib
except ImportError as ie:
	xmlrpclib = None


class SerienServer(IdentifierBase):
	def __init__(self):
		IdentifierBase.__init__(self)
		
		# Check dependencies
		if xmlrpclib is not None:
			self.server = xmlrpclib.ServerProxy(SERIEN_SERVER_URL, verbose=False)

	@classmethod
	def knowsElapsed(cls):
		return True

	@classmethod
	def knowsToday(cls):
		return True

	@classmethod
	def knowsFuture(cls):
		return True

	def getEpisode(self, name, begin, end=None, service=None):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or String or None
		logDebug("SerienServer getEpisode")
		
		self.name = name
		self.begin = begin
		self.end = end
		self.service = service
		
		self.knownids = []
		
		
		# Check dependencies
		if xmlrpclib is None:
			logInfo(_("Error install")  + " python-xmlrpclib")
			return _("Error install") + " python-xmlrpclib"
		
		
		# Check preconditions
		if not name:
			logInfo(_("Skip SerienServer: No show name specified"))
			return _("Skip SerienServer: No show name specified")
		if not begin:
			logInfo(_("Skip SerienServer: No begin timestamp specified"))
			return _("Skip SerienServer: No begin timestamp specified")
		if not service:
			logInfo(_("Skip SerienServer: No service specified"))
			return _("Skip SerienServer: No service specified")
		
		logInfo("SerienServer getEpisode, name, begin, end=None, service", name, begin, end, service)
		
		# Prepare parameters
		name = re.sub("[^a-zA-Z0-9-*]", " ", name.lower())
		webChannels = self.lookupChannelByReference(service)
		unixtime = str(int(mktime(begin.timetuple())))
		
		# Lookup
		for webChannel in webChannels:
			logInfo("SerienServer getSeasonEpisode():", idname, webChannel, unixtime)
			
			result = self.server.sp.cache.getSeasonEpisode( idname, webChannel, unixtime, self.max_time_drift )
			logDebug("SerienServer getSeasonEpisode result:", result)
			
			if result:
				return ( result['season'], result['episode'], result['title'], result['series'] )

		else:
			if unixtime < time():
				return ( _("Please try Fernsehserien.de") )
			else:
				return ( _("No matching series found") )
