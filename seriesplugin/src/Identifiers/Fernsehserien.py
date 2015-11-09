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

from time import time
from datetime import datetime, timedelta

# Internal
from Plugins.Extensions.SeriesPlugin.IdentifierBase import IdentifierBase
from Plugins.Extensions.SeriesPlugin.Logger import splog

from bs4 import BeautifulSoup
from HTMLParser import HTMLParser

#import codecs
#utf8_encoder = codecs.getencoder("utf-8")


# Constants
SERIESLISTURL = "http://www.fernsehserien.de/suche?"
EPISODEIDURL = 'http://www.fernsehserien.de%s/sendetermine/%s'

#OLD trs[x] = [None,        u'31.10.2012', u'20:15\u201321:15 Uhr', u'ProSieben',                     u'8.', u'15',       u'Richtungswechsel']
#NEW trs[x] = [None, u'So', u'31.10.2012', u'20:15\u201321:15',     u'ProSieben', None, u'216', None, u'8.', u'15', None, u'Richtungswechsel']
COL_DATE = 2
COL_TIME = 3
COL_CHANNEL = 4
#COL_ABS_EPISODE = 6
COL_SEASON = 8
COL_EPISODE = 9
COL_TITLE = 11

CompiledRegexpNonASCII = re.compile('\xe2\x80.')


