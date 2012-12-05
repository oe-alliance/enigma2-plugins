from __future__ import print_function

# Plugins Config
from xml.etree.cElementTree import parse as cet_parse
from os import path as os_path
from AutoTimerConfiguration import parseConfig, buildConfig

# Navigation (RecordTimer)
import NavigationInstance

# Timer
from ServiceReference import ServiceReference
from RecordTimer import RecordTimerEntry
from Components.TimerSanityCheck import TimerSanityCheck

# Timespan
from time import localtime, strftime, time, mktime
from datetime import timedelta, date

# EPGCache & Event
from enigma import eEPGCache, eServiceReference, eServiceCenter, iServiceInformation

from twisted.internet import reactor, defer
from twisted.python import failure
from threading import currentThread
import Queue

# AutoTimer Component
from AutoTimerComponent import preferredAutoTimerComponent

from itertools import chain
from collections import defaultdict
from difflib import SequenceMatcher
from operator import itemgetter

from Plugins.SystemPlugins.Toolkit.SimpleThread import SimpleThread

try:
	from Plugins.Extensions.SeriesPlugin.plugin import renameTimer
except ImportError as ie:
	renameTimer = None

from . import config, xrange, itervalues

XML_CONFIG = "/etc/enigma2/autotimer.xml"

def getTimeDiff(timer, begin, end):
	if begin <= timer.begin <= end:
		return end - timer.begin
	elif timer.begin <= begin <= timer.end:
		return timer.end - begin
	return 0

def blockingCallFromMainThread(f, *a, **kw):
	"""
	  Modified version of twisted.internet.threads.blockingCallFromThread
	  which waits 30s for results and otherwise assumes the system to be shut down.
	  This is an ugly workaround for a twisted-internal deadlock.
	  Please keep the look intact in case someone comes up with a way
	  to reliably detect from the outside if twisted is currently shutting
	  down.
	"""
	queue = Queue.Queue()
	def _callFromThread():
		result = defer.maybeDeferred(f, *a, **kw)
		result.addBoth(queue.put)
	reactor.callFromThread(_callFromThread)

	result = None
	while True:
		try:
			result = queue.get(True, 30)
		except Queue.Empty as qe:
			if True: #not reactor.running: # reactor.running is only False AFTER shutdown, we are during.
				raise ValueError("Reactor no longer active, aborting.")
		else:
			break

	if isinstance(result, failure.Failure):
		result.raiseException()
	return result

typeMap = {
	"exact": eEPGCache.EXAKT_TITLE_SEARCH,
	"partial": eEPGCache.PARTIAL_TITLE_SEARCH,
	"description": -99
}

caseMap = {
	"sensitive": eEPGCache.CASE_CHECK,
	"insensitive": eEPGCache.NO_CASE_CHECK
}

class AutoTimer:
	"""Read and save xml configuration, query EPGCache"""

	def __init__(self):
		# Initialize
		self.timers = []
		self.configMtime = -1
		self.uniqueTimerId = 0
		self.defaultTimer = preferredAutoTimerComponent(
			0,		# Id
			"",		# Name
			"",		# Match
			True 	# Enabled
		)

# Configuration

	def readXml(self):
		# Abort if no config found
		if not os_path.exists(XML_CONFIG):
			print("[AutoTimer] No configuration file present")
			return

		# Parse if mtime differs from whats saved
		mtime = os_path.getmtime(XML_CONFIG)
		if mtime == self.configMtime:
			print("[AutoTimer] No changes in configuration, won't parse")
			return

		# Save current mtime
		self.configMtime = mtime

		# Parse Config
		configuration = cet_parse(XML_CONFIG).getroot()

		# Empty out timers and reset Ids
		del self.timers[:]
		self.defaultTimer.clear(-1, True)

		parseConfig(
			configuration,
			self.timers,
			configuration.get("version"),
			0,
			self.defaultTimer
		)
		self.uniqueTimerId = len(self.timers)

	def getXml(self):
		return buildConfig(self.defaultTimer, self.timers, webif = True)

	def writeXml(self):
		file = open(XML_CONFIG, 'w')
		file.writelines(buildConfig(self.defaultTimer, self.timers))
		file.close()

