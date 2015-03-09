# -*- coding: utf-8 -*-
# by betonme @2012

from collections import defaultdict

from thread import start_new_thread

#TODO Implement Twisted handler
#Twisted 12.x
#from twisted.web.client import getPage as twGetPage
#Twisted 8.x
#from twisted.web.client import _parse, HTTPClientFactory
#from twisted.internet import reactor
#Twisted All
#from twisted.python.failure import Failure

from time import sleep
import socket

from time import time
from datetime import datetime, timedelta

#import urllib2
from urllib import urlencode
from urllib2 import urlopen, URLError, Request, build_opener, HTTPCookieProcessor

from Components.config import config
from Tools.BoundFunction import boundFunction

# Internal
from ModuleBase import ModuleBase
from Cacher import Cacher, INTER_QUERY_TIME
from Channels import ChannelsBase
from Logger import splog
from Analytics import Analytics


class MyException(Exception):
    pass

class IdentifierBase(ModuleBase, Cacher, ChannelsBase, Analytics):
	def __init__(self):
		ModuleBase.__init__(self)
		Cacher.__init__(self)
		ChannelsBase.__init__(self)
		Analytics.__init__(self)
		
		socket.setdefaulttimeout(5)
		
		self.max_time_drift = int(config.plugins.seriesplugin.max_time_drift.value) * 60
		
		self.name = ""
		self.begin = None
		self.end = None
		self.channel = ""
		self.ids = []
		
		self.knownids = []
		
		self.returnvalue = None
		
		self.search_depth = 0;
		
		self.now = time()
		today = datetime.today()
		self.actual_month = today.month
		self.actual_year = today.year

	################################################
	# Helper function
	def getAlternativeSeries(self, name):
		
		self.search_depth += 1
		if( self.search_depth < config.plugins.seriesplugin.search_depths.value ):
			return " ".join(name.split(" ")[:-1])
		else:
			return ""

	def filterKnownIds(self, newids):
		# Filter already checked series
		filteredids = [elem for elem in newids if elem not in self.knownids]
		
		# Add new ids to knownid list
		self.knownids.extend(filteredids)
		
		return filteredids


	################################################
	# URL functions
	def getPage(self, url, headers={}, expires=INTER_QUERY_TIME, counter=0):
		response = None
		
		splog("SSBase getPage", url)
		
		cached = self.getCached(url, expires)
		
		self.sendAnalytics(url, True if cached else False)
		
		if cached:
			splog("SSBase cached")
			response = cached
		
		else:
			splog("SSBase not cached")
			
			try:
				req = Request(url, headers=headers)
				response = urlopen(req, timeout=15).read()
				
				#splog("SSBase response to cache: ", response) 
				if response:
					self.doCachePage(url, response)
			
			except URLError as e:
				 # For Python 2.6
				if counter > 2:
					splog("SSBase URLError counter > 2")
					raise MyException("There was an URLError: %r" % e)
				elif hasattr(e, "code"):
					splog("SSBase URLError code")
					print e.code, e.msg, counter
					sleep(2)
					return self.getPage(url, headers, expires, counter+1)
				else:
					splog("SSBase URLError else")
					raise MyException("There was an URLError: %r" % e)
			
			except socket.timeout as e:
				 # For Python 2.7
				if counter > 2:
					splog("SSBase URLError counter > 2")
					raise MyException("There was an SocketTimeout: %r" % e)
				elif hasattr(e, "code"):
					splog("SSBase URLError code")
					print e.code, e.msg, counter
					sleep(2)
					return self.getPage(url, headers, expires, counter+1)
				else:
					splog("SSBase URLError else")
					raise MyException("There was an SocketTimeout: %r" % e)
			
		splog("SSBase success")
		return response
	
	################################################
	# Service prototypes
	@classmethod
	def knowsElapsed(cls):
		# True: Service knows elapsed air dates
		# False: Service doesn't know elapsed air dates
		return False

	@classmethod
	def knowsToday(cls):
		# True: Service knows today air dates
		# False: Service doesn't know today air dates
		return False

	@classmethod
	def knowsFuture(cls):
		# True: Service knows future air dates
		# False: Service doesn't know future air dates
		return False

	################################################
	# To be implemented by subclass
	def getEpisode(self, name, begin, end, service):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or String or None
		return None
