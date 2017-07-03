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
from enigma import getDesktop
# Configuration
from Components.config import config, getConfigListEntry
from Components.PluginComponent import plugins
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from boxbranding import getImageDistro

# Plugin definition
from Plugins.Plugin import PluginDescriptor
HD = False
if getDesktop(0).size().width() >= 1280:
	HD = True
	
def getAutoTimerSettingsDefinitions():

	# TODO : read from setup.xml if posible
	intervaltext = _("Poll Interval (in h)")
	intervaldesc = _("This is the delay in hours that the AutoTimer will wait after a search to search the EPG again.")

	if getImageDistro() in ('openmips', 'openatv'):
		intervaltext = _("Poll Interval (in mins)")
		intervaldesc = _("This is the delay in minutes that the AutoTimer will wait after a search to search the EPG again.")

	return [
		[_("Poll automatically"), config.plugins.autotimer.autopoll,"autopoll", _("Unless this is enabled AutoTimer will NOT automatically look for events matching your AutoTimers but only when you leave the GUI with the green button.")],
		[_("Only poll while in standby"), config.plugins.autotimer.onlyinstandby,"onlyinstandby", _("When this is enabled AutoTimer will ONLY check for new events whilst in stanadby.")],
		#TODO integrate this setting or let comment out
		#[_("Delay after editing (in sec)"), config.plugins.autotimer.editdelay,"editdelay", _("This is the delay in seconds that the AutoTimer will wait after editing the AutoTimers.")],
		[_("Startup delay (in min)"), config.plugins.autotimer.delay,"delay", _("This is the delay in minutes that the AutoTimer will wait on initial launch to not delay enigma2 startup time.")],
		#TODO back to hours
		#[_("Poll Interval (in h)"), config.plugins.autotimer.interval,"interval", _("This is the delay in hours that the AutoTimer will wait after a search to search the EPG again.")],
		#[_("Poll Interval (in mins)"), config.plugins.autotimer.interval,"interval", _("This is the delay in minutes that the AutoTimer will wait after a search to search the EPG again.")],
		[intervaltext, config.plugins.autotimer.interval,"interval", intervaldesc],
		#TODO integrate this setting or let comment out
		#[_("Timeout (in min)"), config.plugins.autotimer.timeout,"timeout", _("This is the duration in minutes that the AutoTimer is allowed to run.")],
		[_("Only add timer for next x days"), config.plugins.autotimer.maxdaysinfuture,"maxdaysinfuture", _("You can control for how many days in the future timers are added. Set this to 0 to disable this feature.")],
		[_("Show in plugin browser"), config.plugins.autotimer.show_in_plugins,"show_in_plugins", _("Enable this to be able to access the AutoTimer Overview from within the plugin browser.")],
		[_("Show in extension menu"), config.plugins.autotimer.show_in_extensionsmenu,"show_in_extensionsmenu", _("Enable this to be able to access the AutoTimer Overview from within the extension menu.")],
		[_("Modify existing timers"), config.plugins.autotimer.refresh,"refresh", _("This setting controls the behavior when a timer matches a found event.")],
		[_("Guess existing timer based on begin/end"), config.plugins.autotimer.try_guessing,"try_guessing", _("If this is enabled an existing timer will also be considered recording an event if it records at least 80% of the it.")],
		[_("Add similar timer on conflict"), config.plugins.autotimer.addsimilar_on_conflict,"addsimilar_on_conflict", _("If a timer conflict occurs, AutoTimer will search outside the timespan for a similar event and add it.")],
		[_("Add timer as disabled on conflict"), config.plugins.autotimer.disabled_on_conflict,"disabled_on_conflict", _("This toggles the behavior on timer conflicts. If an AutoTimer matches an event that conflicts with an existing timer it will not ignore this event but add it disabled.")],
		[_("Include \"AutoTimer\" in tags"), config.plugins.autotimer.add_autotimer_to_tags,"add_autotimer_to_tags", _("If this is selected, the tag \"AutoTimer\" will be given to timers created by this plugin.")],
		[_("Include AutoTimer name in tags"), config.plugins.autotimer.add_name_to_tags,"add_name_to_tags", _("If this is selected, the name of the respective AutoTimer will be added as a tag to timers created by this plugin.")],
		[_("Show notification on conflicts"), config.plugins.autotimer.notifconflict,"notifconflict", _("By enabling this you will be notified about timer conflicts found during automated polling. There is no intelligence involved, so it might bother you about the same conflict over and over.")],
		[_("Show notification on similars"), config.plugins.autotimer.notifsimilar,"notifsimilar", _("By enabling this you will be notified about similar timers added during automated polling. There is no intelligence involved, so it might bother you about the same conflict over and over.")],
		[_("Editor for new AutoTimers"), config.plugins.autotimer.editor,"editor", _("The editor to be used for new AutoTimers. This can either be the Wizard or the classic editor.")],
		[_("Support \"Fast Scan\"?"), config.plugins.autotimer.fastscan,"fastscan", _("When supporting \"Fast Scan\" the service type is ignored. You don't need to enable this unless your Image supports \"Fast Scan\" and you are using it.")],
		[_("Skip poll during records"), config.plugins.autotimer.skip_during_records,"skip_during_records", _("If enabled, the polling will be skipped if a recording is in progress.")],
		[_("Skip poll during epg refresh"), config.plugins.autotimer.skip_during_epgrefresh,"skip_during_epgrefresh", _("If enabled, the polling will be skipped if EPGRefresh is currently running.")],
		[_("Popup timeout in seconds"), config.plugins.autotimer.popup_timeout,"popup_timeout", _("If 0, the popup will remain open.")],
		[_("Remove not existing events"), config.plugins.autotimer.check_eit_and_remove,"check_eit_and_remove", _("Check the event id (eit) and remove the timer if there is no corresponding EPG event. Due to compatibility issues with SerienRecorder and IPRec, only timer created by AutoTimer are affected.")],
		[_("Always write config"), config.plugins.autotimer.always_write_config,"always_write_config", _("Write the config file after every change which the user quits by saving.")]
	]


