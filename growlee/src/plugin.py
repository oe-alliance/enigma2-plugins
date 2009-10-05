from Plugins.Plugin import PluginDescriptor

from Tools import Notifications
from netgrowl import GrowlRegistrationPacket, GrowlNotificationPacket, \
		GROWL_UDP_PORT, md5_constructor
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from struct import unpack
from socket import gaierror

from Screens.Setup import SetupSummary
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigSubsection, \
		ConfigText, ConfigPassword, ConfigYesNo
from Components.ConfigList import ConfigListScreen

config.plugins.growlee = ConfigSubsection()
config.plugins.growlee.enable_incoming = ConfigYesNo(default=False)
config.plugins.growlee.enable_outgoing = ConfigYesNo(default=False)
config.plugins.growlee.address = ConfigText(fixed_size=False)
config.plugins.growlee.password = ConfigPassword()

class GrowleeConfiguration(Screen, ConfigListScreen):
	skin = """<screen title="Growlee Configuration" position="center,center" size="565,280">
		<widget name="config" position="5,5" size="555,100" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = "Growlee Configuration"
		self.onChangedEntry = []

		# Define Actions
		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keySave,
			}
		)

		ConfigListScreen.__init__(
			self,
			[
				getConfigListEntry(_("Receive Notifications?"), config.plugins.growlee.enable_incoming),
				getConfigListEntry(_("Send Notifications?"), config.plugins.growlee.enable_outgoing),
				getConfigListEntry(_("Address"), config.plugins.growlee.address),
				getConfigListEntry(_("Password"), config.plugins.growlee.password),
			],
			session=session,
			on_change=self.changed
		)

		# Trigger change
		self.changed()

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except:
				pass

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def keySave(self):
		if self["config"].isChanged():
			global port
			if port:
				def maybeConnect(*args, **kwargs):
					if config.plugins.growlee.enable_incoming.value or config.plugins.growlee.enable_outgoing.value:
						global port
						port = reactor.listenUDP(GROWL_UDP_PORT, growlProtocolOneWrapper)

				d = port.stopListening()
				if d is not None:
					d.addCallback(maybeConnect).addErrback(emergencyDisable)
				else:
					maybeConnect()
			elif config.plugins.growlee.enable_incoming.value or config.plugins.growlee.enable_outgoing.value:
				port = reactor.listenUDP(GROWL_UDP_PORT, growlProtocolOneWrapper)

		self.saveAll()
		self.close()

def configuration(session, **kwargs):
	session.open(GrowleeConfiguration)

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
		if config.plugins.growlee.enable_outgoing.value:
			addr = (config.plugins.growlee.address.value, GROWL_UDP_PORT)
			p = GrowlRegistrationPacket(password=config.plugins.growlee.password.value)
			p.addNotification()
			try:
				self.transport.write(p.payload(), addr)
			except gaierror:
				emergencyDisable()

	def sendNotification(self, *args, **kwargs):
		if not self.transport or not config.plugins.growlee.enable_outgoing.value:
			return

		addr = (config.plugins.growlee.address.value, GROWL_UDP_PORT)
		p = GrowlNotificationPacket(*args, **kwargs)
		try:
			self.transport.write(p.payload(), addr)
		except gaierror:
			emergencyDisable()

	def datagramReceived(self, data, addr):
		Len = len(data)
		if Len < 16 or not config.plugins.growlee.enable_incoming.value:
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
			notification, title, description = unpack(("%ds%ds%ds") % (nlen, tlen, dlen), data[12:Len-alen-16])

			# XXX: we should add a proper fix :-)
			Notifications.notificationAdded.remove(gotNotification)
			Notifications.AddPopup(
				title + '\n' + description,
				MessageBox.TYPE_INFO,
				5
			)
			Notifications.notificationAdded.insert(0, gotNotification)

		# TODO: do we want to handle register packets? :-)

growlProtocolOneWrapper = GrowlProtocolOneWrapper()
port = None

def gotNotification():
	notifications = Notifications.notifications
	if notifications:
		_, screen, args, kwargs, _ = notifications[-1]
		if screen is MessageBox:

			if "text" in kwargs:
				description = kwargs["text"]
			else:
				description = args[0]
			description = description.decode('utf-8')

			growlProtocolOneWrapper.sendNotification(title="Dreambox", description=description, password=config.plugins.growlee.password.value)

def autostart(**kwargs):
	if config.plugins.growlee.enable_incoming.value or config.plugins.growlee.enable_outgoing.value:
		global port
		port = reactor.listenUDP(GROWL_UDP_PORT, growlProtocolOneWrapper)

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

