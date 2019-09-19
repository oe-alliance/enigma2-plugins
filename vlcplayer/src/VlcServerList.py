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
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.MenuList import MenuList
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.config import config
from Screens.ChoiceBox import ChoiceBox
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap
from VlcServerConfig import vlcServerConfig
from VlcServerConfig import VlcServerConfigScreen
from enigma import eListboxPythonMultiContent, RT_HALIGN_LEFT, gFont
import os
from skin import parseFont

class VlcServerList(MenuList):
	def __init__(self):
		MenuList.__init__(self, list, False, eListboxPythonMultiContent)
		self.font = gFont("Regular", 18)
		self.l.setFont(0, self.font)
		self.l.setItemHeight(23)
		self.l.setBuildFunc(self.buildListboxEntry)

	def applySkin(self, desktop, parent):
		attribs = [ ]
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "font":
					self.font = parseFont(value, ((1,1),(1,1)))
					self.l.setFont(0, self.font)
				elif attrib == "itemHeight":
					self.l.setItemHeight(int(value))
				else:
					attribs.append((attrib, value))
			self.skinAttributes = attribs
		return MenuList.applySkin(self, desktop, parent)

	def buildListboxEntry(self, vlcServer, defaultServer):
		size = self.l.getItemSize()
		height = size.height()
		res = [
			vlcServer,
			(eListboxPythonMultiContent.TYPE_TEXT, height + 15, 0, size.width() - height - 15, height, 0, RT_HALIGN_LEFT, vlcServer.getName())
		]

		if defaultServer is not None and defaultServer.getName() == vlcServer.getName():
			png = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/VlcPlayer/vlc_default.png"))
		else:
			png = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/VlcPlayer/vlc.png"))

		if png is not None:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 0, height, height, png))

		return res

	def update(self, serverList, defaultServer):
		self.list = [(server, defaultServer) for server in serverList]
		self.l.setList(self.list)
		self.moveToIndex(0)

	def getSelection(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]

class VlcServerListScreen(Screen):
	skin = """
		<screen position="80,100" size="560,400" title="Select VLC-Server Profile" >
			<widget name="serverlabel" position="10,10" size="550,20" font="Regular;17"/>
			<widget name="serverlist" position="10,35" size="550,310"  scrollbarMode="showOnDemand"/>
			<ePixmap name="red"    position="0,355"   zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green"  position="140,355" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,355" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue"   position="420,355" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,355" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,355" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="280,355" zPosition="5" size="140,40" valign="center" halign="center"  font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="420,355" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, defaultServer):
		Screen.__init__(self, session)
		self.session = session
		self.serverlist = VlcServerList()
		self.defaultServer = defaultServer
		
		self.setTitle(_("Select VLC-Server profile"))
		self["serverlabel"] = Label(_("List of known profiles. Note: key info - help"))
		self["serverlist"] = self.serverlist
		self["key_red"] = Button(_("delete server"))
		self["key_green"] = Button(_("add server"))
		self["key_yellow"] = Button(_("edit server"))
		self["key_blue"] = Button(_("set default"))

		self["actions"] = ActionMap(["WizardActions", "ColorActions", "ChannelSelectEPGActions"],
			{
			 "back": 	self.close,
			 "red": 	self.keyDelete,
			 "green": 	self.keyAddServer,
			 "yellow": 	self.keyEditServer,
			 "blue":	self.keyGetDefault,
			 "up": 		self.up,
			 "down": 	self.down,
			 "left": 	self.left,
			 "right": 	self.right,
			 "ok":		self.ok,
			 "info":	self.showHelp,
			 "epg":		self.showHelp
            }, -1)

		self.onLayoutFinish.append(self.initialServerlistUpdate)

	def initialServerlistUpdate(self):
		self.updateServerlist()
		if self.defaultServer is not None:
			defaultIndex = vlcServerConfig.getServerlist().index(self.defaultServer)
			self.serverlist.moveToIndex(defaultIndex)

	def updateServerlist(self):
		self.serverlist.update(vlcServerConfig.getServerlist(), self.defaultServer)

	def keyAddServer(self):
		newServer = vlcServerConfig.new()
		self.session.openWithCallback(self.addCallback, VlcServerConfigScreen, newServer)

	def addCallback(self, result, server):
		if result:
			vlcServerConfig.save(server)
			self.updateServerlist()
		else:
			vlcServerConfig.delete(server)

	def showHelp(self):
		#os.system("cat /usr/lib/enigma/python/Plugins/Extensions/VlcPlayer/help.txt")
		self.session.open(MessageBox,
			_("Latest compatible version VLC 2.0.7\nSetup VLC for PC:\nTools -> Preferences -> All -> Interface -> Main Interface -> Select Web\nFind file c:/Program Files/VideoLAN/VLC/Lua/http/.hosts and insert your box ip (without #).\nAdd shortcut to the startup of the background start VLC 'C:\Program Files\VideoLAN\VLC\vlc.exe --intf telnet --extraintf http'"),
			MessageBox.TYPE_INFO
		)

	def keyDelete(self):
		server = self.serverlist.getSelection()
		if server is not None:
			self.session.openWithCallback(self.deleteCallback, MessageBox, _("Really delete this Server?"))

	def deleteCallback(self, result):
		if result:
			vlcServerConfig.delete(self.serverlist.getSelection())
			self.updateServerlist()

	def keyEditServer(self):
		server = self.serverlist.getSelection()
		if server is not None:
			self.session.openWithCallback(self.editCallback, VlcServerConfigScreen, server)

	def editCallback(self, result, server):
		if result:
			vlcServerConfig.save(server)
			index = self.serverlist.getSelectedIndex()
			self.updateServerlist()
			self.serverlist.moveToIndex(index)
		else:
			vlcServerConfig.cancel(server)

	def keyGetDefault(self):
		server = self.serverlist.getSelection()
		if config.plugins.vlcplayer.defaultserver.value != '':
			if server is not None:
				self.session.openWithCallback(self.actionCallback, ChoiceBox, title=_("Choose an action:"), list=[(_("Set as default"), "set"), (_("Reset default"), "reset")])
		else:
			if server is not None:
				self.keySetAsDefault()

	def actionCallback(self, answer):
		if answer is None:
			return
		if answer[1] == "set":
			self.keySetAsDefault()
		elif answer[1] == "reset":
			self.keyResetDefault()
		else:
			pass

	def keyResetDefault(self):
		config.plugins.vlcplayer.defaultserver.value = ''
		config.plugins.vlcplayer.defaultserver.save()
		self.defaultServer = None
		self.updateServerlist()

	def keySetAsDefault(self):
		self.defaultServer = self.serverlist.getSelection()
		index = self.serverlist.getSelectedIndex()
		self.updateServerlist()
		self.serverlist.moveToIndex(index)

	def up(self):
		self.serverlist.up()

	def down(self):
		self.serverlist.down()

	def left(self):
		self.serverlist.pageUp()

	def right(self):
		self.serverlist.pageDown()

	def close(self, server = None):
		Screen.close(self, server, self.defaultServer)

	def ok(self):
		self.close(self.serverlist.getSelection())
