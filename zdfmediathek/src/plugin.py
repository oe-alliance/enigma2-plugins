# -*- coding: UTF-8 -*-
from Plugins.Plugin import PluginDescriptor
from six.moves import reload_module
from . import zdf


def main(session, **kwargs):
    reload_module(zdf)
    session.open(zdf.ZDFMediathek)


def Plugins(**kwargs):
    return PluginDescriptor(name="ZDF Mediathek", description="ZDF Mediathek Plugin für Enigma2", where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], icon="logo.png", fnc=main)
