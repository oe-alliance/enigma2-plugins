from Screens import PluginBrowser
from Screens.InfoBarGenerics import InfoBarNotifications

OriginalPluginBrowser = PluginBrowser.PluginBrowser
if not issubclass(OriginalPluginBrowser, InfoBarNotifications):
	class NotifiablePluginBrowser(OriginalPluginBrowser, InfoBarNotifications):
		def __init__(self, *args, **kwargs):
			OriginalPluginBrowser.__init__(self, *args, **kwargs)
			InfoBarNotifications.__init__(self)
	PluginBrowser.PluginBrowser = NotifiablePluginBrowser
else:
	NotifiablePluginBrowser = OriginalPluginBrowser

def uninstall():
	PluginBrowser.PluginBrowser = OriginalPluginBrowser

__all__ = ['OriginalPluginBrowser', 'NotifiablePluginBrowser', 'uninstall']
