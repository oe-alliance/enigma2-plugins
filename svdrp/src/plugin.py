from Plugins.Plugin import PluginDescriptor

from SVDRP import SimpleVDRProtocolAbstraction

connection = None

def autostart(reason, **kwargs):
	if reason == 0:
		global connection
		connection = SimpleVDRProtocolAbstraction()

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			where=PluginDescriptor.WHERE_AUTOSTART,
			fnc=autostart,
			needsRestart=False,
		),
	]

