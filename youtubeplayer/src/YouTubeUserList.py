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

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label
from Components.MenuList import MenuList
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap
from YouTubeUserConfig import youTubeUserConfig
from YouTubeUserConfig import YouTubeUserConfigScreen
from enigma import eListboxPythonMultiContent, RT_HALIGN_LEFT, gFont

from . import _


def YouTubeUserListEntry(youTubeUser, defaultUser):
	res = [youTubeUser]
	res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 470, 20, 0, RT_HALIGN_LEFT, youTubeUser.getName()))

	if defaultUser is not None and defaultUser.getName() == youTubeUser.getName():
		png = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/YouTubePlayer/user_default.png"))
	else:
		png = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/YouTubePlayer/user.png"))
	if png is not None:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 2, 20, 20, png))

	return res


class YouTubeUserList(MenuList):
	def __init__(self):
		MenuList.__init__(self, list, False, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 18))
		self.l.setItemHeight(23)

	def update(self, userList, defaultUser):
		self.list = []
		for user in userList:
			self.list.append(YouTubeUserListEntry(user, defaultUser))
		self.l.setList(self.list)
		self.moveToIndex(0)

	def getSelection(self):
		if self.l.getCurrentSelection() is None:
			return None
		return self.l.getCurrentSelection()[0]


class YouTubeUserListScreen(Screen):
	LOGIN_SUCCESS = 1
	LOGIN_CANCEL = 2
	LOGIN_FAILED = 3

	def __init__(self, session, defaultUser):
		Screen.__init__(self, session)
		self.session = session
		self.userlist = YouTubeUserList()
		self.defaultUser = defaultUser

		self["label_info"] = Label(_("To use the selected feature you have to login to YouTube. Select a user-profile to login!"))
		self["userlist"] = self.userlist
		self["key_red"] = Button(_("delete user"))
		self["key_green"] = Button(_("add user"))
		self["key_yellow"] = Button(_("edit user"))
		self["key_blue"] = Button(_("set default"))

		self["actions"] = ActionMap(["YouTubeUserListScreenActions"],
		{
			"delete": self.keyDelete,
			"add": self.keyAddUser,
			"edit": self.keyEditUser,
			"default": self.keySetAsDefault,
			
			"ok": self.ok,
			"cancel": self.close,
			"up": self.up,
			"down": self.down,
			"left": self.left,
			"right": self.right,
		}, -2)
		
		self.onLayoutFinish.append(self.initialUserlistUpdate)

	def showTestScreen(self):
		self.suggestionsWindow.show()

	def initialUserlistUpdate(self):
		self.updateUserlist()
		if self.defaultUser is not None:
			defaultIndex = youTubeUserConfig.getUserlist().index(self.defaultUser)
			self.userlist.moveToIndex(defaultIndex)

	def updateUserlist(self):
		self.userlist.update(youTubeUserConfig.getUserlist(), self.defaultUser)

	def keyDelete(self):
		user = self.userlist.getSelection()
		if user is not None:
			self.session.openWithCallback(self.deleteCallback, MessageBox, _("Really delete %(user)s?") % {"user": user.getName()})

	def deleteCallback(self, result):
		if result:
			youTubeUserConfig.delete(self.userlist.getSelection())
			self.updateUserlist()

	def keyAddUser(self):
		newUser = youTubeUserConfig.new()
		self.session.openWithCallback(self.addCallback, YouTubeUserConfigScreen, newUser)

	def addCallback(self, result, user):
		if result:
			youTubeUserConfig.save(user)
			self.updateUserlist()
		else:
			youTubeUserConfig.delete(user)

	def keyEditUser(self):
		user = self.userlist.getSelection()
		if user is not None:
			self.session.openWithCallback(self.editCallback, YouTubeUserConfigScreen, user)

	def editCallback(self, result, user):
		if result:
			youTubeUserConfig.save(user)
			index = self.userlist.getSelectedIndex()
			self.updateUserlist()
			self.userlist.moveToIndex(index)
		else:
			youTubeUserConfig.cancel(user)

	def keySetAsDefault(self):
		self.defaultUser = self.userlist.getSelection()
		index = self.userlist.getSelectedIndex()
		self.updateUserlist()
		self.userlist.moveToIndex(index)

	def up(self):
		self.userlist.up()

	def down(self):
		self.userlist.down()

	def left(self):
		self.userlist.pageUp()

	def right(self):
		self.userlist.pageDown()

	def close(self, loginState=LOGIN_CANCEL):
		youTubeUserConfig.setAsDefault(self.defaultUser)
		Screen.close(self, loginState)

	def ok(self):
		try:
			if self.userlist.getSelection().login():
				self.close(YouTubeUserListScreen.LOGIN_SUCCESS)
			else:
				self.close(YouTubeUserListScreen.LOGIN_FAILED)
		except:
			self.close(YouTubeUserListScreen.LOGIN_FAILED)
