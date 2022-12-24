'''
Configuration screens for EmailClient
'''
from Screens.Screen import Screen
from Screens.Setup import Setup
from Screens.MessageBox import MessageBox
from Components.config import config, getConfigListEntry, ConfigText, ConfigPassword, ConfigSelection, ConfigEnableDisable
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.ActionMap import ActionMap

from . import _, initLog, debug, scaleV, DESKTOP_WIDTH, DESKTOP_HEIGHT  # @UnresolvedImport# pylint: disable-msg=C0103,F0401


class EmailConfigOptions(Setup):
	def __init__(self, session):
		Setup.__init__(self, session, "emailconfig", plugin="Extensions/EmailClient", PluginLanguageDomain="EmailClient")

	def keySave(self):
		if config.plugins.emailimap.debug.isChanged():
			initLog()
		Setup.keySave(self)


class EmailConfigAccount(Setup):
	def __init__(self, session, params=None):
		if params:
			(self._name, self._server, self._port, self._user, self._password, self._interval, self._maxmail, self._listall) = params
		else:
			(self._name, self._server, self._port, self._user, self._password, self._interval, self._maxmail, self._listall) = ("", "", "993", "", "", "60", "50", False)
		self._cName = ConfigText(self._name, fixed_size=False)
		self._cServer = ConfigText(self._server, fixed_size=False)
		self._cPort = ConfigSelection(choices=[("143", "143"), ("993", "993 (SSL)")], default=self._port)
		self._cUser = ConfigText(self._user, fixed_size=False)
		self._cPassword = ConfigPassword(self._password, fixed_size=False)
		self._cInterval = ConfigText(self._interval, fixed_size=False)
		self._cInterval.setUseableChars('0123456789,')
		self._cMaxmail = ConfigText(self._maxmail, fixed_size=False)
		self._cMaxmail.setUseableChars('0123456789,')
		self._cListall = ConfigEnableDisable(self._listall)
		Setup.__init__(self, session, "emailconfigaccount", plugin="Extensions/EmailClient", PluginLanguageDomain="EmailClient")

	def keySave(self):
		debug("[EmailConfigAccount] saving")
		# do some sanity checks
		if not self._cName.value or not self._cServer.value or not self._cUser.value or not self._cPassword.value or not self._cInterval.value or not self._cMaxmail.value:
			self.setFootnote(_("empty values - retry"))
		else:
			if self._cListall.value:
				self.close((self._cName.value, self._cServer.value, self._cPort.value, self._cUser.value, self._cPassword.value, self._cInterval.value, self._cMaxmail.value, 1))
			else:
				self.close((self._cName.value, self._cServer.value, self._cPort.value, self._cUser.value, self._cPassword.value, self._cInterval.value, self._cMaxmail.value, 0))

	def keyCancel(self):
		debug("[EmailConfigAccount] cancel")
		self.close(None)

	def closeRecursive(self):
		debug("[EmailConfigAccount] cancel")
		self.close(None)


class _EmailConfigAccount(ConfigListScreen, Screen):
	width = max(2 * 140 + 100, 550)
	height = 5 * 30 + 50
	buttonsGap = (width - 2 * 140) / 3
	skin = """
		<screen position="%d,%d" size="%d,%d" title="Account Setup" >
		<widget name="config" position="0,0" size="%d,%d" scrollbarMode="showOnDemand" />
		<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<widget name="buttonred" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="buttongreen" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>""" % (
					(DESKTOP_WIDTH - width) / 2, (DESKTOP_HEIGHT - height) / 2, width, height,
					width, height - 50,  # config
					buttonsGap, height - 45,
					2 * buttonsGap + 140, height - 45,
					buttonsGap, height - 45, scaleV(22, 18),
					2 * buttonsGap + 140, height - 45, scaleV(22, 18)
					)

	def __init__(self, session, params=None):
		debug("[EmailConfigAccount] __init__")
		self._session = session
		Screen.__init__(self, session)
		self.list = []
		ConfigListScreen.__init__(self, self.list, session=session)
		self["buttonred"] = Label(_("cancel"))
		self["buttongreen"] = Label(_("ok"))
		self["setupActions"] = ActionMap(["SetupActions"],
		{
			"green": self.save,
			"red": self.cancel,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
		}, -2)

		if params:
			(self._name, self._server, self._port, self._user, self._password, self._interval, self._maxmail, self._listall) = params
		else:
			(self._name, self._server, self._port, self._user, self._password, self._interval, self._maxmail, self._listall) = ("", "", "993", "", "", "60", "50", False)
		self._cName = ConfigText(self._name, fixed_size=False)
		self._cServer = ConfigText(self._server, fixed_size=False)
		self._cPort = ConfigSelection(choices=[("143", "143"), ("993", "993 (SSL)")], default=self._port)
		self._cUser = ConfigText(self._user, fixed_size=False)
		self._cPassword = ConfigPassword(self._password, fixed_size=False)
		self._cInterval = ConfigText(self._interval, fixed_size=False)
		self._cInterval.setUseableChars('0123456789,')
		self._cMaxmail = ConfigText(self._maxmail, fixed_size=False)
		self._cMaxmail.setUseableChars('0123456789,')
		self._cListall = ConfigEnableDisable(self._listall)

		self.list = [
					getConfigListEntry(_("account name"), self._cName),
					getConfigListEntry(_("IMAP Server"), self._cServer),
					getConfigListEntry(_("IMAP Port"), self._cPort),
					getConfigListEntry(_("user name"), self._cUser),
					getConfigListEntry(_("password"), self._cPassword),
					getConfigListEntry(_("mail check interval (minutes)"), self._cInterval),
					getConfigListEntry(_("maximum mail size to fetch"), self._cMaxmail),
					getConfigListEntry(_("list all mailboxes"), self._cListall)
					]
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def save(self):
		debug("[EmailConfigAccount] saving")
		# do some sanity checks
		if not self._cName.value or not self._cServer.value or not self._cUser.value or not self._cPassword.value or not self._cInterval.value or not self._cMaxmail.value:
			self._session.open(MessageBox, _("empty values - retry"), type=MessageBox.TYPE_ERROR, timeout=config.plugins.emailimap.timeout.value)
		else:
			if self._cListall.value:
				self.close((self._cName.value, self._cServer.value, self._cPort.value, self._cUser.value, self._cPassword.value, self._cInterval.value, self._cMaxmail.value, 1))
			else:
				self.close((self._cName.value, self._cServer.value, self._cPort.value, self._cUser.value, self._cPassword.value, self._cInterval.value, self._cMaxmail.value, 0))

	def cancel(self):
		debug("[EmailConfigAccount] cancel")
		self.close(None)
