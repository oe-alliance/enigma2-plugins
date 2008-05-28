# -*- coding: ISO-8859-1 -*-
#===============================================================================
# VLC Player Plugin by A. Lätsch 2007
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from enigma import eServiceCenter
from VlcFileList import VlcFileList
from VlcConfig import VLCSettings, VLCServerConfig
from VlcPlayer import VlcPlayer

class VlcBrowser(Screen):
	skin = """
		<screen position="80,100" size="560,400" title="VLC Video Player V1.6" >
			<widget name="currentdir" position="10,10" size="550,20" font="Regular;18"/>
			<widget name="filelist" position="10,35" size="550,310"  scrollbarMode="showOnDemand"/>
			<ePixmap name="red"    position="0,355"   zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green"  position="140,355" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,355" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue"   position="420,355" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,355" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,355" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="280,355" zPosition="5" size="140,40" valign="center" halign="center"  font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="420,355" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	defaultFilter = "(?i)\.(avi|mpeg|mpg|divx|xvid|mp4|mov|ts|vob|wmv|mkv|iso)$"
	
	def __init__(self, session):
		self.session = session
		self.serviceHandler = eServiceCenter.getInstance()
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()
		self.filelist = VlcFileList(self.defaultFilter)

		Screen.__init__(self, session)
		self["currentdir"] = Label("Loading Serverlist...")
		self["filelist"] = self.filelist
		self["key_red"] = Button("filter off")
		self["key_green"] = Button("serverlist")
		self["key_yellow"] = Button("edit server")
		self["key_blue"] = Button(_("settings"))
		self["actions"] = ActionMap(["WizardActions", "MenuActions", "ShortcutActions", "MoviePlayerActions"], 
			{
			 "back": 	self.close, 
			 "red": 	self.keyFilter, 
			 "green": 	self.keyServerlist, 
			 "yellow": 	self.keyEditServer, 
			 "blue": 	self.keySettings, 
			 "up": 		self.up, 
			 "down": 	self.down, 
			 "left": 	self.left, 
			 "right": 	self.right, 
			 "ok":		self.ok, 
			 }, -1)

		self.onLayoutFinish.append(self.keyServerlist)
		self.onClose.append(self.__onClose)

	def keyServerlist(self):
		self.changeDir(None)

	def keyFilter(self):
		if self.filelist.matchingPattern is None:
			self.filelist.matchingPattern = self.defaultFilter
			self["key_red"].setText("filter off")
		else:
			self.filelist.matchingPattern = None
			self["key_red"].setText("filter on")
		dir = self.filelist.getCurrentDirectory()
		self.changeDir(dir)

	def keyEditServer(self):
		servernum = None
		if self.filelist.current_server is None:
			if self.filelist.getSelection() is not None:
				path, isdir = self.filelist.getSelection()
				if isdir:
					servernum = int(path[0:path.find(":")])
		else:
			servernum = self.filelist.current_server
		self.session.openWithCallback(self.refresh, VLCServerConfig, servernum)

	def keySettings(self):
		self.session.open(VLCSettings)

	def up(self):
		self.filelist.up()

	def down(self):
		self.filelist.down()

	def left(self):
		self.filelist.pageUp()

	def right(self):
		self.filelist.pageDown()
	
	def ok(self):
		if self.filelist.getSelection() is not None:
			path, isdir = self.filelist.getSelection()
			if path is None:
				self.session.openWithCallback(self.refresh, VLCServerConfig, None)
			elif isdir:
				self.changeDir(path)
			else:
				servernum, path = path.split(":", 1)
				servernum = int(servernum)
				dlg = self.session.open(VlcPlayer, self.filelist)
				dlg.playfile(servernum, path)

	def __onClose(self):
		self.session.nav.playService(self.oldService)

	def refresh(self):
		self.changeDir(None)
	
	def changeDir(self, dir):
		try:
			self.filelist.changeDir(dir, self.filelist.getCurrentDirectory())
		except Exception, e:
			self.session.open(
				MessageBox, _("Error contacting server %s:\n%s" % (dir, e)), MessageBox.TYPE_ERROR)
			return
		dir = self.filelist.getCurrentDirectory()
		if dir is None:
			self["currentdir"].setText("Serverlist")
		else:
			dir = self.filelist.current_path
			if len(dir) >= 50:
				dir = "..." + dir[-50:]
			self["currentdir"].setText(dir)

#
#-------------------------------------------------------------------------------------------
#
def main(session, **kwargs):
	session.open(VlcBrowser)

def Plugins(**kwargs):
 	return PluginDescriptor(
		name="VLC Video Player", 
		description="VLC Video Player", 
		where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
		fnc = main)
