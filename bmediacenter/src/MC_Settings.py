from __future__ import absolute_import
from os import mkdir
from six import ensure_str
from boxbranding import getMachineBrand, getMachineName
from Components.Console import Console
from Components.ConfigList import ConfigList
from Components.config import KEY_LEFT, KEY_RIGHT, KEY_0
from Components.config import config, getConfigListEntry
from Components.ActionMap import NumberActionMap
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Tools.Directories import fileExists
from .__init__ import _  # for localized messages
mcpath = "/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/skins/defaultHD/images/"


class MC_Settings(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.Console = Console()
		self.service_name = 'djmount'
		self["actions"] = NumberActionMap(["SetupActions", "OkCancelActions"],
		{
			"ok": self.keyOK,
			"cancel": self.close,
			"left": self.keyLeft,
			"right": self.keyRight,
			"0": self.keyNumber,
			"1": self.keyNumber,
			"2": self.keyNumber,
			"3": self.keyNumber,
			"4": self.keyNumber,
			"5": self.keyNumber,
			"6": self.keyNumber,
			"7": self.keyNumber,
			"8": self.keyNumber,
			"9": self.keyNumber
		}, -1)
		self.list = []
		self["configlist"] = ConfigList(self.list)
		self.list.append(getConfigListEntry(_("Show MC in Main-Menu"), config.plugins.mc_globalsettings.showinmainmenu))
		self.list.append(getConfigListEntry(_("Show MC in Extension-Menu"), config.plugins.mc_globalsettings.showinextmenu))
		self.list.append(getConfigListEntry(_("UPNP Enabled"), config.plugins.mc_globalsettings.upnp_enable))

	def keyLeft(self):
		self["configlist"].handleKey(KEY_LEFT)

	def keyRight(self):
		self["configlist"].handleKey(KEY_RIGHT)

	def keyNumber(self, number):
		self["configlist"].handleKey(KEY_0 + number)

	def keyOK(self):
		config.plugins.mc_globalsettings.save()
		if config.plugins.mc_globalsettings.upnp_enable.getValue():
			if fileExists("/media/upnp") is False:
				mkdir("/media/upnp")
			self.Console.ePopen('/usr/bin/opkg list_installed ' + self.service_name, self.checkNetworkState)
		else:
			self.close()

	def checkNetworkState(self, str, retval, extra_args):
		result = ensure_str(result)
		if str.find('Collected errors') != -1:
			self.session.openWithCallback(self.close, MessageBox, _("A background update check is is progress, please wait a few minutes and try again."), type=MessageBox.TYPE_INFO, timeout=10, close_on_any_key=True)
		elif not str:
			self.feedscheck = self.session.open(MessageBox, _('Please wait whilst feeds state is checked.'), MessageBox.TYPE_INFO, enable_input=False)
			self.feedscheck.setTitle(_('Checking Feeds'))
			cmd1 = "opkg update"
			self.CheckConsole = Console()
			self.CheckConsole.ePopen(cmd1, self.checkNetworkStateFinished)
		else:
			self.close()

	def checkNetworkStateFinished(self, result, retval, extra_args=None):
		result = ensure_str(result)
		if result.find('bad address') != -1:
			self.session.openWithCallback(self.InstallPackageFailed, MessageBox, _("Your %s %s is not connected to the internet, please check your network settings and try again.") % (getMachineBrand(), getMachineName()), type=MessageBox.TYPE_INFO, timeout=10, close_on_any_key=True)
		elif result.find('wget returned 1') != -1 or result.find('wget returned 255') != -1 or result.find('404 Not Found') != -1:
			self.session.openWithCallback(self.InstallPackageFailed, MessageBox, _("Sorry feeds are down for maintenance, please try again later."), type=MessageBox.TYPE_INFO, timeout=10, close_on_any_key=True)
		else:
			self.session.openWithCallback(self.InstallPackage, MessageBox, _('Your %s %s will be restarted after the installation of service\nReady to install %s ?') % (getMachineBrand(), getMachineName(), self.service_name), MessageBox.TYPE_YESNO)

	def InstallPackage(self, val):
		if val:
			self.doInstall(self.installComplete, self.service_name)
		else:
			self.feedscheck.close()
			self.close()

	def InstallPackageFailed(self, val):
		self.feedscheck.close()
		self.close()

	def doInstall(self, callback, pkgname):
		self.message = self.session.open(MessageBox, _("please wait..."), MessageBox.TYPE_INFO, enable_input=False)
		self.message.setTitle(_('Installing Service'))
		self.Console.ePopen('/usr/bin/opkg install ' + pkgname, callback)

	def installComplete(self, result=None, retval=None, extra_args=None):
		self.session.open(TryQuitMainloop, 2)
