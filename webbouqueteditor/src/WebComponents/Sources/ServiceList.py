from Components.Sources.Source import Source
from enigma import eServiceCenter, eServiceReference
from Components.ParentalControl import parentalControl, IMG_WHITESERVICE, IMG_WHITEBOUQUET, IMG_BLACKSERVICE, IMG_BLACKBOUQUET
from Components.config import config

class ServiceList(Source):
	def __init__(self, root, command_func = None, validate_commands = True):
		Source.__init__(self)
		self.root = root
		self.command_func = command_func
		self.validate_commands = validate_commands

	def getServicesAsList(self, format = "RN"):
		services = self.getServiceList()
		mylist = services and services.getContent(format, True)
		list = []
		for item in mylist:
			if item[0].flags & eServiceReference.isGroup:
				isGroup = "1"
			else:
				isGroup = "0"
			if item[0].flags & eServiceReference.isMarker:
				isMarker = "1"
			else:
				isMarker = "0"
			isProtected = "0"
			if config.ParentalControl.servicepinactive.value:
				protection = parentalControl.getProtectionType(item[0].toCompareString())
				if protection[0]:
					if protection[1] == IMG_BLACKSERVICE:
						#(locked -S-)
						isProtected = "1"
					elif protection[1] == IMG_BLACKBOUQUET:
						#(locked -B-)
						isProtected = "2"
					elif protection[1] == "":
						# (locked)
						isProtected = "3"
				else:
					if protection[1] == IMG_WHITESERVICE:
						#(unlocked -S-)
						isProtected = "4"
					elif protection[1] == IMG_WHITEBOUQUET:
						#(unlocked -B-)
						isProtected = "5"
					
			list.append((item[0].toString(),item[1],isGroup,isMarker,isProtected))
		return list

	def getServiceList(self):
		serviceHandler = eServiceCenter.getInstance()
		return serviceHandler.list(self.root)
		
	def getRoot(self):
		return self.__root

	def setRoot(self, root):
		assert isinstance(root, eServiceReference)
		self.__root = root
		self.changed()
		
	root = property(getRoot, setRoot)

	def validateReference(self, ref):
		return ref in self.getServicesAsList("S")

	def handleCommand(self, cmd):
		print "ServiceList handle command"
		if self.validate_commands and not self.validateReference(cmd):
			print "Service reference did not validate!"
			return
		ref = eServiceReference(cmd)
		if self.command_func:
			self.command_func(ref)

	list = property(getServicesAsList)
	lut = {"Reference": 0, "Name": 1, "isGroup": 2, "isMarker": 3, "isProtected": 4}			
