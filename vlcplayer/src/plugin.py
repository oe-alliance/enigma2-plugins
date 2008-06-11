# -*- coding: ISO-8859-1 -*-
#===============================================================================
# VLC Player Plugin by A. Lätsch 2007
#                   modified by Volker Christian 2008
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================


from Plugins.Plugin import PluginDescriptor
from Tools.BoundFunction import boundFunction

from VlcServerList import VlcServerListScreen
from VlcServerConfig import vlcPluginInfo

def main(session, **kwargs):
	vlcPluginInfo.pluginPath = kwargs["path"]
	session.open(VlcServerListScreen)


def Plugins(**kwargs):
	return PluginDescriptor(
		name="VLC Video Player",
		description="VLC Video Player",
		where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
		icon = "plugin.png", fnc = boundFunction(main, path = kwargs["path"]))
