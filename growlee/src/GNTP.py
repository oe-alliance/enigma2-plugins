# -*- coding: utf-8 -*-
from __future__ import print_function

from twisted.internet.protocol import Protocol, ReconnectingClientFactory, ServerFactory
from twisted.internet.defer import Deferred
from twisted.internet import reactor
import hashlib
import uuid
import re
import threading
import collections

our_print = lambda *args, **kwargs: print("[growlee.GNTP]", *args, **kwargs)

try:
	from Screens.MessageBox import MessageBox
	from Tools import Notifications

	from GrowleeConnection import emergencyDisable
	from . import NOTIFICATIONID
except ImportError:
	def emergencyDisable():
		our_print('Fallback emergencyDisabled called, stopping reactor')
		reactor.stop()

GNTP_TCP_PORT = 23053

try:
	dict.iteritems
	iteritems = lambda d: d.iteritems()
except AttributeError:
	iteritems = lambda d: d.items()

class GNTPPacket:
	version = '1.0'
	password = ''
	hashAlgorithm = None
	encryptionAlgorithm = None
	def encode(self):
		# TODO: add encryption support
		message = u'GNTP/%s %s ' % (self.version, self.messageType)

		if self.encryptionAlgorithm is None:
			message += u'NONE'
		else:
			message += u'%s:%s' % (self.encryptionAlgorithm, self.ivValue)

		if self.hashAlgorithm is not None:
			message += u' %s:%s.%s' % (self.hashAlgorithm, self.keyHash, self.salt)

		message += u'\r\n'
		return message

	def set_password(self, password, hashAlgorithm='MD5', encryptionAlgorithm=None):
		if password is None:
			self.password = None
			self.hashAlgorithm = None
			self.encryptionAlgorithm = None

		hashes = {
				'MD5': hashlib.md5,
				'SHA1': hashlib.sha1,
				'SHA256': hashlib.sha256,
				'SHA512': hashlib.sha512,
		}
		hashAlgorithm = hashAlgorithm.upper()
		
		if not hashAlgorithm in hashes:
			raise Exception('Unsupported hash algorithm: %s' % hashAlgorithm)
		if encryptionAlgorithm is not None:
			raise Exception('Unsupported encryption algorithm: %s' % encryptionAlgorithm)

		hashfunction = hashes.get(hashAlgorithm)
		password = password.encode('utf8')
		seed = uuid.uuid4().hex
		salt = hashfunction(seed).hexdigest()
		saltHash = hashfunction(seed).digest()
		keyBasis = password+saltHash
		key = hashfunction(keyBasis).digest()
		keyHash = hashfunction(key).hexdigest()

		self.hashAlgorithm = hashAlgorithm
		self.keyHash = keyHash.upper()
		self.salt = salt.upper()

class GNTPRegister(GNTPPacket):
	messageType = 'REGISTER'
	def __init__(self, applicationName=None):
		assert applicationName, "There needs to be an application name set"
		self.applicationName = applicationName
		self.notifications = []
	
	def add_notification(self, name, displayName=None, enabled=True):
		assert name, "Notifications need a name"
		note = {
			'Notification-Name': name,
			'Notification-Enabled': enabled,
		}
		if displayName is not None:
			note['Notification-Display-Name'] = displayName
		self.notifications.append(note)

	def encode(self):
		assert self.notifications, "At least one notification needs to be registered"
		base = GNTPPacket.encode(self)
		base += u"Application-Name: %s\r\n" % self.applicationName
		base += u"Notifications-Count: %d\r\n" % len(self.notifications)

		for note in self.notifications:
			base += u'\r\n'
			for key, value in iteritems(note):
				base += u'%s: %s\r\n' % (key, value)
		base += u'\r\n'
		return base.encode('utf8', 'replace')

class GNTPNotice(GNTPPacket):
	messageType = 'NOTIFY'
	def __init__(self, applicationName, name, title, text='', sticky=False, priority=0):
		assert priority > -3 and priority < 3, "Priority has to be between -2 and 2"
		self.applicationName = applicationName
		self.name = name
		self.title = title
		self.text = text
		self.sticky = sticky
		self.priority = priority
		self.pendingVerification = None

	def encode(self):
		base = GNTPPacket.encode(self)
		base += u"Application-Name: %s\r\n" % self.applicationName
		base += u"Notification-Name: %s\r\n" % self.name
		base += u"Notification-Text: %s\r\n" % self.text.replace('\r\n', '\n') # NOTE: just in case replace CRLF by LF so we don't break protocol
		base += u"Notification-Title: %s\r\n" % self.title
		base += u"Notification-Sticky: %s\r\n" % self.sticky
		base += u"Notification-Priority: %s\r\n" % self.priority
		base += u"Notifications-Count: 1\r\n"
		base += u'\r\n'
		return base.encode('utf8', 'replace')

