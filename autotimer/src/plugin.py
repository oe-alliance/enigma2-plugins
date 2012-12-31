from __future__ import print_function

from . import _, config

# GUI (Screens)
from Screens.MessageBox import MessageBox
# Plugin
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

from AutoTimer import AutoTimer
autotimer = AutoTimer()
autopoller = None

#pragma mark - Help
try:
	from Plugins.SystemPlugins.MPHelp import registerHelp, XMLHelpReader
	from Tools.Directories import resolveFilename, SCOPE_PLUGINS
	file = open(resolveFilename(SCOPE_PLUGINS, "Extensions/AutoTimer/mphelp.xml"), 'r')
	reader = XMLHelpReader(file)
	file.close()
	autotimerHelp = registerHelp(*reader)
except Exception as e:
	print("[AutoTimer] Unable to initialize MPHelp:", e,"- Help not available!")
	autotimerHelp = None
#pragma mark -

# Autostart
def autostart(reason, **kwargs):
	global autopoller

	# Startup
	if reason == 0 and config.plugins.autotimer.autopoll.value:
		# Start Poller
		from AutoPoller import AutoPoller
		autopoller = AutoPoller()
		autopoller.start()

		# Install NPB, main is too late because the Browser is already running
		from Plugins.SystemPlugins.Toolkit import NotifiablePluginBrowser
		NotifiablePluginBrowser.install()
	# Shutdown
	elif reason == 1:
		# Stop Poller
		if autopoller is not None:
			autopoller.stop()
			autopoller = None

		# We re-read the config so we won't save wrong information
		try:
			autotimer.readXml()
		except Exception:
			# XXX: we should at least dump the error
			pass
		else:
			autotimer.writeXml()

# Webgui
def sessionstart(reason, **kwargs):
	if reason == 0 and "session" in kwargs:
		try:
			from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
			from Plugins.Extensions.WebInterface.WebChilds.Screenpage import ScreenPage
			from twisted.web import static
			from twisted.python import util
			from WebChilds.UploadResource import UploadResource

			from AutoTimerResource import AutoTimerDoParseResource, \
				AutoTimerListAutoTimerResource, AutoTimerAddOrEditAutoTimerResource, \
				AutoTimerRemoveAutoTimerResource, AutoTimerChangeSettingsResource, \
				AutoTimerSettingsResource, AutoTimerSimulateResource, API_VERSION
		except ImportError as ie:
			pass
		else:
			if hasattr(static.File, 'render_GET'):
				class File(static.File):
					def render_POST(self, request):
						return self.render_GET(request)
			else:
				File = static.File

			# webapi
			root = AutoTimerListAutoTimerResource()
			root.putChild('parse', AutoTimerDoParseResource())
			root.putChild('remove', AutoTimerRemoveAutoTimerResource())
			root.putChild('edit', AutoTimerAddOrEditAutoTimerResource())
			root.putChild('get', AutoTimerSettingsResource())
			root.putChild('set', AutoTimerChangeSettingsResource())
			root.putChild('simulate', AutoTimerSimulateResource())
			addExternalChild( ("autotimer", root , "AutoTimer-Plugin", API_VERSION, False) )

			# webgui
			session = kwargs["session"]
			root = File(util.sibpath(__file__, "web-data"))
			root.putChild("web", ScreenPage(session, util.sibpath(__file__, "web"), True) )
			root.putChild('tmp', File('/tmp'))
			root.putChild("uploadfile", UploadResource(session))
			addExternalChild( ("autotimereditor", root, "AutoTimer", "1", True) )

# Mainfunction
def main(session, **kwargs):
	global autopoller

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
		autopoller.stop()

	from AutoTimerOverview import AutoTimerOverview
	session.openWithCallback(
		editCallback,
		AutoTimerOverview,
		autotimer
	)

def editCallback(session):
	global autopoller

	# XXX: canceling of GUI (Overview) won't affect config values which might have been changed - is this intended?

	# Don't parse EPG if editing was canceled
	if session is not None:
		# Save xml
		autotimer.writeXml()
		# Poll EPGCache
		autotimer.parseEPG()

	# Start autopoller again if wanted
	if config.plugins.autotimer.autopoll.value:
		if autopoller is None:
			from AutoPoller import AutoPoller
			autopoller = AutoPoller()
		autopoller.start()
	# Remove instance if not running in background
	else:
		autopoller = None

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
# TRANSLATORS: description of AutoTimer in PluginBrowser
pluginlist = PluginDescriptor(name="AutoTimer", description = _("Edit Timers and scan for new Events"), where = PluginDescriptor.WHERE_PLUGINMENU, icon = "plugin.png", fnc = main, needsRestart = False)

def Plugins(**kwargs):
	l = [
		PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart, needsRestart=False),
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart, needsRestart=False),
		# TRANSLATORS: AutoTimer title in MovieList (automatically opens importer, I consider this no further interaction)
		PluginDescriptor(name="AutoTimer", description= _("add AutoTimer"), where = PluginDescriptor.WHERE_MOVIELIST, fnc = movielist, needsRestart = False),
		# TRANSLATORS: AutoTimer title in EventInfo dialog (requires the user to select an event to base the AutoTimer on)
		PluginDescriptor(name=_("add AutoTimer..."), where = PluginDescriptor.WHERE_EVENTINFO, fnc = eventinfo, needsRestart = False),
		PluginDescriptor(name=_("Auto Timers"), description = _("Edit Timers and scan for new Events"), where=PluginDescriptor.WHERE_MENU, fnc=timermenu),
	]
	if config.plugins.autotimer.show_in_extensionsmenu.value:
		l.append(extDescriptor)
	if config.plugins.autotimer.show_in_plugins.value:
		l.append(pluginlist)
	return l

def timermenu(menuid):
	if menuid == "timermenu":
		return [(_("AutoTimers"), main, "autotimer_setup", None)]
	return []

