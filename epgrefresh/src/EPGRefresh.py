# -*- coding: UTF-8 -*-
from __future__ import print_function

# To check if in Standby
import Screens.Standby

# eServiceReference
from enigma import eServiceReference, eServiceCenter, getBestPlayableServiceReference

# ...
from ServiceReference import ServiceReference

from Components.ParentalControl import parentalControl

# Timer
from EPGRefreshTimer import epgrefreshtimer, EPGRefreshTimerEntry, checkTimespan

# To calculate next timer execution
from time import time

# Error-print
from traceback import print_exc
from sys import stdout

# Plugin Config
from xml.etree.cElementTree import parse as cet_parse
from Tools.XMLTools import stringToXML
from os import path as path

# We want a list of unique services
from EPGRefreshService import EPGRefreshService

from OrderedSet import OrderedSet

# Configuration
from Components.config import config

# MessageBox
from Screens.MessageBox import MessageBox
from Tools import Notifications
from Tools.BoundFunction import boundFunction

# ... II
from . import _, ENDNOTIFICATIONID, NOTIFICATIONDOMAIN
from MainPictureAdapter import MainPictureAdapter
from PipAdapter import PipAdapter
from RecordAdapter import RecordAdapter

# Path to configuration
CONFIG = "/etc/enigma2/epgrefresh.xml"
XML_VERSION = "1"

