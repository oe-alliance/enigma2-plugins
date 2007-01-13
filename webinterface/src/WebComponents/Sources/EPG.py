from enigma import *

from Components.Sources.Source import Source
from ServiceReference import ServiceReference

class EPG( Source):
    NOWNEXT=0
    SERVICE=1
    TITLE=2
    
    def __init__(self, navcore,func=NOWNEXT):
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
        else:
            func = self.getEPGNowNext
            
        return func(self.command)
    
    def getEPGNowNext(self,cmd):
        print "getting EPG NOWNEXT", cmd
        events = self.epgcache.lookupEvent(['IBDTSERN',(cmd,0,0,-1)]);
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
    lut = {"EventID": 0, "TimeStart": 1,"Duration": 2, "Title": 3, "Description": 4, "DescriptionExtended": 5, "ServiceReference": 6, "ServiceName": 7}

    