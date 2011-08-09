# Timer
from enigma import eTimer

# Config
from Components.config import config

# Notifications
from Tools.FuzzyDate import FuzzyTime
from Tools.Notifications import AddPopup
from Screens.MessageBox import MessageBox

NOTIFICATIONID = 'AutoTimerConflictEncounteredNotification'
SIMILARNOTIFICATIONID = 'AutoTimerSimilarUsedNotification'

class AutoPoller:
	"""Automatically Poll AutoTimer"""

	def __init__(self):
		# Init Timer
		self.timer = eTimer()

	def start(self, initial = True):
		if initial:
			delay = 2
		else:
			delay = config.plugins.autotimer.interval.value*3600

		if self.query not in self.timer.callback:
			self.timer.callback.append(self.query)
		self.timer.startLongTimer(delay)

	def stop(self):
		if self.query in self.timer.callback:
			self.timer.callback.remove(self.query)
		self.timer.stop()

	def query(self):
		from plugin import autotimer

		# Ignore any program errors
		try:
			ret = autotimer.parseEPG()
		except Exception:
			# Dump error to stdout
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
		else:
			conflicts = ret[4]
			if conflicts and config.plugins.autotimer.notifconflict.value:
				AddPopup(
					_("%d conflict(s) encountered when trying to add new timers:\n%s") % (len(conflicts), '\n'.join([_("%s: %s at %s") % (x[4], x[0], FuzzyTime(x[2])) for x in conflicts])),
					MessageBox.TYPE_INFO,
					5,
					NOTIFICATIONID
				)
			similars = ret[5]
			if similars and config.plugins.autotimer.notifsimilar.value:
				AddPopup(
					_("%d conflict(s) solved with similar timer(s):\n%s") % (len(similars), '\n'.join([_("%s: %s at %s") % (x[4], x[0], FuzzyTime(x[2])) for x in similars])),
					MessageBox.TYPE_INFO,
					5,
					SIMILARNOTIFICATIONID
				)

		self.timer.startLongTimer(config.plugins.autotimer.interval.value*3600)

