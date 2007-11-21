# Plugins Config
from xml.dom.minidom import parse as minidom_parse
from os import path as os_path

# Navigation (RecordTimer)
import NavigationInstance

# Timer
from ServiceReference import ServiceReference
from RecordTimer import RecordTimerEntry, AFTEREVENT
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
CURRENT_CONFIG_VERSION = "4"

def getValue(definitions, default, isList = True):
	# Initialize Output
	ret = ""

	# How many definitions are present
	if isList:
		Len = len(definitions)
		if Len > 0:
			childNodes = definitions[Len-1].childNodes
		else:
			childNodes = []
	else:
		childNodes = definitions.childNodes

	# Iterate through nodes of last one
	for node in childNodes:
		# Append text if we have a text node
		if node.nodeType == node.TEXT_NODE:
			ret = ret + node.data

	# Return stripped output or (if empty) default
	return ret.strip() or default

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

	def readXml(self):
		# Abort if no config found
		if not os_path.exists(XML_CONFIG):
			return

		# Parse if mtime differs from whats saved
		mtime = os_path.getmtime(XML_CONFIG)
		if mtime == self.configMtime:
			print "[AutoTimer] No changes in configuration, won't parse"
			return

		# Save current mtime
		self.configMtime = mtime

		# Parse Config
		dom = minidom_parse(XML_CONFIG)
		
		# Empty out timers and reset Ids
		del self.timers[:]
		self.uniqueTimerId = 0

		# Get Config Element
		for configuration in dom.getElementsByTagName("autotimer"):
			# Parse old configuration files
			if configuration.getAttribute("version") != CURRENT_CONFIG_VERSION:
				from OldConfigurationParser import parseConfig
				parseConfig(configuration, self.timers, configuration.getAttribute("version"), self.uniqueTimerId)
				if not self.uniqueTimerId:
					self.uniqueTimerId = len(self.timers)
				continue
			# Iterate Timers
			for timer in configuration.getElementsByTagName("timer"):
				# Timers are saved as tuple (name, allowedtime (from, to) or None, list of services or None, timeoffset in m (before, after) or None, afterevent)

				# Increment uniqueTimerId
				self.uniqueTimerId += 1

				# Read out match
				match = timer.getAttribute("match").encode("UTF-8")
				if not match:
					print '[AutoTimer] Erroneous config is missing attribute "match", skipping entry'
					continue

				# Read out name
				name = timer.getAttribute("name").encode("UTF-8")
				if not name:
					print '[AutoTimer] Timer is missing attribute "name", defaulting to match'
					name = match

				# Read out enabled
				enabled = timer.getAttribute("enabled") or "yes"
				if enabled == "no":
					enabled = False
				elif enabled == "yes":
					enabled = True
				else:
					print '[AutoTimer] Erroneous config contains invalid value for "enabled":', enabled,', disabling'
					enabled = False

				# Read out timespan
				start = timer.getAttribute("from")
				end = timer.getAttribute("to")
				if start and end:
					start = [int(x) for x in start.split(':')]
					end = [int(x) for x in end.split(':')]
					timetuple = (start, end)
				else:
					timetuple = None

				# Read out max length
				maxlen = timer.getAttribute("maxduration") or None
				if maxlen:
					maxlen = int(maxlen)*60

				# Read out recording path (needs my Location-select patch)
				destination = timer.getAttribute("destination").encode("UTF-8") or None

				# Read out offset
				offset = timer.getAttribute("offset") or None
				if offset:
					offset = offset.split(",")
					if len(offset) == 1:
						before = after = int(offset[0] or 0) * 60
					else:
						before = int(offset[0] or 0) * 60
						after = int(offset[1] or 0) * 60
					offset = (before, after)

				# Read out counter
				counter = int(timer.getAttribute("counter") or '0')
				counterLeft = timer.getAttribute("left") or counter
				counterLimit = timer.getAttribute("lastActivation")
				counterFormat = timer.getAttribute("counterFormat")
				lastBegin = timer.getAttribute("lastBegin") or 0

				# Read out justplay
				justplay = int(timer.getAttribute("justplay") or '0')

				# Read out avoidDuplicateDescription
				avoidDuplicateDescription = bool(timer.getAttribute("avoidDuplicateDescription") or False)

				# Read out allowed services
				servicelist = []					
				for service in timer.getElementsByTagName("serviceref"):
					value = getValue(service, None, False)
					if value:
						# strip all after last :
						pos = value.rfind(':')
						if pos != -1:
							value = value[:pos+1]

						servicelist.append(value)

				# Read out afterevent
				idx = {"none": AFTEREVENT.NONE, "standby": AFTEREVENT.STANDBY, "shutdown": AFTEREVENT.DEEPSTANDBY, "deepstandby": AFTEREVENT.DEEPSTANDBY}
				afterevent = []
				for element in timer.getElementsByTagName("afterevent"):
					value = getValue(element, None, False)

					try:
						value = idx[value]
						start = element.getAttribute("from")
						end = element.getAttribute("to")
						if start and end:
							start = [int(x) for x in start.split(':')]
							end = [int(x) for x in end.split(':')]
							afterevent.append((value, (start, end)))
						else:
							afterevent.append((value, None))
					except KeyError, ke:
						print '[AutoTimer] Erroneous config contains invalid value for "afterevent":', afterevent,', ignoring definition'
						continue

				# Read out exclude
				idx = {"title": 0, "shortdescription": 1, "description": 2, "dayofweek": 3}
				excludes = ([], [], [], []) 
				for exclude in timer.getElementsByTagName("exclude"):
					where = exclude.getAttribute("where")
					value = getValue(exclude, None, False)
					if not (value and where):
						continue

					try:
						excludes[idx[where]].append(value.encode("UTF-8"))
					except KeyError, ke:
						pass

				# Read out includes (use same idx)
				includes = ([], [], [], []) 
				for include in timer.getElementsByTagName("include"):
					where = include.getAttribute("where")
					value = getValue(include, None, False)
					if not (value and where):
						continue

					try:
						includes[idx[where]].append(value.encode("UTF-8"))
					except KeyError, ke:
						pass

				# Finally append tuple
				self.timers.append(AutoTimerComponent(
						self.uniqueTimerId,
						name,
						match,
						enabled,
						timespan = timetuple,
						services = servicelist,
						offset = offset,
						afterevent = afterevent,
						exclude = excludes,
						include = includes,
						maxduration = maxlen,
						destination = destination,
						matchCount = counter,
						matchLeft = counterLeft,
						matchLimit = counterLimit,
						matchFormatString = counterFormat,
						lastBegin = int(lastBegin),
						justplay = justplay,
						avoidDuplicateDescription = avoidDuplicateDescription
				))

	def getTimerList(self):
		return self.timers

	def getEnabledTimerList(self):
		return [x for x in self.timers if x.enabled]

	def getTupleTimerList(self):
		return [(x,) for x in self.timers]

	def getUniqueId(self):
		self.uniqueTimerId += 1
		return self.uniqueTimerId

	def add(self, timer):
		self.timers.append(timer)

	def set(self, timer):
		idx = 0
		for stimer in self.timers:
			if stimer == timer:
				self.timers[idx] = timer
				return
			idx += 1
		self.timers.append(timer)

	def remove(self, uniqueId):
		idx = 0
		for timer in self.timers:
			if timer.id == uniqueId:
				self.timers.pop(idx)
				return
			idx += 1

	def writeXml(self):
		# Generate List in RAM
		list = ['<?xml version="1.0" ?>\n<autotimer version="', CURRENT_CONFIG_VERSION, '">\n\n']

		# Iterate timers
		for timer in self.timers:
			# Common attributes (match, enabled)
			list.extend([' <timer name="', timer.name, '" match="', timer.match, '" enabled="', timer.getEnabled(), '"'])

			# Timespan
			if timer.hasTimespan():
				list.extend([' from="', timer.getTimespanBegin(), '" to="', timer.getTimespanEnd(), '"'])

			# Duration
			if timer.hasDuration():
				list.extend([' maxduration="', str(timer.getDuration()), '"'])

			# Destination (needs my Location-select patch)
			if timer.hasDestination():
				list.extend([' destination="', str(timer.destination), '"'])

			# Offset
			if timer.hasOffset():
				if timer.isOffsetEqual():
					list.extend([' offset="', str(timer.getOffsetBegin()), '"'])
				else:
					list.extend([' offset="', str(timer.getOffsetBegin()), ',', str(timer.getOffsetEnd()), '"'])

			# Counter
			if timer.hasCounter():
				list.extend([' lastBegin="', str(timer.getLastBegin()), '" counter="', str(timer.getCounter()), '" left="', str(timer.getCounterLeft()) ,'"'])
				if timer.hasCounterFormatString():
					list.extend([' lastActivation="', str(timer.getCounterLimit()), '"'])
					list.extend([' counterFormat="', str(timer.getCounterFormatString()), '"'])

			# Duplicate Description
			if timer.getAvoidDuplicateDescription():
				list.append(' avoidDuplicateDescription="1" ')

			# Only display justplay if true
			if timer.justplay:
				list.extend([' justplay="', str(timer.getJustplay()), '"'])

			# Close still opened timer tag
			list.append('>\n')

			# Services
			for serviceref in timer.getServices():
				list.extend(['  <serviceref>', serviceref, '</serviceref>'])
				ref = ServiceReference(str(serviceref))
				list.extend([' <!-- ', ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', ''), ' -->\n'])

			# AfterEvent
			if timer.hasAfterEvent():
				idx = {AFTEREVENT.NONE: "none", AFTEREVENT.STANDBY: "standby", AFTEREVENT.DEEPSTANDBY: "shutdown"}
				for afterevent in timer.getCompleteAfterEvent():
					action, timespan = afterevent
					list.append('  <afterevent')
					if timespan[0] is not None:
						list.append(' from="%02d:%02d" to="%02d:%02d"' % (timespan[0][0], timespan[0][1], timespan[1][0], timespan[1][1]))
					list.extend(['>', idx[action], '</afterevent>\n'])

			# Excludes
			for title in timer.getExcludedTitle():
				list.extend(['  <exclude where="title">', title, '</exclude>\n'])
			for short in timer.getExcludedShort():
				list.extend(['  <exclude where="shortdescription">', short, '</exclude>\n'])
			for desc in timer.getExcludedDescription():
				list.extend(['  <exclude where="description">', desc, '</exclude>\n'])
			for day in timer.getExcludedDays():
				list.extend(['  <exclude where="dayofweek">', day, '</exclude>\n'])

			# Includes
			for title in timer.getIncludedTitle():
				list.extend(['  <include where="title">', title, '</include>\n'])
			for short in timer.getIncludedShort():
				list.extend(['  <include where="shortdescription">', short, '</include>\n'])
			for desc in timer.getIncludedDescription():
				list.extend(['  <include where="description">', desc, '</include>\n'])
			for day in timer.getIncludedDays():
				list.extend(['  <include where="dayofweek">', day, '</include>\n'])

			# End of Timer
			list.append(' </timer>\n\n')

		# End of Configuration
		list.append('</autotimer>\n')

		# Try Saving to Flash
		file = None
		try:
			file = open(XML_CONFIG, 'w')
			file.writelines(list)

			# FIXME: This should actually be placed inside a finally-block but python 2.4 does not support this - waiting for some images to upgrade
			file.close()
		except Exception, e:
			print "[AutoTimer] Error Saving Timer List:", e

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
		recorddict = {}
		for timer in NavigationInstance.instance.RecordTimer.timer_list:
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
				if timer.checkServices(serviceref) or timer.checkDuration(duration) or timer.checkTimespan(timestamp) or timer.checkFilter(name, description, evt.getExtendedDescription(), str(timestamp[6])):
					continue

				# Apply E2 Offset
  				begin -= config.recording.margin_before.value * 60
				end += config.recording.margin_after.value * 60
 
				# Apply custom Offset
				begin, end = timer.applyOffset(begin, end)

				total += 1

				# Append to timerlist and abort if simulating
				timers.append((name, begin, end, serviceref, timer.name))
				if simulateOnly:
					continue

				# Initialize
				newEntry = None

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

							try:
								if newEntry.isAutoTimer:
									print "[AutoTimer] Modifying existing AutoTimer!"
							except AttributeError, ae:
								if config.plugins.autotimer.refresh.value != "all":
									raise AutoTimerIgnoreTimerException("Won't modify existing timer because it's no timer set by us")
								print "[AutoTimer] Warning, we're messing with a timer which might not have been set by us"

							func = NavigationInstance.instance.RecordTimer.timeChanged
							modified += 1

							# Modify values saved in timer
							newEntry.name = name
							newEntry.description = description
							newEntry.begin = int(begin)
							newEntry.end = int(end)
							newEntry.service_ref = ServiceReference(serviceref)

							break
						elif timer.getAvoidDuplicateDescription() and rtimer.description == description:
							raise AutoTimerIgnoreTimerException("We found a timer with same description, skipping event")

				except AutoTimerIgnoreTimerException, etite:
					print etite
					continue

				# Event not yet in Timers
				if newEntry is None:
					if timer.checkCounter(timestamp):
						continue

					new += 1

					print "[AutoTimer] Adding an event."
					newEntry = RecordTimerEntry(ServiceReference(serviceref), begin, end, name, description, eit)
					func = NavigationInstance.instance.RecordTimer.record

					# Mark this entry as AutoTimer (only AutoTimers will have this Attribute set)
					newEntry.isAutoTimer = True

				# Apply afterEvent
 				if timer.hasAfterEvent():
 					afterEvent = timer.getAfterEventTimespan(localtime(end))
 					if afterEvent is None:
 						afterEvent = timer.getAfterEvent()
 					if afterEvent is not None:
 						newEntry.afterEvent = afterEvent

				# Set custom destination directory (needs my Location-select patch)
				if timer.hasDestination():
					# TODO: add warning when patch not installed?
					newEntry.dirname = timer.destination
 
 				# Make this timer a zap-timer if wanted
 				newEntry.justplay = timer.justplay
 
 				# Do a sanity check, although it does not do much right now
 				timersanitycheck = TimerSanityCheck(NavigationInstance.instance.RecordTimer.timer_list, newEntry)
 				if not timersanitycheck.check():
 					print "[Autotimer] Sanity check failed"
 				else:
 					print "[Autotimer] Sanity check passed"

 				# Either add to List or change time
 				func(newEntry)

		return (total, new, modified, timers)