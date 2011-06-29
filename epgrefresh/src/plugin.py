# for localized messages
from . import _

# Config
from Components.config import config, ConfigYesNo, ConfigNumber, \
	ConfigSelection, ConfigSubsection, ConfigClock, ConfigYesNo

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
config.plugins.epgrefresh.interval = ConfigNumber(default = 2)
config.plugins.epgrefresh.delay_standby = ConfigNumber(default = 10)
config.plugins.epgrefresh.inherit_autotimer = ConfigYesNo(default = False)
config.plugins.epgrefresh.afterevent = ConfigYesNo(default = False)
config.plugins.epgrefresh.force = ConfigYesNo(default = False)
config.plugins.epgrefresh.enablemessage = ConfigYesNo(default = True)
config.plugins.epgrefresh.wakeup = ConfigYesNo(default = False)
config.plugins.epgrefresh.lastscan = ConfigNumber(default = 0)
config.plugins.epgrefresh.parse_autotimer = ConfigYesNo(default = False)
config.plugins.epgrefresh.adapter = ConfigSelection(choices = [
		("main", _("Main Picture")),
		("pip", _("Picture in Picture")),
		("pip_hidden", _("Picture in Picture (hidden)")),
		("record", _("Fake recording")),
	], default = "main"
)
config.plugins.epgrefresh.show_in_extensionsmenu = ConfigYesNo(default = False)
config.plugins.epgrefresh.show_help = ConfigYesNo(default = True)

# convert previous parameter
config.plugins.epgrefresh.background = ConfigYesNo(default = False)
if config.plugins.epgrefresh.background.value:
	config.plugins.epgrefresh.adapter.value = "pip_hidden"
	config.plugins.epgrefresh.background.value = False
	config.plugins.epgrefresh.save()

del now, begin, end

#pragma mark - Help
def getHelpName():
	return _("EPGRefresh Help")

def getHelpText():
	return (
		HelpPage(
			_("Welcome to EPGRefresh"),
			_("This help screen is supposed to give you a quick look at everything EPGRefresh has to offer.\nYou can abort it at any time by pressing the RED or EXIT button on your remote control or bring it up at a later point by pressing the HELP button from the configuration menu (more on that later).\n\n\nBut you really should consider to take the few minutes it takes to read these help pages.")
		),
		HelpPage(
			_("The configuration menu"),
			_("This is the entry point of EPGRefresh. From this menu you can configure every aspect of the plugin and start a manual refresh of the EPG.\nThe configuration options each have an explaination which is supposed to help you to understand their effects better. Please give reading them a try, they can save you a lot of time.\n\nUsing the YELLOW button you can start a refresh manually and the INFO button brings up the date the last refresh was completed successfully.\nThe BLUE key opens the service editor (next page).")
		),
		HelpPage(
			_("Editing the service list"),
			_("While the screen does not immediately show it, it does have a lot to offer. The topmost line allows you to choose between the editor for channels and bouquets and the following lines contain the channels/bouquets you chose to refresh.\n\nYou can use the BLUE button to add a new entry to the list or the YELLOW button to remove an existing one.\n\n\nFor most people it should be sufficient to add the \"Favourites\" bouquet by selecting \"Bouquets\" in the first line and by adding it using the BLUE button.")
		),
		HelpPage(
			_("Congratulations"),
			_("You now know how to do your first steps in EPGRefresh.\n\nAs a final note I want to hint you at the fact that this plugin will not do anything on it's own without YOU telling it to. So if you want the refresh to happen automatically in the background you need to configure the plugin to do so.\nThis was not done to cause you any inconvenience but rather to give you the freedom of choice.")
		),
	)

try:
	from Plugins.SystemPlugins.MPHelp import registerHelp, HelpPage
except ImportError, ie:
	print "[EPGRefresh] Unable to find MPHelp, help not available!"
else:
	registerHelp(getHelpName, getHelpText, "EPGRefreshHelp")
#pragma mark -

# Plugin
from EPGRefresh import epgrefresh
from EPGRefreshConfiguration import EPGRefreshConfiguration
from EPGRefreshService import EPGRefreshService

# Plugins
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

def standbyQuestionCallback(session, res = None):
	if res:
		from Screens.Standby import Standby
		session.open(Standby)

# Autostart
def autostart(reason, **kwargs):
	if reason == 0 and kwargs.has_key("session"):
		session = kwargs["session"]
		epgrefresh.session = session

		if config.plugins.epgrefresh.enabled.value:
			if config.plugins.epgrefresh.wakeup.value:
				now = localtime()
				begin = int(mktime(
					(now.tm_year, now.tm_mon, now.tm_mday,
					config.plugins.epgrefresh.begin.value[0],
					config.plugins.epgrefresh.begin.value[1],
					0, now.tm_wday, now.tm_yday, now.tm_isdst)
				))
				# booted +- 10min from begin of timespan
				if abs(time() - begin) < 600:
					from Screens.MessageBox import MessageBox
					from Tools.Notifications import AddNotificationWithCallback
					from Tools.BoundFunction import boundFunction
					# XXX: we use a notification because this will be suppressed otherwise
					AddNotificationWithCallback(
						boundFunction(standbyQuestionCallback, session),
						MessageBox,
						_("This might have been an automated bootup to refresh the EPG. For this to happen it is recommended to put the receiver to Standby.\nDo you want to do this now?"),
						timeout = 15
					)

			epgrefresh.start(session)

	elif reason == 1:
		epgrefresh.stop()

def getNextWakeup():
	# Return invalid time if not automatically refreshing
	if not config.plugins.epgrefresh.enabled.value or \
		not config.plugins.epgrefresh.wakeup.value:

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
		return begin
	# otherwise add 1 day
	return begin+86400

# Mainfunction
def main(session, **kwargs):
	epgrefresh.stop()
	session.openWithCallback(
		doneConfiguring,
		EPGRefreshConfiguration
	)

def doneConfiguring(session, **kwargs):
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

def housekeepingExtensionsmenu(el):
	if el.value:
		plugins.addPlugin(extDescriptor)
	else:
		plugins.removePlugin(extDescriptor)

config.plugins.epgrefresh.show_in_extensionsmenu.addNotifier(housekeepingExtensionsmenu, initial_call = False, immediate_feedback = True)
extDescriptor = PluginDescriptor(name="EPGRefresh", description = _("Automatically refresh EPG"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = extensionsmenu, needsRestart=False)

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
			name = "EPGRefresh",
			description = _("Automatically refresh EPG"),
			where = PluginDescriptor.WHERE_PLUGINMENU, 
			fnc = main,
			needsRestart = needsRestart,
		),
	]
	if config.plugins.epgrefresh.show_in_extensionsmenu.value:
		extDescriptor.needsRestart = needsRestart
		list.append(extDescriptor)

	return list
