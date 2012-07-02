from twisted.internet import reactor, protocol, ssl
from twisted.mail import imap4

# from twisted.internet import defer
# from twisted.python import log
# log.startLogging(open("/tmp/twisted.log","w"))
# defer.setDebugging(True)
from . import debug #@UnresolvedImport # pylint: disable-msg=F0401

class SimpleIMAP4Client(imap4.IMAP4Client):
	greetDeferred = None
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
		pr = self.protocol(contextFactory = self.ctx)
		pr.factory = self
		pr.greetDeferred = self.e2session.onConnect
		auth = imap4.CramMD5ClientAuthenticator(self.username)
		pr.registerAuthenticator(auth)
		return pr

	def startedConnecting(self, connector):
		debug("[SimpleIMAP4ClientFactory] startedConnecting")

	def clientConnectionFailed(self, connector, reason):
		# debug("[SimpleIMAP4ClientFactory] clientConnectionFailed: %s" %reason.getErrorMessage())
		self.e2session.onConnectionFailed(reason)
		protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

	def clientConnectionLost(self, connector, reason):
		# debug("[SimpleIMAP4ClientFactory] clientConnectionLost: %s" %reason.getErrorMessage())
		self.e2session.onConnectionLost(reason)
		protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

def createFactory(e2session, username, hostname, port):
	debug("createFactory: for %s@%s:%s" %(username, hostname, port))

	f2 = ssl.ClientContextFactory()
	factory = SimpleIMAP4ClientFactory(e2session, username, f2)
	if port == 993:
		reactor.connectSSL(hostname, port, factory, f2) #@UndefinedVariable # pylint: disable-msg=E1101
	else:
		reactor.connectTCP(hostname, port, factory) #@UndefinedVariable # pylint: disable-msg=E1101

	debug("createFactory: factory started")
	return factory