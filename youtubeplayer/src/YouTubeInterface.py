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

import gdata.youtube
import gdata.youtube.service

from gdata.service import BadAuthentication

from Tools.LoadPixmap import LoadPixmap

from twisted.web.client import downloadPage

from urllib2 import urlopen, Request, URLError, HTTPError
#, quote, unquote, unquote_plus
from urllib import quote, unquote_plus, unquote

from httplib import HTTPConnection, HTTPException

from urlparse import parse_qs

from socket import gaierror, error

import os
import re

# http://code.google.com/apis/youtube/reference.html#youtube_data_api_tag_media:group

std_headers = {
	'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
	'Accept-Language': 'en-us,en;q=0.5',
}


class YouTubeUser():
	def __init__(self, cfg):
		self.cfg = cfg

	def getCfg(self):
		return self.cfg

	def getName(self):
		return self.cfg.name.value

	def name(self):
		return self.cfg.name

	def getEmail(self):
		return self.cfg.email.value

	def email(self):
		return self.cfg.email

	def getPassword(self):
		return self.cfg.password.value

	def password(self):
		return self.cfg.password

	def login(self):
		return interface.login(self)


class YouTubeFeed():
	def __init__(self, feed, favoritesFeed=False):
		print "[YTB] YouTubeFeed::__init__()"
		self.feed = feed
		self.favoritesFeed = favoritesFeed
		self.entries = []
		self.update()

	def update(self):
		print "[YTB] YouTubeFeed::update()"
		sequenceNumber = int(self.feed.start_index.text)
		print self.feed.entry
		for entry in self.feed.entry:
			self.entries.append(YouTubeEntry(self, entry, sequenceNumber, self.favoritesFeed))
			sequenceNumber = sequenceNumber + 1

	def getTitle(self):
		return self.feed.title.text

	def getEntries(self):
		print "[YTB] YouTubeFeed::getEntries()"
		return self.entries

	def itemCount(self):
		print "[YTB] YouTubeFeed::itemCount()"
		return self.feed.items_per_page.text

	def getTotalResults(self):
		return self.feed.total_results.text

	def getNextFeed(self):
		print "[YTB] YouTubeFeed::getNextFeed()"
		for link in self.feed.link:
			if link.rel == "next":
				return link.href
		return None

	def getPreviousFeed(self):
		print "[YTB] YouTubeFeed::getPreviousFeed()"
		for link in self.feed.link:
			if link.rel == "previous":
				return link.href
		return None

	def getSelfFeed(self):
		print "[YTB] YouTubeFeed::getSelfFeed()"
		for link in self.feed.link:
			if link.rel == "self":
				return link.href
		return None

	def loadThumbnails(self, callback):
		print "[YTB] YouTubeFeed::loadThumbnails()"
		for entry in self.entries:
			entry.loadThumbnails(callback)


