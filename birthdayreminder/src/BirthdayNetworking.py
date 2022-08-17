from __future__ import print_function
#
#  Birthday Reminder E2 Plugin
#
#  $Id: BirthdayNetworking.py,v 1.0 2011-09-04 00:00:00 Shaderman Exp $
#
#  Coded by Shaderman (c) 2011
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons
#  Attribution-NonCommercial-ShareAlike 3.0 Unported
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially
#  distributed other than under the conditions noted above.
#


# PYTHON IMPORTS
from pickle import loads as pickle_loads
from socket import SOL_SOCKET, SO_BROADCAST
from twisted.internet.error import ConnectionDone
from twisted.internet.protocol import DatagramProtocol, ServerFactory, ClientFactory, Protocol
#from uuid import getnode # broken in Python 2.6.7 :(

# ENIGMA IMPORTS
from Components.config import config

# for localized messages
from . import _


# this class handles UDP broadcasts (send/receive)
class BroadcastProtocol(DatagramProtocol):
	def __init__(self, parent):
		self.parent = parent
		self.port = config.plugins.birthdayreminder.broadcastPort.value
		# self.uuid = str(getnode()) # sent with broadcasts to identify ourselves when receiving our own broascast :o
		self.uuid = self.getNodeHack()  # sent with broadcasts to identify ourselves when receiving our own broascast :o

	def startProtocol(self):
		self.transport.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, True)

	def sendBroadcast(self, message):
		newMessage = ''.join([self.uuid, " ", message])
		self.transport.write(newMessage, ("255.255.255.255", self.port))

	def datagramReceived(self, data, addr):
		parts = data.split()  # filter unknown data. we expect two parts, a uuid and a "command"
		if len(parts) != 2:
			return
		if parts[0] == self.uuid:  # ignore our own package
			return
		elif parts[1] == "offeringList":  # a box is offering to send a list
			print("[Birthday Reminder] received a list offer from", addr[0])
			self.parent.requestBirthdayList(addr)
		elif parts[1] == "ping":  # are we there?
			print("[Birthday Reminder] received ping from", addr[0])
			self.parent.sendPingResponse(addr)

	def getNodeHack(self):
		from os import urandom
		return urandom(16)

# the server classes are used to send and receive birthday lists


class TransferServerProtocol(Protocol):
	def __init__(self, parent):
		self.parent = parent

	def connectionMade(self):
		print("[Birthday Reminder] client %s connected" % self.transport.getPeer().host)

	def dataReceived(self, data):
		peer = self.transport.getPeer().host

		if data == "requestingList":
			print("[Birthday Reminder] sending birthday list to client", peer)

			data = self.parent.readRawFile()
			if data:
				self.transport.write(data)
		else:  # should be a pickled birthday list...
			receivedList = None
			try:  # let's see if it's pickled data
				receivedList = pickle_loads(data)
				print("[Birthday Reminder] received birthday list from", peer)
			except:
				print("[Birthday Reminder] received unknown package from", peer)

			if receivedList is None:
				return

			self.parent.writeRawFile(data)
			self.parent.load()
			self.parent.addAllTimers()
			self.parent.showReceivedMessage(len(receivedList), peer)

		self.transport.loseConnection()

	def connectionLost(self, reason):
		if reason.type == ConnectionDone:
			print("[Birthday Reminder] closed connection to client", self.transport.getPeer().host)
		else:
			print("[Birthday Reminder] lost connection to client %s. Reason: %s" % (self.transport.getPeer().host, str(reason.value)))


class TransferServerFactory(ServerFactory):
	def __init__(self, parent):
		self.parent = parent

	def buildProtocol(self, addr):
		return TransferServerProtocol(self.parent)

# the client classes are used to request and receive birthday lists


class TransferClientProtocol(Protocol):
	def __init__(self, parent, data):
		self.parent = parent
		self.data = data

	def dataReceived(self, data):
		peer = self.transport.getPeer().host

		receivedList = None
		try:
			receivedList = pickle_loads(data)
			print("[Birthday Reminder] received birthday list from", peer)
		except:
			print("[Birthday Reminder] received unknown package from", peer)

		if receivedList is None:
			return

		# save and load the received list
		self.parent.save(receivedList)
		self.parent.load()
		self.parent.addAllTimers()
		self.parent.showReceivedMessage(len(receivedList), peer)

	def connectionMade(self):
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
			print("[Birthday Reminder] disconnected from server", connector.getDestination().host)
		else:
			print("[Birthday Reminder] lost connection to server %s. Reason: %s" % (connector.getDestination().host, str(reason.value)))
