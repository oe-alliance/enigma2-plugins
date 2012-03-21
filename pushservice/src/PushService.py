'''
Created on 06.11.2011

@author: Frank Glaser
'''


import os
import sys, traceback

from Components.config import *
from enigma import eTimer
from time import localtime, strftime


# Plugin internal
from . import _
from PushServiceBase import PushServiceBase


#######################################################
# Logical part
class PushService(PushServiceBase):

	def __init__(self):
		PushServiceBase.__init__(self)
		
		self.plugins = []
		
		self.state = "First"
		self.timer = eTimer()
		self.timer.callback.append(self.go)

	def start(self, state = None):
		if self.timer.isActive():
			self.timer.stop()
		
		# Read XML file, parse it and instantiate configured plugins
		plugins = self.load()
		if plugins:
			self.plugins = plugins
		
		self.begin(self.plugins)
		
		self.next(state)

	def next(self, state = None):
		#TODO Start run in a new thread !!!!!!!!!
		# Override statemachine
		if state: self.state = state
		
		if self.state == "Now":
			self.state = "First"
			self.go()
		
		if self.state == "Boot":
			self.state = "First"
			self.timer.startLongTimer( 10 )
		
		elif self.state == "First":
			self.state = "Period"
			cltime = config.pushservice.time.value
			lotime = localtime()
			ltime = lotime[3]*60 + lotime[4]
			ctime = cltime[0]*60 + cltime[1]
			seconds = 60 * abs(ctime - ltime)
			self.timer.startLongTimer( seconds )
		
		elif self.state == "Period":
			period = config.pushservice.period.value
			if period > 0:
				self.timer.startLongTimer( int(period)*60*60 )

	def stop(self):
		# Stop Timer
		if self.timer.isActive():
			self.timer.stop()
		self.state = "First"
		self.end(self.plugins)

	def go(self):
		self.run(self.plugins)
		self.next()
