from __future__ import print_function

#pragma mark - GUI

#pragma mark Screens
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen

#pragma mark Components
from Components.ActionMap import HelpableActionMap
from Components.AVSwitch import AVSwitch
from Components.Label import Label
from Components.Pixmap import Pixmap, MovingPixmap
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List

#pragma mark Configuration
from Components.config import config

#pragma mark Picasa
from .PicasaApi import PicasaApi

from enigma import ePicLoad, ePythonMessagePump, getDesktop
from collections import deque

try:
	xrange = xrange
except NameError:
	xrange = range

our_print = lambda *args, **kwargs: print("[EcasaGui]", *args, **kwargs)

class EcasaPictureWall(Screen, HelpableScreen):
	PICS_PER_PAGE = 15
	PICS_PER_ROW = 5
	skin = """<screen position="center,center" size="600,380">
		<ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on"/>
		<ePixmap position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on"/>
		<ePixmap position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on"/>
		<ePixmap position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on"/>
		<ePixmap position="565,10" size="35,25" pixmap="skin_default/buttons/key_menu.png" alphatest="on"/>
		<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1"/>
		<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1"/>
		<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1"/>
		<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1"/>
		<widget name="waitingtext" position="100,179" size="400,22" valign="center" halign="center" font="Regular;22"/>
		<widget name="image0"  position="30,50"   size="90,90"/>
		<widget name="image1"  position="140,50"  size="90,90"/>
		<widget name="image2"  position="250,50"  size="90,90"/>
		<widget name="image3"  position="360,50"  size="90,90"/>
		<widget name="image4"  position="470,50"  size="90,90"/>
		<widget name="image5"  position="30,160"  size="90,90"/>
		<widget name="image6"  position="140,160" size="90,90"/>
		<widget name="image7"  position="250,160" size="90,90"/>
		<widget name="image8"  position="360,160" size="90,90"/>
		<widget name="image9"  position="470,160" size="90,90"/>
		<widget name="image10" position="30,270"  size="90,90"/>
		<widget name="image11" position="140,270" size="90,90"/>
		<widget name="image12" position="250,270" size="90,90"/>
		<widget name="image13" position="360,270" size="90,90"/>
		<widget name="image14" position="470,270" size="90,90"/>
		<!-- TODO: find/create :P -->
		<widget name="highlight" position="25,45" size="100,100"/>
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
		for i in xrange(self.PICS_PER_PAGE):
			self['image%d' % i] = Pixmap()
			self['title%d' % i] = StaticText()
		self["highlight"] = MovingPixmap()
		self["waitingtext"] = Label(_("Please wait... Loading list..."))

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
		self.__highlighted = 0

		# thumbnail loader
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.gotPicture)
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((90, 90, sc[0], sc[1], False, 1, '#ff000000')) # TODO: hardcoded size is evil!
		self.currentphoto = None
		self.queue = deque()

	@property
	def highlighted(self):
		return self.__highlighted

	@highlighted.setter
	def highlighted(self, highlighted):
		our_print("setHighlighted", highlighted)
		self.__highlighted = highlighted
		origpos = self['image%d' % highlighted].getPosition()
		# TODO: hardcoded highlight offset is evil :P
		self["highlight"].moveTo(origpos[0]-5, origpos[1]-5, 1)
		self["highlight"].startMoving()

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
		self["waitingtext"].hide()
		self.queue.clear()
		pictures = self.pictures
		for i in xrange(self.PICS_PER_PAGE):
			try:
				our_print("trying to initiate download of idx", i+self.offset)
				self.api.downloadThumbnail(pictures[i+self.offset]).addCallbacks(self.pictureDownloaded, self.pictureDownloadFailed)
			except IndexError:
				# no more pictures
				# TODO: set invalid pic for remaining items
				our_print("no more pictures in setup")
				break

	def up(self):
		highlighted = (self.highlighted - self.PICS_PER_ROW) % self.PICS_PER_PAGE
		our_print("up. before:", self.highlighted, ", after:", highlighted)
		self.highlighted = highlighted
	def down(self):
		highlighted = (self.highlighted + self.PICS_PER_ROW) % self.PICS_PER_PAGE
		our_print("down. before:", self.highlighted, ", after:", highlighted)
		self.highlighted = highlighted
	def left(self):
		highlighted = (self.highlighted - 1) % self.PICS_PER_PAGE
		our_print("left. before:", self.highlighted, ", after:", highlighted)
		self.highlighted = highlighted
	def right(self):
		highlighted = (self.highlighted + 1) % self.PICS_PER_PAGE
		our_print("right. before:", self.highlighted, ", after:", highlighted)
		self.highlighted = highlighted
	def nextPage(self):
		our_print("nextPage")
		offset = self.offset + self.PICS_PER_PAGE
		if offset > len(self.pictures):
			self.offset = 0
		else:
			self.offset = offset
		self.setup()
	def prevPage(self):
		our_print("prevPage")
		offset = self.offset - self.PICS_PER_PAGE
		if offset < 0:
			Len = len(self.pictures)
			self.offset = Len - (Len % self.PICS_PER_PAGE)
		else:
			self.offset = offset
		self.setup()
	def select(self):
		try:
			photo = self.pictures[self.highlighted+self.offset]
		except IndexError:
			our_print("no such picture")
			# TODO: indicate in gui
		else:
			self.session.open(EcasaPicture, photo, api=self.api)

class EcasaOverview(EcasaPictureWall):
	"""Overview and supposed entry point of ecasa. Shows featured pictures on the "EcasaPictureWall"."""
	def __init__(self, session):
		EcasaPictureWall.__init__(self, session)
		self.skinName = ["EcasaOverview", "EcasaPictureWall"]
		thread = EcasaThread(self.api.getFeatured)
		thread.deferred.addCallbacks(self.gotPictures, self.errorPictures)
		thread.start()

	def gotPictures(self, pictures):
		if not self.instance: return
		self.pictures = pictures
		self.setup()

	def errorPictures(self, error):
		if not self.instance: return
		our_print("errorPictures", error)
		# TODO: implement

class EcasaPicture(Screen, HelpableScreen):
	def __init__(self, session, photo, api=None):
		size_w = getDesktop(0).size().width()
		size_h = getDesktop(0).size().height()
		self.skin = """
		<screen position="0,0" size="%d,%d" title="%s" flags="wfNoBorder">
			 <widget name="pixmap" position="0,0" size="%d,%d" backgroundColor="black"/>
		</screen>""" % (size_w,size_h,photo.title.text.encode('utf-8'),size_w,size_h)
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		self.photo = photo

		self['pixmap'] = Pixmap()

		self["pictureActions"] = HelpableActionMap(self, "EcasaPictureActions", {
			"info": (self.info, _("show metadata")),
			"exit": (self.close, _("Close")),
			}, -1)


		try:
			real_w = int(photo.media.content[0].width.text)
			real_h = int(photo.media.content[0].heigth.text)
		except Exception as e:
			our_print("EcasaPicture.__init__: illegal w/h values, using max size!")
			real_w = size_w
			real_h = size_h

		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.gotPicture)
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((real_w, real_h, sc[0], sc[1], False, 1, '#ff000000'))

		# NOTE: no need to start an extra thread for this, twisted is "parallel" enough in this case
		api.downloadPhoto(photo).addCallbacks(self.cbDownload, self.ebDownload)

	def gotPicture(self, picInfo=None):
		our_print("picture decoded")
		ptr = self.picload.getData()
		if ptr is not None:
			self['pixmap'].instance.setPixmap(ptr.__deref__())

	def cbDownload(self, tup):
		if not self.instance: return
		filename, photo = tup
		self.picload.startDecode(filename)

	def ebDownload(self, tup):
		if not self.instance: return
		error, photo = tup
		print("ebDownload", error)

	def info(self):
		our_print("info")

#pragma mark - Thread

import threading
from twisted.internet import defer

class EcasaThread(threading.Thread):
	def __init__(self, fnc):
		threading.Thread.__init__(self)
		self.deferred = defer.Deferred()
		self.__pump = ePythonMessagePump()
		self.__pump.recv_msg.get().append(self.gotThreadMsg)
		self.__asyncFunc = fnc
		self.__result = None
		self.__err = None

	def gotThreadMsg(self, msg):
		if self.__err:
			self.deferred.errback(self.__err)
		else:
			try:
				self.deferred.callback(self.__result)
			except Exception as e:
				self.deferred.errback(e)

	def run(self):
		try:
			self.__result = self.__asyncFunc()
		except Exception as e:
			self.__err = e
		finally:
			self.__pump.send(0)
