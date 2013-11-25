# -*- coding: utf-8 -*-
#
# EventPosition - Converter
#
# Coded by Dr.Best (c) 2013
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Multimedia GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Multimedia GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Multimedia GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#

from Converter import Converter
from Poll import Poll
from Components.Element import cached
from time import time

class EventPosition(Poll, Converter, object):
	def __init__(self, type):
		Poll.__init__(self)
		Converter.__init__(self, type)
		self.poll_interval = 30*1000
		self.poll_enabled = True

	@cached
	def getPosition(self):
		event = self.source.event
		if event is None:
			return None
		now = int(time())
		start_time = event.getBeginTime()
		duration = event.getDuration()
		if start_time <= now <= (start_time + duration) and duration > 0:
			return now - start_time
		else:
			return 0

	@cached
	def getLength(self):
		event = self.source.event
		if event is None:
			return None
		start_time = event.getBeginTime()
		duration = event.getDuration()
		end_time = start_time + duration
		return duration

	@cached
	def getCutlist(self):
		return []


	position = property(getPosition)
	length = property(getLength)
	cutlist = property(getCutlist)


	def changed(self, what):
		if what[0] != self.CHANGED_CLEAR:
			self.downstream_elements.changed(what)
			if len(self.downstream_elements):
				if not self.source.event and self.downstream_elements[0].visible:
					self.downstream_elements[0].visible = False
				elif self.source.event and not self.downstream_elements[0].visible:
					self.downstream_elements[0].visible = True
