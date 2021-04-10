############################################################################
#    Copyright (C) 2008 by Volker Christian                                #
#    Volker.Christian@fh-hagenberg.at                                      #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

from YouTubeInterface import interface
from YouTubeAddPlayList import YouTubeAddPlaylistDialog
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Label import Label
from Components.MultiContent import MultiContentEntryText
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_TOP, RT_WRAP

from . import _


def YouTubePlaylistEntryComponent(entry):
	res = [entry]

	res.append(MultiContentEntryText(pos=(5, 5), size=(550, 18), font=0, flags=RT_HALIGN_LEFT | RT_VALIGN_TOP| RT_WRAP, text=entry.getTitle()))
	res.append(MultiContentEntryText(pos=(5, 23), size=(550, 14), font=1, color=0xFFA323, color_sel=0xFFA323, flags=RT_HALIGN_LEFT | RT_VALIGN_TOP| RT_WRAP, text=entry.getDescription()))

	return res


class YouTubePlaylistList(MenuList):
	def __init__(self, list, enableWrapAround=False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 18))
		self.l.setFont(1, gFont("Regular", 14))
		self.l.setItemHeight(41)


class YouTubePlaylistScreen(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)

		self.session = session

		self["red"] = Label(_("Delete Playlist"))
		self["green"] = Label(_("Add new Playlist"))
		
		self.list = []
		self["list"] = YouTubePlaylistList(self.list)
		
		self["actions"] = ActionMap(["YouTubePlaylistScreenActions"],
		{
			"ok"		:	self.choosePlaylist,
			"delete"	:	self.deletePlaylist,
			"add"		:	self.addPlaylist,
			"cancel"	:	self.close
		}, -1)


	def loadPlaylist(self):
		self.list = []
		try:
			feed = interface.getPlaylistFeed()
			for entry in feed.getEntries():
				self.list.append(YouTubePlaylistEntryComponent(entry))
		except Exception, e:
			self.session.open(MessageBox, _("Error loading playlists:\n%s" %
					e), MessageBox.TYPE_ERROR)
		self["list"].setList(self.list)


	def choosePlaylist(self):
		Screen.close(self, self["list"].getCurrent()[0])


	def deletePlaylist(self):
		playList = self["list"].getCurrent()[0]
		if playList is not None:
			self.session.openWithCallback(self.deleteCallback, MessageBox, _("Really delete %(playlist)s?") % {"playlist": playList.getTitle()})


	def deleteCallback(self, result):
		if result:
			if interface.deletePlaylist(self["list"].getCurrent()[0]):
				self.list.remove(self["list"].getCurrent())
				self["list"].setList(self.list)


	def addPlaylist(self):
		self.session.openWithCallback(self.addCallback, YouTubeAddPlaylistDialog)


	def addCallback(self, result, playlistContext):
		if result:
			entry = interface.addPlaylist(playlistContext.name.value, playlistContext.description.value, playlistContext.private.value)
			self.list.append(YouTubePlaylistEntryComponent(entry))
			self["list"].setList(self.list)


	def close(self):
		Screen.close(self, None)
