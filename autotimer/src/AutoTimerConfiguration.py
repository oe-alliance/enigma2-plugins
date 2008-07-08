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
	try:
		childNodes = definitions.childNodes
	except:
		Len = len(definitions)
		if Len > 0:
			childNodes = definitions[Len-1].childNodes
		else:
			childNodes = []

	# Iterate through nodes of last one
	for node in childNodes:
		# Append text if we have a text node
		if node.nodeType == node.TEXT_NODE:
			ret = ret + node.data

	# Return stripped output or (if empty) default
	return ret.strip() or default

def parseConfig(configuration, list, version = None, uniqueTimerId = 0, defaultTimer = None):
	if version != CURRENT_CONFIG_VERSION:
		parseConfigOld(configuration, list, uniqueTimerId)
		return

	if defaultTimer is not None:
		# Read in defaults for a new timer
		for defaults in configuration.getElementsByTagName("defaults"):
			parseEntry(defaults, defaultTimer, True)

	for timer in configuration.getElementsByTagName("timer"):
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
		baseTimer.match = element.getAttribute("match").encode("UTF-8")
		if not baseTimer.match:
			print '[AutoTimer] Erroneous config is missing attribute "match", skipping entry'
			return False

		# Read out name
		baseTimer.name = element.getAttribute("name").encode("UTF-8")
		if not baseTimer.name:
			print '[AutoTimer] Timer is missing attribute "name", defaulting to match'
			baseTimer.name = baseTimer.match

		# Read out enabled
		enabled = element.getAttribute("enabled") or "yes"
		if enabled == "no":
			baseTimer.enabled = False
		elif enabled == "yes":
			baseTimer.enabled = True
		else:
			print '[AutoTimer] Erroneous config contains invalid value for "enabled":', enabled,', disabling'
			baseTimer.enabled = False

	# Read out timespan
	start = element.getAttribute("from")
	end = element.getAttribute("to")
	if start and end:
		start = [int(x) for x in start.split(':')]
		end = [int(x) for x in end.split(':')]
		baseTimer.timespan = (start, end)

	# Read out max length
	maxduration = element.getAttribute("maxduration") or None
	if maxduration:
		baseTimer.maxduration = int(maxlen)*60

	# Read out recording path
	baseTimer.destination = element.getAttribute("location").encode("UTF-8") or None

	# Read out offset
	offset = element.getAttribute("offset") or None
	if offset:
		offset = offset.split(",")
		if len(offset) == 1:
			before = after = int(offset[0] or 0) * 60
		else:
			before = int(offset[0] or 0) * 60
			after = int(offset[1] or 0) * 60
		baseTimer.offset = (before, after)

	# Read out counter
	baseTimer.matchCount = int(element.getAttribute("counter") or '0')
	baseTimer.matchFormatString = element.getAttribute("counterFormat")
	if not defaults:
		baseTimer.counterLimit = element.getAttribute("lastActivation")
		baseTimer.counterFormat = element.getAttribute("counterFormat")
		baseTimer.lastBegin = int(element.getAttribute("lastBegin") or 0)

	# Read out justplay
	justplay = int(element.getAttribute("justplay") or '0')

	# Read out avoidDuplicateDescription
	baseTimer.avoidDuplicateDescription = bool(element.getAttribute("avoidDuplicateDescription") or False)

	# Read out allowed services
	servicelist = baseTimer.services	
	for service in element.getElementsByTagName("serviceref"):
		value = getValue(service, None)
		if value:
			# strip all after last :
			pos = value.rfind(':')
			if pos != -1:
				value = value[:pos+1]

			servicelist.append(value)
	baseTimer.services = servicelist

	# Read out allowed bouquets
	bouquets = baseTimer.bouquets
	for bouquet in element.getElementsByTagName("bouquet"):
		value = getValue(bouquet, None)
		if value:
			bouquets.append(value)
	baseTimer.bouquets = bouquets

	# Read out afterevent
	idx = {"none": AFTEREVENT.NONE, "standby": AFTEREVENT.STANDBY, "shutdown": AFTEREVENT.DEEPSTANDBY, "deepstandby": AFTEREVENT.DEEPSTANDBY}
	afterevent = baseTimer.afterevent
	for element in element.getElementsByTagName("afterevent"):
		value = getValue(element, None)

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
	baseTimer.afterevent = afterevent

	# Read out exclude
	idx = {"title": 0, "shortdescription": 1, "description": 2, "dayofweek": 3}
	excludes = (baseTimer.getExcludedTitle(), baseTimer.getExcludedShort(), baseTimer.getExcludedDescription(), baseTimer.getExcludedDays()) 
	for exclude in element.getElementsByTagName("exclude"):
		where = exclude.getAttribute("where")
		value = getValue(exclude, None)
		if not (value and where):
			continue

		try:
			excludes[idx[where]].append(value.encode("UTF-8"))
		except KeyError, ke:
			pass
	baseTimer.excludes = excludes

	# Read out includes (use same idx)
	includes = (baseTimer.getIncludedTitle(), baseTimer.getIncludedShort(), baseTimer.getIncludedDescription(), baseTimer.getIncludedDays())
	for include in element.getElementsByTagName("include"):
		where = include.getAttribute("where")
		value = getValue(include, None)
		if not (value and where):
			continue

		try:
			includes[idx[where]].append(value.encode("UTF-8"))
		except KeyError, ke:
			pass
	baseTimer.includes = includes

	# Read out recording tags (needs my enhanced tag support patch)
	tags = baseTimer.tags
	for tag in element.getElementsByTagName("tag"):
		value = getValue(tag, None)
		if not value:
			continue

		tags.append(value.encode("UTF-8"))
	baseTimer.tags = tags
	
	return True

