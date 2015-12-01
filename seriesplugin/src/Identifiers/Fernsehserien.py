# -*- coding: utf-8 -*-
# by betonme @2012

import os, sys
import json
import re
import math

from sys import maxint

from Components.config import config
from Tools.BoundFunction import boundFunction

# Imports
from urllib import urlencode
from urllib2 import urlopen

from time import time, mktime
from datetime import datetime, timedelta

# Internal
from Plugins.Extensions.SeriesPlugin.IdentifierBase import IdentifierBase
from Plugins.Extensions.SeriesPlugin.Logger import logDebug, logInfo
from Plugins.Extensions.SeriesPlugin import _

from bs4 import BeautifulSoup
from HTMLParser import HTMLParser

#import codecs
#utf8_encoder = codecs.getencoder("utf-8")


# Constants
SERIESLISTURL = "http://www.fernsehserien.de/suche?"
EPISODEIDURL = 'http://www.fernsehserien.de%s/sendetermine/%s'

#OLD trs[x] = [None,        u'31.10.2012', u'20:15\u201321:15 Uhr', u'ProSieben',                     u'8.', u'15',       u'Richtungswechsel']
#NEW trs[x] = [None, u'So', u'31.10.2012', u'20:15\u201321:15',     u'ProSieben', None, u'216', None, u'8.', u'15', None, u'Richtungswechsel']
TDS_DATE = 2
TDS_TIME = 3
TDS_CHANNEL = 4
#TDS_ABS_EPISODE = 6
TDS_SEASON = 8
TDS_EPISODE = 9
TDS_TITLE = 11

COL_TITLE = 0
COL_CHANNEL = 1
COL_SEASON = 2
COL_EPISODE = 3
COL_DATETIME = 4
COL_SIZE = 5

CompiledRegexpNonASCII = re.compile('\xe2\x80.')


def str_to_utf8(s):
	# Convert a byte string with unicode escaped characters
	logDebug("FS: str_to_utf8: s: ", repr(s))
	#unicode_str = s.decode('unicode-escape')
	#logDebug("FS: str_to_utf8: s: ", repr(unicode_str))
	## Python 2.x can't convert the special chars nativly
	#utf8_str = utf8_encoder(unicode_str)[0]
	#logDebug("FS: str_to_utf8: s: ", repr(utf8_str))
	#return utf8_str  #.decode("utf-8").encode("ascii", "ignore")
	if type(s) == unicode:
		# Default shoud be here
		try:
			s = s.encode('utf-8')
			logDebug("FS: str_to_utf8 encode utf8: s: ", repr(s))
		except:
			s = s.encode('utf-8', 'ignore')
			logDebug("FS: str_to_utf8 except encode utf8 ignore: s: ", repr(s))
	else:
		try:
			s = s.decode('utf-8')
			logDebug("FS: str_to_utf8 decode utf8: s: ", repr(s))
		except:
			try:
				s = unicode(s, 'ISO-8859-1')
				s = s.encode('utf-8')
				logDebug("FS: str_to_utf8 decode ISO-8859-1: s: ", repr(s))
			except:
				try:
					s = unicode(s, 'cp1252')
					s = s.encode('utf-8')
					logDebug("FS: str_to_utf8 decode cp1252: s: ", repr(s))
				except:
					s = unicode(s, 'ISO-8859-1', 'ignore')
					s = s.encode('utf-8')
					logDebug("FS: str_to_utf8 decode ISO-8859-1 ignore: s: ", repr(s))
	s = s.replace('\xe2\x80\x93','-').replace('\xe2\x80\x99',"'").replace('\xc3\x9f','ß')
	return CompiledRegexpNonASCII.sub('', s)

def parseDate(datetimestr):
	return datetime.strptime( datetimestr, "%d.%m.%Y%H:%M" )


