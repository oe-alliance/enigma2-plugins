from __future__ import print_function

from . import _
# Plugin definition
from Plugins.Plugin import PluginDescriptor

from Components.PluginComponent import PluginComponent
from Components.config import config, ConfigSubsection, ConfigSet

from PluginHiderSetup import PluginHiderSetup

from operator import attrgetter

from boxbranding import getImageDistro

config.plugins.pluginhider = ConfigSubsection()
config.plugins.pluginhider.hideextensions = ConfigSet(choices=[])
config.plugins.pluginhider.hideplugins = ConfigSet(choices=[])
config.plugins.pluginhider.hideeventinfo = ConfigSet(choices=[])

hasPluginWeight = True

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
	if hasPluginWeight:
		res.sort(key=attrgetter('weight'))
	return res

def autostart(reason, *args, **kwargs):
	if reason == 0:
		if hasattr(PluginComponent, 'pluginHider_baseGetPlugins'):
			print("[PluginHider] Something went wrong as our autostart handler was called multiple times for startup, printing traceback and ignoring.")
			import traceback, sys
			traceback.print_stack(limit=5, file=sys.stdout)
		else:
			PluginComponent.pluginHider_baseGetPlugins = PluginComponent.getPlugins
			PluginComponent.getPlugins = PluginComponent_getPlugins
	else:
		if hasattr(PluginComponent, 'pluginHider_baseGetPlugins'):
			PluginComponent.getPlugins = PluginComponent.pluginHider_baseGetPlugins
			del PluginComponent.pluginHider_baseGetPlugins
		else:
			print("[PluginHider] Something went wrong as our autostart handler was called multiple times for shutdown, printing traceback and ignoring.")
			import traceback, sys
			traceback.print_stack(limit=5, file=sys.stdout)

def main(session, *args, **kwargs):
	session.open(PluginHiderSetup)

def menu(menuid):
	if getImageDistro() in ('openmips'):
		if menuid != "general_menu":
			return [ ]
	else:
		if menuid != "system":
			return []
	return [(_("Hide Plugins"), main, "pluginhider_setup", None)]

def Plugins(**kwargs):
	pd =  PluginDescriptor(
		where=PluginDescriptor.WHERE_AUTOSTART,
		fnc=autostart,
		needsRestart=False,
	)

	if not hasattr(pd, 'weight'):
		global hasPluginWeight
		hasPluginWeight = False

	return [
		pd,
		PluginDescriptor(
			where=PluginDescriptor.WHERE_MENU,
			fnc=menu,
			needsRestart=False,
		),
	]