def parseConfigOld(configuration, list, uniqueTimerId = 0):
	print "[AutoTimer] Trying to parse old config"

	# Iterate Timers
	for timer in configuration.getElementsByTagName("timer"):
		# Increment uniqueTimerId
		uniqueTimerId += 1

		# Get name (V2+)
		if timer.hasAttribute("name"):
			name = timer.getAttribute("name").encode("UTF-8")
		# Get name (= match) (V1)
		else:
			# Read out name
			name = getValue(timer.getElementsByTagName("name"), "").encode("UTF-8")

		if not name:
			print '[AutoTimer] Erroneous config is missing attribute "name", skipping entry'
			continue

		# Read out match (V3+)
		if timer.hasAttribute("match"):
			# Read out match
			match = timer.getAttribute("match").encode("UTF-8")
			if not match:
				print '[AutoTimer] Erroneous config contains empty attribute "match", skipping entry'
				continue
		# V2-
		else:
			# Setting name to match
			name = match


		# See if Timer is ensabled (V2+)
		if timer.hasAttribute("enabled"):
			enabled = timer.getAttribute("enabled") or "yes"
			if enabled == "no":
				enabled = False
			elif enabled == "yes":
				enabled = True
			else:
				print '[AutoTimer] Erroneous config contains invalid value for "enabled":', enabled,', skipping entry'
				enabled = False
		# V1
		else:
			elements = timer.getElementsByTagName("enabled")
			if len(elements):
				if getValue(elements, "yes") == "no":
					enabled = False
				else:
					enabled = True
			else:
				enabled = True
			

		# Read out timespan (V4+; Falling back on missing definition should be OK)
		if timer.hasAttribute("from") and timer.hasAttribute("to"):
			start = timer.getAttribute("from")
			end = timer.getAttribute("to")
			if start and end:
				start = [int(x) for x in start.split(':')]
				end = [int(x) for x in end.split(':')]
				timetuple = (start, end)
			else:
				timetuple = None
		# V3-
		else:
			elements = timer.getElementsByTagName("timespan")
			Len = len(elements)
			if Len:
				# Read out last definition
				start = elements[Len-1].getAttribute("from")
				end = elements[Len-1].getAttribute("to")
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
		elements = timer.getElementsByTagName("serviceref")
		if len(elements):
			servicelist = []
			for service in elements:
				value = getValue(service, None)
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
		for bouquet in timer.getElementsByTagName("bouquet"):
			value = getValue(bouquet, None)
			if value:
				bouquets.append(value)

		# Read out offset (V4+)
		if timer.hasAttribute("offset"):
			offset = timer.getAttribute("offset") or None
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
			elements = timer.getElementsByTagName("offset")
			Len = len(elements)
			if Len:
				value = elements[Len-1].getAttribute("both")
				if value == '':
					before = int(elements[Len-1].getAttribute("before") or 0) * 60
					after = int(elements[Len-1].getAttribute("after") or 0) * 60
				else:
					before = after = int(value) * 60
				offset = (before, after)
			else:
				offset = None

		# Read out counter
		counter = int(timer.getAttribute("counter") or '0')
		counterLeft = int(timer.getAttribute("left") or counter)
		counterLimit = timer.getAttribute("lastActivation")
		counterFormat = timer.getAttribute("counterFormat")
		lastBegin = int(timer.getAttribute("lastBegin") or 0)

		# Read out justplay
		justplay = int(timer.getAttribute("justplay") or '0')

		# Read out avoidDuplicateDescription
		avoidDuplicateDescription = bool(timer.getAttribute("avoidDuplicateDescription") or False)

		# Read out afterevent (compatible to V* though behaviour for V3- is different as V4+ allows multiple afterevents while the last definication was chosen before)
		idx = {"none": AFTEREVENT.NONE, "standby": AFTEREVENT.STANDBY, "shutdown": AFTEREVENT.DEEPSTANDBY, "deepstandby": AFTEREVENT.DEEPSTANDBY}
		afterevent = []
		for element in timer.getElementsByTagName("afterevent"):
			value = getValue(element, None)

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

		# Read out exclude (V*)
		idx = {"title": 0, "shortdescription": 1, "description": 2, "dayofweek": 3}
		excludes = ([], [], [], []) 
		for exclude in timer.getElementsByTagName("exclude"):
			where = exclude.getAttribute("where")
			value = getValue(exclude, None)
			if not (value and where):
				continue

			try:
				excludes[idx[where]].append(value.encode("UTF-8"))
			except KeyError, ke:
				pass

		# Read out includes (use same idx) (V4+ feature, should not harm V3-)
		includes = ([], [], [], []) 
		for include in timer.getElementsByTagName("include"):
			where = include.getAttribute("where")
			value = getValue(include, None)
			if not (value and where):
				continue

			try:
				includes[idx[where]].append(value.encode("UTF-8"))
			except KeyError, ke:
				pass

		# Read out max length (V4+)
		if timer.hasAttribute("maxduration"):
			maxlen = timer.getAttribute("maxduration") or None
			if maxlen:
				maxlen = int(maxlen)*60
		# V3-
		else:
			elements = timer.getElementsByTagName("maxduration")
			if len(elements):
				maxlen = getValue(elements, None)
				if maxlen is not None:
					maxlen = int(maxlen)*60
			else:
				maxlen = None

		# Read out recording path
		destination = timer.getAttribute("destination").encode("UTF-8") or None

		# Read out recording tags (needs my enhanced tag support patch)
		tags = []
		for tag in timer.getElementsByTagName("tag"):
			value = getValue(tag, None)
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
