from netgrowl import GrowlRegistrationPacket, GrowlNotificationPacket, \
		GROWL_UDP_PORT, md5_constructor
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from struct import unpack

from Tools import Notifications
from Components.config import config

from GrowleeConnection import emergencyDisable
from . import NOTIFICATIONID

class GrowlTalk(DatagramProtocol):
	addr = None

	def gotIP(self, ip):
		self.addr = (ip, GROWL_UDP_PORT)
		if config.plugins.growlee.enable_outgoing.value:
			p = GrowlRegistrationPacket(application="growlee", password=config.plugins.growlee.password.value)
			p.addNotification()
			payload = p.payload()

			self.transport.write(payload, self.addr)

	def noIP(self, error):
		emergencyDisable()

	def startProtocol(self):
		reactor.resolve(config.plugins.growlee.address.value).addCallback(self.gotIP).addErrback(self.noIP)

	def sendNotification(self, *args, **kwargs):
		if not self.transport or not self.addr or not config.plugins.growlee.enable_outgoing.value:
			return

		kwargs["application"] = "growlee"
		kwargs["password"] = config.plugins.growlee.password.value
		p = GrowlNotificationPacket(*args, **kwargs)
		payload = p.payload()

		self.transport.write(payload, self.addr)

	def datagramReceived(self, data, addr):
		if not config.plugins.growlee.enable_incoming.value:
			return

		Len = len(data)
		if Len < 16:
			return

		# ver == GROWL_PROTOCOL_VERSION
		if data[0] != '\x01':
			return

		# type == GROWL_TYPE_NOTIFICATION
		if data[1] == '\x01':
			digest = data[-16:]
			password = config.plugins.growlee.password.value
			checksum = md5_constructor()
			checksum.update(data[:-16])
			if password:
				checksum.update(password)
			if digest != checksum.digest():
				return

			nlen, tlen, dlen, alen = unpack("!HHHH",str(data[4:12]))
			notification, title, description = unpack("%ds%ds%ds" % (nlen, tlen, dlen), data[12:Len-alen-16])
		# type == GROWL_TYPE_NOTIFICATION_NOAUTH
		elif data[1] == '\x05':
			nlen, tlen, dlen, alen = unpack("!HHHH",str(data[4:12]))
			notification, title, description = unpack("%ds%ds%ds" % (nlen, tlen, dlen), data[12:Len-alen])
		else:
			# don't handle any other packet yet
			return

		Notifications.AddNotificationWithID(
			NOTIFICATIONID,
			MessageBox,
			text = title + '\n' + description,
			type = MessageBox.TYPE_INFO,
			timeout = 5,
			close_on_any_key = True,
		)

class GrowlTalkAbstraction:
	def __init__(self):
		self.growltalk = GrowlTalk()
		self.serverPort = reactor.listenUDP(GROWL_UDP_PORT, self.growltalk)

	def sendNotification(self, *args, **kwargs):
		# map timeout -> sticky
		if "timeout" in kwargs:
			if kwargs["timeout"] == -1:
				kwargs["sticky"] = True
			del kwargs["timeout"]

		self.growltalk.sendNotification(*args, **kwargs)

	def stop(self):
		return self.serverPort.stopListening()

