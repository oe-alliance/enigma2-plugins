# Format Counter
from time import strftime

# regular expression
from re import compile as re_compile

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
	def setValues(self, name, match, enabled, timespan = None, services = None, offset = None, \
			afterevent = [], exclude = None, maxduration = None, destination = None, \
			include = None, matchCount = 0, matchLeft = 0, matchLimit = '', matchFormatString = '', \
			lastBegin = 0, justplay = False, avoidDuplicateDescription = 0, bouquets = None, \
			tags = None):
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
		self.bouquets = bouquets
		self.tags = tags or []

### Attributes / Properties

	def getCompleteAfterEvent(self):
		return self._afterevent

	def setAfterEvent(self, afterevent):
		del self._afterevent[:]
		if len(afterevent):
			for definition in afterevent:
				action, timespan = definition
				if timespan is None:
					self._afterevent.append((action, (None,)))
				else:
					self._afterevent.append((action, self.calculateDayspan(*timespan)))

	afterevent = property(getCompleteAfterEvent, setAfterEvent)

	def setBouquets(self, bouquets):
		if bouquets:
			self._bouquets = bouquets
		else:
			self._bouquets = []

	def getBouquets(self):
		return self._bouquets

	bouquets = property(getBouquets, setBouquets)

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

	def getExclude(self):
		return self._exclude

	exclude = property(getExclude, setExclude)

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

	def getInclude(self):
		return self._include

	include = property(getInclude, setInclude)

	def setName(self, name):
		self.name = name

	def getMatch(self):
		return self._match

	def setMatch(self, match):
		# XXX: a sanity check might be useful...
		self._match = match

	match = property(getMatch, setMatch)

	def getServices(self):
		return self._services

	def setServices(self, services):
		if services:
			self._services = services
		else:
			self._services = []

	services = property(getServices, setServices)

	def getTimespan(self):
		return self._timespan

	def setTimespan(self, timespan):
		if timespan is None or len(timespan) and timespan[0] is None:
			self._timespan = (None,)
		else:
			self._timespan = self.calculateDayspan(*timespan)

	timespan = property(getTimespan, setTimespan)

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
		return len(self.tags) > 0

	def hasTimespan(self):
		return self.timespan[0] is not None

	def hasOffset(self):
		return self.offset is not None

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
	 Returns a list of all allowed services by listing the bouquets
	"""
	def getFullServices(self):
		list = self.services[:]

		from enigma import eServiceReference, eServiceCenter
		serviceHandler = eServiceCenter.getInstance()
		for bouquet in self.bouquets:
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
							value = value[:pos+1]

						list.append(value)
					else:
						break

		return list

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

	def getAvoidDuplicateDescription(self):
		return self.avoidDuplicateDescription

	def getCounter(self):
		return self.matchCount

	def getCounterFormatString(self):
		return self.matchFormatString

	def getCounterLeft(self):
		return self.matchLeft

	def getCounterLimit(self):
		return self.matchLimit

	def getDestination(self):
		# XXX: as this function was not added by me (ritzMo) i'll leave it like this but i'm not really sure if this is right ;-)
		return self.destination is not None

	def getDuration(self):
		return self.maxduration/60

	def getEnabled(self):
		return self.enabled and "yes" or "no"

	def getExcludedDays(self):
		return self.exclude[3]

	def getExcludedDescription(self):
		return [x.pattern for x in self.exclude[2]]

	def getExcludedShort(self):
		return [x.pattern for x in self.exclude[1]]

	def getExcludedTitle(self):
		return [x.pattern for x in self.exclude[0]]	

	def getIncludedTitle(self):
		return [x.pattern for x in self.include[0]]

	def getIncludedShort(self):
		return [x.pattern for x in self.include[1]]

	def getIncludedDescription(self):
		return [x.pattern for x in self.include[2]]

	def getIncludedDays(self):
		return self.include[3]

	def getJustplay(self):
		return self.justplay and "1" or "0"

	def getLastBegin(self):
		return self.lastBegin

	def getName(self):
		return self.name

	def getOffsetBegin(self):
		return self.offset[0]/60

	def getOffsetEnd(self):
		return self.offset[1]/60

	def getTags(self):
		return self.tags

	def getTimespanBegin(self):
		return '%02d:%02d' % (self.timespan[0][0], self.timespan[0][1])

	def getTimespanEnd(self):
		return '%02d:%02d' % (self.timespan[1][0], self.timespan[1][1])

	def isOffsetEqual(self):
		return self.offset[0] == self.offset[1]
	
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
		if len(self.exclude[3]):
			list = [x for x in self.exclude[3]]
			if "weekend" in list:
				list.extend(["5", "6"])
			if "weekday" in list:
				list.extend(["0", "1", "2", "3", "4"])
			if dayofweek in list:
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
		if len(self.include[3]):
			list = [x for x in self.include[3]]
			if "weekend" in list:
				list.extend(["5", "6"])
			if "weekday" in list:
				list.extend(["0", "1", "2", "3", "4"])
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

	def checkServices(self, service):
		if len(self.services) or len(self.bouquets): 
			return service not in self.getFullServices()
		return False

	def checkTimespan(self, begin):
		return self.checkAnyTimespan(begin, *self.timespan)

	def decrementCounter(self)
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
			bouquets = self.bouquets,
			tags = self.tags
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
			bouquets = self.bouquets[:],
			tags = self.tags[:]
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
		return ''.join([
			'<AutomaticTimer ',
			self.name,
			' (',
			', '.join([
					str(self.match),
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
					str(self.bouquets),
					str(self.tags)
			 ]),
			 ")>"
		])

