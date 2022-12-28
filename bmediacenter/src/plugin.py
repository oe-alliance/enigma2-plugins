from __future__ import absolute_import
from os import mkdir, system
from skin import loadSkin
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.Label import Label
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigYesNo
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Tools.Directories import pathExists, fileExists

from .MC_VideoPlayer import MC_VideoPlayer
from .MC_PictureViewer import MC_PictureViewer
from .MC_AudioPlayer import MC_AudioPlayer, MC_WebRadio
from .MC_VLCPlayer import MC_VLCServerlist
from .MC_Settings import MC_Settings
from .__init__ import _  # for localized messages

config.plugins.mc_global = ConfigSubsection()
config.plugins.mc_global.vfd = ConfigSelection(default='off', choices=[('off', 'off'), ('on', 'on')])
config.plugins.mc_globalsettings.upnp_enable = ConfigYesNo(default=False)
loadSkin("/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/skins/defaultHD/skin.xml")
try:
	from Plugins.Extensions.DVDPlayer.plugin import *
	dvdplayer = True
except ImportError:
	print("Media Center: Import DVDPlayer failed")
	dvdplayer = False

mcpath = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/skins/defaultHD/images/'
PNAME = "Media Center"


# Subclass of List to support horizontal menu
class DMC_List(List):
	def __init__(self, list=[]):
		List.__init__(self, list)

	def selectPrevious(self):
		if self.getIndex() - 1 < 0:
			self.index = self.count() - 1
		else:
			self.index -= 1
		self.setIndex(self.index)

	def selectNext(self):
		if self.getIndex() + 1 >= self.count():
			self.index = 0
		else:
			self.index += 1
		self.setIndex(self.index)


class DMC_MainMenu(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self["text"] = Label(_("My Music"))
		self["left"] = Pixmap()
		self["middle"] = Pixmap()
		self["right"] = Pixmap()
		self.oldbmcService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()
		# Disable OSD Transparency
		try:
			self.can_osd_alpha = open("/proc/stb/video/alpha", "r") and True or False
		except:
			self.can_osd_alpha = False
		if self.can_osd_alpha:
			open("/proc/stb/video/alpha", "w").write(str("255"))
		try:
			open("/proc/sys/vm/drop_caches", "w").write(str("3"))
		except:
			pass
		menulist = []
		menulist.append((_("My Music"), "MC_AudioPlayer", "menu_music", "50"))
		menulist.append((_("My Videos"), "MC_VideoPlayer", "menu_video", "50"))
#		menulist.append((_("DVD Player"), "MC_DVDPlayer", "menu_video", "50"))
		menulist.append((_("My Pictures"), "MC_PictureViewer", "menu_pictures", "50"))
		menulist.append((_("Web Radio"), "MC_WebRadio", "menu_radio", "50"))
#		menulist.append((_("VLC Player"), "MC_VLCPlayer", "menu_vlc", "50"))
		menulist.append((_("Settings"), "MC_Settings", "menu_settings", "50"))
		self["menu"] = DMC_List(menulist)
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"],
		{
			"cancel": self.Exit,
			"ok": self.okbuttonClick,
			"right": self.next,
			"upRepeated": self.prev,
			"down": self.next,
			"downRepeated": self.next,
			"leftRepeated": self.prev,
			"rightRepeated": self.next,
			"up": self.prev,
			"left": self.prev
		}, -1)
		if config.plugins.mc_globalsettings.upnp_enable.getValue():
			if fileExists("/media/upnp") is False:
				mkdir("/media/upnp")
			system('djmount /media/upnp &')

	def next(self):
		self["menu"].selectNext()
		self.update()

	def prev(self):
		self["menu"].selectPrevious()
		self.update()

	def update(self):
		menus = ["Settings", "Music", "Video", "Picture", "Radio", "Settings", "Music"]
#		menus = ["Settings", "Music", "Video", "DVD", "Picture", "Radio", "VLC", "Settings", "Music"]
		idx = self["menu"].getIndex()
		print(idx)
		self["middle"].instance.setPixmapFromFile(mcpath + "MenuIcon%s.png" % menus[idx + 1])
		self["left"].instance.setPixmapFromFile(mcpath + "MenuIcon%ssw.png" % menus[idx])
		self["right"].instance.setPixmapFromFile(mcpath + "MenuIcon%ssw.png" % menus[idx + 2])
		self["text"].setText(self["menu"].getCurrent()[0])

	def okbuttonClick(self):
		selection = self["menu"].getCurrent()
		if selection is not None:
			if selection[1] == "MC_VideoPlayer":
				self.session.open(MC_VideoPlayer)
			elif selection[1] == "MC_DVDPlayer":
				if dvdplayer:
					self.session.open(DVDPlayer)
				else:
					self.session.open(MessageBox, "Error: DVD-Player Plugin not installed ...", MessageBox.TYPE_INFO)
			elif selection[1] == "MC_PictureViewer":
				self.session.open(MC_PictureViewer)
			elif selection[1] == "MC_AudioPlayer":
				self.session.open(MC_AudioPlayer)
			elif selection[1] == "MC_WebRadio":
				self.session.open(MC_WebRadio)
			elif selection[1] == "MC_VLCPlayer":
				if pathExists("/usr/lib/enigma2/python/Plugins/Extensions/VlcPlayer/") == True:
					self.session.open(MC_VLCServerlist)
				else:
					self.session.open(MessageBox, "Error: VLC-Player Plugin not installed ...", MessageBox.TYPE_INFO)
			elif selection[1] == "MC_Settings":
				self.session.open(MC_Settings)
			else:
				self.session.open(MessageBox, ("Error: Could not find plugin %s\ncoming soon ... :)") % (selection[1]), MessageBox.TYPE_INFO)

	def error(self, error):
		self.session.open(MessageBox, ("UNEXPECTED ERROR:\n%s") % (error), MessageBox.TYPE_INFO)

	def Exit(self):
#		self.session.nav.stopService()
		# Restore OSD Transparency Settings
		try:
			open("/proc/sys/vm/drop_caches", "w").write(str("3"))
		except:
			pass
		if self.can_osd_alpha:
			try:
				if config.plugins.mc_global.vfd.value == "on":
					trans = config.av.osd_alpha.value
				else:
					trans = config.osd.alpha.value
				open("/proc/stb/video/alpha", "w").write(str(trans))
			except:
				print("Set OSD Transparacy failed")
		system('umount /media/upnp')
		self.session.nav.playService(self.oldbmcService)
		self.close()


def main(session, **kwargs):
	session.open(DMC_MainMenu)


def menu(menuid, **kwargs):
	return [(PNAME, main, "dmc_mainmenu", 44)] if menuid == "mainmenu" else []


def Plugins(**kwargs):
	PDESC = "Media Center Plugin for your STB_BOX"
	plist = [PluginDescriptor(name=PNAME, description=PDESC, icon="plugin.png", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main)]
	if config.plugins.mc_globalsettings.showinmainmenu.value:
		plist.append(PluginDescriptor(name=PNAME, description=PDESC, where=PluginDescriptor.WHERE_MENU, fnc=menu))
	if config.plugins.mc_globalsettings.showinextmenu.value:
		plist.append(PluginDescriptor(name=PNAME, description=PDESC, icon="plugin.png", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main))
	return plist
