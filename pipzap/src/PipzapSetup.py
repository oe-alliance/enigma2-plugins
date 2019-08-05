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

class PipzapSetup(Screen, ConfigListScreen):
	skin = """<screen name="PipzapSetup" position="center,center" size="565,370">
		<ePixmap pixmap="buttons/red.png" position="0,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="buttons/green.png" position="140,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
		<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
		<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
		<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="config" position="5,50" size="555,250" scrollbarMode="showOnDemand" />
		<ePixmap pixmap="div-h.png" position="0,301" zPosition="1" size="565,2" />
		<widget source="help" render="Label" position="5,305" size="555,63" font="Regular;21" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = _("pipzap Setup")
		self.onChangedEntry = []

		ConfigListScreen.__init__(
			self,
			[
				getConfigListEntry(_("Enable Hotkey"), config.plugins.pipzap.enable_hotkey, _("Use the STOP-Key to quickly enable/disable pipzap in TV-Mode? Changing this setting requires a restart.")),
				getConfigListEntry(_("Show in Plugin menu"), config.plugins.pipzap.show_in_plugins, _("Adds an entry to the Plugin menu to toggle pipzap")),
				getConfigListEntry(_("Show indicator label if zapping PiP"), config.plugins.pipzap.show_label, _("Displays a label in the opposite corner of PiP if pipzap is enabled.")),
			],
			session = session,
			on_change = self.changed
		)
		def selectionChanged():
			if self["config"].current:
				self["config"].current[1].onDeselect(self.session)
			self["config"].current = self["config"].getCurrent()
			if self["config"].current:
				self["config"].current[1].onSelect(self.session)
			for x in self["config"].onSelectionChanged:
				x()
		self["config"].selectionChanged = selectionChanged
		self["config"].onSelectionChanged.append(self.updateHelp)

		# Initialize widgets
		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))
		self["key_yellow"] = StaticText("")
		from plugin import pipzapHelp
		if pipzapHelp:
			self["key_blue"] = StaticText(_("Help"))
		else:
			self["key_blue"] = StaticText("")
		self["help"] = StaticText()

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
				"blue": self.keyBlue,
			}
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("pipzap Setup"))

	def updateHelp(self):
		cur = self["config"].getCurrent()
		if cur:
			self["help"].text = cur[2]

	def changed(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def keyBlue(self):
		from plugin import pipzapHelp
		if pipzapHelp:
			pipzapHelp.open(self.session)
