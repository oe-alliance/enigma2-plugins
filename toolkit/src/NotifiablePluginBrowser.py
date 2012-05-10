from Screens import PluginBrowser
from Screens.InfoBarGenerics import InfoBarNotifications

OriginalPluginBrowser = PluginBrowser.PluginBrowser
if not issubclass(OriginalPluginBrowser, InfoBarNotifications):
	class NotifiablePluginBrowser(OriginalPluginBrowser, InfoBarNotifications):
		def __init__(self, *args, **kwargs):
			OriginalPluginBrowser.__init__(self, *args, **kwargs)
			if self.skinName == "NotifiablePluginBrowser":
				self.skinName = "PluginBrowser"
			InfoBarNotifications.__init__(self)
else:
	NotifiablePluginBrowser = OriginalPluginBrowser

def install():
	PluginBrowser.PluginBrowser = NotifiablePluginBrowser

def uninstall():
	PluginBrowser.PluginBrowser = OriginalPluginBrowser

__all__ = ['OriginalPluginBrowser', 'NotifiablePluginBrowser', 'install', 'uninstall']
