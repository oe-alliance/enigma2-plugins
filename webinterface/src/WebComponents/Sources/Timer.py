from enigma import *
from enigma import eServiceReference 
from enigma import eServiceCenter

from Components.Sources.Source import Source
from ServiceReference import ServiceReference
from RecordTimer import RecordTimerEntry, RecordTimer, AFTEREVENT,parseEvent

import time, string
# import sys, traceback

class Timer( Source):
    LIST = 0
    ADDBYID = 1
    ADD = 2
    DEL = 3
    TVBROWSER = 4
    
    def __init__(self, session,func = LIST):
        self.func = func
        Source.__init__(self)        
        self.session = session
        self.recordtimer = session.nav.RecordTimer
        self.epgcache = eEPGCache.getInstance()

    def handleCommand(self,cmd):
        if self.func is self.ADDBYID:
            self.result = self.addTimerByEventID(cmd)
        elif self.func is self.ADD:
            self.result = self.addTimer(cmd)
        elif self.func is self.TVBROWSER:
            self.result = self.tvBrowser(cmd)
        elif self.func is self.DEL:
            self.result = self.delTimer(cmd)
        else:
            self.result = False,"unknown command"

    def delTimer(self,param):
        # is there an easier and better way? :\ 
        print "delTimer",param
        
        if param['serviceref'] is None:
            return False,"ServiceReference missing"
        else: 
            serviceref = ServiceReference(param['serviceref'])
        
        if param['begin'] is None:
           return False,"begin missing"
        else:
            begin = float(param['begin'])
        
        if param['end'] is None:
            return False,"end missing"
        else:
        	end = float(param['end'])
             
        toDelete = None
        try:
            print "timer_list ", self.recordtimer.timer_list
            print "processed_timers", self.recordtimer.processed_timers
            for x in self.recordtimer.timer_list + self.recordtimer.processed_timers:
                print "x.begin(%s), x.end(%s), x.service_ref(%s)" % (x.begin, x.end, x.service_ref)
                if str(x.service_ref) == str(serviceref) and float(x.begin) == begin and float(x.end) == end:
	        	          toDelete = x
        except:
            print "Fehler\n"
            
        if toDelete is not None:
        	self.recordtimer.removeEntry(toDelete)
        	return True,"Timer removed"
        else:
        	return False,"Timer not found"
        	print "Timer not found"
        
        #self.session.nav.RecordTimer.saveTimer()
    def tvBrowser(self,param):
        print "addTimerByEventID",param
        
        syear = 0
        if param['syear'] is None:
           return False,"syear missing"
        else:
            syear = int(param['syear'])
        
        smonth = 0
        if param['smonth'] is None:
           return False,"smonth missing"
        else:
            smonth = int(param['smonth'])
        
        sday = 0
        if param['sday'] is None:
           return False,"sday missing"
        else:
            sday = int(param['sday'])
        
        shour = 0
        if param['shour'] is None:
           return False,"shour missing"
        else:
            shour = int(param['shour'])
        
        smin = 0
        if param['smin'] is None:
           return False,"smin missing"
        else:
            smin = int(param['smin'])
            
        eyear = 0
        if param['eyear'] is None:
           return False,"eyear missing"
        else:
            eyear = int(param['eyear'])
        
        emonth = 0
        if param['emonth'] is None:
           return False,"emonth missing"
        else:
            emonth = int(param['emonth'])
        
        eday = 0
        if param['eday'] is None:
           return False,"eday missing"
        else:
            eday = int(param['eday'])
        
        ehour = 0
        if param['ehour'] is None:
           return False,"ehour missing"
        else:
            ehour = int(param['ehour'])
        
        emin = 0
        if param['emin'] is None:
           return False,"emin missing"
        else:
            emin = int(param['emin'])
        
        # for compatibility reasons
        if param['serviceref'] is None:
            return False,"ServiceReference missing"
        else:
            takeApart = string.split(param['serviceref'], '|')
            if len(takeApart) > 1:
                param['serviceref'] = takeApart[1]

        param['begin'] = int( time.strftime("%s",  time.localtime(time.mktime( (syear, smonth, sday, shour, smin, 0, 0, 0, 0) ) ) ) )
        param['end']   = int( time.strftime("%s",  time.localtime(time.mktime( (eyear, emonth, eday, ehour, emin, 0, 0, 0, 0) ) ) ) )
        
        if param['command'] == "add":
            return self.addTimer(param)
        elif param['command'] == "del":
            return self.delTimer(param)
        else:
            return False,"command missing"
        
    def addTimer(self,param):
        # is there an easier and better way? :\ 
        print "addTimer",param
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
        self.recordtimer.record(newtimer)
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
        justplay = False
        if param['justplay'] is None and param['justplay'] == "True":
            justplay = True
        
        newtimer = RecordTimerEntry(ServiceReference(param['serviceref']), begin, end, name, description, eit, False, justplay, AFTEREVENT.NONE)
        self.recordtimer.record(newtimer)
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
#        print "len(self.recordtimer.timer_list) ", len(self.recordtimer.timer_list)
 #       print "timer_list ", self.recordtimer.timer_list
  #      print "processed_timers", self.recordtimer.processed_timers
#        try:
        for item in self.recordtimer.timer_list + self.recordtimer.processed_timers:
            timer = []
            timer.append(item.service_ref)
            timer.append(item.service_ref.getServiceName())
            timer.append(item.eit)
            timer.append(item.name)
            timer.append(item.description)
            timer.append(item.disabled)
            timer.append(item.begin)
            timer.append(item.end)
            timer.append(item.end - item.begin)
            timer.append(item.start_prepare)
            timer.append(item.justplay)
            timer.append(item.afterEvent)
            timer.append(item.log_entries)
            
            try:
                timer.append(item.Filename)
            except:
                timer.append("")
            
            timer.append(item.backoff)       
            
            try:
                timer.append(item.next_activation)
            except:
                timer.append("")
                
            timer.append(item.first_try_prepare)  
            timer.append(item.state)
            timer.append(item.repeated)
            timer.append(item.dontSave)
            timer.append(item.cancelled)
            
            if item.eit is not None:
                self.epgcache.lookupEvent(['E',("%s" % item.service_ref ,2,item.eit)])
                if event[0][0] is not None:
                    timer.append(event[0][0])
                else:
                    timer.append("N/A")
            else:
                timer.append("N/A")
                
            timerlist.append(timer)
#        except:
#            print sys.exc_info()[0]
#            print sys.exc_info()[1]
#            print traceback.extract_tb(sys.exc_info()[2])
            
        return timerlist
    
    list = property(command)
    lut = {"ServiceReference":0
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
           ,"DescriptionExtended":21
           }

