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
EPISODEIDURLATOM  = "http://www.wunschliste.de/xml/atom.pl?"
#EPISODEIDURLRSS  = "http://www.wunschliste.de/xml/rss.pl?"


# Series: EpisodeTitle (Season.Episode) - Weekday Date, Time / Channel (Country)
# Two and a Half Men: Der Mittwochs-Mann (1.5) - Mi 02.05., 19.50:00 Uhr / TNT Serie (Pay-TV)
# Two and a Half Men: Der Mittwochs-Mann (1.5) - Mi 02.05., 19.50:00 Uhr / TNT Serie
# Two and a Half Men: Der Mittwochs-Mann (1) (1.5) - Mi 02.05., 19.50:00 Uhr / TNT Serie
# Der Troedeltrupp - Das Geld liegt im Keller: Folge 109 (109) - Do 03.05., 16.15:00 Uhr / RTL II
# Galileo: U.a.: Die schaerfste Chili der Welt - Fr 04.05., 19.05:00 Uhr / ProSieben
# Galileo: Magazin mit Aiman Abdallah, BRD 2012 - Mi 09.05., 06.10:00 Uhr / ProSieben
# Gute Zeiten, schlechte Zeiten: Folgen 4985 - 4988 (21.84) - Sa 05.05., 11.00:00 Uhr / RTL
# Channel is between last / and ( or line end
CompiledRegexpAtomChannel = re.compile('\/(?!.*\/) ([^\(]+)')
# Date is between last - and channel
CompiledRegexpAtomDate = re.compile('-(?!.*-) (.+)')
# Find optional episode
CompiledRegexpAtomEpisode = re.compile('\((?!.*\()(.+)\) ')
# Series: Title
CompiledRegexpAtomTitle = re.compile('.+: (.+)')

# (Season.Episode) - EpisodeTitle
# (21.84) Folge 4985
# (105) Folge 105
# (4.11/4.11) Mama ist die Beste/Rund um die Uhr
# Galileo: Die schaerfste Chili der Welt
# Galileo: Jumbo auf Achse: Muelltonnenkoch
# Gute Zeiten, schlechte Zeiten: Folgen 4985 - 4988 (21.84) - Sa 05.05., 11.00:00 Uhr / RTL
#CompiledRegexpPrintTitle = re.compile( '(\(.*\) )?(.+)')

CompiledRegexpEpisode = re.compile( '((\d+)[\.x])?(\d+)')


def str_to_utf8(s):
	# Convert a byte string with unicode escaped characters
	logDebug("WLF: str_to_utf8: s: ", repr(s))
	#unicode_str = s.decode('unicode-escape')
	#logDebug("WLF: str_to_utf8: s: ", repr(unicode_str))
	## Python 2.x can't convert the special chars nativly
	#utf8_str = utf8_encoder(unicode_str)[0]
	#logDebug("WLF: str_to_utf8: s: ", repr(utf8_str))
	#return utf8_str  #.decode("utf-8").encode("ascii", "ignore")
	if type(s) != unicode:
		# Default shoud be here
		try:
			s = s.decode('ISO-8859-1')
			logDebug("WLF: str_to_utf8 decode ISO-8859-1: s: ", repr(s))
		except:
			try:
				s = unicode(s, 'utf-8')
				s = s.encode('ISO-8859-1')
				logDebug("WLF: str_to_utf8 decode utf-8: s: ", repr(s))
			except:
				try:
					s = unicode(s, 'cp1252')
					s = s.encode('ISO-8859-1')
					logDebug("WLF: str_to_utf8 decode cp1252: s: ", repr(s))
				except:
					s = unicode(s, 'utf-8', 'ignore')
					s = s.encode('ISO-8859-1')
					logDebug("WLF: str_to_utf8 decode utf-8 ignore: s: ", repr(s))
	else:
		try:
			s = s.encode('ISO-8859-1')
			logDebug("WLF: str_to_utf8 encode ISO-8859-1: s: ", repr(s))
		except:
			s = s.encode('ISO-8859-1', 'ignore')
			logDebug("WLF: str_to_utf8 except encode ISO-8859-1 ignore: s: ", repr(s))
	return s


