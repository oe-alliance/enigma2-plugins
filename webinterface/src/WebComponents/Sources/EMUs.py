from enigma import *
from enigma import eServiceReference, iServiceInformation
from Components.Sources.Source import Source

from RequestData import RequestData

import os, string
import sys, traceback

class EMUs( Source):
    LIST = 0
    STARTSTOP = 1
    
    def __init__(self, session,func = LIST):
        Source.__init__(self)
        self.func = func
        self.session = session
        self.result = False,"EMUs: unknown command"
    
    def handleCommand(self,cmd):
        if self.func is self.STARTSTOP:
            self.result = self.startStop(cmd)
        else:
            self.result = False,"EMUs: unknown command cmd(%s) self.func(%s)" % (cmd, self.func)
        
    def startStop(self,param):
        print "startStop:",param
        
        if param["state"] is None:
            return False,"state missing"
        if param["file"] is None:
            return False,"file missing"
        
        state = param["state"]
        if state == "on":
            state = "start"
        elif state == "off":
            state = "stop"
        try:
            if state == "restart":
                os.system('%s %s &' % (param["file"], "stop") )
                os.system('%s %s &' % (param["file"], "start") )
            else: 
                os.system('%s %s &' % (param["file"], state) )
            return True,"EMU was %s" %state

        except OSError:
            return False,"OSErrorSome error occurred"
        
        return False,"Some error occurred %s ing %s" %(state, param["file"])
            
   
    def command(self):
        ps = []
        psList = os.popen("ps| awk '{print $5;}'| grep usr/bin")
        while 1:
            line = psList.readline()
            if not line:
                break
            line = line.replace("\n","")
            ps.append(line)
       
        list=[]
        grep = os.popen("/bin/grep 'CAMNAME=' /var/script/*")
        while 1:
            line = grep.readline()
            if not line:
                break
            line = line.replace("CAMNAME=","")
            line = line.replace("\"","")

            (file,name) = string.split(line, ':')
            status = "not running"
            
            try:
                grep2 = os.popen("/bin/grep '/usr/bin' %s" % file)
                running = []
                statusR = []
                while 1:
                    line2 = grep2.readline()

                    if not line2:
                        break
                    
                    for x in ps:
                        if line2.rfind(x) > -1:
                            status = "running"
                    
                    running.append(line2)
                    if status == "running":
                        statusR.append(status)

                if len(running) == len(statusR):
                    status = "running"
                else:
                    status = "not running"
                
            except:
                print sys.exc_info()[0]
                print sys.exc_info()[1]
                print traceback.extract_tb(sys.exc_info()[2])

            list0 = []
            list0.append(file)
            list0.append(name)
            list0.append(status)
            if file.rfind("ccam") > -1:
                list0.append("http://%s:16001" % RequestData(request,what=RequestData.HOST) )
            else:
                list0.append(" ")
            list.append(list0)
        return list

    def getText(self):
        (result,text) = self.result
        xml = "<?xml version=\"1.0\"?>\n"
        xml  += "<e2simplexmlresult>\n"
        if result:
            xml += "<e2state>True</e2state>\n"
        else:
            xml += "<e2state>False</e2state>\n"            
        xml += "<e2statetext>%s</e2statetext>\n" % text
        xml += "</e2simplexmlresult>\n"
        return xml
    
    text = property(getText)        
    
    list = property(command)
    lut = {"File": 0
           ,"Name": 1
           ,"Status": 2
           ,"Link": 3
           }

