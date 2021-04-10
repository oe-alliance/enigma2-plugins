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

from time import time
from datetime import datetime, timedelta

from Components.config import config
from Tools.BoundFunction import boundFunction

# Internal
from ModuleBase import ModuleBase
from Cacher import Cacher
from Logger import log


class MyException(Exception):
    pass


class IdentifierBase2(ModuleBase, Cacher):
	def __init__(self):
		ModuleBase.__init__(self)
		Cacher.__init__(self)
		
		self.max_time_drift = int(config.plugins.seriesplugin.max_time_drift.value) * 60
		
		self.name = ""
		self.begin = None
		self.end = None
		self.channel = ""
		self.ids = []
		
		self.knownids = []
		
		self.returnvalue = None
		
		self.search_depth = 0
		
		self.now = time()
		today = datetime.today()
		self.actual_month = today.month
		self.actual_year = today.year

	################################################
	# Helper function
	def getAlternativeSeries(self, name):
		
		self.search_depth += 1
		if(self.search_depth < config.plugins.seriesplugin.search_depths.value):
			
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
	def getLogo(self, future=True, today=False, elapsed=False):
		# Return the name of the logo without extension .png
		pass

	def getEpisode(self, name, begin, end, service):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or String or None
		return None
