from Components.Sources.Source import Source
from Plugins.Extensions.WebInterface.WebChilds import Toplevel

class External(Source):
	def getList(self):
		l = []
		append = l.append
		for child in Toplevel.externalChildren:
			Len = len(child)
			if Len == 5:
				child = (child[0], child[2], child[3], child[4])
			elif Len == 4:
				child = (child[0], child[2], child[3], False)
			elif Len == 3:
				child = (child[0], child[2], "unknown", False)
			elif Len == 2:
				child = (child[0], child[0], "unknown", False)
			else:
				continue
			append(child)
		return l

	list = property(getList)
	lut = {
				"Path":0,
				"Name":1,
				"Version":2,
				"HasGUI":3
	}
