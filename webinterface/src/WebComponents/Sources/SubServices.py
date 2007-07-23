from Components.Sources.Source import Source
from ServiceReference import ServiceReference
from time import sleep

class SubServices(Source):
    
    def __init__(self, session):
        Source.__init__(self)        
        self.session = session
        
    def command(self):
        print "SubServices was called"
        list = []
        
        sleep(5) # FIXMEEEEE very ugly code !! 
        
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

