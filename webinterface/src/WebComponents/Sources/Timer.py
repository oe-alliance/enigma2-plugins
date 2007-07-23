Version = '$Header$';

from enigma import eServiceReference, eEPGCache
from Components.Sources.Source import Source
from Components.config import config
from ServiceReference import ServiceReference
from RecordTimer import RecordTimerEntry, RecordTimer, AFTEREVENT, parseEvent
from Components.config import config
from xml.sax.saxutils import unescape
from time import time, strftime, localtime, mktime
from string import split

class Timer( Source):
    LIST = 0
    ADDBYID = 1
    ADD = 2
    DEL = 3
    TVBROWSER = 4
    CHANGE = 5
    WRITE = 6
    RECNOW = 7
    
    def __init__(self, session,func = LIST):
        self.func = func
        Source.__init__(self)        
        self.session = session
        self.recordtimer = session.nav.RecordTimer
        self.epgcache = eEPGCache.getInstance()
        self.result = False,"unknown command"

    def handleCommand(self,cmd):
        if self.func is self.ADDBYID:
            self.result = self.addTimerByEventID(cmd)
            self.writeTimerList()
        elif self.func is self.ADD:
            self.result = self.addTimer(cmd)
            self.writeTimerList()
        elif self.func is self.TVBROWSER:
            self.result = self.tvBrowser(cmd)
            self.writeTimerList()
        elif self.func is self.DEL:
            self.result = self.delTimer(cmd)
            self.writeTimerList()
        elif self.func is self.CHANGE:
            self.result = self.changeTimer(cmd)
            self.writeTimerList()
        elif self.func is self.WRITE:
            self.result = self.writeTimerList(force=True)
        elif self.func is self.RECNOW:
            print "RECNOW"
            self.result = self.recordNow(cmd)
        else:
            self.result = False,"unknown command cmd(%s) self.func(%s)" % (cmd, self.func)

    def delTimer(self,param):
        # is there an easier and better way? :\ 
        print "delTimer",param
        
        if param['sRef'] is None:
            return False,"ServiceReference missing"
        else: 
            serviceref = ServiceReference(param['sRef'])
        
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
                #print "x.begin(%s), x.end(%s), x.service_ref(%s)" % (x.begin, x.end, x.service_ref)
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
            &command=add&&syear={start_year}&smonth={start_month}&sday={start_day}&shour={start_hour}&smin={start_minute}&eyear={end_year}&emonth={end_month}&eday={end_day}&ehour={end_hour}&emin={end_minute}&sRef={urlencode(channel_name_external, "utf8")}&name={urlencode(title, "utf8")}&description={urlencode(title, "utf8")}&afterevent=0&eit=&disabled=0&justplay=0&repeated=0
        
        to zap for some time:
            &command=add&&syear={start_year}&smonth={start_month}&sday={start_day}&shour={start_hour}&smin={start_minute}&eyear={end_year}&emonth={end_month}&eday={end_day}&ehour={end_hour}&emin={end_minute}&sRef={urlencode(channel_name_external, "utf8")}&name={urlencode(title, "utf8")}&description={urlencode(title, afterevent=0&eit=&disabled=0&justplay=1&repeated=0
        
        to delete something:
            &command=del&&syear={start_year}&smonth={start_month}&sday={start_day}&shour={start_hour}&smin={start_minute}&eyear={end_year}&emonth={end_month}&eday={end_day}&ehour={end_hour}&emin={end_minute}&sRef={urlencode(channel_name_external, "utf8")}&name={urlencode(title, "utf8")}&description={urlencode(title, "utf8")}&afterevent=0&eit=&disabled=0&justplay=0&repeated=0
        """
        
        listDate = ['syear','smonth','sday','shour','smin','eyear','emonth','eday','ehour','emin']
        for element in listDate:
            if param[element] is None:
                return False,"%s missing"%element
            else:
                param[element] = int(param[element])
        param['begin'] = int( strftime("%s",  localtime(mktime( (param['syear'], param['smonth'], param['sday'], param['shour'], param['smin'], 0, 0, 0, -1) ) ) ) )
        param['end']   = int( strftime("%s",  localtime(mktime( (param['eyear'], param['emonth'], param['eday'], param['ehour'], param['emin'], 0, 0, 0, -1) ) ) ) )
        
        for element in listDate:
            del param[element]
        
        if param['sRef'] is None:
            return False,"sRef missing"
        else:
            takeApart = split(param['sRef'], '|')
            if len(takeApart) > 1:
                param['sRef'] = takeApart[1]
        
        repeated = 0
        if param.has_key('repeated'):
            repeated = int(param['repeated'])
        if repeated == 0:
            list = ["mo","tu","we","th","fr","sa","su","ms","mf"]
            for element in list:
                if param.has_key(element):
                    number = param[element] or 0
                    del param[element]
                    repeated = repeated + int(number)
            if repeated > 127:
                repeated = 127
        param['repeated'] = repeated

        if param['command'] == "add":
            del param['command']
            return self.addTimer(param)
        elif param['command'] == "del":
            del param['command']
            return self.delTimer(param)
        elif param['command'] == "change":
            del param['command']
            return self.changeTimer(param)
        else:
            return False,"command missing"
    
    def recordNow(self,param):
        print "recordNow ",param
        
        limitEvent = True
        if param == "undefinitely":
            limitEvent = False
        
        serviceref = self.session.nav.getCurrentlyPlayingServiceReference()
        print serviceref
        #assert isinstance(serviceref, ServiceReference)
        serviceref = ServiceReference(serviceref.toString())
        event = None
        try:
            service = self.session.nav.getCurrentService()
            event = self.epgcache.lookupEventTime(serviceref, -1, 0)
            if event is None:
                info = service.info()
                ev = info.getEvent(0)
                event = ev
        except:
            pass

        begin = time()
        end = begin + 3600 * 10
        name = "instant record"
        description = ""
        eventid = 0

        if event is not None:
            curEvent = parseEvent(event)
            name = curEvent[2]
            description = curEvent[3]
            eventid = curEvent[4]
            if limitEvent:
                end = curEvent[1]
        else:
            if limitEvent:
                return False, "No event found, started recording undefinitely"

        newtimer = RecordTimerEntry(serviceref, begin, end, name, description, eventid, False, False, 0)
        newtimer.dontSave = True
        self.recordtimer.record(newtimer)

        return True,"recording was startet"
        
    def addTimer(self,param):
        # is there an easier and better way? :\ 
        print "addTimer",param
        if param['sRef'] is None:
            return False,"ServiceReference missing"
        else: 
            serviceref = ServiceReference(param['sRef'])
        
        if param['begin'] is None:
           return False,"begin missing"
        else:
            begin = float(param['begin'])
        
        if param['end'] is None:
            return False,"end missing"
        elif float(param['end']) > time():
            end = float(param['end'])
        else:
             return False,"end is in the past"
                
        if param['name'] is None:
            return False,"name is missing"
        else:
            print "name1 ",param['name']
            name = unescape(param['name'])#.encode("UTF-16LE")#.decode('utf-8')
            print "name2 ",name
            #).decode('utf_8')
            
        if param['description'] is not None:
            print "description1 ",param['description']
            description = unescape(param['description'])#.encode("UTF-16LE")#.decode('utf-8')
            print "description2 ",description
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
        
        repeated = 0
        if param.has_key('repeated'):
            repeated = int(param['repeated'])
        
        newtimer = RecordTimerEntry(serviceref, begin, end, name, description, 0, disabled, justplay, afterevent)
        newtimer.repeated = repeated
        self.recordtimer.record(newtimer)
        #self.session.nav.RecordTimer.saveTimer()
        return True,"Timer added"        

    def addTimerByEventID(self,param):
        print "addTimerByEventID",param
        if param['sRef'] is None:
            return False,"ServiceReference not set"
        if param['eventid'] is None:
            return False,"Eventid not set"
        
        justplay = False
        if param['justplay'] is not None:
            if param['justplay'] == "1":
                justplay = True

        epgcache = eEPGCache.getInstance()
        event = epgcache.lookupEventId(eServiceReference(param['sRef']),int(param['eventid']))
        if event is None:
            return False,"Eventid not found"
        (begin, end, name, description, eit) =parseEvent(event)
        
        print "addTimerByEventID newtimer ",param['sRef'], (begin - (int(config.recording.margin_before.value)*60)), (end + (int(config.recording.margin_after.value)*60)), name, description, eit, False, justplay
        newtimer = RecordTimerEntry(ServiceReference(param['sRef']), (begin - (int(config.recording.margin_before.value)*60)), (end + (int(config.recording.margin_after.value)*60)), name, description, eit, False, justplay, AFTEREVENT.NONE)
                        #RecordTimerEntry(serviceref, begin, end, name, description, eit, disabled, justplay, afterevent)
                
        self.recordtimer.record(newtimer)
        return True,"Timer added"    
            
    def changeTimer(self,param):
        
        print "changeTimer ",param
        
        if int(param['deleteOldOnSave']) == 1:
            
            if param['sRef'] is None:
                return False,"ServiceReference missing"
            else: 
                serviceref = ServiceReference(param['sRef'])

            if param['repeated'] is not None:
                repeated = int(param['repeated'])
            else: 
                repeated = 0
            
            if param['begin'] is None:
                return False,"begin missing"
            elif time() <= float(param['begin']):
                begin = float(param['begin'])
            elif time() > float(param['begin']) and repeated == 1:
                begin = time()
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
                #print "beginOld(%s), endOld(%s), channelOld(%s)" % (beginOld, endOld, channelOld)
                for x in self.recordtimer.timer_list + self.recordtimer.processed_timers:
                    #print "x.begin(%s), x.end(%s), x.service_ref(%s)" % (float(x.begin), float(x.end), x.service_ref)
                    if str(x.service_ref) == str(channelOld) and float(x.begin) == beginOld and float(x.end) == endOld:
                        #print "one found"
                        toChange = x
                        toChange.service_ref = ServiceReference(param['sRef'])
                        toChange.begin = int(begin)
                        toChange.end = int(end)
                        toChange.name = name
                        toChange.description = description
                        toChange.disabled = disabled
                        toChange.justplay = justplay
                        toChange.afterEvent = afterevent
                        toChange.repeated = repeated
                        self.session.nav.RecordTimer.timeChanged(toChange)
                        print "Timer changed"
                        return True,"Timer changed"
                        break
            except:
                return False,"error searching for old Timer"            
            if toChange is None:
                return False,"Timer not found"
        else:
            return self.addTimer(param)
    
    def writeTimerList(self,force=False):
        # is there an easier and better way? :\
        if config.plugins.Webinterface.autowritetimer.value or force: 
            print "Timer.py writing timer to flash"
            self.session.nav.RecordTimer.saveTimer()
            return True,"TimerList was saved "
        else:
            return False,"TimerList was not saved "    

    def getText(self):
        print self.result
        (result,text) = self.result
        xml  = "<e2simplexmlresult>\n"
        if result:
            xml += "<e2state>True</e2state>\n"
        else:
            xml += "<e2state>False</e2state>\n"            
        xml += "<e2statetext>%s</e2statetext>\n" % text
        xml += "</e2simplexmlresult>\n"
        return xml
    
    text = property(getText)
    
    ## part for listfiller requests
    def command(self):
        timerlist = []

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
            
            if item.dontSave is True:
                timer.append(1)
            else:
                timer.append(0)
#            timer.append(item.dontSave)

            timer.append(item.cancelled)
            
            if item.eit is not None:
                event = self.epgcache.lookupEvent(['E',("%s" % item.service_ref ,2,item.eit)])
                if event[0][0] is not None:
                    timer.append(event[0][0])
                else:
                    timer.append("N/A")
            else:
                timer.append("N/A")
            
            if item.state == 0:
                timer.append("000000")
            elif item.state == 1:
                timer.append("00BCBC")
            elif item.state == 2:
                timer.append("9F1919")
            else:
                timer.append("00BCBC")
            #toggleDisabled
            if item.disabled is True:
                timer.append("0")
                timer.append("on")
            else:
                timer.append("1")
                timer.append("off")

            timerlist.append(timer)
            
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
           ,"Color":22
           ,"toggleDisabled":23
           ,"toggleDisabledIMG":24
           }       