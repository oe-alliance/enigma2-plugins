# -*- coding: UTF-8 -*-
from Plugins.Plugin import PluginDescriptor
from six.moves import reload_module


def main(session, **kwargs):
    from . import ard
    reload_module(ard)
    session.open(ard.ArdMediathek)


def Plugins(**kwargs):
    return PluginDescriptor(name="ARD Mediathek", description="ARD Mediathek Plugin für Enigma2", where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], icon="logo.png", fnc=main)
