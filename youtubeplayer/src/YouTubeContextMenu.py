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


from Components.MenuList import MenuList
from Screens.Screen import Screen
from Components.ActionMap import ActionMap


class YouTubeEntryContextMenuList(MenuList):
	def __init__(self):
		self.menuList = []
		MenuList.__init__(self, self.menuList)

	def appendEntry(self, entry):
		self.menuList.append(entry)


class YouTubeEntryContextMenu(Screen):
	def __init__(self, session, menuList, title):
		Screen.__init__(self, session)
		self.tmpTitle = title

		self["actions"] = ActionMap(["OkCancelActions"],
		{
			"ok": self.okbuttonClick,
			"cancel": self.cancelClick
		})
		self["menu"] = menuList

		self.onFirstExecBegin.append(self.setTitleDelaied)

	def okbuttonClick(self):
		self.close(self["menu"].getCurrent()[1])

	def cancelClick(self):
		self.close(None)

	def setTitleDelaied(self):
		self.setTitle(self.tmpTitle)
