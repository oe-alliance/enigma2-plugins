from Screens import PluginBrowser as PBBase
from Screens.InfoBarGenerics import InfoBarNotifications

OriginalPluginBrowser = PBBase.PluginBrowser
if not issubclass(OriginalPluginBrowser, InfoBarNotifications):
	class PluginBrowser(OriginalPluginBrowser, InfoBarNotifications):
		def __init__(self, *args, **kwargs):
			OriginalPluginBrowser.__init__(self, *args, **kwargs)
			#if self.skinName in ("NotifiablePluginBrowser", "OriginalPluginBrowser"):
			#	self.skinName = "PluginBrowser"
			InfoBarNotifications.__init__(self)
	NotifiablePluginBrowser = PluginBrowser
else:
	NotifiablePluginBrowser = OriginalPluginBrowser

def install():
	PBBase.PluginBrowser = NotifiablePluginBrowser

def uninstall():
	PBBase.PluginBrowser = OriginalPluginBrowser

__all__ = ['OriginalPluginBrowser', 'NotifiablePluginBrowser', 'install', 'uninstall']
