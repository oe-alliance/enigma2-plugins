# -*- coding: utf-8 -*-
# by betonme @2012

# Imports

import re

from Components.config import config

from Tools.BoundFunction import boundFunction

from urllib import urlencode

from datetime import datetime

from sys import maxint

# Internal
from Plugins.Extensions.SeriesPlugin.IdentifierBase import IdentifierBase
from Plugins.Extensions.SeriesPlugin.Logger import logDebug, logInfo
from Plugins.Extensions.SeriesPlugin import _

try:
	from HTMLParser import HTMLParser
except ImportError as ie:
	HTMLParser = None

try:
	from iso8601 import parse_date
except ImportError as ie:
	parse_date = None

# Constants
SERIESLISTURL     = "http://www.wunschliste.de/ajax/search_dropdown.pl?"
EPISODEIDURLPRINT = "http://www.wunschliste.de/epg_print.pl?"

# (Season.Episode) - EpisodeTitle
# (21.84) Folge 4985
# (105) Folge 105
# (4.11/4.11) Mama ist die Beste/Rund um die Uhr
# Galileo: Die schaerfste Chili der Welt
# Galileo: Jumbo auf Achse: Muelltonnenkoch
# Gute Zeiten, schlechte Zeiten: Folgen 4985 - 4988 (21.84) - Sa 05.05., 11.00:00 Uhr / RTL
#CompiledRegexpPrintTitle = re.compile( '(\(.*\) )?(.+)')

CompiledRegexpEpisode = re.compile( '((\d+)[\.x])?(\d+)' )


def str_to_utf8(s):
	# Convert a byte string with unicode escaped characters
	logDebug("WLP: str_to_utf8: s: ", repr(s))
	#unicode_str = s.decode('unicode-escape')
	#logDebug("WLP: str_to_utf8: s: ", repr(unicode_str))
	## Python 2.x can't convert the special chars nativly
	#utf8_str = utf8_encoder(unicode_str)[0]
	#logDebug("WLP: str_to_utf8: s: ", repr(utf8_str))
	#return utf8_str  #.decode("utf-8").encode("ascii", "ignore")
	if type(s) != unicode:
		# Default shoud be here
		try:
			s = s.decode('ISO-8859-1')
			logDebug("WLP: str_to_utf8 decode ISO-8859-1: s: ", repr(s))
		except:
			try:
				s = unicode(s, 'utf-8')
				s = s.encode('ISO-8859-1')
				logDebug("WLP: str_to_utf8 decode utf-8: s: ", repr(s))
			except:
				try:
					s = unicode(s, 'cp1252')
					s = s.encode('ISO-8859-1')
					logDebug("WLP: str_to_utf8 decode cp1252: s: ", repr(s))
				except:
					s = unicode(s, 'utf-8', 'ignore')
					s = s.encode('ISO-8859-1')
					logDebug("WLP: str_to_utf8 decode utf-8 ignore: s: ", repr(s))
	else:
		try:
			s = s.encode('ISO-8859-1')
			logDebug("WLP: str_to_utf8 encode ISO-8859-1: s: ", repr(s))
		except:
			s = s.encode('ISO-8859-1', 'ignore')
			logDebug("WLP: str_to_utf8 except encode ISO-8859-1 ignore: s: ", repr(s))
	return s


