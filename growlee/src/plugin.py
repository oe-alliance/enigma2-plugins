from Plugins.Plugin import PluginDescriptor

from Tools import Notifications
from netgrowl import GrowlRegistrationPacket, GrowlNotificationPacket, \
		GROWL_UDP_PORT, md5_constructor
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.web.client import getPage
from struct import unpack
from socket import gaierror
from urllib import urlencode

from Screens.Setup import SetupSummary
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigSubsection, \
		ConfigText, ConfigPassword, ConfigYesNo, ConfigSelection
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText

config.plugins.growlee = ConfigSubsection()
config.plugins.growlee.enable_incoming = ConfigYesNo(default=False)
config.plugins.growlee.enable_outgoing = ConfigYesNo(default=False)
config.plugins.growlee.address = ConfigText(fixed_size=False)
config.plugins.growlee.password = ConfigPassword()
config.plugins.growlee.prowl_api_key = ConfigText(fixed_size=False)
config.plugins.growlee.protocol = ConfigSelection(default="growl", choices = [("growl", "Growl"), ("snarl", "Snarl"), ("prowl", "Prowl")])

NOTIFICATIONID = 'GrowleeReceivedNotification'

class GrowleeConfiguration(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = [ "GrowleeConfiguration", "Setup" ]

		# Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		# Summary
		self.setup_title = "Growlee Configuration"
		self.onChangedEntry = []

		# Define Actions
		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
			}
		)

		config.plugins.growlee.protocol.addNotifier(self.setupList, initial_call=False)
		ConfigListScreen.__init__(
			self,
			[],
			session=session,
			on_change=self.changed
		)

		# Trigger change
		self.setupList()
		self.changed()

	def changed(self):
		for x in self.onChangedEntry:
			x()

	def setupList(self, *args):
		l = [
			getConfigListEntry(_("Type"), config.plugins.growlee.protocol),
			getConfigListEntry(_("Send Notifications?"), config.plugins.growlee.enable_outgoing),
		]

		if config.plugins.growlee.protocol.value == "prowl":
			l.append(getConfigListEntry(_("API Key"), config.plugins.growlee.prowl_api_key))
		else:
			l.extend((
				getConfigListEntry(_("Receive Notifications?"), config.plugins.growlee.enable_incoming),
				getConfigListEntry(_("Address"), config.plugins.growlee.address),
				getConfigListEntry(_("Password"), config.plugins.growlee.password),
			))

		self["config"].list = l

	def getCurrentEntry(self):
		cur = self["config"].getCurrent()
		return cur and cur[0]

	def getCurrentValue(self):
		cur = self["config"].getCurrent()
		return cur and str(cur[1].getText())

	def createSummary(self):
		return SetupSummary

	def keySave(self):
		if self["config"].isChanged():
			global port
			if port:
				def maybeConnect(*args, **kwargs):
					if config.plugins.growlee.enable_incoming.value or config.plugins.growlee.enable_outgoing.value:
						doConnect()

				d = port.stopListening()
				if d is not None:
					d.addCallback(maybeConnect).addErrback(emergencyDisable)
				else:
					maybeConnect()
			elif config.plugins.growlee.enable_incoming.value or config.plugins.growlee.enable_outgoing.value:
				doConnect()

		self.saveAll()
		self.close()

	def close(self):
		config.plugins.growlee.protocol.notifiers.remove(self.setupList)
		Screen.close(self)

def configuration(session, **kwargs):
	session.open(GrowleeConfiguration)

def doConnect():
	global port
	if config.plugins.growlee.protocol.value == "snarl":
		port = reactor.listenTCP(GROWL_UDP_PORT, growlProtocolOneWrapper)
	else:
		port = reactor.listenUDP(GROWL_UDP_PORT, growlProtocolOneWrapper)

def emergencyDisable(*args, **kwargs):
	global port
	if port:
		port.stopListening()
		port = None

	if gotNotification in Notifications.notificationAdded:
		Notifications.notificationAdded.remove(gotNotification)
	Notifications.AddPopup(
		_("Network error.\nDisabling Growlee!"),
		MessageBox.TYPE_ERROR,
		10
	)

