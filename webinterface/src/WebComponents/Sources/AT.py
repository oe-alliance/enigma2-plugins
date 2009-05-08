# Code for the AutoTimerPlugin
from Components.Sources.Source import Source

class AT(Source):
	LIST = 0
	WRITE = 1

	def __init__(self, session, func=LIST):
		print "AutoTimer: init: ", func
		Source.__init__(self)
		self.func = func
		self.session = session
		self.result = []

	def handleCommand(self, cmd):
		print "AutoTimer: handleCommand: ", cmd
		if cmd is not None:
			self.cmd = cmd
			if self.func is self.LIST:
				self.result = self.timerList(cmd)
			elif self.func is self.WRITE:
				self.result = self.writeTimer(cmd)

	def timerList(self):
		print "timerList"

		try:
			from Plugins.Extensions.AutoTimer.plugin import autotimer

			if not autotimer:
				from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
				autotimer = AutoTimer()
		except ImportError:
			return []

		returnList = []

		for timer in autotimer.getTimerList():
			print "TIMER: ", timer
			innerList = [
				timer.getName(),
				timer.getMatch()
			]

			if timer.hasAfterEvent():
				innerList.append(timer.getAfterEvent()) # 2
			else:
				innerList.append("") # 2

			#excludes
			innerList.extend((
				timer.getExcludedTitle(),
				timer.getExcludedShort(),
				timer.getExcludedDescription(),
				timer.getExcludedDays(),
												))

			#includes
			innerList.extend((
				timer.getIncludedTitle(),
				timer.getIncludedShort(),
				timer.getIncludedDescription(),
				timer.getIncludedDays(),
												))

			# services
			innerList.extend((
				timer.getServices(), # 11
				timer.getBouquets() # 12
												))

			if timer.hasTimespan():
				innerList.extend((
					timer.getTimespanBegin(), # 13
					timer.getTimespanEnd() # 14
												))
			else:
				innerList.extend(("", "")) # 13, 14

			if timer.hasDuration():
				innerList.append(timer.getDuration()) # 15
			else:
				innerList.append("") # 15

			if timer.hasCounter():
				innerList.extend((
					timer.getCounter(), # 16
					timer.getCounterLeft() # 17
												))
			else:
				innerList.extend((0, 0)) # 16, 17

			innerList.append(timer.getCounterLimit()) # 18

			if timer.hasDestination():
				innerList.append(timer.destination) # 19
			else:
				innerList.append("/hdd/movie/") # 19

			if timer.hasCounterFormatString():
				innerList.append(timer.getCounterFormatString()) # 20
			else:
				innerList.append("") # 20

			innerList.extend((
				timer.getLastBegin(), # 21
				timer.getJustplay(), # 22
				timer.getAvoidDuplicateDescription() # 23
												))

			if timer.hasTags():
				innerList.append(timer.getTags()) # 24
			else:
				innerList.append("") # 24

			print "Enabled", timer.getEnabled()
			innerList.append(timer.getEnabled()) # 25
			innerList.append("off") # 26

			returnList.append(innerList)

		return returnList

	def writeTimer(self, param):
		print "writeTimer: ", param
		# TODO: fix error handling
		return

	def command(self, param):
		print "command: ", param
		return

		param = int(param)

		# TODO: fix error handling

	list = property(timerList)
	lut = {"Name": 0
			, "Match": 1
			, "AfterEvent": 2
			, "ExcludedTitle": 3
			, "ExcludedShort": 4
			, "ExcludedDescription": 5
			, "ExcludedDays": 6
			, "IncludedTitle": 7
			, "IncludedShort": 8
			, "IncludedDescription": 9
			, "IncludedDays": 10
			, "Services": 11
			, "Bouquets": 12
			, "TimespanBegin": 13
			, "TimespanEnd": 14
			, "Duration": 15
			, "Counter": 16
			, "CounterLeft": 17
			, "CounterLimit": 18
			, "Destination": 19
			, "CounterFormatString": 20
			, "LastBegin": 21
			, "Justplay": 22
			, "AvoidDuplicateDescription": 23
			, "Tags": 24
			, "Enabled": 25
			, "toggleDisabledIMG": 26
			}
