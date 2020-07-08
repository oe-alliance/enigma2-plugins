from __future__ import print_function
# PornCenter by AliAbdul
from Components.AVSwitch import AVSwitch
from enigma import ePicLoad, eTimer
from os import listdir, remove
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.Import import my_import
from Tools.LoadPixmap import LoadPixmap
from twisted.web.client import downloadPage, getPage
from six.moves.urllib.request import Request, urlopen
import six
##################################################

class Cache:
	def __init__(self):
		self.sc = AVSwitch().getFramebufferScale()
		self.idx = -1
		self.finishCallback = None
		self.finishCallbackTimer = eTimer()
		self.finishCallbackTimer.callback.append(self.callback)
		self.oldService = None
		self.session = None

	def getIndex(self):
		self.idx += 1
		return self.idx

	def callback(self):
		if self.finishCallback:
			self.finishCallback()

	def startCallbackTimer(self):
		self.finishCallbackTimer.stop()
		self.finishCallbackTimer.start(5000, 1)
cache = Cache()

##################################################

class Movie:
	def __init__(self, name, url, thumb=None):
		self.type = "Movie"
		self.name = name
		self.url = url
		self.thumb = None
		if thumb:
			try:
				req = Request(thumb)
				url_handle = urlopen(req)
				headers = url_handle.info()
				contentType = headers.getheader("content-type")
			except:
				contentType = None
			if contentType:
				if 'image/jpeg' in contentType:
					self.thumbnailFile = "/tmp/"+str(cache.getIndex())+".jpg"
				elif 'image/png' in contentType:
					self.thumbnailFile = "/tmp/"+str(cache.getIndex())+".png"
				else:
					self.thumbnailFile = None
			else:
				self.thumbnailFile = None
			if self.thumbnailFile:
				downloadPage(six.ensure_binary(thumb), self.thumbnailFile).addCallback(self.decodeThumbnail).addErrback(self.error)

	def error(self, error=None):
		if error: print(error)

	def decodeThumbnail(self, str=None):
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.decodeThumbnailFinished)
		self.picload.setPara((150, 75, cache.sc[0], cache.sc[1], False, 1, "#00000000"))
		self.picload.startDecode(self.thumbnailFile)

	def decodeThumbnailFinished(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr:
			self.thumb = ptr
		remove(self.thumbnailFile)
		del self.picload
		cache.startCallbackTimer()

	def getVideoUrl(self):
		return self.url

##################################################

class Plugin:
	def __init__(self, name, thumb):
		self.type = "Plugin"
		self.name = name
		self.thumb = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS)+"/Extensions/PornCenter/Additions/"+thumb)
		self.callback = None

	def getName(self):
		return self.name

	def getEntries(self, callback):
		pass

	def getMoreEntries(self):
		pass

	def getPage(self, url):
		getPage(six.ensure_binary(url)).addCallback(self.getPageCallback).addErrback(self.getPageError)

	def getPageCallback(self, page):
		pass

	def getPageError(self, error=None):
		if error:
			print("[%s] Error: %s" % (self.name, error))

##################################################

def getPlugins():
	try:
		files = sorted(listdir(resolveFilename(SCOPE_PLUGINS)+"/Extensions/PornCenter/Additions"))
	except Exception as exc:
		print("[PornCenter] failed to search for plugins:", exc)
		files = []
	plugins = []
	for file in files:
		if file.endswith(".py") and not file in ["__init__.py", "Plugin.py", "Podcast.py"]:
			try:
				plugin = my_import('.'.join(["Plugins", "Extensions", "PornCenter", "Additions", file[:-3]]))
				if "getPlugin" not in plugin.__dict__:
					print("Plugin %s doesn't have 'getPlugin'-call." % file)
					continue
				p = plugin.getPlugin()
				if p:
					plugins.append(p)
			except Exception as exc:
				print("Plugin %s failed to load: %s" % (file, exc))
				continue
	return plugins
