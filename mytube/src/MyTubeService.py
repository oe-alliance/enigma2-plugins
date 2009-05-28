# -*- coding: iso-8859-1 -*-
from __init__ import _
import gdata.youtube
import gdata.youtube.service
from gdata.service import BadAuthentication
from Tools.LoadPixmap import LoadPixmap
from Components.config import config, Config, ConfigSelection, ConfigText, getConfigListEntry, ConfigSubsection, ConfigYesNo, ConfigIP, ConfigNumber
from Components.ConfigList import ConfigListScreen
from Components.config import KEY_DELETE, KEY_BACKSPACE, KEY_LEFT, KEY_RIGHT, KEY_HOME, KEY_END, KEY_TOGGLEOW, KEY_ASCII, KEY_TIMEOUT

from twisted.web import client
from twisted.internet import reactor
from urllib2 import Request, URLError, HTTPError
from socket import gaierror,error
import re, os, sys, socket
import urllib
from urllib import FancyURLopener, quote
import cookielib
from httplib import HTTPConnection,CannotSendRequest,BadStatusLine
HTTPConnection.debuglevel = 1

#config.plugins.mytube = ConfigSubsection()
#config.plugins.mytube.general = ConfigSubsection()
#config.plugins.mytube.general.useHTTPProxy = ConfigYesNo(default = False)
#config.plugins.mytube.general.ProxyIP = ConfigIP(default=[0,0,0,0])
#config.plugins.mytube.general.ProxyPort = ConfigNumber(default=8080)

class MyOpener(FancyURLopener):
	version = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12'


class GoogleSuggestions():
	def __init__(self, callback, ds = None, json = None, hl = None):
		self.callback = callback
		self.conn = HTTPConnection("google.com")
		self.prepQuerry = "/complete/search?"
		if ds is not None:
			self.prepQuerry = self.prepQuerry + "ds=" + ds + "&"
		if json is not None:
			self.prepQuerry = self.prepQuerry + "json=" + json + "&"
		if hl is not None:
			self.prepQuerry = self.prepQuerry + "hl=" + hl + "&"
		self.prepQuerry = self.prepQuerry + "jsonp=self.gotSuggestions&q="

	def gotSuggestions(self, suggestslist):
		self.callback(suggestslist)

	def getSuggestions(self, querryString):
		if querryString is not "":
			querry = self.prepQuerry + quote(querryString)
			try:
				self.conn.request("GET", querry)
			except (CannotSendRequest, gaierror, error):
				print "[YTB] Can not send request for suggestions"
				self.callback(None)
			else:
				try:
					response = self.conn.getresponse()
				except BadStatusLine:
					print "[YTB] Can not get a response from google"
					self.callback(None)
				else:
					if response.status == 200:
						data = response.read()
						exec data
					else:
						self.callback(None)
			self.conn.close()
		else:
			self.callback(None)


