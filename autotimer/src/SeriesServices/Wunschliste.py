# by betonme @2012

# Imports
from urllib import urlencode
from urllib2 import Request, urlopen, URLError

from xml.etree.cElementTree import XML
from Plugins.Extensions.AutoTimer.iso8601 import parse_date
from datetime import datetime
from time import mktime
import re

from Plugins.Extensions.AutoTimer.SeriesServiceBase import SeriesServiceBase

# Constants
SERIESLISTURL = "http://www.wunschliste.de/ajax/search_dropdown.pl"
EPISODEIDURL = "http://www.wunschliste.de/xml/atom.pl"
#EPISODEIDURL = "http://www.wunschliste.de/xml/rss.pl"


class Wunschliste(SeriesServiceBase):
	def __init__(self):
		SeriesServiceBase.__init__(self)

		# Series: EpisodeTitle (Season/Episode) - Weekday Date, Time / Channel (Country)
		# .*:.*\(.*\..*\).*/.*\(.*\..*\)
		self.regexp = re.compile('(.+):(.*)\((\d+)\.(\d+)\)')
		
		# Used for a simple page caching
		self.cacheid = None
		self.cacheroot = None

	def getName(self):
		return "Wunschliste.de"

	def getId(self):
		return "Wlde"

	def getSeriesList(self, name):
		# On Success: Return a series list of id, name tuples
		# On Failure: Return a empty list or None
		values = { 'q' : name }
		data = urlencode(values)
		req = Request(SERIESLISTURL, data)

		try:
			response = urlopen(req)
			data = response.read()
		except URLError as e:
			data = ""
			print "AutoTimer: Wunschliste URLError"

		serieslist = []
		for line in data.splitlines():
			values =  line.split("|")
			if len(values) == 3:
				name, countryyear, id = values
				#country, year = countryyear.split(",")
				serieslist.append( (id, name + " (" + countryyear + ")" ) )
			else:
				print "AutoTimer: Wunschliste: ParseError: " + str(line)
		return serieslist

	def getEpisodeId(self, id, begin, end=None, channel=None):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or None
		begin = begin and datetime.fromtimestamp(begin)
		end = end and datetime.fromtimestamp(end)

		if self.cacheid != id:
			self.cacheid = id
			values = { 's' : id }
			data = urlencode(values)
			req = Request(EPISODEIDURL, data)

			try:
				response = urlopen(req)
				print "URLOPEN"
				feed = response.read()
			except URLError as e:
				feed = ""
				print "AutoTimer: Wunschliste URLError"

			#Won't work why - getroot is the problem
			#feed = urlopen(req)
			#tree = feed and parse(feed)
			#for entry in tree.findall('{http://www.w3.org/2005/Atom}entry'):
	
			root = feed and XML(feed)
			self.cacheroot = root

		else:
			root = self.cacheroot

		if root is not None:
			for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
				title = entry.find('{http://www.w3.org/2005/Atom}title')
				updated = entry.find('{http://www.w3.org/2005/Atom}updated')
				if title is not None and updated is not None:
					#import iso8601
					#http://code.google.com/p/pyiso8601/
					xbegin = parse_date(updated.text)

					#import pytz
					#xbegin = pytz.UTC.localize(xbegin)
					#xbegin = mktime(xbegin.timetuple())

					# Alternative
					#from dateutil import parser
					#http://labix.org/python-dateutil
					#xbegin = parser.parse(updated.text)

					if begin.date() == xbegin.date():
						# Same day
						if abs(mktime(begin.timetuple()) - mktime(xbegin.timetuple())) < 600:
							# Time difference is below 5 minutes
							# We actually don't check the channel - Any ideas?
							result = self.regexp.match(title.text)
							if result and len(result.groups())>=4:
								
								title = result.group(2)
								season = result.group(3)
								episode = result.group(4)
								return int(season), int(episode), title

		return None




#Maybe later we want to use Twisted, because it is non blocking
#To be tested

	def lookupIdForEpisodeNamingTwisted(self, name):
		from twisted.web.client import getPage
		headers={'Content-Type':'text/xml'}
		values = { 'q' : name }
		headers.update( values )
		getPage(SERIESLISTURL, timeout = 10).addCallback(self.lookupIdForEpisodeNamingCallback).addErrback(self.lookupIdForEpisodeNamingError)

	def lookupIdForEpisodeNamingCallback(self, data):
		serieslist = []
		for line in data.splitlines():
			name, countryyear, id=  line.split("|")
			#country, year = countryyear.split(",")
			serieslist.append( (name + " (" + countryyear + ")", id ) )
		return serieslist

	def lookupIdForEpisodeNamingError(self, error):
		self.session.open(
			MessageBox,
			text = _('No matching series found'),
			type = MessageBox.TYPE_INFO
		)
		return None

