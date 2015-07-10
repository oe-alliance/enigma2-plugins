# Format counter
from time import strftime

# regular expression
from re import compile as re_compile

# Alternatives and service restriction
from enigma import eServiceReference, eServiceCenter

# To get preferred component
from Components.config import config

class AutoTimerComponent(object):
	"""AutoTimer Component which also handles validity checks"""

	"""
	 Initiate
	"""
	def __init__(self, id, name, match, enabled, *args, **kwargs):
		self.id = id
		self._afterevent = []
		self.setValues(name, match, enabled, *args, **kwargs)

	"""
	 Unsets all Attributes
	"""
	def clear(self, id = -1, enabled = False):
		self.id = id
		self.setValues('', '', enabled)

	"""
	 Create a deep copy of this instance
	"""
	def clone(self):
		return self.__deepcopy__({})

	"""
	 Hook needed for WebIf
	"""
	def getEntry(self):
		return self

	"""
	 Keeps init small and helps setting many values at once
	"""
	def setValues(self, name, match, enabled, timespan=None, services=None, \
			offset=None, afterevent=[], exclude=None, maxduration=None, \
			destination=None, include=None, matchCount=0, matchLeft=0, \
			matchLimit='', matchFormatString='', lastBegin=0, justplay=False, \
			avoidDuplicateDescription=0, searchForDuplicateDescription=2, bouquets=None, \
			tags=None, searchType="partial", searchCase="insensitive", \
			overrideAlternatives=True, timeframe=None, vps_enabled=False, \
			vps_overwrite=False, setEndtime=False, series_labeling=False):
		self.name = name
		self.match = match
		self.enabled = enabled
		self.timespan = timespan
		self.services = services
		self.offset = offset
		self.afterevent = afterevent
		self.exclude = exclude
		self.maxduration = maxduration
		self.destination = destination
		self.include = include
		self.matchCount = matchCount
		self.matchLeft = matchLeft
		self.matchLimit = matchLimit
		self.matchFormatString = matchFormatString
		self.lastBegin = lastBegin
		self.justplay = justplay
		self.avoidDuplicateDescription = avoidDuplicateDescription
		self.searchForDuplicateDescription = searchForDuplicateDescription
		self.bouquets = bouquets
		self.tags = tags or []
		self.searchType = searchType
		self.searchCase = searchCase
		self.overrideAlternatives = overrideAlternatives
		self.timeframe = timeframe
		self.vps_enabled = vps_enabled
		self.vps_overwrite = vps_overwrite
		self.series_labeling = series_labeling
		self.setEndtime = setEndtime

### Attributes / Properties

	def setAfterEvent(self, afterevent):
		if afterevent is not self._afterevent:
			del self._afterevent[:]
		else:
			self._afterevent = []

		for action, timespan in afterevent:
			if timespan is None or timespan[0] is None:
				self._afterevent.append((action, (None,)))
			else:
				self._afterevent.append((action, self.calculateDayspan(*timespan)))

	afterevent = property(lambda self: self._afterevent, setAfterEvent)

	def setBouquets(self, bouquets):
		if bouquets:
			self._bouquets = bouquets
		else:
			self._bouquets = []

	bouquets = property(lambda self: self._bouquets , setBouquets)

	def setExclude(self, exclude):
		if exclude:
			self._exclude = (
				[re_compile(x) for x in exclude[0]],
				[re_compile(x) for x in exclude[1]],
				[re_compile(x) for x in exclude[2]],
				exclude[3]
			)
		else:
			self._exclude = ([], [], [], [])

	exclude = property(lambda self: self._exclude, setExclude)

	def setInclude(self, include):
		if include:
			self._include = (
				[re_compile(x) for x in include[0]],
				[re_compile(x) for x in include[1]],
				[re_compile(x) for x in include[2]],
				include[3]
			)
		else:
			self._include = ([], [], [], [])

	include = property(lambda self: self._include, setInclude)

	def setSearchCase(self, case):
		assert case in ("sensitive", "insensitive"), "search case must be sensitive or insensitive"
		self._searchCase = case

	searchCase = property(lambda self: self._searchCase, setSearchCase)

	def setSearchType(self, type):
		assert type in ("exact", "partial", "start", "description"), "search type must be exact, partial, start or description"
		self._searchType = type

	searchType = property(lambda self: self._searchType, setSearchType)

	def setServices(self, services):
		if services:
			self._services = services
		else:
			self._services = []

	services = property(lambda self: self._services, setServices)

	def setTimespan(self, timespan):
		if timespan is None or timespan and timespan[0] is None:
			self._timespan = (None,)
		else:
			self._timespan = self.calculateDayspan(*timespan)

	timespan = property(lambda self: self._timespan, setTimespan)

