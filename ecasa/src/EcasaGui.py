from __future__ import print_function

#pragma mark - GUI

#pragma mark Screens
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen

#pragma mark Components
from Components.ActionMap import HelpableActionMap
from Components.AVSwitch import AVSwitch
from Components.Pixmap import Pixmap, MovingPixmap
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List

#pragma mark Configuration
from Components.config import config

#pragma mark Picasa
from .PicasaApi import PicasaApi

from enigma import ePicLoad
from collections import deque

try:
	xrange = xrange
except NameError:
	xrange = range

our_print = lambda *args, **kwargs: print("[EcasaGui]", *args, **kwargs)

class EcasaPictureWall(Screen, HelpableScreen):
	skin = """<screen position="center,center" size="600,400">
		<ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
		<ePixmap position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
		<ePixmap position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/>
		<ePixmap position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
		<ePixmap position="565,10" size="35,25" pixmap="skin_default/buttons/key_menu.png" alphatest="on"/>
		<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1"/>
		<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1"/>
		<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1"/>
		<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1"/>
		<!-- TODO: check size! -->
		<widget name="image0" position="30,50" size="72,72"/>
		<widget name="image1" position="110,50" size="72,72"/>
		<widget name="image2" position="190,50" size="72,72"/>
		<widget name="image3" position="30,150" size="72,72"/>
		<widget name="image4" position="110,150" size="72,72"/>
		<widget name="image5" position="190,150" size="72,72"/>
		<widget name="image6" position="30,250" size="72,72"/>
		<widget name="image7" position="110,250" size="72,72"/>
		<widget name="image8" position="190,250" size="72,72"/>
		<!-- TODO: find/create :P -->
		<widget name="highlight" position="20,40" size="92,92"/>
		</screen>"""
	def __init__(self, session, api=None):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		if api is None:
			self.api = PicasaApi(
					config.plugins.ecasa.google_username.value,
					config.plugins.ecasa.google_password.value,
					config.plugins.ecasa.cache.value)

		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText()
		self["key_yellow"] = StaticText()
		self["key_blue"] = StaticText()
		for i in xrange(9):
			self['image%d' % i] = Pixmap()
			self['title%d' % i] = StaticText()
		self["highlight"] = MovingPixmap()

		self["overviewActions"] = HelpableActionMap(self, "EcasaOverviewActions", {
			"up": self.up,
			"down": self.down,
			"left": self.left,
			"right": self.right,
			"nextPage": (self.nextPage, _("show next page")),
			"prevPage": (self.prevPage, _("show previous page")),
			"select": self.select,
			"exit":self.close,
			}, -1)

		self.offset = 0
		self.highlighted = 0

		# thumbnail loader
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.gotPicture)
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((72, 72, sc[0], sc[1], False, 1, '#ff000000')) # TODO: hardcoded size is evil!
		self.currentphoto = None
		self.queue = deque()

	def gotPicture(self, picInfo=None):
		our_print("picture decoded")
		ptr = self.picload.getData()
		if ptr is not None:
			idx = self.pictures.index(self.currentphoto)
			realIdx = idx - self.offset
			self['image%d' % realIdx].instance.setPixmap(ptr.__deref__())
		self.currentphoto = None
		self.maybeDecode()

	def maybeDecode(self):
		our_print("maybeDecode")
		if self.currentphoto is not None: return
		our_print("no current photo, checking for queued ones")
		try:
			filename, self.currentphoto = self.queue.pop()
		except IndexError:
			our_print("no queued photos")
			# no more pictures
			pass
		else:
			self.picload.startDecode(filename)

	def pictureDownloaded(self, tup):
		filename, photo = tup
		our_print("pictureDownloaded", filename, photo)
		self.queue.append((filename, photo))
		self.maybeDecode()

	def pictureDownloadFailed(self, tup):
		error, photo = tup
		our_print("pictureDownloadFailed", error, photo)
		# TODO: indicate in gui

	def setup(self):
		our_print("setup")
		self.queue.clear()
		pictures = self.pictures
		for i in xrange(9):
			try:
				our_print("trying to initiate download of idx", i+self.offset)
				self.api.downloadThumbnail(pictures[i+self.offset]).addCallbacks(self.pictureDownloaded, self.pictureDownloadFailed)
			except IndexError:
				# no more pictures
				our_print("no more pictures in setup")
				break

	def up(self):
		our_print("UP")
	def down(self):
		our_print("DOWN")
	def left(self):
		our_print("LEFT")
	def right(self):
		our_print("RIGHT")
	def nextPage(self):
		our_print("NEXT PAGE")
	def prevPage(self):
		our_print("PREV PAGE")
	def select(self):
		our_print("SELECT")

class EcasaOverview(EcasaPictureWall):
	def __init__(self, session):
		EcasaPictureWall.__init__(self, session)
		self.skinName = ["EcasaOverview", "EcasaPictureWall"]
		self.onLayoutFinish.append(self.go)

	def go(self):
		self.onLayoutFinish.remove(self.go)
		self.pictures = self.api.getFeatured()
		self.setup()

