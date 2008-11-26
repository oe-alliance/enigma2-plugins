##
## RS Downloader
## by AliAbdul
##
from Plugins.Plugin import PluginDescriptor
from RS import rapidshare
from RSMain import RSMain
from RSTranslation import _

##############################################################################

def autostart(reason, **kwargs):
	if reason == 0:
		rapidshare.startDownloading()

##############################################################################

def main(session, **kwargs):
	session.open(RSMain)

##############################################################################

def Plugins(**kwargs):
	return [PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart),
			PluginDescriptor(name=_("RS Downloader"), description=_("Download files from rapidshare in the background"), where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], icon="rs.png", fnc=main)]
