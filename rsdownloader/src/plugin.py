# -*- coding: utf-8 -*-
##
## RS Downloader
## by AliAbdul
##
##
from base64 import encodestring
from Components.ActionMap import ActionMap
from Components.config import config, ConfigClock, ConfigInteger, ConfigSelection, ConfigSubsection, ConfigText, ConfigYesNo, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Console import Console as eConsole
from Components.FileList import FileList
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.ScrollLabel import ScrollLabel
from container.decrypt import decrypt
from enigma import eListboxPythonMultiContent, eTimer, gFont, RT_HALIGN_CENTER, RT_HALIGN_RIGHT
from os import listdir, remove, system
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.Console import Console as ConsoleScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from time import localtime, sleep, strftime, time
from Tools.Directories import fileExists, resolveFilename, SCOPE_SKIN_IMAGE, SCOPE_LANGUAGE, SCOPE_PLUGINS
from Tools.Downloader import HTTPProgressDownloader
from Tools.LoadPixmap import LoadPixmap
from twisted.internet import reactor
from twisted.python import failure
from twisted.web.client import getPage
from urllib2 import Request
from urlparse import urlparse, urlunparse
from xml.etree.cElementTree import parse
import os, gettext, re, socket, sys, urllib, urllib2

##############################################################################

config.plugins.RSDownloader = ConfigSubsection()
config.plugins.RSDownloader.onoff = ConfigYesNo(default=True)
config.plugins.RSDownloader.username = ConfigText(default="", fixed_size=False)
config.plugins.RSDownloader.password = ConfigText(default="", fixed_size=False)
config.plugins.RSDownloader.lists_directory = ConfigText(default="/media/hdd/rs/lists/", fixed_size=False)
config.plugins.RSDownloader.downloads_directory = ConfigText(default="/media/hdd/rs/downloads", fixed_size=False)
config.plugins.RSDownloader.ignore_time = ConfigYesNo(default=False)
config.plugins.RSDownloader.start_time = ConfigClock(default=time())
config.plugins.RSDownloader.end_time = ConfigClock(default=time())
config.plugins.RSDownloader.download_monday = ConfigYesNo(default=True)
config.plugins.RSDownloader.download_tuesday = ConfigYesNo(default=True)
config.plugins.RSDownloader.download_wednesday = ConfigYesNo(default=True)
config.plugins.RSDownloader.download_thursday = ConfigYesNo(default=True)
config.plugins.RSDownloader.download_friday = ConfigYesNo(default=True)
config.plugins.RSDownloader.download_saturday = ConfigYesNo(default=True)
config.plugins.RSDownloader.download_sunday = ConfigYesNo(default=True)
config.plugins.RSDownloader.count_downloads = ConfigInteger(default=3, limits=(1, 10))
config.plugins.RSDownloader.count_maximal_downloads = ConfigInteger(default=40, limits=(1, 1000))
config.plugins.RSDownloader.write_log = ConfigYesNo(default=True)
config.plugins.RSDownloader.reconnect_type = ConfigSelection(choices={"script": _("Script"), "fritz": _("fritz.Box"), "no": _("No reconnect")}, default="fritz")
config.plugins.RSDownloader.reconnect_script = ConfigText(default="", fixed_size=False)
config.plugins.RSDownloader.autorestart_failed = ConfigYesNo(default=False)
config.plugins.RSDownloader.mark_small_as_failed = ConfigYesNo(default=True)
config.plugins.RSDownloader.unrar_password = ConfigText(default="", fixed_size=False)
config.plugins.RSDownloader.reconnect_start_time = ConfigClock(default=time())
config.plugins.RSDownloader.reconnect_end_time = ConfigClock(default=time())
config.plugins.Netload = ConfigSubsection()
config.plugins.Netload.username = ConfigText(default="", fixed_size=False)
config.plugins.Netload.password = ConfigText(default="", fixed_size=False)
config.plugins.Uploaded = ConfigSubsection()
config.plugins.Uploaded.username = ConfigText(default="", fixed_size=False)
config.plugins.Uploaded.password = ConfigText(default="", fixed_size=False)

##############################################################################

PluginLanguageDomain = "RSDownloader"
PluginLanguagePath = "Extensions/RSDownloader/locale/"

def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print "[" + PluginLanguageDomain + "] fallback to default translation for " + txt
		return gettext.gettext(txt)

language.addCallback(localeInit())

##############################################################################

def writeLog(message):
	if config.plugins.RSDownloader.write_log.value:
		try:
			f = open("/tmp/rapidshare.log", "a")
			f.write(strftime("%c", localtime(time())) + " - " + message + "\n")
			f.close()
		except:
			pass

##############################################################################

def _parse(url):
	url = url.strip()
	parsed = urlparse(url)
	scheme = parsed[0]
	path = urlunparse(('','') + parsed[2:])
	host, port = parsed[1], 80
	if '@' in host:
		username, host = host.split('@')
		if ':' in username:
			username, password = username.split(':')
		else:
			password = ""
	else:
		username = ""
		password = ""
	if ':' in host:
		host, port = host.split(':')
		port = int(port)
	if path == "":
		path = "/"
	return scheme, host, port, path, username, password

class ProgressDownload:
	def __init__(self, url, outputfile, contextFactory=None, *args, **kwargs):
		scheme, host, port, path, username, password = _parse(url)
		if username and password:
			url = scheme + '://' + host + ':' + str(port) + path
			basicAuth = encodestring("%s:%s"%(username, password))
			authHeader = "Basic " + basicAuth.strip()
			AuthHeaders = {"Authorization": authHeader}
			if kwargs.has_key("headers"):
				kwargs["headers"].update(AuthHeaders)
			else:
				kwargs["headers"] = AuthHeaders
		self.factory = HTTPProgressDownloader(url, outputfile, *args, **kwargs)
		self.connection = reactor.connectTCP(host, port, self.factory)

	def start(self):
		return self.factory.deferred

	def stop(self):
		self.connection.disconnect()

	def addProgress(self, progress_callback):
		self.factory.progress_callback = progress_callback

##############################################################################

def get(url):
	try:
		data = urllib2.urlopen(url)
		return data.read()
	except:
		return ""
   
def post(url, data):
	try:
		return urllib2.urlopen(url, data).read()
	except:
		return ""

def matchGet(rex, string):
	match = re.search(rex, string)
	if match:
		if len(match.groups()) == 0:
			return string[match.span()[0]:match.span()[1]]
		if len(match.groups()) == 1:
			return match.groups()[0]
	else:
		return False

##############################################################################

