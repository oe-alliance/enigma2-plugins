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


from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from VlcFileList import VlcFileList
from VlcPlayList import VlcPlayList
from VlcPlayer import VlcPlayer


class VlcMediaListScreen(Screen):
	skin = """
		<screen position="80,100" size="560,400" title="VLC-Server" >
			<widget name="listlabel" position="10,10" size="550,20" font="Regular;18"/>
			<widget name="filelist" position="10,35" size="550,300" scrollbarMode="showOnDemand"/>
			<widget name="playlist" position="10,35" size="550,300" scrollbarMode="showOnDemand"/>
			<ePixmap name="red"    position="0,355"   zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green"  position="140,355" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,355" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue"   position="420,355" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,355" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,355" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="280,355" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="420,355" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""
	
	defaultFilter = "(?i)\.(avi|mpeg|mpg|divx|xvid|mp4|mov|ts|vob|wmv|mkv|iso|m3u|pls|xspf)$"

	def __init__(self, session, server):
		Screen.__init__(self, session)
		self.session = session
		self.server = server
		self.filelistlabel = "Filelist:" + self.server.getBasedir()
		self.playlistlabel = "Playlist"
		self["listlabel"] = Label("")
		self["filelist"] = VlcFileList(server, self.defaultFilter)
		self["playlist"] = VlcPlayList(server)
		self["key_red"] = Button("filter off")
		self["key_green"] = Button("refresh")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("play DVD")
		self["actions"] = ActionMap(["WizardActions", "MenuActions", "ShortcutActions", "MoviePlayerActions", "EPGSelectActions"],
			{
			 "back": 	self.close,
			 "red": 	self.keyFilter,
			 "green":	self.update,
			 "yellow":	self.switchLists,
			 "blue":	self.keyDvd,
			 "up": 		self.up,
			 "down": 	self.down,
			 "left": 	self.left,
			 "right": 	self.right,
			 "ok":		self.ok,
			 "prevBouquet": self.switchLists,
			 "nextBouquet": self.switchLists,
			 }, -1)
		self.currentList = None
		self.playlistIds = []

		self.switchToFileList()

		self.onClose.append(self.__onClose)
		self.onShown.append(self.__onShown)
		
	def __onClose(self):
		try:
			for id in self.playlistIds:
				self.server.delete(id)
		except Exception, e:
			pass

	def __onShown(self):
		self.setTitle("Server: " + (self.server.getName() or self.server.getHost()))

	def update(self):
		try:
			self.updateFilelist()
			self.updatePlaylist()
			if self.currentList == self["playlist"]:
				self.switchToPlayList()
			else:
				self.switchToFileList()
		except Exception, e:
			self.session.open(
				MessageBox, _("Error updating file- and playlist from server %s:\n%s" % (
						self.server.getName(), e)
					), MessageBox.TYPE_ERROR)

	def updatePlaylist(self):
		self["playlist"].update()

	def updateFilelist(self):
		self["filelist"].update()

	def keyFilter(self):
		if self["filelist"].regex is None:
			self["filelist"].changeRegex(self.defaultFilter)
			self["key_red"].setText("filter off")
		else:
			self["filelist"].changeRegex(None)
			self["key_red"].setText("filter on")
		try:
			self.updateFilelist()
		except Exception, e:
			self.session.open(
				MessageBox, _("Error updating filelist from server %s:\n%s" % (
						self.server.getName(), e)
					), MessageBox.TYPE_ERROR)

	def keyDvd(self):
		self.play("dvdsimple://" + self.server.getDvdPath(), "DVD")

	def up(self):
		self.currentList.up()

	def down(self):
		self.currentList.down()

	def left(self):
		self.currentList.pageUp()

	def right(self):
		self.currentList.pageDown()

	def play(self, media, name):
		dlg = self.session.open(VlcPlayer, self.server, self.currentList)
		dlg.playfile(media, name)

	def ok(self):
		media, name = self.currentList.activate()
		if media is not None:
			if media.endswith(".m3u"):
				try:
					id = self.server.loadPlaylist(media)
					if id is not None:
						self.playlistIds.append(id)
						self.updatePlaylist()
				except Exception, e:
					self.session.open(
						MessageBox, _("Error loading playlist %s into server %s:\n%s" % (
								media, self.server.getName(), e)
							), MessageBox.TYPE_ERROR)
			elif media.endswith(".iso"):
				self.play("dvdsimple://" + media, "DVD")
			else:
				self.play(media, name)
		elif name is not None:
			self.setLabel(name)
	
	def setLabel(self, text):
		if self.currentList == self["filelist"]:
			self.filelistlabel = "Filelist:" + text
		else:
			self.playlistlabel = text
		self["listlabel"].setText(text)
			
	def switchLists(self):
		if self.currentList == self["filelist"]:
			self.switchToPlayList()
		else:
			self.switchToFileList()

	def switchToFileList(self):
		self["playlist"].hide()
		self["filelist"].show()
		self.currentList = self["filelist"]
		self["listlabel"].setText(self.filelistlabel)
		self["key_yellow"].setText("show playlist")

	def switchToPlayList(self):
		self["filelist"].hide()
		self["playlist"].show()
		self.currentList = self["playlist"]
		self["listlabel"].setText(self.playlistlabel)
		self["key_yellow"].setText("show filelist")
