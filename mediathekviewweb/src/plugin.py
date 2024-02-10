# -*- coding: UTF-8 -*-
from Plugins.Plugin import PluginDescriptor
from six.moves import reload_module


def main(session, **kwargs):
	from . import mediathekviewweb
	reload_module(mediathekviewweb)
	session.open(mediathekviewweb.Mediathekviewweb)


def Plugins(**kwargs):
	return PluginDescriptor(name="Mediathekviewweb", description="Mediathekviewweb Plugin für Enigma2", where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], icon="logo.png", fnc=main)
