from Components.Sources.Source import Source
from Components.NimManager import nimmanager

class Frontend(Source, object):
	def __init__(self):
		Source.__init__(self)

	def getList(self):
		nims = []
		for nim in nimmanager.nimList():
			info = nim.split(":")
			nims.append((
						info[0],
						info[1]
					))
		return nims

	list = property(getList)
	lut = {
		"Name" : 0,
		"Type" : 1
	}
