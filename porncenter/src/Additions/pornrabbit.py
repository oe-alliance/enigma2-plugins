from __future__ import print_function
# pornrabbit plugin by AliAbdul
from Plugin import Movie, Plugin
import re, urllib2

##################################################

class PornRabbitMovie(Movie):
	def __init__(self, name, url, thumb):
		Movie.__init__(self, name, url, thumb)

	def getVideoUrl(self):
		try:
			data = urllib2.urlopen(self.url).read()
		except:
			data = ""
		reonecat = re.compile(r'<span class="download"><a href="(.+?).mp4"')
		list = reonecat.findall(data)
		if list and len(list) > 0:
			return list[0]+".mp4"
		else:
			return None

##################################################

class PornRabbitSub(Plugin):
	def __init__(self, name, url):
		self.url = url
		self.moreEntries = True
		Plugin.__init__(self, name, "pornrabbit.png")

	def getEntries(self, callback, currPage=1):
		self.currPage = currPage
		self.callback = callback
		self.getPage("http://www.pornrabbit.com%spage%d.html" % (self.url, self.currPage))

	def getDetails(self, div):
		name = None
		url = None
		thumb = None
		reonecat = re.compile(r'<img src="(.+?)"(.+?)<h3>(.+?)</h3>(.+?)class="link"><a href="(.+?)"><b>Play', re.DOTALL)
		for t, x1, n, x2, u in reonecat.findall(div):
			name = n
			thumb = t
			url = "http://www.pornrabbit.com"+u
		return (name, url, thumb)

	def getPageCallback(self, page):
		movies = []
		tmps = []
		if '<div class="video">' in page:
			while '<div class="video">' in page:
				idx = page.index('<div class="video">')
				page = page[idx:]
				idx = page.index('</div>')
				tmps.append(page[:idx])
				page = page[idx:]
		for tmp in tmps:
			(name, url, thumb) = self.getDetails(tmp)
			if name and url and thumb:
				movies.append(PornRabbitMovie(name, url, thumb))
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

class PornRabbit(Plugin):
	def __init__(self):
		Plugin.__init__(self, "Porn Rabbit", "pornrabbit.png")

	def getEntries(self, callback):
		self.callback = callback
		self.getPage("http://www.pornrabbit.com/category.html")

	def getDetails(self, div):
		name = None
		url = None
		reonecat = re.compile(r'<h3>(.+?)<span class(.+?)<a href="(.+?)"><b>', re.DOTALL)
		for n, x, u in reonecat.findall(div):
			name = n
			if len(u) > 10:
				url = u[:-10]
		return (name, url)

	def getPageCallback(self, page):
		plugins = []
		reonecat = re.compile(r'<div class="categ">(.+?)</div>', re.DOTALL)
		for tmp in reonecat.findall(page):
			(name, url) = self.getDetails(tmp)
			if name and url:
				plugins.append(PornRabbitSub("Porn Rabbit - " + name, url))
		self.callback(plugins)

	def getPageError(self, error=None):
		if error: print("[%s] Error: %s" % (self.name, error))

##################################################

def getPlugin():
	return PornRabbit()
