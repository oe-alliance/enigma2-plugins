# -*- coding: utf-8 -*-
# CurlyTx plugin registration and startup
# Copyright (C) 2011 Christian Weiske <cweiske@cweiske.de>
# License: GPLv3 or later

from Plugins.Plugin import PluginDescriptor

import CurlyTx
from . import config
from Components.config import config

 
def main(session, **kwargs):
    """ Opens the main window """
    try:
        session.open(CurlyTx.CurlyTx)
    except:
        import traceback
        traceback.print_exc()

def menuHook(menuid):
    """ Called whenever a menu is created """
    if menuid == "mainmenu" and config.plugins.CurlyTx.menuMain.value:
        return [(config.plugins.CurlyTx.menuTitle.value, main, "curlytx", 41)]
    return []

 
def Plugins(**kwargs):
    """ Register CurlyTx in the extension list and main menu """
    list = [
#        PluginDescriptor(name = config.plugins.CurlyTx.menuTitle.value,
#                         description = "View remote text files",
#                         where = [PluginDescriptor.WHERE_PLUGINMENU],
#                         fnc = main),
        PluginDescriptor(name=config.plugins.CurlyTx.menuTitle.value,
                         description=_("View remote text files"),
                         where=PluginDescriptor.WHERE_MENU,
                         fnc=menuHook),
        ]
    if config.plugins.CurlyTx.menuExtensions.value:
        list.append(
            PluginDescriptor(name=config.plugins.CurlyTx.menuTitle.value,
                             description=_("View remote text files"),
                             where=[PluginDescriptor.WHERE_EXTENSIONSMENU],
                             fnc=main)
        )
    return list
