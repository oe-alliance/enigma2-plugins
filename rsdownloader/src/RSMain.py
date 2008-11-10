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
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

##############################################################################

class RSMain(Screen):
	skin = """
		<screen position="200,175" size="320,250" title="RS Downloader">
			<widget name="list" position="10,10" size="300,230" />
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
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
			
			elif selected == (_("Show info...")):
				self.session.open(MessageBox, (_("RS Downloader\nby AliAbdul\n\nThis plugin allows you to download files from rapidshare in the background. You can use this plugin only with a rapidshare-account!")), MessageBox.TYPE_INFO)
