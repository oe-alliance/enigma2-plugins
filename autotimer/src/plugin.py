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
config.plugins.autotimer.disabled_on_conflict = ConfigEnableDisable(default = False)
config.plugins.autotimer.show_in_extensionsmenu = ConfigYesNo(default = False)
config.plugins.autotimer.fastscan = ConfigYesNo(default = False)
config.plugins.autotimer.notifconflict = ConfigYesNo(default = True)
config.plugins.autotimer.maxdaysinfuture = ConfigNumber(default = 0)
config.plugins.autotimer.show_help = ConfigYesNo(default = True)

autotimer = None
autopoller = None


#pragma mark - Help
def getHelpName():
	return _("AutoTimer Help")

def getHelpText():
	return (
		(
			_("Welcome to the AutoTimer-Plugin"),
			_("This help screen is supposed to give you a quick look at everything the AutoTimer has to offer.\nYou can abort it at any time by pressing the RED or EXIT button on your remote control or bring it up at a later point by selecting it from the control menu using the MENU button from the regular entry point of the plugin (more on that later).\n\n\nBut you really should consider to take the few minutes it takes to read this help pages.")
		),
		(
			_("The \"Overview\""),
			_("The AutoTimer overview is the standard entry point to this plugin.\n\nIf AutoTimers are configured you can choose them from a list to change them (OK button on your remove) or remove them (YELLOW button on your remote).\nNew Timers can be added by pressing the BLUE button and the control menu can be opened using the MENU button.\n\nWhen leaving the plugin using the GREEN button it will search the EPG for matching events ONCE. To configure a regular search interval of the plugin to search for events open the control menu and enter the plugin setup.")
		),
		(
			_("What is this \"control menu\" you keep talking about?"),
			_("The control menu hides less frequently used options of the plugin, including the configuration and default settings for new AutoTimers.\n\nWhile you can just open the menu and take a look for yourself, let's go through the available options:\n - Help:\n   What you are looking at right now\n - Preview:\n   Simulate EPG search, helps finding errors in your setup.\n - Import existing Timer:\n   Create a new AutoTimer based on an existing regular timer.\n - Import from EPG:\n   Create an AutoTimer based on an EPG event.\n - Setup:\n   Generic configuration of the plugin.\n - Edit new timer defaults:\n   Configure default values for new AutoTimers.\n - Create a new timer using the wizard/classic editor:\n   Use the non-default editor to create a new AutoTimer.")
		),
		(
			_("Generic setup"),
			_("This screen should be pretty straight-forward. If the option name does not give its meaning away there should be an explanation for each of them when you select them. If there is no visible explanation this is most likely a skin issue and please try if the default skin fixes the issue.\n\nA lot of effort has been put in making the parameters as easy to understand as possible, so give reading them a try ;-).")
		),
		(
			_("Wizard or Classic Editor?"),
			_("This is mostly a matter of taste.\nThe Wizard provides you with a reduced set of options and presents them in smaller sets at a time. It is mostly aimed at users not very experienced with this plugin or the \"expert\" level features of enigma2.\n\nYou can check out the \"classic\" editor by opening an existing timer from the overview and if you prefer this view over the wizard you can change the default editor in the setup dialog.")
		),
		(
			_("Congratulations"),
			_("You now know almost everything there is to know about the AutoTimer-Plugin.\n\nAs a final hint I can't stress how important it is to take a look at the help texts that are shown in the setup dialogs as they cover the most frequently asked questions. Surprisingly even after the hints were added ;-).")
		),
	)

try:
	from Plugins.SystemPlugins.MPHelp import registerHelp
except ImportError, ie:
	print "[AutoTimer] Unable to find MPHelp, help not available!"
else:
	registerHelp(getHelpName, getHelpText, "AutoTimerHelp")
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
			_("Found a total of %d matching Events.\n%d Timer were added and %d modified, %d conflicts encountered.") % (ret[0], ret[1], ret[2], len(ret[4])),
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
		plugins.removePlugin(extDescriptor)

config.plugins.autotimer.show_in_extensionsmenu.addNotifier(housekeepingExtensionsmenu, initial_call = False, immediate_feedback = True)
extDescriptor = PluginDescriptor(name="AutoTimer", description = _("Edit Timers and scan for new Events"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = extensionsmenu, needsRestart = False)

def Plugins(**kwargs):
	l = [
		PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, fnc = autostart, needsRestart = False),
		PluginDescriptor(name="AutoTimer", description = _("Edit Timers and scan for new Events"), where = PluginDescriptor.WHERE_PLUGINMENU, icon = "plugin.png", fnc = main, needsRestart = False),
		PluginDescriptor(name="AutoTimer", description= _("add AutoTimer..."), where = PluginDescriptor.WHERE_MOVIELIST, fnc = movielist, needsRestart = False),
		PluginDescriptor(name=_("add AutoTimer..."), where = PluginDescriptor.WHERE_EVENTINFO, fnc = eventinfo, needsRestart = False),
	]
	if config.plugins.autotimer.show_in_extensionsmenu.value:
		l.append(extDescriptor)
	return l