### See if Attributes are set

	def hasAfterEvent(self):
		return len(self.afterevent)

	def hasAfterEventTimespan(self):
		for afterevent in self.afterevent:
			if afterevent[1][0] is not None:
				return True
		return False

	def hasCounter(self):
		return self.matchCount != 0

	def hasCounterFormatString(self):
		return self.matchFormatString != ''

	def hasDestination(self):
		return self.destination is not None

	def hasDuration(self):
		return self.maxduration is not None

	def hasTags(self):
		return len(self.tags)

	def hasTimespan(self):
		return self.timespan[0] is not None

	def hasOffset(self):
		return self.offset is not None

	def hasTimeframe(self):
		return self.timeframe is not None

### Helper

	"""
	 Returns a tulple of (input begin, input end, begin earlier than end)
	"""
	def calculateDayspan(self, begin, end, ignore = None):
		if end[0] < begin[0] or (end[0] == begin[0] and end[1] <= begin[1]):
			return (begin, end, True)
		else:
			return (begin, end, False)

	"""
	 Returns if a given timestruct is in a timespan
	"""
	def checkAnyTimespan(self, time, begin = None, end = None, haveDayspan = False):
		if begin is None:
			return False

		# Check if we span a day
		if haveDayspan:
			# Check if begin of event is later than our timespan starts
			if time.tm_hour > begin[0] or (time.tm_hour == begin[0] and time.tm_min >= begin[1]):
				# If so, event is in our timespan
				return False
			# Check if begin of event is earlier than our timespan end
			if time.tm_hour < end[0] or (time.tm_hour == end[0] and time.tm_min <= end[1]):
				# If so, event is in our timespan
				return False
			return True
		else:
			# Check if event begins earlier than our timespan starts
			if time.tm_hour < begin[0] or (time.tm_hour == begin[0] and time.tm_min < begin[1]):
				# Its out of our timespan then
				return True
			# Check if event begins later than our timespan ends
			if time.tm_hour > end[0] or (time.tm_hour == end[0] and time.tm_min > end[1]):
				# Its out of our timespan then
				return True
			return False

	"""
	 Called when a timer based on this component was added
	"""
	def update(self, begin, timestamp):
		# Only update limit when we have new begin
		if begin > self.lastBegin:
			self.lastBegin = begin

			# Update Counter:
			# %m is Month, %U is week (sunday), %W is week (monday)
			newLimit = strftime(self.matchFormatString, timestamp)

			if newLimit != self.matchLimit:
				self.matchLeft = self.matchCount
				self.matchLimit = newLimit

