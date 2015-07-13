# -*- coding: utf-8 -*-
# for localized messages
from __init__ import _
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.config import config, ConfigIP, NoSave, ConfigText, ConfigEnableDisable, ConfigPassword, ConfigSelection, getConfigListEntry, ConfigYesNo
from Components.ConfigList import ConfigListScreen
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap, NumberActionMap
from enigma import ePoint
from AutoMount import iAutoMount, AutoMount
from re import sub as re_sub

from boxbranding import getImageDistro

class AutoMountEdit(Screen, ConfigListScreen):
	skin = """
		<screen name="AutoMountEdit" position="center,center" size="560,450" title="MountEdit">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget name="config" position="5,50" size="550,250" zPosition="1" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,420" zPosition="1" size="560,2" />
			<widget source="introduction" render="Label" position="10,430" size="540,21" zPosition="10" font="Regular;21" halign="center" valign="center" backgroundColor="#25062748" transparent="1"/>
			<widget name="VKeyIcon" pixmap="skin_default/buttons/key_text.png" position="10,430" zPosition="10" size="35,25" transparent="1" alphatest="on" />
			<widget name="HelpWindow" pixmap="skin_default/vkey_icon.png" position="160,350" zPosition="1" size="1,1" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session, plugin_path, mountinfo = None, newmount = True):
		self.skin_path = plugin_path
		self.session = session
		Screen.__init__(self, self.session)

		self.onChangedEntry = [ ]
		self.mountinfo = mountinfo
		self.newmount = newmount
		if self.mountinfo is None:
			#Initialize blank mount enty
			self.mountinfo = { 'isMounted': False, 'mountusing': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, 'username': False, 'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }

		self.applyConfigRef = None
		self.updateConfigRef = None
		self.mounts = iAutoMount.getMountsList()
		self.createConfig()

		self["actions"] = NumberActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.ok,
			"back": self.close,
			"cancel": self.close,
			"red": self.close,
			"green": self.ok,
		}, -2)

		self["VirtualKB"] = ActionMap(["VirtualKeyboardActions"],
		{
			"showVirtualKeyboard": self.KeyText,
		}, -2)

		self.list = []
		ConfigListScreen.__init__(self, self.list,session = self.session)
		self.createSetup()
		self.onLayoutFinish.append(self.layoutFinished)
		# Initialize Buttons
		self["VKeyIcon"] = Pixmap()
		self["HelpWindow"] = Pixmap()
		self["introduction"] = StaticText(_("Press OK to activate the settings."))
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self.selectionChanged()

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

	def layoutFinished(self):
		self.setup_title = _("Mounts editor")
		Screen.setTitle(self, _(self.setup_title))
		self["VKeyIcon"].hide()
		self["VirtualKB"].setEnabled(False)
		self["HelpWindow"].hide()

	# helper function to convert ips from a sring to a list of ints
	def convertIP(self, ip):
		strIP = ip.split('.')
		ip = []
		for x in strIP:
			ip.append(int(x))
		return ip

	def exit(self):
		self.close()

	def createConfig(self):
		self.mountusingEntry = None
		self.sharenameEntry = None
		self.mounttypeEntry = None
		self.activeEntry = None
		self.ipEntry = None
		self.sharedirEntry = None
		self.optionsEntry = None
		self.usernameEntry = None
		self.passwordEntry = None
		self.hdd_replacementEntry = None

		self.mountusing = []
		self.mountusing.append(("autofs", _("AUTOFS (mount as needed)")))
		self.mountusing.append(("fstab", _("FSTAB (mount at boot)")))
		self.mountusing.append(("enigma2", _("Enigma2 (mount using enigma2)")))
		self.mountusing.append(("old_enigma2", _("Enigma2 old format (mount using linux)")))

		self.sharetypelist = []
		self.sharetypelist.append(("cifs", _("CIFS share")))
		self.sharetypelist.append(("nfs", _("NFS share")))

		mountusing_default = "fstab"
		if getImageDistro() in ("openvix", "easy-gui-aus", "beyonwiz", "openatv", "openhdf"):
			mountusing_default = "autofs"

		if self.mountinfo.has_key('mountusing'):
			mountusing = self.mountinfo['mountusing']
			if mountusing is False:
				mountusing = mountusing_default
		else:
				mountusing = mountusing_default

		if self.mountinfo.has_key('mounttype'):
			mounttype = self.mountinfo['mounttype']
			if mounttype is False:
				mounttype = "nfs"
		else:
			mounttype = "nfs"

		if self.mountinfo.has_key('active'):
			active = self.mountinfo['active']
			if active == 'True':
				active = True
			if active == 'False':
				active = False
		else:
			active = True
		if self.mountinfo.has_key('ip'):
			if self.mountinfo['ip'] is False:
				ip = [192, 168, 0, 0]
			else:
				ip = self.convertIP(self.mountinfo['ip'])
		else:
			ip = [192, 168, 0, 0]

		if mounttype == "nfs":
			defaultOptions = "rw,nolock,tcp"
		else:
			defaultOptions = "rw,utf8"
		if self.mountinfo['sharename'] and self.mountinfo.has_key('sharename'):
			sharename = re_sub("\W", "", self.mountinfo['sharename'])
			self.old_sharename = sharename
		else:
			sharename = ""
			self.old_sharename = None
		if self.mountinfo.has_key('sharedir'):
			sharedir = self.mountinfo['sharedir']
			self.old_sharedir = sharedir
		else:
			sharedir = ""
			self.old_sharedir = None
		if self.mountinfo.has_key('options'):
			options = self.mountinfo['options']
		else:
			options = defaultOptions
		if self.mountinfo.has_key('username'):
			username = self.mountinfo['username']
		else:
			username = ""
		if self.mountinfo.has_key('password'):
			password = self.mountinfo['password']
		else:
			password = ""
		if self.mountinfo.has_key('hdd_replacement'):
			hdd_replacement = self.mountinfo['hdd_replacement']
			if hdd_replacement == 'True':
				hdd_replacement = True
			if hdd_replacement == 'False':
				hdd_replacement = False
		else:
			hdd_replacement = False
		if sharename is False:
			sharename = ""
		if sharedir is False:
			sharedir = ""
		if username is False:
			username = ""
		if password is False:
			password = ""

		self.mountusingConfigEntry = NoSave(ConfigSelection(self.mountusing, default = mountusing ))
		self.activeConfigEntry = NoSave(ConfigEnableDisable(default = active))
		self.ipConfigEntry = NoSave(ConfigIP(default = ip))
		self.sharenameConfigEntry = NoSave(ConfigText(default = sharename, visible_width = 50, fixed_size = False))
		self.sharedirConfigEntry = NoSave(ConfigText(default = sharedir, visible_width = 50, fixed_size = False))
		self.optionsConfigEntry = NoSave(ConfigText(default = defaultOptions, visible_width = 50, fixed_size = False))
		if options is not False:
			self.optionsConfigEntry.value = options
		self.usernameConfigEntry = NoSave(ConfigText(default = username, visible_width = 50, fixed_size = False))
		self.passwordConfigEntry = NoSave(ConfigPassword(default = password, visible_width = 50, fixed_size = False))
		self.mounttypeConfigEntry = NoSave(ConfigSelection(self.sharetypelist, default = mounttype ))
		self.hdd_replacementConfigEntry = NoSave(ConfigYesNo(default = hdd_replacement))

	def createSetup(self):
		self.list = []
		self.mountusingEntry = getConfigListEntry(_("Mount using"), self.mountusingConfigEntry)
		self.list.append(self.mountusingEntry)
		self.activeEntry = getConfigListEntry(_("Active"), self.activeConfigEntry)
		self.list.append(self.activeEntry)
		self.sharenameEntry = getConfigListEntry(_("Local share name"), self.sharenameConfigEntry)
		self.list.append(self.sharenameEntry)
		self.mounttypeEntry = getConfigListEntry(_("Mount type"), self.mounttypeConfigEntry)
		self.list.append(self.mounttypeEntry)
		self.ipEntry = getConfigListEntry(_("Server IP"), self.ipConfigEntry)
		self.list.append(self.ipEntry)
		self.sharedirEntry = getConfigListEntry(_("Server share"), self.sharedirConfigEntry)
		self.list.append(self.sharedirEntry)
		self.hdd_replacementEntry = getConfigListEntry(_("use as HDD replacement"), self.hdd_replacementConfigEntry)
		self.list.append(self.hdd_replacementEntry)
		self.optionsEntry = getConfigListEntry(_("Mount options"), self.optionsConfigEntry)
		self.list.append(self.optionsEntry)
		if self.mounttypeConfigEntry.value == "cifs":
			self.usernameEntry = getConfigListEntry(_("Username"), self.usernameConfigEntry)
			self.list.append(self.usernameEntry)
			self.passwordEntry = getConfigListEntry(_("Password"), self.passwordConfigEntry)
			self.list.append(self.passwordEntry)

		self["config"].list = self.list
		self["config"].l.setList(self.list)
		self["config"].onSelectionChanged.append(self.selectionChanged)

	def newConfig(self):
		if self["config"].getCurrent() == self.mounttypeEntry:
			if self.mounttypeConfigEntry.value == "nfs":
				defaultOptions = "rw,nolock,tcp"
			else:
				defaultOptions = "rw,utf8"
			if self.mountinfo.has_key('options'):
				options = self.mountinfo['options']
			else:
				options = defaultOptions
			self.optionsConfigEntry = NoSave(ConfigText(default = defaultOptions, visible_width = 50, fixed_size = False))
			if options is not False:
				self.optionsConfigEntry.value = options
			self.createSetup()

	def KeyText(self):
		print "Green Pressed"
		if self["config"].getCurrent() == self.sharenameEntry:
			self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'sharename'), VirtualKeyBoard, title = (_("Enter share name:")), text = self.sharenameConfigEntry.value)
		if self["config"].getCurrent() == self.sharedirEntry:
			self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'sharedir'), VirtualKeyBoard, title = (_("Enter share directory:")), text = self.sharedirConfigEntry.value)
		if self["config"].getCurrent() == self.optionsEntry:
			self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'options'), VirtualKeyBoard, title = (_("Enter options:")), text = self.optionsConfigEntry.value)
		if self["config"].getCurrent() == self.usernameEntry:
			self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'username'), VirtualKeyBoard, title = (_("Enter username:")), text = self.usernameConfigEntry.value)
		if self["config"].getCurrent() == self.passwordEntry:
			self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'password'), VirtualKeyBoard, title = (_("Enter password:")), text = self.passwordConfigEntry.value)

	def VirtualKeyBoardCallback(self, callback = None, entry = None):
		if callback is not None and len(callback) and entry is not None and len(entry):
			if entry == 'sharename':
				self.sharenameConfigEntry.setValue(callback)
				self["config"].invalidate(self.sharenameConfigEntry)
			if entry == 'sharedir':
				self.sharedirConfigEntry.setValue(callback)
				self["config"].invalidate(self.sharedirConfigEntry)
			if entry == 'options':
				self.optionsConfigEntry.setValue(callback)
				self["config"].invalidate(self.optionsConfigEntry)
			if entry == 'username':
				self.usernameConfigEntry.setValue(callback)
				self["config"].invalidate(self.usernameConfigEntry)
			if entry == 'password':
				self.passwordConfigEntry.setValue(callback)
				self["config"].invalidate(self.passwordConfigEntry)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()

	def selectionChanged(self):
		current = self["config"].getCurrent()
		if current == self.mountusingEntry or current == self.activeEntry or current == self.ipEntry or current == self.mounttypeEntry or current == self.hdd_replacementEntry:
			self["VKeyIcon"].hide()
			self["VirtualKB"].setEnabled(False)
		else:
			helpwindowpos = self["HelpWindow"].getPosition()
			if current[1].help_window.instance is not None:
				current[1].help_window.instance.move(ePoint(helpwindowpos[0],helpwindowpos[1]))
				self["VKeyIcon"].show()
				self["VirtualKB"].setEnabled(True)

	def ok(self):
		current = self["config"].getCurrent()
		if current == self.sharenameEntry or current == self.sharedirEntry or current == self.sharedirEntry or current == self.optionsEntry or current == self.usernameEntry or current == self.passwordEntry:
			if current[1].help_window.instance is not None:
				current[1].help_window.instance.hide()

		sharename = re_sub("\W", "", self.sharenameConfigEntry.value)
		if self.sharedirConfigEntry.value.startswith("/"):
			sharedir = self.sharedirConfigEntry.value[1:]
		else:
			sharedir = self.sharedirConfigEntry.value

		sharexists = False
		for data in self.mounts:
			if self.mounts[data]['sharename'] == self.old_sharename:
				sharexists = True
				break

		if not self.newmount and self.old_sharename and self.old_sharename != self.sharenameConfigEntry.value:
			self.session.openWithCallback(self.updateConfig, MessageBox, _("You have changed the share name!\nUpdate existing entry and continue?\n"), default=False )
		elif not self.newmount and self.old_sharename and self.old_sharename == self.sharenameConfigEntry.value and sharexists:
			self.session.openWithCallback(self.updateConfig, MessageBox, _("A mount entry with this name already exists!\nUpdate existing entry and continue?\n"), default=False )
		else:
			self.session.openWithCallback(self.applyConfig, MessageBox, _("Are you sure you want to save this network mount?\n\n") )

	def updateConfig(self, ret = False):
		if (ret == True):
			sharedir = None
			if self.old_sharename != self.sharenameConfigEntry.value:
				xml_sharename = self.old_sharename
			else:
				xml_sharename = self.sharenameConfigEntry.value

			if self.sharedirConfigEntry.value.startswith("/"):
				sharedir = self.sharedirConfigEntry.value[1:]
			else:
				sharedir = self.sharedirConfigEntry.value
			iAutoMount.setMountsAttribute(xml_sharename, "mountusing", self.mountusingConfigEntry.value)
			iAutoMount.setMountsAttribute(xml_sharename, "sharename", self.sharenameConfigEntry.value)
			iAutoMount.setMountsAttribute(xml_sharename, "active", self.activeConfigEntry.value)
			iAutoMount.setMountsAttribute(xml_sharename, "ip", self.ipConfigEntry.getText())
			iAutoMount.setMountsAttribute(xml_sharename, "sharedir", sharedir)
			iAutoMount.setMountsAttribute(xml_sharename, "mounttype", self.mounttypeConfigEntry.value)
			iAutoMount.setMountsAttribute(xml_sharename, "options", self.optionsConfigEntry.value)
			iAutoMount.setMountsAttribute(xml_sharename, "username", self.usernameConfigEntry.value)
			iAutoMount.setMountsAttribute(xml_sharename, "password", self.passwordConfigEntry.value)
			iAutoMount.setMountsAttribute(xml_sharename, "hdd_replacement", self.hdd_replacementConfigEntry.value)

			self.updateConfigRef = None
			self.updateConfigRef = self.session.openWithCallback(self.updateConfigfinishedCB, MessageBox, _("Please wait while updating your network mount..."), type = MessageBox.TYPE_INFO, enable_input = False)
			iAutoMount.writeMountsConfig()
			iAutoMount.getAutoMountPoints(self.updateConfigDataAvail, True)
		else:
			self.close()

	def updateConfigDataAvail(self, data):
		if data is True:
			self.updateConfigRef.close(True)

	def updateConfigfinishedCB(self,data):
		if data is True:
			self.session.openWithCallback(self.Updatefinished, MessageBox, _("Your network mount has been updated."), type = MessageBox.TYPE_INFO, timeout = 10)

	def Updatefinished(self,data):
		if data is not None:
			if data is True:
				self.close()

	def applyConfig(self, ret = False):
		if (ret == True):
			data = { 'isMounted': False, 'mountusing': False, 'active': False, 'ip': False, 'sharename': False, 'sharedir': False, \
					'username': False, 'password': False, 'mounttype' : False, 'options' : False, 'hdd_replacement' : False }
			data['mountusing'] = self.mountusingConfigEntry.value
			data['active'] = self.activeConfigEntry.value
			data['ip'] = self.ipConfigEntry.getText()
			data['sharename'] = re_sub("\W", "", self.sharenameConfigEntry.value)
			# "\W" matches everything that is "not numbers, letters, or underscores",where the alphabet defaults to ASCII.
			if self.sharedirConfigEntry.value.startswith("/"):
				data['sharedir'] = self.sharedirConfigEntry.value[1:]
			else:
				data['sharedir'] = self.sharedirConfigEntry.value
			data['options'] =  self.optionsConfigEntry.value
			data['mounttype'] = self.mounttypeConfigEntry.value
			data['username'] = self.usernameConfigEntry.value
			data['password'] = self.passwordConfigEntry.value
			data['hdd_replacement'] = self.hdd_replacementConfigEntry.value
			self.applyConfigRef = None
			self.applyConfigRef = self.session.openWithCallback(self.applyConfigfinishedCB, MessageBox, _("Please wait for activation of your network mount..."), type = MessageBox.TYPE_INFO, enable_input = False)
			iAutoMount.automounts[self.sharenameConfigEntry.value] = data
			iAutoMount.writeMountsConfig()
			iAutoMount.getAutoMountPoints(self.applyConfigDataAvail, True)
		else:
			self.close()

	def applyConfigDataAvail(self, data):
		if data is True:
			self.applyConfigRef.close(True)

	def applyConfigfinishedCB(self,data):
		if data is True:
			self.session.openWithCallback(self.applyfinished, MessageBox, _("Your network mount has been activated."), type = MessageBox.TYPE_INFO, timeout = 10)

	def applyfinished(self,data):
		if data is not None:
			if data is True:
				self.close()
