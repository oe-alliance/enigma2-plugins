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

from Components.Renderer.Renderer import Renderer
from enigma import ePixmap
from enigma import BT_SCALE, BT_KEEP_ASPECT_RATIO
from Tools.LoadPixmap import LoadPixmap


class MSNWeatherPixmap(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.iconFileName = ""
		self.pix = None

	GUI_WIDGET = ePixmap

	def postWidgetCreate(self, instance):
		pass

	def disconnectAll(self):
		Renderer.disconnectAll(self)

	def doSuspend(self, suspended):
		if suspended:
			self.changed((self.CHANGED_CLEAR,))
		else:
			self.changed((self.CHANGED_DEFAULT,))

	def updateIcon(self, filename):
		new_IconFileName = filename
		if (self.iconFileName != new_IconFileName):
			self.iconFileName = new_IconFileName
			self.pix = LoadPixmap(self.iconFileName)
			self.instance.setPixmapScale(BT_SCALE | BT_KEEP_ASPECT_RATIO)
			self.instance.setPixmap(self.pix)

	def changed(self, what):
		if what[0] != self.CHANGED_CLEAR:
			if self.instance:
				self.updateIcon(self.source.iconfilename)
		else:
			if self.instance:
				self.updateIcon(None)
