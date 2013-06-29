# -*- coding: utf-8 -*-
# for localized messages
from __init__ import _
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap
from Components.config import ConfigText, ConfigPassword, NoSave, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
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
		<screen name="UserDialog" position="center,center" size="560,300" title="UserDialog">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget name="config" position="5,50" size="550,200" zPosition="1" scrollbarMode="showOnDemand" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,270" zPosition="1" size="560,2" />
			<widget source="introduction" render="Label" position="10,280" size="540,21" zPosition="10" font="Regular;21" halign="center" valign="center" backgroundColor="#25062748" transparent="1"/>
			<widget name="VKeyIcon" pixmap="skin_default/buttons/key_text.png" position="10,280" zPosition="10" size="35,25" transparent="1" alphatest="on" />
			<widget name="HelpWindow" pixmap="skin_default/vkey_icon.png" position="160,250" zPosition="1" size="1,1" transparent="1" alphatest="on" />	
		</screen>"""

	def __init__(self, session, plugin_path, hostinfo = None ):
		self.skin_path = plugin_path
		self.session = session
		Screen.__init__(self, self.session)
		self.hostinfo = hostinfo
		self.cache_ttl = 86400 #600 is default, 0 disables, Seconds cache is considered valid
		self.cache_file = '/etc/enigma2/' + self.hostinfo + '.cache' #Path to cache directory
		self.createConfig()

		self["actions"] = NumberActionMap(["SetupActions"],
		{
			"ok": self.ok,
			"back": self.close,
			"cancel": self.close,
			"red": self.close,
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
		self["introduction"] = StaticText(_("Press OK to save settings."))
		self["key_red"] = StaticText(_("Close"))

	def layoutFinished(self):
		self.setTitle(_("Enter user and password for host: ")+ self.hostinfo)

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

	def KeyText(self):
		if self["config"].getCurrent() == self.usernameEntry:
			self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'username'), VirtualKeyBoard, title = (_("Enter username:")), text = self.username.value)
		if self["config"].getCurrent() == self.passwordEntry:
			self.session.openWithCallback(lambda x : self.VirtualKeyBoardCallback(x, 'password'), VirtualKeyBoard, title = (_("Enter password:")), text = self.password.value)

	def VirtualKeyBoardCallback(self, callback = None, entry = None):
		if callback is not None and len(callback) and entry is not None and len(entry):
			if entry == 'username':
				self.username.setValue(callback)
				self["config"].invalidate(self.usernameEntry)
			if entry == 'password':
				self.password.setValue(callback)
				self["config"].invalidate(self.passwordEntry)

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

