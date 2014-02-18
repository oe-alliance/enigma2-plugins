from __future__ import print_function

# for localized messages
from . import _, NOTIFICATIONDOMAIN

# Config
from Components.config import config, ConfigYesNo, ConfigNumber, ConfigSelection, \
	ConfigSubsection, ConfigClock, ConfigYesNo, ConfigInteger, ConfigDirectory, NoSave
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Tools.BoundFunction import boundFunction

# Error-print
from traceback import print_exc
from sys import stdout

# Calculate default begin/end
from time import time, localtime, mktime
now = localtime()
begin = mktime((
	now.tm_year, now.tm_mon, now.tm_mday, 20, 15, \
	0, now.tm_wday, now.tm_yday, now.tm_isdst)
)
end = mktime((
	now.tm_year, now.tm_mon, now.tm_mday, 06, 30, \
	0, now.tm_wday, now.tm_yday, now.tm_isdst)
)

#Configuration
config.plugins.epgrefresh = ConfigSubsection()
config.plugins.epgrefresh.enabled = ConfigYesNo(default = False)
config.plugins.epgrefresh.begin = ConfigClock(default = int(begin))
config.plugins.epgrefresh.end = ConfigClock(default = int(end))
config.plugins.epgrefresh.interval_seconds = ConfigNumber(default = 120)
config.plugins.epgrefresh.delay_standby = ConfigNumber(default = 10)
config.plugins.epgrefresh.inherit_autotimer = ConfigYesNo(default = False)
config.plugins.epgrefresh.afterevent = ConfigYesNo(default = False)
config.plugins.epgrefresh.force = ConfigYesNo(default = False)
config.plugins.epgrefresh.enablemessage = ConfigYesNo(default = True)
config.plugins.epgrefresh.wakeup = ConfigYesNo(default = False)
config.plugins.epgrefresh.lastscan = ConfigNumber(default = 0)
config.plugins.epgrefresh.parse_autotimer = ConfigSelection(choices = [
		("always", _("Yes")),
		("never", _("No")),
		("bg_only", _("Background only")),
		("ask_yes", _("Ask default Yes")),
		("ask_no", _("Ask default No")),
	], default = "never"
)
config.plugins.epgrefresh.adapter = ConfigSelection(choices = [
		("main", _("Main Picture")),
		("pip", _("Picture in Picture")),
		("pip_hidden", _("Picture in Picture (hidden)")),
		("record", _("Fake recording")),
	], default = "main"
)
config.plugins.epgrefresh.show_in_extensionsmenu = ConfigYesNo(default = False)
config.plugins.epgrefresh.show_run_in_extensionsmenu = ConfigYesNo(default = True)
config.plugins.epgrefresh.show_backuprestore_in_extmenu = ConfigYesNo(default = False)
config.plugins.epgrefresh.show_help = ConfigYesNo(default = True)
config.plugins.epgrefresh.wakeup_time = ConfigInteger(default=-1)
config.plugins.epgrefresh.backup_enabled = ConfigYesNo(default = True)
config.plugins.epgrefresh.backup_filesize_valid = ConfigNumber(default=1024)
config.plugins.epgrefresh.backup_timespan_valid = ConfigNumber(default=7)
config.plugins.epgrefresh.showadvancedoptions = NoSave(ConfigYesNo(default = False))
config.plugins.epgrefresh.backup_epgwrite_wait = ConfigNumber(default=3)
config.plugins.epgrefresh.showin_usr_scripts = ConfigYesNo(default = True)
config.plugins.epgrefresh.backup_strategy = ConfigSelection(choices = [
		("biggest", _("Biggest before Youngest")),
		("youngest", _("Youngest before Biggest")),
	], default = "biggest"
)
config.plugins.epgrefresh.backup_enable_debug = ConfigYesNo(default = False)
config.plugins.epgrefresh.backup_log_dir = ConfigDirectory(default = "/hdd")
config.plugins.epgrefresh.backup_max_boot_count = ConfigNumber(default=3)

# convert previous parameters
config.plugins.epgrefresh.background = ConfigYesNo(default = False)
if config.plugins.epgrefresh.background.value:
	config.plugins.epgrefresh.adapter.value = "pip_hidden"
	config.plugins.epgrefresh.background.value = False
	config.plugins.epgrefresh.save()
config.plugins.epgrefresh.interval = ConfigNumber(default = 2)
if config.plugins.epgrefresh.interval.value != 2:
	config.plugins.epgrefresh.interval_seconds.value = config.plugins.epgrefresh.interval.value * 60
	config.plugins.epgrefresh.interval.value = 2
	config.plugins.epgrefresh.save()