def reconnect(host='fritz.box', port=49000):
	writeLog("Reconnecting fritz.Box...")
	http_body = '\r\n'.join((
		'<?xml version="1.0" encoding="utf-8"?>',
		'<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">',
		'  <s:Body>',
		'    <u:ForceTermination xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1"/>',
		'  </s:Body>',
		'</s:Envelope>'))
	http_data = '\r\n'.join((
		'POST /upnp/control/WANIPConn1 HTTP/1.1',
		'Host: %s:%d'%(host, port),
		'SoapAction: urn:schemas-upnp-org:service:WANIPConnection:1#ForceTermination',
		'Content-Type: text/xml; charset="utf-8"',
		'Content-Length: %d'%len(http_body),
		'',
		http_body))
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((host, port))
		s.send(http_data)
		s.close()
	except:
		writeLog("Error while reconnecting fritz.Box: " + str(sys.exc_info()))

##############################################################################

def reconnect_script():
	script = config.plugins.RSDownloader.reconnect_script.value
	if script != "" and fileExists(script):
		writeLog("Reconnecting with script %s..."%script)
		system(script)
	else:
		writeLog("Error: Reconnect script %s not found!"%script)

##############################################################################

std_headers = {
	'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
	'Accept-Language': 'en-us,en;q=0.5',
}