class WLAtomParser(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.title = False
		self.updated = False
		self.titlestr = ''
		self.updatedstr = ''
		self.list = []

	def handle_starttag(self, tag, attributes):
		if tag == 'title':
			self.title = True
		elif tag == 'updated':
			self.updated = True

	def handle_endtag(self, tag):
		if tag == 'title':
			self.title = False
		elif tag == 'updated':
			self.updated = False
		elif tag == 'entry':
			self.list.append( (self.titlestr, self.updatedstr) )
			self.titlestr = ''
			self.updatedstr = ''

	def handle_data(self, data):
		if self.title:
			self.titlestr += data
		elif self.updated:
			self.updatedstr = data


class WunschlisteFeed(IdentifierBase):
	def __init__(self):
		IdentifierBase.__init__(self)

	@classmethod
	def knowsToday(cls):
		return False

	@classmethod
	def knowsFuture(cls):
		return True

	def getName(self):
		return "Wunschliste"

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
		
		
		logInfo("WLF: getEpisode, name, begin, end=None, service", name, begin, end, service)
		
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
					logInfo("WLF: Possible matched series:", self.series)
					
					result = self.getNextPage( id )
					if result:
						return result
					
			else:
				name = self.getAlternativeSeries(name)
		
		else:
			return ( self.returnvalue or _("No matching series found") )

	def getSeries(self, name):
		#url = SERIESLISTURL + urlencode({ 'q' : re.sub("[^a-zA-Z0-9-*]", " ", name) })
		url = SERIESLISTURL + urlencode({ 'q' : name.lower() })
		data = self.getPage( url )
		
		if data and isinstance(data, basestring):
			data = self.parseSeries(data)
			self.doCacheList(url, data)
		
		if data and isinstance(data, list):
			logDebug("WLF: ids", data)
			return self.filterKnownIds(data)

	def parseSeries(self, data):
		serieslist = []
		for line in data.splitlines():
			values = line.split("|")
			if len(values) == 4:
				idname, countryyear, id, temp = values
				logDebug(id, idname)
				serieslist.append( (id, idname) )
			else:
				logDebug("WLF: ParseError: " + str(line))
		serieslist.reverse()
		return serieslist

	def parseNextPage(self, data):
		# Handle malformed HTML issues
		data = data.replace('&amp;','&')  # target=\"_blank\"&amp;
		parser = WLAtomParser()
		parser.feed(data)
		#logDebug(parser.list)
		return parser.list
	
	def getNextPage(self, id):
		logDebug("WLF: getNextPage")
		
		url = EPISODEIDURLATOM + urlencode({ 's' : id })
		data = self.getPage( url )
		
		if data and isinstance(data, basestring):
			data = self.parseNextPage(data)
			self.doCacheList(url, data)
		
		if data and isinstance(data, list):
			trs = data
			
			yepisode = None
			ydelta = maxint
			
			for tds in trs:
				if tds and len(tds) == 2:
					xtitle, xupdated = tds
					if xtitle is not None and xupdated is not None:
						#import iso8601
						#http://code.google.com/p/pyiso8601/
						xbegin = parse_date(xupdated)
						xbegin = xbegin.replace(tzinfo=None)
						
						#"2014-11-10T20:15:00+01:00"
						#xbegin =  datetime.strptime(xupdated[0:-6], "%Y-%m-%dT%H:%M:%S");
						
						#Py2.6
						delta = abs(self.begin - xbegin)
						delta = delta.seconds + delta.days * 24 * 3600
						#Py2.7
						#delta = abs(self.begin - xbegin).total_seconds()
						logDebug("WLF:", self.begin, '-', xbegin, '-', delta, '-', self.max_time_drift)
						
						if delta <= self.max_time_drift:
							result = CompiledRegexpAtomChannel.search(xtitle)
							if result and len(result.groups()) >= 1:
								
								xchannel = result.group(1)
								logInfo("WLF: Possible match witch channel: ", xchannel)
								if self.compareChannels(self.service, xchannel):
									
									if delta < ydelta:
										# Slice string to remove channel
										xtitle = xtitle[:result.start()]
										result = CompiledRegexpAtomDate.search(xtitle)
										
										if result and len(result.groups()) >= 1:
											# Slice string to remove date
											xtitle = xtitle[:result.start()]
											result = CompiledRegexpAtomEpisode.search(xtitle)
											
											if result and len(result.groups()) >= 1:
												# Extract season and episode
												xepisode = result.group(1)
												# Slice string to remove season and episode
												xtitle = xtitle[:result.start()]
												
												result = CompiledRegexpEpisode.search(xepisode)
												if result and len(result.groups()) >= 3:
													xseason = result and result.group(2) or config.plugins.seriesplugin.default_season.value
													xepisode = result and result.group(3) or config.plugins.seriesplugin.default_episode.value
												else:
													logDebug("WLF: wrong episode format", xepisode)
													xseason = config.plugins.seriesplugin.default_season.value
													xepisode = config.plugins.seriesplugin.default_episode.value
											else:
												logDebug("WLF: wrong title format", xtitle)
												xseason = config.plugins.seriesplugin.default_season.value
												xepisode = config.plugins.seriesplugin.default_episode.value
											result = CompiledRegexpAtomTitle.search(xtitle)
											
											if result and len(result.groups()) >= 1:
												# Extract episode title
												xtitle = result.group(1)
												
												# Handle encodings
												xtitle = str_to_utf8(xtitle)
												
												yepisode = (xseason, xepisode, xtitle, self.series)
												
												ydelta = delta
									
									else: #if delta >= ydelta:
										break
								
								else:
									self.returnvalue = _("Check the channel name")
								
						else:
							if yepisode:
								return ( yepisode )
							
							if delta <= 600:
								# Compare channels?
								logInfo("WLF: Max time trift exceeded", delta)
			
			if yepisode:
				return ( yepisode )

		else:
			logInfo("WLF: No data returned")
		
		# Nothing found
		return