class MyTubeFeedEntry():
	def __init__(self, feed, entry, favoritesFeed = False):
		self.feed = feed
		self.entry = entry
		self.favoritesFeed = favoritesFeed
		self.thumbnail = {}
		self.myopener = MyOpener()
		urllib.urlopen = MyOpener().open
		"""if config.plugins.mytube.general.useHTTPProxy.value is True:
			proxy = {'http': 'http://'+str(config.plugins.mytube.general.ProxyIP.getText())+':'+str(config.plugins.mytube.general.ProxyPort.value)}
			self.myopener = MyOpener(proxies=proxy)
			urllib.urlopen = MyOpener(proxies=proxy).open
		else:
			self.myopener = MyOpener()
			urllib.urlopen = MyOpener().open"""
		
	def isPlaylistEntry(self):
		return False

	def getTubeId(self):
		#print "[MyTubeFeedEntry] getTubeId"
		ret = None
		if self.entry.media.player:
			ret = self.entry.media.player.url.split("=").pop()
		return ret

	def getTitle(self):
		#print "[MyTubeFeedEntry] getTitle",self.entry.media.title.text
		return self.entry.media.title.text

	def getDescription(self):
		#print "[MyTubeFeedEntry] getDescription"
		if self.entry.media is not None and self.entry.media.description is not None:
			return self.entry.media.description.text
		return "not vailable"

	def getThumbnailUrl(self, index = 0):
		#print "[MyTubeFeedEntry] getThumbnailUrl"
		if index < len(self.entry.media.thumbnail):
			return self.entry.media.thumbnail[index].url
		return None

	def getPublishedDate(self):
		if self.entry.published is not None:
			return self.entry.published.text
		return "unknown"

	def getViews(self):
		if self.entry.statistics is not None:
			return self.entry.statistics.view_count
		return "not available"
	
	def getDuration(self):
		if self.entry.media is not None and self.entry.media.duration is not None:
			return self.entry.media.duration.seconds
		else:
			return 0

	def getRatingAverage(self):
		if self.entry.rating is not None:
			return self.entry.rating.average
		return 0


	def getNumRaters(self):
		if self.entry.rating is not None:
			return self.entry.rating.num_raters
		return ""	

	def getAuthor(self):
		authors = []
		for author in self.entry.author:
			authors.append(author.name.text)
		author = ", ".join(authors)
		return author

	def PrintEntryDetails(self):
		EntryDetails = { 'Title': None, 'TubeID': None, 'Published': None, 'Published': None, 'Description': None, 'Category': None, 'Tags': None, 'Duration': None, 'Views': None, 'Rating': None, 'Thumbnails': None}
		EntryDetails['Title'] = self.entry.media.title.text
		EntryDetails['TubeID'] = self.getTubeId()
		EntryDetails['Description'] = self.getDescription()
		EntryDetails['Category'] = self.entry.media.category[0].text
		EntryDetails['Tags'] = self.entry.media.keywords.text
		EntryDetails['Published'] = self.getPublishedDate()
		EntryDetails['Views'] = self.getViews()
		EntryDetails['Duration'] = self.getDuration()
		EntryDetails['Rating'] = self.getNumRaters()
		EntryDetails['RatingAverage'] = self.getRatingAverage()
		EntryDetails['Author'] = self.getAuthor()
		# show thumbnails
		list = []
		for thumbnail in self.entry.media.thumbnail:
			print 'Thumbnail url: %s' % thumbnail.url
			list.append(str(thumbnail.url))
		EntryDetails['Thumbnails'] = list
		#print EntryDetails
		return EntryDetails


	def getVideoUrl(self):
		mrl = None
		isHDAvailable = False
		req = "http://www.youtube.com/watch?v=" + str(self.getTubeId())
		try:
			response = urllib.urlopen(req)
			"""if config.plugins.mytube.general.useHTTPProxy.value is True:
				proxy = {'http': str(config.plugins.mytube.general.ProxyIP.getText())+':'+str(config.plugins.mytube.general.ProxyPort.value)}
				print "USING PRXY---->",proxy
				response = urllib.urlopen(req,proxies=proxy)
			else:
				response = urllib.urlopen(req)"""
		except HTTPError, e:
			print "[MyTube] The server coundn't fulfill the request."
			print "[MyTube] Error code: ", e.code
		except URLError, e:
			print "[MyTube] We failed to reach a server."
			print "[MyTube] Reason: ", e.reason
		except IOError, e:
			print "[MyTube] We failed to reach a server."
			print "[MyTube] Reason: ", e
		else:
			while not None:
				data = response.readline()
				if data == "":
					break

				if "isHDAvailable = true" in data:
					isHDAvailable = True
					print "HD AVAILABLE"
				else:
					pass
				m = re.search("watch_fullscreen\\?(?P<vid_query>.*?)&title=(?P<name>.*)';\n", data)
				if m:
					break
			response.close
			if m:
				t= re.match (".*[?&]t=([^&]+)", m.group('vid_query')).groups()[0]
				if isHDAvailable is True:
					mrl = "http://www.youtube.com/get_video?video_id=" + quote(self.getTubeId()) + "&t=" + t + "&fmt=22"
					print "[MyTube] GOT HD URL: ", mrl
				else:
					mrl = "http://www.youtube.com/get_video?video_id=" + quote(self.getTubeId()) + "&t=" + t + "&fmt=18"
					print "[MyTube] GOT SD URL: ", mrl

			else:
				print "[MyTube] No valid mp4-url found"
		#self.myopener = MyOpener()
		#urllib.urlopen = MyOpener().open
		return mrl

	def getRelatedVideos(self):
		print "[MyTubeFeedEntry] getResponseVideos()"
		for link in self.entry.link:
			#print "Related link: ", link.rel.endswith
			if link.rel.endswith("video.related"):
				print "Found Related: ", link.href
				return link.href

	def getResponseVideos(self):
		print "[MyTubeFeedEntry] getResponseVideos()"
		for link in self.entry.link:
			#print "Responses link: ", link.rel.endswith
			if link.rel.endswith("video.responses"):
				print "Found Responses: ", link.href
				return link.href

