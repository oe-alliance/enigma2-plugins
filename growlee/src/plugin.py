from Plugins.Plugin import PluginDescriptor

from Tools import Notifications

from Screens.Setup import SetupSummary
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigSubsection, \
		ConfigText, ConfigPassword, ConfigYesNo, ConfigSelection, ConfigSet, \
		ConfigSubList, NoSave
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText

from GrowleeConnection import gotNotification, emergencyDisable, growleeConnection

from . import NOTIFICATIONID

growlee = ConfigSubsection()
config.plugins.growlee = growlee
growlee.hostcount = ConfigNumber(default=0)
growlee.hosts = ConfigSubList()

i = 0
while i < growlee.hostcount.value:
	s = ConfigSubsection()
	s.name = ConfigText(default=str(i+1), fixed_size=False)
	s.enable_incoming = ConfigYesNo(default=False)
	s.enable_outgoing = ConfigYesNo(default=False)
	s.address = ConfigText(fixed_size=False)
	s.password = ConfigPassword()
	s.protocol = ConfigSelection(default="growl", choices=[("growl", "Growl"), ("snarl", "Snarl"), ("prowl", "Prowl")])
	s.level = ConfigSelection(default="-1", choices=[("-1", _("Low (Yes/No)")), ("0", _("Normal (Information)")), ("1", _("High (Warning)")), ("2", _("Highest (Emergency)"))])
	s.blacklist = ConfigSet(choices=[])
	growlee.hosts.append(s)
	i += 1
	del s

# XXX: change to new config format
growlee.enable_outgoing = ConfigYesNo(default=False)
if growlee.hostcount.value == 0 and growlee.enable_outgoing.value:
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

	s = ConfigSubsection()
	s.name = ConfigText(default="1", fixed_size=False)
	s.enable_incoming = ConfigYesNo(default=False)
	s.enable_outgoing = ConfigYesNo(default=False)
	s.address = ConfigText(fixed_size=False)
	s.password = ConfigPassword()
	s.protocol = ConfigSelection(default="growl", choices=[("growl", "Growl"), ("snarl", "Snarl"), ("prowl", "Prowl")])
	s.level = ConfigSelection(default="-1", choices=[("-1", _("Low (Yes/No)")), ("0", _("Normal (Information)")), ("1", _("High (Warning)")), ("2", _("Highest (Emergency)"))])
	s.blacklist = ConfigSet(choices=[])

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
	growlee.hosts.append(s)

	growlee.save()
	del s

del i, growlee

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

		self.hostElement = NoSave(ConfigSelection(choices=[(x, x.name.value) for x in config.plugins.growlee.hosts]))
		self.hostElement.addNotifier(self.setupList, initial_call=False)
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
		last = self.cur
		if self.setupList in last.protocol.notifiers:
			last.protocol.notifiers.remove(self.setupList)
		cur = self.hostElement.value
		cur.protocol.notifiers.append(self.setupList)

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
			l.extend((
				getConfigListEntry(_("Receive Notifications?"), cur.enable_incoming),
				getConfigListEntry(_("Address"), cur.address),
			))
			if proto == "growl":
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
		if self["config"].isChanged():
			def maybeConnect(*args, **kwargs):
				if config.plugins.growlee.enable_incoming.value or config.plugins.growlee.enable_outgoing.value:
					growleeConnection.listen()

			d = growleeConnection.stop()
			if d is not None:
				d.addCallback(maybeConnect).addErrback(emergencyDisable)
			else:
				maybeConnect()

		self.saveAll()
		self.close()

	def close(self):
		config.plugins.growlee.protocol.notifiers.remove(self.setupList)
		Screen.close(self)

def configuration(session, **kwargs):
	session.open(GrowleeConfiguration)

def autostart(**kwargs):
	# NOTE: we need to be the first one to be notified since other listeners
	# may remove the notifications from the list for good
	Notifications.notificationAdded.insert(0, gotNotification)

	if config.plugins.growlee.enable_incoming.value or config.plugins.growlee.enable_outgoing.value:
		growleeConnection.listen()

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

