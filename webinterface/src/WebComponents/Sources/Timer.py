Version = '$Header$';

from enigma import eServiceReference, eEPGCache
from Components.Sources.Source import Source
from Components.config import config
from ServiceReference import ServiceReference
from RecordTimer import RecordTimerEntry, RecordTimer, AFTEREVENT, parseEvent
from Components.config import config
from xml.sax.saxutils import unescape
from time import time, strftime, localtime, mktime

class Timer( Source):
    LIST = 0
    ADDBYID = 1
    ADD = 2
    DEL = 3
    TVBROWSER = 4
    CHANGE = 5
    WRITE = 6
    RECNOW = 7
    
    def __init__(self, session, func = LIST):
        self.func = func
        Source.__init__(self)
        self.session = session
        self.recordtimer = session.nav.RecordTimer
        self.epgcache = eEPGCache.getInstance()
        self.result = False,"unknown command"
        

    def handleCommand(self, cmd):
        if self.func is self.ADDBYID:
            self.result = self.addTimerByEventID(cmd)
            self.writeTimerList()
        elif self.func is self.ADD:
            self.result = self.editTimer(cmd)
            self.writeTimerList()
        elif self.func is self.TVBROWSER:
            self.result = self.tvBrowser(cmd)
            self.writeTimerList()
        elif self.func is self.DEL:
            self.result = self.delTimer(cmd)
            self.writeTimerList()
        elif self.func is self.CHANGE:
            self.result = self.editTimer(cmd)
            self.writeTimerList()
        elif self.func is self.WRITE:
            self.result = self.writeTimerList(force=True)
        elif self.func is self.RECNOW:
            print "RECNOW"
            self.result = self.recordNow(cmd)
        else:
            self.result = False, "Unknown function: '%s'" %(self.func)



    def delTimer(self, param):
        print "[WebComponents.Timer] delTimer"
        
        if param.has_key('sRef'):
            service_ref = ServiceReference(param['sRef'])            
        else: 
            return False, "Missing Parameter: sRef"
        
        if param.has_key('begin'):
            begin = int(param['begin'])
        else:
            return False, "Missing Parameter: begin"
        
        if param.has_key('end'):
            end = int(param['end'])
        else:
        	return False, "Missing Parameter: end"
             
        try:
            for timer in self.recordtimer.timer_list + self.recordtimer.processed_timers:
                if str(timer.service_ref) == str(service_ref) and int(timer.begin) == begin and int(timer.end) == end:
                    self.recordtimer.removeEntry(timer)
                    return True, "The timer '%s' has been deleted successfully" %(timer.name)
        except:
            return False, "The timer has NOT been deleted"
            
       	return False, "No matching Timer found"

    
    def tvBrowser(self, param):
        print "[WebComponents.Timer] tvbrowser"
        
        """ The URL's for the tvBrowser-Capture-Driver are:
        
            http://dreambox/web/tvbrowser? +
            
        To add something:
            &command=add&&year={year}&month={month}&day={day}&shour={start_hour}&smin={start_minute}&ehour={end_hour}&emin={end_minute}&sRef={urlencode(channel_name_external, "utf8")}&name={urlencode(title, "utf8")}&description={urlencode(descr, "utf8")}&dirname={dirname}&tags={urlencode("tag1 tag2...", "utf8")}&afterevent=0&eit=&disabled=0&justplay=0&repeated=0
        
        to zap for some time:
            &command=add&&year={year}&month={month}&day={day}&shour={start_hour}&smin={start_minute}&ehour={end_hour}&emin={end_minute}&sRef={urlencode(channel_name_external, "utf8")}&name={urlencode(title, "utf8")}&description={urlencode(descr, "utf8")}&dirname={dirname}&tags={urlencode("tag1 tag2...", "utf8")}&afterevent=0&eit=&disabled=0&justplay=1&repeated=0
        
        to delete something:
            &command=del&&year={year}&month={month}&day={day}&shour={start_hour}&smin={start_minute}&ehour={end_hour}&emin={end_minute}&sRef={urlencode(channel_name_external, "utf8")}
        """
        
        listDate = ['year','month','day','shour','smin','ehour','emin']
        for element in listDate:
            if param[element] is None:
                if param['s'+element] is None:
                    return False,"%s missing"%element
                else:
                    param[element] = int(param['s'+element])
            else:
                param[element] = int(param[element])
        param['begin'] = int(mktime( (param['year'], param['month'], param['day'], param['shour'], param['smin'], 0, 0, 0, -1) ) )
        param['end']   = int(mktime( (param['year'], param['month'], param['day'], param['ehour'], param['emin'], 0, 0, 0, -1) ) )
        if param['end'] < param['begin']:
            param['end'] += 86400
        for element in listDate:
            del param[element]
        
        if param['sRef'] is None:
            return False, "Missing Parameter: sRef"
        else:
            takeApart = param['sRef'].split('|')
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
            return self.editTimer(param)
        elif param['command'] == "del":
            del param['command']
            return self.delTimer(param)
        elif param['command'] == "change":
            del param['command']
            return self.editTimer(param)
        else:
            return False, "Unknown command: '%s'" %param['command']
    
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
                return False, "No event found, started infinite recording"

        location = config.movielist.last_videodir.value
        timer = RecordTimerEntry(serviceref, begin, end, name, description, eventid, False, False, 0, dirname = location)
        timer.dontSave = True
        self.recordtimer.record(timer)

        return True, "Instant recording started"


