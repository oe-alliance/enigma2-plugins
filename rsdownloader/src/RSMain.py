##
## RS Downloader
## by AliAbdul
##
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from os import path as os_path
from RS import rapidshare
from RSConfig import RSConfig, config
from RSDownloadBrowser import RSDownloadBrowser
from RSListBrowser import RSListBrowser
from RSProgress import RSProgress
from RSSearch import RSSearch
from RSTranslation import _, TitleScreen
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Tools.Directories import fileExists

if fileExists("/usr/lib/enigma2/python/Screens/LTKeyBoard.pyc"):
	from Screens.LTKeyBoard import LTKeyBoard
	LT = True
else:
	from Components.Input import Input
	from Screens.InputBox import InputBox
	LT = False

##############################################################################

class RSMain(TitleScreen):
	skin = """
		<screen position="200,165" size="320,270" title="RS Downloader">
			<widget name="list" position="10,10" size="300,250" />
		</screen>"""

	def __init__(self, session, args = None):
		TitleScreen.__init__(self, session)
		self.session = session
		
		self["list"] = MenuList([
			_("Start downloading..."),
			_("Show lists..."),
			_("Show downloads..."),
			_("Show progress..."),
			_("Edit configs..."),
			_("Show status..."),
			_("Show log..."),
			_("Delete log..."),
			_("Use search-engine..."),
			_("Show info...")])
		
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.okClicked, "cancel": self.close}, -1)

	def okClicked(self):
		selected = self["list"].getCurrent()
		if selected is not None:
			if selected == (_("Start downloading...")):
				if not rapidshare.downloading:
					ret = rapidshare.startDownloading()
					if ret:
						self.session.open(MessageBox, _("Started downloading..."), MessageBox.TYPE_INFO)
					else:
						self.session.open(MessageBox, _("Could not start downloading!"), MessageBox.TYPE_ERROR)
				else:
					self.session.open(MessageBox, _("Already downloading!"), MessageBox.TYPE_ERROR)
			
			elif selected == (_("Show lists...")):
				path = config.plugins.RSDownloader.lists_directory.value
				if os_path.exists(path):
					self.session.open(RSListBrowser, path)
				else:
					self.session.open(MessageBox, (_("Couldn't find the directory %s!") % path), MessageBox.TYPE_ERROR)
			
			elif selected == (_("Show downloads...")):
				path = config.plugins.RSDownloader.downloads_directory.value
				if os_path.exists(path):
					self.session.open(RSDownloadBrowser, path)
				else:
					self.session.open(MessageBox, (_("Couldn't find the directory %s!") % path), MessageBox.TYPE_ERROR)
			
			elif selected == (_("Show progress...")):
				self.session.open(RSProgress)
			
			elif selected == (_("Edit configs...")):
				self.session.open(RSConfig)
			
			elif selected == (_("Show status...")):
				if rapidshare.downloading:
					self.session.open(MessageBox, (_("Downloading %s.") % rapidshare.downloading_file), MessageBox.TYPE_INFO)
				else:
					self.session.open(MessageBox, _("Stopped!"), MessageBox.TYPE_INFO)
			
			elif selected == (_("Show log...")):
				self.session.open(Console, "RS Downloader", ["cat /tmp/rapidshare.log"])
			
			elif selected == (_("Delete log...")):
				self.session.open(Console, "RS Downloader", ["rm -f /tmp/rapidshare.log"])
			
			elif selected == (_("Use search-engine...")):
				title = _("Search http://rapidshare-search-engine.com for:")
				if LT:
					self.session.openWithCallback(self.searchCallback, LTKeyBoard, title=title)
				else:
					self.session.openWithCallback(self.searchCallback, InputBox, title=title, text="", maxSize=False, type=Input.TEXT)
			
			elif selected == (_("Show info...")):
				self.session.open(MessageBox, (_("RS Downloader\nby AliAbdul\n\nThis plugin allows you to download files from rapidshare in the background.")), MessageBox.TYPE_INFO)

	def searchCallback(self, callback):
		if callback is not None and callback != "":
			self.session.open(RSSearch, callback)