class EPGRefresh:
	"""Simple Class to refresh EPGData"""

	def __init__(self):
		# Initialize
		self.services = (OrderedSet(), OrderedSet())
		self.forcedScan = False
		self.isrunning = False
		self.doStopRunningRefresh = False
		self.session = None
		self.beginOfTimespan = 0
		self.refreshAdapter = None
		# to call additional tasks (from other plugins)
		self.finishNotifiers = { }

		# Mtime of configuration files
		self.configMtime = -1
		
		# Todos after finish
		self._initFinishTodos()

		# Read in Configuration
		self.readConfiguration()

	def _initFinishTodos(self):
		self.finishTodos = [self._ToDoCallAutotimer, self._ToDoAutotimerCalled, self._callFinishNotifiers, self.finish]
	
	def addFinishNotifier(self, notifier):
		if not callable(notifier):
			print("[EPGRefresh] notifier" + str(notifier) + " isn't callable")
			return
		self.finishNotifiers[str(notifier)] = notifier

	def removeFinishNotifier(self, notifier):
		notifierKey = str(notifier)
		if self.finishNotifiers.has_key(notifierKey):
			self.finishNotifiers.pop(notifierKey)

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
		configuration = cet_parse(CONFIG).getroot()
		version = configuration.get("version", None)
		if version is None:
			factor = 60
		else: #if version == "1"
			factor = 1

		# Add References
		for service in configuration.findall("service"):
			value = service.text
			if value:
				# strip all after last : (custom name)
				pos = value.rfind(':')
				# don't split alternative service
				if value.find('1:134:1') == -1 and pos != -1:
					value = value[:pos+1]

				duration = service.get('duration', None)
				duration = duration and int(duration)*factor

				self.services[0].add(EPGRefreshService(value, duration))
		for bouquet in configuration.findall("bouquet"):
			value = bouquet.text
			if value:
				duration = bouquet.get('duration', None)
				duration = duration and int(duration)
				self.services[1].add(EPGRefreshService(value, duration))

	def buildConfiguration(self, webif = False):
		list = ['<?xml version="1.0" ?>\n<epgrefresh version="', XML_VERSION, '">\n\n']

		if webif:
			for serviceref in self.services[0].union(self.services[1]):
				ref = ServiceReference(str(serviceref))
				list.extend((
					' <e2service>\n',
					'  <e2servicereference>', str(serviceref), '</e2servicereference>\n',
					'  <e2servicename>', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), '</e2servicename>\n',
					' </e2service>\n',
				))
		else:
			for service in self.services[0]:
				ref = ServiceReference(service.sref)
				list.extend((' <!--', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), '-->\n', ' <service'))
				if service.duration is not None:
					list.extend((' duration="', str(service.duration), '"'))
				list.extend(('>', stringToXML(service.sref), '</service>\n'))
			for bouquet in self.services[1]:
				ref = ServiceReference(bouquet.sref)
				list.extend((' <!--', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), '-->\n', ' <bouquet'))
				if bouquet.duration is not None:
					list.extend((' duration="', str(bouquet.duration), '"'))
				list.extend(('>', stringToXML(bouquet.sref), '</bouquet>\n'))

		list.append('\n</epgrefresh>')

		return list

	def saveConfiguration(self):
		file = open(CONFIG, 'w')
		file.writelines(self.buildConfiguration())

		file.close()

	def maybeStopAdapter(self):
		if self.refreshAdapter:
			self.refreshAdapter.stop()
			self.refreshAdapter = None

	def forceRefresh(self, session = None):
		print("[EPGRefresh] Forcing start of EPGRefresh")
		if self.session is None:
			if session is not None:
				self.session = session
			else:
				return False

		self.forcedScan = True
		self.prepareRefresh()
		return True
	
	def stopRunningRefresh(self, session = None):
		print("[EPGRefresh] Forcing stop of EPGRefresh")
		if self.session is None:
			if session is not None:
				self.session = session
			else:
				return False
		self.doStopRunningRefresh = True

	def start(self, session = None):
		if session is not None:
			self.session = session

		epgrefreshtimer.setRefreshTimer(self.createWaitTimer)

	def stop(self):
		print("[EPGRefresh] Stopping Timer")
		self.maybeStopAdapter()
		epgrefreshtimer.clear()

	def addServices(self, fromList, toList, channelIds):
		for scanservice in fromList:
			service = eServiceReference(scanservice.sref)
			if (service.flags & eServiceReference.isGroup):
				service = getBestPlayableServiceReference(eServiceReference(scanservice.sref), eServiceReference())
			if not service.valid() \
				or (service.flags & (eServiceReference.isMarker|eServiceReference.isDirectory)):

				continue

			channelID = '%08x%04x%04x' % (
				service.getUnsignedData(4), # NAMESPACE
				service.getUnsignedData(2), # TSID
				service.getUnsignedData(3), # ONID
			)

			if channelID not in channelIds:
				toList.append(scanservice)
				channelIds.append(channelID)

	def generateServicelist(self, services, bouquets):
		# This will hold services which are not explicitely in our list
		additionalServices = []
		additionalBouquets = []

		# See if we are supposed to read in autotimer services
		if config.plugins.epgrefresh.inherit_autotimer.value:
			try:
				# Import Instance
				from Plugins.Extensions.AutoTimer.plugin import autotimer

				if autotimer is None:
					# Create an instance
					from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
					autotimer = AutoTimer()

				# Read in configuration
				autotimer.readXml()
			except Exception as e:
				print("[EPGRefresh] Could not inherit AutoTimer Services:", e)
			else:
				# Fetch services
				for timer in autotimer.getEnabledTimerList():
					additionalServices.extend([EPGRefreshService(x, None) for x in timer.services])
					additionalBouquets.extend([EPGRefreshService(x, None) for x in timer.bouquets])

		scanServices = []
		channelIdList = []
		self.addServices(services, scanServices, channelIdList)

		serviceHandler = eServiceCenter.getInstance()
		for bouquet in bouquets.union(additionalBouquets):
			myref = eServiceReference(bouquet.sref)
			list = serviceHandler.list(myref)
			if list is not None:
				while 1:
					s = list.getNext()
					# TODO: I wonder if its sane to assume we get services here (and not just new lists)
					if s.valid():
						additionalServices.append(EPGRefreshService(s.toString(), None))
					else:
						break
		del additionalBouquets[:]

		self.addServices(additionalServices, scanServices, channelIdList)
		del additionalServices[:]

		return scanServices

	def isRunning(self):
		return self.isrunning
	
	def isRefreshAllowed(self):
		if self.isRunning():
			message = _("There is still a refresh running. The Operation isn't allowed at this moment.")
			try:
				if self.session != None:
					self.session.open(MessageBox, message, \
						 MessageBox.TYPE_INFO, timeout=10)
			except:
				print("[EPGRefresh] Error while opening Messagebox!")
				print_exc(file=stdout)
				Notifications.AddPopup(message, MessageBox.TYPE_INFO, 10)
			return False
		return True

	def prepareRefresh(self):
		if not self.isRefreshAllowed():
			return
		self.isrunning = True
		print("[EPGRefresh] About to start refreshing EPG")

		self._initFinishTodos()
		# Maybe read in configuration
		try:
			self.readConfiguration()
		except Exception as e:
			print("[EPGRefresh] Error occured while reading in configuration:", e)

		self.scanServices = self.generateServicelist(self.services[0], self.services[1])

		# Debug
		print("[EPGRefresh] Services we're going to scan:", ', '.join([repr(x) for x in self.scanServices]))

		self.maybeStopAdapter()
		# NOTE: start notification is handled in adapter initializer
		if config.plugins.epgrefresh.adapter.value.startswith("pip"):
			hidden = config.plugins.epgrefresh.adapter.value == "pip_hidden"
			refreshAdapter = PipAdapter(self.session, hide=hidden)
		elif config.plugins.epgrefresh.adapter.value.startswith("record"):
			refreshAdapter = RecordAdapter(self.session)
		else:
			refreshAdapter = MainPictureAdapter(self.session)

		if (not refreshAdapter.backgroundCapable and Screens.Standby.inStandby) or not refreshAdapter.prepare():
			print("[EPGRefresh] Adapter is not able to run in background or not available, falling back to MainPictureAdapter")
			refreshAdapter = MainPictureAdapter(self.session)
			refreshAdapter.prepare()
		self.refreshAdapter = refreshAdapter

		try:
			from plugin import AdjustExtensionsmenu, extStopDescriptor, extPendingServDescriptor, extRunDescriptor
			AdjustExtensionsmenu(True, extPendingServDescriptor)
			AdjustExtensionsmenu(True, extStopDescriptor)
			AdjustExtensionsmenu(False, extRunDescriptor)
		except:
			print("[EPGRefresh] Error while adding 'Stop Running EPG-Refresh' to Extensionmenu")
			print_exc(file=stdout)
			
		self.refresh()

	def cleanUp(self):
		print("[EPGRefresh] Debug: Cleanup")
		config.plugins.epgrefresh.lastscan.value = int(time())
		config.plugins.epgrefresh.lastscan.save()
		self.doStopRunningRefresh = False
		
		try:
			from plugin import AdjustExtensionsmenu, housekeepingExtensionsmenu, extStopDescriptor, extPendingServDescriptor
			AdjustExtensionsmenu(False, extPendingServDescriptor)
			AdjustExtensionsmenu(False, extStopDescriptor)
			housekeepingExtensionsmenu(config.plugins.epgrefresh.show_run_in_extensionsmenu, force=True)
		except:
			print("[EPGRefresh] Error while removing 'Stop Running EPG-Refresh' to Extensionmenu:")
			print_exc(file=stdout)
		
		# Start Todo-Chain
		self._nextTodo()

	def _nextTodo(self, *args, **kwargs):
		print("[EPGRefresh] Debug: Calling nextTodo")
		if len(self.finishTodos) > 0:
			finishTodo = self.finishTodos.pop(0)
			print("[EPGRefresh] Debug: Call " + str(finishTodo))
			finishTodo(*args, **kwargs)
		

	def _ToDoCallAutotimer(self):
		if config.plugins.epgrefresh.parse_autotimer.value != "never":
			if config.plugins.epgrefresh.parse_autotimer.value in ("ask_yes", "ask_no"):
				defaultanswer = True if config.plugins.epgrefresh.parse_autotimer.value == "ask_yes" else False
				if self.forcedScan:
					# only if we are interactive
					Notifications.AddNotificationWithCallback(self._ToDoCallAutotimerCB, MessageBox, \
						text = _("EPG refresh finished.\nShould AutoTimer be search for new matches?"), \
						type = MessageBox.TYPE_YESNO, default = defaultanswer, timeout = 10)
				else:
					self._ToDoCallAutotimerCB(parseAT=defaultanswer)
			else:
				if self.forcedScan\
					and config.plugins.epgrefresh.parse_autotimer.value == "bg_only":
					self._nextTodo()
				else:
					# config.parse_autotimer = always / bg_only
					self._ToDoCallAutotimerCB(parseAT=True)
		else:
			self._nextTodo()

	def _ToDoCallAutotimerCB(self, parseAT):
		print("[EPGRefresh] Debug: Call AutoTimer: " + str(parseAT))
		if parseAT:
			try:
				# Import Instance
				from Plugins.Extensions.AutoTimer.plugin import autotimer
	
				if autotimer is None:
					# Create an instance
					from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
					autotimer = AutoTimer()
	
				# Parse EPG
				deferred = autotimer.parseEPGAsync(simulateOnly=False)
				deferred.addCallback(self._nextTodo)
				deferred.addErrback(self._autotimerErrback)
			#except Exception as e:
			except:
				from traceback import format_exc
				#print("[EPGRefresh] Could not start AutoTimer:", e)
				print("[EPGRefresh] Could not start AutoTimer:" + str(format_exc()))
		else:
			self._nextTodo()
	
	def _autotimerErrback(self, failure):
		print("[EPGRefresh] Debug: AutoTimer failed:" + str(failure))
		if config.plugins.epgrefresh.enablemessage.value:
			Notifications.AddPopup(_("AutoTimer failed with error %s") % (str(failure)), \
				MessageBox.TYPE_ERROR, 100)
		self._nextTodo()

	def _ToDoAutotimerCalled(self, *args, **kwargs):
