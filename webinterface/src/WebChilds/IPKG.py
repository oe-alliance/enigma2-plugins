from enigma import eConsoleAppContainer

from twisted.web2 import resource, stream, responsecode, http

class IPKGResource(resource.Resource):
    IPKG_PATH = "/usr/bin/ipkg"
    
    SIMPLECMDS = [ "list", "list_installed", "update", "upgrade" ]
    PACKAGECMDS = [ "info", "status", "install", "remove" ]
    FILECMDS = [ "search" ]
    
  
    def render(self, request):
        self.args = request.args
        self.command = self.getArg("command")
        
        if self.command is not None:
            
            if self.command in IPKGResource.SIMPLECMDS:
                return self.execSimpleCmd()
            
            elif self.command in IPKGResource.PACKAGECMDS:
                return self.execPackageCmd() 
            
            elif self.command in IPKGResource.FILECMDS:
                return self.execFileCmd()
                
            else:
                return self.doErrorPage("Unknown command: ", self.command)
        else:
            return self.doIndexPage()
            

    def buildCmd(self, parms = []):
        cmd = [IPKGResource.IPKG_PATH, "ipkg", self.command] + parms
        print "[IPKG.py] cmd: %s" %cmd
        return cmd

    
    def execCmd(self, parms = []):
        cmd = self.buildCmd(parms)
        return http.Response(responsecode.OK,stream=IPKGConsoleStream(cmd) )
    
    
    def execSimpleCmd(self):
         return self.execCmd()


    def execPackageCmd(self):
        package = self.getArg("package")
        if package is not None:
            return self.execCmd([package])
        
        else:
            return self.doErrorPage("Missing parameter: package")
        
        
    def execFileCmd(self):
        file = self.getArg("file")
        if file is not None:
            return self.execCmd([file])
        
        else:
            return self.doErrorPage("Missing parameter: file")
        

    def doIndexPage(self):
        html  = "<html><body>"
        html += "<h1>Interface to IPKG</h1>"
        html += "update, ?command=update<br>"
        html += "upgrade, ?command=upgrade<br>"
        html += "list_installed, ?command=list_installed<br>"
        html += "list, ?command=list<br>"
        html += "search, ?command=search&file=&lt;filename&gt;<br>"
        html += "info, ?command=search&package=&lt;packagename&gt;<br>"
        html += "status, ?command=search&package=&lt;packagename&gt;<br>"
        html += "install, ?command=install&package=&lt;packagename&gt;<br>"
        html += "remove, ?command=remove&package=&lt;packagename&gt;<br>"
        html += "</body></html>"
        return http.Response(responsecode.OK,stream=html)

        
    def doErrorPage(self, errormsg):
        return http.Response(responsecode.OK,stream=errormsg)
    
    
    def getArg(self, key):
        if self.args.has_key(key):
            return self.args[key][0]
        else:
            return None

class IPKGConsoleStream(stream.ProducerStream):
    def __init__(self, cmd):
        stream.ProducerStream.__init__(self)
        self.container = eConsoleAppContainer()
        
        self.container.dataAvail.append(self.dataAvail)
        self.container.appClosed.append(self.cmdFinished)
        
        self.container.execute(*cmd)

    
    def cmdFinished(self, data):
        self.finish()    
            
    
    def dataAvail(self, data):
        self.write(data)
