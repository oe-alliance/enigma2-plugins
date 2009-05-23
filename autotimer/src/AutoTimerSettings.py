# for localized messages
from . import _

# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap

# Configuration
from Components.config import config, getConfigListEntry

class AutoTimerSettings(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "Setup"

		# Summary
		self.setup_title = _("AutoTimer Settings")
		self.onChangedEntry = []

		ConfigListScreen.__init__(
			self,
			[
				getConfigListEntry(_("Poll automatically"), config.plugins.autotimer.autopoll),
				getConfigListEntry(_("Poll Interval (in h)"), config.plugins.autotimer.interval),
				getConfigListEntry(_("Show in Extensionmenu"), config.plugins.autotimer.show_in_extensionsmenu),
				getConfigListEntry(_("Modify existing Timers"), config.plugins.autotimer.refresh),
				getConfigListEntry(_("Guess existing Timer based on Begin/End"), config.plugins.autotimer.try_guessing),
				getConfigListEntry(_("Add timer as disabled on conflict"), config.plugins.autotimer.disabled_on_conflict),
				getConfigListEntry(_("Editor for new AutoTimers"), config.plugins.autotimer.editor),
			],
			session = session,
			on_change = self.changed
		)

		# Initialize widgets
		self["oktext"] = Label(_("OK"))
		self["canceltext"] = Label(_("Cancel"))
		self["ok"] = Pixmap()
		self["cancel"] = Pixmap()
		self["title"] = Label(_("AutoTimer Settings"))

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
		self.setTitle(_("Configure AutoTimer behavior"))

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

