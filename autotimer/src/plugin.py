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

# Webinterface
from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
from Plugins.Extensions.WebInterface.WebChilds.Screenpage import ScreenPage

# Twisted
from twisted.web import static
from twisted.python import util

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
config.plugins.autotimer.episode_scheme = ConfigSelection(choices = [
		(" S{season:02d}E{episode:02d}",  _("S01E01")),
		(" S{season:d}E{episode:d}",      _("S1E1")),
		(" S{season:02d}xE{episode:02d}", _("S01xE01")),
		(" S{season:d}xE{episode:d}",     _("S1xE1")),
		(" S{season:02d}.E{episode:02d}", _("S01.E01")),
		(" S{season:d}.E{episode:d}",     _("S1.E1")),
		(" S{season:02d} E{episode:02d}", _("S01 E01")),
		(" S{season:d} E{episode:d}",     _("S1 E1")),
		(" {season:02d}{episode:02d}",    _("0101")),
		(" {season:d}{episode:02d}",      _("101")),
		(" {season:02d}x{episode:02d}",   _("01x01")),
		(" {season:d}x{episode:d}",       _("1x1")),
		(" {season:02d}.{episode:02d}",   _("01.01")),
		(" {season:d}.{episode:d}",       _("1.1")),
		(" {season:02d} {episode:02d}",   _("01 01")),
		(" {season:d} {episode:d}",       _("1 1")),
		("_S{season:02d}E{episode:02d}",  _("_S01E01")),
		("_S{season:d}E{episode:d}",      _("_S1E1")),
		("_S{season:02d}xE{episode:02d}", _("_S01xE01")),
		("_S{season:d}xE{episode:d}",     _("_S1xE1")),
		("_S{season:02d}.E{episode:02d}", _("_S01.E01")),
		("_S{season:d}.E{episode:d}",     _("_S1.E1")),
		("_S{season:02d} E{episode:02d}", _("_S01 E01")),
		("_S{season:d} E{episode:d}",     _("_S1 E1")),
		("_{season:02d}{episode:02d}",    _("_0101")),
		("_{season:d}{episode:02d}",      _("_101")),
		("_{season:02d}x{episode:02d}",   _("_01x01")),
		("_{season:d}x{episode:d}",       _("_1x1")),
		("_{season:02d}.{episode:02d}",   _("_01.01")),
		("_{season:d}.{episode:d}",       _("_1.1")),
		("_{season:02d} {episode:02d}",   _("_01 01")),
		("_{season:d} {episode:d}",       _("_1 1")),

		(" S{season:02d}E{episode:02d} {title:s}",  _("S01E01 title")),
		(" S{season:d}E{episode:d} {title:s}",      _("S1E1 title")),
		(" S{season:02d}xE{episode:02d} {title:s}", _("S01xE01 title")),
		(" S{season:d}xE{episode:d} {title:s}",     _("S1xE1 title")),
		(" S{season:02d}.E{episode:02d} {title:s}", _("S01.E01 title")),
		(" S{season:d}.E{episode:d} {title:s}",     _("S1.E1 title")),
		(" S{season:02d} E{episode:02d} {title:s}", _("S01 E01 title")),
		(" S{season:d} E{episode:d} {title:s}",     _("S1 E1 title")),
		(" {season:02d}{episode:02d} {title:s}",    _("0101 title")),
		(" {season:d}{episode:02d} {title:s}",      _("101 title")),
		(" {season:02d}x{episode:02d} {title:s}",   _("01x01 title")),
		(" {season:d}x{episode:d} {title:s}",       _("1x1 title")),
		(" {season:02d}.{episode:02d} {title:s}",   _("01.01 title")),
		(" {season:d}.{episode:d} {title:s}",       _("1.1 title")),
		(" {season:02d} {episode:02d} {title:s}",   _("01 01 title")),
		(" {season:d} {episode:d} {title:s}",       _("1 1 title")),
		("_S{season:02d}E{episode:02d}_{title:s}",  _("_S01E01_title")),
		("_S{season:d}E{episode:d}_{title:s}",      _("_S1E1_title")),
		("_S{season:02d}xE{episode:02d}_{title:s}", _("_S01xE01_title")),
		("_S{season:d}xE{episode:d}_{title:s}",     _("_S1xE1_title")),
		("_S{season:02d}.E{episode:02d}_{title:s}", _("_S01.E01_title")),
		("_S{season:d}.E{episode:d}_{title:s}",     _("_S1.E1_title")),
		("_S{season:02d} E{episode:02d}_{title:s}", _("_S01 E01_title")),
		("_S{season:d} E{episode:d}_{title:s}",     _("_S1 E1_title")),
		("_{season:02d}{episode:02d}_{title:s}",    _("_0101_title")),
		("_{season:d}{episode:02d}_{title:s}",      _("_101_title")),
		("_{season:02d}x{episode:02d}_{title:s}",   _("_01x01_title")),
		("_{season:d}x{episode:d}_{title:s}",       _("_1x1_title")),
		("_{season:02d}.{episode:02d}_{title:s}",   _("_01.01_title")),
		("_{season:d}.{episode:d}_{title:s}",       _("_1.1_title")),
		("_{season:02d} {episode:02d}_{title:s}",   _("_01 01_title")),
		("_{season:d} {episode:d}_{title:s}",       _("_1 1_title")),
	], default = " S{season:02d}E{episode:02d} {title:s}"
)