class MyTubePlayerService():
#	Do not change the client_id and developer_key in the login-section!
#	ClientId: ytapi-dream-MyTubePlayer-i0kqrebg-0
#	DeveloperKey: AI39si4AjyvU8GoJGncYzmqMCwelUnqjEMWTFCcUtK-VUzvWygvwPO-sadNwW5tNj9DDCHju3nnJEPvFy4WZZ6hzFYCx8rJ6Mw
	def __init__(self):
		print "[MyTube] MyTubePlayerService - init"
		self.feedentries = []
		self.feed = None
		
	def startService(self):
		print "[MyTube] MyTubePlayerService - startService"
		self.yt_service = gdata.youtube.service.YouTubeService()
		self.yt_service.developer_key = 'AI39si4AjyvU8GoJGncYzmqMCwelUnqjEMWTFCcUtK-VUzvWygvwPO-sadNwW5tNj9DDCHju3nnJEPvFy4WZZ6hzFYCx8rJ6Mw'
		self.yt_service.client_id = 'ytapi-dream-MyTubePlayer-i0kqrebg-0'
		self.loggedIn = False
		#os.environ['http_proxy'] = 'http://169.229.50.12:3128'
		#proxy = os.environ.get('http_proxy')
		#print "FOUND ENV PROXY-->",proxy
		#for a in os.environ.keys():
		#	print a

	def stopService(self):
		print "[MyTube] MyTubePlayerService - stopService"
		del self.ytService
		self.loggedIn = False

	def isLoggedIn(self):
		return self.loggedIn

	def getFeed(self, url):
		print "[MyTube] MyTubePlayerService - getFeed:",url
		self.feedentries = []
		self.feed = self.yt_service.GetYouTubeVideoFeed(url)
		for entry in self.feed.entry:
			MyFeedEntry = MyTubeFeedEntry(self, entry)
			self.feedentries.append(MyFeedEntry)
		return self.feed			

	def search(self, searchTerms, startIndex = 1, maxResults = 25,
					orderby = "relevance", racy = "include", 
					author = "", lr = "", categories = "", sortOrder = "ascending"):
		print "[MyTube] MyTubePlayerService - search()"
		self.feedentries = []
		query = gdata.youtube.service.YouTubeVideoQuery()
		query.vq = searchTerms
		query.orderby = orderby
		query.racy = racy
		query.sortorder = sortOrder
		if lr is not None:
			query.lr = lr
		if categories[0] is not None:
			query.categories = categories
		query.start_index = startIndex
		query.max_results = maxResults
		try:
			feed = self.yt_service.YouTubeQuery(query)
		except gaierror:
			feed = None
		if feed is not None:
			self.feed = feed
			for entry in self.feed.entry:
				MyFeedEntry = MyTubeFeedEntry(self, entry)
				self.feedentries.append(MyFeedEntry)
		return self.feed		

	def getTitle(self):
		return self.feed.title.text

	def getEntries(self):
		return self.feedentries

	def itemCount(self):
		return self.feed.items_per_page.text

	def getTotalResults(self):
		return self.feed.total_results.text
	
	def getNextFeedEntriesURL(self):
		for link in self.feed.link:
			if link.rel == "next":
				return link.href
		return None


myTubeService = MyTubePlayerService()
