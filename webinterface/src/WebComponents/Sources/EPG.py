from Components.Sources.Source import Source
from ServiceReference import ServiceReference
from enigma import eServiceCenter, eServiceReference, eEPGCache

class EPG( Source):
    NOW=0
    NEXT=1
    SERVICE=2
    TITLE=3
    
    def __init__(self, navcore,func=NOW):
        self.func = func
        Source.__init__(self)        
        self.navcore = navcore
        self.epgcache = eEPGCache.getInstance()
        
    def handleCommand(self,cmd):
        self.command = cmd

    def do_func(self):
        if self.func is self.TITLE:
            func = self.searchEvent
        elif self.func is self.SERVICE:
            func = self.getEPGofService
        elif self.func is self.NOW:
            func = self.getEPGNow
        elif self.func is self.NEXT:
            func = self.getEPGNext
            
        return func(self.command)
    
    def getEPGNow(self,bouqetref):
        return self.getEPGNowNext(bouqetref)
    
    def getEPGNext(self, bouqetref):
        return self.getEPGNowNext(bouqetref, False)
    
    def getEPGNowNext(self, bouqetref, now=True):
        print "getting EPG NOW/NEXT", bouqetref
        serviceHandler = eServiceCenter.getInstance()
        list = serviceHandler.list(eServiceReference(bouqetref))
        services = list and list.getContent('S')
        
        search = ['IBDTSERN']
        for service in services:
            if now:
                search.append((service,0,-1))
            else:
                search.append((service,1,-1))        
        
        events = self.epgcache.lookupEvent(search);
        if events:
                return events
        else:
                return []
    
    def getEPGofService(self,cmd):
        print "getting EPG of Service", cmd
        events = self.epgcache.lookupEvent(['IBDTSERN',(cmd,0,-1,-1)]);
        if events:
                return events
        else:
                return []
    
    def searchEvent(self,cmd):
        print "getting EPG by title",cmd
        events = self.epgcache.search(('IBDTSERN',256,eEPGCache.PARTIAL_TITLE_SEARCH,cmd,1));
        if events:
            return events
        else:
            return []
        
    list = property(do_func)
    lut = {"EventID": 0, "TimeStart": 1,"Duration": 2, "Title": 3, "Description": 4, "DescriptionExtended": 5, "ServiceReference": 6, "ServiceName": 7 }

    