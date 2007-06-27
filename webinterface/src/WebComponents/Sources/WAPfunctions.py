Version = '$Header$';

from enigma import *
from Components.Sources.Source import Source

import time, re

class WAPfunctions( Source):
    FILLOPTIONLIST = 0
    REPEATED = 1
    SERVICELIST = 2
    
    lut = {"Name":0
          ,"Value":1
          ,"Selected":2
          }
    
    def __init__(self, session,func = FILLOPTIONLIST):
        self.func = func
        Source.__init__(self)        
        self.session = session
        self.result = ["unknown command"]

    def handleCommand(self,cmd):
        print "WAPfunctions: handleCommand"
        if self.func is self.FILLOPTIONLIST:
            self.result = self.fillOptionList(cmd)
        elif self.func is self.REPEATED:
            self.result = self.fillRepeated(cmd)
        elif self.func is self.SERVICELIST:
            self.result = self.serviceList(cmd)
        else:
            self.result = ["unknown command cmd(%s) self.func(%s)" % (cmd, self.func)]

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

        cutKey = re.sub("^[es]", "", key, 1)
        
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
            input = param[key] or 0
            input = int(input)
        
        self.result = self.fillOptionListAny(input,start,end)
        return self.result
    
    def fillOptionListAny(self,input,start,end):
        returnList = []
        for i in range(start,end+1,1):
            returnList1 = []
            j = str(i)
            if len(j) == 1:
                j = "0%s" % j
            returnList1.append(j)
            returnList1.append(i)
            if i==input:
                returnList1.append("selected")
            else:
                returnList1.append("")
            returnList.append(returnList1)
        return returnList
        
    def fillRepeated(self,param):
        # is there an easier and better way? :\ 
        print "fillRepeated",param
        #del param["sRef"]
        repeated = param or 0
        repeated = int(repeated)
        
        self.lut = {"Name":0
          ,"Value":1
          ,"Description":2
          ,"Selected":3
          }
        
        mo = []
        mo.append("mo")
        mo.append(1)
        mo.append("Monday")
        tu = []
        tu.append("tu")
        tu.append(2)
        tu.append("Tuesday")
        we = []
        we.append("we")
        we.append(4)
        we.append("Wednesday")
        th = []
        th.append("th")
        th.append(8)
        th.append("Thursday")
        fr = []
        fr.append("fr")
        fr.append(16)
        fr.append("Friday")
        sa = []
        sa.append("sa")
        sa.append(32)
        sa.append("Saturday")
        su = []
        su.append("su")
        su.append(64)
        su.append("Sunday")
        mf = []
        mf.append("mf")
        mf.append(31)
        mf.append("Mo-Fr")
        ms = []
        ms.append("ms")
        ms.append(127)
        ms.append("Mo-Su")
        
        if repeated == 127:
            repeated = repeated - 127
            ms.append("checked")
        else:
            ms.append("")
        if repeated >= 64:
            repeated = repeated - 64
            su.append("checked")
        else:
            su.append("")
        if repeated == 31:
            repeated = repeated - 31
            mf.append("checked")
        else:
            mf.append("")
        if repeated >= 32:
            repeated = repeated - 32
            sa.append("checked")
        else:
            sa.append("")
        if repeated >= 16:
            repeated = repeated - 16
            fr.append("checked")
        else:
            fr.append("")
        if repeated >= 8:
            repeated = repeated - 8
            th.append("checked")
        else:
            th.append("")
        if repeated >= 4:
            repeated = repeated - 4
            we.append("checked")
        else:
            we.append("")
        if repeated >= 2:
            repeated = repeated - 2
            tu.append("checked")
        else:
            tu.append("")
        if repeated == 1:
            repeated = repeated - 1
            mo.append("checked")
        else:
            mo.append("")
            
        returnList = []
        returnList.append(mo)
        returnList.append(tu)
        returnList.append(we)
        returnList.append(th)
        returnList.append(fr)
        returnList.append(sa)
        returnList.append(su)
        returnList.append(mf)
        returnList.append(ms)

        return returnList
    
    def getServiceList(self, sRef):
        self["ServiceList"].root = sRef
    def serviceList(self,param):
        from Components.Sources.ServiceList import ServiceList
        self["ServiceList"] = ServiceList(param, command_func = self.getServiceList, validate_commands=False)
        print self["ServiceList"]
        return self["ServiceList"]
    
    def getText(self):
        print self.result
        (result,text) = self.result
        return text
    
    def getList(self):
        print self.result
        return self.result

    ## part for listfiller requests
    def command(self):
        timerlist = []

        return timerlist
    
    text = property(getText)
    list = property(getList)