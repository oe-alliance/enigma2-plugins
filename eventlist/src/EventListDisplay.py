# -*- coding: utf-8 -*-
#
# EventListDisplay - Renderer
#
# Coded by Dr.Best (c) 2013
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
from enigma import eCanvas, eRect, gFont
from skin import parseColor, parseFont

class EventListDisplay(Renderer):
	GUI_WIDGET = eCanvas

	def __init__(self):
		Renderer.__init__(self)
		self.backgroundColor = parseColor("#ff000000")
		self.rowHeight = 20
		self.columns = {}
		self.primetimeoffset = 10

	def pull_updates(self):
		if self.instance is None:
			return
		self.instance.clear(self.backgroundColor)
		content = self.source.getContent()
		content_count = len(content)
		primetime = self.source.primetime
		if primetime == 1 and content_count == 1:
			primetime = 0
		y = 0
		a = 1
		for item in content:
			i = 0
			while i < 3:
				if self.columns.has_key(str(i)):
					value = self.columns[str(i)]
					self.instance.writeText(eRect(value[0], y+int((self.rowHeight-value[4])/2), value[1], self.rowHeight), value[2], self.backgroundColor, value[3], item[value[5]], value[6])
				i += 1
			a += 1
			y += self.rowHeight
			if a == content_count and primetime == 1:
				y += self.primetimeoffset

	def changed(self, what):
		self.pull_updates()

	def applySkin(self, desktop, parent):

		attribs = [ ]
		from enigma import eSize

		def parseSize(str):
			x, y = str.split(',')
			return eSize(int(x), int(y))
	
		def parseColumnValue(value):
			x, length, color, fontname, fontheight, align, itemindex = value.split(',')
			return (int(x), int(length), parseColor(color), gFont(fontname,int(fontheight)), int(fontheight), int(itemindex), int(align))

		for (attrib, value) in self.skinAttributes:
			if attrib == "size":
				self.instance.setSize(parseSize(value))
				attribs.append((attrib,value))
			elif attrib == "column0":
				self.columns["0"] = parseColumnValue(value)
			elif attrib == "column1":
				self.columns["1"] = parseColumnValue(value)
			elif attrib == "column2":
				self.columns["2"] = parseColumnValue(value)
			elif attrib == "rowHeight":
				self.rowHeight = int(value)
			elif attrib == "primetimeoffset":
				self.primetimeoffset = int(value)
			elif attrib == "backgroundColor":
				self.backgroundColor = parseColor(value)
				self.instance.clear(self.backgroundColor)
				attribs.append((attrib,value))
			else:
				attribs.append((attrib,value))
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