class RSDownload:
	def __init__(self, url):
		writeLog("Adding: %s"%url)
		self.url = url
		self.download = None
		self.downloading = False
		self.progress = 0
		self.size = 0
		self.status = _("Waiting")
		self.name = self.url.split("/")[-1]
		self.finishCallbacks = []

	def mayReconnect(self):
		start = config.plugins.RSDownloader.reconnect_start_time.value
		end = config.plugins.RSDownloader.reconnect_end_time.value
		t = localtime()
		hour_now = t[3]
		minute_now = t[4]
		hour_start = start[0]
		minute_start = start[1]
		hour_end = end[0]
		minute_end = end[1]
		if start == end: # Same start and end-time
			return True
		elif hour_end < hour_start: # Different days!!!
			if hour_now > hour_start or hour_now < hour_end:
				return True
			elif hour_now == hour_start and minute_now > minute_start:
				return True
			elif hour_now == hour_end and minute_now < minute_end:
				return True
			else:
				return False
		elif hour_now > hour_start and hour_now < hour_end: # Same day...
			return True
		elif hour_now == hour_start and minute_now > minute_start: # Same day, same start-hour...
			return True
		elif hour_now == hour_end and minute_now < minute_end: # Same day, same end-hour...
			return True
		else:
			return False

	def start(self):
		writeLog("Downloading: %s"%self.url)
		self.downloading = True
		self.progress = 0
		self.size = 0
		username = config.plugins.RSDownloader.username.value
		password = config.plugins.RSDownloader.password.value
		nl_username = config.plugins.Netload.username.value
		nl_password = config.plugins.Netload.password.value
		ul_username = config.plugins.Uploaded.username.value
		ul_password = config.plugins.Uploaded.password.value
		if self.url.__contains__("rapidshare.com") and username == "" and password == "":
			writeLog("Free RS-Download: %s"%self.url)
			self.status = _("Checking")
			if self.mayReconnect():
				if config.plugins.RSDownloader.reconnect_type.value == "fritz":
					reconnect()
					sleep(3)
				if config.plugins.RSDownloader.reconnect_type.value == "script":
					reconnect_script()
					sleep(3)
			data = get(self.url)
			url = matchGet('<form[^>]+action="([^"]+)', data)
			if not url:
				writeLog("Failed: %s"%self.url)
				self.httpFailed(True, "Failed to get download page url: %s"%self.url)
			else:
				data = post(url, "dl.start=Free")
				seconds = matchGet('var c=([0-9]+)', data)
				if not seconds:
					self.httpFailed(True, "Failed to get download page url: %s"%self.url)
				else:
					writeLog("Free RS-Download... must wait %s seconds: %s"%(seconds, self.url))
					self.status = "%s %s"%(_("Waiting"), seconds)
					url = matchGet('"dlf" action="([^"]+)', data)
					if not url:
						self.httpFailed(True, "Failed to get download page url: %s"%self.url)
					else:
						self.freeDownloadUrl = url
						self.freeDownloadTimer = eTimer()
						self.freeDownloadTimer.callback.append(self.freeDownloadStart)
						self.freeDownloadTimer.start((int(seconds) + 2) * 1000, 1)
		elif (self.url.__contains__("uploaded.to") or self.url.__contains__("ul.to")) and ul_username == "" and ul_password == "":
			writeLog("Free Uploaded.to-Download: %s"%self.url)
			self.status = _("Checking")
			if self.mayReconnect():
				if config.plugins.RSDownloader.reconnect_type.value == "fritz":
					reconnect()
					sleep(3)
				if config.plugins.RSDownloader.reconnect_type.value == "script":
					reconnect_script()
					sleep(3)
			data = get(self.url)
			tmp = re.search(r"Or wait (\d+) minutes", data)
			if tmp:
				minutes = tmp.group(1)
				writeLog("Free Uploaded.to-Download... must wait %s minutes: %s"%(minutes, self.url))
				self.status = "%s %s"%(_("Waiting"), minutes)
				self.freeDownloadTimer = eTimer()
				self.freeDownloadTimer.callback.append(self.start)
				self.freeDownloadTimer.start((int(minutes) + 1) * 60000, 1)
			else:
				try:
					url = re.search(r".*<form name=\"download_form\" method=\"post\" action=\"(.*)\">", data).group(1)
				except:
					url = None
				if url:
					self.name = re.search(r"<td><b>\s+(.+)\s", data).group(1) + re.search(r"</td><td>(\..+)</td></tr>", data).group(1)
					self.status = _("Downloading")
					self.download = ProgressDownload(url, ("%s/%s"%(config.plugins.RSDownloader.downloads_directory.value, self.name)).replace("//", "/"))
					self.download.addProgress(self.httpProgress)
					self.download.start().addCallback(self.httpFinished).addErrback(self.httpFailed)
				else:
					self.httpFailed(True, "File is offline: %s"%self.url)
		elif self.url.__contains__("youtube.com"):
			writeLog("Getting youtube video link: %s"%self.url)
			self.status = _("Checking")
			downloadLink = self.getYoutubeDownloadLink()
			if downloadLink:
				self.status = _("Downloading")
				writeLog("Downloading video: %s"%downloadLink)
				req = urllib2.Request(downloadLink)
				url_handle = urllib2.urlopen(req)
				headers = url_handle.info()
				if headers.getheader("content-type") == "video/mp4":
					ext = "mp4"
				else:
					ext = "flv"
				self.download = ProgressDownload(downloadLink, ("%s/%s.%s"%(config.plugins.RSDownloader.downloads_directory.value, self.name, ext)).replace("//", "/"))
				self.download.addProgress(self.httpProgress)
				self.download.start().addCallback(self.httpFinished).addErrback(self.httpFailed)
			else:
				self.httpFailed(True, "Failed to get video url: %s"%self.url)
		else:
			if self.url.__contains__("rapidshare.com") and username != "" and password != "":
				url = self.url.replace("http://", "http://" + username + ":" + password + "@")
			elif (self.url.__contains__("uploaded.to") or self.url.__contains__("ul.to")) and ul_username != "" and ul_password != "":
				url = self.url.replace("http://", "http://" + ul_username + ":" + ul_password + "@")
			elif self.url.__contains__("netload.in") and nl_username != "" and nl_password != "":
				url = self.url.replace("http://", "http://" + nl_username + ":" + nl_password + "@")
			else:
				url = self.url
			self.status = _("Downloading")
			self.download = ProgressDownload(url, ("%s/%s"%(config.plugins.RSDownloader.downloads_directory.value, self.name)).replace("//", "/").replace(".html", ""))
			self.download.addProgress(self.httpProgress)
			self.download.start().addCallback(self.httpFinished).addErrback(self.httpFailed)

	def freeDownloadStart(self):
		self.status = _("Downloading")
		self.download = ProgressDownload(self.freeDownloadUrl, ("%s/%s"%(config.plugins.RSDownloader.downloads_directory.value, self.name)).replace("//", "/").replace(".html", ""))
		self.download.addProgress(self.httpProgress)
		self.download.start().addCallback(self.httpFinished).addErrback(self.httpFailed)

	def stop(self):
		self.progress = 0
		self.downloading = False
		self.status = _("Waiting")
		if self.download:
			writeLog("Stopping download: %s"%self.url)
			self.download.stop()

	def httpProgress(self, recvbytes, totalbytes):
		if self.size == 0:
			self.size = int((totalbytes / 1024) / 1024)
		self.progress = int(100.0 * float(recvbytes) / float(totalbytes))

	def httpFinished(self, string=None):
		if string is not None:
			writeLog("Failed: %s"%self.url)
			writeLog("Error: %s"%string)
		self.status = _("Checking")
		self.checkTimer = eTimer()
		self.checkTimer.callback.append(self.doCheckTimer)
		self.checkTimer.start(10000, 1)

	def doCheckTimer(self):
		if (self.size == 0) or (self.progress < 100) or ((config.plugins.RSDownloader.mark_small_as_failed.value == True) and (self.size < 1)):
			self.status = _("Failed")
			if config.plugins.RSDownloader.autorestart_failed.value:
				self.restartFailedTimer = eTimer()
				self.restartFailedTimer.callback.append(self.restartFailedCheck)
				self.restartFailedTimer.start(10000*60, 1)
		elif self.progress == 100:
			self.status = _("Finished")
			writeLog("Finished: %s"%self.url)
		self.downloading = False
		self.execFinishCallbacks()

	def restartFailedCheck(self):
		if self.status == _("Failed"): # check if user didn't restart already
			self.download = None
			self.status = _("Waiting")

	def execFinishCallbacks(self):
		for x in self.finishCallbacks:
			x()

	def httpFailed(self, failure=None, error=""):
		if failure:
			if error == "":
				error = failure.getErrorMessage()
			if error != "" and not error.startswith("[Errno 2]"):
				writeLog("Failed: %s"%self.url)
				writeLog("Error: %s"%error)
				self.status = _("Checking")
		self.checkTimer = eTimer()
		self.checkTimer.callback.append(self.doCheckTimer)
		self.checkTimer.start(10000, 1)

	def getTubeId(self):
		url = self.url
		if url.__contains__("&feature="):
			idx = url.index("&feature=")
			url = url[:idx]
		split = url.split("=")
		ret = split.pop()
		if ret == 'youtube_gdata':
			tmpval = split.pop()
			if tmpval.endswith("&feature"):
				tmp = tmpval.split("&")
				ret = tmp.pop(0)
		return ret

	def getYoutubeDownloadLink(self):
		html = get(self.url)
		if html != "":
			reonecat = re.compile(r'<title>(.+?)</title>', re.DOTALL)
			titles = reonecat.findall(html)
			if titles:
				self.name = titles[0]
				if self.name.__contains__("\t- "):
					idx = self.name.index("\t- ")
					self.name = (self.name[idx+3:]).replace("&amp;", "&").replace("\t", "").replace("\n", "")
		mrl = None
		isHDAvailable = False
		video_id = str(self.getTubeId())
		watch_url = "http://www.youtube.com/watch?v="+video_id
		watchrequest = Request(watch_url, None, std_headers)
		try:
			watchvideopage = urllib2.urlopen(watchrequest).read()
		except:
			watchvideopage = ""
		if "isHDAvailable = true" in watchvideopage:
			isHDAvailable = True
		info_url = 'http://www.youtube.com/get_video_info?&video_id=%s&el=detailpage&ps=default&eurl=&gl=US&hl=en'%video_id
		inforequest = Request(info_url, None, std_headers)
		try:
			infopage = urllib2.urlopen(inforequest).read()
		except:
			infopage = ""
		mobj = re.search(r'(?m)&token=([^&]+)(?:&|$)', infopage)
		if mobj:
			token = urllib.unquote(mobj.group(1))
			myurl = 'http://www.youtube.com/get_video?video_id=%s&t=%s&eurl=&el=detailpage&ps=default&gl=US&hl=en'%(video_id, token)
			if isHDAvailable is True:
				mrl = '%s&fmt=%s'%(myurl, '22')
			else:
				mrl = '%s&fmt=%s'%(myurl, '18')
		return mrl

##############################################################################