### Makes saving Config easier

	getAvoidDuplicateDescription = lambda self: self.avoidDuplicateDescription

	getBouquets = lambda self: self._bouquets

	getCompleteAfterEvent = lambda self: self._afterevent

	getCounter = lambda self: self.matchCount
	getCounterFormatString = lambda self: self.matchFormatString
	getCounterLeft = lambda self: self.matchLeft
	getCounterLimit = lambda self: self.matchLimit

	# XXX: as this function was not added by me (ritzMo) i'll leave it like this but i'm not really sure if this is right ;-)
	getDestination = lambda self: self.destination is not None

	getDuration = lambda self: self.maxduration/60

	getEnabled = lambda self: self.enabled and "yes" or "no"

	getExclude = lambda self: self._exclude
	getExcludedDays = lambda self: self.exclude[3]
	getExcludedDescription = lambda self: [x.pattern for x in self.exclude[2]]
	getExcludedShort = lambda self: [x.pattern for x in self.exclude[1]]
	getExcludedTitle = lambda self: [x.pattern for x in self.exclude[0]]

	getId = lambda self: self.id

	getInclude = lambda self: self._include
	getIncludedTitle = lambda self: [x.pattern for x in self.include[0]]
	getIncludedShort = lambda self: [x.pattern for x in self.include[1]]
	getIncludedDescription = lambda self: [x.pattern for x in self.include[2]]
	getIncludedDays = lambda self: self.include[3]

	getJustplay = lambda self: self.justplay and "1" or "0"

	getLastBegin = lambda self: self.lastBegin

	getMatch = lambda self: self.match
	getName = lambda self: self.name

	getOffsetBegin = lambda self: self.offset[0]/60
	getOffsetEnd = lambda self: self.offset[1]/60

	getOverrideAlternatives = lambda self: self.overrideAlternatives and "1" or "0"

	getServices = lambda self: self._services

	getTags = lambda self: self.tags

	getTimespan = lambda self: self._timespan
	getTimespanBegin = lambda self: '%02d:%02d' % (self.timespan[0][0], self.timespan[0][1])
	getTimespanEnd = lambda self: '%02d:%02d' % (self.timespan[1][0], self.timespan[1][1])

	getTimeframe = lambda self: self.timeframe
	getTimeframeBegin = lambda self: int(self.timeframe[0])
	getTimeframeEnd	= lambda self: int(self.timeframe[1])

	isOffsetEqual = lambda self: self.offset[0] == self.offset[1]

### Actual functionality

	def applyOffset(self, begin, end):
		if self.offset is None:
			return (begin, end)
		return (begin - self.offset[0], end + self.offset[1])

	def checkCounter(self, timestamp):
		# 0-Count is considered "unset"
		if self.matchCount == 0:
			return False

		# Check if event is in current timespan (we can only manage one!)
		limit = strftime(self.matchFormatString, timestamp)
		if limit != self.matchLimit:
			return True

		if self.matchLeft > 0:
			return False
		return True

	def checkDuration(self, length):
		if self.maxduration is None:
			return False
		return length > self.maxduration

	def checkExcluded(self, title, short, extended, dayofweek):
		if dayofweek and self.exclude[3]:
			list = self.exclude[3]
			if dayofweek in list:
				return True
			if "weekend" in list and dayofweek in ("5", "6"):
				return True
			if "weekday" in list and dayofweek in ("0", "1", "2", "3", "4"):
				return True

		for exclude in self.exclude[0]:
			if exclude.search(title):
				return True
		for exclude in self.exclude[1]:
			if exclude.search(short):
				return True
		for exclude in self.exclude[2]:
			if exclude.search(extended):
				return True
		return False

	def checkFilter(self, title, short, extended, dayofweek):
		if self.checkExcluded(title, short, extended, dayofweek):
			return True

		return self.checkIncluded(title, short, extended, dayofweek)

	def checkIncluded(self, title, short, extended, dayofweek):
		if dayofweek and self.include[3]:
			list = self.include[3][:]
			if "weekend" in list:
				list.extend(("5", "6"))
			if "weekday" in list:
				list.extend(("0", "1", "2", "3", "4"))
			if dayofweek not in list:
				return True

		for include in self.include[0]:
			if not include.search(title):
				return True
		for include in self.include[1]:
			if not include.search(short):
				return True
		for include in self.include[2]:
			if not include.search(extended):
				return True

		return False

	def checkServices(self, check_service):
		services = self.services
		bouquets = self.bouquets
		if services or bouquets:
			addbouquets = []

			for service in services:
				if service == check_service:
					return False

				myref = eServiceReference(str(service))
				if myref.flags & eServiceReference.isGroup:
					addbouquets.append(service)

			serviceHandler = eServiceCenter.getInstance()
			for bouquet in bouquets + addbouquets:
				myref = eServiceReference(str(bouquet))
				mylist = serviceHandler.list(myref)
				if mylist is not None:
					while 1:
						s = mylist.getNext()
						# TODO: I wonder if its sane to assume we get services here (and not just new lists)
						# We can ignore markers & directorys here because they won't match any event's service :-)
						if s.valid():
							# strip all after last :
							value = s.toString()
							pos = value.rfind(':')
							if pos != -1:
								if value[pos-1] == ':':
									pos -= 1
								value = value[:pos+1]

							if value == check_service:
								return False
						else:
							break
			return True
		return False

	"""
	Return alternative service including a given ref.
	Note that this only works for alternatives that the autotimer is restricted to.
	"""
	def getAlternative(self, override_service):
		services = self.services
		if services:
			serviceHandler = eServiceCenter.getInstance()

			for service in services:
				myref = eServiceReference(str(service))
				if myref.flags & eServiceReference.isGroup:
					mylist = serviceHandler.list(myref)
					if mylist is not None:
						while 1:
							s = mylist.getNext()
							if s.valid():
								# strip all after last :
								value = s.toString()
								pos = value.rfind(':')
								if pos != -1:
									if value[pos-1] == ':':
										pos -= 1
									value = value[:pos+1]

								if value == override_service:
									return service
							else:
								break
		return override_service

	def checkTimespan(self, begin):
		return self.checkAnyTimespan(begin, *self.timespan)

	def decrementCounter(self):
		if self.matchCount and self.matchLeft > 0:
			self.matchLeft -= 1

	def getAfterEvent(self):
		for afterevent in self.afterevent:
			if afterevent[1][0] is None:
				return afterevent[0]
		return None

	def getAfterEventTimespan(self, end):
		for afterevent in self.afterevent:
			if not self.checkAnyTimespan(end, *afterevent[1]):
				return afterevent[0]
		return None

	def checkTimeframe(self, begin):
		if self.timeframe is not None:
			start, end = self.timeframe
			if begin > start and begin < (end + 24*60*60):
				return False
			return True
		return False

