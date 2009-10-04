from twisted.internet import reactor
from twisted.internet import protocol
from twisted.internet import ssl
from twisted.internet import defer
from twisted.mail import imap4

from Tools import Notifications
from Screens.MessageBox import MessageBox
from twisted.internet.protocol import ReconnectingClientFactory

import time
# from twisted.python import log
# log.startLogging(open("/tmp/twisted.log","w"))
from . import debug
# defer.setDebugging(True)

class SimpleIMAP4Client(imap4.IMAP4Client):
	greetDeferred = None
	def __init__(self,e2session, contextFac = None):
		self.e2session = e2session
		imap4.IMAP4Client.__init__(self,contextFactory = contextFac)
		
	def serverGreeting(self, caps):
		debug("[SimpleIMAP4Client] serverGreeting: %s" %caps)
		self.serverCapabilities = caps
		if self.greetDeferred is not None:
			self.greetDeferred(self)

class SimpleIMAP4ClientFactory(protocol.ReconnectingClientFactory):
	
	protocol = SimpleIMAP4Client

	def __init__(self, e2session, username, factory):
		self.maxDelay = 30
		self.noisy = True
		self.ctx = factory
		self.e2session = e2session
		self.username = username

	def buildProtocol(self, addr):
		debug("[SimpleIMAP4ClientFactory] building protocol: %s" %addr)
		p = self.protocol(self.e2session,contextFac = self.ctx)
		p.factory = self
		p.greetDeferred = self.e2session.onConnect
		auth = imap4.CramMD5ClientAuthenticator(self.username)
		p.registerAuthenticator(auth)
		return p

	def startedConnecting(self, connector):
		debug("[SimpleIMAP4ClientFactory] startedConnecting: %s" %time.ctime())

	def clientConnectionFailed(self, connector, reason):
		debug("[SimpleIMAP4ClientFactory] clientConnectionFailed: %s" %reason.getErrorMessage())
		self.e2session.onConnectFailed(reason)
		ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

	def clientConnectionLost(self, connector, reason):
		debug("[SimpleIMAP4ClientFactory] clientConnectionLost: %s" %reason.getErrorMessage())
		self.e2session.onConnectFailed(reason)
		ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

def createFactory( e2session,username,hostname, port):
	debug("createFactory: for %s@%s:%s at %s" %(username,hostname,port, "time: %s" %time.ctime()))

	f2 = ssl.ClientContextFactory()
	factory = SimpleIMAP4ClientFactory(e2session, username, f2)
	if port == 993:
		c = reactor.connectSSL( hostname, port,factory,f2)
	else:
		c = reactor.connectTCP( hostname, port,factory)

	debug("createFactory: factory started")
	return factory