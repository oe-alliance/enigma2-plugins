from enigma import eConsoleAppContainer

from twisted.web2 import resource, stream, responsecode, http

class IPKGResource(resource.Resource):
    def render(self, req):
       self.args = req.args
       if self.getArg("command") == "update":
           return self.doUpdate()
       elif self.getArg("command") == "upgrade":
           return self.doUpgrade()
       elif self.getArg("command") == "list_installed":
           return self.doListInstalled()
       elif self.getArg("command") == "list":
           return self.doListAvaiable()
       elif self.getArg("command") == "search":
           return self.doSearch()
       elif self.getArg("command") == "info":
           return self.doInfo()
       elif self.getArg("command") == "status":
           return self.doInfo()
       elif self.getArg("command") == "install":
           return self.doInstall()
       elif self.getArg("command") == "remove":
           return self.doRemove()
       elif self.getArg("command"):
           return self.doErrorPage("no or unknown command")
       else:
           return self.doIndexPage()

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

    def doUpdate(self):
        return http.Response(responsecode.OK,stream=IPKGConsoleStream("ipkg update"))
        
    def doUpgrade(self):
        return http.Response(responsecode.OK,stream=IPKGConsoleStream("ipkg upgrade"))
        
    def doListInstalled(self):
        return http.Response(responsecode.OK,stream=IPKGConsoleStream("ipkg list_installed"))
        
    def doListAvaiable(self):
        return http.Response(responsecode.OK,stream=IPKGConsoleStream("ipkg list"))

    def doSearch(self):
        if self.getArg("file"):
            return http.Response(responsecode.OK,stream=IPKGConsoleStream("ipkg search "+self.getArg("file")))
        else:
            return self.doErrorPage("no file to search givven")

    def doInfo(self):
        if self.getArg("package"):
            return http.Response(responsecode.OK,stream=IPKGConsoleStream("ipkg info "+self.getArg("package")))
        else:
            return self.doErrorPage("no package to print info givven")

    def doStatus(self):
        if self.getArg("package"):
            return http.Response(responsecode.OK,stream=IPKGConsoleStream("ipkg status "+self.getArg("package")))
        else:
            return self.doErrorPage("no package to print status givven")

    def doInstall(self):
        if self.getArg("package"):
            return http.Response(responsecode.OK,stream=IPKGConsoleStream("ipkg install "+self.getArg("package")))
        else:
            return self.doErrorPage("no package to install givven")

    def doRemove(self):
        if self.getArg("package"):
            return http.Response(responsecode.OK,stream=IPKGConsoleStream("ipkg remove "+self.getArg("package")))
        else:
            return self.doErrorPage("no package to remove givven")

    def doListAvaiable(self):
        return http.Response(responsecode.OK,stream=IPKGConsoleStream("ipkg list"))
        
    def doErrorPage(self,errormsg):
        return http.Response(responsecode.OK,stream=errormsg)
    
    def getArg(self,key):
        if self.args.has_key(key):
            return self.args[key][0]
        else:
            return False

class IPKGConsoleStream(stream.ProducerStream):
    def __init__(self,cmd):
        stream.ProducerStream.__init__(self)
        self.container = eConsoleAppContainer()
        self.container.appClosed.append(self.cmdFinished)
        self.container.dataAvail.append(self.dataAvail)
        self.container.execute(cmd)

    def cmdFinished(self,data):
        self.finish()    
            
    def dataAvail(self,data):
        self.write(data)
