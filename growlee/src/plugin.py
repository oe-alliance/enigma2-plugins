from Plugins.Plugin import PluginDescriptor

from Tools import Notifications

from Screens.Setup import SetupSummary
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigSubsection, \
		ConfigText, ConfigPassword, ConfigYesNo, ConfigSelection, ConfigSet, \
		ConfigSubList, ConfigNumber, NoSave
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText

from GrowleeConnection import gotNotification, emergencyDisable, growleeConnection

from . import NOTIFICATIONID

growlee = ConfigSubsection()
config.plugins.growlee = growlee
growlee.hostcount = ConfigNumber(default=0)
growlee.hosts = ConfigSubList()

def addHost(name):
	s = ConfigSubsection()
	s.name = ConfigText(default=name, fixed_size=False)
	s.enable_incoming = ConfigYesNo(default=False)
	s.enable_outgoing = ConfigYesNo(default=False)
	s.address = ConfigText(fixed_size=False)
	s.password = ConfigPassword()
	s.protocol = ConfigSelection(default="growl", choices=[("growl", "Growl"), ("gntp", "GNTP"), ("snarl", "Snarl"), ("prowl", "Prowl"), ("syslog", "Syslog UDP")])
	s.level = ConfigSelection(default="-1", choices=[("-1", _("Low (Yes/No)")), ("0", _("Normal (Information)")), ("1", _("High (Warning)")), ("2", _("Highest (Emergency)"))])
	s.blacklist = ConfigSet(choices=[])
	config.plugins.growlee.hosts.append(s)
	return s

i = 0
while i < growlee.hostcount.value:
	addHost(str(i+1))
	i += 1

# XXX: change to new config format
# NOTE: after some time, remove this and hardcode default length to 1
# since internally we assume to have at least 1 host configured
if growlee.hostcount.value == 0:
	growlee.enable_outgoing = ConfigYesNo(default=False)
	growlee.enable_incoming = ConfigYesNo(default=False)
	growlee.address = ConfigText(fixed_size=False)
	growlee.password = ConfigPassword()
	password = growlee.password.value
	growlee.prowl_api_key = ConfigText()
	growlee.protocol = ConfigSelection(default="growl", choices=[("growl", "Growl"), ("snarl", "Snarl"), ("prowl", "Prowl")])
	growlee.level = ConfigSelection(default="-1", choices=[("-1", _("Low (Yes/No)")), ("0", _("Normal (Information)")), ("1", _("High (Warning)")), ("2", _("Highest (Emergency)"))])
	growlee.blacklist = ConfigSet(choices=[])
	if growlee.protocol.value == "prowl":
		password = growlee.prowl_api_key.value

	s = addHost(_("Converted connection"))
	s.enable_incoming.value = growlee.enable_incoming.value
	s.enable_outgoing.value = growlee.enable_outgoing.value
	s.address.value = growlee.address.value
	s.password.value = password
	s.protocol.value = growlee.protocol.value
	s.level.value = growlee.level.value
	s.blacklist.value = growlee.blacklist.value

	growlee.enable_incoming.value = False
	growlee.enable_outgoing.value = False
	growlee.address.value = ""
	growlee.password.value = ""
	growlee.prowl_api_key.value = ""
	growlee.protocol.value = "growl"
	growlee.level.value = "-1"
	growlee.blacklist.value = []

	growlee.hostcount.value += 1
	growlee.save()
	del s

del i, growlee