class RS:
	def __init__(self):
		self.downloads = []
		self.checkTimer = eTimer()
		self.checkTimer.callback.append(self.startDownloading)
		self.checkTimer.start(5000*60, False)

	def mayDownload(self):
		if config.plugins.RSDownloader.onoff.value == False:
			writeLog("RS Downloader is turned off...")
			return False
		elif config.plugins.RSDownloader.ignore_time.value:
			return True
		else:
			start = config.plugins.RSDownloader.start_time.value
			end = config.plugins.RSDownloader.end_time.value
			t = localtime()
			weekday = t[6]
			if weekday == 0 and config.plugins.RSDownloader.download_monday.value == False:
				return False
			elif weekday == 1 and config.plugins.RSDownloader.download_tuesday.value == False:
				return False
			elif weekday == 2 and config.plugins.RSDownloader.download_wednesday.value == False:
				return False
			elif weekday == 3 and config.plugins.RSDownloader.download_thursday.value == False:
				return False
			elif weekday == 4 and config.plugins.RSDownloader.download_friday.value == False:
				return False
			elif weekday == 5 and config.plugins.RSDownloader.download_saturday.value == False:
				return False
			elif weekday == 6 and config.plugins.RSDownloader.download_sunday.value == False:
				return False
			else:
				hour_now = t[3]
				minute_now = t[4]
				hour_start = start[0]
				minute_start = start[1]
				hour_end = end[0]
				minute_end = end[1]
				if start == end: # Same start and end-time
					return True
				elif hour_end < hour_start: # Different days!!!
					if hour_now > hour_start or hour_now < hour_end:
						return True
					elif hour_now == hour_start and minute_now > minute_start:
						return True
					elif hour_now == hour_end and minute_now < minute_end:
						return True
					else:
						return False
				elif hour_now > hour_start and hour_now < hour_end: # Same day...
					return True
				elif hour_now == hour_start and minute_now > minute_start: # Same day, same start-hour...
					return True
				elif hour_now == hour_end and minute_now < minute_end: # Same day, same end-hour...
					return True
				else:
					return False

	def allDownloadsFinished(self):
		allDone = True
		for download in self.downloads:
			if (download.status != _("Failed")) and (download.status != _("Finished")):
				allDone = False
				break
		return allDone

	def startDownloading(self):
		if self.mayDownload() == True:
			if self.allDownloadsFinished() == True:
				self.readLists()
			downloadCount = 0
			for download in self.downloads:
				if download.downloading == True:
					downloadCount += 1 # Count the downloaded files
			# Get next download
			download = None
			for next in self.downloads:
				if next.downloading == False and next.status.startswith(_("Waiting")):
					download = next
					break
			if download:
				# Check URL of next download
				onlyOneAllowed = True
				if download.url.__contains__("rapidshare.com"):
					if config.plugins.RSDownloader.username.value != "" and config.plugins.RSDownloader.password.value != "":
						onlyOneAllowed = False
				elif download.url.__contains__("uploaded.to") or download.url.__contains__("ul.to"):
					if config.plugins.Uploaded.username.value != "" and config.plugins.Uploaded.password.value != "":
						onlyOneAllowed = False
				elif download.url.__contains__("netload.in"):
					if config.plugins.Netload.username.value != "" and config.plugins.Netload.password.value != "":
						onlyOneAllowed = False
				if onlyOneAllowed and downloadCount == 0:
					download.start() # Start only first download in the list
				elif onlyOneAllowed == False:
					mayDownloadCount = config.plugins.RSDownloader.count_downloads.value - downloadCount
					for download in self.downloads:
						if download.downloading == False:
							if mayDownloadCount > 0 and download.status == _("Waiting"):
								download.start()
								mayDownloadCount -= 1

	def addDownload(self, url):
		error = False
		for download in self.downloads:
			if download.url == url:
				error = True
		if error:
			return False
		else:
			download = RSDownload(url)
			download.finishCallbacks.append(self.cleanLists)
			self.downloads.append(download)
			return True

	def readLists(self):
		writeLog("Reading all lists...")
		path = config.plugins.RSDownloader.lists_directory.value
		if not path.endswith("/"):
			path = path + "/"
		writeLog("Directory: " + path)
		try:
			file_list = listdir(path)
			file_list.sort()
			writeLog("Count of lists: " + str(len(file_list)))
		except:
			file_list = []
			writeLog("Could not find any list: " + str(sys.exc_info()))
		added_downloads = 0
		for x in file_list:
			list = path + x
			if list.endswith(".txt"):
				try:
					writeLog("Reading list %s..."%list)
					f = open(list, "r")
					count = 0
					for l in f:
						if l.startswith("http://"):
							if added_downloads < config.plugins.RSDownloader.count_maximal_downloads.value:
								if (self.addDownload(l.replace("\n", "").replace("\r", ""))) == True:
									count += 1
									added_downloads += 1
							else:
								break
					f.close()
					if count == 0:
						writeLog("Empty list or downloads already in download list: %s"%list)
					else:
						writeLog("Added %d files from list %s..."%(count, list))
				except:
					writeLog("Error while reading list %s!"%list)
			else:
				writeLog("No *.txt file: %s!"%list)

	def cleanLists(self):
		writeLog("Cleaning lists...")
		path = config.plugins.RSDownloader.lists_directory.value
		if not path.endswith("/"):
			path = path + "/"
		try:
			file_list = listdir(path)
		except:
			file_list = []
			writeLog("Error while searching for lists: " + str(sys.exc_info()))
		
		finished_downloads = []
		for download in self.downloads:
			if download.status == _("Finished"):
				finished_downloads.append(download)
		for x in file_list:
			list = path + x
			if list.endswith(".txt"):
				try:
					f = open(list, "r")
					content = f.read()
					f.close()
					for finished in finished_downloads:
						if content.__contains__(finished.url):
							content = content.replace(finished.url, "")
							content = content.replace("\n\n", "\n").replace("\r\r", "\r")
					f = open(list, "w")
					f.write(content)
					f.close()
				except:
					writeLog("Error while cleaning list %s: %s" % (list, str(sys.exc_info())))
		self.startDownloading()

	def removeDownload(self, url):
		tmp = []
		for download in self.downloads:
			if download.url == url:
				download.stop()
			else:
				tmp.append(download)
		del self.downloads
		self.downloads = tmp
		self.removeFromLists(url)

	def removeFromLists(self, url):
		path = config.plugins.RSDownloader.lists_directory.value
		if not path.endswith("/"):
			path = path + "/"
		try:
			file_list = listdir(path)
		except:
			file_list = []
			writeLog("Error while searching for lists: " + str(sys.exc_info()))
		for x in file_list:
			list = path + x
			try:
				f = open(list, "r")
				content = f.read()
				f.close()
				if content.__contains__(url):
					content = content.replace(url, "")
					content = content.replace("\n\n", "\n").replace("\r\r", "\r")
				f = open(list, "w")
				f.write(content)
				f.close()
			except:
				writeLog("Error while removing link from list: " + str(sys.exc_info()))

	def clearFinishedDownload(self, url):
		idx = 0
		for x in self.downloads:
			if x.url == url:
				del self.downloads[idx]
				break
			else:
				idx += 1

	def clearFinishedDownloads(self):
		tmp = []
		for download in self.downloads:
			if download.status != _("Finished"):
				tmp.append(download)
		del self.downloads
		self.downloads = tmp

	def deleteFailedDownloads(self):
		tmp = []
		for download in self.downloads:
			if download.status == _("Failed"):
				self.removeFromLists(download.url)
			else:
				tmp.append(download)
		del self.downloads
		self.downloads = tmp

	def abortAllDownloads(self):
		tmp = []
		for download in self.downloads:
			if download.status == _("Downloading"):
				download.stop()
				download.download = None
				download.downloading = False
				download.progress = 0
				download.size = 0
				download.status = _("Waiting")
			tmp.append(download)
		del self.downloads
		self.downloads = tmp
		self.startDownloading()

	def restartFailedDownloads(self):
		tmp = []
		for download in self.downloads:
			if download.status == _("Failed"):
				download.download = None
				download.downloading = False
				download.progress = 0
				download.size = 0
				download.status = _("Waiting")
			tmp.append(download)
		del self.downloads
		self.downloads = tmp
		self.startDownloading()

