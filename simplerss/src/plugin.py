from Plugins.Plugin import PluginDescriptor

from RSSSetup import RSSSetup
from RSSScreens import RSSOverview
from RSSPoller import RSSPoller

from Components.config import config, ConfigSubsection, ConfigSubList, ConfigEnableDisable, ConfigInteger, ConfigText

# Initialize Configuration
config.plugins.simpleRSS = ConfigSubsection()
config.plugins.simpleRSS.show_new = ConfigEnableDisable(default=True)
config.plugins.simpleRSS.interval = ConfigInteger(default=10, limits=(5, 300))
config.plugins.simpleRSS.feedcount = ConfigInteger(default=0)
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
		rssPoller = RSSPoller(session)

	# Show Overview when we have feeds
	if len(rssPoller.feeds):
		session.openWithCallback(closed, RSSOverview, rssPoller)
	# Show Setup otherwise
	else:
		session.openWithCallback(closed, RSSSetup, rssPoller)

# Plugin window has been closed
def closed():
	# If SimpleRSS should not run in Background: shutdown
	if not config.plugins.simpleRSS.keep_running.value:
		# Get Global rssPoller-Object
		global rssPoller
		
		rssPoller.shutdown()
		rssPoller = None

# Autostart
def autostart(reason, **kwargs):
	global rssPoller

	# Instanciate when autostarting active, session present and enigma2 is launching
	if config.plugins.simpleRSS.autostart.value and kwargs.has_key("session") and reason == 0:
		rssPoller = RSSPoller(kwargs["session"])
	elif reason == 1:
		if rssPoller is not None:
			rssPoller.shutdown()
			rssPoller = None

def Plugins(**kwargs):
 	return [ PluginDescriptor(name="RSS Reader", description="A simple to use RSS reader", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
 		PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart),
 		PluginDescriptor(name="View RSS", description="Let's you view current RSS entries", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main) ]
