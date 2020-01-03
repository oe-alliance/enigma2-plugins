# -*- coding: utf-8 -*-
from twisted.internet import reactor, defer
from twisted.internet.protocol import Protocol, ClientCreator
from twisted.protocols.ftp import FTPClient, FTPFileListProtocol

from os import SEEK_END

# XXX: did I ever actually test supportPartial?
class FTPProgressDownloader(Protocol):
	"""Download to a file from FTP and keep track of progress."""

	def __init__(self, host, port, path, fileOrName, username = 'anonymous', \
		password = 'my@email.com', writeProgress = None, passive = True, \
		supportPartial = False, *args, **kwargs):

		timeout = 30

		# We need this later
		self.path = path
		self.resume = supportPartial

		# Initialize
		self.currentlength = 0
		self.totallength = None
		if writeProgress and type(writeProgress) is not list:
			writeProgress = [ writeProgress ]
		self.writeProgress = writeProgress

		# Output
		if isinstance(fileOrName, str):
			self.filename = fileOrName
			self.file = None
		else:
			self.file = fileOrName

		creator = ClientCreator(reactor, FTPClient, username, password, passive = passive)

		creator.connectTCP(host, port, timeout).addCallback(self.controlConnectionMade).addErrback(self.connectionFailed)

		self.deferred = defer.Deferred()

	def controlConnectionMade(self, ftpclient):
		# We need the client locally
		self.ftpclient = ftpclient

		# Try to fetch filesize
		self.ftpFetchSize()

	# Handle recieved msg
	def sizeRcvd(self, msgs):
		# Split up return
		code, msg = msgs[0].split()
		if code == '213':
			self.totallength = int(msg)
			for cb in self.writeProgress or [ ]:
				cb(0, self.totallength)

			# We know the size, so start fetching
			self.ftpFetchFile()
		else:
			# Error while reading size, try to list it
			self.ftpFetchList()

	def ftpFetchSize(self):
		d = self.ftpclient.queueStringCommand('SIZE ' + self.path)
		d.addCallback(self.sizeRcvd).addErrback(self.ftpFetchList)

	# Handle recieved msg
	def listRcvd(self, *args):
		# Quit if file not found
		if not len(self.filelist.files):
			self.connectionFailed()
			return

		self.totallength = self.filelist.files[0]['size']
		for cb in self.writeProgress or [ ]:
			cb(0, self.totallength)

		# Invalidate list
		self.filelist = None

		# We know the size, so start fetching
		self.ftpFetchFile()

	def ftpFetchList(self, *args, **kwargs):
		self.filelist = FTPFileListProtocol()
		d = self.ftpclient.list(self.path, self.filelist)
		d.addCallback(self.listRcvd).addErrback(self.connectionFailed)

	def openFile(self):
		if self.resume:
			file = open(self.filename, 'ab')
		else:
			file = open(self.filename, 'wb')

		return (file, file.tell())

	def ftpFetchFile(self):
		offset = 0

		# Finally open file
		if self.file is None:
			try:
				self.file, offset = self.openFile()
			except IOError as ie:
				# TODO: handle exception
				raise ie

		offset = self.resume and offset or 0

		d = self.ftpclient.retrieveFile(self.path, self, offset = offset)
		d.addCallback(self.ftpFinish).addErrback(self.connectionFailed)

	def dataReceived(self, data):
		if not self.file:
			return

		if self.writeProgress:
			self.currentlength += len(data)
			for cb in self.writeProgress:
				cb(self.currentlength, self.totallength)
		try:
			# XXX: why did i always seek? do we really need this?
			if self.resume:
				self.file.seek(0, SEEK_END)

			self.file.write(data)
		except IOError as ie:
			# TODO: handle exception
			self.file = None
			raise ie

	def ftpFinish(self, code = 0, message = None):
		self.ftpclient.quit()
		if self.file is not None:
			self.file.close()
		self.deferred.callback(code)

	def connectionFailed(self, reason = None):
		if self.file is not None:
			self.file.close()
		self.deferred.errback(reason)
