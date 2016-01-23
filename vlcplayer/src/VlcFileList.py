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

import re

from enigma import eListboxPythonMultiContent, RT_HALIGN_LEFT, gFont
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import SCOPE_SKIN_IMAGE, SCOPE_PLUGINS, resolveFilename
from Components.MenuList import MenuList

from pyexpat import ExpatError

from skin import parseFont

MEDIA_EXTENSIONS = {
		"mp3": "music",
		"wav": "music",
		"ogg": "music",
		"ts": "movie",
		"avi": "movie",
		"mpg": "movie",
		"mpeg": "movie",
		"wmv": "movie",
		"mov": "movie",
		"iso": "movie",
		"mkv": "movie",
		"flv": "movie"
	}

PLAYLIST_EXTENSIONS = {
		"m3u": "playlist.png",
		"pls": "playlist.png",
		"xspf": "playlist.png",
	}

class VlcFileList(MenuList):
	def __init__(self, getFilesAndDirsCB, baseDir, matchingPattern):
		MenuList.__init__(self, list, False, eListboxPythonMultiContent)
		self.font = gFont("Regular", 18)
		self.l.setFont(0, self.font)
		self.l.setItemHeight(23)
		self.l.setBuildFunc(self.buildListboxEntry)
		self.currentDirectory = baseDir
		self.getFilesAndDirsCB = getFilesAndDirsCB
		self.changeRegex(matchingPattern)

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

	def buildListboxEntry(self, path, isDir, name):
		size = self.l.getItemSize()
		height = size.height()
		res = [
			(path, isDir, name),
			(eListboxPythonMultiContent.TYPE_TEXT, height + 15, 0, size.width() - height - 15, height, 0, RT_HALIGN_LEFT, name)
		]

		if isDir:
			png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "extensions/directory.png"))
		else:
			extension = name.split('.')
			extension = extension[-1].lower()
			if MEDIA_EXTENSIONS.has_key(extension):
				png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "extensions/" + MEDIA_EXTENSIONS[extension] + ".png"))
			elif PLAYLIST_EXTENSIONS.has_key(extension):
				png = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/VlcPlayer/") + PLAYLIST_EXTENSIONS[extension])
			else:
				png = None

		if png is not None:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 0, height, height, png))

		return res

	def update(self):
		success = False
		filelistEntries = self.getFilesAndDirsCB(self.currentDirectory, self.regex)
		fileEntries = []
		directoryEntries = []
		if filelistEntries is not None:
			files, directories = filelistEntries
			for file in files:
				name, path = file
				fileEntries.append((path, False, name))
			for directory in directories:
				name, path = directory
				directoryEntries.append((path, True, name))
			fileEntries.sort(cmp = lambda x, y: cmp(x[0], y[0]))
			directoryEntries.sort(cmp = lambda x, y: cmp(x[0], y[0]))
			success = True
		self.list = directoryEntries + fileEntries
		self.l.setList(self.list)
		self.moveToIndex(0)
		return success

	def isVideoTS(self):
		for e in self.list:
			if e[1] == True and e[0].upper().endswith("VIDEO_TS"):
				return True
		return False

	def changeDirectory(self, directory):
		previousDirectory = self.currentDirectory
		self.currentDirectory = directory
		try:
			if self.update():
				if self.isVideoTS():
					ret = "dvdsimple://" + self.currentDirectory + "/VIDEO_TS", self.currentDirectory
					self.currentDirectory = previousDirectory
					self.update()
				else:
					ret = None, self.currentDirectory
			else:
				self.currentDirectory = previousDirectory
				ret = None, None
		except ExpatError, e:
			print e
			self.currentDirectory = previousDirectory
			self.update()
			ret = None, self.currentDirectory
		return ret

	def activate(self):
		cur = self.getCurrent()
		if cur is not None:
			if cur[1]:
				ret = self.changeDirectory(cur[0])
			else:
				ret = cur[0], cur[2]
		else:
			ret = None, None
		return ret

	def changeRegex(self, matchingPattern):
		if matchingPattern is not None:
			self.regex = re.compile(matchingPattern)
		else:
			self.regex = None

	def getNextFile(self):
		i = self.getSelectedIndex() + 1
		Len = len(self.list)
		while i < Len:
			cur = self.list[i]
			if cur[1] == False:
				self.moveToIndex(i)
				return cur[0], cur[2]
			i = i + 1
		return None, None

	def getPrevFile(self):
		i = self.getSelectedIndex() - 1
		while i > -1:
			cur = self.list[i]
			if cur[1] == False:
				self.moveToIndex(i)
				return cur[0], cur[2]
			i = i - 1
		return None, None
