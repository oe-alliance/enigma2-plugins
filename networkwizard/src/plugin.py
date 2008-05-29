from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.SystemInfo import SystemInfo
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry, config
from Components.config import config


def NetworkWizardMain(session, **kwargs):
	session.open(NetworkWizard)

def startSetup(menuid):
	if menuid != "system": 
		return [ ]

	return [(_("Network Wizard") + "...", NetworkWizardMain, "nw_wizard", 40)]

def NetworkWizard(*args, **kwargs):
	from NetworkWizard import NetworkWizard
	return NetworkWizard(*args, **kwargs)

def Plugins(**kwargs):
	list = [
		#PluginDescriptor(name=_("Network Wizard"), description=_("Network Wizard"), where = PluginDescriptor.WHERE_MENU, fnc=startSetup) 
	]
	if config.misc.firstrun.value:
		list.append(PluginDescriptor(name=_("Network Wizard"), where = PluginDescriptor.WHERE_WIZARD, fnc=(1, NetworkWizard)))
 	return list