def str_to_utf8(s):
	# Convert a byte string with unicode escaped characters
	splog("FS: str_to_utf8: s: ", repr(s))
	#unicode_str = s.decode('unicode-escape')
	#splog("FS: str_to_utf8: s: ", repr(unicode_str))
	## Python 2.x can't convert the special chars nativly
	#utf8_str = utf8_encoder(unicode_str)[0]
	#splog("FS: str_to_utf8: s: ", repr(utf8_str))
	#return utf8_str  #.decode("utf-8").encode("ascii", "ignore")
	if type(s) == unicode:
		# Default shoud be here
		try:
			s = s.encode('utf-8')
			splog("FS: str_to_utf8 encode utf8: s: ", repr(s))
		except:
			s = s.encode('utf-8', 'ignore')
			splog("FS: str_to_utf8 except encode utf8 ignore: s: ", repr(s))
	else:
		try:
			s = s.decode('utf-8')
			splog("FS: str_to_utf8 decode utf8: s: ", repr(s))
		except:
			try:
				s = unicode(s, 'ISO-8859-1')
				s = s.encode('utf-8')
				splog("FS: str_to_utf8 decode ISO-8859-1: s: ", repr(s))
			except:
				try:
					s = unicode(s, 'cp1252')
					s = s.encode('utf-8')
					splog("FS: str_to_utf8 decode cp1252: s: ", repr(s))
				except:
					s = unicode(s, 'ISO-8859-1', 'ignore')
					s = s.encode('utf-8')
					splog("FS: str_to_utf8 decode ISO-8859-1 ignore: s: ", repr(s))
	s = s.replace('\xe2\x80\x93','-').replace('\xe2\x80\x99',"'").replace('\xc3\x9f','ß')
	return CompiledRegexpNonASCII.sub('', s)


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
		self.year = begin.year
		self.end = end
		self.service = service
		
		self.series = ""
		self.first = None
		self.last = None
		self.page = 0
		
		self.td_max_time_drift = timedelta(seconds=self.max_time_drift)
		
		self.knownids = []
		self.returnvalue = None
		
		# Check preconditions
		if not name:
			splog(_("FS: Skip Fernsehserien: No show name specified"))
			return _("Skip Fernsehserien: No show name specified")
		if not begin:
			splog(_("FS: Skip Fernsehserien: No begin timestamp specified"))
			return _("Skip Fernsehserien: No begin timestamp specified")
		
		if self.begin > datetime.now():
			self.future = True
		else:
			self.future = False
		splog("FS: Fernsehserien getEpisode future", self.future)
	
		while name:	
			ids = self.getSeries(name)
			
			while ids:
				idserie = ids.pop()
				
				if idserie and len(idserie) == 2:
					id, idname = idserie
					
					# Handle encodings
					self.series = str_to_utf8(idname)
					
					#self.page = 0
					if self.future:
						self.page = 0
					else:
						if self.actual_year == self.year:
							#if self.begin > self.now-timedelta(seconds=3600):
							self.page = 0
							#else:
							#	self.page = -1
						else:
							self.page = 0
							
							year_base_url = EPISODEIDURL % (id, '')
							splog("FS: year_base_url: ", year_base_url)
							
							year_url = year_base_url+"jahr-"+str(self.year+1)
							splog("FS: year_url: ", year_url)
							
							#/sendetermine/jahr-2014
							# Increment year by one, because we want to start at the end of the year
							from Plugins.Extensions.SeriesPlugin.plugin import buildURL
							response = urlopen( buildURL(year_url) )
							
							#redirecturl = http://www.fernsehserien.de/criminal-intent-verbrechen-im-visier/sendetermine/-14
							redirect_url = response.geturl()
							splog("FS: redirect_url: ", redirect_url)
							
							try:
								self.page = int( redirect_url.replace(year_base_url,'') )
							except:
								self.page = 0
					
					self.first = None
					self.last = None
					
					while self.page is not None:
						result = self.getNextPage(id)
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
			splog("FS: ids", data)
			return self.filterKnownIds(data)

	def parseSeries(self, data):
		serieslist = []
		#splog( "FS: parseSeries", data)
		for line in json.loads(data):
			id = line['id']
			idname = line['value']
			splog("FS: ", id, idname)
			if not idname.endswith("/person"):
				serieslist.append( ( id, idname ) )
		serieslist.reverse()
		return serieslist

	def parseNextPage(self, data):
		trs = []
		
		# Handle malformed HTML issues
		data = data.replace('\\"','"')  # target=\"_blank\"
		data = data.replace('\'+\'','') # document.write('<scr'+'ipt
		
		soup = BeautifulSoup(data)
		
		div = soup.find('div', 'gray-bar-header nicht-nochmal')
		if div and div.string:
			year = div.string[-4:]
			splog( "FS: year by div", year)
		else:
			year = self.year
			splog( "FS: year not found", year)
		
		table = soup.find('table', 'sendetermine')
		if table:
			for trnode in table.find_all('tr'):
				
				tdnodes = trnode and trnode.find_all('td')
				if tdnodes:
					# Filter for known rows
					if len(tdnodes) == 12:
						tds = []
						
						for idx, tdnode in enumerate(tdnodes):
							if tdnode is None:
								splog( "FS: Error: tdnode is none" )
								return []
							
							if idx == COL_TIME:
								tds.append( tdnode.string[0:5] )
							elif idx == COL_DATE:
								tds.append( tdnode.string[0:11] )
							elif idx == COL_CHANNEL:
								#tds[COL_CHANNEL] = tdnode[COL_CHANNEL]['title']
								spans = tdnode.find('span')
								if spans:
									#splog( "FS: spans", len(spans), spans)
									tds.append( spans.get('title', '') )
								else:
									tds.append(tdnode.string or "")
							else:
								tds.append(tdnode.string or "")
						
						if tds[COL_TIME].find('\xc2\xa0') != -1:
							#splog( "FS: tdnodes xc2xa0", len(tdnodes), tdnodes)
							continue
						if tds[COL_DATE].find('\xc2\xa0') != -1:
							#splog( "FS: tdnodes xc2xa0", len(tdnodes), tdnodes)
							continue
						
						tds.append( year )
						#splog( "FS: table tds", tds)
						trs.append( tds )
					
					# This row belongs to the previous
					#TODO
					#elif trs and len(tdnodes) == 5:
					#	trs[-1][5] += ' ' + (tdnodes[3].string or "")
					#	trs[-1][6] += ' ' + (tdnodes[4].string or "")
					#else:
					#	splog( "FS: tdnodes", len(tdnodes), tdnodes)
				
				#else:
				#	splog( "FS: tdnodes", tdnodes )
		
			#http://www.fernsehserien.de/weisst-du-eigentlich-wie-lieb-ich-dich-hab/sendetermine/-1
			for idx,tds in enumerate(trs):
				if tds[COL_TIME] == "&nbsp;":
					if idx > 0:
						tds[COL_TIME] = trs[idx-1][COL_TIME]
				if tds[COL_DATE] == "&nbsp;":
					if idx > 0:
						tds[COL_DATE] = trs[idx-1][COL_DATE]
		else:
			splog( "FS: table not found")
		
		#splog("FS: ", trs)
		return trs

	def getNextPage(self, id):
		url = EPISODEIDURL % (id, self.page)
		data = self.getPage(url)
		
		if data and isinstance(data, basestring):
			splog("FS: getNextPage: basestring")
			data = self.parseNextPage(data)
			self.doCacheList(url, data)
		
		if data and isinstance(data, list):
			splog("FS: getNextPage: list")
			
			trs = data
			
			yepisode = None
			ydelta = maxint
			
			#first = trs[0][2]
			#last = trs[-1][2]
			#print first[0:5]
			#print last[6:11] 
			
			# trs[0] first line [2] second element = timestamps [a:b] use first time
			cust_date = trs[0][COL_TIME] + trs[0][COL_DATE]
			if len(cust_date) == 11:
				cust_date += trs[0][-1]
			#splog("FS: ", cust_date)
			if len(cust_date) != 15:
				return
			first = datetime.strptime( cust_date, "%H:%M%d.%m.%Y" )
			
			# trs[-1] last line [2] second element = timestamps [a:b] use second time
			cust_date = trs[-1][COL_TIME] + trs[-1][COL_DATE]
			if len(cust_date) == 11:
				cust_date += trs[-1][-1]
			#splog("FS: ", cust_date)
			if len(cust_date) != 15:
				return
			last = datetime.strptime( cust_date, "%H:%M%d.%m.%Y" )
			
			#first = first - self.td_max_time_drift
			#last = last + self.td_max_time_drift
			
			
			if self.page != 0:
				new_page = (self.first != first or self.last != last)
				splog("FS: getNextPage: first_on_prev_page, first, last_on_prev_page, last, if: ", self.first, first, self.last, last, new_page)
				self.first = first
				self.last = last
			else:
				new_page = True
			
			if new_page:
				test_future_timespan = ( (first-self.td_max_time_drift) <= self.begin and self.begin <= (last+self.td_max_time_drift) )
				test_past_timespan = ( (first+self.td_max_time_drift) >= self.begin and self.begin >= (last-self.td_max_time_drift) )
				
				splog("FS: first_on_page, self.begin, last_on_page, if, if:", first, self.begin, last, test_future_timespan, test_past_timespan )
				if ( test_future_timespan or test_past_timespan ):
					#search in page for matching datetime
					for tds in trs:
						if tds and len(tds) >= 11:
							# Grey's Anathomy
							#OLD [None, u'31.10.2012', u'20:15\u201321:15 Uhr', u'ProSieben', u'8.', u'15', u'Richtungswechsel']
							# 
							# Gute Zeiten 
							#OLD [None, u'20.11.2012', u'06:40\u201307:20 Uhr', u'NDR', None, u'4187', u'Folge 4187']
							#OLD [None, u'\xa0', None, u'5132', u'Folge 5132']
							
							# Wahnfried
							#OLD [u'Sa', u'26.12.1987', u'\u2013', u'So', u'27.12.1987', u'1Plus', None]
							
							# First part: date, times, channel
							xdate = tds[COL_DATE]
							xbegin = tds[COL_TIME]
							#splog( "FS: tds", tds )
							
							#xend = xbegin[6:11]
							#xbegin = xbegin[0:5]
							cust_date = xbegin+xdate
							if len(cust_date) == 11:
								cust_date += tds[-1]
							#splog("FS: ", cust_date)
							if len(cust_date) != 15:
								continue
							xbegin = datetime.strptime( cust_date, "%H:%M%d.%m.%Y" )
							#xend = datetime.strptime( xend+xdate, "%H:%M%d.%m.%Y" )
							#print "xbegin", xbegin
							
							#Py2.6
							delta = abs(self.begin - xbegin)
							delta = delta.seconds + delta.days * 24 * 3600
							#Py2.7 delta = abs(self.begin - xbegin).total_seconds()
							splog("FS: ", self.begin, xbegin, delta, self.max_time_drift)
							
							if delta <= self.max_time_drift:
								
								if self.compareChannels(self.service, tds[COL_CHANNEL]):
									
									if delta < ydelta:
										
										splog( "FS: tds", len(tds), tds )
										if len(tds) >= 10:
											# Second part: s1e1, s1e2,
											xseason = tds[COL_SEASON] or "1"
											xepisode = tds[COL_EPISODE]
											xtitle = tds[COL_TITLE]
										elif len(tds) >= 7:
											#TODO
											# Second part: s1e1, s1e2,
											xseason = tds[4]
											xepisode = tds[5]
											if xseason and xseason.find(".") != -1:
												xseason = xseason[:-1]
												xtitle = tds[6]
											else:
												xseason = "1"
												xtitle = tds[6]
										elif len(tds) == 6:
											xseason = "1"
											xepisode = "1"
											xtitle = tds[5]
										if xseason and xepisode and xtitle and self.series:
										
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
				
				else:
					# TODO calculate next page : use firstrow lastrow datetime
					if not self.future:
						if first > self.begin:
							self.page -= 1
							return
					
					else:
						if self.begin > last:
							self.page += 1
							return
		
		self.page = None
		return
