# Plugin definition
from Plugins.Plugin import PluginDescriptor

from Components.PluginComponent import PluginComponent
from Components.config import config, ConfigSubsection, ConfigSet

from PluginHiderSetup import PluginHiderSetup

config.plugins.pluginhider = ConfigSubsection()
config.plugins.pluginhider.hideextensions = ConfigSet(choices=[])
config.plugins.pluginhider.hideplugins = ConfigSet(choices=[])
config.plugins.pluginhider.hideeventinfo = ConfigSet(choices=[])

def hidePlugin(plugin):
	"""Convenience function for external code to hide a plugin."""
	hide = config.plugins.pluginhider.hideplugins.value
	if not plugin.name in hide:
		hide.append(plugin.name)
		config.plugins.pluginhider.hideplugins.save()	

def PluginComponent_getPlugins(self, where):
	if not isinstance(where, list):
		where = [ where ]

	res = []
	if PluginDescriptor.WHERE_EXTENSIONSMENU in where:
		hide = config.plugins.pluginhider.hideextensions.value
		res.extend((x for x in self.plugins.get(PluginDescriptor.WHERE_EXTENSIONSMENU, []) if x.name not in hide))
		where.remove(PluginDescriptor.WHERE_EXTENSIONSMENU)

	if PluginDescriptor.WHERE_PLUGINMENU in where:
		hide = config.plugins.pluginhider.hideplugins.value
		res.extend((x for x in self.plugins.get(PluginDescriptor.WHERE_PLUGINMENU, []) if x.name not in hide))
		where.remove(PluginDescriptor.WHERE_PLUGINMENU)

	if PluginDescriptor.WHERE_EVENTINFO in where:
		hide = config.plugins.pluginhider.hideeventinfo.value
		res.extend((x for x in self.plugins.get(PluginDescriptor.WHERE_EVENTINFO , []) if x.name not in hide))
		where.remove(PluginDescriptor.WHERE_EVENTINFO)

	if where:
		res.extend(PluginComponent.pluginHider_baseGetPlugins(self, where))
	res.sort(key=lambda x:x.weight)
	return res

def autostart(reason, *args, **kwargs):
	if reason == 0:
		PluginComponent.pluginHider_baseGetPlugins = PluginComponent.getPlugins
		PluginComponent.getPlugins = PluginComponent_getPlugins
	else:
		PluginComponent.getPlugins = PluginComponent.pluginHider_baseGetPlugins

def main(session, *args, **kwargs):
	session.open(PluginHiderSetup)

def menu(menuid):
	if menuid != "system":
		return []
	return [(_("Hide Plugins"), main, "pluginhider_setup", None)]

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			where=PluginDescriptor.WHERE_AUTOSTART,
			fnc=autostart,
			needsRestart=False,
		),
		PluginDescriptor(
			where=PluginDescriptor.WHERE_MENU,
			fnc=menu,
			needsRestart=False,
		),
	]