class GrowlProtocolOneWrapper(DatagramProtocol):
	def startProtocol(self):
		proto = config.plugins.growlee.protocol.value
		if config.plugins.growlee.enable_outgoing.value and not proto == "prowl":
			addr = (config.plugins.growlee.address.value, GROWL_UDP_PORT)
			if proto == "growl":
				p = GrowlRegistrationPacket(password=config.plugins.growlee.password.value)
				p.addNotification()
				payload = p.payload()
			else: #proto == "snarl":
				payload = "type=SNP#?version=1.0#?action=register#?app=growlee\r\n"
			try:
				self.transport.write(payload, addr)
			except gaierror:
				emergencyDisable()

	def doStop(self):
		if config.plugins.growlee.enable_outgoing.value and config.plugins.growlee.protocol.value == "snarl":
			addr = (config.plugins.growlee.address.value, GROWL_UDP_PORT)
			payload = "type=SNP#?version=1.0#?action=unregister#?app=growlee\r\n"
			try:
				self.transport.write(payload, addr)
			except gaierror:
				pass
		DaragramProtocol.doStop(self)

	def sendNotification(self, *args, **kwargs):
		if not self.transport or not config.plugins.growlee.enable_outgoing.value:
			return

		proto = config.plugins.growlee.protocol.value
		if proto == "prowl":
			headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
			data = {
				'apikey': config.plugins.growlee.prowl_api_key.value,
				'application': "growlee",
				'event': kwargs.get('title', 'No title.'),
				'description': kwargs.get('description', 'No message.'),
				'priority': 0
			}

			print urlencode(data)
			getPage('https://prowl.weks.net/publicapi/add/', method = 'POST', headers = headers, postdata = urlencode(data)).addErrback(emergencyDisable)
		else:
			addr = (config.plugins.growlee.address.value, GROWL_UDP_PORT)
			if proto == "growl":
				p = GrowlNotificationPacket(*args, **kwargs)
				payload = p.payload()
			else: #proto == "snarl":
				title = kwargs.get('title', 'No title.')
				text = kwargs.get('description', 'No message.')
				timeout = kwargs.get('timeout', 10)
				payload = "type=SNP#?version=1.0#?action=notification#?app=growlee#?class=growleeClass#?title=%s#?text=%s#?timeout=%d\r\n" % (title, text, timeout)
			try:
				self.transport.write(payload, addr)
			except gaierror:
				emergencyDisable()

	def datagramReceived(self, data, addr):
		proto = config.plugins.growlee.protocol.value
		if proto == "prowl" or not config.plugins.growlee.enable_incoming.value:
			return

		Len = len(data)
		if proto == "growl":
			if Len < 16:
				return

			digest = data[-16:]
			password = config.plugins.growlee.password.value
			checksum = md5_constructor()
			checksum.update(data[:-16])
			if password:
				checksum.update(password)
			if digest != checksum.digest():
				return

			# notify packet
			if data[1] == '\x01':
				nlen, tlen, dlen, alen = unpack("!HHHH",str(data[4:12]))
				notification, title, description = unpack("%ds%ds%ds" % (nlen, tlen, dlen), data[12:Len-alen-16])

				Notifications.AddNotificationWithID(
					NOTIFICATIONID,
					MessageBox,
					text = title + '\n' + description,
					type = MessageBox.TYPE_INFO,
					timeout = 5,
					close_on_any_key = True,
				)

			# TODO: do we want to handle register packets? :-)
		else: #proto == "snarl":
			if Len < 23 or not data[:23] == "type=SNP#?version=1.0#?":
				return

			items = data[23:].split('#?')

			title = ''
			description = ''
			timeout = 5
			for item in items:
				key, value = item.split('=')
				if key == "action":
					if value != "notification":
						# NOTE: we pretent to accept pretty much everything one throws at us
						addr = (config.plugins.growlee.address.value, GROWL_UDP_PORT)
						payload = "SNP/1.0/0/OK\r\n"
						try:
							self.transport.write(payload, addr)
						except gaierror:
							emergencyDisable()
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

growlProtocolOneWrapper = GrowlProtocolOneWrapper()
port = None

def gotNotification():
	notifications = Notifications.notifications
	if notifications:
		_, screen, args, kwargs, id = notifications[-1]
		if screen is MessageBox and id != NOTIFICATIONID:

			if "text" in kwargs:
				description = kwargs["text"]
			else:
				description = args[0]
			description = description.decode('utf-8')

			growlProtocolOneWrapper.sendNotification(title="Dreambox", description=description, password=config.plugins.growlee.password.value)

def autostart(**kwargs):
	if config.plugins.growlee.enable_incoming.value or config.plugins.growlee.enable_outgoing.value:
		doConnect()

	# NOTE: we need to be the first one to be notified since other listeners
	# may remove the notifications from the list for good
	Notifications.notificationAdded.insert(0, gotNotification)

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			where=PluginDescriptor.WHERE_SESSIONSTART,
			fnc=autostart,
		),
		PluginDescriptor(
			name="Growlee",
			description=_("Configure Growlee"), 
			where=PluginDescriptor.WHERE_PLUGINMENU,
			fnc=configuration,
		),
	]

