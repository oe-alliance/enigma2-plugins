# -*- coding: utf-8 -*-
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory, ServerFactory
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver

from Screens.MessageBox import MessageBox
from Tools import Notifications

from GrowleeConnection import emergencyDisable
from . import NOTIFICATIONID

SNP_TCP_PORT = 9887

class SnarlNetworkProtocol(LineReceiver):
	def __init__(self, client = False):
		self.client = client

	def connectionMade(self):
		self.factory.addClient(self)
		if self.client:
			payload = "type=SNP#?version=1.0#?action=register#?app=growlee"
			self.sendLine(payload)

			payload = "type=SNP#?version=1.0#?action=add_class#?app=growlee#?class=growleeClass#?title=Notifications from your Dreambox"
			self.sendLine(payload)

	def connectionLost(self, reason):
		self.factory.removeClient(self)

	def stop(self):
		if self.client:
			payload = "type=SNP#?version=1.0#?action=unregister#?app=growlee"
			self.sendLine(payload)

		self.transport.loseConnection()

	def sendNotification(self, title='No title.', description='No message.', timeout=1):
		if not self.client or not self.transport:
			return

		payload = "type=SNP#?version=1.0#?action=notification#?app=growlee#?class=growleeClass#?title=%s#?text=%s#?timeout=%d" % (title, description, timeout)
		self.sendLine(payload)

	def lineReceived(self, data):
		if self.client or not self.transport:
			return

		Len = len(data)
		if Len < 23 or not data[:23] == "type=SNP#?version=1.0#?":
			return

		items = data[23:].split('#?')

		title = ''
		description = ''
		timeout = 5
		for item in items:
			key, value = item.split('=')
			if key == "action":
				if value == "unregister":
					payload = "SNP/1.0/0/OK"
					self.sendLine(payload)
					self.transport.loseConnection()
					return
				elif value != "notification":
					# NOTE: we pretend to handle&accept pretty much everything one throws at us
					payload = "SNP/1.0/0/OK"
					self.sendLine(payload)
					return
			elif key == "title":
				title = value
			elif key == "text":
				description = value
			elif key == "timeout":
				timeout = int(value)

		Notifications.AddNotificationWithID(
			NOTIFICATIONID,
			MessageBox,
			text = title + '\n' + description,
			type = MessageBox.TYPE_INFO,
			timeout = timeout,
			close_on_any_key = True,
		)

		# return ok
		payload = "SNP/1.0/0/OK"
		self.sendLine(payload)

class SnarlNetworkProtocolClientFactory(ClientFactory):
	client = None

	def buildProtocol(self, addr):
		p = SnarlNetworkProtocol(client = True)
		p.factory = self
		return p

	def sendNotification(self, title='No title.', description='No message.', priority=0, timeout=-1):
		if self.client:
			title = title.decode('utf-8', 'ignore').encode('iso8859-15', 'ignore')
			description = description.decode('utf-8', 'ignore').encode('iso8859-15', 'ignore')

			# NOTE: timeout = 0 means sticky, so add one second to map -1 to 0 and make 0 non-sticky
			if timeout < 1:
				timeout += 1

			self.client.sendNotification(title=title, description=description, timeout=timeout)

	def addClient(self, client):
		self.client = client

	def removeClient(self, client):
		self.client = None

class SnarlNetworkProtocolServerFactory(ServerFactory):
	protocol = SnarlNetworkProtocol

	def __init__(self):
		self.clients = []

	def addClient(self, client):
		self.clients.append(client)

	def removeClient(self, client):
		self.clients.remove(client)

	def sendNotification(self, *args, **kwargs):
		pass

	def stopFactory(self):
		for client in self.clients:
			client.stop()

class SnarlNetworkProtocolAbstraction:
	clientPort = None
	serverPort = None
	pending = 0

	def __init__(self, host):
		self.clientFactory = SnarlNetworkProtocolClientFactory()
		self.serverFactory = SnarlNetworkProtocolServerFactory()

		if host.enable_outgoing.value:
			reactor.resolve(host.address.value).addCallback(self.gotIP).addErrback(self.noIP)

		if host.enable_incoming.value:
			self.serverPort = reactor.listenTCP(SNP_TCP_PORT, self.serverFactory)
			self.pending += 1

	def gotIP(self, ip):
		self.clientPort = reactor.connectTCP(ip, SNP_TCP_PORT, self.clientFactory)
		self.pending += 1

	def noIP(self, error):
		emergencyDisable()

	def sendNotification(self, *args, **kwargs):
		self.clientFactory.sendNotification(*args, **kwargs)

	def maybeClose(self, resOrFail, defer = None):
		self.pending -= 1
		if self.pending == 0:
			if defer:
				defer.callback(True)

	def stop(self):
		defer = Deferred()
		if self.clientPort:
			d = self.clientPort.disconnect()
			if d:
				d.addBoth(self.maybeClose, defer = defer)
			else:
				self.pending -= 1

		if self.serverPort:
			d = self.serverPort.stopListening()
			if d:
				d.addBoth(self.maybeClose, defer = defer)
			else:
				self.pending -= 1

		if self.pending == 0:
			reactor.callLater(1, defer.callback, True)
		return defer

