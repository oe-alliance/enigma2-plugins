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
from Cacher import Cacher
from Channels import ChannelsBase
from Logger import logDebug, logInfo


class MyException(Exception):
    pass

class IdentifierBase(ModuleBase, Cacher, ChannelsBase):
	def __init__(self):
		ModuleBase.__init__(self)
		Cacher.__init__(self)
		ChannelsBase.__init__(self)
		
		socket.setdefaulttimeout( float(config.plugins.seriesplugin.socket_timeout.value) )
		
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
			
			if self.search_depth == 1:
				if name.find("-") != -1:
					alt = " ".join(name.split("-")[:-1]).strip()
				else:
					alt = " ".join(name.split(" ")[:-1])
			else:
				alt = " ".join(name.split(" ")[:-1])
			
			# Avoid searchs with: The, Der, Die, Das...
			if len(alt) > 3:
				return alt
			else:
				return ""
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
	def getPage(self, url, use_proxy=True, counter=0):
		response = None
		
		logDebug("IB: getPage", url)
		
		cached = self.getCached(url)
		
		if cached:
			logDebug("IB: cached")
			response = cached
		
		else:
			logDebug("IB: not cached")
			
			try:
				from plugin import buildURL, USER_AGENT
				
				if use_proxy:
					temp_url = buildURL(url)
				else:
					temp_url = url
				
				req = Request( temp_url, headers={'User-Agent':USER_AGENT})
				response = urlopen(req, timeout=float(config.plugins.seriesplugin.socket_timeout.value)).read()
				
				if not response:
					logDebug("IB: No data returned")
				
				#logDebug("IB: response to cache: ", response) 
				#if response:
				#	self.doCachePage(url, response)
			
			except URLError as e:
				 # For Python 2.6
				if counter > 2:
					logDebug("IB: URLError counter > 2")
					raise MyException("There was an URLError: %r" % e)
				elif hasattr(e, "code"):
					logDebug("IB: URLError code")
					print e.code, e.msg, counter
					sleep(2)
					return self.getPage(url, use_proxy, counter+1)
				else:
					logDebug("IB: URLError else")
					raise MyException("There was an URLError: %r" % e)
			
			except socket.timeout as e:
				 # For Python 2.7
				if counter > 2:
					logDebug("IB: URLError counter > 2")
					raise MyException("There was an SocketTimeout: %r" % e)
				elif hasattr(e, "code"):
					logDebug("IB: URLError code")
					print e.code, e.msg, counter
					sleep(2)
					return self.getPage(url, use_proxy, counter+1)
				else:
					logDebug("IB: URLError else")
					raise MyException("There was an SocketTimeout: %r" % e)
			
		logDebug("IB: success")
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
