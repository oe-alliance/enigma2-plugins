from Screens.Screen import Screen
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Label import Label
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.MenuList import MenuList
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import *
from __init__ import _
mcpath = "/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/skins/defaultHD/images/"
#try:
#	from enigma import evfd
#except Exception, e:
#	print "Media Center: Import evfd failed"
class MC_Settings(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = NumberActionMap(["SetupActions","OkCancelActions"],
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
	def keyLeft(self):
		self["configlist"].handleKey(KEY_LEFT)
	def keyRight(self):
		self["configlist"].handleKey(KEY_RIGHT)
	def keyNumber(self, number):
		self["configlist"].handleKey(KEY_0 + number)
	def keyOK(self):
		config.plugins.mc_globalsettings.save()
#		if config.plugins.mc_global.vfd.value == "on":
#			evfd.getInstance().vfd_write_string(_("Settings"))
		self.close()
