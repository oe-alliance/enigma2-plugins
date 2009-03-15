# -*- coding: utf-8 -*-
# for localized messages
from __init__ import _
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Components.Network import iNetwork
from Components.Sources.List import List
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
from os import path as os_path

from MountView import AutoMountView
from MountEdit import AutoMountEdit
from AutoMount import iAutoMount, AutoMount
from UserManager import UserManager

class AutoMountManager(Screen):
	skin = """
		<screen name="AutoMountManager" position="90,140" size="560,350" title="AutoMountManager">
			<widget source="config" render="Listbox" position="10,10" size="540,220" scrollbarMode="showOnDemand" >
				<convert type="TemplatedMultiContent">
					{"template": [
							MultiContentEntryText(pos = (0, 3), size = (480, 25), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
							MultiContentEntryText(pos = (10, 29), size = (480, 17), font=1, flags = RT_HALIGN_LEFT, text = 2), # index 3 is the Description
							MultiContentEntryPixmapAlphaTest(pos = (500, 1), size = (48, 48), png = 3), # index 4 is the pixmap
						],
					"fonts": [gFont("Regular", 20),gFont("Regular", 14)],
					"itemHeight": 50
					}
				</convert>
			</widget>
			<widget name="introduction" position="90,260" size="300,20" zPosition="10" font="Regular;21" halign="center" transparent="1" />
			<widget name="ButtonRedtext" position="410,305" size="140,21" zPosition="10" font="Regular;21" transparent="1" />
			<widget name="ButtonRed" pixmap="skin_default/buttons/button_red.png" position="390,305" zPosition="10" size="15,16" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/bottombar.png" position="10,250" size="540,120" zPosition="1" transparent="1" alphatest="on" />
		</screen>"""
	def __init__(self, session, iface ,plugin_path):
		self.skin_path = plugin_path
		self.session = session
		self.hostname = None
		self.restartLanRef = None
		Screen.__init__(self, session)
		self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions"],
		{
			"ok": self.keyOK,
			"back": self.exit,
			"cancel": self.exit,
			"red": self.exit,
		})
		self["ButtonRed"] = Pixmap()
		self["ButtonRedtext"] = Label(_("Close"))
		self["introduction"] = Label(_("Press OK to select."))

		self.list = []
		self["config"] = List(self.list)
		self.updateList()
		self.onClose.append(self.cleanup)
		self.onShown.append(self.setWindowTitle)

	def setWindowTitle(self):
		self.setTitle(_("MountManager"))

	def cleanup(self):
		iNetwork.stopRestartConsole()
		iNetwork.stopGetInterfacesConsole()

	def updateList(self):
		self.list = []
		okpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "SystemPlugins/NetworkBrowser/icons/ok.png"))
		self.list.append((_("Add new network mount point"),"add", _("Add a new NFS or CIFS mount point to your Dreambox."), okpng ))
		self.list.append((_("Mountpoints management"),"view", _("View, edit or delete mountpoints on your Dreambox."), okpng ))
		self.list.append((_("User management"),"user", _("View, edit or delete usernames and passwords for your network."), okpng))
		self.list.append((_("Change hostname"),"hostname", _("Change the hostname of your Dreambox."), okpng))
		self["config"].setList(self.list)

	def exit(self):
		self.close()

	def keyOK(self, returnValue = None):
		if returnValue == None:
			returnValue = self["config"].getCurrent()[1]
			if returnValue is "add":
				self.addMount()
			elif returnValue is "view":
				self.viewMounts()
			elif returnValue is "user":
				self.userEdit()
			elif returnValue is "hostname":
				self.hostEdit()

	def addMount(self):
		self.session.open(AutoMountEdit, self.skin_path)

	def viewMounts(self):
		self.session.open(AutoMountView, self.skin_path)

	def userEdit(self):
		self.session.open(UserManager, self.skin_path)

	def hostEdit(self):
		if os_path.exists("/etc/hostname"):
			fp = open('/etc/hostname', 'r')
			self.hostname = fp.read()
			fp.close()
			self.session.openWithCallback(self.hostnameCallback, VirtualKeyBoard, title = (_("Enter new hostname for your Dreambox")), text = self.hostname)

	def hostnameCallback(self, callback = None):
		if callback is not None and len(callback):
			fp = open('/etc/hostname', 'w+')
			fp.write(callback)
			fp.close()
			self.restartLan()

	def restartLan(self):
		iNetwork.restartNetwork(self.restartLanDataAvail)
		self.restartLanRef = self.session.openWithCallback(self.restartfinishedCB, MessageBox, _("Please wait while your network is restarting..."), type = MessageBox.TYPE_INFO, enable_input = False)

	def restartLanDataAvail(self, data):
		if data is True:
			iNetwork.getInterfaces(self.getInterfacesDataAvail)

	def getInterfacesDataAvail(self, data):
		if data is True:
			if self.restartLanRef.execing:
				self.restartLanRef.close(True)

	def restartfinishedCB(self,data):
		if data is True:
			self.session.open(MessageBox, _("Finished restarting your network"), type = MessageBox.TYPE_INFO, timeout = 10, default = False)