class AutoTimerSettings(Screen, ConfigListScreen):
	if HD:
		skin = """<screen name="AutoTimerSettings" title="AutoTimer Settings" position="center,center" size="750,635">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="5,50" size="740,475" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,530" zPosition="1" size="750,2" />
			<widget source="help" render="Label" position="5,535" size="740,110" font="Regular;21" />
		</screen>"""
	else:
		skin = """<screen name="AutoTimerSettings" title="AutoTimer Settings" position="center,center" size="565,430">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="5,50" size="555,300" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,355" zPosition="1" size="565,2" />
			<widget source="help" render="Label" position="5,360" size="555,70" font="Regular;20" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = _("AutoTimer Settings")
		self.onChangedEntry = []

		configdef = getAutoTimerSettingsDefinitions()

		configs = []
		
		for (title,cfg,key,description) in configdef:
			configs.append(
					getConfigListEntry(title, cfg, description)
				)

		ConfigListScreen.__init__(
			self,
			configs,
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

		# Define Actions
		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.Save,
			}
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		from plugin import AUTOTIMER_VERSION
		self.setTitle(_("Configure AutoTimer behavior") + " - Version: " + AUTOTIMER_VERSION)

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
		return str(self["config"].getCurrent()[0])

	def Save(self):
		self.saveAll()
		if not config.plugins.autotimer.show_in_plugins.value:
			for plugin in plugins.getPlugins(PluginDescriptor.WHERE_PLUGINMENU):
				if plugin.name == "AutoTimer":
					plugins.removePlugin(plugin)

		if not config.plugins.autotimer.show_in_extensionsmenu.value:
			for plugin in plugins.getPlugins(PluginDescriptor.WHERE_EXTENSIONSMENU):
				if plugin.name == "AutoTimer":
					plugins.removePlugin(plugin)
				
		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
		self.close()

	def createSummary(self):
		return SetupSummary
