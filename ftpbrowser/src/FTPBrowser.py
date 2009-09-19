# for localized messages
from . import _

# Core
from enigma import RT_HALIGN_LEFT, eListboxPythonMultiContent

# Tools
from Tools.Directories import SCOPE_SKIN_IMAGE, resolveFilename
from Tools.LoadPixmap import LoadPixmap
from Tools.Notifications import AddPopup

# GUI (Screens)
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBarGenerics import InfoBarNotifications
from NTIVirtualKeyBoard import NTIVirtualKeyBoard

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
from twisted.protocols.basic import FileSender

# For new and improved _parse
from urlparse import urlparse, urlunparse

# System
from os import path as os_path
from time import time

# Config
from Components.config import config

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
	absolute = directory + name
	if isDir:
		absolute += '/'

	res = [
		(absolute, isDir, file['size']),
		(eListboxPythonMultiContent.TYPE_TEXT, 35, 1, 470, 20, 0, RT_HALIGN_LEFT, name)
	]
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
		# TODO: is any of the 'advanced' features useful (and more of all can they be implemented) here?
		list = [FTPFileEntryComponent(file, self.current_directory) for file in self.filelist.files]
		list.sort(key = lambda x: (not x[0][1], x[0][0]))
		if self.current_directory != "/":
			list.insert(0, FileEntryComponent(name = "<" +_("Parent Directory") + ">", absolute = '/'.join(self.current_directory.split('/')[:-2]) + '/', isDir = True))

		self.l.setList(list)
		self.list = list

		select = self.select
		if select is not None:
			i = 0
			self.moveToIndex(0)
			for x in list:
				p = x[0][0]

				if p == select:
					self.moveToIndex(i)
					break
				i += 1

	def listFailed(self, *args):
		# XXX: we might end up here if login fails, we might want to add some check for this (e.g. send a dummy command before doing actual work)
		if self.current_directory != "/":
			self.list = [FileEntryComponent(name = "<" +_("Parent Directory") + ">", absolute = '/'.join(self.current_directory.split('/')[:-2]) + '/', isDir = True)]
		else:
			self.list = []
		self.l.setList(self.list)

