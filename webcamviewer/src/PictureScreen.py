# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from twisted.web.client import HTTPDownloader
from twisted.internet import reactor
from six import ensure_binary
from six.moves.urllib.parse import urlparse, urlunparse
from enigma import ePicLoad, eTimer, getDesktop
from Components.config import config
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Screens.Screen import Screen
from .FTPDownloader import FTPDownloader


def _parse(url, defaultPort=None):
	url = url.strip()
	parsed = urlparse(url)
	scheme = parsed[0]
	filepath = urlunparse((b'', b'') + (parsed[2:]))
	if defaultPort is None:
		if scheme == 'https':
			defaultPort = 443
		elif scheme == 'ftp':
			defaultPort = 21
		else:
			defaultPort = 80

	host, port = parsed[1], defaultPort

	if b'@' in host:
		username, host = host.split('@')
		if b':' in username:
			username, password = username.split(':')
		else:
			password = ""
	else:
		username = ""
		password = ""

	if b':' in host:
		host, port = host.split(':')
		port = int(port)

	if filepath == "":
		filepath = "/"

	return scheme, host, port, filepath, username, password


def download(url, file, contextFactory=None, *args, **kwargs):
	"""Download a remote file from http(s) or ftp.

	@param file: filepath to file on filesystem, or file-like object.

	See HTTPDownloader to see what extra args can be passed if remote file
	is accessible via http or https. Both Backends should offer supportPartial.
	"""
	scheme, host, port, filepath, username, password = _parse(url)

	if scheme == 'ftp':
		if not (username and password):
			username = 'anonymous'
			password = 'my@email.com'

		client = FTPDownloader(
			host,
			port,
			filepath,
			file,
			username,
			password,
			*args,
			**kwargs
		)
		return client.deferred

	# We force username and password here as we lack a satisfying input method
	if username and password:
		from six import PY3
		from base64 import b64encode

		# twisted will crash if we don't rewrite this ;-)
		url = '%s://%s:%s%s' % (scheme, host, port, filepath)

		base64string = "%s:%s" % (username, password)
		base64string = b64encode(ensure_binary(base64string))
		if PY3:
			base64string.decode()
		AuthHeaders = {"Authorization": "Basic %s" % base64string}

		if "headers" in kwargs:
			kwargs["headers"].update(AuthHeaders)
		else:
			kwargs["headers"] = AuthHeaders

	factory = HTTPDownloader(url, file, *args, **kwargs)
	if scheme == 'https':
		from twisted.internet import ssl
		if contextFactory is None:
			contextFactory = ssl.ClientContextFactory()
		reactor.connectSSL(host, port, factory, contextFactory)
	else:
		reactor.connectTCP(host, port, factory)

	return factory.deferred


class PictureScreen(Screen):
	skin = ""
	processing = False  # if fetching or converting is active
	autoreload = False

	def __init__(self, session, title, filename, slideshowcallback=None, args=0):
		self.slideshowcallback = slideshowcallback
		self.screentitle = title
		self.filename = filename

		size_w = getDesktop(0).size().width()
		size_h = getDesktop(0).size().height()
		self.skin = """
		<screen position="0,0" size="%i,%i" title="%s" flags=\"wfNoBorder\">
			<widget name="pixmap" position="0,0" size="%i,%i" backgroundColor=\"black\"/>
		</screen>""" % (size_w, size_h, filename, size_w, size_h)
		Screen.__init__(self, session)

		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.setPictureCB)
		self.picload.setPara((size_w, size_h, 1, 1, False, 1, '#ff000000'))
		self["pixmap"] = Pixmap()

		self.paused = False

		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ChannelSelectBaseActions", "ShortcutActions"], {
			"ok": self.do,
			"back": self.exit,
			"green": self.AutoReloaderSwitch,
			"yellow": self.pause,
			"red": self.prev,
			"blue": self.next,
		}, -1)

		self.onLayoutFinish.append(self.do)

	def AutoReloaderSwitch(self):
		if self.filename.startswith(("http://", "https://", "ftp://")):
			if not self.autoreload:
				self.autoreload = True
				self.do()
			else:
				self.autoreload = False

		if self.paused:
			self.paused = False
			self.slideshowcallback()
			self.closetimer.start(int(config.plugins.pictureviewer.slideshowtime.value))

	def do(self):
		if self.processing:
			pass
		elif self.filename.startswith((ensure_binary("http://"), ensure_binary("https://"), ensure_binary("ftp://"))):
			self.fetchFile(self.filename)
		else:
			self.sourcefile = self.filename
			self.setPicture(self.filename)

	def exit(self):
		self.cleanUP()
		self.close()

	def cleanUP(self):
		try:
			if exists("/tmp/loadedfile"):
				remove("/tmp/loadedfile")
		except:  # OSerror??
			pass

	def fetchFile(self, url):
		self.processing = True
		self.setTitle("loading File")
		print("fetching URL", url)
		self.sourcefile = "/tmp/loadedfile"
		download(url, self.sourcefile).addCallback(self.fetchFinished).addErrback(self.fetchFailed)

	def fetchFailed(self, string):
		print("fetch failed", string)
		self.setTitle("fetch failed: %s" % string)

	def fetchFinished(self, string):
		print("fetching finished")
		self.setPicture(self.sourcefile)

	def setPicture(self, string):
		if not self.paused:
			self.setTitle(self.screentitle)
		else:
			self.setTitle("%s:%s" % (_("pause"), self.screentitle))
		self.picload.startDecode(string)

	def setPictureCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr is not None:
			self["pixmap"].instance.setPixmap(ptr)
		self.processing = False

		if self.autoreload is True:
				self.cleanUP()
				self.do()
		elif self.slideshowcallback is not None:
				self.closetimer = eTimer()
				self.closetimer.timeout.get().append(self.slideshowcallback)
				print("waiting", config.plugins.pictureviewer.slideshowtime.value, "seconds for next picture")
				if not self.paused:
					self.closetimer.start(int(config.plugins.pictureviewer.slideshowtime.value))

	def pause(self):
		if not self.slideshowcallback:
			return
		if not self.paused:
			self.closetimer.stop()
			self.paused = True

			self.setTitle("%s:%s" % (_("pause"), self.filename.split("/")[-1]))
		else:
			self.paused = False

			self.setTitle(self.filename.split("/")[-1])
			self.slideshowcallback()
			self.closetimer.start(int(config.plugins.pictureviewer.slideshowtime.value))

	def prev(self):
		if not self.slideshowcallback:
			return
		if not self.paused:
			self.closetimer.stop()
			self.paused = True
		self.slideshowcallback(prev=True)

	def next(self):
		if not self.slideshowcallback:
			return
		if not self.paused:
			self.closetimer.stop()
			self.paused = True
		self.slideshowcallback()
