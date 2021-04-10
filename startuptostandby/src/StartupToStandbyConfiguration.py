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


class StartupToStandbyConfiguration(Screen, ConfigListScreen):
	"""Configuration of Startup To Standby"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ["StartupToStandbyConfiguration", "Setup"]

		# Summary
		self.setup_title = _("StartupToStandby Configuration")
		self.onChangedEntry = []

		# Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
			}
		)

		ConfigListScreen.__init__(
			self,
			[
				getConfigListEntry(_("Enabled"), config.plugins.startuptostandby.enabled)
			],
			session=session,
			on_change=self.changed
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
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
