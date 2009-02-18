from Components.Sources.Source import Source
from ServiceReference import ServiceReference
from enigma import eServiceCenter, eServiceReference, eEPGCache

class EPG( Source):
    BOUQUETNOW=0
    BOUQUETNEXT=1
    SERVICENOW=2
    SERVICENEXT=3
    SERVICE=4
    TITLE=5
    BOUQUET=6


    def __init__(self, navcore, func=BOUQUETNOW):
        self.func = func
        Source.__init__(self)        
        self.navcore = navcore
        self.epgcache = eEPGCache.getInstance()
        self.command = None
        
    def handleCommand(self, cmd):
        self.command = cmd

    def do_func(self):
        if not self.command is None:
            if self.func is self.TITLE:
                func = self.searchEvent
            elif self.func is self.SERVICE:
                func = self.getEPGofService
            elif self.func is self.BOUQUETNOW:
                func = self.getBouquetEPGNow
            elif self.func is self.BOUQUETNEXT:
                func = self.getBouquetEPGNext
            elif self.func is self.BOUQUET:
                func = self.getEPGofBouquet
            elif self.func is self.SERVICENOW:
                func = self.getServiceEPGNow
            elif self.func is self.SERVICENEXT:
                func = self.getServiceEPGNext
            
            return func(self.command)
        else:
            return []
    
    def getBouquetEPGNow(self, ref):
        return self.getEPGNowNext(ref)
    
    def getBouquetEPGNext(self, ref):
        return self.getEPGNowNext(ref, False)
    
    def getServiceEPGNow(self, ref):
        return self.getEPGNowNext(ref, True, True)
    
    def getServiceEPGNext(self, ref):
        return self.getEPGNowNext(ref, False, True)
    
    def getEPGNowNext(self, ref, now=True, service=False):
        print "[WebComponents.EPG] getting EPG NOW/NEXT", ref

        if service:
            search = ['IBDTSERNX']
            if now:
                search.append((ref, 0, -1))
            else:
                search.append((ref, 1, -1))
               
            events = self.epgcache.lookupEvent(search)
            if events:
                return events
                
        else:
            serviceHandler = eServiceCenter.getInstance()
            list = serviceHandler.list(eServiceReference(ref))
            services = list and list.getContent('S')
            search = ['IBDTSERN']
            
            if len(services) > 0: # It's a Bouquet
                for service in services:
                    if now:
                        search.append((service,0,-1))
                    else:
                        search.append((service,1,-1))
         
            
            events = self.epgcache.lookupEvent(search)
            if events:
                return events

        return []
        
    
    def getEPGofService(self, ref, options = 'IBDTSERN'):
        print "getting EPG of Service", ref
        events = self.epgcache.lookupEvent([options ,(ref,0,-1,-1)]);
        if events:
                return events
        else:
                return []
    
    def getEPGofBouquet(self, bouqetref):
        print "[WebComponents.EPG] getting EPG for Bouquet", bouqetref
        
        serviceHandler = eServiceCenter.getInstance()
        sl = serviceHandler.list(eServiceReference(bouqetref))
        services = sl and sl.getContent('S')
        
        search = ['IBDTSERN']
        
        for service in services:
            search.append((service,0,-1,-1))
        
        events = self.epgcache.lookupEvent(search)
        
        if events:
            return events
        else:
            return []
        
        
    def searchEvent(self, cmd):
        print "[WebComponents.EPG] getting EPG by title",cmd
        events = self.epgcache.search(('IBDTSERN',256,eEPGCache.PARTIAL_TITLE_SEARCH,cmd,1));
        if events:
            return events
        else:
            return []
        
    list = property(do_func)
    lut = {"EventID": 0, "TimeStart": 1,"Duration": 2, "Title": 3, "Description": 4, "DescriptionExtended": 5, "ServiceReference": 6, "ServiceName": 7 }

    