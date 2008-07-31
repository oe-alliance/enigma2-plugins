# Timer
from enigma import eTimer

# Config
from Components.config import config

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

		# Ignore any exceptions
		try:
			autotimer.parseEPG()
		except:
			# Dump error to stdout
			import traceback, sys
			traceback.print_exc(file=sys.stdout)

		self.timer.startLongTimer(config.plugins.autotimer.interval.value*3600)

