# GUI (Screens)
from Components.ConfigList import ConfigListScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from NTIVirtualKeyBoard import NTIVirtualKeyBoard

# GUI (Components)
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Label import Label

# Config
from Components.config import config, ConfigInteger, ConfigSubsection, \
		ConfigText, ConfigPassword, ConfigYesNo, getConfigListEntry

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

class FTPServer:
	def __init__(self, cfg):
		self.cfg = cfg

	def getCfg(self):
		return self.cfg

	def getName(self):
		return self.cfg.name.value

	def getAddress(self):
		return self.cfg.address.value

	def getUsername(self):
		return self.cfg.username.value

	def getPassword(self):
		return self.cfg.password.value

	def getPort(self):
		return self.cfg.port.value

	def getPassive(self):
		return self.cfg.passive.value

	def getPath(self):
		# TODO: implement
		return '/'

	def getURI(self):
		if self.getUsername() != "":
			uri = "ftp://%s:%s@%s:%d%s" % (self.getUsername(), self.getPassword(), self.getAddress(), self.getPort(), self.getPath())
		else:
			uri = "ftp://%s:%d%s" % (self.getAddress(), self.getPort(), self.getPath())
		return uri

	def save(self):
		self.cfg.save()

	def cancel(self):
		self.cfg.cancel()

def ftpserverFromURI(uri, name = ""):
	scheme, host, port, path, username, password = _parse(uri, defaultPort = 21)
	
	newServer = ConfigSubsection()
	config.plugins.ftpbrowser.server.append(newServer)
	newServer.name = ConfigText(fixed_size = False)
	newServer.name.value = name or host
	newServer.address = ConfigText(fixed_size = False)
	newServer.address.value = host
	newServer.username = ConfigText(fixed_size = False)
	newServer.username.value = username
	newServer.password = ConfigPassword()
	newServer.password.value = password
	newServer.port = ConfigInteger(0, (0, 65535))
	newServer.port.value = port
	newServer.passive = ConfigYesNo(False)

	newServer.save()
	config.plugins.ftpbrowser.servercount.value += 1
	config.plugins.ftpbrowser.servercount.save()

	return newServer

class FTPServerEditor(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="560,180" title="FTP Server Editor">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="10,50" size="550,130" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, server):
		Screen.__init__(self, session)

		self.server = server

		self["key_red"] = Label(_("Exit"))
		self["key_green"] = Label(_("OK"))
		self["key_yellow"] = Label("")
		self["key_blue"] = Label(_("Enter URI"))

		ConfigListScreen.__init__(self, [
			getConfigListEntry(_("Name:"), server.cfg.name),
			getConfigListEntry(_("Address:"), server.cfg.address),
			getConfigListEntry(_("Username:"), server.cfg.username),
			getConfigListEntry(_("Password:"), server.cfg.password),
			getConfigListEntry(_("Port:"), server.cfg.port)
		])
		
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"save": self.keySave,
				"cancel": self.keyCancel,
				"blue": self.getURI,
			}, -2)

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("FTP Server Editor"))

	def gotURI(self, res):
		if res:
			cfg = self.server.cfg

			# _parse gets confused without a scheme
			if not res.startswith("ftp://"):
				res = "ftp://" + res
			scheme, host, port, path, username, password = _parse(res, defaultPort = 21)

			cfg.address.value = host
			cfg.username.value = username
			cfg.password.value = password
			cfg.port.value = port

	def getURI(self):
		self.session.openWithCallback(
			self.gotURI,
			NTIVirtualKeyBoard,
			title = _("Enter URI of FTP Server:"),
			text = self.server.getURI(),
		)

	def keySave(self):
		self.saveAll()
		self.close(True)

class FTPServerManager(Screen):
	skin = """
		<screen position="center,center" size="560,420" title="FTP Server Manager" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="list" position="0,50" size="560,360" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.changed = False
		
		self["key_red"] = Label(_("Delete"))
		self["key_green"] = Label(_("Add"))
		self["key_yellow"] = Label(_("Edit"))
		self["key_blue"] = Label(_("Save"))
		self["list"] = MenuList([])
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.exit,
				"ok": self.okClicked,
				"red": self.delete,
				"green": self.add,
				"yellow": self.edit,
				"blue": self.save
			}, -1)
		
		self.onLayoutFinish.extend((
			self.updateServerList,
			self.layoutFinished,
		))

	def layoutFinished(self):
		self.setTitle(_("FTP Server Manager"))

	def updateServerList(self):
		list = [server.name.value for server in config.plugins.ftpbrowser.server]
		self["list"].setList(list)

	def exit(self, server=None):
		if self.changed:
			self.save(False)
		self.close(server)

	def okClicked(self):
		idx = self["list"].getSelectedIndex()
		ftpserverconfig = config.plugins.ftpbrowser
		Len = ftpserverconfig.servercount.value

		if Len and idx < Len:
			server = FTPServer(ftpserverconfig.server[idx])
			self.exit(server)

	def delete(self):
		self.session.openWithCallback(
			self.deleteConfirm,
			MessageBox,
			_("Really delete this entry?\nIt cannot be recovered!")
		)

	def deleteConfirm(self, ret):
		if not ret:
			return

		idx = self["list"].getSelectedIndex()
		ftpserverconfig = config.plugins.ftpbrowser
		Len = ftpserverconfig.servercount.value

		if Len and idx < Len:
			del ftpserverconfig.server[idx]
			ftpserverconfig.servercount.value -= 1
			self.updateServerList()
			self.changed = True

	def add(self):
		newServer = ConfigSubsection()
		config.plugins.ftpbrowser.server.append(newServer)
		newServer.name = ConfigText("Name", fixed_size = False)
		newServer.address = ConfigText("192.168.2.12", fixed_size = False)
		newServer.username = ConfigText("root", fixed_size = False)
		newServer.password = ConfigPassword("dreambox")
		newServer.port = ConfigInteger(21, (1, 65535))
		newServer.passive = ConfigYesNo(False)
		config.plugins.ftpbrowser.servercount.value += 1
		config.plugins.ftpbrowser.servercount.save()

		self.updateServerList()
		self.changed = True

	def edit(self):
		idx = self["list"].getSelectedIndex()
		ftpserverconfig = config.plugins.ftpbrowser
		Len = ftpserverconfig.servercount.value

		if Len and idx < Len:
			self.session.openWithCallback(
				self.editCallback,
				FTPServerEditor,
				FTPServer(ftpserverconfig.server[idx])
			)

	def editCallback(self, ret = False):
		if ret:
			self.updateServerList()
			self.changed = True

	def save(self, showMessageBox=True):
		config.plugins.ftpbrowser.save()
		if showMessageBox:
			self.session.open(
				MessageBox,
				_("Configuration saved."),
				type = MessageBox.TYPE_INFO
			)

