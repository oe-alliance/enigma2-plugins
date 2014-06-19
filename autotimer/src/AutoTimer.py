from __future__ import print_function

# for localized messages
from . import _

# Plugins Config
from xml.etree.cElementTree import parse as cet_parse
from os import path as os_path
from AutoTimerConfiguration import parseConfig, buildConfig

# Tasks
import Components.Task

# GUI (Screens)
from Screens.MessageBox import MessageBox
from Tools.FuzzyDate import FuzzyTime
from Tools.Notifications import AddPopup

# Navigation (RecordTimer)
import NavigationInstance

# Timer
from ServiceReference import ServiceReference
from RecordTimer import RecordTimerEntry
# from Components.TimerSanityCheck import TimerSanityCheck

# Timespan
from time import localtime, strftime, time, mktime, sleep
from datetime import timedelta, date

# EPGCache & Event
from enigma import eEPGCache, eServiceReference, eServiceCenter, iServiceInformation

# from twisted.internet import reactor, defer
# from twisted.python import failure
# from threading import currentThread
# import Queue

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

NOTIFICATIONID = 'AutoTimerNotification'
CONFLICTNOTIFICATIONID = 'AutoTimerConflictEncounteredNotification'
SIMILARNOTIFICATIONID = 'AutoTimerSimilarUsedNotification'

def getTimeDiff(timer, begin, end):
	if begin <= timer.begin <= end:
		return end - timer.begin
	elif timer.begin <= begin <= timer.end:
		return timer.end - begin
	return 0

# def blockingCallFromMainThread(f, *a, **kw):
# 	"""
# 	  Modified version of twisted.internet.threads.blockingCallFromThread
# 	  which waits 30s for results and otherwise assumes the system to be shut down.
# 	  This is an ugly workaround for a twisted-internal deadlock.
# 	  Please keep the look intact in case someone comes up with a way
# 	  to reliably detect from the outside if twisted is currently shutting
# 	  down.
# 	"""
# 	queue = Queue.Queue()
# 	def _callFromThread():
# 		result = defer.maybeDeferred(f, *a, **kw)
# 		result.addBoth(queue.put)
# 	reactor.callFromThread(_callFromThread)
# 
# 	result = None
# 	while True:
# 		try:
# 			result = queue.get(True, 30)
# 		except Queue.Empty as qe:
# 			if True: #not reactor.running: # reactor.running is only False AFTER shutdown, we are during.
# 				raise ValueError("Reactor no longer active, aborting.")
# 		else:
# 			break
# 
# 	if isinstance(result, failure.Failure):
# 		result.raiseException()
# 	return result

typeMap = {
	"exact": eEPGCache.EXAKT_TITLE_SEARCH,
	"partial": eEPGCache.PARTIAL_TITLE_SEARCH,
	"start": eEPGCache.START_TITLE_SEARCH,
	"description": -99
}

caseMap = {
	"sensitive": eEPGCache.CASE_CHECK,
	"insensitive": eEPGCache.NO_CASE_CHECK
}

