# for localized messages
from . import _

# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

# GUI (Components)
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Label import Label
from Components.FileList import FileList, FileEntryComponent
from Components.Button import Button

# FTP Client
from twisted.internet import reactor, defer
from twisted.internet.protocol import Protocol, ClientCreator
from twisted.protocols.ftp import FTPClient, FTPFileListProtocol

# For new and improved _parse
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
		self.list = [FileEntryComponent(name = file['filename'], absolute = self.current_directory + '/' + file['filename'], isDir = True if file['filetype'] == 'd' else False) for file in self.filelist.files]
		if self.current_directory != "/":
			self.list.insert(0, FileEntryComponent(name = "<" +_("Parent Directory") + ">", absolute = '/'.join(self.current_directory.split('/')[:-1]) + '/', isDir = True))
		self.l.setList(self.list)

	def listFailed(self, *args):
		if self.current_directory != "/":
			self.list = [FileEntryComponent(name = "<" +_("Parent Directory") + ">", absolute = '/'.join(self.current_directory.split('/')[:-1]) + '/', isDir = True)]
		else:
			self.list = []
		self.l.setList(self.list)

class FTPBrowser(Screen):
	skin = """
		<screen name="FTPBrowser" position="100,100" size="550,400" title="FTP Browser" >
			<widget name="local" position="20,10" size="220,350" scrollbarMode="showOnDemand" />
			<widget name="remote" position="245,10" size="220,350" scrollbarMode="showOnDemand" />
			<ePixmap name="red" position="0,360" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="140,360" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,360" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue" position="420,360" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,360" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,360" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="280,360" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="420,360" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.ftpclient = None
		self.currlist = "remote"
		self["local"] = FileList("/media/hdd")
		self["remote"] = FTPFileList()
		self["key_red"] = Button("")
		self["key_green"] = Button("")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		URI = "ftp://root@localhost:21" # TODO: make configurable
		self.connect(URI)

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions", 
			{
				"ok": (self.ok, _("enter directory/get file/put file")),
				"cancel": (self.cancel , _("close")),
			}, -2)

		self["ChannelSelectBaseActions"] = HelpableActionMap(self, "ChannelSelectBaseActions",
			{
				"nextBouquet": (self.setLocal, _("Select local file list")),
				"prevBouquet": (self.setRemote, _("Select remote file list")),
			})

		self["actions"] = ActionMap(["DirectionActions"],
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

	def ok(self):
		if self.currlist == "remote":
			# Get file/change directory
			if self["remote"].canDescent():
				self["remote"].descent()
			else:
				# XXX: implement
				pass
		else:
			# Put file/change directory
			assert(self.currlist == "local")
			if self["local"].canDescent():
				self["local"].descent()
			else:
				# XXX: implement
				pass

	def cancel(self):
		# TODO: anything else?
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
		if args:
			print args[0]
		self.session.open(
				MessageBox,
				_("Could not connect to ftp server!\nClosing."),
				type = MessageBox.TYPE_ERROR,
				timeout = 3,
		)

