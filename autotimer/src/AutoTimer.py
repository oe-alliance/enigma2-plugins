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

# Enigma2 Config
from Components.config import config

# AutoTimer Component
from AutoTimerComponent import preferredAutoTimerComponent

XML_CONFIG = "/etc/enigma2/autotimer.xml"

def getTimeDiff(timer, begin, end):
	if begin <= timer.begin <= end:
		return end - timer.begin
	elif timer.begin <= begin <= timer.end:
		return timer.end - begin
	return 0

typeMap = {
	"exact": eEPGCache.EXAKT_TITLE_SEARCH,
	"partial": eEPGCache.PARTIAL_TITLE_SEARCH
}

caseMap = {
	"sensitive": eEPGCache.CASE_CHECK,
	"insensitive": eEPGCache.NO_CASE_CHECK
}

class AutoTimerIgnoreTimerException(Exception):
	def __init__(self, cause):
		self.cause = cause

	def __str__(self):
		return "[AutoTimer] " + str(self.cause)

	def __repr__(self):
		return str(type(self))

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
			print "[AutoTimer] No configuration file present"
			return

		# Parse if mtime differs from whats saved
		mtime = os_path.getmtime(XML_CONFIG)
		if mtime == self.configMtime:
			print "[AutoTimer] No changes in configuration, won't parse"
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
		list = self.timers
		return [(x,) for x in list]

	def getSortedTupleTimerList(self):
		list = self.timers[:]
		list.sort()
		return [(x,) for x in list]

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

