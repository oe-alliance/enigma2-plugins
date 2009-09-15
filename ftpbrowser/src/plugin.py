#
# POC FTP Browser for Enigma2
#

from FTPBrowser import FTPBrowser

ftpbrowser = None

def main(session, **kwargs):
	global ftpbrowser
	if not ftpbrowser:
		ftpbrowser = session.instantiateDialog(FTPBrowser)
	session.execDialog(ftpbrowser)

def Plugins(**kwargs):
	from Plugins.Plugin import PluginDescriptor

	return [
		PluginDescriptor(
			name="FTPBrowser",
			where = PluginDescriptor.WHERE_PLUGINMENU,
			fnc = main
		)
	]
