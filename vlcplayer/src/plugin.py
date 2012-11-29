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
from . import _

from Plugins.Plugin import PluginDescriptor

from VlcServerList import VlcServerListScreen
from VlcMediaList import VlcMediaListScreen
from VlcServerConfig import vlcServerConfig

class __VlcManager():
	def __init__(self, session):
		print "[VLC] VlcManager"
		self.session = session

	def startSession(self):
		defaultServer = vlcServerConfig.getDefaultServer()
		if defaultServer is None:
			self.openServerlist()
		else:
			self.openMedialist(defaultServer)

	def openServerlist(self):
		print "[VLC] openServerlist"
		defaultServer = vlcServerConfig.getDefaultServer()
		self.session.openWithCallback(self.serverlistClosed, VlcServerListScreen, defaultServer)

	def serverlistClosed(self, selectedServer, defaultServer):
		vlcServerConfig.setAsDefault(defaultServer)
		self.openMedialist(selectedServer)

	def openMedialist(self, selectedServer):
		print "[VLC] openMedialist"
		if selectedServer is not None:
			self.session.openWithCallback(self.medialistClosed, VlcMediaListScreen, selectedServer).keyUpdate()

	def medialistClosed(self, proceed = False):
		print "[VLC] medialistClosed"
		if proceed:
			self.openServerlist()


def main(session, **kwargs):
	__VlcManager(session).startSession()


def Plugins(**kwargs):
	return PluginDescriptor(
		name="VLC Video Player",
		description=_("A video streaming solution based on VLC"),
		where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
		icon = "plugin.png", fnc = main)
