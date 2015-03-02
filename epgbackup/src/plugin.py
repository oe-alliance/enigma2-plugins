# for localized messages
from . import _

# Config
from Components.config import config, ConfigYesNo, ConfigNumber, ConfigSelection, \
	ConfigSubsection, ConfigSelectionNumber, ConfigDirectory, NoSave
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Tools.BoundFunction import boundFunction

# Error-print
from EPGBackupTools import debugOut, PLUGIN_VERSION
from traceback import format_exc

extPrefix = _("EXTENSIONMENU_PREFIX")

config.plugins.epgbackup = ConfigSubsection()
# Do not change order of choices
config.plugins.epgbackup.show_setup_in = ConfigSelection(choices=[
		("extension", _("extensions")),
		("plugin", _("pluginmenue")),
		("both", _("extensions") + "/" + _("pluginmenue")),
		("system", _("systemmenue")),
	], default = "both")
config.plugins.epgbackup.show_make_backup_in_extmenu = ConfigYesNo(default = False)
config.plugins.epgbackup.show_backuprestore_in_extmenu = ConfigYesNo(default = False)
config.plugins.epgbackup.backup_enabled = ConfigYesNo(default = True)
config.plugins.epgbackup.make_backup_after_unsuccess_restore = ConfigYesNo(default = True)
config.plugins.epgbackup.callAfterEPGRefresh = ConfigYesNo(default = True)
config.plugins.epgbackup.backupSaveInterval = ConfigSelection(choices = [
        ("-1",_("backup timer disabled")),
        ("30",_("30 minutes")),
        ("60",_("1 hour")),
        ("300",_("6 hours")),
        ("1200",_("1 day")),
    ], default = "-1")
config.plugins.epgbackup.show_messages_background = ConfigYesNo(default = True)
config.plugins.epgbackup.filesize_valid = ConfigSelectionNumber(min = 1, 
        max = 20, stepwidth = 1, default = 3, wraparound = True)
config.plugins.epgbackup.timespan_valid = ConfigNumber(default=7)
config.plugins.epgbackup.showadvancedoptions = NoSave(ConfigYesNo(default = False))
config.plugins.epgbackup.epgwrite_wait = ConfigNumber(default=3)
config.plugins.epgbackup.showin_usr_scripts = ConfigYesNo(default = True)
config.plugins.epgbackup.backup_strategy = ConfigSelection(choices = [
		("youngest_before_biggest", _("Youngest before Biggest"), _("The youngest file from the saved backup-files will be restored.\nIf it is older than the current existing EPG-file and the EPG-file isn't valid then the biggest backup-file will be restored.")),
		("biggest_before_youngest", _("Biggest before Youngest"), _("The biggest file from the saved backup-files will be restored.\nIf it is smaller than the current existing EPG-file and the EPG-file isn't valid then the youngest backup-file will be restored.")),
		("youngest", _("Only younger"), _("The backup-file will only be restored if it is younger than the current existing EPG-file.")),
		("biggest", _("Only bigger"), _("The backup-file will only be restored if it is greater than the current existing EPG-file.")),
	], default = "youngest_before_biggest"
)
config.plugins.epgbackup.enable_debug = ConfigYesNo(default = False)
config.plugins.epgbackup.plugin_debug_in_file = ConfigYesNo(default = False)
config.plugins.epgbackup.backup_log_dir = ConfigDirectory(default = "/tmp")
config.plugins.epgbackup.max_boot_count = ConfigNumber(default=3)

try:
	from Components.Language import language
	from Plugins.SystemPlugins.MPHelp import registerHelp, XMLHelpReader
	from Tools.Directories import resolveFilename, SCOPE_PLUGINS, fileExists
	lang = language.getLanguage()[:2]
	
	HELPPATH = resolveFilename(SCOPE_PLUGINS, "Extensions/EPGBackup")
	if fileExists(HELPPATH + "/locale/" + str(lang) + "/mphelp.xml"):
		helpfile = HELPPATH + "/locale/" + str(lang) + "/mphelp.xml"
	else:
		helpfile = HELPPATH + "/mphelp.xml"
	reader = XMLHelpReader(helpfile)
	epgBackuphHelp = registerHelp(*reader)
except:
	debugOut("Help-Error:\n" + str(format_exc()), forced=True)
	epgBackuphHelp = None
	
# Plugin
epgbackup = None
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

gUserScriptExists = False
# Autostart
def autostart(reason, **kwargs):
	global epgbackup
	global gUserScriptExists
	
	if reason == 0 and "session" in kwargs:
		session = kwargs["session"]
		
		from EPGBackupSupport import EPGBackupSupport
		try:
			epgbackup = EPGBackupSupport(session)
		except:
			debugOut("Error while initializing EPGBackupSupport:\n" + str(format_exc()), forced=True)
	
		try:
			from Plugins.Extensions.UserScripts.plugin import UserScriptsConfiguration
			gUserScriptExists = True
			del UserScriptsConfiguration
		except:
			pass

def openconfig(session, **kwargs):
	try:
		from EPGBackupConfig import EPGBackupConfig
		session.openWithCallback(doneConfiguring, EPGBackupConfig)
	except:
		debugOut("Config-Import-Error:\n" + str(format_exc()), forced=True)

