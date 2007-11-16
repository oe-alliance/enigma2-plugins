# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Button import Button

# Configuration
from Components.config import config, getConfigListEntry

class AutoTimerConfiguration(Screen, ConfigListScreen):
	"""Configuration of AutoTimer"""

	skin = """<screen name="AutoTimerConfiguration" title="Configure AutoTimer" position="75,155" size="565,280">
		<widget name="config" position="5,5" size="555,225" scrollbarMode="showOnDemand" />
		<ePixmap position="0,235" zPosition="4" size="140,40" pixmap="skin_default/key-red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,235" zPosition="4" size="140,40" pixmap="skin_default/key-green.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = "AutoTimer Configuration"
		self.onChangedEntry = []

		self.list = [
			getConfigListEntry(_("Poll automatically"), config.plugins.autotimer.autopoll),
			getConfigListEntry(_("Poll Interval (in h)"), config.plugins.autotimer.interval),
			getConfigListEntry(_("Modify existing Timers"), config.plugins.autotimer.refresh),
			getConfigListEntry(_("Guess existing Timer based on Begin/End"), config.plugins.autotimer.try_guessing),
		]

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
			}
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