autotimer = None
autopoller = None
autotimerseries = None

#pragma mark - Help
try:
	from Plugins.SystemPlugins.MPHelp import registerHelp, XMLHelpReader
	from Tools.Directories import resolveFilename, SCOPE_PLUGINS
	reader = XMLHelpReader(resolveFilename(SCOPE_PLUGINS, "Extensions/AutoTimer/mphelp.xml"))
	autotimerHelp = registerHelp(*reader)
except Exception as e:
	print("[AutoTimer] Unable to initialize MPHelp:", e,"- Help not available!")
	autotimerHelp = None
#pragma mark -

# Autostart
def autostart(reason, **kwargs):
	global autotimer
	global autopoller
	global autotimerseries

	# Startup
	if reason == 0 and config.plugins.autotimer.autopoll.value:
		# Initialize AutoTimerSeries
		from AutoTimerSeries import AutoTimerSeries
		autotimerseries = AutoTimerSeries()

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
			autotimerseries = None

# Webgui
def sessionstart(reason, **kwargs):
	if reason == 0 and "session" in kwargs:
		from WebChilds.UploadResource import UploadResource
		if hasattr(static.File, 'render_GET'):
			class File(static.File):
				def render_POST(self, request):
					return self.render_GET(request)
		else:
			File = static.File

		session = kwargs["session"]
		root = File(util.sibpath(__file__, "web-data"))
		root.putChild("web", ScreenPage(session, util.sibpath(__file__, "web"), True) )
		root.putChild('tmp', File('/tmp'))
		root.putChild("uploadfile", UploadResource(session))
		addExternalChild( ("autotimereditor", root, "AutoTimer", "1", True) )

# Mainfunction
def main(session, **kwargs):
	global autotimer
	global autopoller
	global autotimerseries

	if autotimerseries is None:
		from AutoTimerSeries import AutoTimerSeries
		autotimerseries = AutoTimerSeries()

	if autotimer is None:
		from AutoTimer import AutoTimer
		autotimer = AutoTimer()

	try:
		autotimer.readXml()
	except SyntaxError as se:
		session.open(
			MessageBox,
			_("Your config file is not well-formed:\n%s") % (str(se)),
			type = MessageBox.TYPE_ERROR,
			timeout = 10
		)
		return

	# Do not run in background while editing, this might screw things up
	if autopoller is not None:
		autopoller.pause()

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
			_("Found a total of %d matching Events.\n%d Timer were added and\n%d modified,\n%d conflicts encountered,\n%d similars added.") % (ret[0], ret[1], ret[2], len(ret[4]), len(ret[5])),
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
		except ValueError as ve:
			print("[AutoTimer] housekeepingExtensionsmenu got confused, tried to remove non-existant plugin entry... ignoring.")

config.plugins.autotimer.show_in_extensionsmenu.addNotifier(housekeepingExtensionsmenu, initial_call = False, immediate_feedback = True)
extDescriptor = PluginDescriptor(name="AutoTimer", description = _("Edit Timers and scan for new Events"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = extensionsmenu, needsRestart = False)

def Plugins(**kwargs):
	l = [
		PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart, needsRestart=False),
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart, needsRestart=False),
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