class FTPBrowser(Screen, Protocol, InfoBarNotifications, HelpableScreen):
	skin = """
		<screen name="FTPBrowser" position="center,center" size="560,440" title="FTP Browser">
			<widget name="localText" position="20,10" size="200,20" font="Regular;18" />
			<widget name="local" position="20,40" size="255,320" scrollbarMode="showOnDemand" />
			<widget name="remoteText" position="285,10" size="200,20" font="Regular;18" />
			<widget name="remote" position="285,40" size="255,320" scrollbarMode="showOnDemand" />
			<widget name="eta" position="20,360" size="200,30" font="Regular;23" />
			<widget name="speed" position="330,360" size="200,30" halign="right" font="Regular;23" />
			<widget source="progress" render="Progress" position="20,390" size="520,10" />
			<ePixmap name="green" position="10,400" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="180,400" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue" position="350,400" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_green" position="10,400" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="180,400" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="350,400" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<ePixmap position="515,408" zPosition="1" size="35,25" pixmap="skin_default/buttons/key_menu.png" alphatest="on" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		InfoBarNotifications.__init__(self)
		self.ftpclient = None
		self.file = None
		self.currlist = "local"

		# Init what we need for dl progress
		self.currentLength = 0
		self.lastLength = 0
		self.lastTime = 0
		self.lastApprox = 0
		self.fileSize = 0

		self["localText"] = Label(_("Local"))
		self["local"] = FileList("/media/hdd/", showMountpoints = False)
		self["remoteText"] = Label(_("Remote (not connected)"))
		self["remote"] = FTPFileList()
		self["eta"] = Label("")
		self["speed"] = Label("")
		self["progress"] = VariableProgressSource()
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button("")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		self.URI = "ftp://"

		self["ftpbrowserBaseActions"] = HelpableActionMap(self, "ftpbrowserBaseActions",
			{
				"ok": (self.ok, _("enter directory/get file/put file")),
				"cancel": (self.cancel , _("close")),
				"menu": (self.menu, _("open menu")),
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

		self.onExecBegin.append(self.reinitialize)

	def reinitialize(self):
		# NOTE: this will clear the remote file list if we are not currently connected. this behavior is intended.
		# XXX: but do we also want to do this when we just returned from a notification?
		self["remote"].refresh()
		self["local"].refresh()

		if not self.ftpclient:
			self.connect(self.URI)
		# XXX: Actually everything else should be taken care of... recheck this!

	def menuCallback(self, ret):
		ret and ret[1]()

	def menu(self):
		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			title = _("What do you want to do?"),
			list = (
				(_("Connect to server from history"), self.connectHistory),
				(_("Connect to new server"), self.connectNew),
			)
		)

	def connectHistory(self):
		options = [(x, x) for x in config.plugins.ftpbrowser.history.value]

		if options:
			self.session.openWithCallback(
				self.connectWrapper,
				ChoiceBox,
				title = _("Select server to connect to"),
				list = options
			)
		else:
			self.session.open(
				MessageBox,
				_("No history"),
				type = MessageBox.TYPE_INFO
			)

	def inputCallback(self, res):
		if res:
			self.connect(res)

	def connectNew(self):
		self.session.openWithCallback(
			self.inputCallback,
			NTIVirtualKeyBoard,
			title = _("Enter URI of FTP Server:"),
			text = self.URI,
		)

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
					else:
						d = self.ftpclient.retrieveFile(absRemoteFile, self, offset = 0)
						d.addCallback(self.getFinished).addErrback(self.getFailed)
		else:
			# Put file/change directory
			assert(self.currlist == "local")
			if self["local"].canDescent():
				self["local"].descent()
			else:
				if self.file:
					self.session.open(
						MessageBox,
						_("There already is an active transfer."),
						type = MessageBox.TYPE_WARNING
					)
					return

				localFile = self["local"].getSelection()
				if not localFile:
					return

				def remoteFileExists(absName):
					for file in self["remote"].getFileList():
						if file[0][0] == absName:
							return True
					return False

				# XXX: isn't this supposed to be an absolute filename? well, it's not for me :-/
				fileName = localFile[0]
				absLocalFile = self["local"].getCurrentDirectory() + fileName
				directory = self["remote"].getCurrentDirectory()
				sep = '/' if directory != '/' else ''
				remoteFile = directory + sep + fileName
				if not force and remoteFileExists(remoteFile):
					self.session.openWithCallback(
						self.okQuestion,
						MessageBox,
						_("A file with this name already exists on the remote host.\nDo you want to overwrite it?"),
					)
				else:
					self.currentLength = 0
					self.lastLength = 0
					self.lastTime = 0
					self.lastApprox = 0

					def sendfile(consumer, fileObj):
						FileSender().beginFileTransfer(fileObj, consumer, transform = self.putProgress).addCallback(  
							lambda _: consumer.finish()).addCallback(
							self.putComplete).addErrback(self.putFailed)

					try:
						self.fileSize = int(os_path.getsize(absLocalFile))
						self.file = open(absLocalFile, 'rb')
					except (IOError, OSError), e:
						# TODO: handle this
						raise e
					else:
						dC, dL = self.ftpclient.storeFile(remoteFile)
						dC.addCallback(sendfile, self.file)

	def transferFinished(self, msg, type, toRefresh):
		AddPopup(msg, type, -1)

		self["eta"].setText("")
		self["speed"].setText("")
		self["progress"].invalidate()
		self[toRefresh].refresh()
		self.file.close()
		self.file = None

	def putComplete(self, *args):
		self.transferFinished(
			_("Upload finished."),
			MessageBox.TYPE_INFO,
			"remote"
		)

	def putFailed(self, *args):
		self.transferFinished(
			_("Error during download."),
			MessageBox.TYPE_ERROR,
			"remote"
		)

	def getFinished(self, *args):
		self.transferFinished(
			_("Download finished."),
			MessageBox.TYPE_INFO,
			"local"
		)

	def getFailed(self, *args):
		self.transferFinished(
			_("Error during download."),
			MessageBox.TYPE_ERROR,
			"local"
		)

	def putProgress(self, chunk):
		self.currentLength += len(chunk)
		self.gotProgress(self.currentLength, self.fileSize)
		return chunk

	def gotProgress(self, pos, max):
		self["progress"].writeValues(pos, max)

		newTime = time()
		# Check if we're called the first time (got total)
		lastTime = self.lastTime
		if lastTime == 0:
			self.lastTime = newTime

		# We dont want to update more often than every two sec (could be done by a timer, but this should give a more accurate result though it might lag)
		elif int(newTime - lastTime) >= 2:
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
		res = res and res[1]
		if res:
			if res == 1:
				self.file.close()
				self.file = None
				self.disconnect()
			self.close()

	def cancel(self):
		config.plugins.ftpbrowser.save()

		if self.file is not None:
			self.session.openWithCallback(
				self.cancelQuestion,
				ChoiceBox,
				title = _("A transfer is currently in progress.\nWhat do you want to do?"),
				list = (
					(_("Run in Background"), 2),
					(_("Abort transfer"), 1),
					(_("Cancel"), 0)
				)
			)
			return

		self.disconnect()
		self.close()

	def up(self):
		self[self.currlist].up()

	def down(self):
		self[self.currlist].down()

	def left(self):
		self[self.currlist].pageUp()

	def right(self):
		self[self.currlist].pageDown()

	def disconnect(self):
		if self.ftpclient:
			# XXX: according to the docs we should wait for the servers answer to our quit request, we just hope everything goes well here
			self.ftpclient.quit()
			self.ftpclient = None
			self["remote"].ftpclient = None
		self["remoteText"].setText(_("Remote (not connected)"))

	def connectWrapper(self, ret):
		if ret:
			self.connect(ret[1])

	def connect(self, address):
		self.disconnect()

		self.URI = address

		scheme, host, port, path, username, password = _parse(address)
		if not host:
			return

		# Maintain history
		history = config.plugins.ftpbrowser.history.value
		if address not in history:
			history.insert(0, address)
			if len(history) > 10:
				history.pop(10)
		else:
			history.remove(address)
			history.insert(0, address)

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
		self["remoteText"].setText(_("Remote"))

		scheme, host, port, path, username, password = _parse(self.URI)
		self["remote"].changeDir(path)

	def connectionFailed(self, *args):
		print "[FTPBrowser] connection failed", args

		self.URI = "ftp://"
		self["remoteText"].setText(_("Remote (not connected)"))
		self.session.open(
				MessageBox,
				_("Could not connect to ftp server!"),
				type = MessageBox.TYPE_ERROR,
				timeout = 3,
		)

