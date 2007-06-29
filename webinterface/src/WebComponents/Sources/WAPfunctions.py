Version = '$Header$';

from Components.Sources.Source import Source
from Components.Sources.Source import Source
from Components.Sources.ServiceList import ServiceList
from enigma import eServiceReference


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
        self.result = ["unknown command (%s)"  % self.func]

    def handleCommand(self,cmd):
        print "WAPfunctions: handleCommand", cmd
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
        
        mo = ["mo",   1, "Monday"]
        tu = ["tu",   2, "Tuesday"]
        we = ["we",   4, "Wednesday"]
        th = ["th",   8, "Thursday"]
        fr = ["fr",  16, "Friday"]
        sa = ["sa",  32, "Saturday"]
        su = ["su",  64, "Sunday"]
        mf = ["mf",  31, "Mo-Fr"]
        ms = ["ms", 127, "Mo-Su"]
        
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
        
        if repeated >= 32:
            repeated = repeated - 32
            sa.append("checked")
        else:
            sa.append("")
        
        if repeated == 31:
            repeated = repeated - 31
            mf.append("checked")
        else:
            mf.append("")

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
    
    def serviceList(self,param):
        print "serviceList: ",param
        sRef = str(param["sRef"])
        bouquet = str(param["bouquet"])
        returnList = []
        sRefFound = 0
        
        ref = eServiceReference(bouquet)
        self.servicelist = ServiceList(ref, command_func = self.getServiceList, validate_commands=False)
        self.servicelist.setRoot(ref)
        for (ref2, name) in self.servicelist.getServicesAsList():
            print "ref2: (",ref2, ") name: (",name,")"
            returnListPart = []
            returnListPart.append(name)
            returnListPart.append(ref2)
            if ref2 == str(sRef):
                returnListPart.append("selected")
                sRefFound = 1
            else:
                returnListPart.append("")
            returnList.append(returnListPart)

        if sRefFound == 0:
            returnListPart = ["Inserted", sRef, "selected"]
            returnList.append(returnListPart)
        print returnList
        return returnList
    
    def getServiceList(self, ref):
        self.servicelist.root = ref
        
    def getText(self):
        print self.result
        (result,text) = self.result
        return text
    
    def filterXML(self, item):
        item = item.replace("&", "&amp;").replace("<", "&lt;").replace('"', '&quot;').replace(">", "&gt;")
        return item

    def getList(self):
        print self.result
        return self.result

    ## part for listfiller requests
    def command(self):
        timerlist = []

        return timerlist
    
    text = property(getText)
    list = property(getList)