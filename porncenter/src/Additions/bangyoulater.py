# bangyoulater plugin by AliAbdul
from Plugin import Movie, Plugin
import re
import urllib2

##################################################

class bangYouLaterSub(Plugin):
	def __init__(self, name, url):
		self.url = url
		self.moreEntries = True
		Plugin.__init__(self, name, "bangyoulater.png")

	def getEntries(self, callback, currPage=1):
		self.currPage = currPage
		self.callback = callback
		self.getPage("%s/%d" % (self.url, self.currPage))

	def getPageCallback(self, page):
		movies = []
		reonecat = re.compile(r'<div class="mobile_item">(.+?)</td>', re.DOTALL)
		for div in reonecat.findall(page):
			reonecat = re.compile(r'<a href="/player.php(.+?)"><img src="(.+?)" /></a>.+?margin-top: 8px;">(.+?)</div>', re.DOTALL)
			for url, thumb, name in reonecat.findall(div):
				movies.append(Movie(name, "http://stream.bangyoulater.com/"+url[3:]+"/mobile.mp4", thumb))
		self.callback(movies)

	def getMoreEntries(self):
		if self.moreEntries:
			self.getEntries(self.callback, self.currPage+1)

	def getPageError(self, error=None):
		if error and self.currPage == 1:
			print "[%s] Error: %s" % (self.name, error)
		else:
			self.moreEntries = False

##################################################

class bangYouLater(Plugin):
	def __init__(self):
		Plugin.__init__(self, "Bang You Later", "bangyoulater.png")

	def getEntries(self, callback):
		self.callback = callback
		self.getPage("http://mobile.bangyoulater.com")

	def getPageCallback(self, page):
		plugins = []
		if 'Most Discussed' in page:
			page = page[page.index('Most Discussed'):]
		reonecat = re.compile(r'<option value="(.+?)">(.+?)</option>', re.DOTALL)
		for cat, name in reonecat.findall(page):
			plugins.append(bangYouLaterSub("Bang You Later - "+name, "http://mobile.bangyoulater.com/?cat="+cat))
		self.callback(plugins)

	def getPageError(self, error=None):
		if error: print "[%s] Error: %s" % (self.name, error)

##################################################

def getPlugin():
	return bangYouLater()
