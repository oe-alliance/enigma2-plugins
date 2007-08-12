from Components.FileList import FileEntryComponent
from Components.FileList import FileList
from Components.config import config
from urllib import urlencode
from urllib import urlopen
import re
import xml.sax
import os.path

class vlcBrowseXmlHandler(xml.sax.ContentHandler):
	
	def __init__(self, host, regex = None):
		self.host = host
		self.regex = regex
		self.files = []
		self.directories = []
	
	def startElement(self, name, attrs):
		if name == "element" and attrs is not None:
			type = attrs.getValue("type")
			name = attrs.getValue("name").encode("latin_1", "replace")
			path = self.host + ":" + attrs.getValue("path").encode("latin_1")
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
	
#	def _getFilesAndDirs_old(self, host, path, regex = None):
#		files = []
#		directories = []
#		result = vlcHttpCommand_old(host, path)
#		entries = result.split("\n")
#		for e in entries:
#			if e[0:4] == "DIR:":
#				e = e[4:]
#				directories.append(FileEntryComponent(os.path.basename(e), host+":"+e, True))
#			elif len(e) > 0:
#				if regex is None or regex.search(e):
#					files.append(FileEntryComponent(os.path.basename(e), host+":"+e, False))
#		return (files,directories)

	def _getFilesAndDirs(self, servernum, path, regex = None):
		cfg = config.plugins.vlcplayer.servers[servernum]
		url = "http://%s:%d/requests/browse.xml?%s" % (cfg.host.value, cfg.httpport.value, urlencode({'dir': path}))
		print "[VLC] _getFilesAndDirs", url
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
		print "[VLC] changeDir ", directory
		if directory is None:
			self.initServerlist()
			return

		directory = directory.replace("\\","/")
		directory = os.path.normpath(directory)
		if directory == ".":
			self.initServerlist()
			return

		i = directory.find(":")
		servernum = int(directory[0:i])
		path = directory[i+1:]
		if len(path) == 0:
			path = "/"

		if self.matchingPattern is not None:
			regex = re.compile(self.matchingPattern)
		else:
			regex = None

		files, directories = self._getFilesAndDirs(servernum, path, regex)

		directories.sort(cmp=lambda x, y: cmp(x[0], y[0]));
		files.sort(cmp=lambda x, y: cmp(x[0], y[0]));
		self.list = directories + files
		self.l.setList(self.list)
		self.current_directory = str(servernum) + ":" + path
		self.current_server = servernum
		self.current_path = path
		
		if select is not None:
			self.setSelection(select)

	def setSelection(self, select):
		i = 0
		self.moveToIndex(0)
		for x in self.list:
			p = x[0][0]
			if p == select:
				self.moveToIndex(i)
			i += 1
