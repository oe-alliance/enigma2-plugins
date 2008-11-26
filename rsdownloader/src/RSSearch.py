##
## RS Downloader
## by AliAbdul
##
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from RSConfig import config
from RSTranslation import _, TitleScreen
from Screens.MessageBox import MessageBox
from twisted.web.client import getPage

##############################################################################

class RSSearch(TitleScreen):
	skin = """
		<screen position="75,75" size="570,425" title="Searching... please wait!">
			<widget name="list" position="0,0" size="570,425" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, searchFor):
		TitleScreen.__init__(self, session)
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
			list = ("%s/search.txt" % config.plugins.RSDownloader.lists_directory.value).replace("//", "/")
			
			try:
				f = open(list, "r")
				content = f.read()
				f.close()
				
				if not content.endswith("\n"):
					content += "\n"
			except:
				content = ""
			
			try:
				f = open(list, "w")
				f.write("%s%s\n" % (content, url))
				f.close()
				self.session.open(MessageBox, (_("Added %s to the download-list.") % url), MessageBox.TYPE_INFO)
			except:
				self.session.open(MessageBox, (_("Error while adding %s to the download-list!") % url), MessageBox.TYPE_ERROR)

	def search(self):
		getPage("http://rapidshare-search-engine.com/index-s_submit=Search&sformval=1&s_type=0&what=1&s=%s&start=%d.html" % (self.searchFor, self.curPage)).addCallback(self.searchCallback).addErrback(self.searchError)

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
				
				self.instance.setTitle(_("Page %d / %d. Push < > to switch the page...") % (self.curPage, self.maxPage))
			
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
					list.append("%s - %s" % (size, name))
				except:
					list.append("%s - %s" % (size, url))
		
		self.files = files
		self["list"].setList(list)

	def searchError(self, error=""):
		self.session.open(MessageBox, (_("Error while searching http://rapidshare-search-engine.com!\n\nError: %s") % str(error)), MessageBox.TYPE_ERROR)

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

