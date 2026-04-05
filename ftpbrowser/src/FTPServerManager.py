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
from Components.config import config, ConfigInteger, ConfigSelection, ConfigSubsection, \
        ConfigText, ConfigPassword, ConfigYesNo, getConfigListEntry

# For new and improved _parse
from urllib.parse import urlparse, urlunparse


def _parse(url, defaultPort=None):
    url = url.strip()
    parsed = urlparse(url)
    scheme = parsed[0]
    path = urlunparse(('', '') + parsed[2:])

    if defaultPort is None:
        if scheme == 'https':
            defaultPort = 443
        elif scheme == 'sftp':
            defaultPort = 22
        elif scheme == 'ftp':
            defaultPort = 21
        else:
            defaultPort = 80

    host, port = parsed[1], defaultPort

    if '@' in host:
        username, host = host.split('@', 1)
        if ':' in username:
            username, password = username.split(':', 1)
        else:
            password = ""
    else:
        username = ""
        password = ""

    if ':' in host:
        host, port = host.rsplit(':', 1)
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

    def getProtocol(self):
        return getattr(self.cfg, 'protocol', None) and self.cfg.protocol.value or 'ftp'

    def getAddress(self):
        return self.cfg.address.value

    def getUsername(self):
        return self.cfg.username.value

    def getPassword(self):
        return self.cfg.password.value

    def getPort(self):
        return self.cfg.port.value

    def getPassive(self):
        return getattr(self.cfg, 'passive', None) and self.cfg.passive.value or False

    def getPath(self):
        return getattr(self.cfg, 'path', None) and self.cfg.path.value or '/'

    def getURI(self):
        scheme = self.getProtocol()
        if self.getUsername() != "":
            uri = "%s://%s:%s@%s:%d%s" % (scheme, self.getUsername(), self.getPassword(), self.getAddress(), self.getPort(), self.getPath())
        else:
            uri = "%s://%s:%d%s" % (scheme, self.getAddress(), self.getPort(), self.getPath())
        return uri

    def save(self):
        self.cfg.save()

    def cancel(self):
        self.cfg.cancel()


def ftpserverFromURI(uri, name="", save=True):
    defaultPort = 22 if uri.startswith('sftp://') else 21
    scheme, host, port, path, username, password = _parse(uri, defaultPort=defaultPort)
    if scheme not in ('ftp', 'sftp'):
        scheme = 'ftp'

    newServer = ConfigSubsection()
    if save:
        config.plugins.ftpbrowser.server.append(newServer)
    newServer.name = ConfigText(fixed_size=False)
    newServer.name.value = name or host
    newServer.protocol = ConfigSelection(default=scheme, choices=[('ftp', 'FTP'), ('sftp', 'SFTP')])
    newServer.address = ConfigText(fixed_size=False)
    newServer.address.value = host
    newServer.username = ConfigText(fixed_size=False)
    newServer.username.value = username
    newServer.password = ConfigPassword()
    newServer.password.value = password
    newServer.port = ConfigInteger(0, (0, 65535))
    newServer.port.value = port
    newServer.path = ConfigText(fixed_size=False)
    newServer.path.value = path or '/'
    newServer.passive = ConfigYesNo(False)

    if save:
        newServer.save()
        config.plugins.ftpbrowser.servercount.value += 1
        config.plugins.ftpbrowser.servercount.save()

    return FTPServer(newServer)


class FTPServerEditor(ConfigListScreen, Screen):
    skin = """
        <screen position="center,center" size="820,340" title="FTP Server Editor">
            <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
            <widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget source="key_blue" render="Label"  position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget name="config" position="10,50" size="800,280" scrollbarMode="showOnDemand" />
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
            getConfigListEntry(_("Protocol:"), server.cfg.protocol),
            getConfigListEntry(_("Address:"), server.cfg.address),
            getConfigListEntry(_("Username:"), server.cfg.username),
            getConfigListEntry(_("Password:"), server.cfg.password),
            getConfigListEntry(_("Port:"), server.cfg.port),
            getConfigListEntry(_("Path:"), server.cfg.path),
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

            if not (res.startswith("ftp://") or res.startswith("sftp://")):
                res = "ftp://" + res
            defaultPort = 22 if res.startswith('sftp://') else 21
            scheme, host, port, path, username, password = _parse(res, defaultPort=defaultPort)

            cfg.protocol.value = scheme if scheme in ('ftp', 'sftp') else 'ftp'
            cfg.address.value = host
            cfg.username.value = username
            cfg.password.value = password
            cfg.port.value = port
            cfg.path.value = path or '/'

    def getURI(self):
        self.session.openWithCallback(
            self.gotURI,
            NTIVirtualKeyBoard,
            title=_("Enter URI of FTP/SFTP Server:"),
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
            <widget source="key_blue" render="Label"  position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
            <widget source="list" render="Listbox" position="10,50" size="540,360" scrollbarMode="showOnDemand">
                <convert type="StringList" />
            </widget>
        </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self.setTitle(_("FTP Server Manager"))

        self.serverlist = [FTPServer(x) for x in config.plugins.ftpbrowser.server]
        self["list"] = List([(x.getName(), x) for x in self.serverlist])
        self["key_red"] = StaticText(_("Exit"))
        self["key_green"] = StaticText(_("Bearbeiten"))
        self["key_yellow"] = StaticText(_("New"))
        self["key_blue"] = StaticText(_("Delete"))

        self["actions"] = ActionMap(["WizardActions", "MenuActions", "ColorActions"],
            {
                "ok": self.ok,
                "back": self.close,
                "red": self.close,
                "green": self.edit,
                "yellow": self.new,
                "blue": self.delete,
                "menu": self.edit,
            }, -1)

        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self.setTitle(_("FTP Server Manager"))

    def createSummary(self):
        return FTPServerManagerSummary

    def updateServerList(self):
        self.serverlist = [FTPServer(x) for x in config.plugins.ftpbrowser.server]
        self["list"].setList([(x.getName(), x) for x in self.serverlist])

    def editCallback(self, ret=False):
        if ret:
            self.updateServerList()

    def edit(self):
        cur = self["list"].getCurrent()
        if cur:
            self.session.openWithCallback(self.editCallback, FTPServerEditor, cur[1])

    def newCallback(self, ret=False):
        if ret:
            self.updateServerList()

    def new(self):
        self.session.openWithCallback(self.newCallback, FTPServerEditor, ftpserverFromURI('ftp://', save=True))

    def delete(self):
        cur = self["list"].getCurrent()
        if cur:
            server = cur[1]
            cfg = server.getCfg()
            config.plugins.ftpbrowser.server.remove(cfg)
            config.plugins.ftpbrowser.servercount.value -= 1
            config.plugins.ftpbrowser.servercount.save()
            self.updateServerList()

    def ok(self):
        cur = self["list"].getCurrent()
        self.close(cur and cur[1])
