##
## RS Downloader
## by AliAbdul
##
from enigma import eTimer
from FritzReconnect import reconnect
from os import listdir
from RSConfig import config
from RSDownloader import downloadPage, GET, POST, matchGet
from RSLog import writeLog
from time import localtime, sleep
from Tools.Directories import fileExists

##############################################################################

class RS:
	def __init__(self):
		self.files = []
		self.downloaded_files = []
		self.failed_files = []
		self.downloading_file = ""
		
		self.downloading = False
		
		self.downloadTimer = eTimer()
		self.downloadTimer.timeout.get().append(self.download)
		self.freeDownloadTimer = eTimer()
		self.freeDownloadTimer.timeout.get().append(self.freeDownload)
		self.reloadTimer = eTimer()
		self.reloadTimer.timeout.get().append(self.startDownloading)

	def addFile(self, file):
		writeLog("Adding %s to download-list..." % file)
		
		if self.files.__contains__(file):
			writeLog("File %s is already in the download-list!" % file)
		
		elif self.downloaded_files.__contains__(file):
			writeLog("File %s already downloaded!" % file)
		
		elif self.downloading_file == file:
			writeLog("Already downloading %s!" % file)
		
		else:
			self.files.append(file)
			writeLog("Added %s to the downloads." % file)

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
			try:
				writeLog("Reading list %s..." % list)
				
				f = open(list, "r")
				for l in f:
					if l.startswith("http://"):
						self.addFile(l.replace("\n", "").replace("\r", ""))
				f.close()
			except:
				writeLog("Error while reading list %s!" % list)

	def startDownloading(self):
		self.reloadTimer.stop()
		
		mayDownload = self.mayDownload()
		if mayDownload:
			self.downloading = True
			writeLog("Starting downloads...")
			self.readLists()
			self.downloadTimer.start(1, 1)
			return True
		else:
			self.reloadTimer.start(5 * 60 * 1000, 1)
			return False

	def download(self):
		if len(self.files) > 0:
			writeLog("Getting next file...")
			self.downloading_file = self.files[0]
			del self.files[0]
			writeLog("Downloading file %s..." % self.downloading_file)
			
			username = config.plugins.RSDownloader.username.value
			password = config.plugins.RSDownloader.password.value
			freeRsDownload = False
			if username != "" and password != "":
				downloading_file = self.downloading_file.replace("http://", "http://" + username + ":" + password + "@")
			else:
				downloading_file = self.downloading_file
				if downloading_file.startswith("http://rapidshare.com"):
					freeRsDownload = True
			
			path = config.plugins.RSDownloader.downloads_directory.value
			if not path.endswith("/"):
				path = path + "/"
			
			try:
				list = downloading_file.split("/")
				file = path + list[(len(list)-2)] + "_" + list[(len(list)-1)]
				file = file.replace(".html", "")
			except:
				file = downloading_file.replace(".html", "").replace("http://", "")
			writeLog("Local file: " + file)
			
			if fileExists(file):
				writeLog("File %s already exists! Downloading next one...")
				self.downloadTimer.start(1, 1)
			else:
				if freeRsDownload:
					if config.plugins.RSDownloader.reconnect_fritz.value == True:
						reconnect()
						sleep(3)
					data = GET(downloading_file)
					url = matchGet('<form[^>]+action="([^"]+)', data)
					if not url:
						self.downloadError("Failed to get download page url")
					else:
						data = POST(url, "dl.start=Free")
						seconds = matchGet('var c=([0-9]+)', data)
						if not seconds:
							self.downloadError("Failed to get download page url")
						else:
							writeLog("Free RS-download... must wait %s seconds!" % seconds)
							url = matchGet('"dlf" action="([^"]+)', data)
							if not url:
								self.downloadError("Failed to get download page url")
							else:
								self.freeDownloadUrl = url
								self.freeDownloadFile = file
								self.freeDownloadTimer.start((int(seconds) + 2) * 1000, 1)
				else:
					downloadPage(downloading_file, file).addCallback(self.downloadCallback).addErrback(self.downloadError)
		else:
			self.downloading_file = ""
			self.downloading = False
			writeLog("Empty list... everything done?")
			
			self.reloadTimer.start(5 * 60 * 1000, 1)

	def freeDownload(self):
		downloadPage(self.freeDownloadUrl, self.freeDownloadFile).addCallback(self.downloadCallback).addErrback(self.downloadError)

	def downloadCallback(self, callback = None):
		writeLog("File %s downloaded." % self.downloading_file)
		
		self.cleanLists(self.downloading_file)
		
		self.downloaded_files.append(self.downloading_file)
		self.downloadTimer.start(1, 1)

	def downloadError(self, error = None):
		if error is not None:
			writeLog("Error while downloading: " + str(error))
		
		self.failed_files.append(self.downloading_file)
		self.downloadTimer.start(1, 1)

	def cleanLists(self, file):
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
				
				if content.__contains__(file):
					content = content.replace(file, "")
					content = content.replace("\n\n", "\n").replace("\r\r", "\r")
					
					f = open(list, "w")
					f.write(content)
					f.close()
			except:
				writeLog("Error while cleaning list %s!" % list)

	def mayDownload(self):
		start = config.plugins.RSDownloader.start_time.value
		end = config.plugins.RSDownloader.end_time.value
		t = localtime()
		
		#print "====>Start:", str(start)
		#print "====>End:", str(end)
		#print "====>Now:", str(t)
		
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
		elif hour_now > hour_start and hour_now < hour_end: # Same day...
			return True
		elif hour_now == hour_start and minute_now > minute_start: # Same day, same start-hour...
			return True
		elif hour_now == hour_end and minute_now < minute_end: # Same day, same end-hour...
			return True
		
		return False

rapidshare = RS()
