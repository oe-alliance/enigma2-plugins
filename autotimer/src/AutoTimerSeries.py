# by betonme @2012

import os

# Plugin framework
import imp
#import sys
from operator import isCallable

# Path
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from SeriesServiceBase import SeriesServiceBase

# Constants
PLUGIN_PATH = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/AutoTimer/SeriesServices/" )
MODULE_PREFIX = 'AutoTimerSeriesService'


class AutoTimerSeries():
	def __init__(self):
		self.series_services = {}
		self.loadServices()

	def loadServices(self):
		self.series_services = {}
		
		path = PLUGIN_PATH
		if not os.path.exists(path):
			return
		
		files = [fname[:-3] for fname in os.listdir(path) if fname.endswith(".py")]
		
		for name in files:
			module = None
				
			try:
				fp, pathname, description = imp.find_module(name, [path])
			except Exception, e:
				print "AutoTimerSeries: Find: " + str(e)
				fp = None
			
			if not fp:
				continue
			
			try:
				# Use a prefix to avoid namespace conflicts
				module = imp.load_module(MODULE_PREFIX+name, fp, pathname, description)
			except Exception, e:
				print "AutoTimerSeries: Load: " + str(e)
			finally:
				# Since we may exit via an exception, close fp explicitly.
				if fp:
					fp.close()
			
			if not module:
				print "AutoTimerSeries: Load: no module"
				continue
			
			# Instantiate only if the class is available
			if not hasattr(module, name):
				print "AutoTimerSeries: Error no class definition"
				continue
			
			attrname = getattr(module, name)
			print attrname
			if not attrname:
				print "AutoTimerSeries: Error in getattr"
				continue
			
			# Instantiate only if the class is a subclass of PluginBase
			if not issubclass( attrname, SeriesServiceBase):
				print "AutoTimerSeries: Error no subclass of SeriesServiceBase"
				continue
			
			# Instantiate service
			if not isCallable(attrname):
				print "AutoTimerSeries: Module is not callable"
			
			# Create service instance
			service = attrname()
			
			# Add to service list
			self.series_services[ service.getId() ] = service

	def getServices(self):
		# Return a services list of id, name tuples
		services = [ ("None", "Not used") ]
		services.extend( [ (id, service.getName()) for (id, service) in self.series_services.items() ] )
		return services

	def getSeriesList(self, service, name):
		# Return a series list of id, name tuples
		if service in self.series_services:
			return self.series_services[service].getSeriesList(name)
		return []
		
	def getEpisodeId(self, service, id, begin, end=None, channel=None):
		# Return a season, episode, title tuple
		if service in self.series_services:
			return self.series_services[service].getEpisodeId(id, begin, end, channel)
		return []
