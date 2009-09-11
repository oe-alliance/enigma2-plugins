from Components.Sources.Source import Source
from Components.ParentalControl import parentalControl
from Components.config import config
from ServiceReference import ServiceReference

class ParentControl(Source):
	def __init__(self, session):
		Source.__init__(self)
		self.session = session

	def command(self):
		print "ParentControl was called"
		list = []

		if config.ParentalControl.configured.value:
			parentalControl.open()
			servicelist = None
			if config.ParentalControl.type.value == "whitelist":
				servicelist = parentalControl.whitelist
			else:
				servicelist = parentalControl.blacklist

			for service_ref in servicelist:
				list.append((str(service_ref), ServiceReference(service_ref).getServiceName()))

		print "list", list
		return list

	list = property(command)
	lut = {"ServiceReference": 0
			, "ServiceName":1
			}

