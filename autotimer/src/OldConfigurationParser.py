from AutoTimerComponent import AutoTimerComponent
from AutoTimer import getValue
from RecordTimer import AFTEREVENT

def parseConfig(configuration, list, version = None, uniqueTimerId = 0):
	if version == "3":
		print "[AutoTimer] Trying to parse config version 3"
		parseConfig_v3(configuration, list, uniqueTimerId)
	elif version == "2":
		print "[AutoTimer] Trying to parse config version 2"
		parseConfig_v2(configuration, list, uniqueTimerId)
	else:
		print "[AutoTimer] Trying to parse unversioned config file"
		parseConfig_v1(configuration, list, uniqueTimerId)

def parseConfig_v3(configuration, list, uniqueTimerId = 0):
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

		# Guess allowedtime
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

		# Read out allowed services
		servicelist = []			
		for service in timer.getElementsByTagName("serviceref"):
			value = getValue(service, None)
			if value:
				# strip all after last :
				pos = value.rfind(':')
				if pos != -1:
					value = value[:pos+1]

				servicelist.append(value)

		# Read out offset
		elements = timer.getElementsByTagName("offset")
		Len = len(elements)
		if Len:
			value = elements[Len-1].getAttribute("both")
			if value:
				before = after = int(value) * 60
			else:
				before = int(elements[Len-1].getAttribute("before") or 0) * 60
				after = int(elements[Len-1].getAttribute("after") or 0) * 60
			offset = (before, after)
		else:
			offset = None

		# Read out afterevent
		elements = timer.getElementsByTagName("afterevent")
		Len = len(elements)
		if Len:
			idx = {"none": AFTEREVENT.NONE, "standby": AFTEREVENT.STANDBY, "shutdown": AFTEREVENT.DEEPSTANDBY, "deepstandby": AFTEREVENT.DEEPSTANDBY}
			value = getValue(elements[Len-1], None)

			try:
				value = idx[value]
				start = elements[Len-1].getAttribute("from")
				end = elements[Len-1].getAttribute("to")
				if start and end:
					start = [int(x) for x in start.split(':')]
					end = [int(x) for x in end.split(':')]
					afterevent = [(value, (start, end))]
				else:
					afterevent = [(value, None)]
			except KeyError, ke:
				print '[AutoTimer] Erroneous config contains invalid value for "afterevent":', afterevent,', ignoring definition'
				afterevent = []
		else:
			afterevent = []

		# Read out exclude
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

		# Read out max length
		# TODO: this item is unique, shouldn't it be an attribute then?
		maxlen = getValue(timer.getElementsByTagName("maxduration"), None)
		if maxlen is not None:
			maxlen = int(maxlen)*60
		else:
			maxlen = None

		# Finally append tuple
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
			maxduration = maxlen
		))
		

def parseConfig_v2(configuration, list, uniqueTimerId = 0):
	# Iterate Timers
	for timer in configuration.getElementsByTagName("timer"):
		# Increment uniqueTimerId
		uniqueTimerId += 1

		# Read out match/name
		match = timer.getAttribute("name").encode("UTF-8")
		if not match:
			print '[AutoTimer] Erroneous config is missing attribute "name", skipping entry'
			continue

		# Setting name to match
		name = match

		enabled = timer.getAttribute("enabled") or "yes"
		if enabled == "no":
			enabled = False
		elif enabled == "yes":
			enabled = True
		else:
			print '[AutoTimer] Erroneous config contains invalid value for "enabled":', enabled,', disabling entry'
			enabled = False

		# Guess allowedtime
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

		# Read out allowed services
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

		# Read out offset
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

		# Read out afterevent
		elements = timer.getElementsByTagName("afterevent")
		Len = len(elements)
		if Len:
			idx = {"none": AFTEREVENT.NONE, "standby": AFTEREVENT.STANDBY, "shutdown": AFTEREVENT.DEEPSTANDBY, "deepstandby": AFTEREVENT.DEEPSTANDBY}
			value = getValue(elements[Len-1], None)
			try:
				value = idx[value]
				start = elements[Len-1].getAttribute("from")
				end = elements[Len-1].getAttribute("to")
				if start and end:
					start = [int(x) for x in start.split(':')]
					end = [int(x) for x in end.split(':')]
					afterevent = [(value, (start, end))]
				else:
					afterevent = [(value, None)]
			except KeyError, ke:
				print '[AutoTimer] Erroneous config contains invalid value for "afterevent":', afterevent,', ignoring definition'
				afterevent = []
		else:
			afterevent = []

		# Read out exclude
		elements = timer.getElementsByTagName("exclude")
		if len(elements):
			excludes = ([], [], [], [])
			idx = {"title": 0, "shortdescription": 1, "description": 2, "dayofweek": 3}
			for exclude in elements:
				where = exclude.getAttribute("where")
				value = getValue(exclude, None)
				if not (value and where):
					continue

				try:
					excludes[idx[where]].append(value.encode("UTF-8"))
				except KeyError, ke:
					pass
		else:
			excludes = None

		# Read out max length
		elements = timer.getElementsByTagName("maxduration")
		if len(elements):
			maxlen = getValue(elements, None)
			if maxlen is not None:
				maxlen = int(maxlen)*60
		else:
			maxlen = None

		# Finally append tuple
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
			maxduration = maxlen
		))