rapidshare = RS()

##############################################################################

class ChangedScreen(Screen):
	def __init__(self, session, parent=None):
		Screen.__init__(self, session, parent)
		self.onLayoutFinish.append(self.setScreenTitle)

	def setScreenTitle(self):
		self.setTitle(_("RS Downloader"))

##############################################################################

class ReconnectScriptSelector(ChangedScreen):
	skin = """
		<screen position="center,center" size="560,450" title="RS Downloader">
			<widget name="list" position="0,0" size="560,450" />
		</screen>"""

	def __init__(self, session):
		ChangedScreen.__init__(self, session)
		self["list"] = FileList("/", matchingPattern="(?i)^.*\.(sh)")
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.okClicked, "cancel": self.close}, -1)

	def okClicked(self):
		if self["list"].canDescent():
			self["list"].descent()
		else:
			cur = self["list"].getCurrent()
			if cur:
				self.close("%s/%s"%(self["list"].getCurrentDirectory(), cur[0][0]))

##############################################################################

class RSConfig(ConfigListScreen, ChangedScreen):
	skin = """
		<screen position="center,center" size="560,450" title="RS Downloader">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="0,45" size="560,400" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session):
		ChangedScreen.__init__(self, session)
		
		self["key_green"] = Label(_("Save"))
		
		ConfigListScreen.__init__(self, [
			getConfigListEntry(_("Download in the background:"), config.plugins.RSDownloader.onoff),
			getConfigListEntry(_("Username:"), config.plugins.RSDownloader.username),
			getConfigListEntry(_("Password:"), config.plugins.RSDownloader.password),
			getConfigListEntry(_("Username (netload.in):"), config.plugins.Netload.username),
			getConfigListEntry(_("Password (netload.in):"), config.plugins.Netload.password),
			getConfigListEntry(_("Username (uploaded.to):"), config.plugins.Uploaded.username),
			getConfigListEntry(_("Password (uploaded.to):"), config.plugins.Uploaded.password),
			getConfigListEntry(_("Lists directory:"), config.plugins.RSDownloader.lists_directory),
			getConfigListEntry(_("Downloads directory:"), config.plugins.RSDownloader.downloads_directory),
			getConfigListEntry(_("Ignore download times:"), config.plugins.RSDownloader.ignore_time),
			getConfigListEntry(_("Allow downloading on monday:"), config.plugins.RSDownloader.download_monday),
			getConfigListEntry(_("Allow downloading on tuesday:"), config.plugins.RSDownloader.download_tuesday),
			getConfigListEntry(_("Allow downloading on wednesday:"), config.plugins.RSDownloader.download_wednesday),
			getConfigListEntry(_("Allow downloading on thursday:"), config.plugins.RSDownloader.download_thursday),
			getConfigListEntry(_("Allow downloading on friday:"), config.plugins.RSDownloader.download_friday),
			getConfigListEntry(_("Allow downloading on saturday:"), config.plugins.RSDownloader.download_saturday),
			getConfigListEntry(_("Allow downloading on sunday:"), config.plugins.RSDownloader.download_sunday),
			getConfigListEntry(_("Don't download before:"), config.plugins.RSDownloader.start_time),
			getConfigListEntry(_("Don't download after:"), config.plugins.RSDownloader.end_time),
			getConfigListEntry(_("Maximal downloads:"), config.plugins.RSDownloader.count_downloads),
			getConfigListEntry(_("Take x downloads to list:"), config.plugins.RSDownloader.count_maximal_downloads),
			getConfigListEntry(_("Write log:"), config.plugins.RSDownloader.write_log),
			getConfigListEntry(_("Reconnect type:"), config.plugins.RSDownloader.reconnect_type),
			getConfigListEntry(_("Choose reconnect script:"), config.plugins.RSDownloader.reconnect_script),
			getConfigListEntry(_("Don't reconnect before:"), config.plugins.RSDownloader.reconnect_start_time),
			getConfigListEntry(_("Don't reconnect after:"), config.plugins.RSDownloader.reconnect_end_time),
			getConfigListEntry(_("Restart failed after 10 minutes:"), config.plugins.RSDownloader.autorestart_failed),
			getConfigListEntry(_("Mark files < 1 MB as failed:"), config.plugins.RSDownloader.mark_small_as_failed)])
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {"green": self.save, "cancel": self.exit}, -1)

	def save(self):
		for x in self["config"].list:
			x[1].save()
		self.close()

	def exit(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def keyLeft(self):
		sel = self["config"].getCurrent()[1]
		if sel == config.plugins.RSDownloader.reconnect_script:
			self.reconnectScriptSelector()
		else:
			ConfigListScreen.keyLeft(self)

	def keyRight(self):
		sel = self["config"].getCurrent()[1]
		if sel == config.plugins.RSDownloader.reconnect_script:
			self.reconnectScriptSelector()
		else:
			ConfigListScreen.keyRight(self)

	def reconnectScriptSelector(self):
		self.session.openWithCallback(self.reconnectScriptSelectorCallback, ReconnectScriptSelector)

	def reconnectScriptSelectorCallback(self, callback=None):
		if callback:
			config.plugins.RSDownloader.reconnect_script.value = callback
			self["config"].setList(self["config"].getList())

##############################################################################

class RSSearch(Screen):
	skin = """
		<screen position="center,center" size="560,450" title="Searching... please wait!">
			<widget name="list" position="0,0" size="570,450" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, searchFor):
		Screen.__init__(self, session)
		self.session = session
		
		self.searchFor = searchFor.replace(" ", "%2B")
		self.maxPage = 1
		self.curPage = 1
		self.files = []
		
		self["list"] = MenuList([])
		
		self["actions"] = ActionMap(["OkCancelActions", "InfobarChannelSelection"],
			{
				"historyBack": self.previousPage,
				"historyNext": self.nextPage,
				"ok": self.okClicked,
				"cancel": self.close
			}, -1)
		
		self.onLayoutFinish.append(self.search)

	def okClicked(self):
		if len(self.files) > 0:
			idx = self["list"].getSelectedIndex()
			url = self.files[idx]
			try:
				f = open(("%s/search.txt" % config.plugins.RSDownloader.lists_directory.value).replace("//", "/"), "a")
				f.write("%s\n"%url)
				f.close()
				self.session.open(MessageBox, (_("Added %s to the download-list.") % url), MessageBox.TYPE_INFO)
			except:
				self.session.open(MessageBox, (_("Error while adding %s to the download-list!") % url), MessageBox.TYPE_ERROR)

	def search(self):
		getPage("http://rapidshare-search-engine.com/index-s_submit=Search&sformval=1&s_type=0&what=1&s=%s&start=%d.html"%(self.searchFor, self.curPage)).addCallback(self.searchCallback).addErrback(self.searchError)

	def searchCallback(self, html=""):
		list = []
		files = []
		
		if html.__contains__("Nothing found, sorry."):
			self.session.open(MessageBox, (_("Error while searching http://rapidshare-search-engine.com!\n\nError: Nothing found, sorry.")), MessageBox.TYPE_ERROR)
			self.instance.setTitle(_("Nothing found, sorry."))
		else:
			tmp = html
			while tmp.__contains__("goPg('"):
				idx = tmp.index("goPg('")
				tmp = tmp[idx+6:]
				idx = tmp.index("'")
				pageNumber = tmp[:idx]
				
				try:
					pageNumber = int(pageNumber)
					if pageNumber > self.maxPage:
						self.maxPage = pageNumber
				except:
					pass
				
				self.instance.setTitle(_("Page %d / %d. Push < > to switch the page...")%(self.curPage, self.maxPage))
			
			while html.__contains__('title="Download"'):
				idx = html.index('title="Download"')
				html = html[idx:]
				idx = html.index('value="')
				html = html[idx+7:]
				idx = html.index('"')
				size = html[:idx]
				idx = html.index('http://rapidshare.com/')
				html = html[idx:]
				idx = html.index('"')
				url = html[:idx]
				
				files.append(url) 
				try:
					urllist = url.split("/")
					idx = len(urllist) - 1
					name = urllist[idx]
					list.append("%s - %s"%(size, name))
				except:
					list.append("%s - %s"%(size, url))
		
		self.files = files
		self["list"].setList(list)

	def searchError(self, error=""):
		self.session.open(MessageBox, (_("Error while searching http://rapidshare-search-engine.com!\n\nError: %s")%str(error)), MessageBox.TYPE_ERROR)

	def previousPage(self):
		if self.curPage > 1:
			self.curPage -= 1
			self.instance.setTitle(_("Loading previous page... please wait!"))
			self.search()

	def nextPage(self):
		if self.curPage < self.maxPage:
			self.curPage += 1
			self.instance.setTitle(_("Loading next page... please wait!"))
			self.search()

