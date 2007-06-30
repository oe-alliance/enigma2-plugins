Version = '$Header$';

from Components.Sources.Source import Source
from Components.Sources.Source import Source
from Components.Sources.ServiceList import ServiceList
from enigma import eServiceReference


import time, re

class WAPfunctions( Source):
    LISTTIME = 0
    REPEATED = 1
    SERVICELIST = 2
    OPTIONLIST = 3
    FILLVALUE = 4
    DELETEOLD = 5
    
    lut = {"Name":0
          ,"Value":1
          ,"Selected":2
          }
    
    def __init__(self, session,func = LISTTIME):
        self.func = func
        Source.__init__(self)        
        self.session = session
        self.result = ["unknown command (%s)"  % self.func]

    def handleCommand(self,cmd):
        print "WAPfunctions: handleCommand", cmd
        if self.func is self.LISTTIME:
            self.result = self.fillListTime(cmd)
        elif self.func is self.REPEATED:
            self.result = self.fillRepeated(cmd)
        elif self.func is self.SERVICELIST:
            self.result = self.serviceList(cmd)
        elif self.func is self.OPTIONLIST:
            self.result = self.fillOptionList(cmd)
        elif self.func is self.FILLVALUE:
            self.result = self.fillValue(cmd)
        elif self.func is self.DELETEOLD:
            self.result = self.deleteOldSaved(cmd)
        else:
            self.result = ["unknown command cmd(%s) self.func(%s)" % (cmd, self.func)]

    def fillListTime(self,param):
        print "fillListTime",param
        
        input = 0
        start = 1
        end = 1
        
        timeNow = time.time()
        timePlusTwo = timeNow + 7200

        if param.has_key('begin'):
            begin = param['begin'] or 0
            begin = int(begin)
            del param['begin']
            if begin > 0:
                timeNow = begin
        if param.has_key('end'):
            end = param['end'] or 0
            end = int(end)
            del param['end']
            if end > 0:
                timePlusTwo = end
        
        t = {}
        t["sday"]=time.strftime("%d", time.localtime(timeNow))
        t["smonth"]=time.strftime("%m", time.localtime(timeNow))
        t["syear"]=time.strftime("%Y", time.localtime(timeNow))
        t["smin"]=time.strftime("%M", time.localtime(timeNow))
        t["shour"]=time.strftime("%H", time.localtime(timeNow))
        
        t["eday"]=time.strftime("%d", time.localtime(timePlusTwo))
        t["emonth"]=time.strftime("%m", time.localtime(timePlusTwo))
        t["eyear"]=time.strftime("%Y", time.localtime(timePlusTwo))
        t["emin"]=time.strftime("%M", time.localtime(timePlusTwo))
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
        
        if param[key] == "now" or param[key] == "end" or param[key] == "begin":
            input = int(t[key])
        else:
            input = param[key] or 0
            input = int(input)
        #print cutKey,param[key],input
        
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
        print "fillRepeated",param
        repeated = param or 0
        repeated = int(repeated)
        
        self.lut = {"Name":0
          ,"Value":1
          ,"Description":2
          ,"Selected":3
          }
        
        mo = ["mo",   1, "Mo "]#"Monday"]
        tu = ["tu",   2, "Tu "]#"Tuesday"]
        we = ["we",   4, "We "]#"Wednesday"]
        th = ["th",   8, "Th "]#"Thursday"]
        fr = ["fr",  16, "Fr "]#"Friday"]
        sa = ["sa",  32, "Sa "]#"Saturday"]
        su = ["su",  64, "Su "]#"Sunday"]
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
        
        if bouquet == '':
            bouquet = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet'
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

        if sRefFound == 0 and sRef != '':
            returnListPart = ["Inserted", sRef, "selected"]
            returnList.append(returnListPart)
        #print returnList
        return returnList

    def getServiceList(self, ref):
        self.servicelist.root = ref
    
    def fillOptionList(self,param):
         
        print "fillOptionList",param
        returnList = []
        if param.has_key("justplay"):
            number = param["justplay"] or 0
            number = int(number)
            if number == 1:
                returnList.append(["Record",0,""])
                returnList.append(["Zap",1,"selected"])
            else:
                returnList.append(["Record",0,"selected"])
                returnList.append(["Zap",1,""])
        elif param.has_key("afterevent"):
            number = param["afterevent"] or 0
            number = int(number)
            if number == 2:
                returnList.append(["Nothing",0,""])
                returnList.append(["Standby",1,""])
                returnList.append(["Deepstandby/Shutdown",2,"selected"])
            elif number == 1:
                returnList.append(["Nothing",0,""])
                returnList.append(["Standby",1,"selected"])
                returnList.append(["Deepstandby/Shutdown",2,""])
            else:
                returnList.append(["Nothing",0,"selected"])
                returnList.append(["Standby",1,""])
                returnList.append(["Deepstandby/Shutdown",2,""])
        
        return returnList
    
    def deleteOldSaved(self,param):
        print "deleteOldSaved",param
        returnList = []
        returnList.append(["deleteOldOnSave",param["deleteOldOnSave"],""])
        returnList.append(["command",param["command"],""])
        if int(param["deleteOldOnSave"]) == 1:
            returnList.append(["channelOld",param["sRef"],""])
            returnList.append(["beginOld",param["begin"],""])
            returnList.append(["endOld",param["end"],""])
        return returnList
            
    
    def fillValue(self,param):
        print "fillValue: ",param
        return [["",param,""]]

    def getText(self):
        (result,text) = self.result
        return text
    
    def filterXML(self, item):
        item = item.replace("&", "&amp;").replace("<", "&lt;").replace('"', '&quot;').replace(">", "&gt;")
        return item

    def getList(self):
        return self.result

    ## part for listfiller requests
    def command(self):
        timerlist = []

        return timerlist
    
    text = property(getText)
    list = property(getList)