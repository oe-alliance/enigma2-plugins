from enigma import eServiceReference
from Components.Sources.Source import Source
from Components.FileList import FileList
from os import path as os_path

class MP(Source):
	LIST = 0
	PLAY = 1
	COMMAND = 3
	WRITEPLAYLIST = 4
	ADD = 5

	def __init__(self, session, func=LIST):
		Source.__init__(self)
		self.func = func
		self.session = session
		error = "unknown command (%s)" % func
		if func is self.LIST:
			self.result = ((error, error, error),)
		else:
			self.result = (False, error)

	def handleCommand(self, cmd):
		self.cmd = cmd
		func = self.func
		if func is self.LIST:
			self.result = self.getFileList(cmd)
		elif func is self.PLAY:
			self.result = self.playFile(cmd)
		elif func is self.COMMAND:
			self.result = self.command(cmd)
		elif func is self.WRITEPLAYLIST:
			self.result = self.writePlaylist(cmd)
		elif func is self.ADD:
			self.result = self.addFile(cmd)

	def tryOpenMP(self):
		# check if there is an active link
		if hasattr(self.session, "mediaplayer"):
			mp = self.session.mediaplayer
			try:
				len(mp.playlist)
			except Exception, e:
				pass
			else:
				return mp

		# check if we actually have the mp installed
		try:
			from Plugins.Extensions.MediaPlayer.plugin import MediaPlayer, MyPlayList
		# nope, bail out
		except ImportError, ie:
			return None
		else:
			# mp installed, see if it's running
			if isinstance(self.session.current_dialog, MediaPlayer):
				self.session.mediaplayer = self.session.current_dialog
			# start new mp
			else:
				self.session.mediaplayer = self.session.open(MediaPlayer)
			return self.session.mediaplayer

	def getFileList(self, param):
		if param["path"] == "playlist":
			mp = self.tryOpenMP()
			# TODO: Fix dummy return if unable to load mp
			if mp is None:
				return (("empty", "True", "playlist"),)

			if mp.playlist:
				return [(serviceRef.toString(), "True", "playlist") for serviceRef in mp.playlist.getServiceRefList()]
			else:
				return (("empty", "True", "playlist"),)

		matchingPattern = "(?i)^.*\.(mp3|ogg|ts|wav|wave|m3u|pls|e2pls|mpg|vob)" #MediaPlayer-Match
		useServiceRef = False
		if param["types"] == "audio":
			matchingPattern = "(?i)^.*\.(mp3|ogg|wav|wave|m3u|pls|e2pls)"
			useServiceRef = True
		elif param["types"] == "video":
			matchingPattern = "(?i)^.*\.(ts|avi|mpeg|m3u|pls|e2pls|mpg|vob)"
			useServiceRef = True
		elif param["types"] == "any":
			matchingPattern = ".*"
		else:
			matchingPattern = param["types"]

		path = param["path"]
		if path == "undefined":
			path = None
		elif path is not None and not os_path.exists(path):
			# TODO: returning something is better than just dying but is this return sane?
			return ((None, True, path),)

		filelist = FileList(path, showDirectories=True, showFiles=True, matchingPattern=matchingPattern, useServiceRef=useServiceRef, isTop=False)
		list = filelist.getFileList()
		if useServiceRef is True:
			returnList = [ (x[0][0].toString(), x[0][1], path) if x[0][1] is False else (x[0][0], x[0][1], path) for x in list ]
		else:
			returnList = [ (param["path"] + x[0][0], x[0][1], path) if x[0][1] is False else (x[0][0], x[0][1], path) for x in list ]

		return returnList

	def playFile(self, param):
		return self.addFile(param, play=True)

	def addFile(self, param, play=False):
		# TODO: fix error handling
		mp = self.tryOpenMP()
		if mp is None:
			return (False, "mediaplayer not installed")

		# TODO: what's the root for?
		root = param["root"]
		file = param["file"]

		if not file:
			return (False, "missing or invalid parameter file")

		ref = eServiceReference(file)
		if not ref.valid():
			if not os_path.exists(file):
				return (False, "%s is neither a valid reference nor a valid file" % file)
			ref = eServiceReference(4097, 0, file)

		mp.playlist.addFile(ref)
		if play:
			mp.playServiceRefEntry(ref)
			ret = (True, "%s added to playlist and playback started" % file)
		else:
			ret = (True, "%s added to playlist" % file)

		mp.playlist.updateList()
		return ret

	def writePlaylist(self, param):
		filename = "playlist/%s.e2pls" % param
		from Tools.Directories import resolveFilename, SCOPE_CONFIG

		# TODO: fix error handling
		mp = self.tryOpenMP()
		if mp is None:
			return (False, "mediaplayer not installed")

		mp.playlistIOInternal.save(resolveFilename(SCOPE_CONFIG, filename))

	def command(self, param):
		# TODO: fix error handling
		mp = self.tryOpenMP()
		if mp is None:
			return (False, "mediaplayer not installed")

		if param == "previous":
			mp.previousMarkOrEntry()
		elif param == "play":
			mp.playEntry()
		elif param == "pause":
			mp.pauseEntry()
		elif param == "next":
			mp.nextEntry()
		elif param == "stop":
			mp.stopEntry()
		elif param == "exit":
			mp.exit()
		else:
			return (False, "unknown parameter %s" % param)
		return (True, "executed %s" % param)

	list = property(lambda self: self.result)
	lut = {"ServiceReference": 0
			, "IsDirectory": 1
			, "Root": 2
			}
