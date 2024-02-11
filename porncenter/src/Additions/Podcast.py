from __future__ import print_function
from __future__ import absolute_import
# podcast plugin by AliAbdul
from .Plugin import Movie, Plugin
import re

##################################################


def encodeUrl(url):
	url = url.replace("&amp;", "&")
	url = url.replace("&lt;", "<")
	url = url.replace("&gt;", ">")
	url = url.replace("&#39;", "'")
	url = url.replace("&quot;", '"')
	url = url.replace("&#42;", "*")
	url = url.replace("&#124;", "|")
	url = url.replace("&#039;", "'")
	url = url.replace("&#187;", ">>")
	return url

##################################################


class Podcast(Plugin):
	def __init__(self, name, icon, url):
		self.url = url
		Plugin.__init__(self, name, icon)

	def getEntries(self, callback):
		self.callback = callback
		self.getPage(self.url)

	def getPageCallback(self, page):
		movies = []
		if page.__contains__("</title>"):
			page = page[page.index("</title>") + 8:]
		reonecat = re.compile(r'<title>(.+?)</title>.+?<description>(.+?)</description>.+?<enclosure(.+?)/>.+?', re.DOTALL)
		for title, description, info in reonecat.findall(page):
			if title.startswith("<![CDATA["):
				title = title[9:]
			if title.endswith("]]>"):
				title = title[:-3]
			url = None
			thumb = None
			if info.__contains__('url="'):
				idx = info.index('url="')
				url = info[idx + 5:]
				idx = url.index('"')
				url = url[:idx]
			if description.__contains__('img src="'):
				idx = description.index('img src="')
				thumb = description[idx + 9:]
				idx = thumb.index('"')
				thumb = thumb[:idx]
			if url:
				movies.append(Movie(encodeUrl(title), url, thumb))
		self.callback(movies)

	def getPageError(self, error=None):
		if error:
			print(error)