#===============================================================================
# This Function can add a new or edit an exisiting Timer.
# When the Parameter "deleteOldOnSave" is not set, a new Timer will be added.
# Otherwise, and if the parameters channelOld, beginOld and endOld are set,
# an existing timer with corresponding values will be changed.
#===============================================================================
    def editTimer(self, param):
        print "[WebComponents.Timer] editTimer"
        
        #OK first we need to parse all of your Parameters
        #For some of them (like afterEvent or justplay) we can use default values
        #for others (the serviceReference or the Begin/End time of the timer 
        #we have to quit if they are not set/have illegal values
              
        if param.has_key('sRef'):
            service_ref = ServiceReference(param['sRef'])
        else:
            return False, "Missing Parameter: sRef"
                
        repeated = 0
        if param.has_key('repeated'):
            repeated = int(param['repeated'])
        
            
        if param.has_key('begin'):
            begin = int(param['begin'])
            if time() <= begin:                
                pass
            elif time() > int(begin) and repeated == 0:
                begin = time()
            else:
                return False, "Illegal Parameter value for Parameter begin : '%s'" %begin              
        else:
            return False, "Missing Parameter: begin"
        
        if param.has_key('end'): 
            end = int(param['end'])
        else:
            return False, "Missing Parameter: end"
          
        if param.has_key('name'):
            name = param['name']
        else:
            return False, "Missing Parameter: name"
        
        if param.has_key('description'):
            description = param['description'].replace("\n", " ")
        else:
            return False, "Missing Parameter: description"
                
        disabled = False #Default to: Enabled
        if param.has_key('disabled'):            
            if param['disabled'] == "1":
                disabled = True
            else:
                #TODO - maybe we can give the user some useful hint here
                pass
            
        justplay = False #Default to: Record
        if param.has_key('justplay'):
            if param['justplay'] == "1":
                justplay =  True
            
        afterEvent = 3 #Default to Afterevent: Auto
        if param.has_key('afterevent'):
            if ( param['afterevent'] == "0") or (param['afterevent'] == "1") or (param['afterevent'] == "2"):
                afterEvent = int(param['afterevent'])

        dirname = config.movielist.last_timer_videodir.value
        if param.has_key('dirname') and param['dirname']:
            dirname = param['dirname']

        tags = []
        if param.has_key('tags') and param['tags']:
            tags = unescape(param['tags']).split(' ')

        delold = 0
        if param.has_key('deleteOldOnSave'):
            delold = int(param['deleteOldOnSave'])

        #Try to edit an existing Timer
        if delold:
            if param.has_key('channelOld') and param['channelOld'] != '':
                channelOld = ServiceReference(param['channelOld'])
            else:
                return False, "Missing Parameter: channelOld"
            # We do need all of the following Parameters, too, for being able of finding the Timer.
            # Therefore so we can neither use default values in this part nor can we 
            # continue if a parameter is missing            
            if param.has_key('beginOld'):
                beginOld = int(param['beginOld'])
            else:
                return False, "Missing Parameter: beginOld"
            
            if param.has_key('endOld'):
                endOld = int(param['endOld'])
            else:
                return False, "Missing Parameter: endOld"
            
            #let's try to find the timer
            try:
                for timer in self.recordtimer.timer_list + self.recordtimer.processed_timers:
                    if str(timer.service_ref) == str(channelOld):
                        if int(timer.begin) == beginOld:
                            if int(timer.end) == endOld:
                                #we've found the timer we've been searching for
                                #Let's apply the new values
                                timer.service_ref = service_ref
                                timer.begin = int(begin)
                                timer.end = int(end)
                                timer.name = name
                                timer.description = description
                                timer.disabled = disabled
                                timer.justplay = justplay
                                timer.afterEvent = afterEvent
                                timer.repeated = repeated
                                timer.dirname = dirname
                                timer.tags = tags
                                
                                #send the changed timer back to enigma2 and hope it's good
                                self.session.nav.RecordTimer.timeChanged(timer)
                                print "[WebComponents.Timer] editTimer: Timer changed!"
                                return True, "Timer %s has been changed!" %(timer.name)
            except:
                #obviously some value was not good, return an error
                return False, "Changing the timer for '%s' failed!" %name
            
            return False, "Could not find timer '%s' with given start and end time!" %name

        #Try adding a new Timer

        try:
            #Create a new instance of recordtimerentry
            timer = RecordTimerEntry(service_ref, begin, end, name, description, 0, disabled, justplay, afterEvent, dirname = dirname, tags = tags)
            timer.repeated = repeated
            #add the new timer
            self.recordtimer.record(timer)
            return True, "Timer added successfully!"
        except:
            #something went wrong, most possibly one of the given paramater-values was wrong
            return False, "Could not add timer '%s'!" %name
            
        return False, "Unexpected Error"
                

    def addTimerByEventID(self, param):
        print "[WebComponents.Timer] addTimerByEventID", param
        if param['sRef'] is None:
            return False, "Missing Parameter: sRef"
        if param['eventid'] is None:
            return False, "Missing Parameter: eventid"
        
        justplay = False
        if param['justplay'] is not None:
            if param['justplay'] == "1":
                justplay = True

        location = config.movielist.last_timer_videodir.value
        if param.has_key('dirname') and param['dirname']:
            location = param['dirname']
        tags = []
        if param.has_key('tags') and param['tags']:
            tags = unescape(param['tags']).split(' ')

        epgcache = eEPGCache.getInstance()
        event = epgcache.lookupEventId(eServiceReference(param['sRef']),int(param['eventid']))
        if event is None:
            return False, "EventId not found"
        
        (begin, end, name, description, eit) = parseEvent(event)

        timer = RecordTimerEntry(ServiceReference(param['sRef']), begin , end, name, description, eit, False, justplay, AFTEREVENT.NONE, dirname=location, tags=tags)
        self.recordtimer.record(timer)
        return True, "Timer '%s' added" %(timer.name)  
            
        
    def writeTimerList(self, force=False):
        # is there an easier and better way? :\
        if config.plugins.Webinterface.autowritetimer.value or force: 
            print "Timer.py writing timer to flash"
            self.session.nav.RecordTimer.saveTimer()
            return True, "TimerList was saved "
        else:
            return False, "TimerList was not saved "    


    def getText(self):
        print "[WebComponents.Timer] result: ", self.result
        (result, text) = self.result
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

            if item.disabled:
                timer.append("1")
            else:
                timer.append("0")

            timer.append(item.begin)
            timer.append(item.end)
            timer.append(item.end - item.begin)
            timer.append(item.start_prepare)
            
            if item.justplay:
                timer.append(1)
            else:
                timer.append(0)

            timer.append(item.afterEvent)
            
            timer.append(item.dirname)
            timer.append(" ".join(item.tags))

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
            
            if item.dontSave:
                timer.append(1)
            else:
                timer.append(0)

            timer.append(item.cancelled)
            
            if item.eit is not None:
                event = self.epgcache.lookupEvent(['EX',("%s" % item.service_ref ,2,item.eit)])
                if event[0][0] is not None:
                    timer.append(event[0][0])
                else:
                    timer.append("N/A")
            else:
                timer.append("N/A")
            
            #toggleDisabled
            if item.disabled:
                timer.append("0")
                timer.append("on")
            else:
                timer.append("1")
                timer.append("off")

            timerlist.append(timer)
            
        return timerlist
    
    list = property(command)
    lut = {
               "ServiceReference":0,
               "ServiceName": 1,
               "EIT":2,
               "Name":3,
               "Description":4,
               "Disabled":5,
               "TimeBegin":6,
               "TimeEnd":7,
               "Duration":8,
               "startPrepare":9,
               "justPlay":10,
               "afterEvent":11,
               "Location":12,
               "Tags":13,
               "LogEntries":14,
               "Filename":15,
               "Backoff":16,
               "nextActivation":17,
               "firstTryPrepare":18,
               "State":19,
               "Repeated":20,
               "dontSave":21,
               "Cancled":22,
               "DescriptionExtended":23,
               "toggleDisabled":24,
               "toggleDisabledIMG":25,
           }
