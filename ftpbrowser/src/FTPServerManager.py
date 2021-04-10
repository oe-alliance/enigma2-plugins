# for localized messages
from . import _

# GUI (Screens)
from Components.ConfigList import ConfigListScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Plugins.SystemPlugins.Toolkit.NTIVirtualKeyBoard import NTIVirtualKeyBoard

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText

# Config
from Components.config import config, ConfigInteger, ConfigSubsection, \
		ConfigText, ConfigPassword, ConfigYesNo, getConfigListEntry

# For new and improved _parse
from six.moves.urllib.parse import urlparse, urlunparse

def _parse(url, defaultPort=None):
	url = url.strip()
	parsed = urlparse(url)
	scheme = parsed[0]
	path = urlunparse(('', '') + parsed[2:])

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

def ftpserverFromURI(uri, name="", save=True):
	scheme, host, port, path, username, password = _parse(uri, defaultPort=21)
	
	newServer = ConfigSubsection()
	if save:
		config.plugins.ftpbrowser.server.append(newServer)
	newServer.name = ConfigText(fixed_size=False)
	newServer.name.value = name or host
	newServer.address = ConfigText(fixed_size=False)
	newServer.address.value = host
	newServer.username = ConfigText(fixed_size=False)
	newServer.username.value = username
	newServer.password = ConfigPassword()
	newServer.password.value = password
	newServer.port = ConfigInteger(0, (0, 65535))
	newServer.port.value = port
	newServer.passive = ConfigYesNo(False)

	if save:
		newServer.save()
		config.plugins.ftpbrowser.servercount.value += 1
		config.plugins.ftpbrowser.servercount.save()

	return FTPServer(newServer)

class FTPServerEditor(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="560,180" title="FTP Server Editor">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_blue" render="Label"  position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="10,50" size="550,130" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, server):
		Screen.__init__(self, session)

		self.onChangedEntry = []
		self.setup_title = _("FTP Server Editor")
		self.server = server

		self["key_red"] = StaticText(_("Exit"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText(_("Enter URI"))

		ConfigListScreen.__init__(self, [
			getConfigListEntry(_("Name:"), server.cfg.name),
			getConfigListEntry(_("Address:"), server.cfg.address),
			getConfigListEntry(_("Username:"), server.cfg.username),
			getConfigListEntry(_("Password:"), server.cfg.password),
			getConfigListEntry(_("Port:"), server.cfg.port),
			getConfigListEntry(_("Passive:"), server.cfg.passive),
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

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def gotURI(self, res):
		if res:
			cfg = self.server.cfg

			# _parse gets confused without a scheme
			if not res.startswith("ftp://"):
				res = "ftp://" + res
			scheme, host, port, path, username, password = _parse(res, defaultPort=21)

			cfg.address.value = host
			cfg.username.value = username
			cfg.password.value = password
			cfg.port.value = port

	def getURI(self):
		self.session.openWithCallback(
			self.gotURI,
			NTIVirtualKeyBoard,
			title=_("Enter URI of FTP Server:"),
			text=self.server.getURI(),
		)

	def keySave(self):
		self.saveAll()
		self.close(True)

class FTPServerManagerSummary(Screen):
	skin = """
	<screen position="0,0" size="132,64">
		<widget source="parent.Title" render="Label" position="6,4" size="120,21" font="Regular;18" />
		<widget source="parent.list" render="Label" position="6,25" size="120,21" font="Regular;16">
			<convert type="StringListSelection" />
		</widget>
		<widget source="global.CurrentTime" render="Label" position="56,46" size="82,18" font="Regular;16" >
			<convert type="ClockToText">WithSeconds</convert>
		</widget>
	</screen>"""

class FTPServerManager(Screen):
	skin = """
		<screen position="center,center" size="560,420" title="FTP Server Manager" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="list" render="Listbox" position="0,50" size="560,360" scrollbarMode="showAlways">
				<convert type="TemplatedMultiContent">
					{"template": [
							MultiContentEntryText(pos=(1,1), size=(540,22), text = 0, font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
						],
					  "fonts": [gFont("Regular", 20)],
					  "itemHeight": 24
					 }
				</convert>
			</widget>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.changed = False

		self["key_red"] = StaticText(_("Delete"))
		self["key_green"] = StaticText(_("Add"))
		self["key_yellow"] = StaticText(_("Edit"))
		self["key_blue"] = StaticText(_("Save"))
		self["list"] = List([])
		
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

	def createSummary(self):
		return FTPServerManagerSummary

	def layoutFinished(self):
		self.setTitle(_("FTP Server Manager"))

	def updateServerList(self):
		list = [(server.name.value,) for server in config.plugins.ftpbrowser.server]
		self["list"].setList(list)

	def exit(self, server=None):
		if self.changed:
			self.save(False)
		self.close(server)

	def okClicked(self):
		idx = self["list"].index
		if idx is None:
			return

		ftpserverconfig = config.plugins.ftpbrowser
		Len = ftpserverconfig.servercount.value

		if Len and idx < Len:
			server = FTPServer(ftpserverconfig.server[idx])
			self.exit(server)

	def delete(self):
		idx = self["list"].index
		if idx is None:
			return

		self.session.openWithCallback(
			self.deleteConfirm,
			MessageBox,
			_("Really delete this entry?\nIt cannot be recovered!")
		)

	def deleteConfirm(self, ret):
		if not ret:
			return

		idx = self["list"].index
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
		newServer.name = ConfigText("Name", fixed_size=False)
		newServer.address = ConfigText("192.168.2.12", fixed_size=False)
		newServer.username = ConfigText("root", fixed_size=False)
		newServer.password = ConfigPassword("dreambox")
		newServer.port = ConfigInteger(21, (1, 65535))
		newServer.passive = ConfigYesNo(False)
		config.plugins.ftpbrowser.servercount.value += 1
		config.plugins.ftpbrowser.servercount.save()

		self.updateServerList()
		self.changed = True

	def edit(self):
		idx = self["list"].index
		ftpserverconfig = config.plugins.ftpbrowser
		Len = ftpserverconfig.servercount.value

		if idx is not None and Len and idx < Len:
			self.session.openWithCallback(
				self.editCallback,
				FTPServerEditor,
				FTPServer(ftpserverconfig.server[idx])
			)

	def editCallback(self, ret=False):
		if ret:
			self.updateServerList()
			self.changed = True

	def save(self, showMessageBox=True):
		config.plugins.ftpbrowser.save()
		if showMessageBox:
			self.session.open(
				MessageBox,
				_("Configuration saved."),
				type=MessageBox.TYPE_INFO
			)

