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
from urlparse import parse_qs

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
	'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
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
		#GET /complete/search?output=toolbar&ds=yt&hl=en&jsonp=self.gotSuggestions&q=s
		self.prepQuerry = "/complete/search?output=toolbar&"
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
				print "[MyTube]  Can not send request for suggestions"
				self.callback(None)
			else:
				try:
					response = self.conn.getresponse()
				except BadStatusLine:
					print "[MyTube]  Can not get a response from google"
					self.callback(None)
				else:
					if response.status == 200:
						data = response.read()
						self.gotSuggestions(data)
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
		VIDEO_FMT_PRIORITY_MAP = {
			'38' : 1, #MP4 Original (HD)
			'37' : 2, #MP4 1080p (HD)
			'22' : 3, #MP4 720p (HD)
			'18' : 4, #MP4 360p
			'35' : 5, #FLV 480p
			'34' : 6, #FLV 360p
		}
		video_url = None
		video_id = str(self.getTubeId())

		# Getting video webpage
		#URLs for YouTube video pages will change from the format http://www.youtube.com/watch?v=ylLzyHk54Z0 to http://www.youtube.com/watch#!v=ylLzyHk54Z0.
		watch_url = 'http://www.youtube.com/watch?v=%s&gl=US&hl=en' % video_id
		watchrequest = Request(watch_url, None, std_headers)
		try:
			print "[MyTube] trying to find out if a HD Stream is available",watch_url
			watchvideopage = urlopen2(watchrequest).read()
		except (URLError, HTTPException, socket.error), err:
			print "[MyTube] Error: Unable to retrieve watchpage - Error code: ", str(err)
			return video_url

		# Get video info
		for el in ['&el=embedded', '&el=detailpage', '&el=vevo', '']:
			info_url = ('http://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en' % (video_id, el))
			request = Request(info_url, None, std_headers)
			try:
				infopage = urlopen2(request).read()
				videoinfo = parse_qs(infopage)
				if 'fmt_url_map' in videoinfo:
					break
			except (URLError, HTTPException, socket.error), err:
				print "[MyTube] Error: unable to download video infopage",str(err)
				return video_url

		if 'fmt_url_map' not in videoinfo:
			# Attempt to see if YouTube has issued an error message
			if 'reason' not in videoinfo:
				print '[MyTube] Error: unable to extract "fmt_url_map" parameter for unknown reason'
			else:
				reason = unquote_plus(videoinfo['reason'][0])
				print '[MyTube] Error: YouTube said: %s' % reason.decode('utf-8')
			return video_url

		video_fmt_map = {}
		fmt_infomap = {}
		tmp_fmtUrlDATA = videoinfo['fmt_url_map'][0].split(',')
		for fmtstring in tmp_fmtUrlDATA:
			(fmtid,fmturl) = fmtstring.split('|')
			if VIDEO_FMT_PRIORITY_MAP.has_key(fmtid):
				video_fmt_map[VIDEO_FMT_PRIORITY_MAP[fmtid]] = { 'fmtid': fmtid, 'fmturl': unquote_plus(fmturl) }
			fmt_infomap[int(fmtid)] = unquote_plus(fmturl)
		print "[MyTube] got",sorted(fmt_infomap.iterkeys())
		if video_fmt_map and len(video_fmt_map):
			print "[MyTube] found best available video format:",video_fmt_map[sorted(video_fmt_map.iterkeys())[0]]['fmtid']
			video_url = video_fmt_map[sorted(video_fmt_map.iterkeys())[0]]['fmturl']
			print "[MyTube] found best available video url:",video_url
		
		return video_url
	
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
