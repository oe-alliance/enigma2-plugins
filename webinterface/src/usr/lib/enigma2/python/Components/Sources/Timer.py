from enigma import *

from Source import Source
from ServiceReference import ServiceReference
from enigma import eServiceReference 
class Timer( Source):
    
    def __init__(self, session):
        #self.func = func
        Source.__init__(self)        
        self.session = session
        self.recordtimer = session.nav.RecordTimer
        
#    def handleCommand(self,cmd):
#        self.command = cmd

    
    def command(self):
        timerlist = []
        for item in self.recordtimer.timer_list+self.recordtimer.processed_timers:
            timer = []
            timer.append(item.service_ref)
            timer.append(item.service_ref.getServiceName())
            timer.append(item.eit)
            timer.append(self.convert(item.name))
            timer.append(self.convert(item.description))
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
    
    def convert(self,input):
        #this is not nice, but ",',<,> and & are controlchars in xml and must be replaced
        return input.replace("<","&lt;").replace(">","&gt;").replace("&","&amp;").replace("\"","&quot;").replace("'","&apos;")
        
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

