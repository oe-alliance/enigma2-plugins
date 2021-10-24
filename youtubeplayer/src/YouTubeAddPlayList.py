from __future__ import absolute_import
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

from Screens.Screen import Screen

from Components.config import Config
from Components.config import ConfigText
from Components.config import ConfigYesNo
from Components.config import getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Button import Button

from .ConfigTextWithSuggestions import ConfigTextWithSuggestions

from . import _

playlistContext = Config()
playlistContext.name = ConfigText(_("Name"), False)
playlistContext.description = ConfigText(_("Description"), False)
playlistContext.private = ConfigYesNo()


class YouTubeAddPlaylistDialog(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)

		self.session = session

		self["actions"] = ActionMap(["YouTubeAddPlaylistActions"],
		{
			"save": self.keySave,
			"cancel": self.keyCancel
		}, -2)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		cfglist = []
		cfglist.append(getConfigListEntry(_("Playlist Name"), playlistContext.name))
		cfglist.append(getConfigListEntry(_("Playlist Description"), playlistContext.description))
		cfglist.append(getConfigListEntry(_("private"), playlistContext.private))

		ConfigListScreen.__init__(self, cfglist, session)

	def keySave(self):
		self.close(True, playlistContext)

	def keyCancel(self):
		self.close(False, playlistContext)
