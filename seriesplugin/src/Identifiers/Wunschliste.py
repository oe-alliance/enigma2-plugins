# -*- coding: utf-8 -*-
# by betonme @2012

# Imports
from Components.config import config

from Tools.BoundFunction import boundFunction

from urllib import urlencode

from HTMLParser import HTMLParser

from datetime import datetime

import re
from sys import maxint

# Internal
from Plugins.Extensions.SeriesPlugin.IdentifierBase import IdentifierBase
from Plugins.Extensions.SeriesPlugin.Logger import splog

from iso8601 import parse_date

#import codecs
#utf8_encoder = codecs.getencoder("utf-8")


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

CompiledRegexpEpisode = re.compile( '((\d+)[\.x])?(\d+)')


def str_to_utf8(s):
	# Convert a byte string with unicode escaped characters
	splog("WL: str_to_utf8: s: ", repr(s))
	#unicode_str = s.decode('unicode-escape')
	#splog("WL: str_to_utf8: s: ", repr(unicode_str))
	## Python 2.x can't convert the special chars nativly
	#utf8_str = utf8_encoder(unicode_str)[0]
	#splog("WL: str_to_utf8: s: ", repr(utf8_str))
	#return utf8_str  #.decode("utf-8").encode("ascii", "ignore")
	if type(s) != unicode:
		# Default shoud be here
		try:
			s = s.decode('ISO-8859-1')
			splog("WL: str_to_utf8 decode ISO-8859-1: s: ", repr(s))
		except:
			try:
				s = unicode(s, 'utf-8')
				s = s.encode('ISO-8859-1')
				splog("WL: str_to_utf8 decode utf-8: s: ", repr(s))
			except:
				try:
					s = unicode(s, 'cp1252')
					s = s.encode('ISO-8859-1')
					splog("WL: str_to_utf8 decode cp1252: s: ", repr(s))
				except:
					s = unicode(s, 'utf-8', 'ignore')
					s = s.encode('ISO-8859-1')
					splog("WL: str_to_utf8 decode utf-8 ignore: s: ", repr(s))
	else:
		try:
			s = s.encode('ISO-8859-1')
			splog("WL: str_to_utf8 encode ISO-8859-1: s: ", repr(s))
		except:
			s = s.encode('ISO-8859-1', 'ignore')
			splog("WL: str_to_utf8 except encode ISO-8859-1 ignore: s: ", repr(s))
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
		
		self.begin = begin
		self.end = end
		self.service = service
		
		self.knownids = []
		self.returnvalue = None
		
		# Check preconditions
		if not name:
			splog(_("Skip Wunschliste: No show name specified"))
			return _("Skip Wunschliste: No show name specified")
		if not begin:
			splog(_("Skip Wunschliste: No begin timestamp specified"))
			return _("Skip Wunschliste: No begin timestamp specified")
		
		splog("WunschlistePrint getEpisode")
		
		while name:	
			ids = self.getSeries(name)
			
			while ids:
				idserie = ids.pop()
				
				if idserie and len(idserie) == 2:
					id, idname = idserie
					
					# Handle encodings
					self.series = str_to_utf8(idname)
					
					result = self.getNextPage( id )
					if result:
						return result
					
			else:
				name = self.getAlternativeSeries(name)
		
		else:
			return ( self.returnvalue or _("No matching series found") )

	def getSeries(self, name):
		#url = SERIESLISTURL + urlencode({ 'q' : re.sub("[^a-zA-Z0-9-*]", " ", name) })
		url = SERIESLISTURL + urlencode({ 'q' : name })
		data = self.getPage( url )
		
		if data and isinstance(data, basestring):
			data = self.parseSeries(data)
			self.doCacheList(url, data)
		
		if data and isinstance(data, list):
			splog("WunschlistePrint ids", data)
			return self.filterKnownIds(data)

	def parseSeries(self, data):
		serieslist = []
		for line in data.splitlines():
			values = line.split("|")
			if len(values) == 4:
				idname, countryyear, id, temp = values
				splog(id, idname)
				serieslist.append( (id, idname) )
			else:
				splog("WunschlistePrint: ParseError: " + str(line))
		serieslist.reverse()
		return serieslist

	def parseNextPage(self, data):
		# Handle malformed HTML issues
		#data = data.replace('&quot;','&')
		data = data.replace('&amp;','&')
		parser = WLPrintParser()
		parser.feed(data)
		#splog(parser.list)
		return parser.list

	def getNextPage(self, id):
		splog("WunschlistePrint getNextPage")
		
		url = EPISODEIDURLPRINT + urlencode({ 's' : id })
		data = self.getPage( url )
		
		if data and isinstance(data, basestring):
			data = self.parseNextPage(data)
			self.doCacheList(url, data)
		
		if data and isinstance(data, list):
			trs = data
			
			yepisode = None
			ydelta = maxint
			actual_year = self.actual_year
			
			for tds in trs:
				if tds and len(tds) >= 5:
					#print tds
					xchannel, xday, xdate, xbegin, xend = tds[:5]
					xtitle = "".join(tds[4:])
					if self.actual_month == 12 and xdate.endswith(".01."):
						year = str(self.actual_year+1)
					else:
						year = str(self.actual_year)
					xbegin   = datetime.strptime( xdate+year+" "+xbegin, "%d.%m.%Y %H.%M Uhr" )
					#xend     = datetime.strptime( xdate+xend, "%d.%m.%Y%H.%M Uhr" )
					#splog(xchannel, xdate, xbegin, xend, xtitle)
					#splog(datebegin, xbegin, abs((datebegin - xbegin)))
					
					#Py2.6
					delta = abs(self.begin - xbegin)
					delta = delta.seconds + delta.days * 24 * 3600
					#Py2.7 delta = abs(self.begin - xbegin).total_seconds()
					splog(self.begin, xbegin, delta, self.max_time_drift)
					
					if delta <= self.max_time_drift:
						
						if self.compareChannels(self.service, xchannel):
						
							if delta < ydelta:
								
								print len(tds), tds
								if len(tds) >= 7:
									xepisode, xtitle = tds[5:7]
								
									if xepisode:
										result = CompiledRegexpEpisode.search(xepisode)
										
										if result and len(result.groups()) >= 3:
											xseason = result and result.group(2) or "1"
											xepisode = result and result.group(3) or "0"
										else:
											xseason = "1"
											xepisode = "0"
									else:
										xseason = "1"
										xepisode = "0"
								
								elif len(tds) == 6:
									xtitle = tds[5]
									xseason = "0"
									xepisode = "0"
								
								# Handle encodings
								xtitle = str_to_utf8(xtitle)
								
								yepisode = (xseason, xepisode, xtitle, self.series)
								ydelta = delta
							
							else: #if delta >= ydelta:
								break
						
						else:
							self.returnvalue = _("Check the channel name")
						
					elif yepisode:
						break
			
			if yepisode:
				return ( yepisode )
