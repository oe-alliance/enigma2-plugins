from Components.Sources.Source import Source
from Components.config import config

class LocationsAndTags(Source):
	CURRLOCATION = 0
	LOCATIONS = 1
	TAGS = 2

	def __init__(self, session, func):
		self.func = func
		Source.__init__(self)
		self.session = session
		self.result = [ False, "one two three four unknown command" ]

	def handleCommand(self, cmd):
		if self.func is self.CURRLOCATION:
			self.result = self.getCurrentLocation()
		elif self.func is self.LOCATIONS:
			self.result = self.getLocations()
		elif self.func is self.TAGS:
			self.result = self.getTags()
		else:
			self.result = False

	def getCurrentLocation(self):
		return config.movielist.last_videodir.value

	def getLocations(self):
		return config.movielist.videodirs.value

	def getTags(self):
		try:
			file = open("/etc/enigma2/movietags")
			tags = [x.rstrip() for x in file.readlines()]
			while "" in tags:
				tags.remove("")
			file.close()
		except IOError, ioe:
			tags = []
		return tags

	def getText(self):
		self.handleCommand(None)

		if self.result:
			return str(self.result)
		else:
			return ""

	def getList(self):
		self.handleCommand(None)
		list = self.result
		if list is None:
			list = []
		
		return list

	text = property(getText)
	simplelist = property(getList)
