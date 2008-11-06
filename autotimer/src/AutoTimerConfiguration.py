# -*- coding: UTF-8 -*-
# for localized messages
from . import _

from AutoTimerComponent import AutoTimerComponent
from RecordTimer import AFTEREVENT
from Tools.XMLTools import stringToXML
from ServiceReference import ServiceReference

CURRENT_CONFIG_VERSION = "5"

def getValue(definitions, default):
	# Initialize Output
	ret = ""

	# How many definitions are present
	if isinstance(definitions, list):
		Len = len(definitions)
		if Len > 0:
			childNodes = definitions[Len-1].text
		else:
			childNodes = ""
	else:
		ret = definitions.text

	# Return stripped output or (if empty) default
	return ret.strip() or default

def parseConfig(configuration, list, version = None, uniqueTimerId = 0, defaultTimer = None):
	if version != CURRENT_CONFIG_VERSION:
		parseConfigOld(configuration, list, uniqueTimerId)
		return

	if defaultTimer is not None:
		# Read in defaults for a new timer
		for defaults in configuration.findall("defaults"):
			parseEntry(defaults, defaultTimer, True)

	for timer in configuration.findall("timer"):
		uniqueTimerId += 1
		baseTimer = AutoTimerComponent(
			uniqueTimerId,
			'',
			'',
			True
		)

		if parseEntry(timer, baseTimer):
			list.append(baseTimer)

def parseEntry(element, baseTimer, defaults = False):
	if not defaults:
		# Read out match
		baseTimer.match = element.get("match", "").encode("UTF-8")
		if not baseTimer.match:
			print '[AutoTimer] Erroneous config is missing attribute "match", skipping entry'
			return False

		# Read out name
		baseTimer.name = element.get("name", "").encode("UTF-8")
		if not baseTimer.name:
			print '[AutoTimer] Timer is missing attribute "name", defaulting to match'
			baseTimer.name = baseTimer.match

		# Read out enabled
		enabled = element.get("enabled", "yes")
		if enabled == "no":
			baseTimer.enabled = False
		elif enabled == "yes":
			baseTimer.enabled = True
		else:
			print '[AutoTimer] Erroneous config contains invalid value for "enabled":', enabled,', disabling'
			baseTimer.enabled = False

	# Read out timespan
	start = element.get("from")
	end = element.get("to")
	if start and end:
		start = [int(x) for x in start.split(':')]
		end = [int(x) for x in end.split(':')]
		baseTimer.timespan = (start, end)

	# Read out max length
	maxduration = element.get("maxduration")
	if maxduration:
		baseTimer.maxduration = int(maxduration)*60

	# Read out recording path
	baseTimer.destination = element.get("location", "").encode("UTF-8") or None

	# Read out offset
	offset = element.get("offset")
	if offset:
		offset = offset.split(",")
		if len(offset) == 1:
			before = after = int(offset[0] or 0) * 60
		else:
			before = int(offset[0] or 0) * 60
			after = int(offset[1] or 0) * 60
		baseTimer.offset = (before, after)

	# Read out counter
	baseTimer.matchCount = int(element.get("counter", 0))
	baseTimer.matchFormatString = element.get("counterFormat", "")
	if not defaults:
		baseTimer.counterLimit = element.get("lastActivation", "")
		baseTimer.counterFormat = element.get("counterFormat", "")
		baseTimer.lastBegin = int(element.get("lastBegin", 0))

	# Read out justplay
	justplay = int(element.get("justplay", 0))

	# Read out avoidDuplicateDescription
	baseTimer.avoidDuplicateDescription = int(element.get("avoidDuplicateDescription", 0))

	# Read out allowed services
	servicelist = baseTimer.services	
	for service in element.findall("serviceref"):
		value = service.text
		if value:
			# strip all after last :
			pos = value.rfind(':')
			if pos != -1:
				value = value[:pos+1]

			servicelist.append(value)
	baseTimer.services = servicelist

	# Read out allowed bouquets
	bouquets = baseTimer.bouquets
	for bouquet in element.findall("bouquet"):
		value = bouquet.text
		if value:
			bouquets.append(value)
	baseTimer.bouquets = bouquets

	# Read out afterevent
	idx = {"none": AFTEREVENT.NONE, "standby": AFTEREVENT.STANDBY, "shutdown": AFTEREVENT.DEEPSTANDBY, "deepstandby": AFTEREVENT.DEEPSTANDBY}
	afterevent = baseTimer.afterevent
	for element in element.findall("afterevent"):
		value = element.text

		try:
			value = idx[value]
		except KeyError, ke:
			print '[AutoTimer] Erroneous config contains invalid value for "afterevent":', afterevent,', ignoring definition'
			continue

		start = element.get("from")
		end = element.get("to")
		if start and end:
			start = [int(x) for x in start.split(':')]
			end = [int(x) for x in end.split(':')]
			afterevent.append((value, (start, end)))
		else:
			afterevent.append((value, None))
	baseTimer.afterevent = afterevent

	# Read out exclude
	idx = {"title": 0, "shortdescription": 1, "description": 2, "dayofweek": 3}
	excludes = (baseTimer.getExcludedTitle(), baseTimer.getExcludedShort(), baseTimer.getExcludedDescription(), baseTimer.getExcludedDays()) 
	for exclude in element.findall("exclude"):
		where = exclude.get("where")
		value = exclude.text
		if not (value and where):
			continue

		try:
			excludes[idx[where]].append(value.encode("UTF-8"))
		except KeyError, ke:
			pass
	baseTimer.exclude = excludes

	# Read out includes (use same idx)
	includes = (baseTimer.getIncludedTitle(), baseTimer.getIncludedShort(), baseTimer.getIncludedDescription(), baseTimer.getIncludedDays())
	for include in element.findall("include"):
		where = include.get("where")
		value = include.text
		if not (value and where):
			continue

		try:
			includes[idx[where]].append(value.encode("UTF-8"))
		except KeyError, ke:
			pass
	baseTimer.include = includes

	# Read out recording tags (needs my enhanced tag support patch)
	tags = baseTimer.tags
	for tag in element.findall("tag"):
		value = tag.text
		if not value:
			continue

		tags.append(value.encode("UTF-8"))
	baseTimer.tags = tags
	
	return True

