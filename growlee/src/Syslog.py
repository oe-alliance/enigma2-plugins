# -*- coding: utf-8 -*-
from __future__ import print_function

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.internet import reactor
from time import strftime, strptime, localtime
from os import uname

from Screens.MessageBox import MessageBox
from Tools import Notifications

from GrowleeConnection import emergencyDisable
from . import NOTIFICATIONID

SYSLOG_UDP_PORT = 514

FACILITY = {
	'kern': 0, 'user': 1, 'mail': 2, 'daemon': 3,
	'auth': 4, 'syslog': 5, 'lpr': 6, 'news': 7,
	'uucp': 8, 'cron': 9, 'authpriv': 10, 'ftp': 11,
	'local0': 16, 'local1': 17, 'local2': 18, 'local3': 19,
	'local4': 20, 'local5': 21, 'local6': 22, 'local7': 23,
}

SEVERITY = {
	'emerg': 0, 'alert':1, 'crit': 2, 'err': 3,
	'warning': 4, 'notice': 5, 'info': 6, 'debug': 7
}

try:
	dict.iteritems
	reverse = lambda map: dict((v,k) for k,v in map.iteritems())
except AttributeError:
	reverse = lambda map: dict((v,k) for k,v in map.items())

SEVERITYMAP = {
	-1: SEVERITY['info'],
	MessageBox.TYPE_YESNO: SEVERITY['debug'],
	MessageBox.TYPE_INFO: SEVERITY['info'],
	MessageBox.TYPE_WARNING: SEVERITY['warning'],
	MessageBox.TYPE_ERROR: SEVERITY['err'],
}

class SyslogNetworkProtocol(DatagramProtocol):
	addr = None
	def __init__(self, host):
		self.host = host

	def gotIP(self, ip):
		self.addr = (ip, SYSLOG_UDP_PORT)

	def noIP(self, error):
		print("--------------------------------", error)
		emergencyDisable()

	def startProtocol(self):
		reactor.resolve(self.host.address.value).addCallback(self.gotIP).addErrback(self.noIP)

	def sendNotification(self, title='No title.', description='No message.', priority=0):
		if not self.transport or not self.addr or not self.host.enable_outgoing.value:
			return

		ltime = localtime()
		day = strftime("%d", ltime)
		if day[0] == "0":
			day = " " + day[1:]
		value = strftime("%b %%s %H:%M:%S", ltime)
		timestamp = value % (day,)
		payload = "<%d>%s %s growlee: (%s) %s" % (FACILITY['local0'] * 8 + SEVERITYMAP[priority], timestamp, uname()[1], title, description.replace('\n', ' '),)
		# TODO: better way to stay within the 1024 char-limit (e.g. ignore title, multiple packets, ...)
		#if len(payload) > 1024:
		#	payload = payload[:1024]
		self.transport.write(payload, self.addr)

	def datagramReceived(self, data, addr):
		if not self.host.enable_incoming.value:
			return

		Len = len(data)
		# NOTE: since we're capable of handling longer messages, lets just do so
		# even if they do not comply to the protocol
		#if Len > 1024: # invalid according to rfc
		#	return

		# read prio field
		prio, data = data.split('>', 1)
		prio = int(prio[1:])
		facility, severity = divmod(prio, 8) # just the ids
		#facility = reverse(FACILITY)[facility]
		type = reverse(SEVERITYMAP).get(severity, MessageBox.TYPE_ERROR)

		# parse remaining header
		try:
			# try to parse timestamp to determine validity
			timestamp = strptime(data[:15], '%b %d %H:%M:%S')
		except ValueError:
			message = data
		else:
			hostname, body = data[16:].split(' ', 1)
			# NOTE: we could re-process timestamp to get a customized display format,
			# but lets just keep this for now
			message = hostname + ' @ ' + data[:15] + ': ' + body

		Notifications.AddNotificationWithID(
			NOTIFICATIONID,
			MessageBox,
			text = message,
			type = type,
			timeout = 10, # XXX: un-hardcode timeout?
			close_on_any_key = True,
		)

class SyslogAbstraction:
	def __init__(self, host):
		self.syslog = SyslogNetworkProtocol(host)
		listeningPort = SYSLOG_UDP_PORT if host.enable_incoming.value else 0
		self.serverPort = reactor.listenUDP(listeningPort, self.syslog)

	def sendNotification(self, title='No title.', description='No description.', priority=-1, timeout=-1):
		self.syslog.sendNotification(title=title, description=description, priority=priority)

	def stop(self):
		return self.serverPort.stopListening()
