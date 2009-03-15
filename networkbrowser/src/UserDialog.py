# -*- coding: utf-8 -*-
# for localized messages
from __init__ import _
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap
from Components.config import ConfigText, ConfigPassword, NoSave, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap, NumberActionMap
from enigma import ePoint
from cPickle import dump, load
from os import path as os_path, unlink, stat, mkdir
from time import time
from stat import ST_MTIME

def write_cache(cache_file, cache_data):
	#Does a cPickle dump
	if not os_path.isdir( os_path.dirname(cache_file) ):
		try:
			mkdir( os_path.dirname(cache_file) )
		except OSError:
			print os_path.dirname(cache_file), 'is a file'
	fd = open(cache_file, 'w')
	dump(cache_data, fd, -1)
	fd.close()

def valid_cache(cache_file, cache_ttl):
	#See if the cache file exists and is still living
	try:
		mtime = stat(cache_file)[ST_MTIME]
	except:
		return 0
	curr_time = time()
	if (curr_time - mtime) > cache_ttl:
		return 0
	else:
		return 1

def load_cache(cache_file):
	#Does a cPickle load
	fd = open(cache_file)
	cache_data = load(fd)
	fd.close()
	return cache_data

class UserDialog(Screen, ConfigListScreen):
	skin = """
		<screen name="UserDialog" position="90,110" size="560,380" title="UserDialog">
			<widget name="config" position="10,10" size="540,200" zPosition="1" scrollbarMode="showOnDemand" />
			<widget name="ButtonGreen" pixmap="skin_default/buttons/button_green.png" position="20,330" zPosition="10" size="15,16" transparent="1" alphatest="on" />
			<widget name="introduction2" position="90,300" size="300,20" zPosition="10" font="Regular;21" halign="center" transparent="1" />
			<widget name="ButtonRedtext" position="410,345" size="140,21" zPosition="10" font="Regular;21" transparent="1" />
			<widget name="ButtonRed" pixmap="skin_default/buttons/button_red.png" position="390,345" zPosition="10" size="15,16" transparent="1" alphatest="on" />
			<widget name="VKeyIcon" pixmap="skin_default/vkey_icon.png" position="35,310" zPosition="10" size="60,48" transparent="1" alphatest="on" />
			<widget name="HelpWindow" pixmap="skin_default/vkey_icon.png" position="175,300" zPosition="1" size="1,1" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/bottombar.png" position="10,290" size="540,120" zPosition="1" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session, plugin_path, hostinfo = None ):
		self.skin_path = plugin_path
		self.session = session
		Screen.__init__(self, self.session)
		self.hostinfo = hostinfo
		self.cache_ttl = 86400 #600 is default, 0 disables, Seconds cache is considered valid
		self.cache_file = '/etc/enigma2/' + self.hostinfo + '.cache' #Path to cache directory
		self.createConfig()

		self["shortcuts"] = ActionMap(["ShortcutActions","WizardActions"],
		{
			"red": self.close,
			"back": self.close,
			"ok": self.ok,
		}, -2)

		self["VirtualKB"] = ActionMap(["ShortcutActions","WizardActions"],
		{
			"green": self.KeyGreen,
		}, -2)

		self.list = []
		ConfigListScreen.__init__(self, self.list,session = self.session)
		self.createSetup()
		self.onLayoutFinish.append(self.layoutFinished)
		# Initialize Buttons
		self["ButtonGreen"] = Pixmap()
		self["VKeyIcon"] = Pixmap()
		self["HelpWindow"] = Pixmap()
		self["introduction2"] = Label(_("Press OK to save settings."))
		self["ButtonRed"] = Pixmap()
		self["ButtonRedtext"] = Label(_("Close"))

	def layoutFinished(self):
		print self["config"].getCurrent()
		self.setTitle(_("Enter user and password for host: ")+ self.hostinfo)
		self["ButtonGreen"].show()
		self["VKeyIcon"].show()
		self["VirtualKB"].setEnabled(True)
		self["HelpWindow"].show()

	# helper function to convert ips from a sring to a list of ints
	def convertIP(self, ip):
		strIP = ip.split('.')
		ip = []
		for x in strIP:
			ip.append(int(x))
		return ip

	def createConfig(self):
		self.usernameEntry = None
		self.passwordEntry = None
		self.username = None
		self.password = None

		if os_path.exists(self.cache_file):
			print 'Loading user cache from ',self.cache_file
			try:
				self.hostdata = load_cache(self.cache_file)
				username = self.hostdata['username']
				password = self.hostdata['password']
			except:
				username = "username"
				password = "password"
		else:
			username = "username"
			password = "password"

		self.username = NoSave(ConfigText(default = username, visible_width = 50, fixed_size = False))
		self.password = NoSave(ConfigPassword(default = password, visible_width = 50, fixed_size = False))

	def createSetup(self):
		self.list = []
		self.usernameEntry = getConfigListEntry(_("Username"), self.username)
		self.list.append(self.usernameEntry)
		self.passwordEntry = getConfigListEntry(_("Password"), self.password)
		self.list.append(self.passwordEntry)

		self["config"].list = self.list
		self["config"].l.setList(self.list)
		self["config"].onSelectionChanged.append(self.selectionChanged)

	def KeyGreen(self):
		if self["config"].getCurrent() == self.usernameEntry:
			self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'username'), VirtualKeyBoard, title = (_("Enter username:")), text = self.username.value)
		if self["config"].getCurrent() == self.passwordEntry:
			self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'password'), VirtualKeyBoard, title = (_("Enter password:")), text = self.password.value)

	def VirtualKeyBoardCallback(self, callback = None, entry = None):
		if callback is not None and len(callback) and entry is not None and len(entry):
			if entry == 'username':
				self.username = NoSave(ConfigText(default = callback, visible_width = 50, fixed_size = False))
				self.createSetup()
			if entry == 'password':
				self.password = NoSave(ConfigPassword(default = callback, visible_width = 50, fixed_size = False))
				self.createSetup()

	def newConfig(self):
		if self["config"].getCurrent() == self.InterfaceEntry:
			self.createSetup()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)

	def keyRight(self):
		ConfigListScreen.keyRight(self)

	def selectionChanged(self):
		current = self["config"].getCurrent()
		helpwindowpos = self["HelpWindow"].getPosition()
		if current[1].help_window.instance is not None:
			current[1].help_window.instance.move(ePoint(helpwindowpos[0],helpwindowpos[1]))

	def ok(self):
		current = self["config"].getCurrent()
		self.hostdata = { 'username': self.username.value, 'password': self.password.value }
		write_cache(self.cache_file, self.hostdata)
		self.close(True)

