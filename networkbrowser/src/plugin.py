# -*- coding: utf-8 -*-
# for localized messages
from __init__ import _

from Plugins.Plugin import PluginDescriptor
from NetworkBrowser import NetworkBrowser
from Components.Network import iNetwork
from MountManager import AutoMountManager

plugin_path = ""

def NetworkBrowserMain(session, iface = None, **kwargs):
	session.open(NetworkBrowser,iface, plugin_path)

def MountManagerMain(session, iface = None, **kwargs):
	session.open(AutoMountManager, iface, plugin_path)

def NetworkBrowserCallFunction(iface):
	interfaceState = iNetwork.getAdapterAttribute(iface, "up")
	if interfaceState is True:
		return NetworkBrowserMain
	else:
		return None

def MountManagerCallFunction(iface):
	return MountManagerMain

def RemountMain(session, iface = None, **kwargs):
	from AutoMount import iAutoMount
	iAutoMount.getAutoMountPoints() 

def RemountCallFunction(iface):
	if iNetwork.getAdapterAttribute(iface, "up"):
		return RemountMain

def Plugins(path, **kwargs):
	global plugin_path
	plugin_path = path
	return [
		PluginDescriptor(name=_("NetworkBrowser"), description=_("Search for network shares"), where = PluginDescriptor.WHERE_NETWORKSETUP, fnc={"ifaceSupported": NetworkBrowserCallFunction, "menuEntryName": lambda x: _("NetworkBrowser"), "menuEntryDescription": lambda x: _("Search for network shares...")}),
		PluginDescriptor(name=_("MountManager"), description=_("Manage network shares"), where = PluginDescriptor.WHERE_NETWORKSETUP, fnc={"ifaceSupported": MountManagerCallFunction, "menuEntryName": lambda x: _("MountManager"), "menuEntryDescription": lambda x: _("Manage your network shares...")}),
		PluginDescriptor(name=_("Mount again"), description=_("Attempt to mount shares again"), where = PluginDescriptor.WHERE_NETWORKSETUP,
			fnc={"ifaceSupported": RemountCallFunction,
				"menuEntryName": lambda x: _("Mount again"),
				"menuEntryDescription": lambda x: _("Attempt to recover lost mounts (in background)")})
	]

