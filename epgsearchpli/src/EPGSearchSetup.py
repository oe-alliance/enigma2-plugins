# for localized messages  	 
from . import _

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

class EPGSearchSetup(Screen, ConfigListScreen):
	skin = """<screen name="EPGSearchSetup" position="center,center" size="585,420">
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
		<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
		<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="config" position="5,50" size="575,250" scrollbarMode="showOnDemand" />
		<ePixmap pixmap="skin_default/div-h.png" position="0,325" zPosition="1" size="585,2" />
		<widget source="help" render="Label" position="5,329" size="575,85" font="Regular;21" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = _("EPGSearch Setup")
		self.onChangedEntry = []

		ConfigListScreen.__init__(
			self,
			[
				getConfigListEntry(_("Length of History"), config.plugins.epgsearch.history_length, _("How many entries to keep in the search history at most. 0 disables history entirely!")),
				getConfigListEntry(_("Add \"Search\" Button to EPG"), config.plugins.epgsearch.add_search_to_epg , _("If this setting is enabled, the plugin adds a \"Search\" Button to the regular EPG.")),
				getConfigListEntry(_("Type blue Button"), config.plugins.epgsearch.type_button_blue , _("Select type: 'Search and Select channel' or 'Search'.")),
				getConfigListEntry(_("Use Picons"), config.plugins.epgsearch.picons , _("If this setting is enabled, the plugin adds picons.")),
				getConfigListEntry(_("Encoding Search to EPG"), config.plugins.epgsearch.encoding , _("Choosing an encoding. \"UTF-8\" to search for EPG cyrillic.")),
				getConfigListEntry(_("Search type"), config.plugins.epgsearch.search_type , _("Select type for search, \"partial match\" for the most extensive search.")),
				getConfigListEntry(_("Add \"Search event in EPG\" to event menu"), config.plugins.epgsearch.show_in_furtheroptionsmenu, _("Adds \"Search event in EPG\" item into the event menu (needs restart GUI)")),
				getConfigListEntry(_("Add \"Search event in EPG\" to channel menu"), config.plugins.epgsearch.search_in_channelmenu, _("Adds \"Search event in EPG\" item into the channel selection context menu (needs restart GUI)")),
				getConfigListEntry(_("Search strictness"), config.plugins.epgsearch.search_case , _("Select whether or not you want to enforce case correctness.")),
				getConfigListEntry(_("Search only bouquets"), config.plugins.epgsearch.bouquet , _("If this setting is enabled, searching EPG in only services in user bouquets.")),
				getConfigListEntry(_("Display name service as in bouquets"), config.plugins.epgsearch.favorit_name , _("If 'Search only bouquets' is enabled, show service name as in bouquets for renamed services.")),
				getConfigListEntry(_("Search type for filter"), config.plugins.epgsearch.filter_type , _("Select type for filter search. Press button P +/- for show/hide filter in description after search.")),
				
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
		self["help"] = StaticText()
		self.prev_add_search_to_epg = config.plugins.epgsearch.add_search_to_epg.value

		# Define Actions
		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.save,
			}
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("EPGSearch Setup"))

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

	def save(self):
		self.keySave()
		current = config.plugins.epgsearch.add_search_to_epg.value
		if current and self.prev_add_search_to_epg != current:
			self.refreshPlugins()

	def refreshPlugins(self):
		from Components.PluginComponent import plugins
		from Tools.Directories import SCOPE_PLUGINS, resolveFilename
		plugins.clearPluginList()
		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))