#######################################################################
#
#    Push Service for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=167779
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################

import os
import sys
import traceback
from time import localtime

from Components.config import config
from enigma import eTimer
from Tools.BoundFunction import boundFunction


# Plugin internal
from . import _
from PushServiceBase import PushServiceBase


# States
(PSBOOT, PSBOOTRUN, PSFIRST, PSFIRSTRUN, PSCYCLE) = range(5)
#MABE use an enum http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python


#######################################################
# Logical part
class PushService(PushServiceBase):

	def __init__(self):
		PushServiceBase.__init__(self)
		
		self.state = PSBOOT if config.pushservice.runonboot.value else PSFIRST
		
		self.timer = eTimer()
		self.timer.callback.append(self.do)
		
		# Read XML file, parse it and instantiate configured plugins
		self.load()
		
		#TODO Run in a new thread


	######################################
	# Statemachine and timer
	def start(self):
		print "PushService start"
		self.stopTimer()
		
		self.begin()
		self.next()

	def stop(self):
		print "PushService stop"
		self.stopTimer()
		
		self.end()
		self.state = PSFIRST

	def next(self, state=None):
		if state:
			self.state = state
		print "PushService next", self.state
		
		if self.state == PSBOOT:
			self.startTimer(int(config.pushservice.bootdelay.value), PSBOOTRUN)
		
		elif self.state == PSBOOTRUN \
			or self.state == PSFIRST:
			cltime = config.pushservice.time.value
			lotime = localtime()
			ltime = lotime[3]*60 + lotime[4]
			ctime = cltime[0]*60 + cltime[1]
			seconds = 60 * abs(ctime - ltime)
			self.startTimer(seconds, PSFIRSTRUN)
		
		elif self.state == PSFIRSTRUN \
			or self.state == PSCYCLE:
			period = int(config.pushservice.period.value)
			if period > 0:
				self.startTimer(period*60*60, PSCYCLE)

	def do(self):
		self.run()
		self.next()

	def startTimer(self, seconds, state=None):
		if state:
			self.state = state
		self.timer.startLongTimer(seconds)

	def stopTimer(self):
		if self.timer.isActive():
			self.timer.stop()
