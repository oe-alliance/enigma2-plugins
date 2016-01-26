# -*- coding: utf-8 -*-
# by betonme @2012

# Imports
import os, sys
import re
import math

from sys import maxint

from Components.config import config
from Tools.BoundFunction import boundFunction

from urllib import urlencode
from urllib2 import urlopen

from time import time, mktime
from datetime import datetime, timedelta

# Internal
from Plugins.Extensions.SeriesPlugin.IdentifierBase import IdentifierBase
from Plugins.Extensions.SeriesPlugin.Logger import logDebug, logInfo
from Plugins.Extensions.SeriesPlugin import _

try:
	import json
except ImportError as ie:
	json = None

try:
	from bs4 import BeautifulSoup
except ImportError as ie:
	BeautifulSoup = None
	
# Constants
SERIESLISTURL = "http://www.fernsehserien.de/suche?"
EPISODEIDURL = 'http://www.fernsehserien.de%s/sendetermine/%s'

# Remote column mapping
#OLD trs[x] = [None,        u'31.10.2012', u'20:15\u201321:15 Uhr', u'ProSieben',                     u'8.', u'15',       u'Richtungswechsel']
#NEW trs[x] = [None, u'So', u'31.10.2012', u'20:15\u201321:15',     u'ProSieben', None, u'216', None, u'8.', u'15', None, u'Richtungswechsel']
TDS_DATE = 2
TDS_TIME = 3
TDS_CHANNEL = 4
#TDS_ABS_EPISODE = 6
TDS_SEASON = 8
TDS_EPISODE = 9
TDS_TITLE = 11

# Local column mapping
COL_TITLE = 0
COL_CHANNEL = 1
COL_SEASON = 2
COL_EPISODE = 3
COL_DATETIME = 4
COL_SIZE = 5

