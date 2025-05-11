# -*- coding: utf-8 -*-
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

from __future__ import print_function
from __future__ import absolute_import
from .YouTubeInterface import interface

from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.SystemInfo import BoxInfo
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_TOP, RT_WRAP
from enigma import eTimer

from Tools.NumericalTextInput import NumericalTextInput

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Components.config import config

from Plugins.Extensions.VlcPlayer.VlcServerConfig import vlcServerConfig
from Plugins.Extensions.VlcPlayer.VlcServer import VlcServer
from Plugins.Extensions.VlcPlayer.VlcServerList import VlcServerListScreen

from .YouTubeContextMenu import YouTubeEntryContextMenu, YouTubeEntryContextMenuList

from Tools.BoundFunction import boundFunction

from .YouTubePlayer import YouTubePlayer
from .DirectYouTubePlayer import DirectYouTubePlayer

from .YouTubeUserConfig import youTubeUserConfig
from .YouTubeUserList import YouTubeUserListScreen
from .YouTubePlayList import YouTubePlaylistScreen

#from Screens.InfoBar import MoviePlayer
#from enigma import eServiceReference

from . import _


def YouTubeEntryComponent(entry):
	res = [entry]
# 385
	res.append(MultiContentEntryText(pos=(150, 5), size=(370, 42), font=0, flags=RT_HALIGN_LEFT | RT_VALIGN_TOP | RT_WRAP, text=entry.getTitle()))
	res.append(MultiContentEntryText(pos=(150, 46), size=(370, 56), font=1, color=0xFFA323, color_sel=0xFFA323, flags=RT_HALIGN_LEFT | RT_VALIGN_TOP | RT_WRAP, text=entry.getDescription()))

	if entry.thumbnail["0"] is None:
		png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/plugin.png"))
	else:
		png = entry.thumbnail["0"]
	res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 5), size=(130, 97), png=png))

	return res


class YouTubeVideoDetailsScreen(Screen):
	def __init__(self, session, entry):
		Screen.__init__(self, session)
		self.entry = entry
		self["video_description"] = ScrollLabel(entry.getDescription())
		durationInSecs = int(entry.getDuration())
		mins = int(durationInSecs / 60)
		secs = durationInSecs - mins * 60
		duration = "%d:%02d" % (mins, secs)

		self["label_video_duration"] = Label(_("Duration") + ":")
		self["video_duration"] = Label(duration)

		self["label_video_rating_average"] = Label(_("Rate") + ":")
		self["starsbg"] = Pixmap()
		self["stars"] = ProgressBar()

		self["label_video_numraters"] = Label(_("Ratings") + ":")
		self["video_numraters"] = Label(entry.getNumRaters())

		self["label_video_statistics_favorite_count"] = Label(_("Favorited") + ":")
		self["video_statistics_favorite_count"] = Label(entry.getFavoriteCount())

		self["label_video_statistics_view_count"] = Label(_("Views") + ":")
		self["video_statistics_view_count"] = Label(entry.getViewCount())

		self["label_video_author"] = Label(_("Author:") + ":")
		self["video_author"] = Label(entry.getAuthor())

		self["label_video_published_on"] = Label(_("Added") + ":")
		self["video_published_on"] = Label(entry.getPublishedOn().split("T")[0])

		self["label_video_category"] = Label(_("Category") + ":")
		self["video_category"] = Label(entry.getCategory())
		self["label_video_tags"] = Label(_("Tags") + ":")
		self["video_tags"] = Label(entry.getTags())

		self["video_thumbnail_1"] = Pixmap()
		self["video_thumbnail_2"] = Pixmap()
		self["video_thumbnail_3"] = Pixmap()

		self["actions"] = ActionMap(["YouTubeVideoDetailsScreenActions"],
		{
			"ok": self.close,
			"cancel": self.close,
			"up": self.pageUp,
			"down": self.pageDown,
			"left": self.pageUp,
			"right": self.pageDown
		})

		self.onFirstExecBegin.append(self.setPixmap)
		self.onFirstExecBegin.append(self.setInitialize)

	def pageUp(self):
		self["video_description"].pageUp()

	def pageDown(self):
		self["video_description"].pageDown()

	def setInitialize(self):
		Screen.setTitle(self, self.entry.getTitle())
		if self.entry.getRatingAverage() != "not available":
			ratingStars = int(round(20 * float(self.entry.getRatingAverage()), 0))
			print("[YTB] Rating: ", ratingStars, "    ", self["stars"].getRange())
			self["stars"].setValue(ratingStars)
		else:
			self["stars"].hide()
			self["starsbg"].hide()

	def setPixmap(self):
		self["video_thumbnail_1"].instance.setPixmap(self.entry.thumbnail["0"])
		self.entry.loadThumbnail(1, self.setThumbnail_2)
		self.entry.loadThumbnail(2, self.setThumbnail_3)
		self["video_thumbnail_2"].hide()
		self["video_thumbnail_3"].hide()

	def setThumbnail_2(self, entry):
		self["video_thumbnail_2"].instance.setPixmap(self.entry.thumbnail["1"])
		self["video_thumbnail_2"].show()

	def setThumbnail_3(self, entry):
		self["video_thumbnail_3"].instance.setPixmap(self.entry.thumbnail["2"])
		self["video_thumbnail_3"].show()


