from Components.Sources.Source import Source
from Components.NimManager import nimmanager


class Frontend(Source):
	def getList(self):
		return [nim.split(":") for nim in nimmanager.nimList()]

	list = property(getList)
	lut = {
		"Name": 0,
		"Type": 1
	}
