from twisted.internet import reactor
from twisted.internet.protocol import ClientFactory,connectionDone
from twisted.web2.client.http import HTTPClientProtocol

from twisted.internet import error 

import socket

class myProtocol(HTTPClientProtocol):
    path = "/"
    method = "GET"
    data=""
    header=""
    headerread=False
    def __init__(self,hostname,path,method="GET"):
        self.path=path
        self.method=method
        self.hostname=hostname
        HTTPClientProtocol.__init__(self)
        self.setRawMode()
        
    def rawDataReceived(self,line):
        for l in line.split(self.delimiter): 
            if self.headerread:
                self.data +=l
            else:
                if l == "":
                    self.headerread=True
                else:
                    self.header +=l
                
    def connectionMade(self):
        self.sendLine("%s %s HTTP/1.0"%(self.method,self.path))
        self.sendLine("Host: %s"%self.hostname)
        self.sendLine("User-Agent: enigma2 lastfm")
        self.sendLine("")

        
class myClientFactory(ClientFactory):

    initialDelay = 20
    maxDelay = 500
    
    def __init__(self,hostname,path,method="GET",callback=None,errorback=None):
        self.hangup_ok = False
        self.path=path
        self.method=method
        self.callback=callback
        self.errorback=errorback
        self.protocol = myProtocol(hostname,self.path,method=self.method)
        
    def startedConnecting(self, connector):
        pass
    def buildProtocol(self, addr):
        return self.protocol

    def clientConnectionLost(self, connector, reason):
        if not self.hangup_ok:
            self.callback(self.protocol.data)
    def clientConnectionFailed(self, connector, reason):
        if self.errorback is not None:
            self.errorback(reason.getErrorMessage())
        ClientFactory.clientConnectionFailed(self, connector, reason)


class testConn:
    def __init__(self,hostname,port,path,method="GET",callback=None,errorback=None):
        f = myClientFactory(hostname,path,method,callback,errorback)
        try:
            hostname = socket.gethostbyname(hostname)
        except socket.error:
            msg = "address %r not found" % (hostname,)
            if errorback is not None:
                errorback(msg)
        
        reactor.connectTCP(hostname, port, f)
