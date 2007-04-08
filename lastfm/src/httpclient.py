from twisted.python.log import startLogging
#startLogging(open("/tmp/twisted.log",'w'))

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
                #print "BODY",l
                self.data +=l
            else:
                if l == "":
                    #print "END HEADER",l
                    self.headerread=True
                else:
                    #print "HEADER",l
                    self.header +=l
                
    def connectionMade(self):
        self.sendLine("%s %s HTTP/1.0"%(self.method,self.path))
        self.sendLine("Host: %s"%self.hostname)
        self.sendLine("User-Agent: enigma2 lastfm")
        self.sendLine("")

        
class myClientFactory(ClientFactory):

    initialDelay = 20
    maxDelay = 500
    
    def __init__(self,hostname,path,method="GET",callback=None):
        self.hangup_ok = False
        self.path=path
        self.method=method
        self.callback=callback
        self.protocol = myProtocol(hostname,self.path,method=self.method)
        
    def startedConnecting(self, connector):
        pass
    def buildProtocol(self, addr):
        return self.protocol

    def clientConnectionLost(self, connector, reason):
        if not self.hangup_ok:
            self.callback(self.protocol.data)
    def clientConnectionFailed(self, connector, reason):
        print "Connection to host failed! (%s)" % reason.getErrorMessage()
        ClientFactory.clientConnectionFailed(self, connector, reason)


class testConn:
    def __init__(self,hostname,port,path,method="GET",callback=None,errback=None):
        print hostname
        f = myClientFactory(hostname,path,method,callback)
        try:
            hostname = socket.gethostbyname(hostname)
        except socket.error:
            msg = "address %r not found" % (hostname,)
            if errback is not None:
                errback(msg)
        
        reactor.connectTCP(hostname, port, f)
#########

import base64

import socket
import string

True = 1
False = 0

class httpclientDISABLED:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.status = None
        self.headers = None
        self.response = None

    def readline(self, s):
        res = ""
        while True:
            try:
                c = s.recv(1)
            except:
                break
            res = res + c
            if c == '\n':
                break
            if not c:
                break
        #print res
        return res

    def req(self, url):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
#        if config.useproxy:
#            s.connect((config.proxyhost, config.proxyport))
#            s.send("GET http://" + self.host + ":" + str(self.port) + url + " HTTP/1.0\r\n")
#            if config.proxyuser != "":
#                s.send("Proxy-Authorization: Basic " + base64.b64encode(config.proxyuser + ":" + config.proxypass) + "\r\n")
#        else:
#            print "reg: ",self.host, self.port,url
            s.connect((self.host, self.port))
            s.send("GET " + url + " HTTP/1.0\r\n")
            s.send("Host: " + self.host + "\r\n")
            s.send("\r\n")

            line = self.readline(s)
            #print line
            self.status = string.rstrip(line)
            
            self.headers = {}
            while True:
                line = self.readline(s)
                if not line:
                    break
                if line == "\r\n":
                    break
                tmp = string.split(line, ": ")
                try:
                  self.headers[tmp[0]] = string.rstrip(tmp[1])
                except:
                  print "BUG"
                  print "self.headers[tmp[0]] = string.rstrip(tmp[1]) has no tmp[1]"
                  print line
                  print tmp              
            self.response = ""
            while True:
                line = self.readline(s)
                if not line:
                    break
                self.response = self.response + line
            s.close()
        except socket.error,e:
            print e
            self.response = ""
            return False,e