class YouTubeEntry():
	def __init__(self, feed, entry, sequenceNumber, favoritesFeed=False):
		print "[YTB] YouTubeEntry::__init__()"
		self.feed = feed
		self.entry = entry
		self.sequenceNumber = sequenceNumber
		self.favoritesFeed = favoritesFeed
		self.thumbnail = {}

	def isPlaylistEntry(self):
		return False

	def getYouTubeId(self):
		print "[YTB] YouTubeEntry::getYouTubeId()"
		ret = None
		if self.entry.media.player:
			split = self.entry.media.player.url.split("=")
			ret = split.pop()
			if ret == 'youtube_gdata':
				tmpval = split.pop()
				if tmpval.endswith("&feature"):
					tmp = tmpval.split("&")
					ret = tmp.pop(0)
		return ret

	def getTitle(self):
		print "[YTB] YouTubeEntry::getTitle()"
		return self.entry.media.title.text

	def getDescription(self):
		print "[YTB] YouTubeEntry::getDescription()"
		return self.entry.media.description.text

	def getThumbnailUrl(self, index):
		print "[YTB] YouTubeEntry::getThumbnailUrl"
		if index < len(self.entry.media.thumbnail):
			return self.entry.media.thumbnail[index].url
		return None

	def getRelatedFeed(self):
		print "[YTB] YouTubeEntry::getRelatedFeed()"
		for link in self.entry.link:
			print "Related link: ", link.rel.endswith
			if link.rel.endswith("video.related"):
				print "Found Related: ", link.href
				return link.href

	def getResponsesFeed(self):
		print "[YTB] YouTubeEntry::getResponseFeed()"
		for link in self.entry.link:
			print "Responses link: ", link.rel.endswith
			if link.rel.endswith("video.responses"):
				print "Found Responses: ", link.href
				return link.href

	def loadThumbnail(self, index, callback):
		print "[YTB] YouTubeEntry::loadThumbnail()"
		thumbnailUrl = self.getThumbnailUrl(index)
		if thumbnailUrl is not None and self.getYouTubeId() is not None:
			thumbnailFile = "/tmp/" + self.getYouTubeId() + "_" + str(index) + ".jpg"
			self.thumbnail[str(index)] = None
			cookie = {"entry": self, "file": thumbnailFile, "callback": callback, "index": index}
			downloadPage(thumbnailUrl, thumbnailFile).addCallback(fetchFinished, cookie).addErrback(fetchFailed, cookie)

	def loadThumbnails(self, callback):
		print "[YTB] YouTubeEntry::loadThumbnails()"
		self.loadThumbnail(0, callback)

	def verify_url(self, url):
		try:
			request = Request(url, None, std_headers)
			data = urlopen(request)
			data.read(1)
			url = data.geturl()
			data.close()
		except (OSError, IOError, URLError, HTTPException, error), err:
					return None
		else:
			return url

	def getVideoUrl(self, fmt):
		video_id = str(self.getYouTubeId())
		if video_id is None:
			return None #, no video_id
		for el_type in ['detailpage', 'embedded', 'vevo']:
			video_info_url = ('http://www.youtube.com/get_video_info?&video_id=%s&el=%s&ps=default&eurl=&gl=DE&hl=en' % (video_id, el_type))
			request = Request(video_info_url, None, std_headers)
			try:
				video_info_page = urlopen(request).read()
				video_info = parse_qs(video_info_page)
				if 'token' in video_info:
					break
			except (URLError, HTTPException, error), err:
				return None #, ('ERROR: unable to download video info webpage: %s' % str(err))
		if 'token' not in video_info:
			if 'reason' not in video_info:
				reason = 'Unable to extract "t" parameter for unknown reason'
			else:
				reason = unquote_plus(video_info['reason'][0])
			return None #, reason
		else:
			quality_fallback_dict = dict({"22": "18", "18": "6", "6": "1"})
			token = video_info['token'][0]
			while True:
				print "[YTB] Trying fmt=" + fmt
				video_real_url = 'http://www.youtube.com/get_video?video_id=%s&t=%s&eurl=&el=detailpage&ps=default&gl=US&hl=en&fmt=%s' % (video_id, token, fmt)
				video_real_url = self.verify_url(video_real_url)
				if video_real_url is None:
					if fmt == "1":
						print "[YTB] no valid fmt found"
						break
					else:
						print "[YTB] not found"
						fmt = quality_fallback_dict[fmt]
				else:
					print "[YTB] found"
					break
			return video_real_url #, 'OK'

	def getDuration(self):
		if self.entry.media is not None and self.entry.media.duration is not None:
			return self.entry.media.duration.seconds
		return "not available"

	def getRatingAverage(self):
		if self.entry.rating is not None:
			return self.entry.rating.average
		return "not available"

	def getNumRaters(self):
		if self.entry.rating is not None:
			return self.entry.rating.num_raters
		return ""

	def getRatingMax(self):
		if self.entry.rating is not None:
			return self.entry.rating.max
		return "not available"

	def getRatingMin(self):
		if self.entry.rating is not None:
			return self.entry.rating.min
		return "not available"

	def getFavoriteCount(self):
		if self.entry.statistics is not None:
			return self.entry.statistics.favorite_count
		return "not available"

	def getViewCount(self):
		if self.entry.statistics is not None:
			return self.entry.statistics.view_count
		return "not available"

	def getAuthor(self):
		authorList = []
		for author in self.entry.author:
			authorList.append(author.name.text)
		authors = ", ".join(authorList)
		return authors

	def getPublishedOn(self):
		if self.entry.published is not None:
			return self.entry.published.text
		return "unknown"

	def getCategory(self):
		return self.entry.GetYouTubeCategoryAsString()

	def getTags(self):
		if self.entry.media is not None and self.entry.media.keywords is not None:
			return self.entry.media.keywords.text
		return "not available"

	def belongsToFavorites(self):
		return self.favoritesFeed

	def belongsToPlaylistId(self):
		return self.playlistId


