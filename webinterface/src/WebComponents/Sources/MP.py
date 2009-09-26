from enigma import eServiceReference, iServiceInformation, eServiceCenter
from Components.Sources.Source import Source
from ServiceReference import ServiceReference
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
		# See is the Link is still active
		if self.session.mediaplayer is not None:
			try:
				test = len(self.session.mediaplayer.playlist)
				return True
			except Exception:
				pass

		# Link inactive, instantiate new MP
		try:
			from Plugins.Extensions.MediaPlayer.plugin import MediaPlayer, MyPlayList
			self.session.mediaplayer = self.session.open(MediaPlayer)
			self.session.mediaplayer.playlist = MyPlayList()
			return True

		# No MP installed
		except ImportError, ie:
			return False

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

		returnList = []

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
		for x in list:
			if useServiceRef == True:
				if x[0][1] == False: #isDir
					returnList.append((x[0][0].toString(), x[0][1], param["path"]))
				else:
					returnList.append((x[0][0], x[0][1], param["path"]))
			else:
				if x[0][1] == False: #isDir
					returnList.append((param["path"] + x[0][0], x[0][1], param["path"]))
				else:
					returnList.append((x[0][0], x[0][1], param["path"]))

		return returnList

	def playFile(self, param):
		print "playFile: ", param
		# TODO: fix error handling
		if not self.tryOpenMP():
			return

		root = param["root"]
		file = param["file"]

		mp = self.session.mediaplayer
		ref = eServiceReference(file)

		mp.switchToPlayList()

		if len(mp.playlist) == 1:
				mp.changeEntry(0)

		mp.playlist.addFile(ref)

		#mp.playServiceRefEntry(ref)
		sRefList = mp.playlist.getServiceRefList()
		Len = len(sRefList)
		print "len len(mp.playlist.getServiceRefList()): ", len(mp.playlist.getServiceRefList())
		if Len:
			lastEntry = Len - 1
			currref = sRefList[lastEntry]
			if self.session.nav.getCurrentlyPlayingServiceReference() is None or currref != self.session.nav.getCurrentlyPlayingServiceReference():
				self.session.nav.playService(sRefList[lastEntry])
				info = eServiceCenter.getInstance().info(currref)
				description = info and info.getInfoString(currref, iServiceInformation.sDescription) or ""
				mp["title"].setText(description)
			mp.unPauseService()
			#mp.playEntry(len(self.playlist.getServiceRefList()))

		mp.playlist.updateList()
		mp.infoTimerFire()

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
