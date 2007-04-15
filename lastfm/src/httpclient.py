from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory,connectionDone
from twisted.web2.client.http import HTTPClientProtocol
from twisted.internet import error 
import urlparse

import socket

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
        
    def getIPAdress(self):
        """    
            socket.gethostbyname() is syncron
            Enigma2 is blocked while process is running    
        """
        return socket.gethostbyname(self.hostname)

    def HeaderLoaded(self,headers):
        self.headers = headers
        for i in self.onHeaderLoaded:
            i(headers)
        self.onHeaderLoaded=[]
        
    def RequestError(self,error):
        for i in self.onRequestError:
            i(error)
        self.onRequestError = []
        
    def RequestFinished(self,data):
        for i in self.onRequestFinished:
            i(data)
       
class Enigma2URLHTTPRequest(Enigma2HTTPRequest):
    def __init__(self,url,method="GET",headerfields={}):
        x= urlparse.urlsplit(url)
        if x[1].rfind(":")>0:
            y = x[1].split(":")
            hostname = y[0]
            port = int(y[1])
        else:
            hostname = x[1]
            port = 80
        path=x[2]
        Enigma2HTTPRequest.__init__(self,hostname,path,port,method=method,headerfields=headerfields)
    
class Enigma2HTTPProtocol(HTTPClientProtocol):
    headers={}
    headerread=False
    responseFirstLine = True # to indikate, that first line of responseheader was read

    def __init__(self,request):
        self.request = request
        HTTPClientProtocol.__init__(self)
        self.setRawMode()
        
    def rawDataReceived(self,line):
        for l in line.split(self.delimiter): 
            if self.headerread:
                self.request.data +=l
            else:
                if l == "":
                    self.headerread = True
                    self.request.HeaderLoaded(self.headers)
                else:
                    self.parseHeaderLine(l)
    
    def parseHeaderLine(self,line):
        if self.responseFirstLine is  True:
            (protocoll,responsecode,statuscode) = line.split(" ")
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
        self.sendLine("%s %s HTTP/1.0"%(self.request.method,self.request.path))
        self.sendLine("Host: %s"%self.request.hostname)
        for i in self.request.headerfields:
            self.sendLine(i+": "+self.request.headerfields[i])
        self.sendLine("")

        
class Enigma2HTTPClientFactory(ClientFactory):

    initialDelay = 20
    maxDelay = 500
    
    def __init__(self,request):
        self.hangup_ok = False
        self.request = request
       
    def startedConnecting(self, connector):
        pass
    
    def buildProtocol(self, addr):
        return Enigma2HTTPProtocol(self.request)

    def clientConnectionLost(self, connector, reason):
        if not self.hangup_ok:
            self.request.RequestFinished(self.request.data)
        ClientFactory.clientConnectionLost(self, connector, reason)
        
    def clientConnectionFailed(self, connector, reason):
        if self.errorback is not None:
            self.request.RequestError(reason.getErrorMessage())
        ClientFactory.clientConnectionFailed(self, connector, reason)

def getURL(url,callback=None,errorback=None,headercallback=None,method="GET",headers={}):
    """ 
        this will is called with a url
        url = http://www.hostna.me/somewhere/on/the/server <string>
    """
    req = Enigma2URLHTTPRequest(url,method=method,headerfields=headers)
    req.onRequestError.append(errorback)
    req.onRequestFinished.append(callback)
    reactor.connectTCP(req.getIPAdress(),req.port, Enigma2HTTPClientFactory(req))

def getPage(hostname,port,path,method="GET",callback=None,errorback=None):#,headercallback=None,headers={}):
    """ 
        this will is called with separte hostname,port,path
        hostname = www.hostna.me <string>
        port = 80 <int>
        path= /somewhere/on/the/server <string>
    """
    req = Enigma2HTTPRequest(hostname,path,port,method=method)#,headerfields=headers)
    req.onRequestError.append(errorback)
    req.onRequestFinished.append(callback)
    reactor.connectTCP(req.getIPAdress(),req.port, Enigma2HTTPClientFactory(req))

def getFile(filename,url,method="GET",callback=None,errorback=None,headercallback=None,headers={}):
    """ 
        this will is called with a url and a target file
        fimename = /tmp/target.jpg 
        url = http://www.hostna.me/somewhere/on/the/server.jpg <string>
    """
    def save(data):
        try:
            fp = open(filename,"w")
            fp.write(data)
            fp.close()
            if callback is not None:
                callback()
        except Exception,e:
            if errorback is not None:
                errorback(e)
    getURL(url,method=method,callback=save,errorback=errorback,headercallback=headercallback,headers=headers)
