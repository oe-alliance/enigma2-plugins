# mp4porn plugin by AliAbdul
from Plugin import Movie, Plugin
import re
import urllib2

##################################################


class MP4PornMovie(Movie):
	def __init__(self, name, url, thumb):
		Movie.__init__(self, name, url, thumb)

	def getVideoUrl(self):
		try:
			data = urllib2.urlopen(self.url).read()
		except:
			data = ""
		reonecat = re.compile(r'\| <a href="(.+?).m4v"')
		list = reonecat.findall(data)
		if list and len(list) > 0:
			return "%s%s" % (list[0], ".m4v")
		else:
			return None

##################################################


class MP4Porn(Plugin):
	def __init__(self):
		self.moreEntries = True
		Plugin.__init__(self, "mp4porn.mobi", "mp4porn.png")

	def getEntries(self, callback, currPage=1):
		self.currPage = currPage
		self.callback = callback
		self.getPage("http://mp4porn.mobi/page/%d/" % self.currPage)

	def getPageCallback(self, page):
		movies = []
		reonecat = re.compile(r'<div class="post" onclick="location.href=(.+?)"> <div class="thumb"><a href="(.+?)"><img src="(.+?)" width="120" height="90" alt="(.+?)" />', re.DOTALL)
		for unneeded, url, thumb, name in reonecat.findall(page):
			movies.append(MP4PornMovie(name, url, thumb))
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


def getPlugin():
	return MP4Porn()
