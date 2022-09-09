# -*- coding: UTF-8 -*-
from Plugins.Plugin import PluginDescriptor
from six.moves import reload_module
from . import netzkino


def main(session, **kwargs):
    reload_module(netzkino)
    session.open(netzkino.netzkino)


def Plugins(**kwargs):
    return PluginDescriptor(name="NetzKino", description="Netzkino Plugin", where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], icon="logo.png", fnc=main)
