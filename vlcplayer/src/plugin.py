# -*- coding: ISO-8859-1 -*-
#===============================================================================
# VLC Player Plugin by A. Latsch 2007
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
from Screens.MessageBox import MessageBox
import array, struct, fcntl
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, SHUT_RDWR
from os import system as os_system, path as os_path

SIOCGIFCONF = 0x8912
BYTES = 4096
testOK = False

class __VlcManager():
	def __init__(self, session):
		print "[VLC] VlcManager"
		self.session = session
		self.testThread = None
		self.testTime = 2.0
		self.testHost = ""
		self.testPort = 80

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
			if selectedServer.getPingIp():
				global testOK
				testOK = False
				self.testHost = "%s" % selectedServer.getHost()
				link = "down"
				for iface in self.get_iface_list():
					if "lo" in iface: continue
					if os_path.exists("/sys/class/net/%s/operstate"%(iface)):
						fd = open("/sys/class/net/%s/operstate"%(iface), "r")
						link = fd.read().strip()
						fd.close()
					if link != "down": break
				if link != "down":
					s = socket(AF_INET, SOCK_STREAM)
					s.settimeout(self.testTime)
					try:
						testOK = not bool(s.connect_ex((self.testHost, self.testPort)))
					except:
						testOK = False
					if testOK:
						s.shutdown(SHUT_RDWR)
					s.close()
					if testOK:
						self.session.openWithCallback(self.medialistClosed, VlcMediaListScreen, selectedServer).keyUpdate()
					else:
						self.openServerlist()
						server_name = selectedServer.getName()
						self.session.open(MessageBox, _("No ping from Server:\n%s\n%s") % (server_name, self.testHost), MessageBox.TYPE_ERROR, timeout = 5)
			else:
				self.session.openWithCallback(self.medialistClosed, VlcMediaListScreen, selectedServer).keyUpdate()

	def get_iface_list(self):
		names = array.array('B', '\0' * BYTES)
		sck = socket(AF_INET, SOCK_DGRAM)
		bytelen = struct.unpack('iL', fcntl.ioctl(sck.fileno(), SIOCGIFCONF, struct.pack('iL', BYTES, names.buffer_info()[0])))[0]
		sck.close()
		namestr = names.tostring()
		return [namestr[i:i+32].split('\0', 1)[0] for i in range(0, bytelen, 32)]

	def medialistClosed(self, proceed = False):
		print "[VLC] medialistClosed"
		if proceed:
			self.openServerlist()

def main(session, **kwargs):
	__VlcManager(session).startSession()

def Plugins(**kwargs):
	return PluginDescriptor(
		name=_("VLC Video Player"),
		description=_("A video streaming solution based on VLC"),
		where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
		icon = "plugin.png", fnc = main)
