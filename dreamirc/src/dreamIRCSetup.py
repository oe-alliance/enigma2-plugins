from __future__ import print_function
from __future__ import absolute_import
##
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.config import *
from Components.ConfigList import *
from Components.Sources.StaticText import StaticText
from Components.SystemInfo import BoxInfo

import xml.dom.minidom
from xml.dom.minidom import Node
from xml.dom import EMPTY_NAMESPACE
from Tools import XMLTools
from Tools.XMLTools import elementsWithTag, mergeText

from socket import gethostbyname_ex

from .dreamIRCTools import *


class dreamIRCSetupScreen(ConfigListScreen, Screen):
	from enigma import getDesktop
	desk = getDesktop(0)
	x = int(desk.size().width())
	y = int(desk.size().height())
	print("[dreamIRC] setup: current desktop size: %dx%d" % (x, y))

	if (y >= 720):
		skin = """
			<screen position="390,205" size="500,300" title="dreamIRC - edit settings" >
			<widget name="config" position="10,10" size="480,260" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/div-h.png" position="10,245" size="480,2" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/red.png" position="60,250" size="160,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="280,250" size="160,40" alphatest="on" />
			<widget source="key_red" render="Label" position="60,250" zPosition="1" size="150,40" font="Regular;19" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="280,250" zPosition="1" size="150,40" font="Regular;19" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		</screen>"""
	else:
		skin = """
			<screen position="110,145" size="500,300" title="dreamIRC - edit settings" >
			<widget name="config" position="10,10" size="480,260" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/div-h.png" position="10,245" size="480,2" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/red.png" position="60,250" size="160,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="280,250" size="160,40" alphatest="on" />
			<widget source="key_red" render="Label" position="60,250" zPosition="1" size="150,40" font="Regular;19" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="280,250" zPosition="1" size="150,40" font="Regular;19" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		</screen>"""

	def __init__(self, session, args=0):
		Screen.__init__(self, session)
		self.hardware_info = BoxInfo.getItem("model")
		self.device = self.hardware_info.get_device_name()
		self.mac = getMacAddress()
		self.mac_end = self.mac[6:]
		self.dreamIRCconf = ConfigSubsection()
		self.reloadFile()
		list = []
		list.append(getConfigListEntry(_('Nickname'), self.dreamIRCconf.nick))
		if config.usage.setup_level.index > 1:  # advanced
			list.append(getConfigListEntry(_('Passwd'), self.dreamIRCconf.passwd))
		if config.usage.setup_level.index >= 1:  # intermediate+
			list.append(getConfigListEntry(_('Server1'), self.dreamIRCconf.server1))
		if config.usage.setup_level.index > 1:  # advanced
			list.append(getConfigListEntry(_('Server2'), self.dreamIRCconf.server2))
			list.append(getConfigListEntry(_('Server3'), self.dreamIRCconf.server3))
		if config.usage.setup_level.index >= 1:  # intermediate+
			list.append(getConfigListEntry(_('Port'), self.dreamIRCconf.port))
		list.append(getConfigListEntry(_('Channel'), self.dreamIRCconf.channel))
		if config.usage.setup_level.index > 1:  # i
			list.append(getConfigListEntry(_('Debug'), self.dreamIRCconf.debug))

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))

		ConfigListScreen.__init__(self, list)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
				{
						"green": self.saveAndExit,
						"red": self.dontSaveAndExit,
						"cancel": self.dontSaveAndExit
				}, -1)

	def load(self):
		self.reloadFile()
		self.accounts = [ircsupport.IRCAccount(self.type, int(self.nr), str(self.nick), str(self.passwd), str(self.server1), int(self.port), str(self.channel))]
		print(self.accounts)
		return self.accounts

	def reloadFile(self):
		try:
			doc = xml.dom.minidom.parse(accounts_xml)
			root = doc.childNodes[0]
			for node in elementsWithTag(root.childNodes, "account"):
				self.nick = node.getAttribute("nick")
				self.passwd = node.getAttribute("passwd")
				self.server1 = node.getAttribute("server1")
				self.server2 = node.getAttribute("server2")
				self.server3 = node.getAttribute("server3")
				self.port = node.getAttribute("port")
				self.channel = node.getAttribute("channel")
				self.debug = node.getAttribute("debug")
			if ((self.nick.lower() == "dreamircuser") or (self.nick == "") or (self.nick[0] == " ") or (self.nick.lower() == "dm8000-vip")):
				print("[dreamIRC] nickname error... restoring default...")
				self.nick = self.device + "_" + self.mac_end
		except IOError:
			self.type = "IRC"
			self.login = "1"
			self.nick = self.device + "_" + self.mac_end
			self.passwd = ""
			self.server1 = "irc.belwue.de"
			self.server2 = "irc.freenet.de"
			self.server3 = "irc.tu-illmenau.de"
			self.port = "06667"
			self.channel = "#dreamirc"
			self.debug = "False"

		if self.debug != "True" or self.debug != "False":
			self.debug = "False"
		self.dreamIRCconf.nick = ConfigText(default=self.nick, fixed_size=False)
		self.dreamIRCconf.passwd = ConfigText(default=self.passwd, fixed_size=False)
		self.dreamIRCconf.server1 = ConfigText(default=self.server1, fixed_size=False)
		self.dreamIRCconf.server2 = ConfigText(default=self.server2, fixed_size=False)
		self.dreamIRCconf.server3 = ConfigText(default=self.server3, fixed_size=False)
		self.dreamIRCconf.port = ConfigInteger(default=int(self.port), limits=(0, 99999))
		self.dreamIRCconf.channel = ConfigText(default=self.channel, fixed_size=False)
		self.dreamIRCconf.debug = ConfigSelection(default=self.debug, choices=["False", "True"])

	def keySave(self):
		self.accounts = []
		self.type = "IRC"
		self.login = "1"
		self.nick = self.dreamIRCconf.nick.value
		self.passwd = self.dreamIRCconf.passwd.value
		self.server1 = self.dreamIRCconf.server1.value
		self.server2 = self.dreamIRCconf.server2.value
		self.server3 = self.dreamIRCconf.server3.value
		self.port = self.dreamIRCconf.port.value
		self.channel = self.dreamIRCconf.channel.value
		self.debug = self.dreamIRCconf.debug.value
		global accounts_xml
		fp = open(accounts_xml, 'w')
		fp.write("<?xml version=\"1.0\" encoding=\"iso-8859-1\" ?>\n")
		fp.write("<accounts>\n")
		fp.write("    <account type=\"%s\" login=\"%s\" nick=\"%s\" passwd=\"%s\" server1=\"%s\" server2=\"%s\" server3=\"%s\" port=\"%s\" channel=\"%s\" debug=\"%s\" />\n" % (self.type, self.login, self.nick, self.passwd, self.server1, self.server2, self.server3, self.port, self.channel, self.debug))
		fp.write("</accounts>\n")
		fp.close()
		if self.server1:
			self.checkServer(self.server1)
		if self.server2:
			self.checkServer(self.server2)
		if self.server3:
			self.checkServer(self.server3)

	def checkServer(self, server):
			try:
				result = gethostbyname_ex(server)
			except:
				self.session.open(MessageBox, _("irc server %s not responding!\nplease check your network settings and/or irc servername..." % server), MessageBox.TYPE_ERROR)

	def saveAndExit(self):
		for x in self["config"].list:
			x[1].save()
		self.keySave()
		self.close()

	def dontSaveAndExit(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()


class dreamIRCConfig:
	def load(self):
		self.pipe = MessagePipe()
		self.status1 = False
		self.status2 = False
		self.status3 = False
		self.hardware_info = BoxInfo.getItem("model")
		self.device = self.hardware_info.get_device_name()
		self.mac = getMacAddress()
		self.mac_end = self.mac[6:]
		try:
			doc = xml.dom.minidom.parse(accounts_xml)
			root = doc.childNodes[0]
			for node in elementsWithTag(root.childNodes, "account"):
				self.type = node.getAttribute("type")
				self.login = node.getAttribute("login")
				self.nick = node.getAttribute("nick")
				if ((self.nick.lower() == "dreamircuser") or (self.nick == "") or (self.nick[0] == " ") or (self.nick.lower() == "dm8000-vip")):
					print("[dreamIRC] nickname error... restoring default...")
					self.nick = self.device + "_" + self.mac_end
				self.passwd = node.getAttribute("passwd")
				self.server1 = node.getAttribute("server1")  # atm only ip.. cause of probs with theads and dns..
				self.server2 = node.getAttribute("server2")
				self.server3 = node.getAttribute("server3")
				self.port = node.getAttribute("port")
				self.channel = node.getAttribute("channel")
				self.debug = node.getAttribute("debug")  # not used yet.. later will enable/disable console debug out..
		except IOError:
			self.type = "IRC"
			self.login = "1"
			self.nick = self.device + "_" + self.mac_end
			self.passwd = ""
			self.server1 = "irc.freenet.de"
			self.server2 = "irc.freenet.de"
			self.server3 = "irc.tu-illmenau.de"
			self.port = "06667"
			self.channel = "#dreamirc"
			self.debug = ""
		self.server1 = self.server1.strip()
		self.server2 = self.server2.strip()
		self.server3 = self.server3.strip()
		if self.server3:
			try:
				self.result3 = gethostbyname_ex(self.server3)
				if self.result3:
					for ip_tmp3 in self.result3[2]:
						self.ip = ip_tmp3
						self.server = self.server3
						self.status3 = True
			except:
				print("unable to resolve hostname %s..." % self.server3)
		if self.server2:
			try:
				self.result2 = gethostbyname_ex(self.server2)
				if self.result2:
					for ip_tmp2 in self.result2[2]:
						self.ip = ip_tmp2
						self.server = self.server2
						self.status2 = True
			except:
				print("unable to resolve hostname %s..." % self.server2)
		if self.server1:
			try:
				self.result1 = gethostbyname_ex(self.server1)
				if self.result1:
					for ip_tmp1 in self.result1[2]:
						self.ip = ip_tmp1
						self.server = self.server1
						self.status1 = True
			except:
				print("unable to resolve hostname %s..." % self.server1)

		if self.status1 is False and self.status2 is False and self.status3 is False:
			self.pipe.add("ERROR!!! no irc server was valid... please check settings...")
			return False
		else:
			print(" account = type: %s login:%s nick:%s passwd:%s server:%s ip:%s port:%s channel:%s debug:%s " % (self.type, self.login, self.nick, self.passwd, self.server, self.ip, self.port, self.channel, self.debug))
			self.accounts = [ircsupport.IRCAccount(self.type, int(self.login), str(self.nick), str(self.passwd), str(self.ip), int(self.port), str(self.channel))]
			print(self.accounts)
			return self.accounts

	def channel(self):
			doc = xml.dom.minidom.parse(accounts_xml)
			root = doc.childNodes[0]
			for node in elementsWithTag(root.childNodes, "account"):
				self.channel = node.getAttribute("channel")
			return self.channel
