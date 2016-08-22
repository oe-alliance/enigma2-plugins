# for localized messages
from . import _, allowShowOrbital, updateOrbposConfig, purgeOrbposConfig, getOrbposConfList, orbposChoicelist

# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.Boolean import Boolean

# Configuration
from Components.config import config, getConfigListEntry
from Components.PluginComponent import plugins
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.BoundFunction import boundFunction

# Plugin definition
from Plugins.Plugin import PluginDescriptor

from collections import defaultdict

class EPGSearchSetup(Screen, ConfigListScreen):
	skin = """<screen name="EPGSearchSetup" position="center,center" size="565,370">
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
		<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
		<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="config" position="5,50" size="555,250" scrollbarMode="showOnDemand" />
		<ePixmap pixmap="skin_default/div-h.png" position="0,301" zPosition="1" size="565,2" />
		<widget source="help" render="Label" position="5,305" size="555,63" font="Regular;21" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = [self.skinName, "Setup"]
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["VKeyIcon"] = Boolean(False)
		self['footnote'] = Label("")
		self["description"] = Label()

		# Summary
		self.setup_title = _("EPGSearch Setup")
		Screen.setTitle(self, _(self.setup_title))
		self.onChangedEntry = []

		ConfigListScreen.__init__(self, [], session = session, on_change = self.changedEntry)
		self.notifiers = (
			config.plugins.epgsearch.scope,
			config.plugins.epgsearch.enableorbpos,
			config.plugins.epgsearch.invertorbpos,
			config.plugins.epgsearch.numorbpos,
		)
		nChoices = updateOrbposConfig(save=True)
		if nChoices <= 2:
			config.plugins.epgsearch.enableorbpos.value = False
		self.createConfig()
		self.addNotifiers()
		self.onClose.append(self.clearNotifiers)

		self["actions"] = ActionMap(["SetupActions", 'ColorActions'],
		{
			"red": self.cancel,
			"green": self.save,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
		}, -2)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

	def addNotifiers(self):
		for n in self.notifiers:
			n.addNotifier(self.updateConfig, initial_call=False)

	def clearNotifiers(self):
		for n in self.notifiers:
			n.removeNotifier(self.updateConfig)

	def createConfig(self):
		configList = [
			getConfigListEntry(_("Search scope"), config.plugins.epgsearch.scope, _("Control where to search in the EPG. When 'all bouquets' is set, all bouquets are searched, even if 'Enable multiple bouquets' is disabled.")),
		]
		if config.plugins.epgsearch.scope.value == "ask":
			configList.append(getConfigListEntry(_("Default scope when asked"), config.plugins.epgsearch.defaultscope, _("Sets the default search scope when the user is asked.")))
		if allowShowOrbital:
			configList.append(getConfigListEntry(_("Show orbital position"), config.plugins.epgsearch.showorbital, _("Show satellite orbital positions in the search results.")))
		configList += [
			getConfigListEntry(_("Search type"), config.plugins.epgsearch.search_type, _("Set type of match used to compare program titles with the search string")),
			getConfigListEntry(_("Search strictness"), config.plugins.epgsearch.search_case, _("Is the search case-sensitive or case-insensitive")),
			getConfigListEntry(_("Show in plugin browser"), config.plugins.epgsearch.showinplugins, _("Enable this to allow access to EPG Search from within the plugin browser.")),
			getConfigListEntry(_("Length of history"), config.plugins.epgsearch.history_length, _("Maximum number of entries in the search history. Set this to 0 to disable search history.")),
			getConfigListEntry(_("Search encoding"), config.plugins.epgsearch.encoding, _("Choose the encoding type for searches, helpful for foreign languages.")),
# 				getConfigListEntry(_("Add \"Search\" button to EPG"), config.plugins.epgsearch.add_search_to_epg , _("If this setting is enabled, the plugin adds a \"Search\" button to the regular EPG.")),
		]
		configList += self.createOrbposConfig()
		self["config"].setList(configList)
		if config.usage.sort_settings.value:
			self["config"].list.sort()

	def updateConfig(self, configElement):
		self.createConfig()

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()
	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]
	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())
	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

	def save(self):
		purgeOrbposConfig()
		self.saveAll()
		if not config.plugins.epgsearch.showinplugins.value:
			for plugin in plugins.getPlugins(PluginDescriptor.WHERE_PLUGINMENU):
				if plugin.name == _("EPGSearch"):
					plugins.removePlugin(plugin)

		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
		self.close()

	def createOrbposConfig(self):
		# Only show source/orbpos choices if there is more than
		# one choice (not including "disabled")
		nChoices = updateOrbposConfig()
		if nChoices > 2:
			configList = [getConfigListEntry(_("Filter results by source"), config.plugins.epgsearch.enableorbpos, _("Include or exclude results depending on their source (e.g. by satellite)"))]
			if config.plugins.epgsearch.enableorbpos.value:
				configList += [
					getConfigListEntry(_("Include/exclude sources"), config.plugins.epgsearch.invertorbpos, _("Use source restrictions below to only include results from the sources, or exclude them.")),
					getConfigListEntry(_("Number of inclusions/exclusions"), config.plugins.epgsearch.numorbpos, _("Number of filters for inclusion/exclusion of results")),
				]
				if config.plugins.epgsearch.invertorbpos.value == _("include"):
					restrictionName = _("Include results from")
				else:
					restrictionName = _("Exclude results from")
				restrictionDesc = _("Include/exclude search results from this type of source")
				configList += [
					getConfigListEntry(restrictionName, confItem, restrictionDesc)
					for confItem in getOrbposConfList(includeDisabled=True)
				]
		else:
			configList = []
		return configList


	def cancel(self):
		self.keyCancel()

	def createSummary(self):
		return SetupSummary
