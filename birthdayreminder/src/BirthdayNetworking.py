# PYTHON IMPORTS
from pickle import loads as pickle_loads
from six import ensure_binary
from socket import SOL_SOCKET, SO_BROADCAST
from twisted.internet.error import ConnectionDone
from twisted.internet.protocol import DatagramProtocol, ServerFactory, ClientFactory, Protocol

# ENIGMA IMPORTS
from Components.config import config

# for localized messages
from . import _


class BroadcastProtocol(DatagramProtocol):  # this class handles UDP broadcasts (send/receive)
	def __init__(self, parent):
		self.parent = parent
		self.port = config.plugins.birthdayreminder.broadcastPort.value
		self.uuid = self.getNodeHack()  # sent with broadcasts to identify ourselves when receiving our own broascast :o

	def startProtocol(self):
		if self.transport:
			self.transport.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, True)

	def sendBroadcast(self, message):
		if self.transport:
			newMessage = ensure_binary(''.join([self.uuid, " ", message]))
			self.transport.write(newMessage, ("255.255.255.255", self.port))

	def datagramReceived(self, data, addr):
		parts = data.split()  # filter unknown data. we expect two parts, a uuid and a "command"
		if len(parts) != 2:
			return
		if parts[0] == self.uuid:  # ignore our own package
			return
		elif parts[1] == "offeringList":  # a box is offering to send a list
			print("[Birthday Reminder] received a list offer from %s" % addr[0])
			self.parent.requestBirthdayList(addr)
		elif parts[1] == "ping":  # are we there?
			print("[Birthday Reminder] received ping from %s" % addr[0])
			self.parent.sendPingResponse(addr)

	def getNodeHack(self):
		from os import urandom
		return str(urandom(16))


class TransferServerProtocol(Protocol):  # the server classes are used to send and receive birthday lists
	def __init__(self, parent):
		self.parent = parent

	def connectionMade(self):
		if self.transport:
			print("[Birthday Reminder] client %s connected" % self.transport.getPeer().host)

	def dataReceived(self, data):
		peer = self.transport.getPeer().host if self.transport else None
		if data == "requestingList":
			print("[Birthday Reminder] sending birthday list to client %s" % peer)
			data = self.parent.readRawFile()
			if data and self.transport:
				self.transport.write(data)
		else:  # should be a pickled birthday list...
			receivedList = None
			try:  # let's see if it's pickled data
				receivedList = pickle_loads(data)
				print("[Birthday Reminder] received birthday list from %s" % peer)
			except Exception as err:
				print("[Birthday Reminder] received unknown package from %s" % peer)
			if receivedList is None:
				return
			self.parent.writeRawFile(data)
			self.parent.load()
			self.parent.addAllTimers()
			self.parent.showReceivedMessage(len(receivedList), peer)
		if self.transport:
			self.transport.loseConnection()

	def connectionLost(self, reason):
		if self.transport:
			if reason.type == ConnectionDone:
				print("[Birthday Reminder] closed connection to client %s" % self.transport.getPeer().host)
			else:
				print("[Birthday Reminder] lost connection to client %s. Reason: %s" % (self.transport.getPeer().host, str(reason.value)))


class TransferServerFactory(ServerFactory):
	def __init__(self, parent):
		self.parent = parent

	def buildProtocol(self, addr):
		return TransferServerProtocol(self.parent)


class TransferClientProtocol(Protocol):  # the client classes are used to request and receive birthday lists
	def __init__(self, parent, data):
		self.parent = parent
		self.data = data

	def dataReceived(self, data):
		peer = self.transport.getPeer().host if self.transport else None
		receivedList = None
		try:
			receivedList = pickle_loads(data)
			print("[Birthday Reminder] received birthday list from %s" % peer)
		except Exception as err:
			print("[Birthday Reminder] received unknown package from %s" % peer)
		if receivedList is None:
			return
		self.parent.save(receivedList)  # save and load the received list
		self.parent.load()
		self.parent.addAllTimers()
		self.parent.showReceivedMessage(len(receivedList), peer)

	def connectionMade(self):
		if self.transport:
			self.transport.write(self.data)


class TransferClientFactory(ClientFactory):
	def __init__(self, parent, data):
		self.parent = parent
		self.data = data

	def buildProtocol(self, addr):
		return TransferClientProtocol(self.parent, self.data)

	def startedConnecting(self, connector):
		dest = ''.join([connector.getDestination().host, ":", str(connector.getDestination().port)])

	def clientConnectionFailed(self, connector, reason):
		print("[Birthday Reminder] connection to server %s failed. Reason: %s" % (connector.getDestination().host, str(reason.value)))

	def clientConnectionLost(self, connector, reason):
		if reason.type == ConnectionDone:
			print("[Birthday Reminder] disconnected from server %s" % connector.getDestination().host)
		else:
			print("[Birthday Reminder] lost connection to server %s. Reason: %s" % (connector.getDestination().host, str(reason.value)))
