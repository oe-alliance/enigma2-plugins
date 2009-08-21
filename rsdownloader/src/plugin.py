##
## RS Downloader
## by AliAbdul
##
##
from base64 import encodestring
from Components.ActionMap import ActionMap
from Components.config import config, ConfigInteger, ConfigText, ConfigYesNo, ConfigClock, ConfigSubsection, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.ScrollLabel import ScrollLabel
from container.decrypt import decrypt
from enigma import eListboxPythonMultiContent, eTimer, gFont, RT_HALIGN_CENTER, RT_HALIGN_RIGHT
from os import environ, listdir, remove
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from time import localtime, sleep, strftime, time
from Tools.Directories import resolveFilename, SCOPE_SKIN_IMAGE, SCOPE_LANGUAGE, SCOPE_PLUGINS
from Tools.Downloader import HTTPProgressDownloader
from Tools.LoadPixmap import LoadPixmap
from twisted.internet import reactor
from twisted.python import failure
from twisted.web.client import getPage
from urlparse import urlparse, urlunparse
import gettext, re, socket, urllib2

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
config.plugins.RSDownloader.count_downloads = ConfigInteger(default=3, limits=(1, 6))
config.plugins.RSDownloader.write_log = ConfigYesNo(default=True)
config.plugins.RSDownloader.reconnect_fritz = ConfigYesNo(default=False)
config.plugins.RSDownloader.autorestart_failed = ConfigYesNo(default=False)

##############################################################################

def localeInit():
	lang = language.getLanguage()
	environ["LANGUAGE"] = lang[:2]
	gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
	gettext.textdomain("enigma2")
	gettext.bindtextdomain("RSDownloader", "%s%s"%(resolveFilename(SCOPE_PLUGINS), "Extensions/RSDownloader/locale/"))