class PatientMessageBox(MessageBox):
	def __init__(self, session, text, type=1, timeout=-1, close_on_any_key=False, default=True):
		MessageBox.__init__(self, session, text, type, timeout, close_on_any_key, default)
		self.skinName = "MessageBox"

	def processDelayed(self, function):
		self.delay_timer = eTimer()
		self.delay_timer.callback.append(self.processDelay)
		self.delay_timer.start(0, 1)
		self.function = function

	def processDelay(self):
		self.function()

	def cancel(self):
		pass

	def ok(self):
		pass

	def alwaysOK(self):
		pass


class YouTubeList(MenuList):
	def __init__(self, list, enableWrapAround=False):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 18))
		self.l.setFont(1, gFont("Regular", 14))
		self.l.setItemHeight(105)


class YouTubeListScreen(Screen, NumericalTextInput):
	def __init__(self, session):
		Screen.__init__(self, session)
		NumericalTextInput.__init__(self)

		self.session = session
		self.serverName = config.plugins.youtubeplayer.serverprofile.value
		self.currentServer = vlcServerConfig.getServerByName(self.serverName)

		self["red"] = Label(_("Select a VLC-Server"))
		self["green"] = Label(_("New YouTube search"))

		self.list = []
		self["list"] = YouTubeList(self.list)

		self["label_total_results"] = Label(_("Total results") + ":")
		self["total_results"] = Label("")

		self["label_currently_shown"] = Label(_("Shown") + ":")
		self["currently_shown"] = Label("")

		self.history = []
		self.historyIndex = 0

		self.isFavoritesFeed = False

		self.patientDialog = None

		self["actions"] = ActionMap(["YouTubeVideoListActions"],
		{
			"play": self.tryToPlay,
			"select": self.justSelectServer,
			"search": self.searchAgain,
			"menu": self.openContextMenu,
			"forward": self.forwardInHistory,
			"backward": self.backInHistory,
			"left": self.keyLeft,
			"right": self.keyRight,
			"up": self.keyUp,
			"down": self.keyDown,
			"info": self.showVideoInfo,
			"cancel": self.close
		}, -1)

	def keyLeft(self):
		self["list"].pageUp()

	def keyRight(self):
		if self["list"].getSelectionIndex() == len(self.list) - 1 and self.feed.getNextFeed() is not None:
			dlg = self.session.openWithCallback(self.loadNextFeed, MessageBox, _("Load further entries of current Feed?"))
		else:
			self["list"].pageDown()

	def keyUp(self):
		self["list"].up()

	def keyDown(self):
		if self["list"].getSelectionIndex() == len(self.list) - 1 and self.feed.getNextFeed() is not None:
			dlg = self.session.openWithCallback(self.loadNextFeed, MessageBox, _("Load further entries of current Feed?"))
		else:
			self["list"].down()

	def insertEntry(self, entry):
		print("[YTB] YouTubeTest::updateFinished()")
		self.list.append(YouTubeEntryComponent(entry))
		self.list.sort(cmp=lambda x, y: cmp(x[0].sequenceNumber, y[0].sequenceNumber))
		currentlyShown = "%d" % len(self.list)
		self["currently_shown"].setText(currentlyShown)
		self["list"].setList(self.list)

	def closePatientDialogDelayed(self):
		if self.patientDialog:
			self.patientDialog.close()
			self.patientDialog = None
		self["list"].setList(self.list)

	def showFeed(self, feed, append):
		if feed is not None:
			self.feed = feed
			self.setTitle(feed.getTitle())
			self["total_results"].setText(feed.getTotalResults())
			if not append:
				self.list = []
				self["list"].setList(self.list)
			self.feed.loadThumbnails(self.insertEntry)
		self.delay_timer = eTimer()
		self.delay_timer.callback.append(self.closePatientDialogDelayed)
		self.delay_timer.start(100, 1)

	def addToHistory(self, feed):
		if feed is not None:
			del self.history[self.historyIndex: len(self.history)]
			self.history.insert(self.historyIndex, feed.getSelfFeed())
			self.historyIndex = self.historyIndex + 1

	def searchFeedReal(self, searchContext):
		print("[YTB] searchFeedReal")
		try:
			feed = interface.search(searchContext.searchTerm.value,
					orderby=searchContext.orderBy.value,
					racy=searchContext.racy.value,
					time=searchContext.time.value,
					lr=searchContext.lr.value,
					categories=[searchContext.categories.value],
					sortOrder=searchContext.sortOrder.value,
					format=config.plugins.youtubeplayer.quality)
		except Exception as e:
			feed = None
			self.session.open(MessageBox, _("Error querying feed for search term %s:\n%s" %
					(searchContext.searchTerm.value, e)), MessageBox.TYPE_ERROR)
		self.showFeed(feed, False)
		self.addToHistory(feed)

	def searchFeed(self, searchContext):
		self.patientDialog = self.session.open(PatientMessageBox, _("Searching, be patient ..."))
		self.patientDialog.processDelayed(boundFunction(self.searchFeedReal, searchContext=searchContext))
		self.isFavoritesFeed = False

	def loadPlaylistFeedReal(self, playlist):
		try:
			feed = interface.getUserPlaylistFeed(playlist)
		except Exception as e:
			feed = None
			self.session.open(MessageBox, _("Error querying playlist-feed for playlist %s:\n%s" %
					(playlist.getTitle(), e)), MessageBox.TYPE_ERROR)
		self.showFeed(feed, False)
		self.addToHistory(feed)

	def loadPlaylistFeed(self, playlist):
		self.patientDialog = self.session.open(PatientMessageBox, _("Loading playlist, be patient ..."))
		self.patientDialog.processDelayed(boundFunction(self.loadPlaylistFeedReal, playlist=playlist))

	def loadFavoritesFeedReal(self, userName="default"):
		try:
			feed = interface.getUserFavoritesFeed(userName)
		except Exception as e:
			feed = None
			self.session.open(MessageBox, _("Error querying favorites feed:\n%s" %
					e), MessageBox.TYPE_ERROR)
		self.showFeed(feed, False)
		self.addToHistory(feed)

	def loadFavoritesFeed(self, userName="default"):
		self.patientDialog = self.session.open(PatientMessageBox, _("Loading favorits, be patient ..."))
		self.patientDialog.processDelayed(boundFunction(self.loadFavoritesFeedReal, userName=userName))
		self.isFavoritesFeed = True

	def loadStandardFeed(self, url):
		self.loadFeed(_("Loading standard feed, be patient ..."), url, "standard feed")

	def loadFeedReal(self, feedUrl, feedName, append=False, addToHistory=True):
		try:
			feed = interface.getFeed(feedUrl)
		except Exception as e:
			feed = None
			self.session.open(MessageBox, _("Error querying feed %s:\n%s" %
					(feedName, e)), MessageBox.TYPE_ERROR)
		self.showFeed(feed, append)
		if addToHistory:
			self.addToHistory(feed)

	def loadFeed(self, text, feedUrl, feedName, append=False, addToHistory=True):
		self.patientDialog = self.session.open(PatientMessageBox, text)
		self.patientDialog.processDelayed(boundFunction(self.loadFeedReal, feedName=feedName,
											feedUrl=feedUrl, append=append, addToHistory=addToHistory))

	def loadPreviousFeed(self, result):
		if not result:
			return
		prevUrl = self.feed.getPreviousFeed()
		if prevUrl is not None:
			self.loadFeed(_("Loading additional videos, be patient ..."), prevUrl, _("additional videos"),
			True, True)

	def loadNextFeed(self, result):
		if not result:
			return
		nextUrl = self.feed.getNextFeed()
		if nextUrl is not None:
			self.loadFeed(_("Loading additional videos, be patient ..."), nextUrl, _("additional videos"),
			True, True)

	def getRelated(self):
		self.loadFeed(_("Loading related videos, be patient ..."), self["list"].getCurrent()[0].getRelatedFeed(), _("related videos"), False, True)
		self.isFavoritesFeed = False

	def getResponses(self):
		self.loadFeed(_("Loading response videos, be patient ..."), self["list"].getCurrent()[0].getResponsesFeed(), _("response videos"), False, True)
		self.isFavoritesFeed = False

	def processDelayed(self, function):
		self.delay_timer = eTimer()
		self.delay_timer.callback.append(self.processDelay)
		self.delay_timer.start(0, 1)
		self.function = function

	def processDelay(self):
		self.function()

	def getRelatedDelayed(self):
		self.processDelayed(self.getRelated)

	def getResponsesDelayed(self):
		self.processDelayed(self.getResponses)

	def backInHistory(self):
		if self.historyIndex > 1:
			self.historyIndex = self.historyIndex - 1
			self.loadFeed(_("Back in history, be patient ..."), self.history[self.historyIndex - 1], _("back in history"), False, False)

	def forwardInHistory(self):
		if self.historyIndex < len(self.history):
			self.historyIndex = self.historyIndex + 1
			self.loadFeed(_("Forward in history, be patient ..."), self.history[self.historyIndex - 1], _("forward in history"), False, False)

	def showVideoInfo(self):
		self.session.open(YouTubeVideoDetailsScreen, self["list"].getCurrent()[0])

	def justSelectServer(self):
		defaultServer = vlcServerConfig.getServerByName(config.plugins.youtubeplayer.serverprofile.value)
		self.selectServer(self.serverSelectedCB, defaultServer)

	def selectServer(self, callback, currentServer):
		self.session.openWithCallback(callback, VlcServerListScreen, currentServer)

	def serverSelectedCB(self, selectedServer, defaultServer):
		if selectedServer is not None:
			self.currentServer = selectedServer
		elif defaultServer is not None:
				self.currentServer = defaultServer
		if defaultServer is not None:
			config.plugins.youtubeplayer.serverprofile.value = defaultServer.getName()
			config.plugins.youtubeplayer.serverprofile.save()

	def selectAndPlayCB(self, selectedServer, defaultServer):
		self.serverSelectedCB(selectedServer, defaultServer)
		self.tryToPlay()

	def login(self, callback):
		self.session.openWithCallback(callback, YouTubeUserListScreen, youTubeUserConfig.getDefaultUser())

	def addToFavoritesReal(self):
		try:
			interface.addToFavorites(self["list"].getCurrent()[0])
		except Exception as e:
			self.session.open(MessageBox, _("Error adding video to favorites:\n%s" %
					e), MessageBox.TYPE_ERROR)

	def addToFavoritesLogin(self, loginState):
		if loginState == YouTubeUserListScreen.LOGIN_SUCCESS:
			self.addToFavoritesReal()
		elif loginState == YouTubeUserListScreen.LOGIN_FAILED:
			self.session.open(MessageBox, _("Login not successful"), MessageBox.TYPE_INFO)
		else:
			pass

	def addToFavorites(self):
		if not interface.isLoggedIn():
			self.login(self.addToFavoritesLogin)
		else:
			self.addToFavoritesReal()

	def removeFromFavoritesReal(self):
		try:
			if interface.removeFromFavorites(self["list"].getCurrent()[0]):
				self.list.remove(self["list"].getCurrent())
				self["list"].setList(self.list)
		except Exception as e:
			self.session.open(MessageBox, _("Error removing video from favorites:\n%s" %
					e), MessageBox.TYPE_ERROR)

	def removeFromFavoritesLogin(self, loginState):
		if loginState == YouTubeUserListScreen.LOGIN_SUCCESS:
			self.removeFromFavoritesReal()
		elif loginState == YouTubeUserListScreen.LOGIN_FAILED:
			self.session.open(MessageBox, _("Login not successful"), MessageBox.TYPE_INFO)
		else:
			pass

	def removeFromFavorites(self):
		if not interface.isLoggedIn():
			self.login(self.removeFromFavoritesLogin)
		else:
			self.removeFromFavoritesReal()

	def removeFromPlaylistReal(self):
		try:
			if interface.removeFromPlaylist(self["list"].getCurrent()[0]):
				self.list.remove(self["list"].getCurrent())
				self["list"].setList(self.list)
		except Exception as e:
			self.session.open(MessageBox, _("Error removing video from playlist:\n%s" %
					e), MessageBox.TYPE_ERROR)

	def removeFromPlaylistLogin(self, loginState):
		if loginState == YouTubeUserListScreen.LOGIN_SUCCESS:
			self.removeFromPlaylistReal()
		elif loginState == YouTubeUserListScreen.LOGIN_FAILED:
			self.session.open(MessageBox, _("Login not successful"), MessageBox.TYPE_INFO)
		else:
			pass

	def removeFromPlaylist(self):
		if not interface.isLoggedIn():
			self.login(self.removeFromPlaylistLogin)
		else:
			self.removeFromPlaylistReal()

	def playlistChoosen(self, playlist):
		if playlist is not None:
			try:
				interface.addToPlaylist(playlist, self["list"].getCurrent()[0])
			except Exception as e:
				self.session.open(MessageBox, _("Error adding video to playlist:\n%s" %
					e), MessageBox.TYPE_ERROR)

	def addToPlaylistReal(self):
		dlg = self.session.openWithCallback(self.playlistChoosen, YouTubePlaylistScreen)
		dlg.loadPlaylist()

	def addToPlaylistLogin(self, loginState):
		if loginState == YouTubeUserListScreen.LOGIN_SUCCESS:
			self.addToPlaylistReal()
		elif loginState == YouTubeUserListScreen.LOGIN_FAILED:
			self.session.open(MessageBox, _("Login not successful"), MessageBox.TYPE_INFO)
		else:
			pass

	def addToPlaylist(self):
		if not interface.isLoggedIn():
			self.login(self.addToPlaylistLogin)
		else:
			self.addToPlaylistReal()

	def getVideoUrl(self, youTubeEntry, fmt):
		mrl = youTubeEntry.getVideoUrl(fmt)
		if mrl is None:
			self.session.open(MessageBox, _("Could not retrive video url for:\n%s") % youTubeEntry.getTubeId(), MessageBox.TYPE_ERROR)
		return mrl

	def tryToPlay(self):
		if BoxInfo.getItem("model") in ("dm8000", "dm800"):
			self.playDirect()
		else:
			if self.currentServer is not None:
				self.play()
			else:
				self.selectServer(self.selectAndPlayCB, None)


