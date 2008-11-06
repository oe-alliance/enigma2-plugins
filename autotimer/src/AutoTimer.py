# Plugins Config
from xml.etree.cElementTree import parse as cet_parse
from os import path as os_path
from AutoTimerConfiguration import parseConfig, writeConfig

# Navigation (RecordTimer)
import NavigationInstance

# Timer
from ServiceReference import ServiceReference
from RecordTimer import RecordTimerEntry
from Components.TimerSanityCheck import TimerSanityCheck

# Timespan
from time import localtime, time

# EPGCache & Event
from enigma import eEPGCache, eServiceReference

# Enigma2 Config
from Components.config import config

# AutoTimer Component
from AutoTimerComponent import AutoTimerComponent

XML_CONFIG = "/etc/enigma2/autotimer.xml"

def getTimeDiff(timer, begin, end):
	if begin <= timer.begin <= end:
		return end - timer.begin
	elif timer.begin <= begin <= timer.end:
		return timer.end - begin
	return 0

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
		# Keep EPGCache
		self.epgcache = eEPGCache.getInstance()

		# Initialize
		self.timers = []
		self.configMtime = -1
		self.uniqueTimerId = 0
		self.defaultTimer = AutoTimerComponent(
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

	def writeXml(self):
		writeConfig(XML_CONFIG, self.defaultTimer, self.timers)

# Manage List

	def add(self, timer):
		self.timers.append(timer)

	def getEnabledTimerList(self):
		return [x for x in self.timers if x.enabled]

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
			return (0, 0, 0, [])

		total = 0
		new = 0
		modified = 0
		timers = []

		self.readXml()

		# Save Recordings in a dict to speed things up a little
		# We include processed timers as we might search for duplicate descriptions
		recorddict = {}
		for timer in NavigationInstance.instance.RecordTimer.timer_list + NavigationInstance.instance.RecordTimer.processed_timers:
			if not recorddict.has_key(str(timer.service_ref)):
				recorddict[str(timer.service_ref)] = [timer]
			else:
				recorddict[str(timer.service_ref)].append(timer)

		# Iterate Timer
		for timer in self.getEnabledTimerList():
			# Search EPG, default to empty list
			ret = self.epgcache.search(('RI', 100, eEPGCache.PARTIAL_TITLE_SEARCH, timer.match, eEPGCache.NO_CASE_CHECK)) or []

			for serviceref, eit in ret:
				eserviceref = eServiceReference(serviceref)

				evt = self.epgcache.lookupEventId(eserviceref, eit)
				if not evt:
					print "[AutoTimer] Could not create Event!"
					continue

				# Try to determine real service (we always choose the last one)
				n = evt.getNumOfLinkageServices()
				if n > 0:
					i = evt.getLinkageService(eserviceref, n-1)
					serviceref = i.toString()

				# Gather Information
				name = evt.getEventName()
				description = evt.getShortDescription()
				begin = evt.getBeginTime()
				duration = evt.getDuration()
				end = begin + duration

				# If event starts in less than 60 seconds skip it
				if begin < time() + 60:
					continue

				# Convert begin time
				timestamp = localtime(begin)

				# Update timer
				timer.update(begin, timestamp)

				# Check Duration, Timespan and Excludes
				if timer.checkServices(serviceref) \
					or timer.checkDuration(duration) \
					or timer.checkTimespan(timestamp) \
					or timer.checkFilter(name, description,
						evt.getExtendedDescription(), str(timestamp.tm_wday)):
					continue

				if timer.hasOffset():
					# Apply custom Offset
					begin, end = timer.applyOffset(begin, end)
				else:
					# Apply E2 Offset
					begin -= config.recording.margin_before.value * 60
					end += config.recording.margin_after.value * 60


				total += 1

				# Append to timerlist and abort if simulating
				timers.append((name, begin, end, serviceref, timer.name))
				if simulateOnly:
					continue

				# Initialize
				newEntry = None
				isNew = False

				# Check for double Timers
				# We first check eit and if user wants us to guess event based on time
				# we try this as backup. The allowed diff should be configurable though.
				try:
					for rtimer in recorddict.get(serviceref, []):
						if rtimer.eit == eit or config.plugins.autotimer.try_guessing.value and getTimeDiff(rtimer, begin, end) > ((duration/10)*8):
							newEntry = rtimer

							# Abort if we don't want to modify timers or timer is repeated
							if config.plugins.autotimer.refresh.value == "none" or newEntry.repeated:
								raise AutoTimerIgnoreTimerException("Won't modify existing timer because either no modification allowed or repeated timer")

							if hasattr(newEntry, "isAutoTimer"):
									print "[AutoTimer] Modifying existing AutoTimer!"
							else:
								if config.plugins.autotimer.refresh.value != "all":
									raise AutoTimerIgnoreTimerException("Won't modify existing timer because it's no timer set by us")
								print "[AutoTimer] Warning, we're messing with a timer which might not have been set by us"

							modified += 1

							# Modify values saved in timer
							newEntry.name = name
							newEntry.description = description
							newEntry.begin = int(begin)
							newEntry.end = int(end)
							newEntry.service_ref = ServiceReference(serviceref)

							break
						elif timer.getAvoidDuplicateDescription() == 1 and rtimer.description == description:
								raise AutoTimerIgnoreTimerException("We found a timer with same description, skipping event")
					if newEntry is None and timer.getAvoidDuplicateDescription() == 2:
						for list in recorddict.values():
							for rtimer in list:
								if rtimer.description == description:
									raise AutoTimerIgnoreTimerException("We found a timer with same description, skipping event")

				except AutoTimerIgnoreTimerException, etite:
					print etite
					continue

				# Event not yet in Timers
				if newEntry is None:
					if timer.checkCounter(timestamp):
						continue

					isNew = True

					print "[AutoTimer] Adding an event."
					newEntry = RecordTimerEntry(ServiceReference(serviceref), begin, end, name, description, eit)

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
				newEntry.tags = timer.tags # This needs my enhanced tag support patch to work

				if isNew:
					if NavigationInstance.instance.RecordTimer.record(newEntry) is None:
						new += 1
						if recorddict.has_key(serviceref):
							recorddict[serviceref].append(newEntry)
						else:
							recorddict[serviceref] = [newEntry]
				else:
					# XXX: this won't perform a sanity check, but do we actually want to do so?
					NavigationInstance.instance.RecordTimer.timeChanged(newEntry)

		return (total, new, modified, timers)

