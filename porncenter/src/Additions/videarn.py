from __future__ import print_function
from __future__ import absolute_import
# videarn plugin by AliAbdul
from .Plugin import Movie, Plugin
import re
from six.moves.urllib.request import urlopen

##################################################

class VidearnMovie(Movie):
	def __init__(self, name, url, thumb):
		Movie.__init__(self, name, url, thumb)

	def getVideoUrl(self):
		try:
			data = urlopen(self.url).read()
		except:
			data = ""
		reonecat = re.compile(r"<source src='(.+?)' type='video/mp4;'>")
		list = reonecat.findall(data)
		if list and len(list) > 0:
			return list[0]
		else:
			return None

##################################################

class VidearnSub(Plugin):
	def __init__(self, name, url):
		self.url = url
		self.moreEntries = True
		Plugin.__init__(self, name, "videarn.png")

	def getEntries(self, callback, currPage=1):
		self.currPage = currPage
		self.callback = callback
		self.getPage("http://videarn.com/%s&page=%d" % (self.url, self.currPage))

	def getPageCallback(self, page):
		movies = []
		reonecat = re.compile(r'<div class="gal">(.+?)</font></div></div></div>', re.DOTALL)
		divs = reonecat.findall(page)
		for div in divs:
			reonecat = re.compile(r'<a href="(.+?)".+?<img src="(.+?)".+?class="galtitle">(.+?)</a>', re.DOTALL)
			for url, thumb, name in reonecat.findall(div):
				movies.append(VidearnMovie(name, "http://videarn.com/"+url, thumb))
		self.callback(movies)

	def getMoreEntries(self):
		if self.moreEntries:
			self.getEntries(self.callback, self.currPage+1)

	def getPageError(self, error=None):
		if error and self.currPage == 1:
			print("[%s] Error: %s" % (self.name, error))
		else:
			self.moreEntries = False

##################################################

class Videarn(Plugin):
	def __init__(self):
		Plugin.__init__(self, "videarn.com", "videarn.png")

	def getEntries(self, callback):
		self.callback = callback
		self.getPage("http://videarn.com")

	def getPageCallback(self, page):
		plugins = []
		start = "<span>Browse Videos</span>"
		end = "</div>"
		if start in page and end in page:
			page = page[page.index(start):]
			page = page[:page.index(end)]
			reonecat = re.compile(r'<a href="(.+?)">(.+?)</a>', re.DOTALL)
			for url, name in reonecat.findall(page):
				plugins.append(VidearnSub("videarn.com - "+name, url))
		self.callback(plugins)

	def getPageError(self, error=None):
		if error:
			print("[%s] Error: %s" % (self.name, error))

##################################################

def getPlugin():
	return Videarn()
