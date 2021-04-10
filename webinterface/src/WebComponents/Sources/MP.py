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
	REMOVE = 6
	CURRENT = 7
	LOADPLAYLIST = 8

	def __init__(self, session, func=LIST):
		Source.__init__(self)
		self.func = func
		self.session = session
		error = _("Unknown command (%s)") % func
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
		elif func is self.LOADPLAYLIST:
			self.result = self.loadPlaylist(cmd)
		elif func is self.REMOVE:
			self.result = self.removeFile(cmd)
		elif func is self.ADD:
			param = {"file": cmd, "root": None}
			self.result = self.addFile(param)

	def tryOpenMP(self, noCreate=False):
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
				# bail out if we don't want to open a new mp
				if noCreate:
					return False
				self.session.mediaplayer = self.session.open(MediaPlayer)
			return self.session.mediaplayer

	def getFileList(self, param):
		if param["path"] == "playlist":
			mp = self.tryOpenMP()
			# TODO: Fix dummy return if unable to load mp
			if mp is None:
				return (("empty", True, "playlist"),)

			if mp.playlist:
				return [(serviceRef.getPath(), False, "playlist") for serviceRef in mp.playlist.getServiceRefList()]
			else:
				return (("empty", True, "playlist"),)

		# try to extract current pattern from media player and use it over our hardcoded one as default
		try:
			matchingPattern = mp.filelist.matchingPattern
		except Exception:
			matchingPattern = "(?i)^.*\.(mp2|mp3|ogg|ts|wav|wave|m3u|pls|e2pls|mpg|vob|avi|divx|m4v|mkv|mp4|m4a|dat|flac|mov|m2ts)" #MediaPlayer-Match

		useServiceRef = False
		if param["types"] == "audio":
			matchingPattern = "(?i)^.*\.(mp3|ogg|wav|wave|m3u|pls|e2pls)"
			useServiceRef = True
		elif param["types"] == "video":
			matchingPattern = "(?i)^.*\.(ts|avi|mpeg|m3u|pls|e2pls|mpg|vob)"
			useServiceRef = True
		elif param["types"] == "any":
			matchingPattern = ".*"
		elif param["types"]:
			matchingPattern = param["types"]

		path = param["path"]
		if path is not None:
			if path.lower() == "filesystems":
				path = None
			elif not os_path.isdir(path):
				# TODO: returning something is better than just dying but is this return sane?
				return ((None, True, path),)

		filelist = FileList(path, showDirectories=True, showFiles=True, matchingPattern=matchingPattern, useServiceRef=useServiceRef, isTop=False)
		list = filelist.getFileList()
		if useServiceRef is True:
			returnList = [(x[0][0].toString(), x[0][1], path) if x[0][1] is False else (x[0][0], x[0][1], path) for x in list]
		else:
			returnList = [(param["path"] + x[0][0], x[0][1], path) if x[0][1] is False else (x[0][0], x[0][1], path) for x in list]

		return returnList

	def playFile(self, param):
		return self.addFile(param, doPlay=True)

	def addFile(self, param, doPlay=False):
		# TODO: fix error handling
		mp = self.tryOpenMP()
		if mp is None:
			return (False, _("Mediaplayer not installed"))

		file = param["file"]
		doAdd = False if param["root"] == "playlist" else True

		if not file:
			return (False, _("Missing or invalid parameter file"))

		ref = eServiceReference(file)
		if not ref.valid():
			if not os_path.isfile(file):
				return (False, _("'%s' is neither a valid reference nor a valid file") % file)
			ref = eServiceReference(4097, 0, file)

		if doAdd:
			mp.playlist.addFile(ref)
		if doPlay:
			mp.playServiceRefEntry(ref)

		mp.playlist.updateList()
		if doPlay:
			return (True, _("Playback of '%s' started") % (file))
		else:
			return (True, _("'%s' has been added to playlist") % (file))

	def removeFile(self, file):
		# TODO: fix error handling
		mp = self.tryOpenMP()
		if mp is None:
			return (False, _("Mediaplayer not installed"))

		ref = eServiceReference(file)
		if not ref.valid():
			ref = eServiceReference(4097, 0, file)
			if not ref.valid():
				return (False, _("'%s' is neither a valid reference nor a valid file") % file)

		serviceRefList = mp.playlist.getServiceRefList()
		i = 0
		for mpref in serviceRefList:
			if mpref == ref:
				mp.playlist.deleteFile(i)
				mp.playlist.updateList()
				return (True, _("'%s' removed from playlist") % file)
			i += 1

		return (False, _("'%s' not found in playlist") % file)

	def loadPlaylist(self, param):
		from Tools.Directories import resolveFilename, SCOPE_PLAYLIST

		# TODO: fix error handling
		mp = self.tryOpenMP()
		if mp is None:
			return (False, _("Mediaplayer not installed"))

		if os_path.isfile(param):
			fullPath = param
			param = param.rsplit('/', 1)[-1]
		else:
			fullPath = resolveFilename(SCOPE_PLAYLIST, param)
			if not os_path.isfile(fullPath):
				return (False, _("Playlist '%s' does not exist") % fullPath)
		mp.PlaylistSelected((param, fullPath))
		return (True, "Playlist loaded from '%s'" % fullPath)

	def writePlaylist(self, param):
		filename = "%s.e2pls" % param
		from Tools.Directories import resolveFilename, SCOPE_PLAYLIST

		# TODO: fix error handling
		mp = self.tryOpenMP()
		if mp is None:
			return (False, _("Mediaplayer not installed"))

		fullPath = resolveFilename(SCOPE_PLAYLIST, filename)
		mp.playlistIOInternal.save(fullPath)
		return (True, _("Playlist saved to '%s'") % fullPath)

	def command(self, param):
		# TODO: fix error handling
		noCreate = True if param == "exit" else False
		mp = self.tryOpenMP(noCreate=noCreate)
		if mp is None:
			return (False, _("Mediaplayer not installed"))
		elif mp is False:
			return (True, _("Mediaplayer was not active"))

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
		elif param == "shuffle":
			mp.playlist.PlayListShuffle()
		elif param == "clear":
			mp.clear_playlist()
		else:
			return (False, _("Unknown parameter %s") % param)
		return (True, _("Command '%s' executed") % param)

	def getCurrent(self):
		mp = self.tryOpenMP()
		if mp is None:
			msg = _("Mediaplayer not installed")
			return ((msg, msg, msg, msg, msg, msg),)

		return ((
			mp["artist"].getText(),
			mp["title"].getText(),
			mp["album"].getText(),
			mp["year"].getText(),
			mp["genre"].getText(),
			mp["coverArt"].coverArtFileName
		),)

	def getList(self):
		if self.func is self.CURRENT:
			return self.getCurrent()
		return self.result

	def getLut(self):
		if self.func is self.CURRENT:
			return {
				"Artist": 0,
				"Title": 1,
				"Album": 2,
				"Year": 3,
				"Genre": 4,
				"CoverFilename": 5,
			}
		return {
			"ServiceReference": 0,
			"IsDirectory": 1,
			"Root": 2,
		}

	list = property(getList)
	lut = property(getLut)
