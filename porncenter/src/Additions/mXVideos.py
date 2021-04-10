# mXVideos plugin by AliAbdul
from Plugin import Movie, Plugin
import re
import urllib2

##################################################

class mXVideosMovie(Movie):
	def __init__(self, name, url, thumb):
		Movie.__init__(self, name, url, thumb)

	def getVideoUrl(self):
		try:
			data = urllib2.urlopen(self.url).read()
		except:
			data = ""
		reonecat = re.compile(r'Watch Video: <a href="(.+?)">MP4</a>')
		list = reonecat.findall(data)
		if list and len(list) > 0:
			return "http://m.xvideos.com" + list[0]
		else:
			return None

##################################################

class mXVideosSub(Plugin):
	def __init__(self, name, url):
		self.url = url
		self.moreEntries = True
		Plugin.__init__(self, name, "mXVideos.png")

	def getEntries(self, callback, currPage=1):
		self.currPage = currPage
		self.callback = callback
		self.getPage("http://m.xvideos.com%s/page/%d" % (self.url, self.currPage))

	def getPageCallback(self, page):
		movies = []
		reonecat = re.compile(r'src="(.+?)" /></a><div class="scene_title"><a href="(.+?)"> (.+?)</a></div></div>', re.DOTALL)
		for thumb, url, name in reonecat.findall(page):
			movies.append(mXVideosMovie(name, "http://m.xvideos.com" + url, thumb))
		self.callback(movies)

	def getMoreEntries(self):
		if self.moreEntries:
			self.getEntries(self.callback, self.currPage + 1)

	def getPageError(self, error=None):
		if error and self.currPage == 1:
			print "[%s] Error: %s" % (self.name, error)
		else:
			self.moreEntries = False

##################################################

class mXVideos(Plugin):
	def __init__(self):
		Plugin.__init__(self, "mXVideos", "mXVideos.png")

	def getEntries(self, callback):
		self.callback = callback
		self.getPage("http://m.xvideos.com/tag/browse")

	def getPageCallback(self, page):
		plugins = []
		idx = 0
		reonecat = re.compile(r'<a href="(.+?)">(.+?)</a><br />', re.DOTALL)
		for url, name in reonecat.findall(page):
			if idx == 0:
				idx += 1
				name = "Amateur"
			plugins.append(mXVideosSub("mXVideos - " + name, url))
		if len(plugins):
			del plugins[-1]
		self.callback(plugins)

	def getPageError(self, error=None):
		if error:
			print "[%s] Error: %s" % (self.name, error)

##################################################

def getPlugin():
	return mXVideos()
