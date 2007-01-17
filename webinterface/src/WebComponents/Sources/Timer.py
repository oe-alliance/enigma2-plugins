from enigma import *
from enigma import eServiceReference 

from Components.Sources.Source import Source
from ServiceReference import ServiceReference
from RecordTimer import RecordTimerEntry, RecordTimer, AFTEREVENT,parseEvent

import time

class Timer( Source):
    LIST = 0
    ADDBYID = 1
    ADD = 2
    def __init__(self, session,func = LIST):
        self.func = func
        Source.__init__(self)        
        self.session = session
        self.recordtimer = session.nav.RecordTimer
        
    def handleCommand(self,cmd):
        if self.func is self.ADDBYID:
            self.result = self.addTimerByEventID(cmd)
        elif self.func is self.ADD:
            self.result = self.addTimer(cmd)
        else:
            self.result = False,"unknown command"
    
    def addTimer(self,param):
        # is there an easier and better way? :\ 
        print "addTimerByEventID",param
        if param['serviceref'] is None:
            return False,"ServiceReference missing"
        else: 
            serviceref = ServiceReference(param['serviceref'])
        
        if param['begin'] is None:
           return False,"begin missing"
        elif time.time() <= float(param['begin']):
            begin = float(param['begin'])
        else:
            return False,"incorrect time begin"
            
        
        if param['end'] is None:
            return False,"end missing"
        elif begin < float(param['end']):
            end = float(param['end'])
        else:
             return False,"incorrect time end"
                
        if param['name'] is None:
            return False,"name is missing"
        else:
            name = param['name']
            
        if param['description'] is not None:
            description = param['description']
        else: 
            description = ""
            
        if param['disabled'] =="0":
            disabled = False
        elif param['disabled'] =="1":
            disabled = True
        else:
            return False,"disabled incorrect"
        
        if param['justplay'] == "0":
            justplay = False
        elif param['justplay'] == "1":
            justplay = True
        else:
            return False,"justplay incorrect"
            
        if param['afterevent'] == "0":
            afterevent = 0
        elif param['afterevent'] == "1":
            afterevent = 1
        elif param['afterevent'] == "2":
            afterevent = 2
        else:
            return False,"afterevent incorrect"
            
        newtimer = RecordTimerEntry(serviceref, begin, end, name, description, 0, disabled, justplay, afterevent)
        self.session.nav.RecordTimer.record(newtimer)
        #self.session.nav.RecordTimer.saveTimer()
        return True,"Timer added"        

    def addTimerByEventID(self,param):
        print "addTimerByEventID",param['serviceref'],param['eventid']
        if param['serviceref'] is None:
            return False,"ServiceReference not set"
        if param['eventid'] is None:
            return False,"Eventid not set"
        epgcache = eEPGCache.getInstance()
        event = epgcache.lookupEventId(eServiceReference(param['serviceref']),int(param['eventid']))
        if event is None:
            return False,"Eventid not found"
        (begin, end, name, description, eit) =parseEvent(event)
        newtimer = RecordTimerEntry(ServiceReference(param['serviceref']), begin, end, name, description, eit, False, False, AFTEREVENT.NONE)
        self.session.nav.RecordTimer.record(newtimer)
        return True,"Timer added"    
            
    def getText(self):    
        (result,text) = self.result
        xml = "<?xml version=\"1.0\"?>\n"
        xml  += "<e2timeraddresult>\n"
        if result:
            xml += "<e2state>True</e2state>\n"
        else:
            xml += "<e2state>False</e2state>\n"            
        xml += "<e2statetext>%s</e2statetext>\n"%text
        xml += "</e2timeraddresult>\n"
        return xml
    
    text = property(getText)    
    
    ## part for listfiller requests
    def command(self):
        timerlist = []
        for item in self.recordtimer.timer_list+self.recordtimer.processed_timers:
            timer = []
            timer.append(item.service_ref)
            timer.append(item.service_ref.getServiceName())
            timer.append(item.eit)
            timer.append(item.name)
            timer.append(item.description)
            timer.append(item.disabled)
            timer.append(item.begin)
            timer.append(item.end)
            timer.append(item.end-item.begin)
            timer.append(item.start_prepare)
            timer.append(item.justplay)
            timer.append(item.afterEvent)
            timer.append(item.log_entries)
            try: 
                timer.append(item.Filename)
            except AttributeError:
                timer.append("")
            
            timer.append(item.backoff)       
            try:
                timer.append(item.next_activation)
            except AttributeError:
                timer.append("")
            timer.append(item.first_try_prepare)  
            timer.append(item.state)  
            timer.append(item.repeated)
            timer.append(item.dontSave)
            timer.append(item.cancelled)
            timerlist.append(timer) 
            
        return timerlist
    
    list = property(command)
    lut = {"ServiceReference": 0
           ,"ServiceName": 1
           ,"EIT":2
           ,"Name":3
           ,"Description":4
           ,"Disabled":5
           ,"TimeBegin":6
           ,"TimeEnd":7
           ,"Duration":8
           ,"startPrepare":9
           ,"justPlay":10
           ,"afterEvent":11
           ,"LogEntries":12
           ,"Filename":13
           ,"Backoff":14
           ,"nextActivation":15
           ,"firstTryPrepare":16
           ,"State":17
           ,"Repeated":18
           ,"dontSave":19
           ,"Cancled":20
           }

