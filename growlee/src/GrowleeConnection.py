# -*- coding: utf-8 -*-
from Components.config import config
from Tools import Notifications
from Screens.MessageBox import MessageBox
from twisted.internet.defer import Deferred
from twisted.internet import reactor

from . import NOTIFICATIONID

def emergencyDisable(*args, **kwargs):
	if args:
		try: args[0].printTraceback()
		except Exception: pass

	global growleeConnection
	if growleeConnection:
		growleeConnection.stop()

	if hasattr(Notifications, 'notificationQueue'):
		addedList = Notifications.notificationQueue.addedCB
	else:
		addedList = Notifications.notificationAdded
	if gotNotification in addedList:
		addedList.remove(gotNotification)
	Notifications.AddPopup(
		_("Network error.\nDisabling Growlee until next restart!"),
		MessageBox.TYPE_ERROR,
		10
	)

def gotNotification():
	if hasattr(Notifications, 'notificationQueue'):
		notifications = Notifications.notificationQueue.queue
		def handler(note):
			return note.fnc, note.screen, note.args, note.kwargs, note.id
	else:
		notifications = Notifications.notifications
		handler = lambda note: note
	if notifications:
		_, screen, args, kwargs, id = handler(notifications[-1])
		if screen is MessageBox and id != NOTIFICATIONID:

			# NOTE: priority is in [-2; 2] but type is [0; 3] so map it
			# XXX: maybe priority==type-2 would be more appropriate
			priority = kwargs.get("type", 0) - 1
			timeout = kwargs.get("timeout", -1)

			if "text" in kwargs:
				description = kwargs["text"]
			else:
				description = args[0]
			description = description

			growleeConnection.sendNotification(title="Dreambox", description=description, priority=priority, timeout=timeout, id=id)

class GrowleeConnection:
	connections = []
	pending = 0

	def sendNotification(self, title="Dreambox", description='', priority=-1, timeout=-1, id=""):
		for connection, host in self.connections:
			try:
				level = int(host.level.value)
			except ValueError:
				level = -1

			if connection and id not in host.blacklist.value and not priority < level:
				connection.sendNotification(title=title, description=description, priority=priority, timeout=timeout)

	def listen(self):
		if self.connections:
			return

		for host in config.plugins.growlee.hosts:
			if not (host.enable_outgoing.value or host.enable_incoming.value):
				continue

			proto = host.protocol.value
			if proto == "prowl":
				from Prowl import ProwlAPI
				connection = ProwlAPI(host)
			elif proto == "growl":
				from GrowlTalk import GrowlTalkAbstraction
				connection = GrowlTalkAbstraction(host)
			elif proto == "gntp":
				from GNTP import GNTPAbstraction
				connection = GNTPAbstraction(host)
			elif proto == "snarl":
				from SNP import SnarlNetworkProtocolAbstraction
				connection = SnarlNetworkProtocolAbstraction(host)
			else: # proto == "syslog":
				from Syslog import SyslogAbstraction
				connection = SyslogAbstraction(host)

			self.connections.append((connection, host))

	def maybeClose(self, resOrFail, defer = None):
		self.pending -= 1
		if self.pending == 0:
			if defer: defer.callback(True)

	def stop(self):
		defer = Deferred()
		self.pending = 0
		for connection, host in self.connections:
			d = connection.stop()
			if d is not None:
				self.pending += 1
				d.addBoth(self.maybeClose, defer = defer)
		del self.connections[:]

		if self.pending == 0:
			reactor.callLater(1, defer, True)
		return defer

growleeConnection = GrowleeConnection()

