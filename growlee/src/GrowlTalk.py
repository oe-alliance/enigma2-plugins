# -*- coding: utf-8 -*-
from __future__ import print_function

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from struct import pack, unpack
from hashlib import md5

from Screens.MessageBox import MessageBox
from Tools import Notifications

from GrowleeConnection import emergencyDisable
from . import NOTIFICATIONID

GROWL_UDP_PORT = 9887

class GrowlTalk(DatagramProtocol):
	addr = None

	def __init__(self, host):
		self.host = host

	def gotIP(self, ip):
		self.addr = (ip, GROWL_UDP_PORT)
		if self.host.enable_outgoing.value:
			p = pack("!BBHBB",
					1, # version
					0, # registration
					7, # length of application name == len("growlee")
					1, # one notification
					1, # one of them default
			)
			p += "growlee" # application name
			p += pack("!H",
					32, # length of first notification type name
			)
			p += "Notifications from your Dreambox" # first notification type name
			p += "\x00" # index of default notifications

			password = self.host.password.value
			checksum = md5()
			checksum.update(p)
			if password:
				checksum.update(password)
			p += checksum.digest()

			self.transport.write(p, self.addr)

	def noIP(self, error):
		print("--------------------------------", error)
		emergencyDisable()

	def startProtocol(self):
		reactor.resolve(self.host.address.value).addCallback(self.gotIP).addErrback(self.noIP)

	def sendNotification(self, title='No title.', description='No description.', flags=0):
		if not self.transport or not self.addr or not self.host.enable_outgoing.value:
			return

		p = pack("!BBHHHHH",
				1, # version
				1, # notification
				flags, # 3-bit signed priority, 1 bit sticky in rightmost nibble
				32, # len("Notifications from your Dreambox")
				len(title),
				len(description),
				7, # len("growlee")
		)
		p += "Notifications from your Dreambox"
		p += title
		p += description
		p += "growlee"

		password = self.host.password.value
		checksum = md5()
		checksum.update(p)
		if password:
			checksum.update(password)
		p += checksum.digest()

		self.transport.write(p, self.addr)

	def datagramReceived(self, data, addr):
		if not self.host.enable_incoming.value:
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
			password = self.host.password.value
			checksum = md5()
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
	def __init__(self, host):
		self.growltalk = GrowlTalk(host)
		listeningPort = GROWL_UDP_PORT if host.enable_incoming.value else 0
		self.serverPort = reactor.listenUDP(listeningPort, self.growltalk)

	def sendNotification(self, title='No title.', description='No description.', priority=-1, timeout=-1):
		if priority < 0:
			flags = 8 + (-priority << 1)
		else:
			flags = priority << 1

		# NOTE: sticky didn't work in any of my tests, but let's assume this is my configurations fault
		if timeout == -1:
			flags |= 1

		self.growltalk.sendNotification(title=title, description=description, flags=flags)

	def stop(self):
		return self.serverPort.stopListening()