class GNTP(Protocol):
	def __init__(self, client=False, host=None, registered=False):
		self.client = client
		self.host = host
		self.registered = registered
		self.__buffer = ''
		self.defer = None
		self.messageLock = threading.Lock()
		self.messageQueue = collections.deque()

	def connectionMade(self):
		if self.client and not self.registered:
			self.messageLock.acquire()

			register = GNTPRegister('growlee')
			register.set_password(self.host.password.value, 'MD5', None)
			register.add_notification("Notifications from your Dreambox", enabled=True)

			our_print("about to send packet:", register.encode().replace('\r\n', '<CRLF>\n'))
			self.transport.write(register.encode())

	def sendNotification(self, title='No title.', description='No description.', sticky=False, priority=0):
		if not self.client or not self.transport:
			return

		note = GNTPNotice('growlee', "Notifications from your Dreambox", title, text=description, sticky=sticky, priority=priority)
		note.set_password(self.host.password.value, 'MD5', None)
		self.messageQueue.append(note)
		self.sendQueuedMessage()

	def sendQueuedMessage(self):
		if not self.registered:
			our_print("not registered though there are queued messages... something is weird!")
			return
		if not self.messageLock.acquire(False):
			return
		try:
			note = self.messageQueue.popleft()
		except IndexError:
			self.messageLock.release()
		else:
			msg = note.encode()
			our_print("about to send packet:", msg.replace('\r\n', '<CRLF>\n'))
			self.transport.write(msg)
			def writeAgain():
				note.set_password(self.host.password.value, 'MD5', None)
				msg = note.encode()
				our_print("about to re-send packet:", msg.replace('\r\n', '<CRLF>\n'))
				self.transport.write(msg)
				# return to "normal" operation in 5 seconds regardless of state
				self.pendingVerification = None
				self.messageLock.release()
				reactor.callLater(5, self.sendQueuedMessage)
			self.pendingVerification = reactor.callLater(30, writeAgain)

	def dataReceived(self, data):
		# only parse complete packages
		self.__buffer += data
		if data[-4:] != '\r\n\r\n': return
		data = self.__buffer
		self.__buffer = ''

		# TODO: proper implementation
		our_print(data.replace('\r\n', '<CRLF>\n'))
		match = re.match('GNTP/(?P<version>\d+\.\d+) (?P<messagetype>REGISTER|NOTIFY|SUBSCRIBE|\-OK|\-ERROR)', data, re.IGNORECASE)
		if not match:
			our_print('invalid/partial return')
			try:
				self.messageLock.release()
			except Exception as e:
				our_print("error releasing lock, something is wierd!", e)
			return
		type = match.group('messagetype')
		if type == '-OK' or type == '-ERROR':
			try:
				self.messageLock.release()
			except Exception as e:
				our_print("error releasing lock, something is wierd!", e)
			match = re.search('Response-Action: (?P<messagetype>.*?)\r', data, re.IGNORECASE)
			if not match:
				our_print('no action found in data')
				return
			rtype = match.group('messagetype')
			if rtype == 'REGISTER':
				self.registered = type == '-OK'
			elif rtype == 'NOTIFY':
				if self.pendingVerification and type == '-OK':
					self.pendingVerification.cancel()
					self.pendingVerification = None
			reactor.callLater(10, self.sendQueuedMessage)


class GNTPClientFactory(ReconnectingClientFactory):
	client = None
	registered = False

	def __init__(self, host):
		self.host = host

	def buildProtocol(self, addr):
		self.client = p = GNTP(client=True, host=self.host, registered=self.registered)
		p.factory = self
		return p

	def clientConnectionLost(self, connector, reason):
		self.registered = self.client.registered
		ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

	def sendNotification(self, *args, **kwargs):
		if self.client:
			self.client.sendNotification(*args, **kwargs)

class GNTPServerFactory(ServerFactory):
	protocol = GNTP

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

class GNTPAbstraction:
	clientPort = None
	serverPort = None
	pending = 0

	def __init__(self, host):
		self.clientFactory = GNTPClientFactory(host)
		self.serverFactory = GNTPServerFactory()

		if host.enable_outgoing.value:
			reactor.resolve(host.address.value).addCallback(self.gotIP).addErrback(self.noIP)

		if host.enable_incoming.value:
			self.serverPort = reactor.listenTCP(GNTP_TCP_PORT, self.serverFactory)
			self.pending += 1

	def gotIP(self, ip):
		self.clientPort = reactor.connectTCP(ip, GNTP_TCP_PORT, self.clientFactory)
		self.pending += 1

	def noIP(self, error):
		emergencyDisable()

	def sendNotification(self, title='No title.', description='No description.', priority=-1, timeout=-1):
		self.clientFactory.sendNotification(title=title, description=description, sticky=timeout==-1, priority=priority)

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

if __name__ == '__main__':
	class Value:
		def __init__(self, value):
			self.value = value
	class Config:
		address = Value('moritz-venns-macbook-pro')
		password = Value('')
		enable_outgoing = Value(True)
		enable_incoming = Value(True)

	def callLater():
		gntp = GNTPAbstraction(Config)
		reactor.callLater(3, gntp.sendNotification)
		reactor.callLater(5, lambda: gntp.sendNotification('Dreambox', 'A record has been started:\nDummy recoding.', priority=0, timeout=5))
	reactor.callLater(1, callLater)
	reactor.run()
