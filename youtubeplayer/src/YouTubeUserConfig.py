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
from Components.ConfigList import ConfigListScreen
from Components.config import ConfigInteger
from Components.config import ConfigSelection
from Components.config import ConfigSubsection
from Components.config import ConfigSubList
from Components.config import ConfigText
from Components.config import config
from Components.config import getConfigListEntry
from Screens.Screen import Screen
from YouTubeInterface import YouTubeUser

from . import _

# This should be executed only once during an enigma2-session
config.plugins.youtubeplayer = ConfigSubsection()
config.plugins.youtubeplayer.serverprofile = ConfigText("", False)
#config.plugins.youtubeplayer.quality = ConfigSelection(
#				[
#				 ("", _("Low Quality (Mono)")),
#				 ("&fmt=6", _("Medium Quality (Mono)")),
#				 ("&fmt=18", _("High Quality (Stereo)")),
#				 ("&fmt=22", _("HD Quality (Stereo)"))
#				], "&fmt=18")
config.plugins.youtubeplayer.quality = ConfigSelection(
				[
				 ("1", _("Low Quality (Mono)")),
				 ("6", _("Medium Quality (Mono)")),
				 ("18", _("High Quality (Stereo)")),
				 ("22", _("HD Quality (Stereo)"))
				], "18")


class __YouTubeUserConfig():
	def __init__(self):
		self.userlist = []
		config.plugins.youtubeplayer.usercount = ConfigInteger(0)
		config.plugins.youtubeplayer.users = ConfigSubList()
		config.plugins.youtubeplayer.defaultuser = ConfigText("", False)
		for usernum in range(0, config.plugins.youtubeplayer.usercount.value):
			self.new()

	# Add a new server or load a configsection if existing

	def new(self):
		newUserConfigSubsection = ConfigSubsection()
		config.plugins.youtubeplayer.users.append(newUserConfigSubsection)
		newUserConfigSubsection.name = ConfigText("User " + str(self.__getUserCount()), False)
		if newUserConfigSubsection.name.value == newUserConfigSubsection.name.default:
			newUserConfigSubsection.name.default = ""
		newUserConfigSubsection.email = ConfigText("", False)
		newUserConfigSubsection.password = ConfigText("", False)
		
		newUser = YouTubeUser(newUserConfigSubsection)

		self.userlist.append(newUser)

		return newUser

	# Add was canceled or existing server should be removed
	def delete(self, user):
		config.plugins.youtubeplayer.users.remove(user.getCfg())
		self.userlist.remove(user)
		self.__save()

	# Edit or Add should complete
	def save(self, user):
		user.getCfg().save()
		self.__save()

	# Edit has been canceled
	def cancel(self, user):
		for element in user.getCfg().dict().values():
			element.cancel()

	def getUserlist(self):
		return self.userlist

	def getUserByName(self, name):
		for user in self.userlist:
			if user.getName() == name:
				return user
		return None

	def getDefaultUser(self):
		return self.getUserByName(config.plugins.youtubeplayer.defaultuser.value)

	def setAsDefault(self, defaultUser):
		if defaultUser is not None:
			config.plugins.youtubeplayer.defaultuser.value = defaultUser.getName()
			config.plugins.youtubeplayer.defaultuser.save()

	def __save(self):
		config.plugins.youtubeplayer.usercount.value = self.__getUserCount()
		config.plugins.youtubeplayer.usercount.save()

	def __getUserCount(self):
		return len(config.plugins.youtubeplayer.users)


youTubeUserConfig = __YouTubeUserConfig()


class YouTubeUserConfigScreen(Screen, ConfigListScreen):
	def __init__(self, session, user):
		Screen.__init__(self, session)
		self.user = user
		self["actions"] = ActionMap(["YouTubeUserConfigScreenActions"],
		{
			"save"		: self.keySave,
			"cancel"	: self.keyCancel
		}, -2)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Save"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		cfglist = []
		cfglist.append(getConfigListEntry(_("User Profile Name"), user.name()))
		cfglist.append(getConfigListEntry(_("E-Mail Address"), user.email()))
		cfglist.append(getConfigListEntry(_("Password"), user.password()))

		ConfigListScreen.__init__(self, cfglist, session)

	def keySave(self):
		self.close(True, self.user)

	def keyCancel(self):
		self.close(False, self.user)
