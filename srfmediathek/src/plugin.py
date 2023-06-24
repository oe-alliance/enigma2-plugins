# -*- coding: UTF-8 -*-
from Plugins.Plugin import PluginDescriptor
from six.moves import reload_module
from . import srf


def main(session, **kwargs):
    reload_module(srf)
    session.open(srf.SRFMediathek)


def Plugins(**kwargs):
    return PluginDescriptor(name="Play SRF Mediathek", description="Play SRF Mediathek Plugin für Enigma2", where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], icon="logo.png", fnc=main)
