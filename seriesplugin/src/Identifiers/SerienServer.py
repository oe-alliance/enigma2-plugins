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
from Plugins.Extensions.SeriesPlugin.Logger import splog
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
			self.server = xmlrpclib.ServerProxy(SERIEN_SERVER_URL, verbose=True)

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
		splog("SerienServer getEpisode")
		
		self.name = name
		self.begin = begin
		self.end = end
		self.service = service
		
		self.knownids = []
		
		
		# Check dependencies
		if xmlrpclib is None:
			splog(_("Error install python_xmlrpclib"))
			return _("Error install python_xmlrpclib")
		
		
		# Check preconditions
		if not name:
			splog(_("Skip SerienServer: No show name specified"))
			return _("Skip SerienServer: No show name specified")
		if not begin:
			splog(_("Skip SerienServer: No begin timestamp specified"))
			return _("Skip SerienServer: No begin timestamp specified")
		if not service:
			splog(_("Skip SerienServer: No service specified"))
			return _("Skip SerienServer: No service specified")
		
		
		# Prepare parameters
		name = re.sub("[^a-zA-Z0-9-*]", " ", name.lower())
		webChannels = self.lookupChannelByReference(service)
		unixtime = str(mktime(begin.timetuple()))
		
		
		# Lookup
		while name:	
			
			#ids = self.getSeries(name)
			#while ids:
			#	idserie = ids.pop()
			#	if idserie and len(idserie) == 2:
			#		id, idname = idserie
			
			idname = name
			for webChannel in webChannels:
				splog("SerienServer getSeasonEpisode():", idname, webChannel, unixtime)
				
				result = self.server.sp.cache.getSeasonEpisode( idname, webChannel, unixtime )
				splog("SerienServer getSeasonEpisode result:", result)
				
				if result:
					self.series = result['series']
					yepisode = ( result['season'], result['episode'], result['title'], result['series'] )
					if yepisode:
						return ( yepisode )

			else:
				name = self.getAlternativeSeries(name)
		
		else:
			if unixtime < time():
				return ( _("Please try Fernsehserien.de") )
			else:
				return ( _("No matching series found") )

#	def getSeries(self, name):
#		#url = SERIESLISTURL + urlencode({ 'q' : re.sub("[^a-zA-Z0-9-*]", " ", name.lower()) })
#		url = SERIESLISTURL + urlencode({ 'q' : name.lower() }
#		data = self.getPage( url, False )
#		
#		if data and isinstance(data, basestring):
#			#id, calue = data
#			#data = json.loads(data).values()
#			data = list(reversed( json.loads(data).values() ) )
#		
#		if data and isinstance(data, list):
#			splog("WunschlistePrint ids", data)
#			return self.filterKnownIds(data)
