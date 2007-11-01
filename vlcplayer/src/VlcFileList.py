# -*- coding: ISO-8859-1 -*-
#===============================================================================
# VLC Player Plugin by A. Lätsch 2007
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

from Components.FileList import FileEntryComponent
from Components.FileList import FileList
from Components.config import config
from urllib import urlencode
from urllib import urlopen
import posixpath
import re
import xml.sax

def normpath(path):
	if path is None:
		return None
	path = path.replace("\\","/").replace("//", "/")
	if path == "/..":
		return ""
	if len(path) > 0 and path[0] != '/': 
		path = posixpath.normpath('/'+path)[1:]
	else:
		path = posixpath.normpath(path)

	if len(path) == 0 or path == "//":
		return "/"
	elif path == ".":
		return None
	return path

class vlcBrowseXmlHandler(xml.sax.ContentHandler):
	
	def __init__(self, host, regex = None):
		self.host = host
		self.regex = regex
		self.files = []
		self.directories = []
	
	def startElement(self, name, attrs):
		if name == "element" and attrs is not None:
			type = attrs.getValue("type")
			name = attrs.getValue("name").encode("utf8")
			path = "%s:%s" % (self.host, normpath(attrs.getValue("path").encode("utf8")))
			if type == "directory":
				self.directories.append(FileEntryComponent(name, path, True))
			elif len(path) > 0:
				if self.regex is None or self.regex.search(path):
					self.files.append(FileEntryComponent(name, path, False))
	

class VlcFileList(FileList):
	def __init__(self, pMatchingPattern=None):
		FileList.__init__(self, None, matchingPattern = pMatchingPattern, useServiceRef = False)
		self.current_directory = None
		self.current_server = None
		self.current_path = None
	
	def __getFilesAndDirs(self, servernum, path, regex = None):
		cfg = config.plugins.vlcplayer.servers[servernum]
		url = "http://%s:%d/requests/browse.xml?%s" % (cfg.host.value, cfg.httpport.value, urlencode({'dir': path}))
		print "[VLC] __getFilesAndDirs", url
		req = urlopen(url)
		if req is None:
			raise IOError, "No response from server"
		handler = vlcBrowseXmlHandler(str(servernum), regex)
		xml.sax.parse(req, handler)
		return (handler.files, handler.directories)
	
	def initServerlist(self):
		self.list = []
		for i in range(0, config.plugins.vlcplayer.servercount.value):
			cfg = config.plugins.vlcplayer.servers[i]
			self.list.append(FileEntryComponent(cfg.host.value, str(i)+":"+cfg.basedir.value, True))
		self.list.append(FileEntryComponent(_("<add server>"), None, False))
		self.l.setList(self.list)
		self.current_directory = None
		self.current_server = None
		self.current_path = None
		
	def changeDir(self, directory, select = None):
		print "[VLC] changeDir ", directory, select
		if directory is None:
			self.initServerlist()
			return

		i = directory.find(":")
		servernum = int(directory[0:i])
		path = normpath(directory[i+1:])
		if path is None:
			self.initServerlist()
			return

		if self.matchingPattern is not None:
			regex = re.compile(self.matchingPattern)
		else:
			regex = None

		files, directories = self.__getFilesAndDirs(servernum, path, regex)

		directories.sort(cmp=lambda x, y: cmp(x[0], y[0]));
		files.sort(cmp=lambda x, y: cmp(x[0], y[0]));
		self.list = directories + files
		self.l.setList(self.list)
		self.current_directory = str(servernum) + ":" + path
		self.current_server = servernum
		self.current_path = path
		
		if select is not None:
			self.setSelection(select)
		else:
			self.moveToIndex(0)

	def setSelection(self, select):
		i = 0
		self.moveToIndex(0)
		for x in self.list:
			p = x[0][0]
			if p == select:
				self.moveToIndex(i)
			i += 1

	def getNextFile(self):
		i = self.getSelectedIndex() + 1
		while i < len(self.list):
			if self.list[i][0][1]==False:
				self.moveToIndex(i)
				return self.list[i][0][0]
			i = i+1
		return None
	
	def getPrevFile(self):
		i = self.getSelectedIndex() - 1
		while i >= 0:
			if self.list[i][0][1]==False:
				self.moveToIndex(i)
				return self.list[i][0][0]
			i = i-1
		return None