class Fernsehserien(IdentifierBase):
	def __init__(self):
		IdentifierBase.__init__(self)

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
		
		self.begin = begin
		#self.date = str(begin.month) + "." + str(begin.day) + "."
		self.year = begin.year
		#self.end = end
		
		self.service = service
		
		self.series = ""
		self.first = None
		self.last = None
		
		self.td_max_time_drift = timedelta(seconds=self.max_time_drift)
		
		self.knownids = []
		self.returnvalue = None
		
		# Check preconditions
		if not name:
			logInfo(_("FS: Skip Fernsehserien: No show name specified"))
			return _("Skip Fernsehserien: No show name specified")
		if not begin:
			logInfo(_("FS: Skip Fernsehserien: No begin timestamp specified"))
			return _("Skip Fernsehserien: No begin timestamp specified")
		
		logInfo("Fernsehserien getEpisode, name, begin, end=None, service", name, begin, end, service)
		
		if self.begin > datetime.now():
			self.future = True
		else:
			self.future = False
		logDebug("FS: Fernsehserien getEpisode future", self.future)
	
		while name:	
			ids = self.getSeries(name)
			
			while ids:
				idserie = ids.pop()
				
				if idserie and len(idserie) == 2:
					id, idname = idserie
					
					# Handle encodings
					self.series = str_to_utf8(idname)
					logInfo("Possible matched series:", self.series)
					
					if self.future:
						page = 0
					else:
						if self.actual_year == self.year:
							#if self.begin > self.now-timedelta(seconds=3600):
							page = 0
							#else:
							#	page = -1
						else:
							page = 0
							
							year_base_url = EPISODEIDURL % (id, '')
							logDebug("FS: year_base_url: ", year_base_url)
							
							year_url = year_base_url+"jahr-"+str(self.year+1)
							logDebug("FS: year_url: ", year_url)
							
							#/sendetermine/jahr-2014
							# Increment year by one, because we want to start at the end of the year
							from Plugins.Extensions.SeriesPlugin.plugin import buildURL
							response = urlopen( buildURL(year_url) )
							
							#redirecturl = http://www.fernsehserien.de/criminal-intent-verbrechen-im-visier/sendetermine/-14
							redirect_url = response.geturl()
							logDebug("FS: redirect_url: ", redirect_url)
							
							try:
								page = int( redirect_url.replace(year_base_url,'') )
							except:
								page = 0
					
					self.first = None
					self.last = None
					
					if page is not None:
						result = self.getNextPage(id, page)
						if result:
							return result
					
			else:
				name = self.getAlternativeSeries(name)
		
		else:
			return ( self.returnvalue or _("No matching series found") )

	def getSeries(self, name):
		parameter =  urlencode({ 'term' : re.sub("[^a-zA-Z0-9*]", " ", name) })
		url = SERIESLISTURL + parameter
		data = self.getPage(url)
		
		if data and isinstance(data, basestring):
			data = self.parseSeries(data)
			self.doCacheList(url, data)
		
		if data and isinstance(data, list):
			logDebug("FS: ids", data)
			return self.filterKnownIds(data)

	def parseSeries(self, data):
		serieslist = []
		#logDebug( "FS: parseSeries", data)
		for line in json.loads(data):
			id = line['id']
			idname = line['value']
			logDebug("FS: ", id, idname)
			if not idname.endswith("/person"):
				serieslist.append( ( id, idname ) )
		serieslist.reverse()
		return serieslist

	def parseNextPage(self, data):
		trs = []
		
		# Search for the date string and skip, but how can we detect the end
		#if data.find( self.date ) == -1:
		#	logDebug( "FS: Skip page because of date check")
		#	return trs
		
		# Handle malformed HTML issues
		data = data.replace('\\"','"')  # target=\"_blank\"
		data = data.replace('\'+\'','') # document.write('<scr'+'ipt
		
		soup = BeautifulSoup(data)
		
		div = soup.find('div', 'gray-bar-header nicht-nochmal')
		if div and div.string:
			year = div.string[6:11].strip()
			logDebug( "FS: year by div", year)
		else:
			year = self.year
			logDebug( "FS: year not found", year)
		
		table = soup.find('table', 'sendetermine')
		if table:
			
			tds = [""]*COL_SIZE
			
			for trnode in table.find_all('tr'):
				
				tdnodes = trnode and trnode.find_all('td')
				if tdnodes:
					
					# Filter for known rows
					if len(tdnodes) == 12:
						
						for idx, tdnode in enumerate(tdnodes):
							
							if not tdnode or not tdnode.string:
								continue
							
							td = tdnode.string.strip()
							#logDebug( "FS: tdnode:", str(td))
							
							if idx == TDS_DATE:
								tds_date = td[0:11].strip()
								
								if tds_date == "&nbsp;":
									continue
								
								if tds_date.find('\xc2\xa0') != -1:
									continue
								
								#Check for 25.11
								dlen = len(tds_date)
								if dlen == 5:
									tds_date += "." + year
								#Check for 25.11.
								elif dlen == 6:
									tds_date += year
								
								tds[COL_DATETIME] = tds_date
							
							elif idx == TDS_TIME:
								tds_time = td[0:5].strip()
								
								if tds_time == "&nbsp;":
									logDebug( "FS: Skip tdnode time nbsp:", len(tds_time), tds_time, td)
									continue
								
								if tds_time.find('\xc2\xa0') != -1:
									logDebug( "FS: Skip tdnode time xc2xa0:", len(tds_time), tds_time, td)
									continue
								
								tds[COL_DATETIME] += tds_time
							
							elif idx == TDS_CHANNEL:
								spans = tdnode.find('span')
								if spans:
									tds[COL_CHANNEL] = spans.get('title', '').strip()
								else:
									tds[COL_CHANNEL] = td
							
							elif idx == TDS_SEASON:
								tds[COL_SEASON] = td
							
							elif idx == TDS_EPISODE:
								tds[COL_EPISODE] = td
							
							elif idx == TDS_TITLE:
								tds[COL_TITLE] = td
						
						if len(tds[COL_DATETIME]) != 15:
							logDebug( "FS: Skip tdnode length datetime != 15:", len(tds[COL_DATETIME]), tds[COL_DATETIME])
							continue
						
						logDebug( "FS: table tds", tds)
						trs.append( tds[:] )
					
					else:
						if len(tdnodes) != 2:
							td = ""
							for tdnode in tdnodes:
								td += "[" + str(tdnode.string).strip() + "]"
							logDebug( "FS: length tdnodes != 12:", len(tdnodes), td)
					
				else:
					logDebug( "FS: No tdnodes")
				
		else:
			logDebug( "FS: table not found")
		
		#logDebug("FS: ", trs)
		return trs

	def getNextPage(self, id, page):
		url = EPISODEIDURL % (id, page)
		data = self.getPage(url)
		
		if data and isinstance(data, basestring):
			logDebug("FS: getNextPage: basestring")
			data = self.parseNextPage(data)
			self.doCacheList(url, data)
		
		if data and isinstance(data, list):
			logDebug("FS: getNextPage: list")
			
			trs = data
			
			yepisode = None
			ydelta = maxint
			
			first = parseDate( trs[0][COL_DATETIME] )
			last = parseDate( trs[-1][COL_DATETIME] )
			
			if page != 0:
				new_page = (self.first != first or self.last != last)
				logDebug("FS: getNextPage: first_on_prev_page, first, last_on_prev_page, last, if: ", self.first, first, self.last, last, new_page)
				self.first = first
				self.last = last
			else:
				new_page = True
			
			if new_page:
				test_future_timespan = ( (first-self.td_max_time_drift) <= self.begin and self.begin <= (last+self.td_max_time_drift) )
				test_past_timespan = ( (first+self.td_max_time_drift) >= self.begin and self.begin >= (last-self.td_max_time_drift) )
				
				logDebug("FS: first_on_page, self.begin, last_on_page, if, if:", first, self.begin, last, test_future_timespan, test_past_timespan )
				if ( test_future_timespan or test_past_timespan ):
					
					for tds in trs:
						
						#logDebug( "FS: tds", tds )
						
						xbegin = parseDate( tds[COL_DATETIME] )
						
						#Py2.6
						delta = abs(self.begin - xbegin)
						delta = delta.seconds + delta.days * 24 * 3600
						#Py2.7 delta = abs(self.begin - xbegin).total_seconds()
						logDebug("FS: ", self.begin, xbegin, delta, self.max_time_drift)
						
						if delta <= self.max_time_drift:
							
							logInfo("Possible match witch channel: ", tds[COL_CHANNEL])
							if self.compareChannels(self.service, tds[COL_CHANNEL]):
								
								if delta < ydelta:
									
									xseason = tds[COL_SEASON] or config.plugins.seriesplugin.default_season.value
									xepisode = tds[COL_EPISODE] or config.plugins.seriesplugin.default_episode.value
									xtitle = str_to_utf8(tds[COL_TITLE])
									
									yepisode = (xseason, xepisode, xtitle, self.series)
									ydelta = delta
								
								else: #if delta >= ydelta:
									break
							
							else:
								self.returnvalue = _("Check the channel name") + " " + tds[COL_CHANNEL]
							
						elif yepisode:
							break
					
					if yepisode:
						return ( yepisode )
				
				else:
					# TODO calculate next page : use firstrow lastrow datetime
					if not self.future:
						if first > self.begin:
							page -= 1
							return self.getNextPage(id, page)
					
					else:
						if self.begin > last:
							page += 1
							return self.getNextPage(id, page)
		
		return