# Manage List

	def add(self, timer):
		self.timers.append(timer)

	def getEnabledTimerList(self):
		return (x for x in self.timers if x.enabled)

	def getTimerList(self):
		return self.timers

	def getTupleTimerList(self):
		lst = self.timers
		return [(x,) for x in lst]

	def getSortedTupleTimerList(self):
		lst = self.timers[:]
		lst.sort()
		return [(x,) for x in lst]

	def getUniqueId(self):
		self.uniqueTimerId += 1
		return self.uniqueTimerId

	def remove(self, uniqueId):
		idx = 0
		for timer in self.timers:
			if timer.id == uniqueId:
				self.timers.pop(idx)
				return
			idx += 1

	def set(self, timer):
		idx = 0
		for stimer in self.timers:
			if stimer == timer:
				self.timers[idx] = timer
				return
			idx += 1
		self.timers.append(timer)

	def parseEPGAsync(self, simulateOnly = False):
		t = SimpleThread(lambda: self.parseEPG(simulateOnly=simulateOnly))
		t.start()
		return t.deferred

# Main function

	def parseTimer(self, timer, epgcache, serviceHandler, recordHandler, checkEvtLimit, evtLimit, timers, conflicting, similars, timerdict, moviedict, simulateOnly=False):
		new = 0
		modified = 0

		# Precompute timer destination dir
		dest = timer.destination or config.usage.default_path.value

		# Workaround to allow search for umlauts if we know the encoding
		match = timer.match
		if timer.encoding != 'UTF-8':
			try:
				match = match.decode('UTF-8').encode(timer.encoding)
			except UnicodeDecodeError:
				pass

		if timer.searchType == "description":
			epgmatches = []
			mask = (eServiceReference.isMarker | eServiceReference.isDirectory)

			casesensitive = timer.searchCase == "sensitive"
			if not casesensitive:
				match = match.lower()

			# Service filter defined
			# Search only using the specified services
			test = [(service, 0, -1, -1) for service in timer.services]

			for bouquet in timer.bouquets:
				services = serviceHandler.list(eServiceReference(bouquet))
				if not services is None:
					while True:
						service = services.getNext()
						if not service.valid(): #check end of list
							break
						if not (service.flags & mask):
							test.append( (service.toString(), 0, -1, -1 ) )

			if not test:
				# No service filter defined
				# Search within all services - could be very slow

				# Get all bouquets
				bouquetlist = []
				refstr = '1:134:1:0:0:0:0:0:0:0:FROM BOUQUET \"bouquets.tv\" ORDER BY bouquet'
				bouquetroot = eServiceReference(refstr)
				mask = eServiceReference.isDirectory
				if config.usage.multibouquet.value:
					bouquets = serviceHandler.list(bouquetroot)
					if bouquets:
						while True:
							s = bouquets.getNext()
							if not s.valid():
								break
							if s.flags & mask:
								info = serviceHandler.info(s)
								if info:
									bouquetlist.append((info.getName(s), s))
				else:
					info = serviceHandler.info(bouquetroot)
					if info:
						bouquetlist.append((info.getName(bouquetroot), bouquetroot))

				# Get all services
				mask = (eServiceReference.isMarker | eServiceReference.isDirectory)
				for name, bouquet in bouquetlist:
					if not bouquet.valid(): #check end of list
						break
					if bouquet.flags & eServiceReference.isDirectory:
						services = serviceHandler.list(bouquet)
						if not services is None:
							while True:
								service = services.getNext()
								if not service.valid(): #check end of list
									break
								if not (service.flags & mask):
									test.append( (service.toString(), 0, -1, -1 ) )

			if test:
				# Get all events
				#  eEPGCache.lookupEvent( [ format of the returned tuples, ( service, 0 = event intersects given start_time, start_time -1 for now_time), ] )
				test.insert(0, 'RITBDSE')
				allevents = epgcache.lookupEvent(test) or []

				# Filter events
				for serviceref, eit, name, begin, duration, shortdesc, extdesc in allevents:
					if match in (shortdesc if casesensitive else shortdesc.lower()) \
						or match in (extdesc if casesensitive else extdesc.lower()):
						epgmatches.append( (serviceref, eit, name, begin, duration, shortdesc, extdesc) )

		else:
			# Search EPG, default to empty list
			epgmatches = epgcache.search( ('RITBDSE', 1000, typeMap[timer.searchType], match, caseMap[timer.searchCase]) ) or []

		# Sort list of tuples by begin time 'B'
		epgmatches.sort(key=itemgetter(3))

		# Contains the the marked similar eits and the conflicting strings
		similardict = defaultdict(list)		

		# Loop over all EPG matches
		for idx, ( serviceref, eit, name, begin, duration, shortdesc, extdesc ) in enumerate( epgmatches ):

			eserviceref = eServiceReference(serviceref)
			evt = epgcache.lookupEventId(eserviceref, eit)
			if not evt:
				print("[AutoTimer] Could not create Event!")
				continue
			# Try to determine real service (we always choose the last one)
			n = evt.getNumOfLinkageServices()
			if n > 0:
				i = evt.getLinkageService(eserviceref, n-1)
				serviceref = i.toString()

			evtBegin = begin
			evtEnd = end = begin + duration

			# If event starts in less than 60 seconds skip it
			if begin < time() + 60:
				print("[AutoTimer] Skipping an event because it starts in less than 60 seconds")
				continue

			# Convert begin time
			timestamp = localtime(begin)
			# Update timer
			timer.update(begin, timestamp)

			# Check if eit is in similar matches list
			# NOTE: ignore evtLimit for similar timers as I feel this makes the feature unintuitive
			similarTimer = False
			if eit in similardict:
				similarTimer = True
				dayofweek = None # NOTE: ignore day on similar timer
			else:
				# If maximum days in future is set then check time
				if checkEvtLimit:
					if begin > evtLimit:
						continue

				dayofweek = str(timestamp.tm_wday)

			# Check timer conditions
			# NOTE: similar matches do not care about the day/time they are on, so ignore them
			if timer.checkServices(serviceref) \
				or timer.checkDuration(duration) \
				or (not similarTimer and (\
					timer.checkTimespan(timestamp) \
					or timer.checkTimeframe(begin) \
				)) or timer.checkFilter(name, shortdesc, extdesc, dayofweek):
				continue

			if timer.hasOffset():
				# Apply custom Offset
				begin, end = timer.applyOffset(begin, end)
			else:
				# Apply E2 Offset
				begin -= config.recording.margin_before.value * 60
				end += config.recording.margin_after.value * 60

			# Overwrite endtime if requested
			if timer.justplay and not timer.setEndtime:
				end = begin

			# Eventually change service to alternative
			if timer.overrideAlternatives:
				serviceref = timer.getAlternative(serviceref)

			# Append to timerlist and abort if simulating
			timers.append((name, begin, end, serviceref, timer.name))
			if simulateOnly:
				continue

			# Check for existing recordings in directory
			if timer.avoidDuplicateDescription == 3:
				# Reset movie Exists
				movieExists = False

				if dest and dest not in moviedict:
					self.addDirectoryToMovieDict(moviedict, dest, serviceHandler)
				for movieinfo in moviedict.get(dest, ()):
					if self.checkSimilarity(timer, name, movieinfo.get("name"), shortdesc, movieinfo.get("shortdesc"), extdesc, movieinfo.get("extdesc") ):
						print("[AutoTimer] We found a matching recorded movie, skipping event:", name)
						movieExists = True
						break
				if movieExists:
					continue

			# Initialize
			newEntry = None
			oldExists = False

			# Check for double Timers
			# We first check eit and if user wants us to guess event based on time
			# we try this as backup. The allowed diff should be configurable though.
			for rtimer in timerdict.get(serviceref, ()):
				if rtimer.eit == eit or config.plugins.autotimer.try_guessing.value and getTimeDiff(rtimer, evtBegin, evtEnd) > ((duration/10)*8):
					oldExists = True

					# Abort if we don't want to modify timers or timer is repeated
					if config.plugins.autotimer.refresh.value == "none" or rtimer.repeated:
						print("[AutoTimer] Won't modify existing timer because either no modification allowed or repeated timer")
						break

					if hasattr(rtimer, "isAutoTimer"):
						rtimer.log(501, "[AutoTimer] AutoTimer %s modified this automatically generated timer." % (timer.name))
					else:
						if config.plugins.autotimer.refresh.value != "all":
							print("[AutoTimer] Won't modify existing timer because it's no timer set by us")
							break

						rtimer.log(501, "[AutoTimer] Warning, AutoTimer %s messed with a timer which might not belong to it." % (timer.name))

					newEntry = rtimer
					modified += 1

					self.modifyTimer(rtimer, name, shortdesc, begin, end, serviceref)
					break
				elif timer.avoidDuplicateDescription >= 1 \
					and not rtimer.disabled:
						if self.checkSimilarity(timer, name, rtimer.name, shortdesc, rtimer.description, extdesc, rtimer.extdesc ):
						# if searchForDuplicateDescription > 1 then check short description
							oldExists = True
							print("[AutoTimer] We found a timer (similar service) with same description, skipping event")
							break

			# We found no timer we want to edit
			if newEntry is None:
				# But there is a match
				if oldExists:
					continue

				# We want to search for possible doubles
				if timer.avoidDuplicateDescription >= 2:
					for rtimer in chain.from_iterable( itervalues(timerdict) ):
						if not rtimer.disabled:
							if self.checkSimilarity(timer, name, rtimer.name, shortdesc, rtimer.description, extdesc, rtimer.extdesc ):
								oldExists = True
								print("[AutoTimer] We found a timer (any service) with same description, skipping event")
								break
					if oldExists:
						continue

				if timer.checkCounter(timestamp):
					print("[AutoTimer] Not adding new timer because counter is depleted.")
					continue

				newEntry = RecordTimerEntry(ServiceReference(serviceref), begin, end, name, shortdesc, eit)
				newEntry.log(500, "[AutoTimer] Try to add new timer based on AutoTimer %s." % (timer.name))

				# Mark this entry as AutoTimer (only AutoTimers will have this Attribute set)
				# It is only temporarily, after a restart it will be lost,
				# because it won't be stored in the timer xml file
				newEntry.isAutoTimer = True

			# Apply afterEvent
			if timer.hasAfterEvent():
				afterEvent = timer.getAfterEventTimespan(localtime(end))
				if afterEvent is None:
					afterEvent = timer.getAfterEvent()
				if afterEvent is not None:
					newEntry.afterEvent = afterEvent

			newEntry.dirname = timer.destination
			newEntry.justplay = timer.justplay
			newEntry.vpsplugin_enabled = timer.vps_enabled
			newEntry.vpsplugin_overwrite = timer.vps_overwrite
			tags = timer.tags[:]
			if config.plugins.autotimer.add_autotimer_to_tags.value:
				tags.append('AutoTimer')
			if config.plugins.autotimer.add_name_to_tags.value:
				name = timer.name.strip()
				if name:
					name = name[0].upper() + name[1:].replace(" ", "_")
					tags.append(name)
			newEntry.tags = tags

			if oldExists:
				# XXX: this won't perform a sanity check, but do we actually want to do so?
				recordHandler.timeChanged(newEntry)

				if renameTimer is not None and timer.series_labeling:
					renameTimer(newEntry, name, evtBegin, evtEnd)

			else:
				conflictString = ""
				if similarTimer:
					conflictString = similardict[eit].conflictString
					newEntry.log(504, "[AutoTimer] Try to add similar Timer because of conflicts with %s." % (conflictString))

				# Try to add timer
				conflicts = recordHandler.record(newEntry)

				if conflicts:
					# Maybe use newEntry.log
					conflictString += ' / '.join(["%s (%s)" % (x.name, strftime("%Y%m%d %H%M", localtime(x.begin))) for x in conflicts])
					print("[AutoTimer] conflict with %s detected" % (conflictString))

					if config.plugins.autotimer.addsimilar_on_conflict.value:
						# We start our search right after our actual index
						# Attention we have to use a copy of the list, because we have to append the previous older matches
						lepgm = len(epgmatches)
						for i in xrange(lepgm):
							servicerefS, eitS, nameS, beginS, durationS, shortdescS, extdescS = epgmatches[ (i+idx+1)%lepgm ]
							if self.checkSimilarity(timer, name, nameS, shortdesc, shortdescS, extdesc, extdescS, force=True ):
								# Check if the similar is already known
								if eitS not in similardict:
									print("[AutoTimer] Found similar Timer: " + name)

									# Store the actual and similar eit and conflictString, so it can be handled later
									newEntry.conflictString = conflictString
									similardict[eit] = newEntry
									similardict[eitS] = newEntry
									similarTimer = True
									if beginS <= evtBegin:
										# Event is before our actual epgmatch so we have to append it to the epgmatches list
										epgmatches.append((servicerefS, eitS, nameS, beginS, durationS, shortdescS, extdescS))
									# If we need a second similar it will be found the next time
								else:
									similarTimer = False
									newEntry = similardict[eitS]
								break

				if conflicts is None:
					timer.decrementCounter()
					new += 1
					newEntry.extdesc = extdesc
					timerdict[serviceref].append(newEntry)

					if renameTimer is not None and timer.series_labeling:
						renameTimer(newEntry, name, evtBegin, evtEnd)

					# Similar timers are in new timers list and additionally in similar timers list
					if similarTimer:
						similars.append((name, begin, end, serviceref, timer.name))
						similardict.clear()

				# Don't care about similar timers
				elif not similarTimer:
					conflicting.append((name, begin, end, serviceref, timer.name))

					if config.plugins.autotimer.disabled_on_conflict.value:
						newEntry.log(503, "[AutoTimer] Timer disabled because of conflicts with %s." % (conflictString))
						newEntry.disabled = True
						# We might want to do the sanity check locally so we don't run it twice - but I consider this workaround a hack anyway
						conflicts = recordHandler.record(newEntry)
		return (new, modified)

	def parseEPG(self, simulateOnly = False):
		if NavigationInstance.instance is None:
			print("[AutoTimer] Navigation is not available, can't parse EPG")
			return (0, 0, 0, [], [], [])

		new = 0
		modified = 0
		timers = []
		conflicting = []
		similars = []

		if currentThread().getName() == 'MainThread':
			doBlockingCallFromMainThread = lambda f, *a, **kw: f(*a, **kw)
		else:
			doBlockingCallFromMainThread = blockingCallFromMainThread

		# NOTE: the config option specifies "the next X days" which means today (== 1) + X
		delta = timedelta(days = config.plugins.autotimer.maxdaysinfuture.value + 1)
		evtLimit = mktime((date.today() + delta).timetuple())
		checkEvtLimit = delta.days > 1
		del delta

		# Read AutoTimer configuration
		self.readXml()

		# Get E2 instances
		epgcache = eEPGCache.getInstance()
		serviceHandler = eServiceCenter.getInstance()
		recordHandler = NavigationInstance.instance.RecordTimer

		# Save Timer in a dict to speed things up a little
		# We include processed timers as we might search for duplicate descriptions
		# NOTE: It is also possible to use RecordTimer isInTimer(), but we won't get the timer itself on a match
		timerdict = defaultdict(list)
		doBlockingCallFromMainThread(self.populateTimerdict, epgcache, recordHandler, timerdict)

		# Create dict of all movies in all folders used by an autotimer to compare with recordings
		# The moviedict will be filled only if one AutoTimer is configured to avoid duplicate description for any recordings
		moviedict = defaultdict(list)

		# Iterate Timer
		for timer in self.getEnabledTimerList():
			tup = doBlockingCallFromMainThread(self.parseTimer, timer, epgcache, serviceHandler, recordHandler, checkEvtLimit, evtLimit, timers, conflicting, similars, timerdict, moviedict, simulateOnly=simulateOnly)
			new += tup[0]
			modified += tup[1]

		return (len(timers), new, modified, timers, conflicting, similars)

