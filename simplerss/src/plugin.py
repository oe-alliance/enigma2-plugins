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
config.plugins.simpleRSS.feed = ConfigSubList()
for i in range(0, config.plugins.simpleRSS.feedcount.value):
	config.plugins.simpleRSS.feed.append(ConfigSubsection())
	config.plugins.simpleRSS.feed[i].uri = ConfigText(default="http://", fixed_size = False)
	config.plugins.simpleRSS.feed[i].autoupdate = ConfigEnableDisable(default=True)

rssPoller = None

# Setup
def main(session, **kwargs):
	global rssPoller
	session.open(RSSSetup, rssPoller)

# Autostart
def autostart(reason, **kwargs):
	global rssPoller

	# not nice (?), but works
	if kwargs.has_key("session") and reason == 0:
		rssPoller = RSSPoller(kwargs["session"])
	elif reason == 1:
		rssPoller.shutdown()
		rssPoller = None

# Show Overview
def showCurrent(session, **kwargs):
	global rssPoller
	if rssPoller is None:
		return
	session.open(RSSOverview, rssPoller)

def Plugins(**kwargs):
 	return [ PluginDescriptor(name="RSS Reader", description="A simple to use RSS reader", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
 		PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart),
 		PluginDescriptor(name="View RSS", description="Let's you view current RSS entries", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=showCurrent) ]