def _(txt):
	t = gettext.dgettext("RSDownloader", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

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
		pass

##############################################################################

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
		
		self.freeDownloadUrl = ""
		self.freeDownloadTimer = eTimer()
		self.freeDownloadTimer.callback.append(self.freeDownloadStart)
		self.checkTimer = eTimer()
		self.checkTimer.callback.append(self.doCheckTimer)
		self.restartFailedTimer = eTimer()
		self.restartFailedTimer.callback.append(self.restartFailedCheck)
		
		self.finishCallbacks = []

	def start(self):
		writeLog("Downloading: %s"%self.url)
		self.downloading = True
		self.progress = 0
		self.size = 0
		username = config.plugins.RSDownloader.username.value
		password = config.plugins.RSDownloader.password.value
		if self.url.__contains__("rapidshare.com") and username == "" and password == "":
			writeLog("Free RS-Download: %s"%self.url)
			self.status = _("Checking")
			if config.plugins.RSDownloader.reconnect_fritz.value:
				reconnect()
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
					writeLog("Free RS-download... must wait %s seconds: %s"%(seconds, self.url))
					self.status = "%s %s"%(_("Waiting"), seconds)
					url = matchGet('"dlf" action="([^"]+)', data)
					if not url:
						self.httpFailed(True, "Failed to get download page url: %s"%self.url)
					else:
						self.freeDownloadUrl = url
						self.freeDownloadTimer.start((int(seconds) + 2) * 1000, 1)
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
			if self.url.__contains__("rapidshare.com"):
				url = self.url.replace("http://", "http://" + username + ":" + password + "@")
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
		if self.progress == 100:
			writeLog("Finished: %s"%self.url)
			self.status = _("Finished")
			self.execFinishCallbacks()

	def httpFinished(self, string=""):
		if string is not None:
			writeLog("Failed: %s"%self.url)
			writeLog("Error: %s"%string)
		self.status = _("Checking")
		self.checkTimer.start(10000, 1)

	def doCheckTimer(self):
		if self.size == 0:
			self.status = _("Failed")
			if config.plugins.RSDownloader.autorestart_failed.value:
				self.restartFailedTimer.start(10000*60, 1)
		elif self.progress == 100:
			self.status = _("Finished")
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
		self.checkTimer.start(10000, 1)

	def getYoutubeDownloadLink(self):
		mrl = None
		html = get(self.url)
		if html != "":
			isHDAvailable = False
			video_id = None
			t = None
			reonecat = re.compile(r'<title>(.+?)</title>', re.DOTALL)
			titles = reonecat.findall(html)
			if titles:
				self.name = titles[0]
				if self.name.startswith("YouTube - "):
					self.name = (self.name[10:]).replace("&amp;", "&")
			if html.__contains__("isHDAvailable = true"):
				isHDAvailable = True
			for line in html.split('\n'):
				if 'swfArgs' in line:
					line = line.strip().split()
					x = 0
					for thing in line:
						if 'video_id' in thing:
							video_id = line[x+1][1:-2]
						elif '"t":' == thing:
							t = line[x+1][1:-2]
						x += 1
			if video_id and t:
				if isHDAvailable == True:
					mrl = "http://www.youtube.com/get_video?video_id=%s&t=%s&fmt=22" % (video_id, t)
				else:
					mrl = "http://www.youtube.com/get_video?video_id=%s&t=%s&fmt=18" % (video_id, t)
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
		return allDone

	def startDownloading(self):
		if self.mayDownload() == True:
			if self.allDownloadsFinished() == True:
				self.readLists()
			downloadCount = 0
			for download in self.downloads:
				if download.downloading == True:
					downloadCount += 1 # Count the downloaded files
			if config.plugins.RSDownloader.username.value == "" and config.plugins.RSDownloader.password.value == "":
				if downloadCount < 1: # Allow one download if without account
					for download in self.downloads:
						if download.downloading == False and download.status.startswith(_("Waiting")):
							download.start() # Start first download in the list
							break
			else:
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
			writeLog("Count of lists: " + str(len(file_list)))
		except:
			file_list = []
			writeLog("Could not find any list!")
		for x in file_list:
			list = path + x
			if list.endswith(".txt"):
				try:
					writeLog("Reading list %s..."%list)
					f = open(list, "r")
					count = 0
					for l in f:
						if l.startswith("http://"):
							if (self.addDownload(l.replace("\n", "").replace("\r", ""))) == True:
								count += 1
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
		for x in file_list:
			list = path + x
			try:
				f = open(list, "r")
				content = f.read()
				f.close()
				for download in self.downloads:
					if download.status == _("Finished") and content.__contains__(download.url):
						content = content.replace(download.url, "")
						content = content.replace("\n\n", "\n").replace("\r\r", "\r")
				f = open(list, "w")
				f.write(content)
				f.close()
			except:
				writeLog("Error while cleaning list %s!"%list)
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
				pass

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
			getConfigListEntry(_("Write log:"), config.plugins.RSDownloader.write_log),
			getConfigListEntry(_("Reconnect fritz.Box before downloading:"), config.plugins.RSDownloader.reconnect_fritz),
			getConfigListEntry(_("Restart failed after 10 minutes:"), config.plugins.RSDownloader.autorestart_failed)])
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {"green": self.save, "cancel": self.exit}, -1)

	def save(self):
		for x in self["config"].list:
			x[1].save()
		self.close()

	def exit(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

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
		#TODO: Add sort list functions
		list.append((_("Delete download"), self.delete))
		list.append((_("Use search engine"), self.search))
		list.append((_("Add downloads from txt files"), self.add))
		list.append((_("Add files from container"), self.addContainer))
		list.append((_("Delete failed downloads"), self.deleteFailed))
		list.append((_("Restart failed downloads"), self.restartFailed))
		list.append((_("Clear finished downloads"), self.clearFinished))
		list.append((_("Show log"), self.showLog))
		list.append((_("Delete log"), self.deleteLog))
		list.append((_("Close plugin"), self.close))
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_("Please choose a function..."), list=list)

	def menuCallback(self, callback=None):
		if callback is not None:
			callback[1]()

	def deleteFailed(self):
		rapidshare.deleteFailedDownloads()

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
			try:
				f = open(("%s/%s.txt" % (config.plugins.RSDownloader.lists_directory.value, callback)).replace("//", "/"), "w")
				for link in links:
					if link.endswith(".html"):
						link = link[:-5]
					elif link.endswith(".htm"):
						link = link[:-4]
					f.write("%s\n"%link)
				f.close()
			except:
				pass
			self.refreshTimer.stop()
			rapidshare.startDownloading()
			self.updateList()

##############################################################################

def autostart(reason, **kwargs):
	if reason == 0:
		rapidshare.startDownloading()

##############################################################################

def main(session, **kwargs):
	session.open(RSMain)

##############################################################################

def Plugins(**kwargs):
	return [
		PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart),
		PluginDescriptor(name=_("RS Downloader"), description=_("Download files from rapidshare"), where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], icon="rs.png", fnc=main)]

