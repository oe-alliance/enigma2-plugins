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


from enigma import eListboxPythonMultiContent, RT_HALIGN_LEFT, gFont
from Components.config import config
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.LoadPixmap import LoadPixmap

from VlcServerConfig import VlcServerConfig
from VlcServerConfig import VlcServerConfigScreen
from VlcMediaList import VlcMediaListScreen
from VlcServerConfig import vlcPluginInfo, _

def VlcServerListEntry(vlcServer):
	res = [ vlcServer ]
	res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 470, 20, 0, RT_HALIGN_LEFT, vlcServer.getName()))

	png = LoadPixmap(vlcPluginInfo.pluginPath + "/vlc.png")
	if png is not None:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 2, 20, 20, png))

	return res


class VlcServerList(MenuList):
	def __init__(self):
		MenuList.__init__(self, list, False, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 18))
		self.l.setItemHeight(23)

	def update(self, serverList):
		self.list = []
		for server in serverList:
			self.list.append(VlcServerListEntry(server))
		self.l.setList(self.list)
		self.moveToIndex(0)

	def getSelection(self):
		if self.l.getCurrentSelection() is None:
			return None
		return self.l.getCurrentSelection()[0]


class VlcServerListScreen(Screen):
	skin = """
		<screen position="80,100" size="560,400" title="VLC Video Player V2.5" >
			<widget name="serverlabel" position="10,10" size="550,20" font="Regular;18"/>
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

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.serverlist = VlcServerList()
		self.vlcServerConfig = VlcServerConfig()

		self["serverlabel"] = Label("List of known VLC-Server")
		self["serverlist"] = self.serverlist
		self["key_red"] = Button(_("delete server"))
		self["key_green"] = Button(_("add server"))
		self["key_yellow"] = Button(_("edit server"))
		self["key_blue"] = Button("")

		self["actions"] = ActionMap(["WizardActions", "MenuActions", "ShortcutActions", "MoviePlayerActions"],
			{
			 "back": 	self.close,
			 "red": 	self.keyDelete,
			 "green": 	self.keyAddServer,
			 "yellow": 	self.keyEditServer,
			 "up": 		self.up,
			 "down": 	self.down,
			 "left": 	self.left,
			 "right": 	self.right,
			 "ok":		self.ok,
			 }, -1)

		self.onLayoutFinish.append(self.updateServerlist)

	def updateServerlist(self):
		self.serverlist.update(self.vlcServerConfig.getServerlist())

	def keyAddServer(self):
		newServer = self.vlcServerConfig.new()
		self.session.openWithCallback(self.addCallback, VlcServerConfigScreen, newServer)

	def addCallback(self, result, server):
		if result:
			self.vlcServerConfig.save(server)
			self.updateServerlist()
		else:
			self.vlcServerConfig.delete(server)

	def keyDelete(self):
		self.session.openWithCallback(self.deleteCallback, MessageBox, _("Really delete this Server?"))

	def deleteCallback(self, result):
		if result:
			self.vlcServerConfig.delete(self.serverlist.getSelection())
			self.updateServerlist()

	def keyEditServer(self):
		server = self.serverlist.getSelection()
		if server is not None:
			self.session.openWithCallback(self.editCallback, VlcServerConfigScreen, server)

	def editCallback(self, result, server):
		if result:
			self.vlcServerConfig.save(server)
			self.updateServerlist()
		else:
			self.vlcServerConfig.cancel(server)

	def up(self):
		self.serverlist.up()

	def down(self):
		self.serverlist.down()

	def left(self):
		self.serverlist.pageUp()

	def right(self):
		self.serverlist.pageDown()

	def ok(self):
		if self.serverlist.getSelection() is not None:
			self.session.open(VlcMediaListScreen, self.serverlist.getSelection()).update()
