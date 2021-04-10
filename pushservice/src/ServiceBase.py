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

from ModuleBase import ModuleBase


# Service base class
class ServiceBase(ModuleBase):
	# You only have to overwrite the functions You need
	# If You don't have to save something, You don't need getOptions / setOptions
	
	UniqueCounter = 0
	
	ForceSingleInstance = True
	
	def __init__(self):
		ModuleBase.__init__(self)
		# Is called on instance creation
		ServiceBase.UniqueCounter += 1
		self.uniqueid = ServiceBase.UniqueCounter

	################################################
	# Base class functions
	@classmethod
	def forceSingle(cls):
		return cls.ForceSingleInstance

	@staticmethod
	def resetUniqueID():
		ServiceBase.UniqueCounter = 0

	################################################
	# Functions to be implemented in the plugin

	def push(self, callback, errback, pluginname, subject, body="", attachments=[]):
		# Will be called, if a plugin wants to send a notification
		# At the end a service has to call one of the functions: callback or errback
		errback("Not implemented: " + self.getName() + ".push()")

#	def test(self, plugin, subject, body="", attachments=[], callback=None, errback=None):
#		# Normally you don't have to overwrite this function
#		self.push(self, plugin, subject, body="", attachments=[], callback=None, errback=None)
