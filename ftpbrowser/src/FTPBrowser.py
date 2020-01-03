# -*- coding: utf-8 -*-
from __future__ import print_function

# for localized messages
from . import _

# Core
from enigma import RT_HALIGN_LEFT, eListboxPythonMultiContent

# Tools
from Tools.Directories import SCOPE_SKIN_IMAGE, resolveFilename
from Tools.LoadPixmap import LoadPixmap
from Tools.Notifications import AddPopup, AddNotificationWithCallback

# GUI (Screens)
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBarGenerics import InfoBarNotifications
from FTPServerManager import FTPServerManager
from FTPQueueManager import FTPQueueManager
from Plugins.SystemPlugins.Toolkit.NTIVirtualKeyBoard import NTIVirtualKeyBoard

# GUI (Components)
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.FileList import FileList, FileEntryComponent, EXTENSIONS
from Components.Sources.StaticText import StaticText
from VariableProgressSource import VariableProgressSource

# FTP Client
from twisted.internet import reactor, defer
from twisted.internet.protocol import Protocol, ClientCreator
from twisted.protocols.ftp import FTPClient, FTPFileListProtocol
from twisted.protocols.basic import FileSender

# System
from os import path as os_path, unlink as os_unlink, rename as os_rename, \
		listdir as os_listdir
from time import time
import re

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
		if extension in EXTENSIONS:
			png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "extensions/" + EXTENSIONS[extension] + ".png"))
		else:
			png = None
	if png is not None:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 2, 20, 20, png))

	return res

class ModifiedFTPFileListProtocol(FTPFileListProtocol):
    fileLinePattern = re.compile(
        r'^(?P<filetype>.)(?P<perms>.{9})\s+(?P<nlinks>\d*)\s*'
        r'(?P<owner>\S+)\s+(?P<group>\S+)\s+(?P<size>\d+)\s+'
        r'(?P<date>...\s+\d+\s+[\d:]+)\s+(?P<filename>.*?)'
        r'( -> (?P<linktarget>[^\r]*))?\r?$'
    )

class FTPFileList(FileList):
	def __init__(self):
		self.ftpclient = None
		self.select = None
		self.isValid = False
		FileList.__init__(self, "/")

	def changeDir(self, directory, select = None):
		if not directory:
			return

		if self.ftpclient is None:
			self.list = []
			self.l.setList(self.list)
			return

		self.current_directory = directory
		self.select = select

		self.filelist = ModifiedFTPFileListProtocol()
		d = self.ftpclient.list(directory, self.filelist)
		d.addCallback(self.listRcvd).addErrback(self.listFailed)

	def listRcvd(self, *args):
		# TODO: is any of the 'advanced' features useful (and more of all can they be implemented) here?
		list = [FTPFileEntryComponent(file, self.current_directory) for file in self.filelist.files]
		list.sort(key = lambda x: (not x[0][1], x[0][0]))
		if self.current_directory != "/":
			list.insert(0, FileEntryComponent(name = "<" +_("Parent Directory") + ">", absolute = '/'.join(self.current_directory.split('/')[:-2]) + '/', isDir = True))

		self.isValid = True
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
			self.list = [
				FileEntryComponent(name = "<" +_("Parent Directory") + ">", absolute = '/'.join(self.current_directory.split('/')[:-2]) + '/', isDir = True),
				FileEntryComponent(name = "<" + _("Error") + ">", absolute = None, isDir = False),
			]
		else:
			self.list = [
				FileEntryComponent(name = "<" + _("Error") + ">", absolute = None, isDir = False),
			]

		self.isValid = False
		self.l.setList(self.list)

