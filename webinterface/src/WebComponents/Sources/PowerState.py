# -*- coding: utf-8 -*-
from Components.Sources.Source import Source


class PowerState(Source):
	def __init__(self, session):
		self.cmd = None
		self.session = session
		Source.__init__(self)

	def handleCommand(self, cmd):
		self.cmd = cmd

	def getStandby(self):
		from Screens.Standby import inStandby
		if inStandby is None:
			return "false"
		else:
			return "true"

	def getText(self):
		if self.cmd == "" or self.cmd is None:
			return self.getStandby()

		#-1: get current state
		# 0: toggle standby
		# 1: poweroff/deepstandby
		# 2: rebootdreambox
		# 3: rebootenigma
		# 4: wakeup (if not already awake)
		# 5: standby
		# 6: kill enigma2
		try:
			from Screens.Standby import inStandby
			from Screens.Standby import Standby
			type = int(self.cmd)
			if type == -1:
				return self.getStandby()

			elif type == 0:
				print "[PowerState.py] Standby 0"
				if inStandby is None:
					self.session.open(Standby)
					return "true"
				else:
					inStandby.Power()
					return "false"

			elif type == 4:
				print "[PowerState.py] Standby 4"
				if inStandby is not None:
					inStandby.Power()
					return "false"
				else:
					return "true"
			elif type == 5:
				print "[PowerState.py] Standby 5"
				if inStandby is None:
					self.session.open(Standby)
					return "true"
				else:
					return "false"
			elif type == 6:
				print "[PowerState.py] Standby 6"
				from twisted.internet import reactor
				import os
				reactor.callLater(1, os.popen, 'killall -9 enigma2')
				return "true"

			elif 0 < type < 4:
				print "[PowerState.py] TryQuitMainloop"
				from Screens.Standby import TryQuitMainloop
				from twisted.internet import reactor
				reactor.callLater(1, self.session.open, TryQuitMainloop, type)
				return "true"

			else:
				print "[PowerState.py] cmd unknown" % type
				return "error"

		except ValueError:
			return "error"

	text = property(getText)