#pragma mark - Help
try:
	from Components.Language import language
	from Plugins.SystemPlugins.MPHelp import registerHelp, XMLHelpReader
	from Tools.Directories import resolveFilename, SCOPE_PLUGINS, fileExists
	lang = language.getLanguage()[:2]
	
	HELPPATH = resolveFilename(SCOPE_PLUGINS, "Extensions/EPGRefresh")
	if fileExists(HELPPATH + "/locale/" + str(lang) + "/mphelp.xml"):
		helpfile = HELPPATH + "/locale/" + str(lang) + "/mphelp.xml"
	else:
		helpfile = HELPPATH + "/mphelp.xml"
	reader = XMLHelpReader(helpfile)
	epgrefreshHelp = registerHelp(*reader)
except Exception as e:
	print("[EPGRefresh] Unable to initialize MPHelp:", e,"- Help not available!")
	epgrefreshHelp = None
#pragma mark -

# Notification-Domain
from Tools import Notifications
try:
	Notifications.notificationQueue.registerDomain(NOTIFICATIONDOMAIN, _("EPGREFRESH_NOTIFICATION_DOMAIN"), deferred_callable = True)
except Exception as e:
	EPGRefreshNotificationKey = ""
	print("[EPGRefresh] Error registering Notification-Domain:", e)
	
# Plugin
from EPGRefresh import epgrefresh
from EPGRefreshService import EPGRefreshService
epgbackup = None
# Plugins
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

#pragma mark - Workaround for unset clock
from enigma import eDVBLocalTimeHandler

def timeCallback(isCallback=True):
	"""Time Callback/Autostart management."""
	thInstance = eDVBLocalTimeHandler.getInstance()
	if isCallback:
		# NOTE: this assumes the clock is actually ready when called back
		# this may not be true, but we prefer silently dying to waiting forever
		thInstance.m_timeUpdated.get().remove(timeCallback)
	elif not thInstance.ready():
		thInstance.m_timeUpdated.get().append(timeCallback)
		return
	epgrefresh.start()

# Autostart
def autostart(reason, **kwargs):
	global epgbackup
	
	if reason == 0 and "session" in kwargs:
		session = kwargs["session"]
		epgrefresh.session = session

		from EPGBackupSupport import EPGBackupSupport
		try:
			epgbackup = EPGBackupSupport(session)
		except:
			print("[EPGRefresh] Error while initializing EPGBackupSupport")
			print_exc(file=stdout)
	
		if config.plugins.epgrefresh.enabled.value:
			# check if box was woken up by a timer, if so, check if epgrefresh set this timer
			if session.nav.wasTimerWakeup() and config.misc.prev_wakeup_time.value == config.plugins.epgrefresh.wakeup_time.value:
				# if box is not in idle mode, do that
				from Screens.Standby import Standby, inStandby
				if not inStandby:
					from Tools import Notifications
					Notifications.AddNotificationWithID("Standby", Standby)
			timeCallback(isCallback=False)

	elif reason == 1:
		epgrefresh.stop()

def getNextWakeup():
	# Return invalid time if not automatically refreshing
	if not config.plugins.epgrefresh.enabled.value or \
		not config.plugins.epgrefresh.wakeup.value:

		setConfigWakeupTime(-1)	
		return -1

	now = localtime()
	begin = int(mktime(
		(now.tm_year, now.tm_mon, now.tm_mday,
		config.plugins.epgrefresh.begin.value[0],
		config.plugins.epgrefresh.begin.value[1],
		0, now.tm_wday, now.tm_yday, now.tm_isdst)
	))

	# todays timespan has not yet begun
	if begin > time():
		setConfigWakeupTime(begin)
		return begin

	# otherwise add 1 day
	setConfigWakeupTime(begin+86400)
	return begin+86400

def setConfigWakeupTime(value):
	config.plugins.epgrefresh.wakeup_time.value = value
	config.plugins.epgrefresh.save()

# Mainfunction
def main(session, **kwargs):
	epgrefresh.stop()
	try:
		from EPGRefreshConfiguration import EPGRefreshConfiguration
		session.openWithCallback(
			doneConfiguring,
			EPGRefreshConfiguration
		)
	except:
		print("[EPGRefresh] Error while Opening EPGRefreshConfiguration")
		print_exc(file=stdout)

def forceRefresh(session, **kwargs):
	epgrefresh.forceRefresh(session)

def stopRunningRefresh(session, **kwargs):
	epgrefresh.stopRunningRefresh(session)

def restoreBackup(session, **kwargs):
	epgbackup.forceBackup()

def showPendingServices(session, **kwargs):
	epgrefresh.showPendingServices(session)

def doneConfiguring(session, needsRestart):
	if needsRestart:
		session.openWithCallback(boundFunction(restartGUICB, session), MessageBox, \
				_("To apply your Changes the GUI has to be restarted.\nDo you want to restart the GUI now?"), \
				MessageBox.TYPE_YESNO, timeout =  30)
	else:
		_startAfterConfig(session)

def restartGUICB(session, answer):
	if answer is True:
		session.open(TryQuitMainloop, 3)
	else:
		_startAfterConfig(session)