### Misc

	def __copy__(self):
		return self.__class__(
			self.id,
			self.name,
			self.match,
			self.enabled,
			timespan = self.timespan,
			services = self.services,
			offset = self.offset,
			afterevent = self.afterevent,
			exclude = (self.getExcludedTitle(), self.getExcludedShort(), self.getExcludedDescription(), self.getExcludedDays()),
			maxduration = self.maxduration,
			destination = self.destination,
			include = (self.getIncludedTitle(), self.getIncludedShort(), self.getIncludedDescription(), self.getIncludedDays()),
			matchCount = self.matchCount,
			matchLeft = self.matchLeft,
			matchLimit = self.matchLimit,
			matchFormatString = self.matchFormatString,
			lastBegin = self.lastBegin,
			justplay = self.justplay,
			avoidDuplicateDescription = self.avoidDuplicateDescription,
			searchForDuplicateDescription = self.searchForDuplicateDescription,
			bouquets = self.bouquets,
			tags = self.tags,
			searchType = self.searchType,
			searchCase = self.searchCase,
			overrideAlternatives = self.overrideAlternatives,
			timeframe = self.timeframe,
			vps_enabled = self.vps_enabled,
			vps_overwrite = self.vps_overwrite,
			series_labeling = self.series_labeling,
		)

	def __deepcopy__(self, memo):
		return self.__class__(
			self.id,
			self.name,
			self.match,
			self.enabled,
			timespan = self.timespan,
			services = self.services[:],
			offset = self.offset and self.offset[:],
			afterevent = self.afterevent[:],
			exclude = (self.getExcludedTitle(), self.getExcludedShort(), self.getExcludedDescription(), self.exclude[3][:]),
			maxduration = self.maxduration,
			destination = self.destination,
			include = (self.getIncludedTitle(), self.getIncludedShort(), self.getIncludedDescription(), self.include[3][:]),
			matchCount = self.matchCount,
			matchLeft = self.matchLeft,
			matchLimit = self.matchLimit,
			matchFormatString = self.matchFormatString,
			lastBegin = self.lastBegin,
			justplay = self.justplay,
			avoidDuplicateDescription = self.avoidDuplicateDescription,
			searchForDuplicateDescription = self.searchForDuplicateDescription,
			bouquets = self.bouquets[:],
			tags = self.tags[:],
			searchType = self.searchType,
			searchCase = self.searchCase,
			overrideAlternatives = self.overrideAlternatives,
			timeframe = self.timeframe,
			vps_enabled = self.vps_enabled,
			vps_overwrite = self.vps_overwrite,
			series_labeling = self.series_labeling,
		)

	def __eq__(self, other):
		if isinstance(other, AutoTimerComponent):
			return self.id == other.id
		return False

	def __lt__(self, other):
		if isinstance(other, AutoTimerComponent):
			return self.name.lower() < other.name.lower()
		return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def __repr__(self):
		return ''.join((
			'<AutomaticTimer ',
			self.name,
			' (',
			', '.join((
					str(self.match),
					str(self.searchCase),
					str(self.searchType),
					str(self.timespan),
					str(self.services),
					str(self.offset),
					str(self.afterevent),
					str(([x.pattern for x in self.exclude[0]],
						[x.pattern for x in self.exclude[1]],
						[x.pattern for x in self.exclude[2]],
						self.exclude[3]
					)),
					str(([x.pattern for x in self.include[0]],
						[x.pattern for x in self.include[1]],
						[x.pattern for x in self.include[2]],
						self.include[3]
					)),
					str(self.maxduration),
					str(self.enabled),
					str(self.destination),
					str(self.matchCount),
					str(self.matchLeft),
					str(self.matchLimit),
					str(self.matchFormatString),
					str(self.lastBegin),
					str(self.justplay),
					str(self.avoidDuplicateDescription),
					str(self.searchForDuplicateDescription),
					str(self.bouquets),
					str(self.tags),
					str(self.overrideAlternatives),
					str(self.timeframe),
					str(self.vps_enabled),
					str(self.vps_overwrite),
					str(self.series_labeling),
			 )),
			 ")>"
		))