# http://cacan.blog385.com/index.php/2008/05/09/youtube-high-quality-hacks/
# add the &fmt=6 onto the end:
#
# http://youtube.com/watch?v=CQzUsTFqtW0&fmt=6
#
# If the YouTube video just sits there loading then that
# is a sign that the video has not been converted to the
# higher resolution yet. To really see the difference you
# should view the video in full screen mode by clicking
# the button in the bottom-right corner of the player.
#
# Note: Alternatively you can add &fmt=18 and it will play
# the high-resolution version when available, otherwise it
# will play the regular version. Here?s a Greasemonkey
# script that will automatically add &fmt=18 onto the end
# of each YouTube URL.

	def play(self):
		print("[YTB] Play()")
		youTubeEntry = self["list"].getCurrent()[0]
		mrl = self.getVideoUrl(youTubeEntry, config.plugins.youtubeplayer.quality.value)
		if mrl is not None:
			entries = []
			entries.append((_("Show video detail info"), [self.showVideoInfo, False]))
			if self["list"].getCurrent()[0].belongsToFavorites():
				entries.append((_("Remove from favorites"), [self.removeFromFavorites, False]))
			else:
				entries.append((_("Add to favorites"), [self.addToFavorites, False]))

			if self["list"].getCurrent()[0].isPlaylistEntry():
				entries.append((_("Remove from playlist"), [self.removeFromPlaylist, False]))
			else:
				entries.append((_("Add to playlist"), [self.addToPlaylist, False]))
			entries.append((_("Get related videos"), [self.getRelatedDelayed, True]))
			entries.append((_("Get video responses"), [self.getResponsesDelayed, True]))

			self.currentServer.play(self.session, mrl, youTubeEntry.getTitle(), self,
								player=boundFunction(YouTubePlayer, contextMenuEntries=entries, infoCallback=self.showVideoInfo, name=self["list"].getCurrent()[0].getTitle()))
		else:
			print("[YTB] No valid flv-mrl found")

	def playDirect(self):
		print("[YTB] PlayDirect()")
		youTubeEntry = self["list"].getCurrent()[0]
		mrl = self.getVideoUrl(youTubeEntry, config.plugins.youtubeplayer.quality.value)
		if mrl is not None:
			entries = []
			entries.append((_("Show video detail info"), [self.showVideoInfo, False]))
			if self["list"].getCurrent()[0].belongsToFavorites():
				entries.append((_("Remove from favorites"), [self.removeFromFavorites, False]))
			else:
				entries.append((_("Add to favorites"), [self.addToFavorites, False]))

			if self["list"].getCurrent()[0].isPlaylistEntry():
				entries.append((_("Remove from playlist"), [self.removeFromPlaylist, False]))
			else:
				entries.append((_("Add to playlist"), [self.addToPlaylist, False]))
			entries.append((_("Get related videos"), [self.getRelatedDelayed, True]))
			entries.append((_("Get video responses"), [self.getResponsesDelayed, True]))

