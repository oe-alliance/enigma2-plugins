from Components.config import ConfigYesNo, NoSave

# Plugin base class
class PluginBase(object):
	# You only have to overwrite the functions You need
	# If You don't have to save something, You don't need getOptions / setOptions
	
	UniqueCounter = 0
	
	ForceSingleInstance = True
	
	def __init__(self):
		# Is called on instance creation
		
		# Default configuration
		self.enable = NoSave(ConfigYesNo( default = False ))
		
		PluginBase.UniqueCounter += 1
		self.uniqueid = PluginBase.UniqueCounter
		
		#self.activation = eTimer()
		
		self.options = {}
		# Build a list of key-value string tuples
		# [ (key, value, description, config element) , ]
		#self.options['enabled'] = ConfigYesNo( default = False )

	################################################
	# Base class functions
	def getName(self):
		# Return the Plugin Name
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
			default = self.getValue(key)
			if type(default) is str:
				self.setValue(key, value)
			elif type(default) is bool:
				self.setValue(key, eval(value))
			elif type(default) is int:
				self.setValue(key, int(value))

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
		return [ ( str(key), str(option.value), str(description) ) for ( key, ( option, description ) ) in self.options.items() ]

	def getConfigOptions(self):
		return [ ( key, option, description) for ( key, ( option, description ) ) in self.options.items() ]

	@classmethod
	def getPluginClass(cls):
		# Return the Plugin Class
		return cls
	
	@classmethod
	def forceSingle(cls):
		return cls.ForceSingleInstance

	@staticmethod
	def resetUniqueID():
		PluginBase.UniqueCounter = 0

	################################################
	# Functions to be implemented in the plugin

	def begin(self):
		# Is called after starting PushSerive
		pass

	def run(self):
		# Return Header, Body, Attachment
		# If empty or none is returned, nothing will be sent
		return [], [], []

	def end(self):
		# Is called after stopping PushSerive
		pass

	# Callback functions
	def success(self):
		# Called after successful sending the message
		pass

	def error(self):
		# Called after message sent has failed
		pass