class WLPrintParser(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.tr= False
		self.td= False
		self.data = []
		self.list = []

	def handle_starttag(self, tag, attributes):
		if tag == 'td':
			self.td= True
		elif tag == 'tr':
			self.tr= True

	def handle_endtag(self, tag):
		if tag == 'td':
			self.td= False
		elif tag == 'tr':
			self.tr= False
			self.list.append(self.data)
			self.data= []

	def handle_data(self, data):
		if self.tr and self.td:
			self.data.append(data)


class Wunschliste(IdentifierBase):
	def __init__(self):
		IdentifierBase.__init__(self)

	@classmethod
	def knowsToday(cls):
		return True

	@classmethod
	def knowsFuture(cls):
		return True

	def getEpisode(self, name, begin, end=None, service=None):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or String or None
		
		
		# Check dependencies
		if HTMLParser is None:
			msg = _("Error install")  + " HTMLParser"
			logInfo(msg)
			return msg
		if parse_date is None:
			msg = _("Error install")  + " parse_date"
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
		
		
		logInfo("WLP: getEpisode, name, begin, end=None, service", name, begin, end, service)
		
		self.begin = begin
		self.end = end
		self.service = service
		
		self.knownids = []
		self.returnvalue = None
		
		while name:	
			ids = self.getSeries(name)
			
			while ids:
				idserie = ids.pop()
				
				if idserie and len(idserie) == 2:
					id, idname = idserie
					
					# Handle encodings
					self.series = str_to_utf8(idname)
					logInfo("Possible matched series:", self.series)
					
					result = self.getNextPage( id )
					if result:
						return result
					
			else:
				name = self.getAlternativeSeries(name)
		
		else:
			return ( self.returnvalue or _("No matching series found") )

	def getSeries(self, name):
		#url = SERIESLISTURL + urlencode({ 'q' : re.sub("[^a-zA-Z0-9-*]", " ", name.lower()) })
		url = SERIESLISTURL + urlencode({ 'q' : name.lower() })
		data = self.getPage( url )
		
		if data and isinstance(data, basestring):
			data = self.parseSeries(data)
			self.doCacheList(url, data)
		
		if data and isinstance(data, list):
			logDebug("WLP: ids", data)
			return self.filterKnownIds(data)

	def parseSeries(self, data):
		serieslist = []
		for line in data.splitlines():
			values = line.split("|")
			if len(values) == 4:
				idname, countryyear, id, temp = values
				logDebug("WLP:", id, idname)
				serieslist.append( (id, idname) )
			else:
				logDebug("WLP: ParseError: " + str(line))
		serieslist.reverse()
		return serieslist

	def parseNextPage(self, data):
		# Handle malformed HTML issues
		#data = data.replace('&quot;','&')
		data = data.replace('&amp;','&')
		parser = WLPrintParser()
		parser.feed(data)
		#logDebug("WLP:", parser.list)
		return parser.list

	def getNextPage(self, id):
		logDebug("WLP: getNextPage")
		
		url = EPISODEIDURLPRINT + urlencode({ 's' : id })
		data = self.getPage( url )
		
		if data and isinstance(data, basestring):
			data = self.parseNextPage(data)
			self.doCacheList(url, data)
		
		if data and isinstance(data, list):
			trs = data
			
			yepisode = None
			ydelta = maxint
			
			for tds in trs:
				if tds and len(tds) >= 5:
					
					#print tds
					
					xchannel, xday, xdate, xbegin, xend = tds[:5]
					
					xtitle = "".join(tds[4:])
					
					if self.actual_month == 12 and xdate.endswith(".01."):
						year = str(self.actual_year+1)
					else:
						year = str(self.actual_year)
					
					xbegin = datetime.strptime( xdate+year+xbegin, "%d.%m.%Y%H.%M Uhr" )
					#xend  = datetime.strptime( xdate+year+xend,   "%d.%m.%Y%H.%M Uhr" )
					#logDebug("WLP:", xchannel, xdate, xbegin, xend, xtitle)
					#logDebug("WLP:", datebegin, xbegin, abs((datebegin - xbegin)))
					
					#Py2.6
					delta = abs(self.begin - xbegin)
					delta = delta.seconds + delta.days * 24 * 3600
					#Py2.7 
					#delta = abs(self.begin - xbegin).total_seconds()
					logDebug("WLP:", self.begin, '-', xbegin, '-', delta, '-', self.max_time_drift)
					
					if delta <= self.max_time_drift:
						
						logInfo("WLP: Possible match witch channel: ", xchannel)
						if self.compareChannels(self.service, xchannel):
						
							if delta < ydelta:
								
								print len(tds), tds
								if len(tds) >= 7:
									xepisode, xtitle = tds[5:7]
								
									if xepisode:
										result = CompiledRegexpEpisode.search(xepisode)
										
										if result and len(result.groups()) >= 3:
											xseason = result and result.group(2) or config.plugins.seriesplugin.default_season.value
											xepisode = result and result.group(3) or config.plugins.seriesplugin.default_episode.value
										else:
											xseason = config.plugins.seriesplugin.default_season.value
											xepisode = config.plugins.seriesplugin.default_episode.value
									else:
										xseason = config.plugins.seriesplugin.default_season.value
										xepisode = config.plugins.seriesplugin.default_episode.value
								
								elif len(tds) == 6:
									xtitle = tds[5]
									xseason = config.plugins.seriesplugin.default_season.value
									xepisode = config.plugins.seriesplugin.default_episode.value
								
								# Handle encodings
								xtitle = str_to_utf8(xtitle)
								
								yepisode = (xseason, xepisode, xtitle, self.series)
								ydelta = delta
							
							else: #if delta >= ydelta:
								return ( yepisode )
						
						else:
							self.returnvalue = _("Check the channel name")
						
					else:
						if yepisode:
							return ( yepisode )
						
						if delta <= 600:
							# Compare channels?
							logInfo("WLP: Max time trift exceeded", delta)
						
			if yepisode:
				return ( yepisode )

		else:
			logInfo("WLP: No data returned")
		
		# Nothing found
		return
