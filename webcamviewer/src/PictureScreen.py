from enigma import loadPic
from enigma import eTimer
from enigma import getDesktop

from Screens.Screen import Screen
from Components.AVSwitch import AVSwitch
from Components.config import config
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap

from FTPDownloader import FTPDownloader
from twisted.web.client import HTTPDownloader
from twisted.internet import reactor
from urlparse import urlparse, urlunparse

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

def download(url, file, contextFactory = None, *args, **kwargs):

	"""Download a remote file from http(s) or ftp.

	@param file: path to file on filesystem, or file-like object.

	See HTTPDownloader to see what extra args can be passed if remote file
	is accessible via http or https. Both Backends should offer supportPartial.
	"""
	scheme, host, port, path, username, password = _parse(url)

	if scheme == 'ftp':
		if not (username and password):
			username = 'anonymous'
			password = 'my@email.com'

		client = FTPDownloader(
			host,
			port,
			path,
			file,
			username,
			password,
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

		if kwargs.has_key("headers"):
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
	prozessing =False # if fetching or converting is active
	autoreload =False
	def __init__(self, session,title,filename, slideshowcallback = None,args=0):
		self.slideshowcallback=slideshowcallback
		self.screentitle = title
		##
		size_w = getDesktop(0).size().width()
		size_h = getDesktop(0).size().height()
		self.skin = """
		<screen position="0,0" size="%i,%i" title="%s" flags=\"wfNoBorder\">
			 <widget name="pixmap" position="0,0" size="%i,%i" backgroundColor=\"black\"/>
		</screen>""" % (size_w,size_h,filename,size_w,size_h)
		Screen.__init__(self, session)
		self.filename = filename
		self["pixmap"] = Pixmap()

		self["actions"] = ActionMap(["WizardActions", "DirectionActions","ChannelSelectBaseActions","ShortcutActions"],
			{
			 "ok": self.do,
			 "back": self.exit,
			 "green":self.AutoReloaderSwitch,
			 }, -1)

		self.onLayoutFinish.append(self.do)

	def AutoReloaderSwitch(self):
		if self.filename.startswith("http") or self.filename.startswith("ftp"):
			if self.autoreload is False:
				self.autoreload = True
				self.do()
			else:
				self.autoreload = False

	def do(self):
		if self.prozessing:
			pass
		elif self.filename.startswith("http") or self.filename.startswith("ftp"):
			self.fetchFile(self.filename)
		else:
			self.sourcefile = self.filename
			self.setPicture(self.filename)

	def exit(self):
		self.cleanUP()
		self.close()

	def cleanUP(self):
		try:
			if os.path.exists("/tmp/loadedfile"):
				os.remove("/tmp/loadedfile")
		except:## OSerror??
			pass

	def fetchFile(self,url):
		self.prozessing =True
		self.setTitle("loading File")
		print "fetching URL ",url
		self.sourcefile = "/tmp/loadedfile"
		download(url,self.sourcefile).addCallback(self.fetchFinished).addErrback(self.fetchFailed)

	def fetchFailed(self,string):
		print "fetch failed",string
		self.setTitle( "fetch failed: "+string)

	def fetchFinished(self,string):
		print "fetching finished "
		self.setPicture(self.sourcefile)

	def setPicture(self,string):
		self.setTitle(self.filename.split("/")[-1])
		pixmap = loadPic(string,getDesktop(0).size().width(),getDesktop(0).size().height(), AVSwitch().getAspectRatioSetting()/2,1, 0,1)
		if pixmap is not None:
			self["pixmap"].instance.setPixmap(pixmap)
		self.prozessing =False

		if self.autoreload is True:
				self.cleanUP()
				self.do()
		elif self.slideshowcallback is not None:
				self.closetimer = eTimer()
				self.closetimer.timeout.get().append(self.slideshowcallback)
				print "waiting ",config.plugins.pictureviewer.slideshowtime.value," seconds for next picture"
				self.closetimer.start(int(config.plugins.pictureviewer.slideshowtime.value))

