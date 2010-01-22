from Plugins.Plugin import PluginDescriptor

from Tools import Notifications

from Screens.Setup import SetupSummary
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigSubsection, \
		ConfigText, ConfigPassword, ConfigYesNo, ConfigSelection, ConfigSet
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText

from GrowleeConnection import gotNotification, emergencyDisable, growleeConnection

from . import NOTIFICATIONID

config.plugins.growlee = ConfigSubsection()
config.plugins.growlee.enable_incoming = ConfigYesNo(default=False)
config.plugins.growlee.enable_outgoing = ConfigYesNo(default=False)
config.plugins.growlee.address = ConfigText(fixed_size=False)
config.plugins.growlee.password = ConfigPassword()
config.plugins.growlee.prowl_api_key = ConfigText(fixed_size=False)
config.plugins.growlee.protocol = ConfigSelection(default="growl", choices = [("growl", "Growl"), ("snarl", "Snarl"), ("prowl", "Prowl")])
config.plugins.growlee.level = ConfigSelection(default=-1, choices = [(-1, _("Low (Yes/No)")), (0, _("Normal (Information)")), (1, _("High (Warning)")), (2, _("Highest (Emergency)"))])
config.plugins.growlee.blacklist = ConfigSet(choices = [])

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
			getConfigListEntry(_("Minimum Priority"), config.plugins.growlee.level),
			getConfigListEntry(_("Send Notifications?"), config.plugins.growlee.enable_outgoing),
		]

		proto = config.plugins.growlee.protocol.value
		if proto ==  "prowl":
			l.append(getConfigListEntry(_("API Key"), config.plugins.growlee.prowl_api_key))
		else:
			l.extend((
				getConfigListEntry(_("Receive Notifications?"), config.plugins.growlee.enable_incoming),
				getConfigListEntry(_("Address"), config.plugins.growlee.address),
			))
			if proto == "growl":
				l.append(
					getConfigListEntry(_("Password"), config.plugins.growlee.password)
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
			d.addCallback(maybeConnect).addErrback(emergencyDisable)

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

