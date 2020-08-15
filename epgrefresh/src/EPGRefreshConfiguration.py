from __future__ import print_function

# for localized messages
from . import _

# GUI (Screens)
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Components.ConfigList import ConfigListScreen
from Components.config import KEY_OK
from Screens.LocationBox import LocationBox
from EPGRefreshChannelEditor import EPGRefreshServiceEditor

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap, HelpableActionMap
from Screens.HelpMenu import HelpMenu, HelpableScreen
from Components.Sources.StaticText import StaticText

# Configuration
from Components.config import config, getConfigListEntry, configfile, NoSave
from Screens.FixedMenu import FixedMenu
from Tools.BoundFunction import boundFunction

from EPGRefresh import epgrefresh
from Components.NimManager import nimmanager
from Screens.MessageBox import MessageBox

# Error-print
from traceback import print_exc
from sys import stdout
import os

VERSION = "2.1.4"
class EPGHelpContextMenu(FixedMenu):
	HELP_RETURN_MAINHELP = 0
	HELP_RETURN_KEYHELP = 1

	def __init__(self, session):
		menu = [(_("General Help"), boundFunction(self.close, self.HELP_RETURN_MAINHELP)),
			(_("Key Help"), boundFunction(self.close, self.HELP_RETURN_KEYHELP)),
			(_("Cancel"), self.close)]

		FixedMenu.__init__(self, session, _("EPGRefresh Configuration Help"), menu)
		self.skinName = ["EPGRefreshConfigurationHelpContextMenu", "Menu" ]

class EPGFunctionMenu(FixedMenu):
	FUNCTION_RETURN_FORCEREFRESH = 0
	FUNCTION_RETURN_STOPREFRESH = 1
	FUNCTION_RETURN_SHOWPENDING = 2

	def __init__(self, session):
		if epgrefresh.isRunning():
			menu = [(_("Stop running refresh"), boundFunction(self.close, self.FUNCTION_RETURN_STOPREFRESH)),
				(_("Pending Services"), boundFunction(self.close, self.FUNCTION_RETURN_SHOWPENDING))]
		else:
			menu = [(_("Refresh now"), boundFunction(self.close, self.FUNCTION_RETURN_FORCEREFRESH))]
		menu.append((_("Cancel"), self.close))

		FixedMenu.__init__(self, session, _("EPGRefresh Functions"), menu)
		self.skinName = ["EPGRefreshConfigurationFunctionContextMenu", "Menu" ]

