from __future__ import print_function
from __future__ import absolute_import
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

from Components.config import ConfigYesNo, NoSave

try:
	#Python >= 2.7
	from collections import OrderedDict
except:
	from .OrderedDict import OrderedDict


# Module base class
class ModuleBase(object):

	def __init__(self):
		# Is called on instance creation
		
		# Default configuration
		self.enable = NoSave(ConfigYesNo( default = False ))
		
		self.options = OrderedDict()
		
		# Build a list of key-value string tuples
		# [ (key, value, description, config element) , ]
		#self.options['enabled'] = ConfigYesNo( default = False )


	################################################
	# Base classmethod functions
	@classmethod
	def getClass(cls):
		# Return the Class
		return cls.__name__


	################################################
	# Base functions
	def getName(self):
		# Return the Class Name
		return self.__class__.__name__

	def getNameId(self):
		return self.getName() + " (" + str(self.getUniqueID()) + ")"

	def getValue(self, key):
		if key in self.options:
			return self.options[key][0].value
		else:
			return None

	def setValue(self, key, value):
		self.options[key][0].value = value

	def getOption(self, key):
		if key in self.options:
			return self.options[key]
		else:
			return None

	def setOption(self, key, option, description):
		self.options[key] = ( option, description )

	def setOptions(self, options):
		# Parse a list of key-value string tuples
		# [ (key, value) , ]
		# If something is missing, the last/default value is used
		for key, value in options:
			try:
				default = self.getValue(key)
				if isinstance(default, str):
					self.setValue(key, value)
				elif isinstance(default, bool):
					self.setValue(key, eval(value))
				elif isinstance(default, int):
					self.setValue(key, int(value))
			except:
				print(_("PushService Module %s:\n") % ( self.getName() ))
				print(_("Skipping config option:") + str(key) + " " + str(value))
				continue

	def getUniqueID(self):
		return self.uniqueid

	def getEnable(self):
		return self.enable.value

	def setEnable(self, enable):
		self.enable.value = enable

	def getConfigEnable(self):
		return self.enable

	def getStringEnable(self):
		return str(self.enable.value)

	def getStringOptions(self):
		return [ ( str(key), str(option.value), str(description) ) for ( key, ( option, description ) ) in list(self.options.items()) ]

	def getConfigOptions(self):
		return [ ( key, option, description) for ( key, ( option, description ) ) in list(self.options.items()) ]


	################################################
	# Functions to be implemented in the plugin
	def begin(self):
		# Is called after starting PushSerive
		pass

	def end(self):
		# Is called after stopping PushSerive
		pass

	def cancel(self):
		# Cancel activities
		pass
