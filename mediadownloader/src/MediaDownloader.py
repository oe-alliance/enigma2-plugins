# -*- coding: utf-8 -*-
from __future__ import print_function

# for localized messages
from . import _

# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

# Download
from VariableProgressSource import VariableProgressSource

from Components.config import config
try:
	from urlparse import urlparse, urlunparse
except ImportError as ie:
	from urllib.parse import urlparse, urlunparse

import time

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

def download(url, file, writeProgress = None, contextFactory = None, \
	*args, **kwargs):

	"""Download a remote file and provide current-/total-length.

	@param file: path to file on filesystem, or file-like object.
	@param writeProgress: function or list of functions taking two parameters (pos, length)

	See HTTPDownloader to see what extra args can be passed if remote file
	is accessible via http or https. Both Backends should offer supportPartial.
	"""

	scheme, host, port, path, username, password = _parse(url)

	if scheme == 'ftp':
		from FTPProgressDownloader import FTPProgressDownloader

		if not (username and password):
			username = 'anonymous'
			password = 'my@email.com'

		client = FTPProgressDownloader(
			host,
			port,
			path,
			file,
			username,
			password,
			writeProgress,
			*args,
			**kwargs
		)
		return client.deferred

	# We force username and password here as we lack a satisfying input method
	if username and password:
		from base64 import encodestring

		# twisted will crash if we don't rewrite this ;-)
		url = scheme + '://' + host + ':' + str(port) + path

		basicAuth = encodestring("%s:%s" % (username, password))
		authHeader = "Basic " + basicAuth.strip()
		AuthHeaders = {"Authorization": authHeader}

		if "headers" in kwargs:
			kwargs["headers"].update(AuthHeaders)
		else:
			kwargs["headers"] = AuthHeaders

	from HTTPProgressDownloader import HTTPProgressDownloader
	from twisted.internet import reactor

	factory = HTTPProgressDownloader(url, file, writeProgress, *args, **kwargs)
	if scheme == 'https':
		from twisted.internet import ssl
		if contextFactory is None:
			contextFactory = ssl.ClientContextFactory()
		reactor.connectSSL(host, port, factory, contextFactory)
	else:
		reactor.connectTCP(host, port, factory)

	return factory.deferred

class MediaDownloader(Screen):
	"""Simple Plugin which downloads a given file. If not targetfile is specified the user will be asked
	for a location (see LocationBox). If doOpen is True the Plugin will try to open it after downloading."""

	skin = """<screen name="MediaDownloader" position="center,center" size="540,95" >
			<widget source="wait" render="Label" position="2,10" size="500,30" valign="center" font="Regular;23" />
			<widget source="progress" render="Progress" position="2,40" size="536,20" />
			<widget source="eta" render="Label" position="2,65" size="200,30" font="Regular;23" />
			<widget source="speed" render="Label" position="338,65" size="200,30" halign="right" font="Regular;23" />
		</screen>"""

	def __init__(self, session, file, askOpen = False, downloadTo = None, callback = None):
		Screen.__init__(self, session)

		# Save arguments local
		self.file = file
		self.askOpen = askOpen
		self.filename = downloadTo
		self.callback = callback

		# Init what we need for progress callback
		self.lastLength = 0
		self.lastTime = 0
		self.lastApprox = 0

		# Inform user about whats currently done
		self["wait"] = StaticText(_("Downloading..."))
		self["progress"] = VariableProgressSource()
		self["eta"] = StaticText(_("ETA ??:?? h")) # XXX: we could just leave eta and speed empty
		self["speed"] = StaticText(_("?? kb/s"))

		# Set Limit if we know it already (Server might not tell it)
		if self.file.size:
			self["progress"].writeValues(0, self.file.size*1048576)

		# Call getFilename as soon as we are able to open a new screen
		self.onExecBegin.append(self.getFilename)

	def getFilename(self):
		self.onExecBegin.remove(self.getFilename)

		# If we have a filename (downloadTo provided) start fetching
		if self.filename is not None:
			self.fetchFile()
		# Else open LocationBox to determine where to save
		else:
			# TODO: determine basename without os.path?
			from os import path
			from Screens.LocationBox import LocationBox

			self.session.openWithCallback(
				self.gotFilename,
				LocationBox,
				_("Where to save?"),
				path.basename(self.file.path),
				minFree = self.file.size,
				bookmarks = config.plugins.mediadownloader.bookmarks
			)

	def gotFilename(self, res):
		# If we got a filename try to fetch file
		if res is not None:
			self.filename = res
			self.fetchFile()
		# Else close
		else:
			self.close()

	def fetchFile(self):
		# Fetch file
		d = download(
			self.file.path,
			self.filename,
			[
				self["progress"].writeValues,
				self.gotProgress
			]
		)

		d.addCallback(self.gotFile).addErrback(self.error)

	def gotProgress(self, pos, max):
		newTime = time.time()
		# Check if we're called the first time (got total)
		lastTime = self.lastTime
		if lastTime == 0:
			self.lastTime = newTime

		# We dont want to update more often than every two sec (could be done by a timer, but this should give a more accurate result though it might lag)
		elif int(newTime - lastTime) >= 2:
			newLength = pos

			lastApprox = round(((newLength - self.lastLength) / (newTime - lastTime) / 1024), 2)

			secLen = int(round(((max-pos) / 1024) / lastApprox))
			self["eta"].text = _("ETA %d:%02d min") % (secLen / 60, secLen % 60)
			self["speed"].text = _("%d kb/s") % (lastApprox)

			self.lastApprox = lastApprox
			self.lastLength = newLength
			self.lastTime = newTime

	def openCallback(self, res):
		from Components.Scanner import openFile

		# Try to open file if res was True
		if res and not openFile(self.session, None, self.filename):
			self.session.open(
				MessageBox,
				_("No suitable Viewer found!"),
				type = MessageBox.TYPE_ERROR,
				timeout = 5
			)

		# Calback with Filename on success
		if self.callback is not None:
			self.callback(self.filename)

		self.close()

	def gotFile(self, data = ""):
		# Ask if file should be opened unless told not to
		if self.askOpen:
			self.session.openWithCallback(
				self.openCallback,
				MessageBox,
				_("Do you want to try to open the downloaded file?"),
				type = MessageBox.TYPE_YESNO
			)
		# Otherwise callback and close
		else:
			# Calback with Filename on success
			if self.callback is not None:
				self.callback(self.filename)

			self.close()

	def error(self, msg = ""):
		if msg != "":
			print("[MediaDownloader] Error downloading:", msg)

		self.session.open(
			MessageBox,
			_("Error while downloading file %s") % (self.file.path),
			type = MessageBox.TYPE_ERROR,
			timeout = 3
		)

		# Calback with None on failure
		if self.callback is not None:
			self.callback(None)

		self.close()
