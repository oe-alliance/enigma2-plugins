from enigma import eServiceReference, iServiceInformation, eServiceCenter
from Components.Sources.Source import Source
from Components.FileList import FileList
from os import path as os_path

class MP(Source):
	LIST = 0
	PLAY = 1
	COMMAND = 3
	WRITEPLAYLIST = 4

	def __init__(self, session, func=LIST):
		Source.__init__(self)
		self.func = func
		self.session = session
		error = "unknown command (%s)" % func
		self.result = ((error, error, error),)

	def handleCommand(self, cmd):
		self.cmd = cmd
		if self.func is self.LIST:
			self.result = self.getFileList(cmd)
		elif self.func is self.PLAY:
			self.result = self.playFile(cmd)
		elif self.func is self.COMMAND:
			self.result = self.command(cmd)
		elif self.func is self.WRITEPLAYLIST:
			self.result = self.writePlaylist(cmd)

	def tryOpenMP(self):
		# check if there is an active link
		if hasattr(self.session, "mediaplayer"):
			mp = self.session.mediaplayer
			try:
				len(mp.playlist)
			except Exception, e:
				pass
			else:
				return True

		# check if we actually have the mp installed
		try:
			from Plugins.Extensions.MediaPlayer.plugin import MediaPlayer, MyPlayList
		# nope, bail out
		except ImportError, ie:
			return False
		else:
			# mp installed, see if it's running
			if isinstance(self.session.current_dialog, MediaPlayer):
				self.session.mediaplayer = self.session.current_dialog
				return True

			# start new mp
			self.session.mediaplayer = self.session.open(MediaPlayer)
			return True


	def getFileList(self, param):
		print "getFileList:", param

		if param["path"] == "playlist":
			# TODO: Fix dummy return if unable to load mp
			if not self.tryOpenMP():
				return (("empty", "True", "playlist"),)

			mp = self.session.mediaplayer
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

		filelist = FileList(param["path"], showDirectories=True, showFiles=True, matchingPattern=matchingPattern, useServiceRef=useServiceRef, isTop=False)
		list = filelist.getFileList()
		if useServiceRef is True:
			returnList = [ (x[0][0].toString(), x[0][1], param["path"]) if x[0][1] is False else (x[0][0], x[0][1], param["path"]) for x in list ]
		else:
			returnList = [ (param["path"] + x[0][0], x[0][1], param["path"]) if x[0][1] is False else (x[0][0], x[0][1], param["path"]) for x in list ]

		return returnList

	def playFile(self, param):
		print "playFile: ", param
		# TODO: fix error handling
		if not self.tryOpenMP():
			return

		# TODO: what's the root for?
		root = param["root"]
		file = param["file"]

		if not file:
			return

		mp = self.session.mediaplayer
		ref = eServiceReference(4097, 0, file)

		mp.playlist.addFile(ref)
		mp.playServiceRefEntry(ref)
		mp.playlist.updateList()

	def writePlaylist(self, param):
		print "writePlaylist: ", param
		filename = "playlist/%s.e2pls" % param
		from Tools.Directories import resolveFilename, SCOPE_CONFIG

		# TODO: fix error handling
		if not self.tryOpenMP():
			return

		mp = self.session.mediaplayer
		mp.playlistIOInternal.save(resolveFilename(SCOPE_CONFIG, filename))

	def command(self, param):
		print "command: ", param

		# TODO: fix error handling
		if not self.tryOpenMP():
			return

		mp = self.session.mediaplayer

		if param == "previous":
			mp.previousEntry()
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

	list = property(lambda self: self.result)
	lut = {"ServiceReference": 0
			, "IsDirectory": 1
			, "Root": 2
			}
