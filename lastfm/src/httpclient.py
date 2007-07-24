from twisted.internet.protocol import ClientFactory
from twisted.web2.client.http import HTTPClientProtocol
from twisted.internet import reactor, error
from urlparse import urlsplit
from socket import gethostbyname

global HTTPCLIENT_requestCount
HTTPCLIENT_requestCount = 0 # counts requests
    
class Enigma2HTTPRequest:
        
    def __init__(self,hostname,path,port,method="GET",headerfields={}):
        self.hostname=hostname
        self.port=port
        self.path=path
        self.method=method
        self.headerfields = headerfields
        self.onRequestFinished = []
        self.onRequestError = []
        self.onHeaderLoaded = []
        
        self.data=""
        self.readsize = 0
        self.headers= {}
        
    def _DataRecived(self,data):
        self.readsize += len(data)
        self.data += data
            
    def getIPAdress(self):
        """    
            socket.gethostbyname() is syncron
            Enigma2 is blocked while process is running    
        """
        try:
            return gethostbyname(self.hostname)
        except:
            return False
        
    def HeaderLoaded(self,headers):
        self.headers = headers
        for i in self.onHeaderLoaded:
            if i is not None:
                i(headers)
        self.onHeaderLoaded=[]
        
    def RequestError(self,error):
        for i in self.onRequestError:
            if i is not None:
                i(error)
        self.onRequestError = []
        
    def RequestFinished(self,data):
        for i in self.onRequestFinished:
            if i is not None:
                i(data)
       
class Enigma2URLHTTPRequest(Enigma2HTTPRequest):
    def __init__(self,url,method="GET",headerfields={}):
        x= urlsplit(url)
        if x[1].rfind(":")>0:
            y = x[1].split(":")
            hostname = y[0]
            port = int(y[1])
        else:
            hostname = x[1]
            port = 80
        path=x[2]
        Enigma2HTTPRequest.__init__(self,hostname,path,port,method=method,headerfields=headerfields)

class Enigma2FileHTTPRequest(Enigma2URLHTTPRequest):
    def __init__(self,targetfile,url,method="GET",headerfields={}):
        Enigma2URLHTTPRequest.__init__(self,url,method=method,headerfields=headerfields)
        self.filehandle = open(targetfile,"w")
        self.onRequestFinished.append(self.close)
        self.onRequestError.append(self.close)
    def close(self,dummy):
        self.filehandle.close()
    
    def _DataRecived(self,data):
        self.readsize += len(data)
        self.filehandle.write(data)
        
            
        
        
class Enigma2HTTPProtocol(HTTPClientProtocol):
    DEBUG = False
    
    def __init__(self,request,requestCount):
        self.request = request
        self.requestCount = requestCount
        self.headers={}
        self.headerread=False
        self.responseFirstLine = True # to indikate, that first line of responseheader was read
        HTTPClientProtocol.__init__(self)
        self.setRawMode()
        
    def rawDataReceived(self,line):
        for l in line.split(self.delimiter): 
            if self.headerread:
                self.request._DataRecived(l)
            else:
                if self.DEBUG:
                    print "HTTP "+self.requestCount+" <<==",l
                if l == "":
                    self.headerread = True
                    self.request.HeaderLoaded(self.headers)
                else:
                    self.parseHeaderLine(l)
    
    def parseHeaderLine(self,line):
        if self.responseFirstLine is  True:
            #print "parseHeaderLine",line.split(" ")
            fields = line.split(" ")
            protocoll = fields[0]
            responsecode  = fields[1]
            statuscode = " ".join(fields[2:])
            self.headers["protocoll"] = protocoll
            self.headers["responsecode"] = responsecode
            self.headers["statuscode"] = statuscode
            self.responseFirstLine = False
        elif line.rfind(":"):
            x = line.split(":")
            key = x[0].lstrip().rstrip().lower()
            var = ":".join(x[1:]).lstrip()
            self.headers[key] = var        
        else:
            print "unknown headerline",line

    def connectionMade(self):
        if self.request.method == "POST":
            (path,params ) = self.request.path.split("?")
        elif self.request.method == "GET":
            path = self.request.path
        self.sendLine("%s %s HTTP/1.0"%(self.request.method,path))
        self.sendLine("Host: %s"%self.request.hostname)
        for i in self.request.headerfields:
            self.sendLine(i+": "+self.request.headerfields[i])
        if self.request.method == "POST":
            self.sendLine("Content-Type: application/x-www-form-urlencoded")
            self.sendLine("Content-Length: "+str(len(params)))
        
        self.sendLine("")
        if self.request.method == "POST":
            self.sendLine(params)
    
    def sendLine(self,data):
        if self.DEBUG:
            print "HTTP "+self.requestCount+" ==>>",data
        HTTPClientProtocol.sendLine(self,data)
        
