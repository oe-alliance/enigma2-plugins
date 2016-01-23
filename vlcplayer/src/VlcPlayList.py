# -*- coding: ISO-8859-1 -*-
#===============================================================================
# VLC Player Plugin by A. Latsch 2007
#                   modified by Volker Christian 2008
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

from enigma import eListboxPythonMultiContent, RT_HALIGN_LEFT, gFont

from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import SCOPE_SKIN_IMAGE, resolveFilename
from Components.MenuList import MenuList

from skin import parseFont

class VlcPlayList(MenuList):
	def __init__(self, getPlaylistEntriesCB):
		MenuList.__init__(self, list, False, eListboxPythonMultiContent)
		self.font = gFont("Regular", 18)
		self.l.setFont(0, self.font)
		self.l.setItemHeight(23)
		self.l.setBuildFunc(self.buildListboxEntry)
		self.getPlaylistEntriesCB = getPlaylistEntriesCB

	def applySkin(self, desktop, parent):
		attribs = [ ]
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "font":
					self.font = parseFont(value, ((1,1),(1,1)))
					self.l.setFont(0, self.font)
				elif attrib == "itemHeight":
					self.l.setItemHeight(int(value))
				else:
					attribs.append((attrib, value))
			self.skinAttributes = attribs
		return MenuList.applySkin(self, desktop, parent)


	def buildListboxEntry(self, name, path):
		size = self.l.getItemSize()
		height = size.height()
		res = [
			(path, name),
			(eListboxPythonMultiContent.TYPE_TEXT, height + 15, 0, size.width() - height - 15, height, 0, RT_HALIGN_LEFT, name)
		]

		png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "extensions/movie.png"))

		if png is not None:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 0, height, height, png))

		return res

	def update(self):
		files = self.getPlaylistEntriesCB()
		fileEntries = []
		if files is not None:
			for file in files:
				name, path = file
				fileEntries.append((name, path))
			fileEntries.sort(cmp = lambda x, y: cmp(x[1][7], y[1][7]))
		self.list = fileEntries
		self.l.setList(self.list)
		self.moveToIndex(0)

	def activate(self):
		cur = self.getCurrent()
		if cur is not None:
			return cur
		return None, None

	def getNextFile(self):
		i = self.getSelectedIndex() + 1
		if i < len(self.list):
			self.moveToIndex(i)
			return self.getCurrent()
		return None, None

	def getPrevFile(self):
		i = self.getSelectedIndex() - 1
		if i < len(self.list):
			self.moveToIndex(i)
			return self.getCurrent()
		return None, None