class FTPBrowser(Screen, Protocol, InfoBarNotifications, HelpableScreen):
	skin = """
		<screen name="FTPBrowser" position="center,center" size="600,440" title="FTP Browser">
			<ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<ePixmap position="565,10" size="35,25" pixmap="skin_default/buttons/key_menu.png" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="localText" render="Label" position="10,50" size="200,20" font="Regular;18" />
			<widget name="local" position="10,80" size="290,320" scrollbarMode="showOnDemand" />
			<widget source="remoteText" render="Label" position="300,50" size="200,20" font="Regular;18" />
			<widget name="remote" position="300,80" size="290,320" scrollbarMode="showOnDemand" />
			<widget source="eta" render="Label" position="20,410" size="200,30" font="Regular;23" />
			<widget source="speed" render="Label" position="380,410" size="200,30" halign="right" font="Regular;23" />
			<widget source="progress" render="Progress" position="20,440" size="560,10" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		InfoBarNotifications.__init__(self)
		self.ftpclient = None
		self.queueManagerInstance = None
		self.file = None
		self.queue = None
		self.currlist = "local"

		# # NOTE: having self.checkNotifications in onExecBegin might make our gui
		# disappear, so let's move it to onShow
		self.onExecBegin.remove(self.checkNotifications)
		self.onShow.append(self.checkNotifications)

		# Init what we need for dl progress
		self.currentLength = 0
		self.lastLength = 0
		self.lastTime = 0
		self.lastApprox = 0
		self.fileSize = 0

		self["localText"] = StaticText(_("Local"))
		self["local"] = FileList("/media/hdd/", showMountpoints = False)
		self["remoteText"] = StaticText(_("Remote (not connected)"))
		self["remote"] = FTPFileList()
		self["eta"] = StaticText("")
		self["speed"] = StaticText("")
		self["progress"] = VariableProgressSource()
		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("Rename"))
		self["key_yellow"] = StaticText(_("Delete"))
		self["key_blue"] = StaticText(_("Upload"))

		self.server = None

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

		self["actions"] = ActionMap(["ftpbrowserDirectionActions", "ColorActions"],
			{
				"up": self.up,
				"down": self.down,
				"left": self.left,
				"right": self.right,
				"green": self.rename,
				"yellow": self.delete,
				"blue": self.transfer,
			}, -2)

		self.onExecBegin.append(self.reinitialize)

	def reinitialize(self):
		# NOTE: this will clear the remote file list if we are not currently connected. this behavior is intended.
		# XXX: but do we also want to do this when we just returned from a notification?
		try:
			self["remote"].refresh()
		except AttributeError as ae:
			# NOTE: we assume the connection was timed out by the server
			self.ftpclient = None
			self["remote"].ftpclient = None
			self["remote"].refresh()

		self["local"].refresh()

		if not self.ftpclient:
			self.connect(self.server)
		# XXX: Actually everything else should be taken care of... recheck this!

	def serverManagerCallback(self, uri):
		if uri:
			self.connect(uri)

	def serverManager(self):
		self.session.openWithCallback(
			self.serverManagerCallback,
			FTPServerManager,
		)

	def queueManagerCallback(self):
		self.queueManagerInstance = None

	def queueManager(self):
		self.queueManagerInstance = self.session.openWithCallback(
			self.queueManagerCallback,
			FTPQueueManager,
			self.queue,
		)

	def menuCallback(self, ret):
		ret and ret[1]()

	def menu(self):
		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list = [
				(_("Server Manager"), self.serverManager),
				(_("Queue Manager"), self.queueManager),
			]
		)

	def setLocal(self):
		self.currlist = "local"
		self["key_blue"].text = _("Upload")

	def setRemote(self):
		self.currlist = "remote"
		self["key_blue"].text = _("Download")

	def okQuestion(self, res = None):
		if res:
			self.ok(force = True)

	def getRemoteFile(self):
		remoteFile = self["remote"].getSelection()
		if not remoteFile or not remoteFile[0]:
			return None, None, None

		absRemoteFile = remoteFile[0]
		if remoteFile[1]:
			fileName = absRemoteFile.split('/')[-2]
		else:
			fileName = absRemoteFile.split('/')[-1]

		if len(remoteFile) == 3:
			fileSize = remoteFile[2]
		else:
			fileSize = 0

		return absRemoteFile, fileName, fileSize

	def getLocalFile(self):
		# XXX: isn't this supposed to be an absolute filename? well, it's not for me :-/
		localFile = self["local"].getSelection()
		if not localFile:
			return None, None

		if localFile[1]:
			absLocalFile = localFile[0]
			fileName = absLocalFile.split('/')[-2]
		else:
			fileName = localFile[0]
			absLocalFile = self["local"].getCurrentDirectory() + fileName

		return absLocalFile, fileName

	def renameCallback(self, newName = None):
		if not newName:
			return

		if self.currlist == "remote":
			absRemoteFile, fileName, fileSize = self.getRemoteFile()
			if not fileName:
				return

			directory = self["remote"].getCurrentDirectory()
			sep = '/' if directory != '/' else ''
			newRemoteFile = directory + sep + newName

			def callback(ret = None):
				AddPopup(_("Renamed %s to %s.") % (fileName, newName), MessageBox.TYPE_INFO, -1)
			def errback(ret = None):
				AddPopup(_("Could not rename %s.") % (fileName), MessageBox.TYPE_ERROR, -1)

			self.ftpclient.rename(absRemoteFile, newRemoteFile).addCallback(callback).addErrback(errback)
		else:
			assert(self.currlist == "local")
			absLocalFile, fileName = self.getLocalFile()
			if not fileName:
				return

			directory = self["local"].getCurrentDirectory()
			newLocalFile = os_path.join(directory, newName)

			try:
				os_rename(absLocalFile, newLocalFile)
			except OSError as ose:
				AddPopup(_("Could not rename %s.") % (fileName), MessageBox.TYPE_ERROR, -1)
			else:
				AddPopup(_("Renamed %s to %s.") % (fileName, newName), MessageBox.TYPE_INFO, -1)

	def rename(self):
		if self.queue:
			return

		if self.currlist == "remote":
			if not self.ftpclient:
				return

			absRemoteFile, fileName, fileSize = self.getRemoteFile()
			if not fileName:
				return
		else:
			assert(self.currlist == "local")
			absLocalFile, fileName = self.getLocalFile()
			if not fileName:
				return

		self.session.openWithCallback(
			self.renameCallback,
			NTIVirtualKeyBoard,
			title = _("Enter new filename:"),
			text = fileName,
		)

	def deleteConfirmed(self, ret):
		if not ret:
			return

		if self.currlist == "remote":
			absRemoteFile, fileName, fileSize = self.getRemoteFile()
			if not fileName:
				return

			def callback(ret = None):
				AddPopup(_("Removed %s.") % (fileName), MessageBox.TYPE_INFO, -1)
			def errback(ret = None):
				AddPopup(_("Could not delete %s.") % (fileName), MessageBox.TYPE_ERROR, -1)

			self.ftpclient.removeFile(absRemoteFile).addCallback(callback).addErrback(errback)
		else:
			assert(self.currlist == "local")
			absLocalFile, fileName = self.getLocalFile()
			if not fileName:
				return

			try:
				os_unlink(absLocalFile)
			except OSError as oe:
				AddPopup(_("Could not delete %s.") % (fileName), MessageBox.TYPE_ERROR, -1)
			else:
				AddPopup(_("Removed %s.") % (fileName), MessageBox.TYPE_INFO, -1)

	def delete(self):
		if self.queue:
			return

		if self.currlist == "remote":
			if not self.ftpclient:
				return

			if self["remote"].canDescent():
				self.session.open(
					MessageBox,
					_("Removing directories is not supported."),
					MessageBox.TYPE_WARNING
				)
				return

			absRemoteFile, fileName, fileSize = self.getRemoteFile()
			if not fileName:
				return
		else:
			assert(self.currlist == "local")
			if self["local"].canDescent():
				self.session.open(
					MessageBox,
					_("Removing directories is not supported."),
					MessageBox.TYPE_WARNING
				)
				return

			absLocalFile, fileName = self.getLocalFile()
			if not fileName:
				return

		self.session.openWithCallback(
			self.deleteConfirmed,
			MessageBox,
			_("Are you sure you want to delete %s?") % (fileName)
		)

	def transferListRcvd(self, res, filelist):
		remoteDirectory, _, _ = self.getRemoteFile()
		localDirectory = self["local"].getCurrentDirectory()

		self.queue = [(True, remoteDirectory + file["filename"], localDirectory + file["filename"], file["size"]) for file in filelist.files if file["filetype"] == "-"]
		self.nextQueue()
	
	def nextQueue(self):
		if self.queue:
			# NOTE: put this transfer back if there already is an active one,
			# it will be picked up again when the active transfer is done
			if self.file:
				return

			top = self.queue[0]
			del self.queue[0]
			if top[0]:
				self.getFile(*top[1:])
			else:
				self.putFile(*top[1:])
		elif self.queue is not None:
			self.queue = None
			self["eta"].text = ""
			self["speed"].text = ""
			self["progress"].invalidate()
			AddPopup(_("Queue processed."), MessageBox.TYPE_INFO, -1)

		if self.queueManagerInstance:
			self.queueManagerInstance.updateList(self.queue)

	def transferListFailed(self, res = None):
		self.queue = None
		AddPopup(_("Could not obtain list of files."), MessageBox.TYPE_ERROR, -1)

	def transfer(self):
		if not self.ftpclient or self.queue:
			return

		if self.currlist == "remote":
			# single file transfer is implemented in self.ok
			if not self["remote"].canDescent():
				return self.ok()
			else:
				absRemoteFile, fileName, fileSize = self.getRemoteFile()
				if not fileName:
					return

				filelist = ModifiedFTPFileListProtocol()
				d = self.ftpclient.list(absRemoteFile, filelist)
				d.addCallback(self.transferListRcvd, filelist).addErrback(self.transferListFailed)
		else:
			assert(self.currlist == "local")
			# single file transfer is implemented in self.ok
			if not self["local"].canDescent():
				return self.ok()
			else:
				localDirectory, _ = self.getLocalFile()
				remoteDirectory = self["remote"].getCurrentDirectory()

				def remoteFileExists(absName):
					for file in self["remote"].getFileList():
						if file[0][0] == absName:
							return True
					return False

				self.queue = [(False, remoteDirectory + file, localDirectory + file, remoteFileExists(remoteDirectory + file)) for file in os_listdir(localDirectory) if os_path.isfile(localDirectory + file)]
				self.nextQueue()


	def getFileCallback(self, ret, absRemoteFile, absLocalFile, fileSize):
		if not ret:
			self.nextQueue()
		else:
			self.getFile(absRemoteFile, absLocalFile, fileSize, force=True)

	def getFile(self, absRemoteFile, absLocalFile, fileSize, force=False):
		if not force and os_path.exists(absLocalFile):
			fileName = absRemoteFile.split('/')[-1]
			AddNotificationWithCallback(
				lambda ret: self.getFileCallback(ret, absRemoteFile, absLocalFile, fileSize),
				MessageBox,
				_("A file with this name (%s) already exists locally.\nDo you want to overwrite it?") % (fileName),
			)
		else:
			self.currentLength = 0
			self.lastLength = 0
			self.lastTime = 0
			self.lastApprox = 0
			self.fileSize = fileSize

			try:
				self.file = open(absLocalFile, 'w')
			except IOError as ie:
				# TODO: handle this
				raise ie
			else:
				d = self.ftpclient.retrieveFile(absRemoteFile, self, offset = 0)
				d.addCallback(self.getFinished).addErrback(self.getFailed)

	def putFileCallback(self, ret, absRemoteFile, absLocalFile, remoteFileExists):
		if not ret:
			self.nextQueue()
		else:
			self.putFile(absRemoteFile, absLocalFile, remoteFileExists, force=True)

	def putFile(self, absRemoteFile, absLocalFile, remoteFileExists, force=False):
		if not force and remoteFileExists:
			fileName = absRemoteFile.split('/')[-1]
			AddNotificationWithCallback(
				lambda ret: self.putFileCallback(ret, absRemoteFile, absLocalFile, remoteFileExists),
				MessageBox,
				_("A file with this name (%s) already exists on the remote host.\nDo you want to overwrite it?") % (fileName),
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
			except (IOError, OSError) as e:
				# TODO: handle this
				raise e
			else:
				dC, dL = self.ftpclient.storeFile(absRemoteFile)
				dC.addCallback(sendfile, self.file)

	def ok(self, force = False):
		if self.queue:
			return

		if self.currlist == "remote":
			if not self.ftpclient:
				return

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

				absRemoteFile, fileName, fileSize = self.getRemoteFile()
				if not fileName:
					return

				absLocalFile = self["local"].getCurrentDirectory() + fileName

				self.getFile(absRemoteFile, absLocalFile, fileSize)
		else:
			# Put file/change directory
			assert(self.currlist == "local")
			if self["local"].canDescent():
				self["local"].descent()
			else:
				if not self.ftpclient:
					return

				if self.file:
					self.session.open(
						MessageBox,
						_("There already is an active transfer."),
						type = MessageBox.TYPE_WARNING
					)
					return

				if not self["remote"].isValid:
					return

				absLocalFile, fileName = self.getLocalFile()
				if not fileName:
					return

				def remoteFileExists(absName):
					for file in self["remote"].getFileList():
						if file[0][0] == absName:
							return True
					return False

				absRemoteFile = self["remote"].getCurrentDirectory() + fileName
				self.putFile(absRemoteFile, absLocalFile, remoteFileExists(absRemoteFile))

	def transferFinished(self, msg, type, toRefresh):
		AddPopup(msg, type, -1)

		self["eta"].text = ""
		self["speed"].text = ""
		self["progress"].invalidate()
		self[toRefresh].refresh()
		self.file.close()
		self.file = None

	def putComplete(self, *args):
		if self.queue is not None:
			self.file.close()
			self.file = None

			self.nextQueue()
		else:
			self.transferFinished(
				_("Upload finished."),
				MessageBox.TYPE_INFO,
				"remote"
			)

	def putFailed(self, *args):
		# NOTE: we continue uploading but notify the user of every error though
		# we only display one success notification
		self.transferFinished(
			_("Error during download."),
			MessageBox.TYPE_ERROR,
			"remote"
		)
		if self.queue is not None:
			self.nextQueue()

	def getFinished(self, *args):
		if self.queue is not None:
			self.file.close()
			self.file = None

			self.nextQueue()
		else:
			self.transferFinished(
				_("Download finished."),
				MessageBox.TYPE_INFO,
				"local"
			)

	def getFailed(self, *args):
		# NOTE: we continue downloading but notify the user of every error though
		# we only display one success notification
		self.transferFinished(
			_("Error during download."),
			MessageBox.TYPE_ERROR,
			"local"
		)
		if self.queue is not None:
			self.nextQueue()

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
			self["eta"].text = _("ETA %d:%02d min") % (secLen / 60, secLen % 60)
			self["speed"].text = _("%d kb/s") % (lastApprox)

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
		except IOError as ie:
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
		self["remoteText"].text = _("Remote (not connected)")

	def connectWrapper(self, ret):
		if ret:
			self.connect(ret[1])

	def connect(self, server):
		self.disconnect()

		self.server = server

		if not server:
			return

		username = server.getUsername()
		if not username:
			username = 'anonymous'
			password = 'my@email.com'
		else:
			password = server.getPassword()

		host = server.getAddress()
		passive = server.getPassive()
		port = server.getPort()
		timeout = 30 # TODO: make configurable

		# XXX: we might want to add a guard so we don't try to connect to another host while a previous attempt is not timed out

		creator = ClientCreator(reactor, FTPClient, username, password, passive = passive)
		creator.connectTCP(host, port, timeout).addCallback(self.controlConnectionMade).addErrback(self.connectionFailed)

	def controlConnectionMade(self, ftpclient):
		print("[FTPBrowser] connection established")
		self.ftpclient = ftpclient
		self["remote"].ftpclient = ftpclient
		self["remoteText"].text = _("Remote")

		self["remote"].changeDir(self.server.getPath())

	def connectionFailed(self, *args):
		print("[FTPBrowser] connection failed", args)

		self.server = None
		self["remoteText"].text = _("Remote (not connected)")
		self.session.open(
				MessageBox,
				_("Could not connect to ftp server!"),
				type = MessageBox.TYPE_ERROR,
				timeout = 3,
		)

