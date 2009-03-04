# To check if in Standby
import Screens.Standby

# Base Class
import timer

# To see if in Timespan and to determine begin of timespan
from time import localtime, mktime, time, strftime

# Config
from Components.config import config

def checkTimespan(begin, end):
	# Get current time
	time = localtime()

	# Check if we span a day
	if begin[0] > end[0] or (begin[0] == end[0] and begin[1] >= end[1]):
		# Check if begin of event is later than our timespan starts
		if time.tm_hour > begin[0] or (time.tm_hour == begin[0] and time.tm_min >= begin[1]):
			# If so, event is in our timespan
			return True
		# Check if begin of event is earlier than our timespan end
		if time.tm_hour < end[0] or (time.tm_hour == end[0] and time.tm_min <= end[1]):
			# If so, event is in our timespan
			return True
		return False
	else:
		# Check if event begins earlier than our timespan starts
		if time.tm_hour < begin[0] or (time.tm_hour == begin[0] and time.tm_min < begin[1]):
			# Its out of our timespan then
			return False
		# Check if event begins later than our timespan ends
		if time.tm_hour > end[0] or (time.tm_hour == end[0] and time.tm_min > end[1]):
			# Its out of our timespan then
			return False
		return True

class EPGRefreshTimerEntry(timer.TimerEntry):
	"""TimerEntry ..."""
	def __init__(self, begin, tocall, nocheck = False):
		timer.TimerEntry.__init__(self, int(begin), int(begin))

		self.function = tocall
		self.nocheck = nocheck
		if nocheck:
			self.state = self.StatePrepared

	def getNextActivation(self):
		# We delay our activation so we won't rush into reprocessing a repeating one
		return self.begin+1

	def activate(self):
		if self.state == self.StateWaiting:
			# Check if in timespan
			if checkTimespan(config.plugins.epgrefresh.begin.value, config.plugins.epgrefresh.end.value):
				print "[EPGRefresh] In Timespan, will check if we're in Standby and have no Recordings running next"
				# Do we realy want to check nav?
				from NavigationInstance import instance
				if config.plugins.epgrefresh.force.value or (Screens.Standby.inStandby and instance is not None and not instance.RecordTimer.isRecording()):
					return True
				else:
					print "[EPGRefresh] Box still in use, rescheduling"

					# Recheck later
					self.begin = time() + config.plugins.epgrefresh.delay_standby.value*60
					return False
			else:
				print "[EPGRefresh] Not in timespan, ending timer"
				self.state = self.StateEnded
				return False
		elif self.state == self.StateRunning:
			self.function()

		return True

	def resetState(self):
		self.state = self.StateWaiting
		self.cancelled = False
		self.timeChanged()

	def timeChanged(self):
		if self.nocheck and self.state < self.StateRunning:
			self.state = self.StatePrepared

	def shouldSkip(self):
		return False

	def __repr__(self):
		return ''.join((
				"<EPGRefreshTimerEntry (",
				', '.join((
					strftime("%c", localtime(self.begin)),
					str(self.repeated),
					str(self.function)
				)),
				")>"
			))

class EPGRefreshTimer(timer.Timer):
	def __init__(self):
		timer.Timer.__init__(self)

	def remove(self, entry):
		print "[EPGRefresh] Timer removed " + str(entry)

		# avoid re-enqueuing
		entry.repeated = False

		# abort timer.
		# this sets the end time to current time, so timer will be stopped.
		entry.abort()

		if entry.state != entry.StateEnded:
			self.timeChanged(entry)

		print "state: ", entry.state
		print "in processed: ", entry in self.processed_timers
		print "in running: ", entry in self.timer_list
		# now the timer should be in the processed_timers list. remove it from there.
		self.processed_timers.remove(entry)

	def setRefreshTimer(self, tocall):
		# Add refresh Timer
		now = localtime()
		# XXX: basic workaround if the clock is not yet set
		year = 2009
		if now.tm_year > 2009:
			year = now.tm_year
		begin = mktime(
			(year, now.tm_mon, now.tm_mday,
			config.plugins.epgrefresh.begin.value[0],
			config.plugins.epgrefresh.begin.value[1],
			0, now.tm_wday, now.tm_yday, now.tm_isdst)
		)

		# If the last scan was finished before our timespan begins/began and
		# timespan began in the past fire the timer once (timer wouldn't do so
		# by itself)
		if config.plugins.epgrefresh.lastscan.value < begin and begin < time():
			tocall()

		refreshTimer = EPGRefreshTimerEntry(begin, tocall, nocheck = True)

		i = 0
		while i < 7:
			refreshTimer.setRepeated(i)
			i += 1

		# We can be sure that whenever this function is called the timer list
		# was wiped, so just add a new timer
		self.addTimerEntry(refreshTimer)

	def add(self, entry):
		entry.timeChanged()
		print "[EPGRefresh] Timer added " + str(entry)
		self.addTimerEntry(entry)

	def clear(self):
		self.timer_list = []

	def isActive(self):
		return len(self.timer_list) > 0

epgrefreshtimer = EPGRefreshTimer()
