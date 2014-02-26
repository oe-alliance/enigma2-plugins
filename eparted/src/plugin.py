# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor
from locale import _

def main(session, **kwargs):
	from eparted import Ceparted
	session.open(Ceparted)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("eParted"), description=_("creating and manipulating partition tables"), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main, icon="eparted.png"), PluginDescriptor(name=_("eParted"), description=_("creating and manipulating partition tables"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)]
