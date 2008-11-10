##
## RS Downloader
## by AliAbdul
##
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from RS import rapidshare
from Screens.Screen import Screen

##############################################################################

class RSProgress(Screen):
	skin = """
		<screen position="80,120" size="560,360" title="RS Downloader">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="list" position="10,45" size="540,300" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		
		self["key_red"] = Label(_("Downloading"))
		self["key_green"] = Label(_("Files"))
		self["key_yellow"] = Label(_("Downloaded"))
		self["key_blue"] = Label(_("Failed"))
		
		self["list"] = MenuList(rapidshare.files)
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"red": self.downloading,
				"green": self.files,
				"yellow": self.downloaded,
				"blue": self.failed,
				"cancel": self.close
			}, -1)

	def downloading(self):
		if rapidshare.downloading_file == "":
			list = []
		else:
			list = [rapidshare.downloading_file]
		self["list"].setList(list)

	def files(self):
		self["list"].setList(rapidshare.files)

	def downloaded(self):
		self["list"].setList(rapidshare.downloaded_files)

	def failed(self):
		self["list"].setList(rapidshare.failed_files)
