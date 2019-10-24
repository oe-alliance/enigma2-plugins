from enigma import eTimer, eDVBLocalTimeHandler, eEPGCache
from time import time
from Components.config import config
from Components.Console import Console
try:
	from Tools.StbHardware import setRTCtime
except:
	from Tools.DreamboxHardware import setRTCtime


class NTPSyncPoller:

	"""Automatically Poll NTP"""

	def __init__(self):
		self.timer = eTimer()
		self.Console = Console()

	def start(self):
		if not self.timer.callback:
			self.timer.callback.append(self.NTPStart)
		self.timer.startLongTimer(0)

	def stop(self):
		if self.timer.callback:
			self.timer.callback.remove(self.NTPStart)
		self.timer.stop()

	def NTPStart(self):
		if config.plugins.SystemTime.choiceSystemTime.value == "1":
			cmd = '/usr/sbin/ntpdate -s -u %s' % config.plugins.SystemTime.ip.value
			self.Console.ePopen(cmd, self.update_schedule)
		self.timer.startLongTimer(int(config.plugins.SystemTime.useNTPminutes.value) * 60)

	def update_schedule(self, result=None, retval=None, extra_args=None):
		if eDVBLocalTimeHandler.getInstance().ready():
			nowTime = time()
			if nowTime > 1388534400:
				setRTCtime(nowTime)
				if config.plugins.SystemTime.choiceSystemTime.value == "0":
					eDVBLocalTimeHandler.getInstance().setUseDVBTime(True)
				else:
					eDVBLocalTimeHandler.getInstance().setUseDVBTime(False)
				try:
					eEPGCache.getInstance().timeUpdated()
				except:
					pass