def showinSetup(menuid):
	if menuid == "system":
		return [(extPrefix + " " + _("EXTENSIONNAME_SETUP"), openconfig, "EPGBackupConfig", None)]
	return []

def makeBackup(session, **kwargs):
	epgbackup.makeBackup(interactive = True)

def restoreBackup(session, **kwargs):
	epgbackup.forceDefaultRestore()

def doneConfiguring(session, needsRestart):
	if needsRestart:
		session.openWithCallback(boundFunction(restartGUICB, session), MessageBox, \
			_("To apply your Changes the GUI has to be restarted.\nDo you want to restart the GUI now?"), \
			MessageBox.TYPE_YESNO, title = _("EPGBackup Config V %s") % (PLUGIN_VERSION), timeout =  30)

def restartGUICB(session, answer):
	if answer is True:
		session.open(TryQuitMainloop, 3)

SetupPlugDescExt = PluginDescriptor(name = extPrefix + " " + _("EXTENSIONNAME_SETUP"), \
	description = _("Backup and restore EPG Data, including integration of EPGRefresh-plugin"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, \
	fnc = openconfig,
	needsRestart = False)
SetupPlugDescPlug = PluginDescriptor(name = extPrefix + " " + _("EXTENSIONNAME_SETUP"), \
	description = _("Backup and restore EPG Data, including integration of EPGRefresh-plugin"), where = PluginDescriptor.WHERE_PLUGINMENU, \
	fnc = openconfig,
	needsRestart = False)
MakePlugDescExt = PluginDescriptor(name = extPrefix + " " + _("Make Backup"), \
	description = _("Start making a Backup"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, \
	fnc = makeBackup,
	needsRestart = False)
RestorePlugDescExt = PluginDescriptor(name = extPrefix + " " + _("Restore Backup"), \
	description = _("Start a Restore of a Backup"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, \
	fnc = restoreBackup,
	needsRestart = False)

def AdjustPlugin(enable, PlugDescriptor):
	try:
		if enable:
			plugins.addPlugin(PlugDescriptor)
		else:
			plugins.removePlugin(PlugDescriptor)
	except ValueError:
		pass
	except:
		debugOut("AdjustPlugin-Error:\n" + str(format_exc()), forced=True)

def PluginHousekeeping(configentry):
	PlugDescInstall = []
	PlugDescDeinstall = []
	# value == extension: prior config-entry is both, so extension has not to be added
	# value == both: prior config-entry is plugin, so only extension must be added
	if configentry == config.plugins.epgbackup.show_setup_in:
		# systemmenu don't have to be adjusted, because restart is required
		if config.plugins.epgbackup.show_setup_in.value == "extension":
			PlugDescDeinstall.append(SetupPlugDescPlug)
		elif config.plugins.epgbackup.show_setup_in.value == "plugin":
			PlugDescInstall.append(SetupPlugDescPlug)
			PlugDescDeinstall.append(SetupPlugDescExt)
		elif config.plugins.epgbackup.show_setup_in.value == "both":
			PlugDescInstall.append(SetupPlugDescExt)
	elif configentry == config.plugins.epgbackup.show_make_backup_in_extmenu:
		if configentry.value:
			PlugDescInstall.append(MakePlugDescExt)
		else:
			PlugDescDeinstall.append(MakePlugDescExt)
	elif configentry == config.plugins.epgbackup.show_backuprestore_in_extmenu:
		if configentry.value:
			PlugDescInstall.append(RestorePlugDescExt)
		else:
			PlugDescDeinstall.append(RestorePlugDescExt)
	
	for PlugDescriptor in PlugDescDeinstall:
		AdjustPlugin(False, PlugDescriptor)
	for PlugDescriptor in PlugDescInstall:
		AdjustPlugin(True, PlugDescriptor)

config.plugins.epgbackup.show_setup_in.addNotifier(PluginHousekeeping, initial_call = False, immediate_feedback = True)
config.plugins.epgbackup.show_make_backup_in_extmenu.addNotifier(PluginHousekeeping, initial_call = False, immediate_feedback = True)
config.plugins.epgbackup.show_backuprestore_in_extmenu.addNotifier(PluginHousekeeping, initial_call = False, immediate_feedback = True)

def Plugins(**kwargs):
	pluginList = [
		PluginDescriptor(
			where = [PluginDescriptor.WHERE_SESSIONSTART,PluginDescriptor.WHERE_AUTOSTART],
			fnc = autostart)
	]
	
	if config.plugins.epgbackup.show_setup_in.value == "system":
		pluginList.append (PluginDescriptor(
			name = extPrefix + " " + _("EXTENSIONNAME_SETUP"),
			description = _("Keep EPG-Data over Crashes"),
			where = PluginDescriptor.WHERE_MENU,
			fnc = showinSetup,
			needsRestart = False)
		)
	else:
		if config.plugins.epgbackup.show_setup_in.value in ("plugin", "both"):
			pluginList.append(SetupPlugDescPlug)
		if config.plugins.epgbackup.show_setup_in.value in ("extension", "both"):
			pluginList.append(SetupPlugDescExt)
	
	if config.plugins.epgbackup.show_make_backup_in_extmenu.value:
		pluginList.append(MakePlugDescExt)
	if config.plugins.epgbackup.show_backuprestore_in_extmenu.value:
		pluginList.append(RestorePlugDescExt)
	
	return pluginList
