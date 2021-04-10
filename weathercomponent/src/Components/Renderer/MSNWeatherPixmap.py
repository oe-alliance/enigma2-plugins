# -*- coding: utf-8 -*-
#
# WeatherPlugin E2
#
# Coded by Dr.Best (c) 2012-2013
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

from Renderer import Renderer
from enigma import ePixmap
from Components.AVSwitch import AVSwitch
from enigma import eEnv, ePicLoad, eRect, eSize, gPixmapPtr


class MSNWeatherPixmap(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.paintIconPixmapCB)
		self.iconFileName = ""

	GUI_WIDGET = ePixmap

	def postWidgetCreate(self, instance):
		for (attrib, value) in self.skinAttributes:
			if attrib == "size":
				x, y = value.split(',')
				self._scaleSize = eSize(int(x), int(y))
				break
		sc = AVSwitch().getFramebufferScale()
		self._aspectRatio = eSize(sc[0], sc[1])
		self.picload.setPara((self._scaleSize.width(), self._scaleSize.height(), sc[0], sc[1], True, 2, '#ff000000'))
		
	def disconnectAll(self):
		self.picload.PictureData.get().remove(self.paintIconPixmapCB)
		self.picload = None
		Renderer.disconnectAll(self)
		
	def paintIconPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr is not None:
			pic_scale_size = eSize()
			# To be added in the future:
			if 'scale' in eSize.__dict__ and self._scaleSize.isValid() and self._aspectRatio.isValid():
				pic_scale_size = ptr.size().scale(self._scaleSize, self._aspectRatio)
			# To be removed in the future:
			elif 'scaleSize' in gPixmapPtr.__dict__:
				pic_scale_size = ptr.scaleSize()
			if pic_scale_size.isValid():
				pic_scale_width = pic_scale_size.width()
				pic_scale_height = pic_scale_size.height()
				dest_rect = eRect(0, 0, pic_scale_width, pic_scale_height)
				self.instance.setScale(1)
				self.instance.setScaleDest(dest_rect)
			else:
				self.instance.setScale(0)
			self.instance.setPixmap(ptr)
		else:
			self.instance.setPixmap(None)
		
	def doSuspend(self, suspended):
		if suspended:
			self.changed((self.CHANGED_CLEAR,))
		else:
			self.changed((self.CHANGED_DEFAULT,))
			
	def updateIcon(self, filename):
		new_IconFileName = filename
		if (self.iconFileName != new_IconFileName):
			self.iconFileName = new_IconFileName
			self.picload.startDecode(self.iconFileName)

	def changed(self, what):
		if what[0] != self.CHANGED_CLEAR:
			if self.instance:
				self.updateIcon(self.source.iconfilename)
		else:
			self.picload.startDecode("")
