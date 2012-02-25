from __future__ import print_function

# Core functionality
from enigma import eTimer, ePythonMessagePump

# Config
from Components.config import config

# Notifications
from Tools.FuzzyDate import FuzzyTime
from Tools.Notifications import AddPopup
from Screens.MessageBox import MessageBox

NOTIFICATIONID = 'AutoTimerConflictEncounteredNotification'
SIMILARNOTIFICATIONID = 'AutoTimerSimilarUsedNotification'

from threading import Thread, Semaphore
from collections import deque

class AutoPollerThread(Thread):
	"""Background thread where the EPG is parsed (unless initiated by the user)."""
	def __init__(self):
		Thread.__init__(self)
		self.__semaphore = Semaphore(0)
		self.__queue = deque(maxlen=1)
		self.__pump = ePythonMessagePump()
		self.__pump.recv_msg.get().append(self.gotThreadMsg)
		self.__timer = eTimer()
		self.__timer.callback.append(self.timeout)
		self.running = False

	def timeout(self):
		self.__semaphore.release()

	def gotThreadMsg(self, msg):
		"""Create Notifications if there is anything to display."""
		ret = self.__queue.pop()
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

	def start(self, initial=True):
		# NOTE: we wait for 10 seconds on initial launch to not delay enigma2 startup time
		if initial: delay = 10
		else: delay = config.plugins.autotimer.interval.value*3600

		self.__timer.startLongTimer(delay)
		if not self.isAlive():
			Thread.start(self)

	def pause(self):
		self.__timer.stop()

	def stop(self):
		self.__timer.stop()
		self.running = False
		self.__semaphore.release()
		self.__pump.recv_msg.get().remove(self.gotThreadMsg)
		self.__timer.callback.remove(self.timeout)

	def run(self):
		sem = self.__semaphore
		queue = self.__queue
		pump = self.__pump
		timer = self.__timer

		self.running = True
		while 1:
			sem.acquire()
			# NOTE: we have to check this here and not using the while to prevent the parser to be started on shutdown
			if not self.running: break

			from plugin import autotimer
			# Ignore any program errors
			try:
				queue.append(autotimer.parseEPG())
				pump.send(0)
			except Exception:
				# Dump error to stdout
				import traceback, sys
				traceback.print_exc(file=sys.stdout)

			timer.startLongTimer(config.plugins.autotimer.interval.value*3600)

class AutoPoller:
	"""Manages actual thread which does the polling. Used for convenience."""

	def __init__(self):
		self.thread = AutoPollerThread()

	def start(self, initial=True):
		self.thread.start(initial=initial)

	def pause(self):
		self.thread.pause()

	def stop(self):
		self.thread.stop()
		# NOTE: while we don't need to join the thread, we should do so in case it's currently parsining
		self.thread.join()
		self.thread = None
