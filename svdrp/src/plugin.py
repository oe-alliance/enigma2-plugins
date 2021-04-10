from __future__ import absolute_import
from Plugins.Plugin import PluginDescriptor

from .SVDRP import SimpleVDRProtocolAbstraction

connection = None


def autostart(reason, **kwargs):
	global connection
	if reason == 0 and connection is None:
		connection = SimpleVDRProtocolAbstraction()


def Plugins(**kwargs):
	return [
		PluginDescriptor(
			where=PluginDescriptor.WHERE_AUTOSTART,
			fnc=autostart,
			needsRestart=False,
		),
	]

