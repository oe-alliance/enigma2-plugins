# for localized messages
from . import _

# Core
from enigma import RT_HALIGN_LEFT, eListboxPythonMultiContent

# Tools
from Tools.Directories import SCOPE_SKIN_IMAGE, resolveFilename
from Tools.LoadPixmap import LoadPixmap

# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

# GUI (Components)
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Label import Label
from Components.FileList import FileList, FileEntryComponent, EXTENSIONS
from Components.Button import Button
from VariableProgressSource import VariableProgressSource

# FTP Client
from twisted.internet import reactor, defer
from twisted.internet.protocol import Protocol, ClientCreator
from twisted.protocols.ftp import FTPClient, FTPFileListProtocol

# For new and improved _parse
from urlparse import urlparse, urlunparse

# System
from os import path as os_path
from time import time

def _parse(url, defaultPort = None):
	url = url.strip()
	parsed = urlparse(url)
	scheme = parsed[0]
	path = urlunparse(('','')+parsed[2:])

	if defaultPort is None:
		if scheme == 'https':
			defaultPort = 443
		elif scheme == 'ftp':
			defaultPort = 21
		else:
			defaultPort = 80

	host, port = parsed[1], defaultPort

	if '@' in host:
		username, host = host.split('@')
		if ':' in username:
			username, password = username.split(':')
		else:
			password = ""
	else:
		username = ""
		password = ""

	if ':' in host:
		host, port = host.split(':')
		port = int(port)

	if path == "":
		path = "/"

	return scheme, host, port, path, username, password

def FTPFileEntryComponent(file, directory):
	isDir = True if file['filetype'] == 'd' else False
	name = file['filename']

	sep = '/' if directory != '/' else ''
	res = [ (directory + sep + name, isDir, file['size']) ]
	res.append((eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 470, 20, 0, RT_HALIGN_LEFT, name))
	if isDir:
		png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "extensions/directory.png"))
	else:
		extension = name.split('.')
		extension = extension[-1].lower()
		if EXTENSIONS.has_key(extension):
			png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "extensions/" + EXTENSIONS[extension] + ".png"))
		else:
			png = None
	if png is not None:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 2, 20, 20, png))

	return res

class FTPFileList(FileList):
	def __init__(self):
		self.ftpclient = None
		self.select = None
		FileList.__init__(self, "/")

	def changeDir(self, directory, select = None):
		if self.ftpclient is None:
			self.list = []
			self.l.setList(self.list)
			return

		self.current_directory = directory
		self.select = select

		self.filelist = FTPFileListProtocol()
		d = self.ftpclient.list(directory, self.filelist)
		d.addCallback(self.listRcvd).addErrback(self.listFailed)

	def listRcvd(self, *args):
		# XXX: we might want to sort this list and/or implement any other feature than 'list directories'
		self.list = [FTPFileEntryComponent(file, self.current_directory) for file in self.filelist.files]
		if self.current_directory != "/":
			self.list.insert(0, FileEntryComponent(name = "<" +_("Parent Directory") + ">", absolute = '/'.join(self.current_directory.split('/')[:-1]) + '/', isDir = True))
		self.l.setList(self.list)

	def listFailed(self, *args):
		if self.current_directory != "/":
			self.list = [FileEntryComponent(name = "<" +_("Parent Directory") + ">", absolute = '/'.join(self.current_directory.split('/')[:-1]) + '/', isDir = True)]
		else:
			self.list = []
		self.l.setList(self.list)

