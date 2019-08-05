# for localized messages
from . import _

# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen

# GUI (Summary)
from Screens.Setup import SetupSummary
from Screens.MessageBox import MessageBox

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

# info
from plugin import AUTOTIMER_VERSION

# Configuration
from Components.config import config, configfile, getConfigListEntry
from Components.PluginComponent import plugins
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# For embed skin... Embed skin should not be needed. Skin falls back to oe-alliance-default-skin "setup" screen.
from enigma import getDesktop
HD = False
if getDesktop(0).size().width() >= 1280:
	HD = True

def getAutoTimerSettingsDefinitions():
	hours_minutes = config.plugins.autotimer.unit.value == "hour" and _("hours") or _("minutes")
	return [
		[_("Poll automatically"), config.plugins.autotimer.autopoll,"autopoll", _("If this is disabled AutoTimer will NOT automatically look for events matching your AutoTimers but only when you leave the GUI with the green button.")],
		[_("Only poll while in standby"), config.plugins.autotimer.onlyinstandby,"onlyinstandby", _("When this is enabled AutoTimer will ONLY check for new events whilst in stanadby.")],
		#TODO integrate this setting or leave commentted out
		#[_("Delay after editing (in sec)"), config.plugins.autotimer.editdelay,"editdelay", _("This is the delay in seconds that the AutoTimer will wait after editing the AutoTimers.")],
		[_("Startup delay (in min)"), config.plugins.autotimer.delay,"delay", _("Startup delay is the number of minutes before polling after a reboot, so as to not delay enigma2 startup time.")],
		[_("Poll unit"), config.plugins.autotimer.unit,"unit", _("Poll unit selects whether the poll interval should be interpreted in hours or minutes.")],
		[_("Poll Interval (in %s)") % hours_minutes, config.plugins.autotimer.interval,"interval", _("This is the delay in %s that the AutoTimer will wait after doing a search before searching the EPG again.") % hours_minutes],
		#TODO integrate this setting or leave commentted out
		#[_("Timeout (in min)"), config.plugins.autotimer.timeout,"timeout", _("This is the duration in minutes that the AutoTimer is allowed to run.")],
		[_("Only add timer for next x days"), config.plugins.autotimer.maxdaysinfuture,"maxdaysinfuture", _("You can control for how many days in the future timers are added. Set this to 0 to disable this feature.")],
		[_("Allow double timer for different services"), config.plugins.autotimer.enable_multiple_timer,"enable_multiple_timer", _("Here you can specify whether simultaneous timers of the same program can be created. This allows simultaneous recording of a program with different resolutions. (e.g. SD service and HD service)")],
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

class AutoTimerSettings(ConfigListScreen, Screen):
	if HD:
		skin = """<screen name="AutoTimerSettings" title="AutoTimer Settings" position="center,center" size="750,635">
			<ePixmap pixmap="buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="5,50" size="740,475" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="div-h.png" position="0,530" zPosition="1" size="750,2" />
			<widget source="description" render="Label" position="5,535" size="740,110" font="Regular;21" />
		</screen>"""
	else:
		skin = """<screen name="AutoTimerSettings" title="AutoTimer Settings" position="center,center" size="565,430">
			<ePixmap pixmap="buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="5,50" size="555,300" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="div-h.png" position="0,355" zPosition="1" size="565,2" />
			<widget source="description" render="Label" position="5,360" size="555,70" font="Regular;20" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setup_title = _("AutoTimer Settings") + _(" - Version: %s") % AUTOTIMER_VERSION
		Screen.setTitle(self, self.setup_title)
		self.skinName = ["AutoTimerSettings", "Setup"]
		self.onChangedEntry = []
		self.session = session
		self.pollUnitEntry = None
		ConfigListScreen.__init__(self, [], session = session, on_change = self.changedEntry)

		self["actions2"] = ActionMap(["SetupActions"],
		{
			"ok": self.keySave,
			"menu": self.keyCancel,
			"cancel": self.keyCancel,
			"save": self.keySave,
		}, -2)

		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Save"))

		# Use self["description"] as this is what "Setup" skin uses.
		# The embedded skin could be removed. 
		# Plugin will use "Setup" screen from default skin if no skin available.
		self["description"] = StaticText("")
		self["help"] = StaticText("") # for backwards compatibility

		self.createSetup()

		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)
		self.selectionChanged()

	def createSetup(self):
		setup_list = []
		for (title,cfg,key,description) in getAutoTimerSettingsDefinitions():
			if cfg is config.plugins.autotimer.unit:
				self.pollUnitEntry = getConfigListEntry(title, cfg, description)
				setup_list.append(self.pollUnitEntry)
			else:
				setup_list.append(getConfigListEntry(title, cfg, description))
		self["config"].list = setup_list
		self["config"].l.setList(setup_list)

	def selectionChanged(self):
		self["description"].setText(self["config"].getCurrent()[2])
		self["help"].setText(self["config"].getCurrent()[2]) # for backwards compatibility

	def changedEntry(self):
		if self["config"].getCurrent() in (self.pollUnitEntry,): # do screen refresh if current entry requires this
			self.createSetup()
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def keySave(self):
		config.plugins.autotimer.save()
		configfile.save()
		if not config.plugins.autotimer.show_in_plugins.value:
			for plugin in plugins.getPlugins(PluginDescriptor.WHERE_PLUGINMENU):
				if plugin.name == "AutoTimer":
					plugins.removePlugin(plugin)

		if not config.plugins.autotimer.show_in_extensionsmenu.value:
			for plugin in plugins.getPlugins(PluginDescriptor.WHERE_EXTENSIONSMENU):
				if plugin.name == "AutoTimer":
					plugins.removePlugin(plugin)

		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
		self.close(False)

	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(self.cancelCallback, MessageBox, _("Really close without saving settings?"))
		else:
			self.cancelCallback(True)

	def cancelCallback(self, answer):
		if answer:
			for x in self["config"].list:
				x[1].cancel()
			self.close(False)
