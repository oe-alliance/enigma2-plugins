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

from Plugins.Plugin import PluginDescriptor

from YouTubeList import YouTubeListScreen
from YouTubePlayList import YouTubePlaylistScreen
from YouTubeSearchDialog import YouTubeSearchDialog, SEARCH, STDFEEDS, PLAYLISTS, FAVORITES, CANCEL
from YouTubeUserList import YouTubeUserListScreen
from YouTubeUserConfig import youTubeUserConfig
from YouTubeStdFeedSelection import YouTubeStdFeedSelectionScreen
from YouTubeInterface import interface, YouTubeInterface
from SkinLoader import loadPluginSkin
from Screens.MessageBox import MessageBox

import os, gettext


def _(txt):
	t = gettext.dgettext("YouTube", txt)
	if t == txt:
		print "[YTB] fallback to default translation for", txt
		t = gettext.gettext(txt)
	return t


class YouTubeManager():
	def __init__(self, session):
		self.session = session
		interface.open()


	def openSearchDialog(self):
		self.session.openWithCallback(self.searchDialogClosed, YouTubeSearchDialog)


	def searchDialogClosed(self, what, searchContext = None):
		print "[YTB] searchDialogClosed: ", what
		if what == SEARCH:
			dlg = self.session.openWithCallback(self.youTubeListScreenClosed, YouTubeListScreen)
			dlg.searchFeed(searchContext)
		elif what == CANCEL:
			interface.close()
		elif what == STDFEEDS:
			self.openStandardFeeds()
		else:
			if what == PLAYLISTS:
				callback = self.openPlaylists
			elif what == FAVORITES:
				callback = self.openFavorites
			if not interface.isLoggedIn():
				self.session.openWithCallback(callback, YouTubeUserListScreen, youTubeUserConfig.getDefaultUser())
			else:
				callback(YouTubeUserListScreen.LOGIN_SUCCESS)


	def openStandardFeeds(self):
		self.session.openWithCallback(self.standardFeedSelected, YouTubeStdFeedSelectionScreen)


	def standardFeedSelected(self, stdFeedUrl):
		if stdFeedUrl is not None:
			dlg = self.session.openWithCallback(self.youTubeListScreenClosed, YouTubeListScreen)
			dlg.loadStandardFeed(stdFeedUrl)
		else:
			self.openSearchDialog()


	def openPlaylists(self, loginState):
		if loginState == YouTubeUserListScreen.LOGIN_SUCCESS:
			print "[YTB] logged in"
			dlg = self.session.openWithCallback(self.playlistChoosen, YouTubePlaylistScreen)
			dlg.loadPlaylist()
		elif loginState == YouTubeUserListScreen.LOGIN_FAILED:
			print "[YTB] not logged in"
			self.session.openWithCallback(self.backToSearchDialog, MessageBox, _("Login not successful"), MessageBox.TYPE_INFO)
		else:
			self.backToSearchDialog()


	def playlistChoosen(self, playlist):
		if playlist is not None:
			dlg = self.session.openWithCallback(self.youTubeListScreenClosed, YouTubeListScreen)
			dlg.loadPlaylistFeed(playlist)
		else:
			self.openSearchDialog()


	def openFavorites(self, loginState):
		if loginState == YouTubeUserListScreen.LOGIN_SUCCESS:
			print "[YTB] logged in"
			dlg = self.session.openWithCallback(self.youTubeListScreenClosed, YouTubeListScreen)
			dlg.loadFavoritesFeed("default")
		elif loginState == YouTubeUserListScreen.LOGIN_FAILED:
			print "[YTB] not logged in"
			self.session.openWithCallback(self.backToSearchDialog, MessageBox, _("Login not successful"), MessageBox.TYPE_INFO)
		else:
			self.backToSearchDialog()


	def backToSearchDialog(self, dummy = True):
		self.openSearchDialog()


	def youTubeListScreenClosed(self, proceed):
		if proceed:
			self.openSearchDialog()
		else:
			interface.close()


def main(session, **kwargs):
	try:
		youTubeManager = YouTubeManager(session)
	except Exception, e:
		session.open(MessageBox, _("Error contacting YouTube:\n%s" % e), MessageBox.TYPE_ERROR)
	else:
		youTubeManager.openSearchDialog()


def Plugins(**kwargs):
	loadPluginSkin(kwargs["path"])
	return PluginDescriptor(
		name="YouTube Player",
		description=_("Search and play YouTube movies"),
		where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
		icon = "plugin.png", fnc = main)
