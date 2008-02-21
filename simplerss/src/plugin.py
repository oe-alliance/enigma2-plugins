from Components.config import config, ConfigSubsection, ConfigSubList, \
	ConfigEnableDisable, ConfigNumber, ConfigText, ConfigSelection

# Initialize Configuration
config.plugins.simpleRSS = ConfigSubsection()
config.plugins.simpleRSS.update_notification = ConfigSelection(
	choices = [
		("notification", _("Notification")),
		("preview", _("Preview")),
		("none", _("none"))
	],
	default = "preview"
)
config.plugins.simpleRSS.interval = ConfigNumber(default=15)
config.plugins.simpleRSS.feedcount = ConfigNumber(default=0)
config.plugins.simpleRSS.autostart = ConfigEnableDisable(default=False)
config.plugins.simpleRSS.keep_running = ConfigEnableDisable(default=True)
config.plugins.simpleRSS.feed = ConfigSubList()
for i in range(0, config.plugins.simpleRSS.feedcount.value):
	config.plugins.simpleRSS.feed.append(ConfigSubsection())
	config.plugins.simpleRSS.feed[i].uri = ConfigText(default="http://", fixed_size = False)
	config.plugins.simpleRSS.feed[i].autoupdate = ConfigEnableDisable(default=True)

# Global Poller-Object
rssPoller = None

# Main Function
def main(session, **kwargs):
	# Get Global rssPoller-Object
	global rssPoller

	# Create one if we have none (no autostart)
	if rssPoller is None:
		from RSSPoller import RSSPoller
		rssPoller = RSSPoller(session)

	# Show Overview when we have feeds
	if len(rssPoller.feeds):
		from RSSScreens import RSSOverview
		session.openWithCallback(closed, RSSOverview, rssPoller)
	# Show Setup otherwise
	else:
		from RSSSetup import RSSSetup
		session.openWithCallback(closed, RSSSetup, rssPoller)

# Plugin window has been closed
def closed():
	# If SimpleRSS should not run in Background: shutdown
	if not config.plugins.simpleRSS.autostart.value and \
		not config.plugins.simpleRSS.keep_running.value:

		# Get Global rssPoller-Object
		global rssPoller
		
		rssPoller.shutdown()
		rssPoller = None

# Autostart
def autostart(reason, **kwargs):
	global rssPoller

	# Instanciate when autostart active, session present and enigma2 is launching
	if config.plugins.simpleRSS.autostart.value and \
		kwargs.has_key("session") and reason == 0:

		from RSSPoller import RSSPoller
		rssPoller = RSSPoller(kwargs["session"])
	elif reason == 1:
		if rssPoller is not None:
			rssPoller.shutdown()
			rssPoller = None

# Filescan 
def filescan_open(item, session, **kwargs):
	from RSSSetup import addFeed

	# Add earch feed
	for each in item:
		addFeed(each)

	from Screens.MessageBox import MessageBox

	# Display Message
	session.open(
		MessageBox,
		"Feed(s) were added to configuration.",
		type = MessageBox.TYPE_INFO,
		timeout = 5
	)

# Filescanner
def filescan(**kwargs):
	from Components.Scanner import Scanner, ScanPath

	# Overwrite checkFile to detect remote files
	class RemoteScanner(Scanner):
		def checkFile(self, file):
			return file.path.startswith("http://") or file.path.startswith("https://")

	return [
		RemoteScanner(
			mimetypes = ["application/rss+xml", "application/atom+xml"],
			paths_to_scan = 
				[
					ScanPath(path = "", with_subdirs = False),
				],
			name = "RSS-Reader",
			description = "Subscribe Newsfeed...",
			openfnc = filescan_open,
		)
	]

def Plugins(**kwargs):
	from Plugins.Plugin import PluginDescriptor
 	return [ PluginDescriptor(name="RSS Reader", description="A simple to use RSS reader", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
 		PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart),
 		PluginDescriptor(name="View RSS", description="Let's you view current RSS entries", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main),
 		PluginDescriptor(where = PluginDescriptor.WHERE_FILESCAN, fnc = filescan)]