class EPGRefreshConfiguration(Screen, HelpableScreen, ConfigListScreen):
	"""Configuration of EPGRefresh"""
        
        skin = """<screen name="EPGRefreshConfiguration" position="center,center" size="700,450">
		<ePixmap position="0,5" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,5" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,5" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,5" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<ePixmap position="572,15" size="35,25" pixmap="skin_default/buttons/key_info.png" alphatest="on" />

		<widget source="key_red" render="Label" position="0,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_green" render="Label" position="140,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_yellow" render="Label" position="280,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_blue" render="Label" position="420,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />

		<widget name="config" position="5,50" size="690,275" scrollbarMode="showOnDemand" />
		<ePixmap pixmap="skin_default/div-h.png" position="5,335" zPosition="1" size="690,2" />
		<widget source="description" render="Label" position="5,345" size="690,105" font="Regular;21" />
	</screen>"""
	
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.list = []
		# Summary
		self.setup_title = _("EPGRefresh Configuration")
		self.onChangedEntry = []
		
		self.session = session
		
		# Although EPGRefresh keeps services in a Set we prefer a list
		self.services = (
			[x for x in epgrefresh.services[0]],
			[x for x in epgrefresh.services[1]]
		)

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)
		self._getConfig()

		self["config"].onSelectionChanged.append(self.updateHelp)

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("Functions"))
		self["key_blue"] = StaticText(_("Edit Services"))

		self["help"] = self["description"] = StaticText()

		# Define Actions
		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
			{
				"yellow": (self.showFunctionMenu, _("Show more Functions")),
				"blue": (self.editServices, _("Edit Services")),
			}
		)
		self["actions"] = HelpableActionMap(self, "ChannelSelectEPGActions",
			{
				"showEPGList": (self.keyInfo, _("Show last EPGRefresh - Time")),
			}
		)
		self["ChannelSelectBaseActions"] = HelpableActionMap(self, "ChannelSelectBaseActions",
			{
				"nextBouquet": (self.pageup, _("Move page up")),
				"prevBouquet": (self.pagedown, _("Move page down")),
			}
		)
		self["actionstmp"] = ActionMap(["HelpActions"],
			{
				"displayHelp": self.showHelp,
			}
		)
		self["SetupActions"] = HelpableActionMap(self, "SetupActions",
			{
				"cancel": (self.keyCancel, _("Close and forget changes")),
				"save": (self.keySave, _("Close and save changes")),
			}
		)
		
		# Trigger change
		self.changed()
		self.needsEnigmaRestart = False
		self.ServicesChanged = False
		
		self.onLayoutFinish.append(self.setCustomTitle)
		self.onFirstExecBegin.append(self.firstExec)
		self["config"].isChanged = self._ConfigisChanged

	def _getConfig(self):
		# Name, configElement, HelpTxt, reloadConfig
		self.list = [] 
		self.list.append(getConfigListEntry(_("Refresh EPG automatically"), config.plugins.epgrefresh.enabled, _("Unless this is enabled, EPGRefresh won't automatically run but needs to be explicitly started by the yellow button in this menu."), True))
		if config.plugins.epgrefresh.enabled.value:
			self.list.append(getConfigListEntry(_("Duration to stay on service (seconds)"), config.plugins.epgrefresh.interval_seconds, _("This is the duration each service/channel will stay active during a refresh."), False))
			self.list.append(getConfigListEntry(_("EPG refresh auto-start earliest (hh:mm)"), config.plugins.epgrefresh.begin, _("An automated refresh will start after this time of day, but before the time specified in next setting."), False))
			self.list.append(getConfigListEntry(_("EPG refresh auto-start latest (hh:mm)"), config.plugins.epgrefresh.end, _("An automated refresh will start before this time of day, but after the time specified in previous setting."), False))
			self.list.append(getConfigListEntry(_("Delay if not in standby (minutes)"), config.plugins.epgrefresh.delay_standby, _("If the receiver currently isn't in standby, this is the duration which EPGRefresh will wait before retry."), False))
			if len(nimmanager.nim_slots) > 1:
				self.list.append(getConfigListEntry(_("Refresh EPG using"), config.plugins.epgrefresh.adapter, _("If you want to refresh the EPG in background, you can choose the method which best suits your needs here, e.g. hidden, fake reocrding or regular Picture in Picture."), False))
			self.list.append(getConfigListEntry(_("Show Advanced Options"), NoSave(config.plugins.epgrefresh.showadvancedoptions), _("Display more Options"), True))
			if config.plugins.epgrefresh.showadvancedoptions.value:
				if config.ParentalControl.servicepinactive.value:
					self.list.append(getConfigListEntry(_("Skip protected Services"), config.plugins.epgrefresh.skipProtectedServices, _("Should protected services be skipped if refresh was started in interactive-mode?"), False))
				self.list.append(getConfigListEntry(_("Show Setup in plugins"), config.plugins.epgrefresh.show_in_plugins, _("Enable this to be able to access the EPGRefresh configuration from within the plugin menu."), False))
				self.list.append(getConfigListEntry(_("Show Setup in extension menu"), config.plugins.epgrefresh.show_in_extensionsmenu, _("Enable this to be able to access the EPGRefresh configuration from within the extension menu."), False))
				self.list.append(getConfigListEntry(_("Show 'EPGRefresh Start now' in extension menu."), config.plugins.epgrefresh.show_run_in_extensionsmenu, _("Enable this to be able to start the EPGRefresh from within the extension menu."), False))
				self.list.append(getConfigListEntry(_("Show popup when refresh starts and ends."), config.plugins.epgrefresh.enablemessage, _("This setting controls whether or not an informational message will be shown at start and completion of refresh."), False))
				self.list.append(getConfigListEntry(_("Wake up from standby for EPG refresh."), config.plugins.epgrefresh.wakeup, _("If this is enabled, the plugin will wake up the receiver from standby if possible. Otherwise it needs to be switched on already."), False))
				self.list.append(getConfigListEntry(_("Force scan even if receiver is in use."), config.plugins.epgrefresh.force, _("This setting controls whether or not the refresh will be initiated even though the receiver is active (either not in standby or currently recording)."), False))
				self.list.append(getConfigListEntry(_("Shutdown after EPG refresh."), config.plugins.epgrefresh.afterevent, _("This setting controls whether the receiver should be set to standby after refresh is completed."), False))
				self.list.append(getConfigListEntry(_("Flush EPG before refresh"), config.plugins.epgrefresh.erase, _("Enable this item to flush all EPG data before starting a new EPG refresh cycle"), False))
				try:
					# try to import autotimer module to check for its existence
					from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
		
					self.list.append(getConfigListEntry(_("Inherit Services from AutoTimer"), config.plugins.epgrefresh.inherit_autotimer, _("Extend the list of services to refresh by those your AutoTimers use?"), True))
					self.list.append(getConfigListEntry(_("Run AutoTimer after refresh"), config.plugins.epgrefresh.parse_autotimer, _("After a successful refresh the AutoTimer will automatically search for new matches if this is enabled. The options 'Ask*' has only affect on a manually refresh. If EPG-Refresh was called in background the default-Answer will be executed!"), False))
				except ImportError as ie:
					print("[EPGRefresh] AutoTimer Plugin not installed:", ie)
			
		self["config"].list = self.list
		self["config"].setList(self.list)

	def firstExec(self):
		from plugin import epgrefreshHelp
		if config.plugins.epgrefresh.show_help.value and epgrefreshHelp:
			config.plugins.epgrefresh.show_help.value = False
			config.plugins.epgrefresh.show_help.save()
			epgrefreshHelp.open(self.session)

	def setCustomTitle(self):
		self.setTitle(' '.join((_("EPGRefresh Configuration"), _("Version"), VERSION)))

	# overwrites / extendends
	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self._onKeyChange()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self._onKeyChange()
	
	# overwrite configlist.isChanged
	def _ConfigisChanged(self):
		is_changed = False
		for x in self["config"].list:
			if not x[1].save_disabled:
				is_changed |= x[1].isChanged()
		return is_changed
	
	def isConfigurationChanged(self):
		return self.ServicesChanged or self._ConfigisChanged()
	
	def _onKeyChange(self):
		cur = self["config"].getCurrent()
		if cur and cur[3]:
			self._getConfig()

	def showHelp(self):
		self.session.openWithCallback(self._HelpMenuCallback, EPGHelpContextMenu)

	def _HelpMenuCallback(self, *result):
		if not len(result):
			return
		result = result[0]

		if result == EPGHelpContextMenu.HELP_RETURN_MAINHELP:
			self._showMainHelp()
		else:
			self._showKeyhelp()
	
	def _showMainHelp(self):
		from plugin import epgrefreshHelp
		if epgrefreshHelp:
			epgrefreshHelp.open(self.session)
	
	def _showKeyhelp(self):
		self.session.openWithCallback(self.callHelpAction, HelpMenu, self.helpList)

	def updateHelp(self):
		cur = self["config"].getCurrent()
		if cur:
			self["description"].text = cur[2]

	def showFunctionMenu(self):
		self.session.openWithCallback(self._FunctionMenuCB, EPGFunctionMenu)

	def _FunctionMenuCB(self, *result):
		if not len(result):
			return
		result = result[0]

		try:
			if result == EPGFunctionMenu.FUNCTION_RETURN_FORCEREFRESH:
				self.forceRefresh()
			if result == EPGFunctionMenu.FUNCTION_RETURN_STOPREFRESH:
				self.stopRunningRefresh()
			if result == EPGFunctionMenu.FUNCTION_RETURN_SHOWPENDING:
				self.showPendingServices()
		except:
			print("[EPGRefresh] Error in Function - Call")
			print_exc(file=stdout)
	
	def forceRefresh(self):
		if not epgrefresh.isRefreshAllowed():
			return
	
		self._saveConfiguration()
		epgrefresh.services = (set(self.services[0]), set(self.services[1]))
		epgrefresh.forceRefresh(self.session)
		self.keySave(False)

	def showPendingServices(self):
		epgrefresh.showPendingServices(self.session)
	
	def stopRunningRefresh(self):
		epgrefresh.stopRunningRefresh(self.session)

	def editServices(self):
		self.session.openWithCallback(
			self.editServicesCallback,
			EPGRefreshServiceEditor,
			self.services
		)

	def editServicesCallback(self, ret):
		if ret:
			self.services = ret
			self.ServicesChanged = True

	# for Summary
	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass
	
	# for Summary
	def getCurrentEntry(self):
		if self["config"].getCurrent():
			return self["config"].getCurrent()[0]

	# for Summary
	def getCurrentValue(self):
		if self["config"].getCurrent():
			return str(self["config"].getCurrent()[1].getText())

	# for Summary
	def createSummary(self):
		return SetupSummary

	def pageup(self):
		self["config"].instance.moveSelection(self["config"].instance.pageUp)

	def pagedown(self):
		self["config"].instance.moveSelection(self["config"].instance.pageDown)

	def keyInfo(self):
		lastscan = config.plugins.epgrefresh.lastscan.value
		if lastscan:
			from Tools.FuzzyDate import FuzzyTime
			scanDate = ', '.join(FuzzyTime(lastscan))
		else:
			scanDate = _("never")

		self.session.open(
				MessageBox,
				_("Last refresh was %s") % (scanDate,),
				type=MessageBox.TYPE_INFO
		)

	def cancelConfirm(self, doCancel):
		if not doCancel:
			return
		for x in self["config"].list:
			x[1].cancel()
		self.close(self.session, False)

	def keyCancel(self):
		if self.isConfigurationChanged():
			self.session.openWithCallback(
				self.cancelConfirm,
				MessageBox,
				_("Really close without saving settings?")
			)
		else:
			self.close(self.session, False)
	
	def closeRecursive(self):
		self.keyCancel()

	def _saveConfiguration(self):
		epgrefresh.services = (set(self.services[0]), set(self.services[1]))
		epgrefresh.saveConfiguration()

		for x in self["config"].list:
			x[1].save()		
		configfile.save()
		
	def keySave(self, doSaveConfiguration = True):
		if self.isConfigurationChanged():
			if not epgrefresh.isRefreshAllowed():
				return
			else:
				epgrefresh.stop()
				if doSaveConfiguration:
					self._saveConfiguration()
		
		self.close(self.session, self.needsEnigmaRestart)