def parseConfigOld(configuration, list, uniqueTimerId = 0):
	print "[AutoTimer] Trying to parse old config"

	# Iterate Timers
	for timer in configuration.findall("timer"):
		# Increment uniqueTimerId
		uniqueTimerId += 1

		# Get name (V2+)
		name = timer.get("name")
		if name:
			name = name.encode("UTF-8")
		# Get name (= match) (V1)
		else:
			# Read out name
			name = getValue(timer.findall("name"), "").encode("UTF-8")

		if not name:
			print '[AutoTimer] Erroneous config is missing attribute "name", skipping entry'
			continue

		# Read out match (V3+)
		match = timer.get("match")
		if match:
			# Read out match
			match = match.encode("UTF-8")
			if not match:
				print '[AutoTimer] Erroneous config contains empty attribute "match", skipping entry'
				continue
		# V2-
		else:
			# Setting match to name
			match = name


		# See if Timer is ensabled (V2+)
		enabled = timer.get("enabled")
		if enabled:
			if enabled == "no":
				enabled = False
			elif enabled == "yes":
				enabled = True
			else:
				print '[AutoTimer] Erroneous config contains invalid value for "enabled":', enabled,', skipping entry'
				enabled = False
		# V1
		else:
			elements = timer.findall("enabled")
			if len(elements):
				if getValue(elements, "yes") == "no":
					enabled = False
				else:
					enabled = True
			else:
				enabled = True

		# Read out timespan (V4+; Falling back on missing definition should be OK)
		start = timer.get("from")
		end = timer.get("to")
		if start and end:
			start = [int(x) for x in start.split(':')]
			end = [int(x) for x in end.split(':')]
			timetuple = (start, end)
		# V3-
		else:
			elements = timer.findall("timespan")
			Len = len(elements)
			if Len:
				# Read out last definition
				start = elements[Len-1].get("from")
				end = elements[Len-1].get("to")
				if start and end:
					start = [int(x) for x in start.split(':')]
					end = [int(x) for x in end.split(':')]
					timetuple = (start, end)
				else:
					print '[AutoTimer] Erroneous config contains invalid definition of "timespan", ignoring definition'
					timetuple = None
			else:
				timetuple = None

		# Read out allowed services (V*)
		elements = timer.findall("serviceref")
		if len(elements):
			servicelist = []
			for service in elements:
				value = service.text
				if value:
					# strip all after last :
					pos = value.rfind(':')
					if pos != -1:
						value = value[:pos+1]

					servicelist.append(value)
		else:
			servicelist = None

		# Read out allowed bouquets (V* though officially supported since V4)
		bouquets = []
		for bouquet in timer.findall("bouquet"):
			value = bouquet.text
			if value:
				bouquets.append(value)

		# Read out offset (V4+)
		offset = timer.get("offset")
		if offset:
			offset = offset.split(",")
			if len(offset) == 1:
				before = after = int(offset[0] or 0) * 60
			else:
				before = int(offset[0] or 0) * 60
				after = int(offset[1] or 0) * 60
			offset = (before, after)
		# V3-
		else:
			elements = timer.findall("offset")
			Len = len(elements)
			if Len:
				value = elements[Len-1].get("both")
				if value == '':
					before = int(elements[Len-1].get("before", 0)) * 60
					after = int(elements[Len-1].get("after", 0)) * 60
				else:
					before = after = int(value) * 60
				offset = (before, after)
			else:
				offset = None

		# Read out counter
		counter = int(timer.get("counter", '0'))
		counterLeft = int(timer.get("left", counter))
		counterLimit = timer.get("lastActivation")
		counterFormat = timer.get("counterFormat", "")
		lastBegin = int(timer.get("lastBegin", 0))

		# Read out justplay
		justplay = int(timer.get("justplay", '0'))

		# Read out avoidDuplicateDescription
		avoidDuplicateDescription = int(timer.get("avoidDuplicateDescription", 0))

		# Read out afterevent (compatible to V* though behaviour for V3- is different as V4+ allows multiple afterevents while the last definication was chosen before)
		idx = {"none": AFTEREVENT.NONE, "standby": AFTEREVENT.STANDBY, "shutdown": AFTEREVENT.DEEPSTANDBY, "deepstandby": AFTEREVENT.DEEPSTANDBY}
		afterevent = []
		for element in timer.findall("afterevent"):
			value = element.text

			try:
				value = idx[value]
			except KeyError, ke:
				print '[AutoTimer] Erroneous config contains invalid value for "afterevent":', afterevent,', ignoring definition'
				continue

			start = element.get("from")
			end = element.get("to")
			if start and end:
				start = [int(x) for x in start.split(':')]
				end = [int(x) for x in end.split(':')]
				afterevent.append((value, (start, end)))
			else:
				afterevent.append((value, None))

		# Read out exclude (V*)
		idx = {"title": 0, "shortdescription": 1, "description": 2, "dayofweek": 3}
		excludes = ([], [], [], []) 
		for exclude in timer.findall("exclude"):
			where = exclude.get("where")
			value = exclude.text
			if not (value and where):
				continue

			try:
				excludes[idx[where]].append(value.encode("UTF-8"))
			except KeyError, ke:
				pass

		# Read out includes (use same idx) (V4+ feature, should not harm V3-)
		includes = ([], [], [], []) 
		for include in timer.findall("include"):
			where = include.get("where")
			value = include.text
			if not (value and where):
				continue

			try:
				includes[idx[where]].append(value.encode("UTF-8"))
			except KeyError, ke:
				pass

		# Read out max length (V4+)
		maxlen = timer.get("maxduration")
		if maxlen:
			maxlen = int(maxlen)*60
		# V3-
		else:
			elements = timer.findall("maxduration")
			if len(elements):
				maxlen = getValue(elements, None)
				if maxlen is not None:
					maxlen = int(maxlen)*60
			else:
				maxlen = None

		# Read out recording path
		destination = timer.get("destination", "").encode("UTF-8") or None

		# Read out recording tags (needs my enhanced tag support patch)
		tags = []
		for tag in timer.findall("tag"):
			value = tag.text
			if not value:
				continue

			tags.append(value.encode("UTF-8"))

		# Finally append timer
		list.append(AutoTimerComponent(
				uniqueTimerId,
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
				lastBegin = lastBegin,
				justplay = justplay,
				avoidDuplicateDescription = avoidDuplicateDescription,
				bouquets = bouquets,
				tags = tags
		))

