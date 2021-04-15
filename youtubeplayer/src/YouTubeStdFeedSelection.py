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
from Components.Sources.List import List
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

from . import _


class YouTubeStdFeedSelectionScreen(Screen):
	STD_FEED = "http://gdata.youtube.com/feeds/api/standardfeeds/"

	def __init__(self, session):
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["OkCancelActions"],
			{
				"ok"		: self.ok,
				"cancel"	: self.close
			})

		menu = [(_("Most Viewed"), "most_viewed")]
		menu.append((_("Top Rated"), "top_rated"))
		menu.append((_("Recently Featured"), "recently_featured"))
		menu.append((_("Watch On Mobile"), "watch_on_mobile"))
		menu.append((_("Most Discussed"), "most_discussed"))
		menu.append((_("Top Favorites"), "top_favorites"))
		menu.append((_("Most Linked"), "most_linked"))
		menu.append((_("Most Responded"), "most_responded"))
		menu.append((_("Most Recent"), "most_recent"))

		self["menu"] = List(menu)

	def ok(self):
		Screen.close(self, self.STD_FEED + self["menu"].getCurrent()[1])

	def close(self):
		Screen.close(self, None)