class YouTubePlaylistFeed():
	def __init__(self, feed):
		print "[YTB] YouTubePlayListFeed::__init__()"
		self.feed = feed
		self.entries = []
		self.update()

	def update(self):
		print "[YTB] YouTubePlayListFeed::update()"
		for entry in self.feed.entry:
			self.entries.append(YouTubePlaylistEntry(entry))

	def getTitle(self):
		print "[YTB] YouTubePlayListFeed::getTitle()"
		return self.feed.title.text

	def getEntries(self):
		print "[YTB] YouTubePlayListFeed::getEntries()"
		return self.entries


class YouTubePlaylistEntry():
	def __init__(self, entry):
		print "[YTB] YouTubePlaylistEntry::__init__()"
		self.entry = entry

	def getTitle(self):
		print "[YTB] YouTubePlaylistEntry::getTitle()"
		return self.entry.title.text

	def getDescription(self):
		print "[YTB] YouTubePlaylistEntry::getDescription()"
		return self.entry.description.text

	def getFeed(self, index=0):
		print "[YTB] YouTubePlaylistEntry::getFeed()"
		return self.entry.feed_link[index].href

	def getSelfFeed(self):
		print "[YTB] YouTubeFeed::getSelfFeed()"
		for link in self.entry.link:
			if link.rel == "self":
				return link.href
		return None


class YouTubePlaylistVideoFeed(YouTubeFeed):
	def __init__(self, feed):
		print "[YTB] YouTubePlaylistVideoFeed::__init__()"
		YouTubeFeed.__init__(self, feed)

	def update(self):
		print "[YTB] YouTubePlaylistVideoFeed::update()"
		sequenceNumber = 1
		print self.feed.entry
		for entry in self.feed.entry:
			self.entries.append(YouTubePlaylistVideoEntry(self, entry, sequenceNumber))
			sequenceNumber = sequenceNumber + 1

	def getFeed(self):
		print "[YTB] YouTubeFeed::getSelfFeed()"
		for link in self.feed.link:
			if link.rel == "feed":
				return link.href
		return None


class YouTubePlaylistVideoEntry(YouTubeEntry):
	def __init__(self, feed, entry, sequenceNumber):
		print "[YTB] YouTubePlaylistVideoEntry::__init__()"
		YouTubeEntry.__init__(self, feed, entry, sequenceNumber)

	def isPlaylistEntry(self):
		return True

	def getSelf(self):
		print "[YTB] YouTubePlaylistVideoEntry::getSelfFeed()"
		for link in self.entry.link:
			if link.rel == "self":
				return link.href
		return None

	YOUTUBE_DEVELOPER_TAG_SCHEME = "http://gdata.youtube.com/schemas/2007/developertags.cat"

	def getCategory(self):
		for category in self.entry.media.category:
			if category.scheme != YouTubePlaylistVideoEntry.YOUTUBE_DEVELOPER_TAG_SCHEME:
				return category.text
		return "not available"


class YouTubeInterface():
#	Do not change the client_id and developer_key in the login-section!
#	ClientId: ytapi-VolkerChristian-YouTubePlayer-pq3mrg1o-0
#	DeveloperKey: AI39si7t0WNyg_tvjBPdRIvBfaUA_XrTY1LNzfjLgCn8A_m92YKtWTcR_auEmI5gKGitJb4SskrjxJSmRc3yhQ4YlHTBAzPSig
	def __init__(self):
		print "[YTB] YouTubeInterface::__init__()"

	def open(self):
		self.ytService = gdata.youtube.service.YouTubeService()
		print "[YTB] YouTubeInterface::open()"
		self.loggedIn = False

	def close(self):
		print "[YTB] YouTubeInterface::close()"
		del self.ytService
		self.loggedIn = False

	def login(self, user):
		print "[YTB] YouTubeInterface::login()"
		ret = False
		if user is not None:
			# http://code.google.com/apis/youtube/developers_guide_python.html#ClientLogin
			self.ytService.email = user.getEmail()
			self.ytService.password = user.getPassword()
			self.ytService.source = 'my-example-application'
			self.ytService.developer_key = "AI39si7t0WNyg_tvjBPdRIvBfaUA_XrTY1LNzfjLgCn8A_m92YKtWTcR_auEmI5gKGitJb4SskrjxJSmRc3yhQ4YlHTBAzPSig"
			self.ytService.client_id = "ytapi-VolkerChristian-YouTubePlayer-pq3mrg1o-0"
			try:
				self.ytService.ProgrammaticLogin()
			except BadAuthentication:
				pass
			else:
				self.loggedIn = True
				ret = True
		return ret

	def isLoggedIn(self):
		return self.loggedIn

	def search(self, searchTerms, startIndex=1, maxResults=25,
					orderby="relevance", time="all_time", racy="include",
					author="", lr="", categories="", sortOrder="ascending", format="6"):
		print "[YTB] YouTubeInterface::search()"
		query = gdata.youtube.service.YouTubeVideoQuery()
		query.vq = searchTerms
		query.orderby = orderby
		query.racy = racy
		query.sortorder = sortOrder
		if lr is not None:
			query.lr = lr
		if categories[0] is not None:
			query.categories = categories
