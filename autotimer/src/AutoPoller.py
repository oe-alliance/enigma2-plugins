# Timer
from enigma import eTimer

# Config
from Components.config import config
from plugin import autotimer

# Notifications
import NavigationInstance

from Logger import doLog

class AutoPoller:
	"""Automatically Poll AutoTimer"""

	def __init__(self):
		# Init Timer
		doLog("[AutoTimer] Auto Poll Enabled")
		self.timer = eTimer()

	def start(self):
		if self.query not in self.timer.callback:
			self.timer.callback.append(self.query)
		self.timer.startLongTimer(config.plugins.autotimer.delay.value * 60)

	def stop(self):
		if self.query in self.timer.callback:
			self.timer.callback.remove(self.query)
		self.timer.stop()

	def query(self):
		self.timer.stop()
		from Screens.Standby import inStandby
		doLog("[AutoTimer] Auto Poll")
		doparse = True
		if config.plugins.autotimer.skip_during_records.getValue() and NavigationInstance.instance.RecordTimer.isRecording():
			doLog("[AutoTimer] Skip check during running records")
			doparse = False
		if config.plugins.autotimer.skip_during_epgrefresh.value:
			try:
				from Plugins.Extensions.EPGRefresh.EPGRefresh import epgrefresh
				if epgrefresh.isrunning:
					doLog("[AutoTimer] Skip check during running EPGRefresh")
					doparse = False
			except:
				pass
		if not inStandby and config.plugins.autotimer.onlyinstandby.value:
			doLog("[AutoTimer] Skip check while not in Standby")
			doparse = False
		if doparse:
			doLog("[AutoTimer] Auto Poll Started")
			# Ignore any program errors
			try:
				ret = autotimer.parseEPG(autoPoll=True)
			except Exception:
				# Dump error to stdout
				import traceback, sys
				traceback.print_exc(file=sys.stdout)
		#TODO back to hours
		#self.timer.startLongTimer(config.plugins.autotimer.interval.value * 3600)
		self.timer.startLongTimer(config.plugins.autotimer.interval.value * 60)
