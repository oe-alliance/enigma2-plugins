# Plugins Config
from xml.etree.cElementTree import parse as cet_parse
from os import path as os_path
from AutoTimerConfiguration import parseConfig, buildConfig

import Components.Task
from twisted.internet import reactor, threads, task

# GUI (Screens)
from Screens.MessageBox import MessageBox
from Tools.FuzzyDate import FuzzyTime
from Tools.Notifications import AddPopup

# Navigation (RecordTimer)
import NavigationInstance

# Timer
from ServiceReference import ServiceReference
from RecordTimer import RecordTimerEntry
from Components.TimerSanityCheck import TimerSanityCheck

# Timespan
from time import localtime, time, mktime, sleep
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
	def parseEPG(self, autoPoll = False, simulateOnly = False):
		name = _("AutoTimerTask")
		job = Components.Task.Job(name)
		task = AutoTimerTask(job, name)
		task.setup(autoPoll, simulateOnly)
		Components.Task.job_manager.AddJob(job)

#class FailedPostcondition(Components.Task.Condition):
	#def __init__(self, exception):
		#self.exception = exception
	#def getErrorMessage(self, task):
		#return str(self.exception)
	#def check(self, task):
		#return self.exception is None

class AutoTimerTask(Components.Task.PythonTask):
	def setup(self, autoPoll, simulateOnly):
		autotimer = AutoTimer()
		if NavigationInstance.instance is None:
			print "[AutoTimer] Navigation is not available, can't parse EPG"
			return (0, 0, 0, [], [])

		self.total = 0
		self.new = 0
		self.modified = 0
		self.nooftimers = []
		self.conflicting = []
		self.autoPoll = autoPoll
		self.simulateOnly = simulateOnly


		self.readXml = autotimer.readXml()

		self.getEnabledTimerList = autotimer.getEnabledTimerList()

	def work(self):
		# NOTE: the config option specifies "the next X days" which means today (== 1) + X
		delta = timedelta(days = config.plugins.autotimer.maxdaysinfuture.value + 1)
		evtLimit = mktime((date.today() + delta).timetuple())
		self.checkEvtLimit = delta.days > 1
		del delta
		
		# Save Recordings in a dict to speed things up a little
		# We include processed timers as we might search for duplicate descriptions
		self.recorddict = {}
		for timer in NavigationInstance.instance.RecordTimer.timer_list + NavigationInstance.instance.RecordTimer.processed_timers:
			self.recorddict.setdefault(str(timer.service_ref), []).append(timer)

		# Create dict of all movies in all folders used by an autotimer to compare with recordings
		self.moviedict = {}
		self.serviceHandler = eServiceCenter.getInstance()

		# Iterate Timer
		for timer in self.getEnabledTimerList:
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
			epgcache = eEPGCache.getInstance()
			ret = epgcache.search(('RI', 900, typeMap[timer.searchType], match, caseMap[timer.searchCase])) or ()

			for serviceref, eit in ret:
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

				# Gather Information
				name = evt.getEventName()
				description = evt.getShortDescription()
				if description == "":
					description = evt.getExtendedDescription()
				begin = evt.getBeginTime()
				duration = evt.getDuration()
				end = begin + duration

				# If event starts in less than 60 seconds skip it
				if begin < time() + 60:
					continue

				# If maximum days in future is set then check time
				if self.checkEvtLimit:
					if begin > evtLimit:
						continue

				# Convert begin time
				timestamp = localtime(begin)

				# Update timer
				timer.update(begin, timestamp)

				# Check Duration, Timespan, Timeframe and Excludes
				if timer.checkServices(serviceref) \
					or timer.checkDuration(duration) \
					or timer.checkTimespan(timestamp) \
					or timer.checkTimeframe(begin) \
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

				# Eventually change service to alternative
				if timer.overrideAlternatives:
					serviceref = timer.getAlternative(serviceref)

				self.total += 1

				# Append to timerlist and abort if simulating
				self.nooftimers.append((name, begin, end, serviceref, timer.name))
				if self.simulateOnly:
					continue

				# Reset movie Exists
				movieExists = False

				# Check for existing recordings in directory
				if timer.avoidDuplicateDescription == 3:
					# Eventually create cache
					if dest and dest not in self.moviedict:
						movielist = self.serviceHandler.list(eServiceReference("2:0:1:0:0:0:0:0:0:0:" + dest))
						if movielist is None:
							print "[AutoTimer] listing of movies in " + dest + " failed"
						else:
							self.moviedict.setdefault(dest, [])
							append = self.moviedict[dest].append
							while 1:
								movieref = movielist.getNext()
								if not movieref.valid():
									break
								if movieref.flags & eServiceReference.mustDescent:
									continue
								info = self.serviceHandler.info(movieref)
								if info is None:
									continue
								append({
									"name": info.getName(movieref),
									"description": info.getInfoString(movieref, iServiceInformation.sDescription)
								})
							del append

					for movieinfo in self.moviedict.get(dest, ()):
						moviename = movieinfo.get("name")
						moviedescription = movieinfo.get("description")
						if moviename == name and moviedescription == description:
							print "[AutoTimer] We found a matching recorded movie, skipping event:", name
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
				for rtimer in self.recorddict.get(serviceref, ()):
					if rtimer.eit == eit or config.plugins.autotimer.try_guessing.value and getTimeDiff(rtimer, begin, end) > ((duration/10)*8):
						oldExists = True

						# Abort if we don't want to modify timers or timer is repeated
						if config.plugins.autotimer.refresh.value == "none" or rtimer.repeated:
							print "[AutoTimer] Won't modify existing timer because either no modification allowed or repeated timer"
							break

						if hasattr(rtimer, "isAutoTimer"):
								print "[AutoTimer] Modifying existing AutoTimer!"
						else:
							if config.plugins.autotimer.refresh.value != "all":
								print "[AutoTimer] Won't modify existing timer because it's no timer set by us"
								break

							print "[AutoTimer] Warning, we're messing with a timer which might not have been set by us"

						newEntry = rtimer
						self.modified += 1

						# Modify values saved in timer
						newEntry.name = name
						newEntry.description = description
						newEntry.begin = int(begin)
						newEntry.end = int(end)
						newEntry.service_ref = ServiceReference(serviceref)

						break
					elif timer.avoidDuplicateDescription >= 1 and not rtimer.disabled and rtimer.name == name and rtimer.description == description:
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
							for list in self.recorddict.values():
								for rtimer in list:
									if not rtimer.disabled and rtimer.name == name and rtimer.description == description:
										raise AutoTimerIgnoreTimerException("We found a timer with same description, skipping event")
						except AutoTimerIgnoreTimerException, etite:
							print etite
							continue

					if timer.checkCounter(timestamp):
						continue

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
				newEntry.tags = timer.tags

				if oldExists:
					# XXX: this won't perform a sanity check, but do we actually want to do so?
					NavigationInstance.instance.RecordTimer.timeChanged(newEntry)
				else:
					conflicts = NavigationInstance.instance.RecordTimer.record(newEntry)
					if conflicts and config.plugins.autotimer.disabled_on_conflict.value:
						newEntry.disabled = True
						# We might want to do the sanity check locally so we don't run it twice - but I consider this workaround a hack anyway
						conflicts = NavigationInstance.instance.RecordTimer.record(newEntry)
						self.conflicting.append((name, begin, end, serviceref, timer.name))
					if conflicts is None:
						timer.decrementCounter()
						self.new += 1
						self.recorddict.setdefault(serviceref, []).append(newEntry)
					else:
						self.conflicting.append((name, begin, end, serviceref, timer.name))
			sleep(0.5)

		if self.autoPoll:
			if self.conflicting and config.plugins.autotimer.notifconflict.value:
				AddPopup(_("%d conflict(s) encountered when trying to add new timers:\n%s") % (len(self.conflicting), '\n'.join([_("%s: %s at %s") % (x[4], x[0], FuzzyTime(x[2])) for x in self.conflicting])), type = MessageBox.TYPE_INFO, timeout = 10)
		else:
			AddPopup(_("Found a total of %d matching Events.\n%d Timer were added and %d modified, %d conflicts encountered.") % (self.total, self.new, self.modified, len(self.conflicting)), type = MessageBox.TYPE_INFO, timeout = 10)
	
		#return (self.total, self.new, self.modified, self.nooftimers, self.conflicting)
