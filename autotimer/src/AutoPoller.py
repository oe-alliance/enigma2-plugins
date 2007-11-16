# Timer
from enigma import eTimer

# Config
from Components.config import config

class AutoPoller:
	"""Automatically Poll AutoTimer"""

	def __init__(self):
		# Keep track if we were launched before
		self.shouldRun = False

		# Init Timer
		self.timer = eTimer()
		self.timer.timeout.get().append(self.query)

	def shouldRun(self):
		return config.plugins.autotimer.autopoll.value

	def start(self, autotimer, initial = True):
		self.autotimer = autotimer
		if initial:
			delay = 2
		else:
			delay = config.plugins.autotimer.interval.value*3600
		self.timer.startLongTimer(delay)

	def stop(self):
		self.timer.stop()

	def query(self):
		# Ignore any exceptions
		try:
			self.autotimer.parseEPG()
		except:
			# Dump error to stdout
			import traceback, sys
			traceback.print_exc(file=sys.stdout)

		self.timer.startLongTimer(config.plugins.autotimer.interval.value*3600)

autopoller = AutoPoller()