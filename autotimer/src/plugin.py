# for localized messages
from . import _

# GUI (Screens)
from Screens.MessageBox import MessageBox

# Config
from Components.config import config, ConfigSubsection, ConfigEnableDisable, \
	ConfigNumber, ConfigSelection, ConfigYesNo

# Plugin
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

# Initialize Configuration
config.plugins.autotimer = ConfigSubsection()
config.plugins.autotimer.autopoll = ConfigEnableDisable(default = False)
config.plugins.autotimer.interval = ConfigNumber(default = 3)
config.plugins.autotimer.refresh = ConfigSelection(choices = [
		("none", _("None")),
		("auto", _("Only AutoTimers created during this session")),
		("all", _("All non-repeating timers"))
	], default = "none"
)
config.plugins.autotimer.try_guessing = ConfigEnableDisable(default = True)
config.plugins.autotimer.editor = ConfigSelection(choices = [
		("plain", _("Classic")),
		("wizard", _("Wizard"))
	], default = "wizard"
)
config.plugins.autotimer.addsimilar_on_conflict = ConfigEnableDisable(default = False)
config.plugins.autotimer.disabled_on_conflict = ConfigEnableDisable(default = False)
config.plugins.autotimer.show_in_extensionsmenu = ConfigYesNo(default = False)
config.plugins.autotimer.fastscan = ConfigYesNo(default = False)
config.plugins.autotimer.notifconflict = ConfigYesNo(default = True)
config.plugins.autotimer.notifsimilar = ConfigYesNo(default = True)
config.plugins.autotimer.maxdaysinfuture = ConfigNumber(default = 0)
config.plugins.autotimer.show_help = ConfigYesNo(default = True)

autotimer = None
autopoller = None

#pragma mark - Help
try:
	from Plugins.SystemPlugins.MPHelp import registerHelp, XMLHelpReader
	from Tools.Directories import resolveFilename, SCOPE_PLUGINS
	reader = XMLHelpReader(resolveFilename(SCOPE_PLUGINS, "Extensions/AutoTimer/mphelp.xml"))
	autotimerHelp = registerHelp(*reader)
except Exception, e:
	print "[AutoTimer] Unable to initialize MPHelp:", e,"- Help not available!"
	autotimerHelp = None
#pragma mark -

# Autostart
def autostart(reason, **kwargs):
	global autotimer
	global autopoller

	# Startup
	if config.plugins.autotimer.autopoll.value and reason == 0:
		# Initialize AutoTimer
		from AutoTimer import AutoTimer
		autotimer = AutoTimer()

		# Start Poller
		from AutoPoller import AutoPoller
		autopoller = AutoPoller()
		autopoller.start()
	# Shutdown
	elif reason == 1:
		# Stop Poller
		if autopoller is not None:
			autopoller.stop()
			autopoller = None

		if autotimer is not None:
			# We re-read the config so we won't save wrong information
			try:
				autotimer.readXml()
			except Exception:
				# XXX: we should at least dump the error
				pass

			# Save xml
			autotimer.writeXml()

			# Remove AutoTimer
			autotimer = None

# Mainfunction
def main(session, **kwargs):
	global autotimer
	global autopoller

	if autotimer is None:
		from AutoTimer import AutoTimer
		autotimer = AutoTimer()

	try:
		autotimer.readXml()
	except SyntaxError, se:
		session.open(
			MessageBox,
			_("Your config file is not well-formed:\n%s") % (str(se)),
			type = MessageBox.TYPE_ERROR,
			timeout = 10
		)
		return

	# Do not run in background while editing, this might screw things up
	if autopoller is not None:
		autopoller.stop()

	from AutoTimerOverview import AutoTimerOverview
	session.openWithCallback(
		editCallback,
		AutoTimerOverview,
		autotimer
	)

def editCallback(session):
	global autotimer
	global autopoller

	# XXX: canceling of GUI (Overview) won't affect config values which might have been changed - is this intended?

	# Don't parse EPG if editing was canceled
	if session is not None:
		# Poll EPGCache
		ret = autotimer.parseEPG()
		session.open(
			MessageBox,
			_("Found a total of %d matching Events.\n%d Timer were added and %d modified, %d conflicts encountered, %d similars added.") % (ret[0], ret[1], ret[2], len(ret[4]), len(ret[5])),
			type = MessageBox.TYPE_INFO,
			timeout = 10
		)

		# Save xml
		autotimer.writeXml()

	# Start autopoller again if wanted
	if config.plugins.autotimer.autopoll.value:
		if autopoller is None:
			from AutoPoller import AutoPoller
			autopoller = AutoPoller()
		autopoller.start(initial = False)
	# Remove instance if not running in background
	else:
		autopoller = None
		autotimer = None

# Movielist
def movielist(session, service, **kwargs):
	from AutoTimerEditor import addAutotimerFromService
	addAutotimerFromService(session, service)

# Event Info
def eventinfo(session, servicelist, **kwargs):
	from AutoTimerEditor import AutoTimerEPGSelection
	ref = session.nav.getCurrentlyPlayingServiceReference()
	session.open(AutoTimerEPGSelection, ref)

# XXX: we need this helper function to identify the descriptor
# Extensions menu
def extensionsmenu(session, **kwargs):
	main(session, **kwargs)

def housekeepingExtensionsmenu(el):
	if el.value:
		plugins.addPlugin(extDescriptor)
	else:
		try:
			plugins.removePlugin(extDescriptor)
		except ValueError, ve:
			print "[AutoTimer] housekeepingExtensionsmenu got confused, tried to remove non-existant plugin entry... ignoring."

config.plugins.autotimer.show_in_extensionsmenu.addNotifier(housekeepingExtensionsmenu, initial_call = False, immediate_feedback = True)
extDescriptor = PluginDescriptor(name="AutoTimer", description = _("Edit Timers and scan for new Events"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = extensionsmenu, needsRestart = False)

def Plugins(**kwargs):
	l = [
		PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, fnc = autostart, needsRestart = False),
		# TRANSLATORS: description of AutoTimer in PluginBrowser
		PluginDescriptor(name="AutoTimer", description = _("Edit Timers and scan for new Events"), where = PluginDescriptor.WHERE_PLUGINMENU, icon = "plugin.png", fnc = main, needsRestart = False),
		# TRANSLATORS: AutoTimer title in MovieList (automatically opens importer, I consider this no further interaction)
		PluginDescriptor(name="AutoTimer", description= _("add AutoTimer"), where = PluginDescriptor.WHERE_MOVIELIST, fnc = movielist, needsRestart = False),
		# TRANSLATORS: AutoTimer title in EventInfo dialog (requires the user to select an event to base the AutoTimer on)
		PluginDescriptor(name=_("add AutoTimer..."), where = PluginDescriptor.WHERE_EVENTINFO, fnc = eventinfo, needsRestart = False),
	]
	if config.plugins.autotimer.show_in_extensionsmenu.value:
		l.append(extDescriptor)
	return l

