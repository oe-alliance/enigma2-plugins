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
from Components.config import getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Button import Button

from ConfigTextWithSuggestions import ConfigTextWithSuggestions

from . import _

searchContext = Config()
searchContext.searchTerm = ConfigTextWithSuggestions("", False, threaded = True)


SEARCH		= 1
STDFEEDS 	= 2
PLAYLISTS 	= 3
FAVORITES 	= 4
CANCEL		= 5


class YouTubeSearchDialog(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)

		self.session = session

		self.propagateUpDownNormally = True
		
		self["actions"] = ActionMap(["YouTubeSearchDialogActions"],
		{
			"standard"	:	self.keyStdFeeds,
			"search"	:	self.keySearch,
			"playlists"	:	self.keyPlaylists,
			"favorites"	:	self.keyFavorites,

			"cancel"	:	self.keyCancel,
			"left"		:	self.keyLeft,
			"right"		:	self.keyRight,
			"up"		:	self.keyUp,
			"down"		:	self.keyDown,
		}, -2)

		self["key_red"] = Button(_("Std.Feeds"))
		self["key_green"] = Button(_("Search"))
		self["key_yellow"] = Button(_("Playlists"))
		self["key_blue"] = Button(_("Favorites"))

		searchContextEntries = []
		searchContextEntries.append(getConfigListEntry(_("Search Term(s)"), searchContext.searchTerm))

		ConfigListScreen.__init__(self, searchContextEntries, session)


	def keyOK(self):
		if isinstance(self["config"].getCurrent()[1], ConfigTextWithSuggestions):
			if not self.propagateUpDownNormally:
				self.propagateUpDownNormally = True
				self["config"].getCurrent()[1].deactivateSuggestionList()
			else:
				if self["config"].getCurrent()[1].activateSuggestionList():
					self.propagateUpDownNormally = False
			self["config"].invalidateCurrent()
		else:
			ConfigListScreen.keyOK(self)


	def keyUp(self):
		if self.propagateUpDownNormally:
			self["config"].instance.moveSelection(self["config"].instance.moveUp)
		else:
			self["config"].getCurrent()[1].suggestionListUp()
			self["config"].invalidateCurrent()


	def keyDown(self):
		if self.propagateUpDownNormally:
			self["config"].instance.moveSelection(self["config"].instance.moveDown)
		else:
			self["config"].getCurrent()[1].suggestionListDown()
			self["config"].invalidateCurrent()


	def keyRight(self):
		if self.propagateUpDownNormally:
			ConfigListScreen.keyRight(self)
		else:
			self["config"].getCurrent()[1].suggestionListPageDown()
			self["config"].invalidateCurrent()


	def keyLeft(self):
		if self.propagateUpDownNormally:
			ConfigListScreen.keyLeft(self)
		else:
			self["config"].getCurrent()[1].suggestionListPageUp()
			self["config"].invalidateCurrent()


	def keyCancel(self):
		if self.propagateUpDownNormally:
			self.close(CANCEL)
		else:
			self.propagateUpDownNormally = True
			self["config"].getCurrent()[1].cancelSuggestionList()
			self["config"].invalidateCurrent()


	def keySearch(self):
		if searchContext.searchTerm.value != "":
			if isinstance(self["config"].getCurrent()[1], ConfigTextWithSuggestions) and not self.propagateUpDownNormally:
				self.propagateUpDownNormally = True
				self["config"].getCurrent()[1].deactivateSuggestionList()
			self.close(SEARCH, searchContext)


	def keyStdFeeds(self):
		if isinstance(self["config"].getCurrent()[1], ConfigTextWithSuggestions) and not self.propagateUpDownNormally:
			self.propagateUpDownNormally = True
			self["config"].getCurrent()[1].deactivateSuggestionList()
		self.close(STDFEEDS)


	def keyPlaylists(self):
		if isinstance(self["config"].getCurrent()[1], ConfigTextWithSuggestions) and not self.propagateUpDownNormally:
			self.propagateUpDownNormally = True
			self["config"].getCurrent()[1].deactivateSuggestionList()
		self.close(PLAYLISTS)


	def keyFavorites(self):
		if isinstance(self["config"].getCurrent()[1], ConfigTextWithSuggestions) and not self.propagateUpDownNormally:
			self.propagateUpDownNormally = True
			self["config"].getCurrent()[1].deactivateSuggestionList()
		self.close(FAVORITES)