#		if config.plugins.epgrefresh.enablemessage.value:
#			if len(args):
#				# Autotimer has been started
#				ret=args[0]
#				Notifications.AddPopup(_("Found a total of %d matching Events.\n%d Timer were added and\n%d modified,\n%d conflicts encountered,\n%d similars added.") \
#					% (ret[0], ret[1], ret[2], len(ret[4]), len(ret[5])),
#					MessageBox.TYPE_INFO, 10)
		self._nextTodo()
	
	def _callFinishNotifiers(self, *args, **kwargs):
		for notifier in self.finishNotifiers.keys():
			print("[EPGRefresh] Debug: call " + str(notifier))
			self.finishNotifiers[notifier]()
		self._nextTodo()
	
	def finish(self, *args, **kwargs):
		print("[EPGRefresh] Debug: Refresh finished!")
		if config.plugins.epgrefresh.enablemessage.value:
			Notifications.AddPopup(_("EPG refresh finished."), MessageBox.TYPE_INFO, 4, ENDNOTIFICATIONID)
		epgrefreshtimer.cleanup()
		self.maybeStopAdapter()
		
		# shutdown if we're supposed to go to deepstandby and not recording
		if not self.forcedScan and config.plugins.epgrefresh.afterevent.value \
			and not Screens.Standby.inTryQuitMainloop:
			self.forcedScan = False
		
			if Screens.Standby.inStandby:
				self.session.open(Screens.Standby.TryQuitMainloop, 1)
			else:
				Notifications.AddNotificationWithID("Shutdown", Screens.Standby.TryQuitMainloop, 1)
		self.forcedScan = False
		self.isrunning = False
		self._nextTodo()
		
	def refresh(self):
		if self.doStopRunningRefresh:
			self.cleanUp()
			return
		
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

					print("[EPGRefresh] Gone out of timespan while refreshing, sorry!")
					self.cleanUp()
				else:
					print("[EPGRefresh] Box no longer in Standby or Recording started, rescheduling")

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

	def isServiceProtected(self, service):
		if not config.ParentalControl.servicepinactive.value:
			print("[EPGRefresh] DEBUG: ParentalControl not configured")
			return False
		print("[EPGRefresh] DEBUG: ParentalControl ProtectionLevel:" + str(parentalControl.getProtectionLevel(str(service))))
		return parentalControl.getProtectionLevel(str(service)) != -1

	def nextService(self):
		# Debug
		print("[EPGRefresh] Maybe zap to next service")

		try:
			# Get next reference
			service = self.scanServices.pop(0)
		except IndexError:
			# Debug
			print("[EPGRefresh] Done refreshing EPG")

			# Clean up
			self.cleanUp()
		else:
			if self.isServiceProtected(service):
				if (not self.forcedScan) or config.plugins.epgrefresh.skipProtectedServices.value == "always":
					print("[EPGRefresh] Service is protected, skipping!")
					self.refresh()
					return
			
			# If the current adapter is unable to run in background and we are in fact in background now,
			# fall back to main picture
			if (not self.refreshAdapter.backgroundCapable and Screens.Standby.inStandby):
				print("[EPGRefresh] Adapter is not able to run in background or not available, falling back to MainPictureAdapter")
				self.maybeStopAdapter()
				self.refreshAdapter = MainPictureAdapter(self.session)
				self.refreshAdapter.prepare()

			# Play next service
			# XXX: we might want to check the return value
			self.refreshAdapter.play(eServiceReference(service.sref))

			# Start Timer
			delay = service.duration or config.plugins.epgrefresh.interval_seconds.value
			epgrefreshtimer.add(EPGRefreshTimerEntry(
				time() + delay,
				self.refresh,
				nocheck = True)
			)
	
	def showPendingServices(self, session):
		LISTMAX = 10
		servcounter = 0
		try:
			servtxt = ""
			for service in self.scanServices:
				if self.isServiceProtected(service):
					if not self.forcedScan or config.plugins.epgrefresh.skipProtectedServices.value == "always":
						continue
				if servcounter <= LISTMAX:
					ref = ServiceReference(service.sref)
					txt = ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
					servtxt = servtxt + str(txt) + "\n"
				servcounter = servcounter + 1
			
			if servcounter > LISTMAX:
				servtxt = servtxt + _("%d more services") % (servcounter)
			session.open(MessageBox, _("Following Services have to be scanned:") \
				+ "\n" + servtxt, MessageBox.TYPE_INFO)
		except:
			print("[EPGRefresh] showPendingServices Error!")
			print_exc(file=stdout)

epgrefresh = EPGRefresh()