##############################################################################

class RSLogScreen(ChangedScreen):
	skin = """
		<screen position="center,center" size="560,450" title="RS Downloader">
			<widget name="label" position="0,0" size="560,450" font="Regular;20" />
		</screen>"""

	def __init__(self, session):
		ChangedScreen.__init__(self, session)
		
		try:
			f = open("/tmp/rapidshare.log")
			log = f.read()
			f.close()
		except:
			log = ""
		self["label"] = ScrollLabel(log)
		
		self["actions"] = ActionMap(["WizardActions"],
			{
				"ok": self.close,
				"back": self.close,
				"up": self["label"].pageUp,
				"down": self["label"].pageDown,
				"left": self["label"].pageUp,
				"right": self["label"].pageDown
			}, -1)

##############################################################################

class RSContainerSelector(ChangedScreen):
	skin = """
		<screen position="center,center" size="560,450" title="RS Downloader">
			<widget name="list" position="0,0" size="560,450" />
		</screen>"""

	def __init__(self, session, list):
		ChangedScreen.__init__(self, session)
		self["list"] = MenuList(list)
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.okClicked, "cancel": self.close}, -1)

	def okClicked(self):
		cur = self["list"].getCurrent()
		self.close(cur)

##############################################################################

class UnrarEntry:
	def __init__(self, name, password, package=None):
		self.name = name
		self.password = password
		self.working = False
		self.finishCallback = None
		self.console = None
		self.command = None
		self.package = None
		self.list = ("%s/%s"%(config.plugins.RSDownloader.lists_directory.value, self.name)).replace("//", "/")
		if package is None:
			try:
				f = open(self.list, "r")
				while True:
					line = f.readline()
					if line == '':
						break
					elif line.startswith("http://") and (line.__contains__("part1.rar") or line.__contains__("part01.rar") or line.__contains__("part001.rar")):
						package = line.split("/")[-1]
						package = package.replace("\n", "").replace("\r", "")
						package = ("%s/%s"%(config.plugins.RSDownloader.downloads_directory.value, package)).replace("//", "/")
						break
				f.close()
			except:
				writeLog("Error while reading rar archive from list: " + str(sys.exc_info()))
		if package:
			self.package = package
			if self.password:
				self.command = "unrar -p%s -o+ x %s %s"%(self.password, package, config.plugins.RSDownloader.downloads_directory.value)
			else:
				self.command = "unrar -o+ x %s %s"%(package, config.plugins.RSDownloader.downloads_directory.value)
		else:
			writeLog("Error finding rar-archives in list: " + self.name)

	def startUnrar(self):
		self.working = True
		if not self.console:
			self.console = eConsole()
		self.console.ePopen(self.command, self.unrarDataAvailable)

	def unrarDataAvailable(self, result, retval, extra_args):
		self.working = False
		try:
			fileName = ("%s/%s_unrar.txt"%(config.plugins.RSDownloader.downloads_directory.value, self.name)).replace("//", "/")
			f = open(fileName, "w")
			f.write(result)
			f.close()
		except:
			print "[RS Downloader] Result of unrar:", result
		self.finishCallback(self.name)

	def allDownloaded(self):
		try:
			f = open(self.list, "r")
			content = f.read()
			f.close()
		except:
			content = ""
		if content.__contains__("http://"):
			return False
		else:
			return True

