from Components.Sources.Source import Source
from ServiceReference import ServiceReference
#from time import sleep

class SubServices(Source):
	def __init__(self, session, streamingScreens = None):
		Source.__init__(self)
		self.session = session
		self.streamingScreens = streamingScreens
		self.cmd = None
	
	def handleCommand(self, cmd):
		if cmd is not None:
			print "[SubServices].handleCommand %s" %cmd
			self.cmd = cmd
	
	def getSubservices(self):
		print "[SubServices].getSubservices called"
		list = []
		
		if self.streamingScreens is None:
			currentServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
			if currentServiceRef is not None:
				list.append([currentServiceRef.toString(),
							 ServiceReference(currentServiceRef).getServiceName()]
							 )
	
				currentService = self.session.nav.getCurrentService()
				subservices = currentService and currentService.subServices()
				if subservices or subservices.getNumberOfSubservices() != 0:
					n = subservices and subservices.getNumberOfSubservices()
					for x in range(n):
						sub = subservices.getSubservice(x)
						list.append([sub.toString(), sub.getName()])
	
			else:
				list.append(["N/A", "N/A"])
	
			print "SubServices is returning list ", list
			return list
		
		elif self.cmd is not None:
			print "[SubServices].getSubservices for Streaming Service"
			for screen in self.streamingScreens:
				if screen is not None:
					service = screen.getRecordService()
					sref = ServiceReference(screen.getRecordServiceRef())						
					if service is not None:						
						print "[SubServices] serviceref: %s | cmd: %s" %(sref, self.cmd)
						
						if sref.__str__() == self.cmd:
							list.append([sref.__str__(), sref.getServiceName()])
							print "[SubServices] Matching recordSerivce found!"
							subservices = service and service.subServices()
							if subservices or subservices.getNumberOfSubservices() != 0:
								n = subservices and subservices.getNumberOfSubservices()
								for x in range(n):
									sub = subservices.getSubservice(x)
									list.append([sub.toString(), sub.getName()])
								
								return list
							else:
								print "[SubServices] no items: %s" %subservices
					else:
						print "[SubServices] Service is None!"
		if len(list) == 0:
			list.append(["N/A", "N/A"])

		return list
	
	list = property(getSubservices)
	lut = {"ServiceReference": 0,
			"Name": 1
			}

