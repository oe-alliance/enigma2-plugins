# Screens
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpMenu, HelpableScreen
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Screens.LocationBox import LocationBox

# for localized messages
from . import _

# GUI (Summary)
from Screens.Setup import SetupSummary

# Configuration
from Components.config import config, getConfigListEntry, configfile, NoSave
from Components.ConfigList import ConfigListScreen
from Components.config import KEY_OK

# Error-print
from EPGBackupTools import debugOut, PLUGIN_VERSION
from traceback import format_exc

from plugin import gUserScriptExists
from plugin import epgbackup
			
class EPGBackupConfig(Screen, HelpableScreen, ConfigListScreen):
	skin = """
		<screen name="EPGBackupSetup" position="center,center" size="700,520" >
			<ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<widget  position="0,0" size="140,40" source="key_red" render="Label" transparent="1" halign="center" valign="center" zPosition="2" foregroundColor="white" font="Regular;18" />
			<ePixmap position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<widget  position="140,0" size="140,40" render="Label" source="key_green" transparent="1" halign="center" valign="center" zPosition="2" foregroundColor="white" font="Regular;18" />
			<ePixmap position="282,10" zPosition="1" size="35,25" pixmap="skin_default/buttons/key_menu.png" alphatest="on" />
			<widget  position="5,45" size="690,335" name="config" scrollbarMode="showOnDemand" enableWrapAround="1" />
			<ePixmap position="0,390" size="700,2" pixmap="skin_default/div-h.png" zPosition="1" />
			<widget  position="5,400" size="690,120" source="help" render="Label" font="Regular;21" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		
		# Summary
		self.setup_title = _("EPGBackup Setup")
		self.onChangedEntry = []
		
		self.session = session
		self.list = []
		ConfigListScreen.__init__(self, self.list, session, on_change = self.changed)
		self["config"].onSelectionChanged.append(self._updateHelp)
		self._getConfig()
		
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["help"] = StaticText()
		
		# Actions
		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
			{
				"red": (self.keyCancel, _("Close and forget changes")),
				"green": (self.keySave, _("Close and save changes")),
			}
		)
		self["MenuActions"] = HelpableActionMap(self, "MenuActions",
			{
				"menu": (self.menu, _("Open Context Menu"))
			}
		)
		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
				"cancel": (self.keyCancel, _("Close and forget changes")),
			}
		)
		self["ChannelSelectBaseActions"] = HelpableActionMap(self, "ChannelSelectBaseActions",
			{
				"nextBouquet": (self.pageup, _("Move page up")),
				"prevBouquet": (self.pagedown, _("Move page down")),
			}
		)
		
		self["HelpActions"] = ActionMap(["HelpActions"],
			{
				"displayHelp": self.showKeyHelp,
			}
		)

		# Trigger change
		self.changed()
		
		self.confShowSetupIn = config.plugins.epgbackup.show_setup_in.value
		
		config.plugins.epgbackup.backup_strategy.addNotifier(self.updateVariableHelpText, initial_call = False, immediate_feedback = True)
		self.onClose.append(self.removeNotifiers)
		
		self.needsEnigmaRestart = False
		self.onLayoutFinish.append(self._layoutFinished)
		self["config"].isChanged = self._ConfigisChanged
	
	def _layoutFinished(self):
		self.setTitle(_("EPGBackup Setup") + " V%s" %(PLUGIN_VERSION))
	
	def removeNotifiers(self):
		try:
			config.plugins.epgbackup.backup_strategy.removeNotifier(self.updateVariableHelpText)
		except:
			debugOut("removeNotifiers-Error:\n" + str(format_exc()), forced=True)
	
	def showMainHelp(self):
		from plugin import epgBackuphHelp
		if epgBackuphHelp:
			epgBackuphHelp.open(self.session)

	def showKeyHelp(self):
		self.session.openWithCallback(self.callHelpAction, HelpMenu, self.helpList)

	def menu(self):
		menuList = []
		if config.plugins.epgbackup.backup_enabled.value:
			menuList.extend( [
				(_("Restore EPG-Backups (Date)"), "MENU_RETURN_RESTORE_DATE"),
				(_("Restore EPG-Backups (Size)"), "MENU_RETURN_RESTORE_SIZE"),
				(_("Make a EPG-Backup"), "MENU_RETURN_DO_BACKUP"),
				(_("Set Restore-File for next boot"), "MENU_RETURN_SET_NEXT_BOOT_RESTORE"),
				("--", None),
			])
		menuList.append((_("Show Help"), "MENU_RETURN_MAINHELP"))

		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list = menuList,
		)

	def menuCallback(self, menuinfo):
		try:
			menuinfo = menuinfo and menuinfo[1]
			if menuinfo:
				if menuinfo == "MENU_RETURN_RESTORE_DATE":
					if epgbackup:
						epgbackup.forceRestore()
				elif menuinfo == "MENU_RETURN_RESTORE_SIZE":
					if epgbackup:
						epgbackup.forceRestoreBySize()
				elif menuinfo == "MENU_RETURN_DO_BACKUP":
					if epgbackup:
						epgbackup.makeBackup(interactive = True)
				elif menuinfo == "MENU_RETURN_SET_NEXT_BOOT_RESTORE":
					if epgbackup:
						epgbackup.setNextBootRestore()
				elif menuinfo == "MENU_RETURN_MAINHELP":
					self.showMainHelp()
		except:
			debugOut("menuCallback-Error:\n" + str(format_exc()), forced=True)
	
	def _getConfig(self):
		# Name, configElement, HelpTxt, reloadConfig
		try:
			self.list = [] 
			self.list.append(getConfigListEntry(_("Enable Backup"), config.plugins.epgbackup.backup_enabled, _("Should the Backup-Functionality be enabled?\nFor more Information have a look at the Help-Screen."), True))
			if config.plugins.epgbackup.backup_enabled.value:
				self.list.append(getConfigListEntry(_("make Backup on start"), config.plugins.epgbackup.make_backup_after_unsuccess_restore, _("Make a backup before starting enigma. A backup-file will only be created, if no valid backup-file could be restored.\nNote: It's logically the same as making a backup at the ending of enigma, because the file didn't change in the meanwhile."), False))
				if epgbackup and epgbackup.epgrefresh_instance:
						self.list.append(getConfigListEntry(_("make Backup after EPGRefresh"), config.plugins.epgbackup.callAfterEPGRefresh, _("Make a backup after EPGRefresh."), False))
				self.list.append(getConfigListEntry(_("make Backup every"), config.plugins.epgbackup.backupSaveInterval, _("Make backups periodically?"), False))
				self.list.append(getConfigListEntry(_("Restore-Strategy"), config.plugins.epgbackup.backup_strategy, None, False))
				self.list.append(getConfigListEntry(_("Valid Filesize"), config.plugins.epgbackup.filesize_valid, _("EPG-Files with a less size of this value (MiB) won't be backuped."), False))
				self.list.append(getConfigListEntry(_("Valid Age"), config.plugins.epgbackup.timespan_valid, _("Only keep EPG-Backup-Files younger than this days."), False))
				self.list.append(getConfigListEntry(_("Show Advanced Options"), NoSave(config.plugins.epgbackup.showadvancedoptions), _("Display more Options"), True))
				if config.plugins.epgbackup.showadvancedoptions.value:
					self.list.append(getConfigListEntry(_("EPG-File-Write Wait"), config.plugins.epgbackup.epgwrite_wait, _("How many seconds should EPGBackup be wait to check if the EPG-File-Size didn't change before it starts the Backup."), False))
					self.list.append(getConfigListEntry(_("Maximum Boot-Count"), config.plugins.epgbackup.max_boot_count, _("After that times of unsuccesfully boot enigma2, the EPG-File will be deleted."), False))
					self.list.append(getConfigListEntry(_("Enable Debug"), config.plugins.epgbackup.enable_debug, _("Should debugmessages be printed?\nMessages from the shell-script will be append to a file. The filename will be added with the current date"), True))
					if config.plugins.epgbackup.enable_debug.value:
						self.list.append(getConfigListEntry(_("append plugin-messages"), config.plugins.epgbackup.plugin_debug_in_file, _("Should the debug-messages from the enigma-plugin also be append to the logfile? If you choose no the messages will print only to standard-out."), False))
						self.list.append(getConfigListEntry(_("Log-directory"), config.plugins.epgbackup.backup_log_dir, _("Directory for the Logfiles."), False))
					if gUserScriptExists:
						self.list.append(getConfigListEntry(_("Show in User-Scripts"), config.plugins.epgbackup.showin_usr_scripts, _("Should the Manage-Script be shown in User-Scripts?"), False))
					
					self.list.append(getConfigListEntry(_("Show messages in background"), config.plugins.epgbackup.show_messages_background, _("Pop a notification if called in background?"), False))
					self.list.append(getConfigListEntry(_("Show setup in"), config.plugins.epgbackup.show_setup_in, _("Where should this setup be displayed?"), False))
					self.list.append(getConfigListEntry(_("Show \"Make Backup\" in extension menu"), config.plugins.epgbackup.show_make_backup_in_extmenu, _("Enable this to be able to make a Backup-File from within the extension menu."), False))
					self.list.append(getConfigListEntry(_("Show \"Restore Backup\" in extension menu"), config.plugins.epgbackup.show_backuprestore_in_extmenu, _("Enable this to be able to start a restore of a Backup-File from within the extension menu."), False))
				
			self["config"].list = self.list
			self["config"].setList(self.list)
		except:
			debugOut("_getConfig-Error:\n" + str(format_exc()), forced=True)

	def _checkNeedsRestart(self):
		if (self.confShowSetupIn == "system" and config.plugins.epgbackup.show_setup_in.value != "system") \
			or (self.confShowSetupIn != "system" and config.plugins.epgbackup.show_setup_in.value == "system"):
			self.needsEnigmaRestart = True
	
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
	
	def keyOK(self):
		self["config"].handleKey(KEY_OK)
		cur = self["config"].getCurrent()
		if cur[1] == config.plugins.epgbackup.backup_log_dir:
			self.session.openWithCallback(self.directorySelected, LocationBox, \
				_("Select Logfile-Location"), "", \
				config.plugins.epgbackup.backup_log_dir.value)

	def directorySelected(self, res):
		if res is not None:
			config.plugins.epgbackup.backup_log_dir.value = res

	def _onKeyChange(self):
		cur = self["config"].getCurrent()
		if cur and cur[3]:
			self._getConfig()

	def _updateHelp(self):
		cur = self["config"].getCurrent()
		if cur:
			if cur[2] == None:
				self.updateVariableHelpText(cur[1])
			else:
				self["help"].text = cur[2]

	def updateVariableHelpText(self, configelement):
		try:
			if configelement == config.plugins.epgbackup.backup_strategy:
				self["help"].text = configelement.getChoices()[configelement.getIndex()][2]
		except:
			debugOut("updateVariableHelpText-Error:\n" + str(format_exc()), forced=True)

	def pageup(self):
		self["config"].instance.moveSelection(self["config"].instance.pageUp)

	def pagedown(self):
		self["config"].instance.moveSelection(self["config"].instance.pageDown)

	def cancelConfirm(self, doCancel):
		if not doCancel:
			return
		for x in self["config"].list:
			x[1].cancel()
		self.close(self.session, False)

	def keyCancel(self):
		if self["config"].isChanged():
			self.session.openWithCallback(
				self.cancelConfirm,
				MessageBox,
				_("Really close without saving settings?")
			)
		else:
			self.close(self.session, False)

	def keySave(self):
		if self["config"].isChanged():
			for x in self["config"].list:
				x[1].save()
			configfile.save()
		
		self._checkNeedsRestart()
		self.close(self.session, self.needsEnigmaRestart)
	
	# for Summary
	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass
	def getCurrentEntry(self):
		if self["config"].getCurrent():
			return self["config"].getCurrent()[0]
	def getCurrentValue(self):
		if self["config"].getCurrent():
			return str(self["config"].getCurrent()[1].getText())
	def createSummary(self):
		return SetupSummary