##############################################################################

class Unrar:
	def __init__(self):
		self.list = []
		self.timer = eTimer()
		self.timer.callback.append(self.checkUnrar)
		self.timer.start(30000, 1)
		self.xmlFile = ("%s/unrar.xml"%config.plugins.RSDownloader.lists_directory.value).replace("//", "/")
		
	def addToList(self, name, password, package=None):
		entry = UnrarEntry(name, password, package)
		self.list.append(entry)

	def deleteEntry(self, name):
		idx = 0
		ret = True
		for x in self.list:
			if x.name == name:
				if x.working:
					ret = False
				else:
					del self.list[idx]
					break
			idx += 1
		return ret

	def checkUnrar(self):
		if len(self.list) > 0:
			self.startUnrar()
		else:
			self.timer.start(30000, 1)

	def isWorking(self):
		ret = False
		for x in self.list:
			if x.working:
				ret = True
				break
		return ret

	def getFirstEmptyList(self):
		entry = None
		for x in self.list:
			if (x.allDownloaded() == True):
				entry = x
				break
		return entry

	def startUnrar(self):
		ret = self.isWorking()
		if ret == False:
			entry = self.getFirstEmptyList()
			if entry:
				if entry.command:
					writeLog("Start unpacking: %s"%entry.name)
					entry.finishCallback = self.cleanFinishedEntry
					entry.startUnrar()
				else:
					self.deleteEntry(entry.name)
					self.timer.start(30000, 1)
			else:
				self.timer.start(30000, 1)
		else:
			self.timer.start(30000, 1)

	def cleanFinishedEntry(self, name):
		writeLog("Unpacking finished: %s"%name)
		self.deleteEntry(name)
		self.checkUnrar()

	def decode_charset(self, str, charset):
		try:
			uni = unicode(str, charset, 'strict')
		except:
			uni = str
		return uni

	def loadXml(self):
		if fileExists(self.xmlFile):
			menu = parse(self.xmlFile).getroot()
			for item in menu.findall("entry"):
				name = item.get("name") or None
				password = item.get("password") or None
				package = item.get("package") or None
				if name and password:
					name = self.decode_charset(name, "utf-8")
					password = self.decode_charset(password, "utf-8")
					self.addToList(str(name), str(password), str(package))

	def writeXml(self):
		xml = '<unrar>\n'
		for x in self.list:
			name = self.decode_charset(x.name, "utf-8")
			password = self.decode_charset(x.password, "utf-8")
			xml += '\t<entry name="%s" password="%s" package="%s" />\n'%(name.encode("utf-8"), password.encode("utf-8"), x.package)
		xml += '</unrar>\n'
		try:
			f = open(self.xmlFile, "w")
			f.write(xml)
			f.close()
		except:
			writeLog("Error writing unrar xml file: %s"%self.xmlFile)
unrar = Unrar()

##############################################################################

class UnrarPackageSelector(ChangedScreen):
	skin = """
		<screen position="center,center" size="560,450" title="RS Downloader">
			<widget name="list" position="0,0" size="560,450" />
		</screen>"""

	def __init__(self, session):
		ChangedScreen.__init__(self, session)
		
		self["list"] = MenuList([])
		
		self["actions"] = ActionMap(["OkCancelActions"],
			{
				"ok": self.okClicked,
				"cancel": self.close
			}, -1)
		
		self.onLayoutFinish.append(self.updateList)

	def updateList(self):
		try:
			names = listdir(config.plugins.RSDownloader.lists_directory.value)
		except:
			names = []
		list = []
		for name in names:
			if name.lower().endswith(".txt"):
				added = False
				for x in unrar.list:
					if x.name == name:
						added = True
				if added == False:
					list.append(name)
		list.sort()
		self["list"].setList(list)

	def okClicked(self):
		cur = self["list"].getCurrent()
		if cur:
			self.name = cur
			self.session.openWithCallback(self.okClickedCallback, VirtualKeyBoard, title=_("Enter unrar password:"), text=config.plugins.RSDownloader.unrar_password.value)

	def okClickedCallback(self, callback=None):
		if callback is None:
			callback = ""
		config.plugins.RSDownloader.unrar_password.value = callback
		config.plugins.RSDownloader.unrar_password.save()
		self.close([self.name, callback])

##############################################################################

class UnrarManager(ChangedScreen):
	skin = """
		<screen position="center,center" size="560,450" title="RS Downloader">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="list" position="0,40" size="560,375" scrollbarMode="showNever" />
		</screen>"""

	def __init__(self, session):
		ChangedScreen.__init__(self, session)
		self.session = session
		
		self["key_red"] = Label(_("Delete"))
		self["key_green"] = Label(_("Add"))
		self["list"] = MenuList([])
		
		self["actions"] = ActionMap(["ColorActions", "OkCancelActions"],
			{
				"red": self.delete,
				"green": self.add,
				"cancel": self.close
			}, prio=-1)
		
		self.onLayoutFinish.append(self.updateList)

	def updateList(self):
		list = []
		for x in unrar.list:
			list.append(x.name)
		list.sort()
		self["list"].setList(list)

	def delete(self):
		cur = self["list"].getCurrent()
		if cur:
			ret = unrar.deleteEntry(cur)
			if ret:
				self.updateList()
			else:
				self.session.open(MessageBox, _("Unrar is already working!"), MessageBox.TYPE_ERROR)

	def add(self):
		self.session.openWithCallback(self.addCallback, UnrarPackageSelector)

	def addCallback(self, callback=None):
		if callback:
			unrar.addToList(callback[0], callback[1])
			self.updateList()

##############################################################################

class RSList(MenuList):
	def __init__(self, list):
		MenuList.__init__(self, list, False, eListboxPythonMultiContent)
		self.l.setItemHeight(25)
		self.l.setFont(0, gFont("Regular", 20))

##############################################################################