#		query.time = time
		query.start_index = startIndex
		query.max_results = maxResults
#		query.format = format
		try:
			feed = YouTubeFeed(self.ytService.YouTubeQuery(query))
		except gaierror:
			feed = None
		return feed

	def getFeed(self, url):
		return YouTubeFeed(self.ytService.GetYouTubeVideoFeed(url))

	def getUserFavoritesFeed(self, userName="default"):
		return YouTubeFeed(self.ytService.GetUserFavoritesFeed(userName), favoritesFeed=True)

	def getUserPlaylistFeed(self, playlistEntry):
		print "[YTB] getUserPlaylistFeed: ", playlistEntry.getFeed()
		return YouTubePlaylistVideoFeed(self.ytService.GetYouTubePlaylistVideoFeed(playlistEntry.getFeed()))

	def addToFavorites(self, entry):
		response = self.ytService.AddVideoEntryToFavorites(entry.entry)
		# The response, if succesfully posted is a YouTubeVideoEntry
		if isinstance(response, gdata.youtube.YouTubeVideoEntry):
			print "[YTB] Video successfully added to favorites"
			return response
		else:
			return None

	def removeFromFavorites(self, entry):
		response = self.ytService.DeleteVideoEntryFromFavorites(entry.getYouTubeId())
		if response is True:
			print "[YTB] Video deleted from favorites"
		return response

	def getPlaylistFeed(self):
		return YouTubePlaylistFeed(self.ytService.GetYouTubePlaylistFeed())

	def addPlaylist(self, name, description, private):
		newPlaylist = None
		newPlaylistEntry = self.ytService.AddPlaylist(name, description, private)
		if isinstance(newPlaylistEntry, gdata.youtube.YouTubePlaylistEntry):
  			newPlaylist = YouTubePlaylistEntry(newPlaylistEntry)
		return newPlaylist

	def deletePlaylist(self, playlistEntry):
		playListUrl = playlistEntry.getSelfFeed()
		return self.ytService.DeletePlaylist(playListUrl)

	def removeFromPlaylist(self, playlistVideoEntry):
		print "[YTB] Removing from Playlist"
		response = self.ytService.Delete(playlistVideoEntry.getSelf())
		if response:
			print "[YTB] Successfull deleted"
		else:
			print "[YTB] Delete unsuccessfull"
		return response

	def addToPlaylist(self, playlistEntry, videoEntry):
		print "[YTB] Adding to Playlist"
		playlistUri = playlistEntry.getFeed()
		response = self.ytService.AddPlaylistVideoEntryToPlaylist(
						playlistUri, videoEntry.getYouTubeId(), videoEntry.getTitle(), videoEntry.getDescription())
		if isinstance(response, gdata.youtube.YouTubePlaylistVideoEntry):
			print "[YTB] Video added"
			return response
		else:
			return None


def fetchFailed(string, cookie):
	print "[YTB] fetchFailed(): ", string
	if os.path.exists(cookie["file"]):
		os.remove(cookie["file"])
	cookie["callback"](cookie["entry"])


def fetchFinished(string, cookie):
	print "[YTB] fetchFinished(): ", string
	if os.path.exists(cookie["file"]):
		print "Loading filename %s" % cookie["file"]
		cookie["entry"].thumbnail[str(cookie["index"])] = LoadPixmap(cookie["file"])
		os.remove(cookie["file"])
	cookie["callback"](cookie["entry"])


interface = YouTubeInterface()
