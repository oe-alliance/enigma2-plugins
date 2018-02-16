from Components.Sources.Source import Source
from enigma import eServiceCenter, eServiceReference
from Components.ParentalControl import LIST_BLACKLIST
from Components.config import config

class ProtectionSettings(Source):
	def __init__(self):
		Source.__init__(self)

	def getProtectionSettings(self):
		configured = config.ParentalControl.servicepinactive.value
		if configured:
			if config.ParentalControl.type.value == LIST_BLACKLIST:
				type = "0"
			else:
				type = "1"
			setuppin = config.ParentalControl.setuppin.value
			setuppinactive = config.ParentalControl.setuppinactive.value
		else:
			type = ""
			setuppin = ""
			setuppinactive = ""
		return [(configured,type,setuppinactive, setuppin)]

	def handleCommand(self, cmd):
		self.getProtectionSettings()

	list = property(getProtectionSettings)
	lut = {"Configured": 0, "Type": 1, "SetupPinActive": 2, "SetupPin": 3}			