class GrowleeConfiguration(Screen, ConfigListScreen):
	skin = """
		<screen name="GrowleeConfiguration" position="center,center" size="560,400" title="Growlee Setup" >
			<ePixmap position="0,0" size="140,40" pixmap="buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,0" size="140,40" pixmap="buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,0" size="140,40" pixmap="buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="420,0" size="140,40" pixmap="buttons/blue.png" transparent="1" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="config" position="5,45" size="550,350" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("New"))
		self["key_blue"] = StaticText(_("Delete"))

		# Summary
		self.setup_title = "Growlee Configuration"
		self.onChangedEntry = []

		# Define Actions
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"blue": self.delete,
			"yellow": self.new,
			"cancel": self.keyCancel,
			"save": self.keySave,
		})

		self.hostElement = NoSave(ConfigSelection(choices=[(x, x.name.value) for x in config.plugins.growlee.hosts]))
		self.hostElement.addNotifier(self.setupList, initial_call=False)
		ConfigListScreen.__init__(
			self,
			[],
			session=session,
			on_change=self.changed
		)
		self.cur = self.hostElement.value

		# Trigger change
		self.setupList()
		self.changed()

	def delete(self):
		from Screens.MessageBox import MessageBox

		self.session.openWithCallback(
			self.deleteConfirm,
			MessageBox,
			_("Really delete this entry?\nIt cannot be recovered!")
		)

	def deleteConfirm(self, result):
		if result and config.plugins.growlee.hostcount.value > 0:
			config.plugins.growlee.hostcount.value -= 1
			config.plugins.growlee.hosts.remove(self.cur)
			self.hostElement.setChoices([(x, x.name.value) for x in config.plugins.growlee.hosts])
			self.cur = self.hostElement.value

	def new(self):
		self.cur = addHost(_("New connection"))
		config.plugins.growlee.hostcount.value += 1
		self.hostElement.setChoices([(x, x.name.value) for x in config.plugins.growlee.hosts])
		self.hostElement.setValue(self.cur)

	def changed(self):
		for x in self.onChangedEntry:
			x()

	def setupList(self, *args):
		last = self.cur
		if self.setupList in last.protocol.notifiers:
			last.protocol.removeNotifier(self.setupList)
		cur = self.hostElement.value
		self.cur = cur
		cur.protocol.addNotifier(self.setupList, initial_call=False)

		l = [
			getConfigListEntry(_("Host"), self.hostElement),
			getConfigListEntry(_("Name"), cur.name),
			getConfigListEntry(_("Type"), cur.protocol),
			getConfigListEntry(_("Minimum Priority"), cur.level),
			getConfigListEntry(_("Send Notifications?"), cur.enable_outgoing),
		]

		proto = cur.protocol.value
		if proto ==  "prowl":
			l.append(getConfigListEntry(_("API Key"), cur.password))
		else:
			if proto != "gntp":
				l.append(getConfigListEntry(_("Receive Notifications?"), cur.enable_incoming))
			l.append(getConfigListEntry(_("Address"), cur.address))
			if proto == "growl" or proto == "gntp":
				l.append(
					getConfigListEntry(_("Password"), cur.password)
				)

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
		config.plugins.growlee.save()
		if self["config"].isChanged():
			def doConnect(*args, **kwargs):
				growleeConnection.listen()

			d = growleeConnection.stop()
			if d is not None:
				d.addCallback(doConnect).addErrback(emergencyDisable)
			else:
				maybeConnect()

		self.saveAll()
		self.close()

	def close(self):
		if self.setupList in self.cur.protocol.notifiers:
			self.cur.protocol.removeNotifier(self.setupList)
		Screen.close(self)

def configuration(session, **kwargs):
	session.open(GrowleeConfiguration)

def autostart(reason, **kwargs):
	if reason == 0:
		if hasattr(Notifications, 'notificationQueue'):
			addedList = Notifications.notificationQueue.addedCB
		else:
			addedList = Notifications.notificationAdded
		# NOTE: we need to be the first one to be notified since other listeners
		# may remove the notifications from the list for good
		addedList.insert(0, gotNotification)

		growleeConnection.listen()

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			where=PluginDescriptor.WHERE_AUTOSTART,
			fnc=autostart,
			needsRestart = False,
		),
		PluginDescriptor(
			name="Growlee",
			description=_("Configure Growlee"), 
			where=PluginDescriptor.WHERE_PLUGINMENU,
			fnc=configuration,
			needsRestart = False,
		),
	]

