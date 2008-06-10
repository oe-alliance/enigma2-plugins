# -*- coding: ISO-8859-1 -*-
#===============================================================================
# VLC Player Plugin by A. Lätsch 2007
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


def VlcPlayListEntry(name, path):
	res = [ path ]
	res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 470, 20, 0, RT_HALIGN_LEFT, name))

	png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "extensions/movie.png"))

	if png is not None:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 2, 20, 20, png))

	return res


class VlcPlayList(MenuList):
	def __init__(self, server, getPlaylistEntriesCB):
		MenuList.__init__(self, list, False, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 18))
		self.l.setItemHeight(23)
		self.server = server
		self.getPlaylistEntriesCB = getPlaylistEntriesCB

	def update(self):
		files = self.getPlaylistEntriesCB()
		fileEntries = []
		if files is not None:
			for file in files:
				[name, path] = file
				fileEntries.append(VlcPlayListEntry(name, path))
			fileEntries.sort(cmp = lambda x, y: cmp(x[1][7], y[1][7]))
		self.list = fileEntries
		self.l.setList(self.list)
		self.moveToIndex(0)

	def activate(self):
		if self.getCurrent() is not None:
			ret = self.getCurrent()[0], self.getCurrent()[1][7]
		return ret

	def getNextFile(self):
		i = self.getSelectedIndex() + 1
		if i < len(self.list):
			self.moveToIndex(i)
			return self.getCurrent()[0], self.getCurrent()[1][7]
		return None, None

	def getPrevFile(self):
		i = self.getSelectedIndex() - 1
		if i < len(self.list):
			self.moveToIndex(i)
			return self.getCurrent()[0], self.getCurrent()[1][7]
		return None, None
