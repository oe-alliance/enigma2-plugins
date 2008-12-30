from Components.Sources.Source import Source
from ServiceReference import ServiceReference
from time import sleep

class SubServices(Source):
    
    def __init__(self, session):
        Source.__init__(self)        
        self.session = session
        
#        self.session.nav.event.append(self.checkSubservicesAvail) # we like to get service events
#
#    def checkSubservicesAvail(self, ev):
#        if ev == iPlayableService.evUpdatedEventInfo:
#            service = self.session.nav.getCurrentService()
#            subservices = service and service.subServices()
#            if subservices or subservices.getNumberOfSubservices() == 0:
#                self["SubserviceQuickzapAction"].setEnabled(False)
        
    def command(self):
        print "SubServices was called"
        list = []
        
        #sleep(5) # FIXMEEEEE very ugly code !! 
        
        list0 = []
        currentServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
        if currentServiceRef is not None:
            list.append( [currentServiceRef.toString(),
                         ServiceReference(currentServiceRef).getServiceName()] 
            )
            
            currentService = self.session.nav.getCurrentService()
            subservices = currentService and currentService.subServices()
            if subservices or subservices.getNumberOfSubservices() != 0:
                n = subservices and subservices.getNumberOfSubservices()
                for x in range(n):
                    sub = subservices.getSubservice(x)                    
                    list.append([sub.toString() , sub.getName()])
                
        else:
            list.append(["N/A", "N/A"])
        
        print "SubServices is returning list ",list
        return list
        
    list = property(command)
    lut = {"ServiceReference": 0
           ,"Name": 1
           }