def RSListEntry(download):
	res = [(download)]
	res.append(MultiContentEntryText(pos=(0, 0), size=(170, 25), font=0, text=download.name))
	res.append(MultiContentEntryText(pos=(175, 0), size=(75, 25), font=0, text="%d%s"%(download.size, "MB"), flags=RT_HALIGN_CENTER))
	res.append(MultiContentEntryPixmapAlphaTest(pos=(260, 9), size=(84, 7), png=LoadPixmap(cached=True, path=resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/progress_bg.png"))))
	res.append(MultiContentEntryPixmapAlphaTest(pos=(260, 10), size=(int(0.84 * download.progress), 5), png=LoadPixmap(cached=True, path=resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/progress_small.png"))))
	res.append(MultiContentEntryText(pos=(360, 0), size=(60, 25), font=0, text="%d%s"%(download.progress, "%"), flags=RT_HALIGN_CENTER))
	res.append(MultiContentEntryText(pos=(420, 0), size=(140, 25), font=0, text=download.status, flags=RT_HALIGN_RIGHT))
	return res

##############################################################################

class RSMain(ChangedScreen):
	skin = """
		<screen position="center,center" size="560,450" title="RS Downloader">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/key_menu.png" position="10,420" size="35,25" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_menu" position="50,422" size="300,25" font="Regular;20" transparent="1" />
			<widget name="list" position="0,40" size="560,375" scrollbarMode="showNever" />
		</screen>"""

	def __init__(self, session):
		ChangedScreen.__init__(self, session)
		self.session = session
		
		self["key_red"] = Label(_("Delete"))
		self["key_green"] = Label(_("Search"))
		self["key_yellow"] = Label(_("Add"))
		self["key_blue"] = Label(_("Config"))
		self["key_menu"] = Label(_("Menu"))
		self["list"] = RSList([])
		
		self.refreshTimer = eTimer()
		self.refreshTimer.callback.append(self.updateList)
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "InfobarMenuActions"],
			{
				"mainMenu": self.menu,
				"cancel": self.close,
				"red": self.delete,
				"green": self.search,
				"yellow": self.add,
				"blue": self.config
			}, prio=-1)
		
		self.onLayoutFinish.append(self.updateList)

	def menu(self):
		list = []
		list.append((_("Delete download"), self.delete))
		list.append((_("Use search engine"), self.search))
		list.append((_("Add downloads from txt files"), self.add))
		list.append((_("Add files from container"), self.addContainer))
		list.append((_("Delete failed downloads"), self.deleteFailed))
		list.append((_("Abort all downloads"), self.abortDownloads))
		list.append((_("Restart failed downloads"), self.restartFailed))
		list.append((_("Clear finished downloads"), self.clearFinished))
		list.append((_("Show log"), self.showLog))
		list.append((_("Delete log"), self.deleteLog))
		if fileExists("/usr/bin/unrar"):
			list.append((_("Open unrar Manager"), self.openUnrarManager))
		else:
			list.append((_("Install unrar"), self.installUnrar))
		list.append((_("Close plugin"), self.close))
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_("Please choose a function..."), list=list)

	def menuCallback(self, callback=None):
		if callback is not None:
			callback[1]()

	def deleteFailed(self):
		rapidshare.deleteFailedDownloads()

	def abortDownloads(self):
		rapidshare.abortAllDownloads()

	def restartFailed(self):
		rapidshare.restartFailedDownloads()

	def clearFinished(self):
		rapidshare.clearFinishedDownloads()

	def showLog(self):
		self.session.open(RSLogScreen)

	def deleteLog(self):
		try:
			remove("/tmp/rapidshare.log")
		except:
			pass

	def openUnrarManager(self):
		self.session.open(UnrarManager)

	def installUnrar(self):
		self.session.open(ConsoleScreen, title=_("Installing unrar..."), cmdlist=["ipkg install http://www.lt-forums.org/ali/downloads/unrar_3.4.3-r0_mipsel.ipk"])

	def updateList(self):
		list = []
		for download in rapidshare.downloads:
			list.append(RSListEntry(download))
		self["list"].setList(list)
		self.refreshTimer.start(2000, 1)

	def delete(self):
		cur = self["list"].getCurrent()
		if cur:
			cur = cur[0]
			if cur.status == _("Finished"):
				rapidshare.clearFinishedDownload(cur.url)
			else:
				self.session.openWithCallback(self.deleteCallback, MessageBox, (_("Delete %s?")%cur.name))

	def deleteCallback(self, callback):
		if callback:
			rapidshare.removeDownload(self["list"].getCurrent()[0].url)
			self.refreshTimer.stop()
			self.updateList()

	def search(self):
		self.session.openWithCallback(self.searchCallback, VirtualKeyBoard, title=_("Search http://rapidshare-search-engine.com for:"))

	def searchCallback(self, callback):
		if callback is not None and callback != "":
			self.session.openWithCallback(self.searchScreenCallback, RSSearch, callback)


	def searchScreenCallback(self):
		self.refreshTimer.stop()
		rapidshare.startDownloading()
		self.updateList()

	def add(self):
		self.refreshTimer.stop()
		rapidshare.startDownloading()
		self.updateList()

	def config(self):
		self.session.openWithCallback(self.configCallback, RSConfig)

	def configCallback(self):
		if config.plugins.RSDownloader.onoff.value:
			rapidshare.startDownloading()
		else:
			for download in rapidshare.downloads:
				if download.downloading:
					download.stop()
		self.updateList()

	def addContainer(self):
		try:
			file_list = listdir(config.plugins.RSDownloader.lists_directory.value)
		except:
			file_list = []
			writeLog("Error while searching for container files: " + str(sys.exc_info()))
		list = []
		for file in file_list:
			if file.lower().endswith(".ccf") or file.lower().endswith(".dlc") or file.lower().endswith(".rsdf"):
				list.append(file)
		list.sort()
		self.session.openWithCallback(self.addContainerCallback, RSContainerSelector, list)

	def addContainerCallback(self, callback=None):
		if callback:
			file = "%s/%s"%(config.plugins.RSDownloader.lists_directory.value, callback)
			file = file.replace("//", "/")
			links = decrypt(file)
			if links:
				try:
					f = open(("%s/%s.txt" % (config.plugins.RSDownloader.lists_directory.value, callback)).replace("//", "/"), "w")
					for link in links:
						if link.endswith(".html"):
							link = link[:-5]
						elif link.endswith(".htm"):
							link = link[:-4]
						f.write("%s\n"%link)
					f.close()
					remove(file)
				except:
					writeLog("Error while writing list file: " + str(sys.exc_info()))
				self.refreshTimer.stop()
				rapidshare.startDownloading()
				self.updateList()
			else:
				self.session.open(MessageBox, (_("Error while decrypting %s!") % callback), MessageBox.TYPE_ERROR)

##############################################################################

def autostart(reason, **kwargs):
	if reason == 0:
		rapidshare.startDownloading()
		unrar.loadXml()
	elif reason == 1:
		unrar.writeXml()

##############################################################################

def main(session, **kwargs):
	session.open(RSMain)

##############################################################################

def Plugins(**kwargs):
	return [
		PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart),
		PluginDescriptor(name=_("RS Downloader"), description=_("Download files from rapidshare"), where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], icon="rs.png", fnc=main)]

