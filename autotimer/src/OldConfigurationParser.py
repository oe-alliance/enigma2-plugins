from AutoTimerComponent import AutoTimerComponent
from AutoTimer import getValue
from RecordTimer import AFTEREVENT

def parseConfig(configuration, list, version = None, uniqueTimerId = 0):
	print "[AutoTimer] Trying to parse old config"

	# Iterate Timers
	for timer in configuration.getElementsByTagName("timer"):
		# Increment uniqueTimerId
		uniqueTimerId += 1

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

def parseConfig_v321(configuration, list, uniqueTimerId = 0):
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
