# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor
from locale import _

def main(session, **kwargs):
	from flashexpander import FlashExpander
	session.open(FlashExpander)

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("FlashExpander"), description=_("extend your flash memory"), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main,icon="flashexpander.png"), PluginDescriptor(name=_("FlashExpander"), description=_("extend your flash memory"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)]
