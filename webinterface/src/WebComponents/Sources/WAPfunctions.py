Version = '$Header$';

from enigma import *
from Components.Sources.Source import Source

import time, re#, sys
#import sys 

#sys.setdefaultencoding('utf8')

class WAPfunctions( Source):
    FILLOPTIONLIST = 0
    
    def __init__(self, session,func = FILLOPTIONLIST):
        self.func = func
        Source.__init__(self)        
        self.session = session
        self.result = False,"unknown command"

    def handleCommand(self,cmd):
        print "WAPfunctions: handleCommand"
        if self.func is self.FILLOPTIONLIST:
            self.result = self.fillOptionList(cmd)
        else:
            self.result = False,"unknown command cmd(%s) self.func(%s)" % (cmd, self.func)

    def fillOptionList(self,param):
        # is there an easier and better way? :\ 
        print "fillOptionList",param
        #del param["sRef"]

        input = 0
        start = 1
        end = 1
        
        timeNow = time.time()
        timePlusTwo = timeNow + 7200
        
        t = {}
        t["sday"]=time.strftime("%d", time.localtime(timeNow))
        t["smonth"]=time.strftime("%m", time.localtime(timeNow))
        t["syear"]=time.strftime("%Y", time.localtime(timeNow))
        t["sminute"]=time.strftime("%M", time.localtime(timeNow))
        t["shour"]=time.strftime("%H", time.localtime(timeNow))
        
        t["eday"]=time.strftime("%d", time.localtime(timePlusTwo))
        t["emonth"]=time.strftime("%m", time.localtime(timePlusTwo))
        t["eyear"]=time.strftime("%Y", time.localtime(timePlusTwo))
        t["eminute"]=time.strftime("%M", time.localtime(timePlusTwo))
        t["ehour"]=time.strftime("%H", time.localtime(timePlusTwo))
        
        key = ""
        for i in param:
            p = str(i)
            if p != "sRef":
                key = p

        print "key: ",key
        cutKey = re.sub("^[es]", "", key, 1)
        print "cutKey: ",cutKey
        
        if cutKey == "min":
            start = 0
            end = 59
        elif cutKey == "hour":
            start = 1
            end = 24
        elif cutKey == "day":
            start = 1
            end = 31
        elif cutKey == "month":
            start = 1
            end = 12
        else:
            start = int(t[key])
            end = int(t[key])+2
        
        if(param[key] == "now"):
            input = int(t[key])
        else:
            input = int(param[key]) or 0
        
        self.result = self.fillOptionListAny(input,start,end)
        return self.result
    
    def fillOptionListAny(self,input,start,end):
        returnList = []
        print input,start,end
        for i in range(start,end+1,1):
            returnList1 = []
            returnList1.append(i)
            returnList1.append(i)
            if i==input:
                returnList1.append("selected")
            else:
                returnList1.append("")
            returnList.append(returnList1)
        return returnList
        
    def getText(self):
        print self.result
        (result,text) = self.result
        return text
    
    def getList(self):
        print self.result
        return self.result
    
    text = property(getText)
    
    ## part for listfiller requests
    def command(self):
        timerlist = []

        return timerlist
    
    list = property(getList)
    lut = {"Name":0
          ,"Value":1
          ,"Selected":2
          }