class FTPBrowser(Screen, Protocol):
	skin = """
		<screen name="FTPBrowser" position="100,100" size="560,410" title="FTP Browser" >
			<widget name="local" position="20,10" size="220,320" scrollbarMode="showOnDemand" />
			<widget name="remote" position="245,10" size="220,320" scrollbarMode="showOnDemand" />
			<widget source="progress" render="Progress" position="20,360" size="520,10" />
			<widget name="eta" position="20,330" size="200,30" font="Regular;23" />
			<widget name="speed" position="330,330" size="200,30" halign="right" font="Regular;23" />
			<ePixmap name="red" position="0,370" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="140,370" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,370" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue" position="420,370" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,370" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,370" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="280,370" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="420,370" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.ftpclient = None
		self.file = None
		self.currlist = "remote"

		# Init what we need for dl progress
		self.currentLength = 0
		self.lastLength = 0
		self.lastTime = 0
		self.lastApprox = 0
		self.fileSize = 0

		self["local"] = FileList("/media/hdd")
		self["remote"] = FTPFileList()
		self["eta"] = Label("")
		self["speed"] = Label("")
		self["progress"] = VariableProgressSource()
		self["key_red"] = Button("")
		self["key_green"] = Button("")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		URI = "ftp://root@localhost:21" # TODO: make configurable
		self.connect(URI)

		self["ftpbrowserBaseActions"] = HelpableActionMap(self, "ftpbrowserBaseActions",
			{
				"ok": (self.ok, _("enter directory/get file/put file")),
				"cancel": (self.cancel , _("close")),
			}, -2)

		self["ftpbrowserListActions"] = HelpableActionMap(self, "ftpbrowserListActions",
			{
				"channelUp": (self.setLocal, _("Select local file list")),
				"channelDown": (self.setRemote, _("Select remote file list")),
			})

		self["actions"] = ActionMap(["ftpbrowserDirectionActions"],
			{
				"up": self.up,
				"down": self.down,
				"left": self.left,
				"right": self.right,
			}, -2)

	def setLocal(self):
		self.currlist = "local"

	def setRemote(self):
		self.currlist = "remote"

	def okQuestion(self, res = None):
		if res:
			self.ok(force = True)

	def ok(self, force = False):
		if self.currlist == "remote":
			# Get file/change directory
			if self["remote"].canDescent():
				self["remote"].descent()
			else:
				if self.file:
					self.session.open(
						MessageBox,
						_("There already is an active transfer."),
						type = MessageBox.TYPE_WARNING
					)
					return

				remoteFile = self["remote"].getSelection()
				if not remoteFile:
					return

				absRemoteFile = remoteFile[0]
				fileName = absRemoteFile.split('/')[-1]
				localFile = self["local"].getCurrentDirectory() + fileName
				if not force and os_path.exists(localFile):
					self.session.openWithCallback(
						self.okQuestion,
						MessageBox,
						_("A file with this name already exists locally.\nDo you want to overwrite it?"),
					)
				else:
					self.currentLength = 0
					self.lastLength = 0
					self.lastTime = 0
					self.lastApprox = 0
					self.fileSize = remoteFile[2]

					try:
						self.file = open(localFile, 'w')
					except IOError, ie:
						# TODO: handle this
						raise ie
					d = self.ftpclient.retrieveFile(absRemoteFile, self, offset = 0)
					d.addCallback(self.getFinished).addErrback(self.getFailed)
		else:
			# Put file/change directory
			assert(self.currlist == "local")
			if self["local"].canDescent():
				self["local"].descent()
			else:
				self.session.open(
					MessageBox,
					_("Not yet implemented."),
					type = MessageBox.TYPE_WARNING
				)

	def getFinished(self, *args):
		self.session.open(
			MessageBox,
			_("Download finished."),
			type = MessageBox.TYPE_INFO
		)

		self["eta"].setText("")
		self["speed"].setText("")
		self["progress"].invalidate()
		self.file.close()
		self.file = None

	def getFailed(self, *args):
		self.session.open(
			MessageBox,
			_("Error during download."),
			type = MessageBox.TYPE_ERROR
		)

		self["eta"].setText("")
		self["speed"].setText("")
		self["progress"].writeValues(0, 0)
		self.file.close()
		self.file = None

	def gotProgress(self, pos, max):
		self["progress"].writeValues(pos, max)

		newTime = time()
		# Check if we're called the first time (got total)
		lastTime = self.lastTime
		if lastTime == 0:
			self.lastTime = newTime

		# We dont want to update more often than every two sec (could be done by a timer, but this should give a more accurate result though it might lag)
		elif int(newTime - lastTime) >= 1:
			lastApprox = round(((pos - self.lastLength) / (newTime - lastTime) / 1024), 2)

			secLen = int(round(((max-pos) / 1024) / lastApprox))
			self["eta"].setText(_("ETA %d:%02d min") % (secLen / 60, secLen % 60))
			self["speed"].setText(_("%d kb/s") % (lastApprox))

			self.lastApprox = lastApprox
			self.lastLength = pos
			self.lastTime = newTime

	def dataReceived(self, data):
		if not self.file:
			return

		self.currentLength += len(data)
		self.gotProgress(self.currentLength, self.fileSize)

		try:
			self.file.write(data)
		except IOError, ie:
			# TODO: handle this
			self.file = None
			raise ie

	def cancelQuestion(self, res = None):
		if res:
			self.file.close()
			self.file = None
			self.cancel()

	def cancel(self):
		if self.file is not None:
			self.session.openWithCallback(
				self.cancelQuestion,
				MessageBox,
				_("A transfer is currently in progress.\nAbort?"),
			)
			return

		self.ftpclient.quit()
		self.close()

	def up(self):
		self[self.currlist].up()

	def down(self):
		self[self.currlist].down()

	def left(self):
		self[self.currlist].pageUp()

	def right(self):
		self[self.currlist].pageDown()

	def connect(self, address):
		self.ftpclient = None
		self["remote"].ftpclient = None

		scheme, host, port, path, username, password = _parse(address)
		if not username:
			username = 'anonymous'
			password = 'my@email.com'

		timeout = 30 # TODO: make configurable
		passive = True # TODO: make configurable
		creator = ClientCreator(reactor, FTPClient, username, password, passive = passive)

		creator.connectTCP(host, port, timeout).addCallback(self.controlConnectionMade).addErrback(self.connectionFailed)

	def controlConnectionMade(self, ftpclient):
		print "[FTPBrowser] connection established"
		self.ftpclient = ftpclient
		self["remote"].ftpclient = ftpclient
		self["remote"].changeDir("/")

	def connectionFailed(self, *args):
		print "[FTPBrowser] connection failed", args
		self.session.open(
				MessageBox,
				_("Could not connect to ftp server!"),
				type = MessageBox.TYPE_ERROR,
				timeout = 3,
		)

