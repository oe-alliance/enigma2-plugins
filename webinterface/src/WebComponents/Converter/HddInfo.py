from Components.Converter.Converter import Converter

class HddInfo(Converter):
	MODEL = 0
	CAPACITY = 1
	FREE = 2

	def __init__(self, type):
		Converter.__init__(self, type)

		self.type = {
					 "Model" : self.MODEL,
					 "Capacity" : self.CAPACITY,
					 "Free" : self.FREE,
					 }[type]

	def getText(self):
		hdd = self.source.hdd

		if hdd is not None:
			if self.type == self.MODEL:
				return "%s" % hdd.model()
			elif self.type == self.CAPACITY:
				return "%s" % hdd.capacity()
			elif self.type == self.FREE:
				if hdd.free() > 1024:
					free = float(hdd.free()) / float(1024)
					return "%.3f GB" % free
				else:
					return "%i MB" % hdd.free()

		return _("N/A")

	text = property(getText)

