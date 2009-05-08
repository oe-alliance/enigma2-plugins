from Components.Sources.Source import Source
from Components.Harddisk import harddiskmanager

class Hdd(Source):
	def __init__(self, devicecount=0):
		Source.__init__(self)
		self.devicecount = devicecount

	def getHddData(self):
		if len(harddiskmanager.hdd) > 0:
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
			disk = [model, capacity, free]
			disks.append(disk)
		
		return disks
		
			
	list = property(getList)	
	lut = { "Model" : 0,
			"Capacity" : 1,
			"Free" : 2		
		}

	def destroy(self):
		Source.destroy(self)