class AutoTimerFastscanComponent(AutoTimerComponent):
	def __init__(self, *args, **kwargs):
		AutoTimerComponent.__init__(self, *args, **kwargs)
		self._fastServices = None

	def setBouquets(self, bouquets):
		AutoTimerComponent.setBouquets(self, bouquets)
		self._fastServices = None

	def setServices(self, services):
		AutoTimerComponent.setServices(self, services)
		self._fastServices = None

	def getFastServices(self):
		if self._fastServices is None:
			fastServices = []
			append = fastServices.append
			addbouquets = []
			for service in self.services:
				myref = eServiceReference(str(service))
				if myref.flags & eServiceReference.isGroup:
					addbouquets.append(service)
				else:
					comp = service.split(':')
					append(':'.join(comp[3:]))

			serviceHandler = eServiceCenter.getInstance()
			for bouquet in self.bouquets + addbouquets:
				myref = eServiceReference(str(bouquet))
				mylist = serviceHandler.list(myref)
				if mylist is not None:
					while 1:
						s = mylist.getNext()
						# TODO: I wonder if its sane to assume we get services here (and not just new lists)
						# We can ignore markers & directorys here because they won't match any event's service :-)
						if s.valid():
							# strip all after last :
							value = s.toString()
							pos = value.rfind(':')
							if pos != -1:
								if value[pos-1] == ':':
									pos -= 1
								value = value[:pos+1]

							comp = value.split(':')
							append(':'.join(value[3:]))
						else:
							break
			self._fastServices = fastServices
		return self._fastServices

	def checkServices(self, check_service):
		services = self.getFastServices()
		if services:
			check = ':'.join(check_service.split(':')[3:])
			for service in services:
				if service == check:
					return False # included
			return True # not included
		return False # no restriction

	def getAlternative(self, override_service):
		services = self.services
		if services:
			override = ':'.join(override_service.split(':')[3:])
			serviceHandler = eServiceCenter.getInstance()

			for service in services:
				myref = eServiceReference(str(service))
				if myref.flags & eServiceReference.isGroup:
					mylist = serviceHandler.list(myref)
					if mylist is not None:
						while 1:
							s = mylist.getNext()
							if s.valid():
								# strip all after last :
								value = s.toString()
								pos = value.rfind(':')
								if pos != -1:
									if value[pos-1] == ':':
										pos -= 1
									value = value[:pos+1]

								if ':'.join(value.split(':')[3:]) == override:
									return service
							else:
								break
		return override_service

# very basic factory ;-)
preferredAutoTimerComponent = lambda *args, **kwargs: AutoTimerFastscanComponent(*args, **kwargs) if config.plugins.autotimer.fastscan.value else AutoTimerComponent(*args, **kwargs)