def writeConfig(filename, defaultTimer, timers):
	# Generate List in RAM
	list = ['<?xml version="1.0" ?>\n<autotimer version="', CURRENT_CONFIG_VERSION, '">\n\n']

	# XXX: we might want to make sure that we don't save empty default here
	list.extend([' <defaults'])

	# Timespan
	if defaultTimer.hasTimespan():
		list.extend([' from="', defaultTimer.getTimespanBegin(), '" to="', defaultTimer.getTimespanEnd(), '"'])

	# Duration
	if defaultTimer.hasDuration():
		list.extend([' maxduration="', str(defaultTimer.getDuration()), '"'])

	# Destination
	if defaultTimer.hasDestination():
		list.extend([' location="', stringToXML(defaultTimer.destination), '"'])

	# Offset
	if defaultTimer.hasOffset():
		if defaultTimer.isOffsetEqual():
			list.extend([' offset="', str(defaultTimer.getOffsetBegin()), '"'])
		else:
			list.extend([' offset="', str(defaultTimer.getOffsetBegin()), ',', str(defaultTimer.getOffsetEnd()), '"'])

	# Counter
	if defaultTimer.hasCounter():
		list.extend([' counter="', str(defaultTimer.getCounter()), '"'])
		if defaultTimer.hasCounterFormatString():
			list.extend([' counterFormat="', str(defaultTimer.getCounterFormatString()), '"'])

	# Duplicate Description
	if defaultTimer.getAvoidDuplicateDescription():
		list.append(' avoidDuplicateDescription="1" ')

	# Only display justplay if true
	if defaultTimer.justplay:
		list.extend([' justplay="', str(defaultTimer.getJustplay()), '"'])

	# Close still opened defaults tag
	list.append('>\n')

	# Services
	for serviceref in defaultTimer.getServices():
		list.extend(['  <serviceref>', serviceref, '</serviceref>'])
		ref = ServiceReference(str(serviceref))
		list.extend([' <!-- ', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), ' -->\n'])

	# Bouquets
	for bouquet in defaultTimer.getBouquets():
		list.extend(['  <bouquet>', str(bouquet), '</bouquet>'])
		ref = ServiceReference(str(bouquet))
		list.extend([' <!-- ', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), ' -->\n'])

	# AfterEvent
	if defaultTimer.hasAfterEvent():
		idx = {AFTEREVENT.NONE: "none", AFTEREVENT.STANDBY: "standby", AFTEREVENT.DEEPSTANDBY: "shutdown"}
		for afterevent in defaultTimer.getCompleteAfterEvent():
			action, timespan = afterevent
			list.append('  <afterevent')
			if timespan[0] is not None:
				list.append(' from="%02d:%02d" to="%02d:%02d"' % (timespan[0][0], timespan[0][1], timespan[1][0], timespan[1][1]))
			list.extend(['>', idx[action], '</afterevent>\n'])

	# Excludes
	for title in defaultTimer.getExcludedTitle():
		list.extend(['  <exclude where="title">', stringToXML(title), '</exclude>\n'])
	for short in defaultTimer.getExcludedShort():
		list.extend(['  <exclude where="shortdescription">', stringToXML(short), '</exclude>\n'])
	for desc in defaultTimer.getExcludedDescription():
		list.extend(['  <exclude where="description">', stringToXML(desc), '</exclude>\n'])
	for day in defaultTimer.getExcludedDays():
		list.extend(['  <exclude where="dayofweek">', stringToXML(day), '</exclude>\n'])

	# Includes
	for title in defaultTimer.getIncludedTitle():
		list.extend(['  <include where="title">', stringToXML(title), '</include>\n'])
	for short in defaultTimer.getIncludedShort():
		list.extend(['  <include where="shortdescription">', stringToXML(short), '</include>\n'])
	for desc in defaultTimer.getIncludedDescription():
		list.extend(['  <include where="description">', stringToXML(desc), '</include>\n'])
	for day in defaultTimer.getIncludedDays():
		list.extend(['  <include where="dayofweek">', stringToXML(day), '</include>\n'])

	# Tags
	for tag in defaultTimer.tags:
		list.extend(['  <tag>', stringToXML(tag), '</tag>\n'])

	# End of Timer
	list.append(' </defaults>\n\n')

	# Iterate timers
	for timer in timers:
		# Common attributes (match, enabled)
		list.extend([' <timer name="', stringToXML(timer.name), '" match="', stringToXML(timer.match), '" enabled="', timer.getEnabled(), '"'])

		# Timespan
		if timer.hasTimespan():
			list.extend([' from="', timer.getTimespanBegin(), '" to="', timer.getTimespanEnd(), '"'])

		# Duration
		if timer.hasDuration():
			list.extend([' maxduration="', str(timer.getDuration()), '"'])

		# Destination
		if timer.hasDestination():
			list.extend([' location="', stringToXML(timer.destination), '"'])

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
			list.extend([' avoidDuplicateDescription="', str(timer.getAvoidDuplicateDescription()), '"'])

		# Only display justplay if true
		if timer.justplay:
			list.extend([' justplay="', str(timer.getJustplay()), '"'])

		# Close still opened timer tag
		list.append('>\n')

		# Services
		for serviceref in timer.getServices():
			list.extend(['  <serviceref>', serviceref, '</serviceref>'])
			ref = ServiceReference(str(serviceref))
			list.extend([' <!-- ', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), ' -->\n'])

		# Bouquets
		for bouquet in timer.getBouquets():
			list.extend(['  <bouquet>', str(bouquet), '</bouquet>'])
			ref = ServiceReference(str(bouquet))
			list.extend([' <!-- ', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), ' -->\n'])

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
			list.extend(['  <exclude where="title">', stringToXML(title), '</exclude>\n'])
		for short in timer.getExcludedShort():
			list.extend(['  <exclude where="shortdescription">', stringToXML(short), '</exclude>\n'])
		for desc in timer.getExcludedDescription():
			list.extend(['  <exclude where="description">', stringToXML(desc), '</exclude>\n'])
		for day in timer.getExcludedDays():
			list.extend(['  <exclude where="dayofweek">', stringToXML(day), '</exclude>\n'])

		# Includes
		for title in timer.getIncludedTitle():
			list.extend(['  <include where="title">', stringToXML(title), '</include>\n'])
		for short in timer.getIncludedShort():
			list.extend(['  <include where="shortdescription">', stringToXML(short), '</include>\n'])
		for desc in timer.getIncludedDescription():
			list.extend(['  <include where="description">', stringToXML(desc), '</include>\n'])
		for day in timer.getIncludedDays():
			list.extend(['  <include where="dayofweek">', stringToXML(day), '</include>\n'])

		# Tags
		for tag in timer.tags:
			list.extend(['  <tag>', stringToXML(tag), '</tag>\n'])

		# End of Timer
		list.append(' </timer>\n\n')

	# End of Configuration
	list.append('</autotimer>\n')

	# Save to Flash
	file = open(filename, 'w')
	file.writelines(list)

	file.close()

