# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
#from Components.Button import Button

# Configuration
from Components.config import config, getConfigListEntry

from sets import Set

class StartupToStandbyConfiguration(Screen, ConfigListScreen):
	"""Configuration of Startup To Standby"""

	skin = """<screen name="StartupToStandbyConfiguration" title="Configure StartupToStandby" position="75,155" size="565,280">
		<widget name="config" position="5,5" size="555,100" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = "StartupToStandby Configuration"
		self.onChangedEntry = []

		# -
		self.list = [
			getConfigListEntry(_("Enabled"), config.plugins.startuptostandby.enabled),
		]

		# Define Actions
		self["actions"] = ActionMap(["SetupActions","ColorActions"],
			{
				"cancel": self.close,
			}
		)

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

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

