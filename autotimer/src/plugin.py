# for localized messages
from . import _

# GUI (Screens)
from Screens.MessageBox import MessageBox

# Config
from Components.config import config, ConfigSubsection, ConfigEnableDisable, \
	ConfigNumber, ConfigSelection

# Initialize Configuration
config.plugins.autotimer = ConfigSubsection()
config.plugins.autotimer.autopoll = ConfigEnableDisable(default = False)
config.plugins.autotimer.interval = ConfigNumber(default = 3)
config.plugins.autotimer.refresh = ConfigSelection(choices = [
		("none", _("None")),
		("auto", _("Only AutoTimers created during this Session")),
		("all", _("All non-repeating Timers"))
	], default = "none"
)
config.plugins.autotimer.try_guessing = ConfigEnableDisable(default = True)

autotimer = None
autopoller = None

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
			# We might shutdown when configuring, timer won't be running then
			try:
				autopoller.stop()
			except ValueError, ve:
				pass

			autopoller = None

		if autotimer is not None:
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

	from xml.parsers.expat import ExpatError

	try:
		autotimer.readXml()
	except ExpatError, ee:
		session.open(
			MessageBox,
			"Your config file is not well-formed.\nError parsing in line: %s" % (ee.lineno),
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
			"Found a total of %d matching Events.\n%d Timer were added and %d modified.." % (ret[0], ret[1], ret[2]),
			type = MessageBox.TYPE_INFO,
			timeout = 10
		)

	# Start autopoller again if wanted
	if config.plugins.autotimer.autopoll.value:
		if autopoller is None:
			from AutoPoller import AutoPoller
			autopoller = AutoPoller()
		autopoller.start(initial = False)
	# Remove instance if not running in background
	else:
		autopoller = None

		# Save xml (as long as we did not cancel)
		session and autotimer.writeXml()
		autotimer = None

# Movielist
def movielist(session, service, **kwargs):
	from AutoTimerEditor import addAutotimerFromService
	addAutotimerFromService(session, service)

def Plugins(**kwargs):
	from Plugins.Plugin import PluginDescriptor

	return [
		PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, fnc = autostart),
		PluginDescriptor(name="AutoTimer", description = _("Edit Timers and scan for new Events"), where = PluginDescriptor.WHERE_PLUGINMENU, icon = "plugin.png", fnc = main),
		PluginDescriptor(name="AutoTimer", description = _("Edit Timers and scan for new Events"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = main),
		PluginDescriptor(name="AutoTimer", description= _("Add AutoTimer..."), where = PluginDescriptor.WHERE_MOVIELIST, fnc = movielist)
	]