# Main function

	def parseEPG(self, simulateOnly = False):
		if NavigationInstance.instance is None:
			print "[AutoTimer] Navigation is not available, can't parse EPG"
			return (0, 0, 0, [], [], [])

		total = 0
		new = 0
		modified = 0
		timers = []
		conflicting = []
		similar = {}			# Contains the the marked similar servicerefs and the conflicting string
		similars = []			# Contains the added similar timers 

		# NOTE: the config option specifies "the next X days" which means today (== 1) + X
		delta = timedelta(days = config.plugins.autotimer.maxdaysinfuture.value + 1)
		evtLimit = mktime((date.today() + delta).timetuple())
		checkEvtLimit = delta.days > 1
		del delta

		# Read AutoTimer Configuration
		self.readXml()

		# Get E2 EPGCache Instance
		epgcache = eEPGCache.getInstance()

		# Save Recordings in a dict to speed things up a little
		# We include processed timers as we might search for duplicate descriptions
		recorddict = {}
		for timer in NavigationInstance.instance.RecordTimer.timer_list + NavigationInstance.instance.RecordTimer.processed_timers:
			recorddict.setdefault(str(timer.service_ref), []).append(timer)

		# Create dict of all movies in all folders used by an autotimer to compare with recordings
		moviedict = {}
		serviceHandler = eServiceCenter.getInstance()

		# Iterate Timer
		for timer in self.getEnabledTimerList():
			# Precompute timer destination dir
			dest = timer.destination or config.usage.default_path.value

			# Workaround to allow search for umlauts if we know the encoding
			match = timer.match
			if timer.encoding != 'UTF-8':
				try:
					match = match.decode('UTF-8').encode(timer.encoding)
				except UnicodeDecodeError:
					pass

			# Search EPG, default to empty list
			epgmatches = epgcache.search(('RITBDSE', 500, typeMap[timer.searchType], match, caseMap[timer.searchCase])) or []

			# Sort list of tuples by begin time 'B'
			epgmatches.sort(key = lambda x: x[3]) 

			# Reset the the marked similar servicerefs
			similar.clear()

			# Loop over all EPG matches
			for serviceref, eit, name, begin, duration, shortdesc, extdesc in epgmatches:

				# Reset similarMatch and conflictString
				similarMatch = False
				conflictString = ""
				
				# Check if serviceref is in similar matches list
				if serviceref in similar:
					similarMatch = True
					conflictString = similar[serviceref]
					del similar[serviceref]

				###### Do we need this ?
				eserviceref = eServiceReference(serviceref)
				evt = epgcache.lookupEventId(eserviceref, eit)
				if not evt:
					print "[AutoTimer] Could not create Event!"
					continue

				# Try to determine real service (we always choose the last one)
				n = evt.getNumOfLinkageServices()
				if n > 0:
					i = evt.getLinkageService(eserviceref, n-1)
					serviceref = i.toString()
				######

				evtBegin = begin
				evtEnd = end = begin + duration
				
				# If event starts in less than 60 seconds skip it
				if begin < time() + 60:
					print "[AutoTimer] Skipping an event because it starts in less than 60 seconds"
					continue

				# If maximum days in future is set then check time
				if checkEvtLimit:
					if begin > evtLimit:
						continue

				# Convert begin time
				timestamp = localtime(begin)

				# Update timer
				timer.update(begin, timestamp)

				# Check Duration, Timespan, Timeframe and Excludes
				# Remove similarMatch if You want perform the check also on similar timers
				if timer.checkServices(serviceref) \
					or timer.checkDuration(duration) \
					or ( not similarMatch and timer.checkTimespan(timestamp) ) \
					or ( not similarMatch and timer.checkTimeframe(begin) ) \
					or timer.checkFilter(name, shortdesc, extdesc, ( not similarMatch and str(timestamp.tm_wday) ) ):
					continue

				if timer.hasOffset():
					# Apply custom Offset
					begin, end = timer.applyOffset(begin, end)
				else:
					# Apply E2 Offset
					begin -= config.recording.margin_before.value * 60
					end += config.recording.margin_after.value * 60

				# Eventually change service to alternative
				if timer.overrideAlternatives:
					serviceref = timer.getAlternative(serviceref)

				total += 1

				# Append to timerlist and abort if simulating
				#if not similarMatch: # Do we want the similar timers in the timers list?
				timers.append((name, begin, end, serviceref, timer.name))
				if simulateOnly:
					continue

				# Check for existing recordings in directory
				if timer.avoidDuplicateDescription == 3:
					# Reset movie Exists
					movieExists = False

					# Eventually create cache
					if dest and dest not in moviedict:
						movielist = serviceHandler.list(eServiceReference("2:0:1:0:0:0:0:0:0:0:" + dest))
						if movielist is None:
							print "[AutoTimer] listing of movies in " + dest + " failed"
						else:
							moviedict[dest] = []
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
									"extdesc": event.getExtendedDescription()
								})
							del append

					for movieinfo in moviedict.get(dest, ()):
						if movieinfo.get("name") == name \
							and movieinfo.get("shortdesc") == shortdesc \
							and movieinfo.get("extdesc") == extdesc:
							print "[AutoTimer] We found a matching recorded movie, skipping event:", name
							movieExists = True
							break

					if movieExists:
						continue

				# Initialize
				newEntry = None
				oldExists = False
				similarExists = False		# Indicates if we found a matching similar timer

				# Check for double Timers
				# We first check eit and if user wants us to guess event based on time
				# we try this as backup. The allowed diff should be configurable though.
				for rtimer in recorddict.get(serviceref, ()):
					if rtimer.eit == eit or config.plugins.autotimer.try_guessing.value and getTimeDiff(rtimer, evtBegin, evtEnd) > ((duration/10)*8):
						oldExists = True

						# Abort if we don't want to modify timers or timer is repeated
						if config.plugins.autotimer.refresh.value == "none" or rtimer.repeated:
							print "[AutoTimer] Won't modify existing timer because either no modification allowed or repeated timer"
							break

						if hasattr(rtimer, "isAutoTimer"):
							rtimer.log(501, "[AutoTimer] AutoTimer %s modified this automatically generated timer." % (timer.name,))
						else:
							if config.plugins.autotimer.refresh.value != "all":
								print "[AutoTimer] Won't modify existing timer because it's no timer set by us"
								break

							rtimer.log(501, "[AutoTimer] Warning, AutoTimer %s messed with a timer which might not belong to it." % (timer.name,))

						newEntry = rtimer
						modified += 1

						# Modify values saved in timer
						newEntry.name = name
						newEntry.description = shortdesc
						newEntry.begin = int(begin)
						newEntry.end = int(end)
						newEntry.service_ref = ServiceReference(serviceref)

						break
					elif timer.avoidDuplicateDescription >= 1 and not rtimer.disabled and rtimer.name == name and rtimer.description == shortdesc:
						oldExists = True
						print "[AutoTimer] We found a timer with same description, skipping event"
						break

				# We found no timer we want to edit
				if newEntry is None:
					# But there is a match
					if oldExists:
						continue

					# We want to search for possible doubles
					if timer.avoidDuplicateDescription >= 2:
						# I thinks thats the fastest way to do this, though it's a little ugly
						try:
							for list in recorddict.values():
								for rtimer in list:
									if not rtimer.disabled and rtimer.name == name and rtimer.description == shortdesc:
										raise AutoTimerIgnoreTimerException("We found a timer with same description, skipping event")
						except AutoTimerIgnoreTimerException, etite:
							print "[AutoTimer] exception: " + str(etite)
							continue

					if timer.checkCounter(timestamp):
						print "[AutoTimer] Not adding new timer because counter is depleted."
						continue

					newEntry = RecordTimerEntry(ServiceReference(serviceref), begin, end, name, shortdesc, eit)
					newEntry.log(500, "[AutoTimer] Adding new timer based on AutoTimer %s." % (timer.name,))

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
				newEntry.tags = timer.tags
				newEntry.vpsplugin_enabled = timer.vps_enabled
				newEntry.vpsplugin_overwrite = timer.vps_overwrite

				if oldExists:
					# XXX: this won't perform a sanity check, but do we actually want to do so?
					NavigationInstance.instance.RecordTimer.timeChanged(newEntry)
				else:
					if similarMatch:
						newEntry.log(504, "[AutoTimer] Similar Timer is added because of conflicts with %s." % (conflictString))
					conflicts = NavigationInstance.instance.RecordTimer.record(newEntry)

					if conflicts:
						conflictString += ' / '.join(["%s (%s)" % (x.name, strftime("%Y%m%d %H%M", localtime(x.begin))) for x in conflicts])

					if conflicts and config.plugins.autotimer.addsimilar_on_conflict.value:
						for servicerefS, eitS, nameS, beginS, durationS, shortdescS, extdescS in epgmatches:
							if evtBegin < beginS:
								# Match must be after our conflicting event
								if extdesc == extdescS and shortdesc == shortdescS:
									# Match only if the descriptions are equal
									print "[AutoTimer] Found similar Timer: " + name
									
									# Indicate that there exists a similar timer
									similarExists = True
									
									# Store the similar serviceref and conflictString, so it can be handled later
									similar[servicerefS] = conflictString
									
									# If this one also will conflict and there are more matches, they will be marked the next time 
									break

					if conflicts and config.plugins.autotimer.disabled_on_conflict.value and not similarExists:			# Don't add disabled timer if a similar timer exists
					#if conflicts and config.plugins.autotimer.disabled_on_conflict.value:													# Add disabled timer even if a similar timer exists
						newEntry.log(503, "[AutoTimer] Timer disabled because of conflicts with %s." % (conflictString,))
						newEntry.disabled = True
						# We might want to do the sanity check locally so we don't run it twice - but I consider this workaround a hack anyway
						conflicts = NavigationInstance.instance.RecordTimer.record(newEntry)
						conflicting.append((name, begin, end, serviceref, timer.name))

					if conflicts is None: 											# Similar timers will be added to the new timer list
					#if conflicts is None and not similarMatch: # Similar timers won't be added to the new timer list
						timer.decrementCounter()
						new += 1
						recorddict.setdefault(serviceref, []).append(newEntry)

					elif conflicts: 														# Conflicting timers will be added also if a similar timer exists
					#elif conflicts and not similarExists: 			# Conflicting timers won't be added if a similar timer exists
						conflicting.append((name, begin, end, serviceref, timer.name))

					if similarMatch and conflicts is None:			# Similar timers can be in new timers list and additionally in similar timers list
					#elif similarMatch and conflicts is None:		# Similar timers will be only in new timers list or similar timers list
						similars.append((name, begin, end, serviceref, timer.name))

		return (total, new, modified, timers, conflicting, similars)