CompiledRegexpNonASCII = re.compile('\xe2\x80')


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
		
		
		# Check dependencies
		if json is None:
			msg = _("Error install")  + " python-json"
			logInfo(msg)
			return msg
		if BeautifulSoup is None:
			msg = _("Error install")  + " BeautifulSoup"
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
		
		
		logInfo("FS: getEpisode, name, begin, end=None, service", name, begin, end, service)
		
		self.begin = begin
		#self.date = str(begin.month) + "." + str(begin.day) + "."
		self.year = begin.year
		#self.end = end
		
		self.service = service
		
		self.series = ""
		self.first_on_prev_page = None
		self.last_on_prev_page = None
		
		self.td_max_time_drift = timedelta(seconds=self.max_time_drift)
		
		self.knownids = []
		self.returnvalue = None
		
		
		# True = future 
		# False = past
		if self.begin > datetime.now():
			self.direction = True
		else:
			self.direction = False
		logDebug("FS: getEpisode direction", self.direction)
		
		
		while name:	
			ids = self.getSeries(name)
			
			while ids:
				idserie = ids.pop()
				
				if idserie and len(idserie) == 2:
					id, idname = idserie
					
					# Handle encodings
					self.series = str_to_utf8(idname)
					logInfo("FS: Possible matched series:", self.series)
					
					if self.direction:
						# The future starts now
						page = 0
					else:
						if self.actual_year == self.year:
							# On realtime conditions we could start at page -1
							# But the proxy is caching every page for about 24 hours, so we start at page 0
							page = 0
						else:
							# We can retrieve the offset of every year to skip several pages
							page = 0
							
							# Sample
							#http://www.fernsehserien.de/criminal-intent-verbrechen-im-visier/sendetermine/
							year_base_url = EPISODEIDURL % (id, '')
							logDebug("FS: year_base_url: ", year_base_url)
							
							# Increment year by one, because we want to start at the end of the year
							year = self.year+1
							
							# Sample
							#http://www.fernsehserien.de/criminal-intent-verbrechen-im-visier/sendetermine/jahr-2014
							year_url = year_base_url+"jahr-"+str(year)
							logDebug("FS: year_url: ", year_url)
							
							from Plugins.Extensions.SeriesPlugin.plugin import buildURL
							response = urlopen( buildURL(year_url) )
							
							# Sample
							#http://www.fernsehserien.de/criminal-intent-verbrechen-im-visier/sendetermine/-14
							redirect_url = response.geturl()
							logDebug("FS: redirect_url: ", redirect_url)
							
							try:
								# Sample -14
								page = int( redirect_url.replace(year_base_url,'') )
							except:
								page = 0
					
					self.first_on_prev_page = None
					self.last_on_prev_page = None
					
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
		
		
		# Idea:
		# Search for the date string and skip parsing, but how can we detect the end
		#if data.find( self.date ) == -1:
		#	logDebug( "FS: Skip page because of date check")
		#	return trs
		
		
		# Handle malformed HTML issues
		data = data.replace('\\"','"')  # target=\"_blank\"
		data = data.replace('\'+\'','') # document.write('<scr'+'ipt
		
		
		soup = BeautifulSoup(data)
		
		
		# On some pages the date is listed without the year
		div = soup.find('div', 'gray-bar-header nicht-nochmal')
		if div and div.string:
			year_of_page = int( div.string[6:11].strip() )
			logDebug( "FS: year by div", year_of_page)
		else:
			year_of_page = self.year
			logInfo( "FS: year not found", year_of_page)
		
		
		table = soup.find('table', 'sendetermine')
		if table:
			
			tds_date = ""
			tds_time = ""
			act_month = 0
			prev_month = 0
			tds = [""]*COL_SIZE
			
			for trnode in table.find_all('tr'):
				
				tdnodes = trnode and trnode.find_all('td')
				if tdnodes:
					
					# Filter for known rows
					if len(tdnodes) == 12:
						
						for idx, tdnode in enumerate(tdnodes):
							#logDebug( "FS: tdnode:", idx, str(tdnode))
							
							if not tdnode:
								continue
							
							if tdnode.string:
								td = tdnode.string.strip()
							else:
								td = ""
							#logDebug( "FS: td:", idx, str(td))
							
							if idx == TDS_DATE:
								# 01.11.2015 [0:11]
								tds_date = td[0:11].strip()
								
								if tds_date == "&nbsp;":
									logDebug( "FS: Skip tdnode date nbsp:", len(tds_date), tds_date, td)
									continue
								
								if tds_date.find('\xc2\xa0') != -1:
									logDebug( "FS: Skip tdnode date xc2xa0:", len(tds_date), tds_date, td)
									continue
								
								dlen = len(tds_date)
								
								# Check for uncomplete date stings
								if dlen != 11:
									
									act_month = int(tds_date[3:5])
									
									# 31.12.2014 - 12
									# 01.01.2015 - 01
									if prev_month == 12 and act_month == 1:
										# Next year
										year_of_page += 1
										year = str(year_of_page)
									
									# 01.01.2015 - 01
									# 31.12.2014 - 12
									elif prev_month == 1 and act_month == 12:
										# Previous year
										year_of_page -= 1
										year = str(year_of_page)
									
									else:
										# Default to same year
										year = str(year_of_page)
									
									prev_month = act_month
									
									# Check for 25.11
									if dlen == 5:
										tds_date += "." + year
									
									# Check for 25.11.
									elif dlen == 6:
										tds_date += year
							
							elif idx == TDS_TIME:
								# We only check the begin time
								# 20:15-21:05 [ : ]
								# 20:15       [0:5]
								tds_time = td[0:5].strip()
								
								if tds_time == "&nbsp;":
									logDebug( "FS: Skip tdnode time nbsp:", len(tds_time), tds_time, td)
									continue
								
								if tds_time.find('\xc2\xa0') != -1:
									logDebug( "FS: Skip tdnode time xc2xa0:", len(tds_time), tds_time, td)
									continue
							
							elif idx == TDS_CHANNEL:
								spans = tdnode.find_all('span')
								#logDebug( "FS: tdnode:", str(td), str(spans))
								if spans:
									for span in spans:
										tds[COL_CHANNEL] = span.get('title', '').strip()
										break
								else:
									tds[COL_CHANNEL] = td
							
							elif idx == TDS_SEASON:
								tds[COL_SEASON] = td
							
							elif idx == TDS_EPISODE:
								tds[COL_EPISODE] = td
							
							elif idx == TDS_TITLE:
								tds[COL_TITLE] = td
						
						tds_datetime = tds_date
						tds_datetime += tds_time
						if len(tds_datetime) != 15:
							logDebug( "FS: Skip tdnode length datetime != 15:", len(tds_datetime), tds_datetime)
							continue
						
						tds[COL_DATETIME] = tds_datetime
						
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
			
			# Set preconditions
			yepisode = None
			ydelta = maxint
			
			
			# Idea:
			# Sort the trs by datetime to avoid the direction handling
			# But the overhead of calculating the datetime and sorting them is too big
			
			
			first_on_page = parseDate( trs[0][COL_DATETIME] )
			last_on_page = parseDate( trs[-1][COL_DATETIME] )
			
			
			# Check if we got a new page
			# You can increment/decrement the paging number endless and You will always receive the last valid page which is never changing
			if page == 0:
				new_page = True
				logDebug("FS: first_on_page, last_on_page: ", first_on_page, last_on_page)
			else:
				new_page = (self.first_on_prev_page != first_on_page or self.last_on_prev_page != last_on_page)
				logDebug("FS: first_on_prev_page, first_on_page, last_on_prev_page, last_on_page, if: ", self.first_on_prev_page, first_on_page, self.last_on_prev_page, last_on_page, new_page)
			
			self.first_on_prev_page = first_on_page
			self.last_on_prev_page = last_on_page				
			
			
			if new_page:
				
				
				# Check direction because the sort order (datetime) will change
				# True = future 
				# False = past
				direction = first_on_page < last_on_page
				
				if direction:
					# True = future 
					# 2015-11-04 - first_on_page
					# 2015-11-05 - self.begin
					# 2015-11-06 - last_on_page
					test_timespan = ( (first_on_page-self.td_max_time_drift) <= self.begin and self.begin <= (last_on_page+self.td_max_time_drift) )
				else:
					# False = past
					# 2015-11-04 - first_on_page
					# 2015-11-05 - self.begin
					# 2015-11-06 - last_on_page
					test_timespan = ( (first_on_page+self.td_max_time_drift) >= self.begin and self.begin >= (last_on_page-self.td_max_time_drift) )
				
				
				logDebug("FS: first_on_page, self.begin, last_on_page, basedirection, direction, if:", first_on_page, '-', self.begin, '-', last_on_page, '-', self.direction, '-', direction, '-', test_timespan )
				if ( test_timespan ):
					
					for tds in trs:
						
						#logDebug( "FS: tds", tds )
						
						xbegin = parseDate( tds[COL_DATETIME] )
						
						#Py2.6
						delta = abs(self.begin - xbegin)
						delta = delta.seconds + delta.days * 24 * 3600
						#Py2.7 
						#delta = abs(self.begin - xbegin).total_seconds()
						logDebug("FS:", self.begin, '-', xbegin, '-', delta, '-', self.max_time_drift)
						
						# delta is an absolute value so we can just do a smaller than check
						if delta <= self.max_time_drift:
							
							logInfo("FS: Possible match witch channel: ", tds[COL_CHANNEL])
							if self.compareChannels(self.service, tds[COL_CHANNEL]):
								
								if delta < ydelta:
									
									yepisode = (
													tds[COL_SEASON] or config.plugins.seriesplugin.default_season.value, 
													tds[COL_EPISODE] or config.plugins.seriesplugin.default_episode.value, 
													str_to_utf8(tds[COL_TITLE]), 
													self.series
												)
									ydelta = delta
									
									# continue and check one further entry maybe we will find a closer match with a smaller delta time
									
								else: #if delta >= ydelta:
									return ( yepisode )
							
							else:
								self.returnvalue = _("Check the channel name") + " " + tds[COL_CHANNEL]
							
						else:
							if yepisode:
								return ( yepisode )
							
							if delta <= 600:
								# Compare channels?
								logInfo("FS: Max time trift exceeded", delta)
					
					if yepisode:
						return ( yepisode )
				
				else:
					
					# Idea:
					# Maybe we can guess the next page using firstrow lastrow datetime
					
					if self.direction:
						# True = future 
						# 2015-11-04 - first_on_page
						# 2015-11-05 - 
						# 2015-11-06 - last_on_page
						# 2015-11-07 - self.begin
						if self.begin > last_on_page:
							return self.getNextPage(id, page+1)
					
					else:
						# False = past
						# 2015-11-03 - self.begin
						# 2015-11-04 - first_on_page
						# 2015-11-05 - 
						# 2015-11-06 - last_on_page
						if first_on_page > self.begin:
							return self.getNextPage(id, page-1)

		else:
			logInfo("FS: No data returned")
		
		# Nothing found
		return