# Supporting functions

	def populateTimerdict(self, epgcache, recordHandler, timerdict):
		for timer in chain(recordHandler.timer_list, recordHandler.processed_timers):
			if timer and timer.service_ref:
				if timer.eit is not None:
					event = epgcache.lookupEventId(timer.service_ref.ref, timer.eit)
					extdesc = event and event.getExtendedDescription() or ''
					timer.extdesc = extdesc
				elif not hasattr(timer, 'extdesc'):
					timer.extdesc = ''
				timerdict[str(timer.service_ref)].append(timer)

	def modifyTimer(self, timer, name, shortdesc, begin, end, serviceref):
		timer.name = name
		timer.description = shortdesc
		timer.begin = int(begin)
		timer.end = int(end)
		timer.service_ref = ServiceReference(serviceref)

	def addDirectoryToMovieDict(self, moviedict, dest, serviceHandler):
		movielist = serviceHandler.list(eServiceReference("2:0:1:0:0:0:0:0:0:0:" + dest))
		if movielist is None:
			print("[AutoTimer] listing of movies in " + dest + " failed")
		else:
			append = moviedict[dest].append
			while 1:
				movieref = movielist.getNext()
				if not movieref.valid():
					break
				if movieref.flags & eServiceReference.mustDescent:
					continue
				info = serviceHandler.info(movieref)
				if info is None:
					continue
				event = info.getEvent(movieref)
				if event is None:
					continue
				append({
					"name": info.getName(movieref),
					"shortdesc": info.getInfoString(movieref, iServiceInformation.sDescription),
					"extdesc": event.getExtendedDescription() or '' # XXX: does event.getExtendedDescription() actually return None on no description or an empty string?
				})

	def checkSimilarity(self, timer, name1, name2, shortdesc1, shortdesc2, extdesc1, extdesc2, force=False):
		foundTitle = name1 == name2
		foundShort = shortdesc1 == shortdesc2 if (timer.searchForDuplicateDescription > 0 or force) else True
		foundExt = True
		# NOTE: only check extended if short description already is a match because otherwise
		# it won't evaluate to True anyway
		if (timer.searchForDuplicateDescription > 0 or force) and foundShort:
			# Some channels indicate replays in the extended descriptions
			# If the similarity percent is higher then 0.8 it is a very close match
			foundExt = ( 0.8 < SequenceMatcher(lambda x: x == " ",extdesc1, extdesc2).ratio() )

		return foundTitle and foundShort and foundExt
