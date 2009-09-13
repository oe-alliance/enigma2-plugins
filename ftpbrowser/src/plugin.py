#
# POC FTP Browser for Enigma2
#

from FTPBrowser import FTPBrowser
#import FTPBrowser

def main(session, **kwargs):
	session.open(FTPBrowser)
	#reload(FTPBrowser)
	#session.open(FTPBrowser.FTPBrowser)

def Plugins(**kwargs):
	from Plugins.Plugin import PluginDescriptor

	return [
		PluginDescriptor(
			name="FTPBrowser",
			where = PluginDescriptor.WHERE_PLUGINMENU,
			fnc = main
		)
	]
