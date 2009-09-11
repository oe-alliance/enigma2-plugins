from Components.Sources.Source import Source
from Components.Harddisk import harddiskmanager

class Hdd(Source):
	def __init__(self, devicecount=0):
		Source.__init__(self)
		self.devicecount = devicecount

	def getHddData(self):
		if harddiskmanager.hdd:
			return harddiskmanager.hdd[0]
		else:
			return None

	hdd = property(getHddData)

	def getList(self):
		disks = []
		for hdd in harddiskmanager.hdd:
			model = "%s" % (hdd.model())
			capacity = "%s" % (hdd.capacity())

			if hdd.free() <= 1024:
				free = "%i MB" % (hdd.free())
			else:
				free = float(hdd.free()) / float(1024)
				free = "%.3f GB" % free
			disks.append((model, capacity, free))

		return disks

	list = property(getList)
	lut = { "Model" : 0,
			"Capacity" : 1,
			"Free" : 2
		}