def parseConfig_v1(configuration, list, uniqueTimerId = 0):
	# Iterate Timers
	for timer in configuration.getElementsByTagName("timer"):
		# Timers are saved as tuple (name, allowedtime (from, to) or None, list of services or None, timeoffset in m (before, after) or None, afterevent)

		# Increment uniqueTimerId
		uniqueTimerId += 1

		# Read out name
		name = getValue(timer.getElementsByTagName("name"), None)
		if name is None:
			print "[AutoTimer] Erroneous config, skipping entry"
			continue

		# Encode name
		name = name.encode('UTF-8')

		# Setting match to name
		match = name

		# Guess allowedtime
		elements = timer.getElementsByTagName("timespan")
		if len(elements):
			# We only support 1 Timespan so far
			start = getValue(elements[0].getElementsByTagName("from"), None)
			end = getValue(elements[0].getElementsByTagName("to"), None)
			if start and end:
				start = [int(x) for x in start.split(':')]
				end = [int(x) for x in end.split(':')]
				timetuple = (start, end)
			else:
				timetuple = None
		else:
			timetuple = None

		# Read out allowed services
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

		# Read out offset
		elements = timer.getElementsByTagName("offset")
		if len(elements):
			value = getValue(elements, None)
			if value is None:
				before = int(getValue(elements[0].getElementsByTagName("before"), 0)) * 60
				after = int(getValue(elements[0].getElementsByTagName("after"), 0)) * 60
			else:
				before = after = int(value) * 60
			offset = (before, after)
		else:
			offset = None

		# Read out afterevent
		idx = {"standby": AFTEREVENT.STANDBY, "shutdown": AFTEREVENT.DEEPSTANDBY, "deepstandby": AFTEREVENT.DEEPSTANDBY}
		afterevent = getValue(timer.getElementsByTagName("afterevent"), None)
		try:
			afterevent = (idx[afterevent], None)
		except KeyError, ke:
			# TODO: do we really want to copy this behaviour?
			afterevent = (AFTEREVENT.NONE, None)

		# Read out exclude
		elements = timer.getElementsByTagName("exclude")
		if len(elements):
			excludes = ([], [], [], [])
			idx = {"title": 0, "shortdescription": 1, "description": 2, "dayofweek": 3}
			for exclude in elements:
				where = exclude.getAttribute("where")
				value = getValue(exclude, None)
				if not (value and where):
					continue

				try:
					excludes[idx[where]].append(value.encode("UTF-8"))
				except KeyError, ke:
					pass
		else:
			excludes = None

		# Read out max length
		elements = timer.getElementsByTagName("maxduration")
		if len(elements):
			maxlen = getValue(elements, None)
			if maxlen is not None:
				maxlen = int(maxlen)*60
		else:
			maxlen = None

		# Read out enabled status
		elements = timer.getElementsByTagName("enabled")
		if len(elements):
			if getValue(elements, "yes") == "no":
				enabled = False
			else:
				enabled = True
		else:
			enabled = True

		# Finally append tuple
		list.append(AutoTimerComponent(
				uniqueTimerId,
				name,
				match,
				enabled,
				timespan = timetuple,
				services = servicelist,
				offset = offset,
				afterevent = [afterevent],
				exclude = excludes,
				maxduration = maxlen
		))
