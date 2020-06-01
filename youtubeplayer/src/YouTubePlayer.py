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

from Plugins.Extensions.VlcPlayer.VlcPlayer import VlcPlayer
from Components.ActionMap import ActionMap

from YouTubeContextMenu import YouTubeEntryContextMenu, YouTubeEntryContextMenuList


class YouTubePlayer(VlcPlayer):
	def __init__(self, session, server, currentList, contextMenuEntries, infoCallback, name):
		VlcPlayer.__init__(self, session, server, currentList)
		self.contextMenuEntries = contextMenuEntries
		self.infoCallback = infoCallback
		self.name = name

		self["menuactions"] = ActionMap(["YouTubePlayerScreenActions"],
		{
			"menu":	self.openContextMenu,
			"info":	self.showVideoInfo,
		}, -1)


	def showVideoInfo(self):
		if self.shown:
			self.hideInfobar()
		self.infoCallback()


	def openContextMenu(self):
		if self.shown:
			self.hideInfobar()
		contextMenuList = YouTubeEntryContextMenuList()
		for entry in self.contextMenuEntries:
			contextMenuList.appendEntry(entry)
		self.session.openWithCallback(self.menuActionCoosen, YouTubeEntryContextMenu, contextMenuList, self.name)


	def menuActionCoosen(self, cookie):
		if cookie is not None:
			if cookie[1]:
				self.stop()
			cookie[0]()
