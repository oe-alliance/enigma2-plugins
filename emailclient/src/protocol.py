from twisted.internet import reactor
from twisted.internet import protocol
from twisted.internet import ssl
from twisted.internet import defer
from twisted.internet import stdio
from twisted.mail import imap4
from twisted.protocols import basic

class SimpleIMAP4Client(imap4.IMAP4Client):
    greetDeferred = None
    def __init__(self,e2session, contextFactory = None):
        self.e2session = e2session
        imap4.IMAP4Client.__init__(self,contextFactory = contextFactory)
        
    def serverGreeting(self, caps):
        self.serverCapabilities = caps
        if self.greetDeferred is not None:
            d, self.greetDeferred = self.greetDeferred, None
            d.callback(self)

class SimpleIMAP4ClientFactory(protocol.ClientFactory):
    
    protocol = SimpleIMAP4Client

    def __init__(self, e2session, username, onConn):
        self.ctx = ssl.ClientContextFactory()
        self.e2session = e2session
        self.username = username
        self.onConn = onConn

    def buildProtocol(self, addr):
        p = self.protocol(self.e2session,self.ctx)
        p.factory = self
        p.greetDeferred = self.onConn
        auth = imap4.CramMD5ClientAuthenticator(self.username)
        p.registerAuthenticator(auth)
        return p
    
    def clientConnectionFailed(self, connector, reason):
        d, self.onConn = self.onConn, None
        d.errback(reason)

def createFactory( e2session,username,hostname, port):
    print "creating factory for ",username,hostname,port
    onConn = defer.Deferred(
        ).addCallback(e2session.onConnect
        ).addErrback(e2session.onConnectFailed
        )

    factory = SimpleIMAP4ClientFactory(e2session,username, onConn)
    reactor.connectTCP(hostname, port, factory)
    