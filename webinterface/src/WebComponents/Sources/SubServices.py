from enigma import *
from Components.Sources.Source import Source
from enigma import eServiceReference, iServiceInformation

from ServiceReference import ServiceReference
import time

class SubServices( Source):
    
    def __init__(self, session):
        Source.__init__(self)        
        self.session = session
        
    def command(self):
        print "SubServices was called"
        list = []
        
        time.sleep(5)
        
        list0 = []
        currentService = self.session.nav.getCurrentlyPlayingServiceReference()
        if currentService is not None:
            list0.append(currentService.toString())
            list0.append( ServiceReference(currentService).getServiceName() )
            list.append(list0)
        else:
            list0.append("N/A")
            list0.append("N/A")
            list.append(list0)

        service = self.session.nav.getCurrentService()
        subservices = service and service.subServices()
        if subservices or subservices.getNumberOfSubservices() != 0:
            n = subservices and subservices.getNumberOfSubservices()
            for x in range(n):
                list1 = []
                sub = subservices.getSubservice(x)
                list1.append(sub.toString())
                list1.append(sub.getName())
                list.append(list1)
        
        print "SubServices is returning list ",list
        return list
        
    list = property(command)
    lut = {"ServiceReference": 0
           ,"Name": 1
           }