class Enigma2HTTPClientFactory(ClientFactory):

    initialDelay = 20
    maxDelay = 500
    def __init__(self,request):
        self.hangup_ok = False
        self.request = request
       
    def startedConnecting(self, connector):
        pass
    
    def buildProtocol(self, addr):
        global HTTPCLIENT_requestCount
        HTTPCLIENT_requestCount = HTTPCLIENT_requestCount + 1
        return Enigma2HTTPProtocol(self.request,str(HTTPCLIENT_requestCount))

    def clientConnectionLost(self, connector, reason):
        if not self.hangup_ok:
            self.request.RequestFinished(self.request.data)
        ClientFactory.clientConnectionLost(self, connector, reason)
        
    def clientConnectionFailed(self, connector, reason):
        self.request.RequestError(reason.getErrorMessage())
        ClientFactory.clientConnectionFailed(self, connector, reason)

def getURL(url,callback=None,errorback=None,headercallback=None,method="GET",headers={}):
    """ 
        this will is called with a url
        url = http://www.hostna.me/somewhere/on/the/server <string>
    """
    req = Enigma2URLHTTPRequest(url,method=method,headerfields=headers)
    req.onRequestError.append(errorback)
    req.onHeaderLoaded.append(headercallback)
    req.onRequestFinished.append(callback)
    ipadress = req.getIPAdress()
    if ipadress is not False:
        reactor.connectTCP(ipadress,req.port, Enigma2HTTPClientFactory(req))
        return req
    else:
        if errorback is not None:
            errorback("Error while resolve Hostname")

def getPage(hostname,port,path,method="GET",callback=None,errorback=None,headercallback=None,headers={}):
    """ 
        this will is called with separte hostname,port,path
        hostname = www.hostna.me <string>
        port = 80 <int>
        path= /somewhere/on/the/server <string>
    """
    req = Enigma2HTTPRequest(hostname,path,port,method=method,headerfields=headers)
    req.onRequestError.append(errorback)
    req.onRequestFinished.append(callback)
    ipadress = req.getIPAdress()
    if ipadress is not False:
        reactor.connectTCP(ipadress,req.port, Enigma2HTTPClientFactory(req))
        return req
    else:
        if errorback is not None:
            errorback("Error while resolve Hostname")

def getFile(filename,url,method="GET",callback=None,errorback=None,headercallback=None,headers={}):
    """ 
        this will is called with a url and a target file
        fimename = /tmp/target.jpg 
        url = http://www.hostna.me/somewhere/on/the/server.jpg <string>
    """
    req = Enigma2FileHTTPRequest(filename,url,method=method,headerfields=headers)
    req.onRequestError.append(errorback)
    req.onHeaderLoaded.append(headercallback)
    req.onRequestFinished.append(callback)
    ipadress = req.getIPAdress()
    if ipadress is not False:
        reactor.connectTCP(ipadress,req.port, Enigma2HTTPClientFactory(req))
        return req
    else:
        if errorback is not None:
            errorback("Error while resolve Hostname")

