# To check if in Standby
import Screens.Standby

# eServiceReference
from enigma import eServiceReference, eServiceCenter

# ...
from ServiceReference import ServiceReference

# Timer
from EPGRefreshTimer import epgrefreshtimer, EPGRefreshTimerEntry, checkTimespan

# To calculate next timer execution
from time import time

# Plugin Config
from xml.etree.cElementTree import parse as cet_parse
from os import path as path

# We want a list of unique services
from sets import Set

# Configuration
from Components.config import config

# Path to configuration
CONFIG = "/etc/enigma2/epgrefresh.xml"

class EPGRefresh:
	"""Simple Class to refresh EPGData"""

	def __init__(self):
		# Initialize 
		self.services = (Set(), Set())
		self.previousService = None
		self.forcedScan = False
		self.session = None
		self.beginOfTimespan = 0

		# Mtime of configuration files
		self.configMtime = -1

		# Read in Configuration
		self.readConfiguration()

	def readConfiguration(self):
		# Check if file exists
		if not path.exists(CONFIG):
			return

		# Check if file did not change
		mtime = path.getmtime(CONFIG)
		if mtime == self.configMtime:
			return

		# Keep mtime
		self.configMtime = mtime

		# Empty out list
		self.services[0].clear()
		self.services[1].clear()

		# Open file
		configuration= cet_parse(CONFIG).getroot()

		# Add References
		for service in configuration.findall("service"):
			value = service.text
			if value:
				# strip all after last : (custom name)
				pos = value.rfind(':')
				if pos != -1:
					value = value[:pos+1]

				self.services[0].add(value)
		for bouquet in configuration.findall("bouquet"):
			value = bouquet.text
			if value:
				self.services[1].add(value)

	def saveConfiguration(self):
		# Generate List in RAM
		list = ['<?xml version="1.0" ?>\n<epgrefresh>\n\n']

		for service in self.services[0]:
			ref = ServiceReference(str(service))
			list.extend([' <!-- ', ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''), ' -->\n'])
			list.extend([' <service>', service, '</service>\n'])
		for bouquet in self.services[1]:
			ref = ServiceReference(str(bouquet))
			list.extend([' <!-- ', ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''), ' -->\n'])
			list.extend([' <bouquet>', bouquet, '</bouquet>\n'])

		list.append('\n</epgrefresh>')

		# Save to Flash
		file = open(CONFIG, 'w')
		file.writelines(list)

		file.close()

	def forceRefresh(self, session = None):
		print "[EPGRefresh] Forcing start of EPGRefresh"
		if session is not None:
			self.session = session

		self.forcedScan = True
		self.prepareRefresh()

	def start(self, session = None):
		if session is not None:
			self.session = session

		epgrefreshtimer.setRefreshTimer(self.createWaitTimer)

	def stop(self):
		print "[EPGRefresh] Stopping Timer"
		epgrefreshtimer.clear()

	def prepareRefresh(self):
		print "[EPGRefresh] About to start refreshing EPG"

		# Keep service
		self.previousService =  self.session.nav.getCurrentlyPlayingServiceReference()

		# Maybe read in configuration
		try:
			self.readConfiguration()
		except Exception, e:
			print "[EPGRefresh] Error occured while reading in configuration:", e

		# Save Services in a dict <transponder data> => serviceref
		self.scanServices = []
		channelIdList = []

		# This will hold services which are not explicitely in our list
		additionalServices = []
		additionalBouquets = []

		# See if we are supposed to read in autotimer services
		if config.plugins.epgrefresh.inherit_autotimer.value:
			try:
				# Import Instance
				from Plugins.Extensions.AutoTimer.plugin import autotimer

				# See if instance is empty
				removeInstance = False
				if autotimer is None:
					removeInstance = True
					# Create an instance
					from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
					autotimer = AutoTimer()

				# Read in configuration
				autotimer.readXml()

				# Fetch services
				for timer in autotimer.getEnabledTimerList():
					additionalServices.extend(timer.getServices())
					additionalBouquets.extend(timer.getBouquets())

				# Remove instance if there wasn't one before
				# we might go into the exception before we reach this line, but we don't care then...
				if removeInstance:
					autotimer = None

			except Exception, e:
				print "[EPGRefresh] Could not inherit AutoTimer Services:", e

		serviceHandler = eServiceCenter.getInstance()
		for bouquet in self.services[1].union(additionalBouquets):
			myref = eServiceReference(str(bouquet))
			list = serviceHandler.list(myref)
			if list is not None:
				while 1:
					s = list.getNext()
					# TODO: I wonder if its sane to assume we get services here (and not just new lists)
					if s.valid():
						additionalServices.append(s.toString())
					else:
						break

		for serviceref in self.services[0].union(additionalServices):
			service = eServiceReference(str(serviceref))
			if not service.valid() \
				or (service.flags & (eServiceReference.isMarker|eServiceReference.isDirectory)):
				
				continue

			channelID = '%08x%04x%04x' % (
				service.getUnsignedData(4), # NAMESPACE
				service.getUnsignedData(2), # TSID
				service.getUnsignedData(3), # ONID
			)

			if channelID not in channelIdList:
				self.scanServices.append(service)
				channelIdList.append(channelID)

		# Debug
		print "[EPGRefresh] Services we're going to scan:", ', '.join([ServiceReference(x).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '') for x in self.scanServices])

		self.refresh()

	def cleanUp(self):
		config.plugins.epgrefresh.lastscan.value = int(time())
		config.plugins.epgrefresh.lastscan.save()

		# shutdown if we're supposed to go to deepstandby and not recording
		if not self.forcedScan and config.plugins.epgrefresh.afterevent.value \
			and not Screens.Standby.inTryQuitMainloop:

			self.session.open(
				Screens.Standby.TryQuitMainloop,
				1
			)

		self.forcedScan = False
		epgrefreshtimer.cleanup()

		# Zap back
		if self.previousService is not None or Screens.Standby.inStandby:
			self.session.nav.playService(self.previousService)

	def refresh(self):
		if self.forcedScan:
			self.nextService()
		else:
			# Abort if a scan finished later than our begin of timespan
			if self.beginOfTimespan < config.plugins.epgrefresh.lastscan.value:
				return
			if config.plugins.epgrefresh.force.value \
				or (Screens.Standby.inStandby and \
					not self.session.nav.RecordTimer.isRecording()):

				self.nextService()
			# We don't follow our rules here - If the Box is still in Standby and not recording we won't reach this line 
			else:
				if not checkTimespan(
					config.plugins.epgrefresh.begin.value,
					config.plugins.epgrefresh.end.value):

					print "[EPGRefresh] Gone out of timespan while refreshing, sorry!"
					self.cleanUp()
				else:
					print "[EPGRefresh] Box no longer in Standby or Recording started, rescheduling"

					# Recheck later
					epgrefreshtimer.add(EPGRefreshTimerEntry(
							time() + config.plugins.epgrefresh.delay_standby.value*60,
							self.refresh,
							nocheck = True)
					)

	def createWaitTimer(self):
		self.beginOfTimespan = time()

		# Add wait timer to epgrefreshtimer
		epgrefreshtimer.add(EPGRefreshTimerEntry(time() + 30, self.prepareRefresh))

	def nextService(self):
		# DEBUG
		print "[EPGRefresh] Maybe zap to next service"

		try:
			# Get next reference
			service = self.scanServices.pop(0)

			# Play next service
			self.session.nav.playService(service)

			# Start Timer
			epgrefreshtimer.add(EPGRefreshTimerEntry(
				time() + config.plugins.epgrefresh.interval.value*60,
				self.refresh,
				nocheck = True)
			)
		except IndexError:
			# Debug
			print "[EPGRefresh] Done refreshing EPG"

			# Clean up
			self.cleanUp()

epgrefresh = EPGRefresh()
