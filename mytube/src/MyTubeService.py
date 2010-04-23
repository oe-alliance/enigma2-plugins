# -*- coding: iso-8859-1 -*-
from __init__ import bin2long, long2bin, rsa_pub1024, decrypt_block
import gdata.youtube
import gdata.youtube.service
from gdata.service import BadAuthentication
from Tools.LoadPixmap import LoadPixmap
from Components.config import config, Config, ConfigSelection, ConfigText, getConfigListEntry, ConfigSubsection, ConfigYesNo, ConfigIP, ConfigNumber
from Components.ConfigList import ConfigListScreen
from Components.config import KEY_DELETE, KEY_BACKSPACE, KEY_LEFT, KEY_RIGHT, KEY_HOME, KEY_END, KEY_TOGGLEOW, KEY_ASCII, KEY_TIMEOUT

from twisted.web import client
from twisted.internet import reactor
from urllib2 import Request, URLError, HTTPError, urlopen as urlopen2
from socket import gaierror,error
import re, os, sys, socket
from urllib import quote, unquote_plus, unquote
import cookielib
from httplib import HTTPConnection,CannotSendRequest,BadStatusLine,HTTPException
HTTPConnection.debuglevel = 1

def validate_cert(cert, key):
	buf = decrypt_block(cert[8:], key) 
	if buf is None:
		return None
	return buf[36:107] + cert[139:196]

def get_rnd():
	try:
		rnd = os.urandom(8)
		return rnd
	except:
		return None

std_headers = {
	'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
	'Accept-Language': 'en-us,en;q=0.5',
}

#config.plugins.mytube = ConfigSubsection()
#config.plugins.mytube.general = ConfigSubsection()
#config.plugins.mytube.general.useHTTPProxy = ConfigYesNo(default = False)
#config.plugins.mytube.general.ProxyIP = ConfigIP(default=[0,0,0,0])
#config.plugins.mytube.general.ProxyPort = ConfigNumber(default=8080)
#class MyOpener(FancyURLopener):
#	version = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12'


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
		"""self.myopener = MyOpener()
		urllib.urlopen = MyOpener().open
		if config.plugins.mytube.general.useHTTPProxy.value is True:
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
			split = self.entry.media.player.url.split("=")
			ret = split.pop()
			if ret == 'youtube_gdata':
				tmpval=split.pop()
				if tmpval.endswith("&feature"):
					tmp = tmpval.split("&")
					ret = tmp.pop(0)
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
		video_id = str(self.getTubeId())
		#URLs for YouTube video pages will change from the format http://www.youtube.com/watch?v=ylLzyHk54Z0 to http://www.youtube.com/watch#!v=ylLzyHk54Z0.
		watch_url = "http://www.youtube.com/watch?v=" + video_id
		watchrequest = Request(watch_url, None, std_headers)
		try:
			print "trying to find out if a HD Stream is available",watch_url
			watchvideopage = urlopen2(watchrequest).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			print "[MyTube] Error: Unable to retrieve watchpage - Error code: ", str(err)
			print "[MyTube] No valid mp4-url found"
			return mrl

		if "'IS_HD_AVAILABLE': true" in watchvideopage:
			isHDAvailable = True
			print "HD AVAILABLE"
		else:
			print "HD Stream NOT AVAILABLE"

		# Get video info
		#info_url = 'http://www.youtube.com/get_video_info?&video_id=%s&el=detailpage&ps=default&eurl=&gl=US&hl=en' % video_id
		info_url = 'http://www.youtube.com/get_video_info?&video_id=%s' % video_id
		inforequest = Request(info_url, None, std_headers)
		try:
			print "getting video_info_webpage",info_url
			infopage = urlopen2(inforequest).read()
		except (urllib2.URLError, httplib.HTTPException, socket.error), err:
			print "[MyTube] Error: Unable to retrieve infopage, error:", str(err)
			print "[MyTube] No valid mp4-url found"
			return mrl

		mobj = re.search(r'(?m)&token=([^&]+)(?:&|$)', infopage)
		if mobj is None:
			# was there an error ?
			mobj = re.search(r'(?m)&reason=([^&]+)(?:&|$)', infopage)
			if mobj is None:
				print 'ERROR: unable to extract "t" parameter for unknown reason'
			else:
				reason = unquote_plus(mobj.group(1))
				print 'ERROR: YouTube said: %s' % reason.decode('utf-8')
			return mrl
	
		token = unquote(mobj.group(1))
		#myurl = 'http://www.youtube.com/get_video?video_id=%s&t=%s&eurl=&el=detailpage&ps=default&gl=US&hl=en' % (video_id, token)
		myurl = 'http://www.youtube.com/get_video?video_id=%s&t=%s' % (video_id, token)
		if isHDAvailable is True:
			mrl = '%s&fmt=%s' % (myurl, '22')
			print "[MyTube] GOT HD URL: ", mrl
		else:
			mrl = '%s&fmt=%s' % (myurl, '18')
			print "[MyTube] GOT SD URL: ", mrl

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
