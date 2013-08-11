# Timer
from enigma import eTimer

# Config
from Components.config import config
from plugin import autotimer

# Notifications
from Tools.FuzzyDate import FuzzyTime
from Tools.Notifications import AddPopup
from Screens.MessageBox import MessageBox
import NavigationInstance

class AutoPoller:
	"""Automatically Poll AutoTimer"""

	def __init__(self):
		# Init Timer
		print "[AutoTimer] Auto Poll Enabled"
		self.timer = eTimer()

	def start(self):
		if self.query not in self.timer.callback:
			self.timer.callback.append(self.query)
		self.timer.startLongTimer(config.plugins.autotimer.delay.value*60)

	def stop(self):
		if self.query in self.timer.callback:
			self.timer.callback.remove(self.query)
		self.timer.stop()

	def query(self):
		self.timer.stop()
		from Screens.Standby import inStandby
		print "[AutoTimer] Auto Poll"
		if config.plugins.autotimer.skip_during_records.getValue() and NavigationInstance.instance.RecordTimer.isRecording():
			print("[AutoTimer] Skip check during running records")
		else:
			if config.plugins.autotimer.onlyinstandby.value and inStandby:
				print "[AutoTimer] Auto Poll Started"
				# Ignore any program errors
				try:
					ret = autotimer.parseEPG(autoPoll = True)
				except Exception:
					# Dump error to stdout
					import traceback, sys
					traceback.print_exc(file=sys.stdout)
			elif not config.plugins.autotimer.onlyinstandby.value:
				print "[AutoTimer] Auto Poll Started"
				# Ignore any program errors
				try:
					ret = autotimer.parseEPG(autoPoll = True)
				except Exception:
					# Dump error to stdout
					import traceback, sys
					traceback.print_exc(file=sys.stdout)
		self.timer.startLongTimer(config.plugins.autotimer.interval.value*60)
