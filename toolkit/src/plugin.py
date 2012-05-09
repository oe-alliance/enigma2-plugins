def autostart(reason, *args, **kwargs):
	import NotifiablePluginBrowser
	if reason == 1:
		NotifiablePluginBrowser.uninstall()

def Plugins(**kwargs):
	from Plugins.Plugin import PluginDescriptor
	return [
		PluginDescriptor(
			where=PluginDescriptor.WHERE_AUTOSTART,
			fnc=autostart,
			needsRestart=False,
		),
	]
