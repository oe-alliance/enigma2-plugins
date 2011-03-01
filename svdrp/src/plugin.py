from Plugins.Plugin import PluginDescriptor

from SVDRP import SimpleVDRProtocolAbstraction

connection = None

def autostart(**kwargs):
	global connection
	connection = SimpleVDRProtocolAbstraction()

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			where=PluginDescriptor.WHERE_SESSIONSTART,
			fnc=autostart,
		),
	]