# class AutoTimerIgnoreTimerException(Exception):
# 	def __init__(self, cause):
# 		self.cause = cause
# 
# 	def __str__(self):
# 		return "[AutoTimer] " + str(self.cause)
# 
# 	def __repr__(self):
# 		return str(type(self))

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
		file = open(XML_CONFIG, 'r')
		configuration = cet_parse(file).getroot()
		file.close()

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
		return sorted([x for x in self.timers if x.enabled], key=lambda x: x.name)

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

	#call from epgrefresh
	def parseEPGAsync(self, simulateOnly=False):
		t = SimpleThread(lambda: self.parseEPG(simulateOnly=simulateOnly))
		t.start()
		return t.deferred

	# Main function
	def parseEPG(self, autoPoll = False, simulateOnly = False):
		self.autoPoll = autoPoll
		self.simulateOnly = simulateOnly
		# if NavigationInstance.instance is None:
		# 	print("[AutoTimer] Navigation is not available, can't parse EPG")
		# 	return (0, 0, 0, [], [], [])

		self.new = 0
		self.modified = 0
		self.skipped = 0
		self.total = 0
		self.autotimers = []
		self.conflicting = []
		self.similars = []

		# if currentThread().getName() == 'MainThread':
		# 	doBlockingCallFromMainThread = lambda f, *a, **kw: f(*a, **kw)
		# else:
		# 	doBlockingCallFromMainThread = blockingCallFromMainThread

		# NOTE: the config option specifies "the next X days" which means today (== 1) + X
		delta = timedelta(days = config.plugins.autotimer.maxdaysinfuture.getValue() + 1)
		self.evtLimit = mktime((date.today() + delta).timetuple())
		self.checkEvtLimit = delta.days > 1
		del delta

		# Read AutoTimer configuration
		self.readXml()

		# Get E2 instances
		self.epgcache = eEPGCache.getInstance()
		self.serviceHandler = eServiceCenter.getInstance()
		self.recordHandler = NavigationInstance.instance.RecordTimer

		# Save Timer in a dict to speed things up a little
		# We include processed timers as we might search for duplicate descriptions
		# NOTE: It is also possible to use RecordTimer isInTimer(), but we won't get the timer itself on a match
		self.timerdict = defaultdict(list)
		self.populateTimerdict(self.epgcache, self.recordHandler, self.timerdict)

		# Create dict of all movies in all folders used by an autotimer to compare with recordings
		# The moviedict will be filled only if one AutoTimer is configured to avoid duplicate description for any recordings
		self.moviedict = defaultdict(list)

		# Iterate Timer
		Components.Task.job_manager.AddJob(self.createTask())

		# for timer in self.getEnabledTimerList():
		# 	tup = doBlockingCallFromMainThread(self.parseTimer, timer, self.epgcache, self.serviceHandler, self.recordHandler, self.checkEvtLimit, self.evtLimit, self.autotimers, self.conflicting, self.similars, self.timerdict, self.moviedict, self.simulateOnly)
		# 	new += tup[0]
		# 	modified += tup[1]
		# return (len(timers), new, modified, timers, conflicting, similars)

	def createTask(self):
		self.timer_count = 0
		self.completed = []
		job = Components.Task.Job(_("AutoTimer"))
		timer = None

		# Iterate Timer
		for timer in self.getEnabledTimerList():
			task = Components.Task.PythonTask(job, timer.name)
			task.work = self.JobStart
			task.weighting = 1
			self.timer_count += 1

		if timer:
			task = Components.Task.PythonTask(job, 'Show results')
			task.work = self.JobMessage
			task.weighting = 1
		
		return job

	def JobStart(self):
		for timer in self.getEnabledTimerList():
			if timer.name not in self.completed:
				self.parseTimer(timer, self.epgcache, self.serviceHandler, self.recordHandler, self.checkEvtLimit, self.evtLimit, self.autotimers, self.conflicting, self.similars, self.timerdict, self.moviedict, self.simulateOnly)
				self.new += self.result[0]
				self.modified += self.result[1]
				self.skipped += self.result[2]
				break

	def parseTimer(self, timer, epgcache, serviceHandler, recordHandler, checkEvtLimit, evtLimit, timers, conflicting, similars, timerdict, moviedict, simulateOnly=False):
		new = 0
		modified = 0
		skipped = 0

		# Precompute timer destination dir
		dest = timer.destination or config.usage.default_path.getValue()

		# Workaround to allow search for umlauts if we know the encoding
		match = timer.match.replace('\xc2\x86', '').replace('\xc2\x87', '')
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
				if config.usage.multibouquet.getValue():
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
			epgmatches = epgcache.search( ('RITBDSE', 3000, typeMap[timer.searchType], match, caseMap[timer.searchCase]) ) or []

		# Sort list of tuples by begin time 'B'
		epgmatches.sort(key=itemgetter(3))

		# Contains the the marked similar eits and the conflicting strings
		similardict = defaultdict(list)		

		# Loop over all EPG matches
		preveit = False
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
			# if begin < time() + 60:
			# 	print ("[AutoTimer] Skipping " + name + " because it starts in less than 60 seconds")
			# 	skipped += 1
			# 	continue

			# Set short description to equal extended description if it is empty.
			if not shortdesc:
				shortdesc = extdesc

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
				begin -= config.recording.margin_before.getValue() * 60
				end += config.recording.margin_after.getValue() * 60

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
					if self.checkSimilarity(timer, name, movieinfo.get("name"), shortdesc, movieinfo.get("shortdesc"), extdesc, movieinfo.get("extdesc")):
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
				if (rtimer.eit == eit or config.plugins.autotimer.try_guessing.getValue()) and getTimeDiff(rtimer, evtBegin, evtEnd) > ((duration/10)*8):
					oldExists = True
					
					# Abort if we don't want to modify timers or timer is repeated
					if config.plugins.autotimer.refresh.getValue() == "none" or rtimer.repeated:
						print("[AutoTimer] Won't modify existing timer because either no modification allowed or repeated timer")
						break

					if eit == preveit:
						break
					
					if (evtBegin - (config.recording.margin_before.getValue() * 60) != rtimer.begin) or (evtEnd + (config.recording.margin_after.getValue() * 60) != rtimer.end) or (shortdesc != rtimer.description):
						if rtimer.isAutoTimer and eit == rtimer.eit:
							print ("[AutoTimer] AutoTimer %s modified this automatically generated timer." % (timer.name))
							rtimer.log(501, "[AutoTimer] AutoTimer %s modified this automatically generated timer." % (timer.name))
							preveit = eit
						else:
							if config.plugins.autotimer.refresh.getValue() != "all":
								print("[AutoTimer] Won't modify existing timer because it's no timer set by us")
								break
							rtimer.log(501, "[AutoTimer] Warning, AutoTimer %s messed with a timer which might not belong to it: %s ." % (timer.name, rtimer.name))
						newEntry = rtimer
						modified += 1
						self.modifyTimer(rtimer, name, shortdesc, begin, end, serviceref, eit)
						rtimer.log(501, "[AutoTimer] AutoTimer modified timer: %s ." % (rtimer.name))
						break
					else:
						print ("[AutoTimer] Skipping timer because it has not changed.")
						skipped += 1
						break
				elif timer.avoidDuplicateDescription >= 1 and not rtimer.disabled:
					if self.checkSimilarity(timer, name, rtimer.name, shortdesc, rtimer.description, extdesc, rtimer.extdesc ):
						print("[AutoTimer] We found a timer with similar description, skipping event")
						oldExists = True
						break

			# We found no timer we want to edit
			if newEntry is None:
				# But there is a match
				if oldExists:
					continue

				# We want to search for possible doubles
				for rtimer in chain.from_iterable( itervalues(timerdict) ):
					if not rtimer.disabled:
						if self.checkDoubleTimers(timer, name, rtimer.name, begin, rtimer.begin, end, rtimer.end ):
							oldExists = True
							# print("[AutoTimer] We found a timer with same StartTime, skipping event")
							break
						if timer.avoidDuplicateDescription >= 2:
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
			if config.plugins.autotimer.add_autotimer_to_tags.getValue():
				tags.append('AutoTimer')
			if config.plugins.autotimer.add_name_to_tags.getValue():
				tagname = timer.name.strip()
				if tagname:
					tagname = tagname[0].upper() + tagname[1:].replace(" ", "_")
					tags.append(tagname)
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

					if config.plugins.autotimer.addsimilar_on_conflict.getValue():
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

					if config.plugins.autotimer.disabled_on_conflict.getValue():
						newEntry.log(503, "[AutoTimer] Timer disabled because of conflicts with %s." % (conflictString))
						newEntry.disabled = True
						# We might want to do the sanity check locally so we don't run it twice - but I consider this workaround a hack anyway
						conflicts = recordHandler.record(newEntry)
		self.result=(new, modified, skipped)
		self.completed.append(timer.name)
		sleep(0.5)
		# return (new, modified)

	def JobMessage(self):
		if self.autoPoll:
			if self.conflicting and config.plugins.autotimer.notifconflict.value:
				AddPopup(
					_("%d conflict(s) encountered when trying to add new timers:\n%s") % (len(self.conflicting), '\n'.join([_("%s: %s at %s") % (x[4], x[0], FuzzyTime(x[2])) for x in self.conflicting])),
					MessageBox.TYPE_INFO,
					15,
					CONFLICTNOTIFICATIONID
				)
			elif self.similars and config.plugins.autotimer.notifsimilar.value:
				AddPopup(
					_("%d conflict(s) solved with similar timer(s):\n%s") % (len(self.similars), '\n'.join([_("%s: %s at %s") % (x[4], x[0], FuzzyTime(x[2])) for x in self.similars])),
					MessageBox.TYPE_INFO,
					15,
					SIMILARNOTIFICATIONID
				)
		else:
			AddPopup(
				_("Found a total of %d matching Events.\n%d Timer were added and\n%d modified,\n%d conflicts encountered,\n%d unchanged,\n%d similars added.") % ((self.new+self.modified+len(self.conflicting)+self.skipped+len(self.similars)), self.new, self.modified, len(self.conflicting), self.skipped, len(self.similars)),
				MessageBox.TYPE_INFO,
				15,
				NOTIFICATIONID
			)
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

	def modifyTimer(self, timer, name, shortdesc, begin, end, serviceref, eit):
		# Don't update the name, it will overwrite the name of the SeriesPlugin
		#timer.name = name
		timer.description = shortdesc
		timer.begin = int(begin)
		timer.end = int(end)
		timer.service_ref = ServiceReference(serviceref)
		timer.eit = eit

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
		foundTitle = False
		foundShort = False
		foundExt = False
		if name1 and name2:
			foundTitle = ( 0.8 < SequenceMatcher(lambda x: x == " ",name1, name2).ratio() )
		# NOTE: only check extended & short if tile is a partial match
		if foundTitle:
			if timer.searchForDuplicateDescription > 0 or force:
				if extdesc1 and extdesc2:
					# Some channels indicate replays in the extended descriptions
					# If the similarity percent is higher then 0.7 it is a very close match
					foundExt = ( 0.7 < SequenceMatcher(lambda x: x == " ",extdesc1, extdesc2).ratio() )

				if not foundExt and shortdesc1 and shortdesc2:
					# some channels do not use extended description, so try to find a close match to short description.
					# If the similarity percent is higher then 0.7 it is a very close match
					foundShort = ( 0.7 < SequenceMatcher(lambda x: x == " ",shortdesc1, shortdesc2).ratio() )
		return foundShort or foundExt

	def checkDoubleTimers(self, timer, name1, name2, starttime1, starttime2, endtime1, endtime2):
		foundTitle = name1 == name2
		foundstart = starttime1 == starttime2
		foundend = endtime1 == endtime2
		return foundTitle and foundstart and foundend
