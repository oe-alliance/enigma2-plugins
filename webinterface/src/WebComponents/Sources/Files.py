from Components.Sources.Source import Source
from os import path, system

class Files( Source):
    DEL = 0
    
    def __init__(self, session,func = DEL):
        Source.__init__(self)
        self.func = func
        self.session = session
        error = "unknown command (%s)" % func
        self.result = [[error,error]]
    
    def handleCommand(self,cmd):
        self.cmd = cmd
        if self.func is self.DEL:
            self.result = self.delFile(cmd)
           
    def delFile(self,param):
        print "delFile:",param
        
        returnList = ["False", "Some error occurred deleting %s" % param]
        
        if path.exists(param):
            system('rm -f "%s"' % param)
        if path.exists(param):
            returnList = ["True","File (%s) was deleted"% param]
        
        return returnList
   
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
    
    def getList(self):
        return self.result
    
    list = property(getList)
    lut = {"State": 0
           ,"Statetext": 1           
           }