#			self.session.open(MoviePlayer, eServiceReference(4097, 0, mrl))

			self.session.open(DirectYouTubePlayer, mrl, youTubeEntry.getTitle(), self, contextMenuEntries=entries, infoCallback=self.showVideoInfo, name=self["list"].getCurrent()[0].getTitle())
		else:
			print("[YTB] No valid flv-mrl found")

	def getNextFile(self):
		i = self["list"].getSelectedIndex() + 1
		if i < len(self.list):
			self["list"].moveToIndex(i)
			youTubeEntry = self["list"].getCurrent()[0]
			return self.getVideoUrl(youTubeEntry, config.plugins.youtubeplayer.quality.value), youTubeEntry.getTitle()
		return None, None

	def getPrevFile(self):
		i = self["list"].getSelectedIndex() - 1
		if i >= 0:
			self["list"].moveToIndex(i)
			youTubeEntry = self["list"].getCurrent()[0]
			return self.getVideoUrl(youTubeEntry, config.plugins.youtubeplayer.quality.value), youTubeEntry.getTitle()
		return None, None

	def openContextMenu(self):
		contextMenuList = YouTubeEntryContextMenuList()
		contextMenuList.appendEntry((_("Show video detail info"), self.showVideoInfo))
		if self["list"].getCurrent()[0].belongsToFavorites():
			contextMenuList.appendEntry((_("Remove from favorites"), self.removeFromFavorites))
		else:
			contextMenuList.appendEntry((_("Add to favorites"), self.addToFavorites))
		if self["list"].getCurrent()[0].isPlaylistEntry():
			contextMenuList.appendEntry((_("Remove from playlist"), self.removeFromPlaylist))
		else:
			contextMenuList.appendEntry((_("Add to playlist"), self.addToPlaylist))
		contextMenuList.appendEntry((_("Get related videos"), self.getRelated))
		contextMenuList.appendEntry((_("Get video responses"), self.getResponses))
		self.session.openWithCallback(self.menuActionCoosen, YouTubeEntryContextMenu, contextMenuList, self["list"].getCurrent()[0].getTitle())

	def menuActionCoosen(self, function):
		if function is not None:
			function()

	def searchAgain(self):
		Screen.close(self, True)

	def close(self):
		Screen.close(self, False)
