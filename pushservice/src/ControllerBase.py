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


# Plugin base class
class ControllerBase(ModuleBase):
	# You only have to overwrite the functions You need
	# If You don't have to save something, You don't need getOptions / setOptions
	
	UniqueCounter = 0
	
	ForceSingleInstance = True
	
	def __init__(self):
		ModuleBase.__init__(self)
		# Is called on instance creation
		ControllerBase.UniqueCounter += 1
		self.uniqueid = ControllerBase.UniqueCounter


	################################################
	# Base class functions
	@classmethod
	def forceSingle(cls):
		return cls.ForceSingleInstance

	@staticmethod
	def resetUniqueID():
		ControllerBase.UniqueCounter = 0


	################################################
	# Functions to be implemented in the plugin
	def run(self, callback, errback):
		# At the end a plugin has to call one of the functions: callback or errback
		# Callback should return with at least one of the parameter: Header, Body, Attachment
		# If empty or none is returned, nothing will be sent
		errback("Not implemented: " + self.getName() + ".run()")

	# Callback functions
	def callback(self):
		# Called after all services succeded
		pass

	def errback(self):
		# Called after all services has returned, but at least one has failed
		pass

#	def test(self):
#		# Normally you don't have to overwrite this function
#		self.run(self)