def _startAfterConfig(session):
	if config.plugins.epgrefresh.enabled.value:
			epgrefresh.start(session)

# Eventinfo
def eventinfo(session, servicelist, **kwargs):
	ref = session.nav.getCurrentlyPlayingServiceReference()
	if not ref:
		return
	sref = ref.toString()
	# strip all after last :
	pos = sref.rfind(':')
	if pos != -1:
		sref = sref[:pos+1]

	epgrefresh.services[0].add(EPGRefreshService(str(sref), None))

# XXX: we need this helper function to identify the descriptor
# Extensions menu
def extensionsmenu(session, **kwargs):
	main(session, **kwargs)

extSetupDescriptor = PluginDescriptor(name=_("EXTENSIONNAME_SETUP"), description = _("Automatically refresh EPG"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = extensionsmenu, needsRestart=False)
extRunDescriptor = PluginDescriptor(name = _("EPGRefresh Start now"), description = _("Start EPGrefresh immediately"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = forceRefresh, needsRestart = False)
extStopDescriptor = PluginDescriptor(name=_("EPGRefresh Stop"), description = _("Stop Running EPG-refresh"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = stopRunningRefresh, needsRestart = False)
extBackupDescriptor = PluginDescriptor(name = _("EPGRefresh Restore Backup"), description = _("Start a Restore of a Backup"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = restoreBackup, needsRestart = False)
extPendingServDescriptor = PluginDescriptor(name = _("EPGRefresh Pending Services"), description = _("Show the pending Services for refresh"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = showPendingServices, needsRestart = False)

def AdjustExtensionsmenu(enable, PlugDescriptor):
	if enable:
		plugins.addPlugin(PlugDescriptor)
	else:
		try:
			plugins.removePlugin(PlugDescriptor)
		except ValueError as ve:
			print("[EPGRefresh] AdjustExtensionsmenu got confused, tried to remove non-existant plugin entry... ignoring.")

def housekeepingExtensionsmenu(configentry):
	PlugDescriptor = None
	if configentry == config.plugins.epgrefresh.show_in_extensionsmenu:
		PlugDescriptor = extSetupDescriptor
	elif configentry == config.plugins.epgrefresh.show_run_in_extensionsmenu:
		PlugDescriptor = extRunDescriptor
	elif configentry == config.plugins.epgrefresh.show_backuprestore_in_extmenu:
		PlugDescriptor = extBackupDescriptor
	if PlugDescriptor != None:
		AdjustExtensionsmenu(configentry.value, PlugDescriptor)

config.plugins.epgrefresh.show_in_extensionsmenu.addNotifier(housekeepingExtensionsmenu, initial_call = False, immediate_feedback = True)
config.plugins.epgrefresh.show_run_in_extensionsmenu.addNotifier(housekeepingExtensionsmenu, initial_call = False, immediate_feedback = True)
config.plugins.epgrefresh.show_backuprestore_in_extmenu.addNotifier(housekeepingExtensionsmenu, initial_call = False, immediate_feedback = True)

def Plugins(**kwargs):
	# NOTE: this might be a little odd to check this, but a user might expect
	# the plugin to resume normal operation if installed during runtime, but
	# this is not given if the plugin is supposed to run in background (as we
	# won't be handed the session which we need to zap). So in turn we require
	# a restart if-and only if-we're installed during runtime AND running in
	# background. To improve the user experience in this situation, we hide
	# all references to this plugin.
	needsRestart = config.plugins.epgrefresh.enabled.value and not plugins.firstRun
	list = [
		PluginDescriptor(
			name = "EPGRefresh",
			where = [
				PluginDescriptor.WHERE_AUTOSTART,
				PluginDescriptor.WHERE_SESSIONSTART
			],
			fnc = autostart,
			wakeupfnc = getNextWakeup,
			needsRestart = needsRestart,
		),
		PluginDescriptor(
			name = _("add to EPGRefresh"),
			where = PluginDescriptor.WHERE_EVENTINFO,
			fnc = eventinfo,
			needsRestart = needsRestart,
		),
		PluginDescriptor(
			name = _("PLUGINNAME_EPGRefresh"),
			description = _("Automatically refresh EPG"),
			where = PluginDescriptor.WHERE_PLUGINMENU, 
			fnc = main,
			needsRestart = needsRestart,
		),
	]
	if config.plugins.epgrefresh.show_in_extensionsmenu.value:
		extSetupDescriptor.needsRestart = needsRestart
		list.append(extSetupDescriptor)
	if config.plugins.epgrefresh.show_run_in_extensionsmenu.value:
		extRunDescriptor.needsRestart = needsRestart
		list.append(extRunDescriptor)
	if config.plugins.epgrefresh.show_backuprestore_in_extmenu.value:
		extBackupDescriptor.needsRestart = needsRestart
		list.append(extBackupDescriptor)

	return list
