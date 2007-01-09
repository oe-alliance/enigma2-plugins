from enigma import *

from Source import Source
from ServiceReference import ServiceReference

class EPG( Source):
    def __init__(self, navcore):
        Source.__init__(self)
        self.navcore = navcore
        self.epgcache = eEPGCache.getInstance()
    def handleCommand(self,cmd):
        print "EPG.handleCommand %s" %cmd   
        self.command = cmd

    def getEPGNowNext(self):
        print "getting EPG of Service ",self.command
        events = self.epgcache.lookupEvent(['IBDTSERN',(self.command,0,0,-1)]);
        if events:
                return self.convertToDictonary(events[:2])
        else:
                return False
    
    def getEPGofService(self):
        print "getting EPG of Service ",self.command
        events = self.epgcache.lookupEvent(['IBDTSERN',(self.command,0,-1,-1)]);
        if events:
                return self.convertToDictonary(events)
        else:
                return False
    
    def searchEvent(self):
        print "searchEvent",self.command
        events = self.epgcache.search(('IBDTSERN',1024,eEPGCache.PARTIAL_TITLE_SEARCH,self.command,1));
        if events:
            return self.convertToDictonary(events)
        else:
            return False
    def convertToDictonary(self,EventList):
        result=[]
        for x in EventList:
            row = {}                        
            row['EventID']=self.convertIfEmpty(x[0])
            row['TimeStart']=self.convertIfEmpty(x[1])
            row['Duration']=self.convertIfEmpty(x[2])
            row['Title']=self.convertIfEmpty(x[3])
            row['Description']=self.convertIfEmpty(x[4])
            row['DescriptionExtended']=self.convertIfEmpty(x[5])
            row['ServiceReference']=self.convertIfEmpty(x[6])
            row['ServiceName']=self.convertIfEmpty(x[7])
            result.append(row)                                    
        return result
    def convertIfEmpty(self,string):
        if string == "":
            return "N/A"
        else:
            return string.__str__()
    epg = property(searchEvent,getEPGofService,getEPGNowNext)    