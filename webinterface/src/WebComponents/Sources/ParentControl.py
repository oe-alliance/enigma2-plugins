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

		if config.ParentalControl.servicepinactive.value:
			parentalControl.open()
			if config.ParentalControl.type.value == "whitelist":
				servicelist = parentalControl.whitelist
			else:
				servicelist = parentalControl.blacklist

			list = [(str(service_ref), ServiceReference(service_ref).getServiceName()) for service_ref in servicelist]
		else:
			list = []

		print "list", list
		return list

	list = property(command)
	lut = {"ServiceReference": 0
			, "ServiceName":1
			}

