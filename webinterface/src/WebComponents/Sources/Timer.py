from enigma import *
from enigma import eServiceReference 
from enigma import eServiceCenter

from Components.Sources.Source import Source
from ServiceReference import ServiceReference
from RecordTimer import RecordTimerEntry, RecordTimer, AFTEREVENT,parseEvent
from Components.config import config

import time, string
# import sys, traceback

class Timer( Source):
    LIST = 0
    ADDBYID = 1
    ADD = 2
    DEL = 3
    TVBROWSER = 4
    CHANGE = 5
    
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
        elif self.func is self.CHANGE:
            self.result = self.changeTimer(cmd)
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
        print "tvbrowser",param
        
        """ Therefor the URL's for the tvBrowser-Capture-Driver are:
        
            http://dreambox/web/tvbrowser? +
            
        To add something:
            &command=add&&syear={start_year}&smonth={start_month}&sday={start_day}&shour={start_hour}&smin={start_minute}&eyear={end_year}&emonth={end_month}&eday={end_day}&ehour={end_hour}&emin={end_minute}&serviceref={urlencode(channel_name_external, "utf8")}&name={urlencode(title, "utf8")}&description={urlencode(title, "utf8")}&afterevent=0&eit=&disabled=0&justplay=0&repeated=0
        
        to zap for some time:
            &command=add&&syear={start_year}&smonth={start_month}&sday={start_day}&shour={start_hour}&smin={start_minute}&eyear={end_year}&emonth={end_month}&eday={end_day}&ehour={end_hour}&emin={end_minute}&serviceref={urlencode(channel_name_external, "utf8")}&name={urlencode(title, "utf8")}&description={urlencode(title, "utf8")}&afterevent=0&eit=&disabled=0&justplay=1&repeated=0
        
        to delete something:
            &command=del&&syear={start_year}&smonth={start_month}&sday={start_day}&shour={start_hour}&smin={start_minute}&eyear={end_year}&emonth={end_month}&eday={end_day}&ehour={end_hour}&emin={end_minute}&serviceref={urlencode(channel_name_external, "utf8")}&name={urlencode(title, "utf8")}&description={urlencode(title, "utf8")}&afterevent=0&eit=&disabled=0&justplay=0&repeated=0
        """
        
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
        
        if param['repeated'] is not None:
            repeated = int(param['repeated'])
        else: 
            repeated = 0
            
        newtimer = RecordTimerEntry(serviceref, begin, end, name, description, 0, disabled, justplay, afterevent)
        newtimer.repeated = repeated
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
        if param['justplay'] is None and param['justplay'] == "1":
            justplay = True
        
        newtimer = RecordTimerEntry(ServiceReference(param['serviceref']), (begin - (int(config.recording.margin_before.value)*60)), (end + (int(config.recording.margin_after.value)*60)), name, description, eit, False, justplay, AFTEREVENT.NONE)
        self.recordtimer.record(newtimer)
        return True,"Timer added"    
            
    def changeTimer(self,param):
        
        print "changeTimer ",param
        
        if int(param['deleteOldOnSave']) == 1:
            
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

            if param['repeated'] is not None:
                repeated = int(param['repeated'])
            else: 
                repeated = 0

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
        
            if param['channelOld'] is None:
                return False,"channelOld missing"
            else: 
                channelOld = ServiceReference(param['channelOld'])
            
            if param['beginOld'] is None:
                return False,"beginOld missing"
            else:
                beginOld = float(param['beginOld'])
            
            if param['endOld'] is None:
                return False,"endOld missing"
            else:
                endOld = float(param['endOld'])
                
            toChange = None
            try:
                for x in self.recordtimer.timer_list + self.recordtimer.processed_timers:
                    #print "x.begin(%s), x.end(%s), x.service_ref(%s)" % (x.begin, x.end, x.service_ref)
                    #print "beginOld(%s), endOld(%s), channelOld(%s)" % (beginOld, endOld, channelOld)
                    if str(x.service_ref) == str(channelOld) and float(x.begin) == beginOld and float(x.end) == endOld:
                        toChange = x
                        toChange.service_ref = ServiceReference(param['serviceref'])
                        toChange.begin = begin
                        toChange.end = end
                        toChange.name = name
                        toChange.description = description
                        toChange.disabled = disabled
                        toChange.justplay = justplay
                        toChange.afterEvent = afterevent
                        toChange.repeated = repeated
                        if disabled is True:
                            toChange.state = 3
                        else:
                            toChange.state = 0
                        print "Timer changed"
                        return True,"Timer changed"
                        break
            except:
                return False,"error searching for old Timer"
            
            if toChange is None:
                return False,"Timer not found"
                print "Timer not found"
        else:
            return self.addTimer(param)
            
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
            if item.disabled is True:
                timer.append("1")
            else:
                timer.append("0")
            #timer.append(item.disabled)

            timer.append(item.begin)
            timer.append(item.end)
            timer.append(item.end - item.begin)
            timer.append(item.start_prepare)
            
            if item.justplay is True:
                timer.append(1)
            else:
                timer.append(0)

            timer.append(item.afterEvent)
            
            """
No passing Logevents, because of error:
XML-Verarbeitungsfehler: nicht wohlgeformt
Adresse: http://dreambox/web/timerlist
Zeile Nr. 374, Spalte 259:        <e2logentries>[(1171275272, 15, 'record time changed, start prepare is now: Mon Feb 12 12:29:40 2007'), (1171279780, 5, 'activating state 1'), (1171279780, 0, "Filename calculated as: '/hdd/movie/20070212 1230 - DISNEY CHANNEL - Quack Pack - Onkel Donald & Die Boys'"), (1171279780, 3, 'prepare ok, writing meta information to /hdd/movie/20070212 1230 - DISNEY CHANNEL - Quack Pack - Onkel Donald & Die Boys'), (1171279780, 6, 'prepare ok, waiting for begin'), (1171279800, 5, 'activating state 2'), (1171279800, 11, 'start recording'), (1171281900, 5, 'activating state 3'), (1171281900, 12, 'stop recording')]</e2logentries>
------------------------------------------------------------------------------------------------------------
No clue, what it could be.
            """
            #timer.append(item.log_entries)
            timer.append("")
            
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
                event = self.epgcache.lookupEvent(['E',("%s" % item.service_ref ,2,item.eit)])
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

