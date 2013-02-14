#
# InternetRadio E2
#
# Coded by Dr.Best (c) 2012
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Multimedia GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Multimedia GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Multimedia GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#

from enigma import ePicLoad
from Components.Pixmap import Pixmap

class InternetRadioCover(Pixmap):
	def __init__(self, callback = None):
		Pixmap.__init__(self)
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.paintIconPixmapCB)
		self.callback = callback
		self.picloaded = False
		self.showPic = False

	def onShow(self):
		Pixmap.onShow(self)
		if self.instance.size().width() > 0:
			self.picload.setPara((self.instance.size().width(), self.instance.size().height(), 1, 1, False, 1, "#00000000"))
			self.showPic = True
	def paintIconPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if self.showPic and ptr != None:
			self.instance.setPixmap(ptr.__deref__())
			self.picloaded = True
		if self.callback is not None:
			self.callback()

	def updateIcon(self, filename):
		self.picloaded = False
		if self.showPic:
			self.picload.startDecode(filename)

	def setPicloaded(self, value):
		self.picloaded = value
		
	def getPicloaded(self):
		return self.picloaded
		
