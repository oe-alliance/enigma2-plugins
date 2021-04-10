from __future__ import print_function
from Components.Sources.Source import Source
from Components.config import config
from Tools.Directories import resolveFilename, SCOPE_CONFIG, SCOPE_HDD
import os

class LocationsAndTags(Source):
	CURRLOCATION = 0
	LOCATIONS = 1
	TAGS = 2
	ADDLOCATION = 3
	REMOVELOCATION = 4

	def __init__(self, session, func):
		self.func = func
		Source.__init__(self)
		self.session = session
		self.result = (False, _("one two three four unknown command"))

	def handleCommand(self, cmd):
		if self.func is self.CURRLOCATION:
			self.result = self.getCurrentLocation()
		elif self.func is self.LOCATIONS:
			self.result = self.getLocations()
		elif self.func is self.TAGS:
			self.result = self.getTags()
		elif self.func is self.ADDLOCATION:
			self.result = self.addLocation(cmd)
		elif self.func is self.REMOVELOCATION:
			self.result = self.removeLocation(cmd)
		else:
			self.result = False

	def getCurrentLocation(self):
		if config.movielist.last_videodir.value and os.path.exists(config.movielist.last_videodir.value):
			return config.movielist.last_videodir.value
		return resolveFilename(SCOPE_HDD)

	def getLocations(self):
		return config.movielist.videodirs.value

	def getTags(self):
		try:
			file = open(resolveFilename(SCOPE_CONFIG, "movietags"))
			tags = [x.rstrip() for x in file]
			while "" in tags:
				tags.remove("")
			file.close()
		except IOError as ioe:
			tags = ()
		return tags

	def addLocation(self, param):
		print("[WebComponents.LocationsAndTags] addLocation: ", param)
		if param['dirname'] is None:
			return (False, "Missing Parameter: dirname")
		dirname = param['dirname']
		if len(dirname) == 0:
			return (False, "Missing value for parameter dirname")
		if not dirname.endswith("/"):
			dirname += "/"
		if not os.path.exists(dirname):
			createFolder = False
			if param['createFolder'] is not None:
				if param['createFolder'] == "1":
					try:
						createFolder = True
						os.makedirs(dirname)
					except OSError:
						return (False, _("Path %s can not be created") % (dirname))
			if not createFolder:
				return (False, _("Path %s does not exist") % (dirname))
		bookmarks = config.movielist.videodirs.value[:] or []
		if dirname in bookmarks:
			return (False, _("Location '%s' is already existing") % (dirname))
		bookmarks.append(dirname)
		config.movielist.videodirs.value = bookmarks
		config.movielist.videodirs.save()
		return (True, _("Location '%s' added successfully") % (dirname))

	def removeLocation(self, param):
		print("[WebComponents.LocationsAndTags] removeLocation: ", param)
		if len(param) == 0:
			return (False, _("Missing value for parameter dirname"))
		dirname = param
		if not dirname.endswith("/"):
			dirname += "/"
		bookmarks = config.movielist.videodirs.value[:] or []
		if dirname in bookmarks:
			bookmarks.remove(dirname)
			config.movielist.videodirs.value = bookmarks
			config.movielist.videodirs.save()
			return (True, _("Location '%s' removed successfully") % (dirname))
		else:
			return (False, _("Location '%s' does not exist") % (dirname))

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
			list = ()

		return list

	text = property(getText)
	simplelist = property(getList)
