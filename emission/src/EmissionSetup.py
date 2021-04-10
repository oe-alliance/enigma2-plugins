# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

# Configuration
from Components.config import config, getConfigListEntry


class EmissionSetup(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ["EmissionSetup", "Setup"]

		# Summary
		self.setup_title = _("eMission settings")
		self.onChangedEntry = []

		ConfigListScreen.__init__(
			self,
			[
				getConfigListEntry(_("Hostname"), config.plugins.emission.hostname),
				getConfigListEntry(_("Username"), config.plugins.emission.username),
				getConfigListEntry(_("Password"), config.plugins.emission.password),
				getConfigListEntry(_("Port"), config.plugins.emission.port),
				getConfigListEntry(_("Auto-add torrent enclosures from SimpleRSS"), config.plugins.emission.autodownload_from_simplerss),
			],
			session=session,
			on_change=self.changed
		)

		# Initialize widgets
		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
			}
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(self.setup_title)

	def changed(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

