# PYTHON IMPORTS
from __future__ import absolute_import

# ENIGMA IMPORTS
from Components.config import config, ConfigSubsection, ConfigSubList, ConfigEnableDisable, ConfigNumber, ConfigText, ConfigSelection
from Components.PluginComponent import plugins
from Components.Scanner import Scanner, ScanPath
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox

# PLUGIN IMPORTS
from . import RSSTickerView, _  # for localized messages
from .RSSScreens import RSSOverview
from .RSSSetup import RSSSetup, addFeed
from .RSSPoller import RSSPoller
from .RSSPoller import RSSPoller

# Initialize Configuration
config.plugins.simpleRSS = ConfigSubsection()
simpleRSS = config.plugins.simpleRSS
simpleRSS.update_notification = ConfigSelection(choices=[("notification", _("Notification")), ("preview", _("Preview")), ("ticker", _("Ticker")), ("none", _("none"))], default="preview")
simpleRSS.interval = ConfigNumber(default=15)
simpleRSS.feedcount = ConfigNumber(default=0)
simpleRSS.autostart = ConfigEnableDisable(default=False)
simpleRSS.keep_running = ConfigEnableDisable(default=True)
simpleRSS.feed = ConfigSubList()
i = 0
while i < simpleRSS.feedcount.value:
	s = ConfigSubsection()
	s.uri = ConfigText(default="http://", fixed_size=False)
	s.autoupdate = ConfigEnableDisable(default=True)
	simpleRSS.feed.append(s)
	i += 1
	del s
del simpleRSS, i
# Global Poller-Object
rssPoller = None

# Main Function


def main(session, **kwargs):
	# Get Global rssPoller-Object
	global rssPoller
	# Create one if we have none (no autostart)
	if rssPoller is None:
		rssPoller = RSSPoller()
	# Show Overview when we have feeds
	if rssPoller.feeds:
		session.openWithCallback(closed, RSSOverview, rssPoller)
	# Show Setup otherwise
	else:
		session.openWithCallback(closed, RSSSetup, rssPoller)
# Plugin window has been closed


def closed():
	# If SimpleRSS should not run in Background: shutdown
	if not (config.plugins.simpleRSS.autostart.value or config.plugins.simpleRSS.keep_running.value):
		# Get Global rssPoller-Object
		global rssPoller
		if rssPoller:
			rssPoller.shutdown()
		rssPoller = None

# Autostart


def autostart(reason, **kwargs):
	global rssPoller

	if "session" in kwargs and config.plugins.simpleRSS.update_notification.value == "ticker":
		if RSSTickerView.tickerView is None:
			RSSTickerView.tickerView = kwargs["session"].instantiateDialog(RSSTickerView.RSSTickerView)

	# Instanciate when enigma2 is launching, autostart active and session present or installed during runtime
	if reason == 0 and config.plugins.simpleRSS.autostart.value and \
		(not plugins.firstRun or "session" in kwargs):
		rssPoller = RSSPoller()
	elif reason == 1 and rssPoller is not None:
		rssPoller.shutdown()
		rssPoller = None

# Filescan


def filescan_open(item, session, **kwargs):
	# Add earch feed
	for each in item:
		addFeed(each)
	# Display Message
	session.open(MessageBox, _("%d Feed(s) were added to configuration.") % (len(item)), type=MessageBox.TYPE_INFO, timeout=5)
	# Filescanner


def filescan(**kwargs):
	# Overwrite checkFile to detect remote files
	class RemoteScanner(Scanner):
		def checkFile(self, file):
			return file.path.startswith(("http://", "https://"))
	return [RemoteScanner(mimetypes=("application/rss+xml", "application/atom+xml"),
							paths_to_scan=(ScanPath(path="",
			    	 		with_subdirs=False),),
							name="RSS-Reader",
							description=_("Subscribe Newsfeed..."),
							openfnc=filescan_open,)
			]


def Plugins(**kwargs):
	return [
		PluginDescriptor(
			name="RSS Reader",
			description=_("A simple to use RSS reader"),
			icon="plugin.png",
			where=PluginDescriptor.WHERE_PLUGINMENU,
			fnc=main,
			needsRestart=False,
			),
		PluginDescriptor(
			where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART],
			fnc=autostart,
			needsRestart=False,
			),
 		PluginDescriptor(
			name=_("View RSS..."),
			description="Let's you view current RSS entries",
			where=PluginDescriptor.WHERE_EXTENSIONSMENU,
			fnc=main,
			needsRestart=False,
			),
 		PluginDescriptor(
			where=PluginDescriptor.WHERE_FILESCAN,
			fnc=filescan,
			needsRestart=False,
			)
			]
