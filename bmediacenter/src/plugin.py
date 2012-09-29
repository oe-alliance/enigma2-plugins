import os
import commands
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Components.ConfigList import ConfigList
from Components.config import *
from Components.Label import Label
from Screens.Screen import Screen
from Components.Pixmap import Pixmap
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from MC_AudioPlayer import MC_AudioPlayer, MC_WebRadio
from MC_VideoPlayer import MC_VideoPlayer
from MC_VLCPlayer import MC_VLCServerlist
from MC_PictureViewer import MC_PictureViewer
from MC_WeatherInfo import msnWetterDateMain, msnWetterMain
from MC_Settings import MC_Settings
from __init__ import _
from os import system
config.plugins.mc_global = ConfigSubsection()
config.plugins.mc_global.vfd = ConfigSelection(default="off", choices = [("off", "off"),("on", "on")])
try:
	from enigma import evfd
	config.plugins.mc_global.vfd.value = "on"
	config.plugins.mc_global.save()
except Exception, e:
	print "Media Center: Import evfd failed"
try:
	from Plugins.Extensions.DVDPlayer.plugin import *
	dvdplayer = True
except:
	print "Media Center: Import DVDPlayer failed"
	dvdplayer = False
	
mcpath = "/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/skins/defaultHD/images/"

class DMC_MainMenu(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self["text"] = Label(_("My Music"))
		self["left"] = Pixmap()
		self["middle"] = Pixmap()
		self["right"] = Pixmap()
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()
		# Disable OSD Transparency
		try:
			self.can_osd_alpha = open("/proc/stb/video/alpha", "r") and True or False
		except:
			self.can_osd_alpha = False
		if self.can_osd_alpha:
			open("/proc/stb/video/alpha", "w").write(str("255"))
		open("/proc/sys/vm/drop_caches", "w").write(str("3"))
		list = []
		list.append((_("My Music"), "MC_AudioPlayer", "menu_music", "50"))
		list.append((_("My Music"), "MC_AudioPlayer", "menu_music", "50"))
		list.append((_("My Videos"), "MC_VideoPlayer", "menu_video", "50"))
		list.append((_("DVD Player"), "MC_DVDPlayer", "menu_video", "50"))
		list.append((_("My Pictures"), "MC_PictureViewer", "menu_pictures", "50"))
		list.append((_("Web Radio"), "MC_WebRadio", "menu_radio", "50"))
		list.append((_("VLC Player"), "MC_VLCPlayer", "menu_vlc", "50"))
		list.append((_("Weather Info"), "MC_WeatherInfo", "menu_weather", "50"))
		list.append((_("Settings"), "MC_Settings", "menu_settings", "50"))
		list.append(("Exit", "Exit", "menu_exit", "50"))
		self["menu"] = List(list)
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

		if config.plugins.mc_global.vfd.value == "on":
			evfd.getInstance().vfd_write_string(_("My Music"))
		#command('djmount /media/upnp')
	def next(self):
		self["menu"].selectNext()
		if self["menu"].getIndex() == 1:
			self["menu"].setIndex(2)
		if self["menu"].getIndex() == 9:
			self["menu"].setIndex(1)
		self.update()
	def prev(self):
		self["menu"].selectPrevious()
		if self["menu"].getIndex() == 0:
			self["menu"].setIndex(8)
		self.update()
	def update(self):
		if self["menu"].getIndex() == 1:
			self["left"].instance.setPixmapFromFile(mcpath +"MenuIconSettingssw.png")
			self["middle"].instance.setPixmapFromFile(mcpath +"MenuIconMusic.png")
			self["right"].instance.setPixmapFromFile(mcpath +"MenuIconVideosw.png")
		elif self["menu"].getIndex() == 2:
			self["left"].instance.setPixmapFromFile(mcpath +"MenuIconMusicsw.png")
			self["middle"].instance.setPixmapFromFile(mcpath +"MenuIconVideo.png")
			self["right"].instance.setPixmapFromFile(mcpath +"MenuIconDVDsw.png")
		elif self["menu"].getIndex() == 3:
			self["left"].instance.setPixmapFromFile(mcpath +"MenuIconVideosw.png")
			self["middle"].instance.setPixmapFromFile(mcpath +"MenuIconDVD.png")
			self["right"].instance.setPixmapFromFile(mcpath +"MenuIconPicturesw.png")
		elif self["menu"].getIndex() == 4:
			self["left"].instance.setPixmapFromFile(mcpath +"MenuIconDVDsw.png")
			self["middle"].instance.setPixmapFromFile(mcpath +"MenuIconPicture.png")
			self["right"].instance.setPixmapFromFile(mcpath +"MenuIconRadiosw.png")
		elif self["menu"].getIndex() == 5:
			self["left"].instance.setPixmapFromFile(mcpath +"MenuIconPicturesw.png")
			self["middle"].instance.setPixmapFromFile(mcpath +"MenuIconRadio.png")
			self["right"].instance.setPixmapFromFile(mcpath +"MenuIconVLCsw.png")
		elif self["menu"].getIndex() == 6:
			self["left"].instance.setPixmapFromFile(mcpath +"MenuIconRadiosw.png")
			self["middle"].instance.setPixmapFromFile(mcpath +"MenuIconVLC.png")
			self["right"].instance.setPixmapFromFile(mcpath +"MenuIconWeathersw.png")
		elif self["menu"].getIndex() == 7:
			self["left"].instance.setPixmapFromFile(mcpath +"MenuIconVLCsw.png")
			self["middle"].instance.setPixmapFromFile(mcpath +"MenuIconWeather.png")
			self["right"].instance.setPixmapFromFile(mcpath +"MenuIconSettingssw.png")
		elif self["menu"].getIndex() == 8:
			self["left"].instance.setPixmapFromFile(mcpath +"MenuIconWeathersw.png")
			self["middle"].instance.setPixmapFromFile(mcpath +"MenuIconSettings.png")
			self["right"].instance.setPixmapFromFile(mcpath +"MenuIconMusicsw.png")
		if config.plugins.mc_global.vfd.value == "on":
			evfd.getInstance().vfd_write_string(self["menu"].getCurrent()[0])
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
					self.session.open(MessageBox,"Error: DVD-Player Plugin not installed ...",  MessageBox.TYPE_INFO)
			elif selection[1] == "MC_PictureViewer":
				self.session.open(MC_PictureViewer)
			elif selection[1] == "MC_AudioPlayer":
				self.session.open(MC_AudioPlayer)
			elif selection[1] == "MC_WebRadio":
				self.session.open(MC_WebRadio)
			elif selection[1] == "MC_VLCPlayer":
				if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/VlcPlayer/") == True:
					self.session.open(MC_VLCServerlist)
				else:
					self.session.open(MessageBox,"Error: VLC-Player Plugin not installed ...",  MessageBox.TYPE_INFO)
			elif selection[1] == "MC_WeatherInfo":
				colorfile = '/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/color'
				if fileExists(colorfile):
					f = open(colorfile, 'r')
					data = f.readline()
					f.close()
					if 'bluedate' in data:
						self.session.open(msnWetterDateMain)
					elif 'blackdate' in data:
						self.session.open(msnWetterDateMain)
					elif 'bluenodate' in data:
						self.session.open(msnWetterMain)
					elif 'blacknodate' in data:
						self.session.open(msnWetterMain)
			elif selection[1] == "MC_Settings":
				self.session.open(MC_Settings)
			else:
				self.session.open(MessageBox,("Error: Could not find plugin %s\ncoming soon ... :)") % (selection[1]),  MessageBox.TYPE_INFO)
	def error(self, error):
		self.session.open(MessageBox,("UNEXPECTED ERROR:\n%s") % (error),  MessageBox.TYPE_INFO)
	def Exit(self):
		# Restart old service
		self.session.nav.stopService()
		self.session.nav.playService(self.oldService)
		## Restore OSD Transparency Settings
		os.system("echo " + hex(0)[2:] + " > /proc/stb/vmpeg/0/dst_top")
		os.system("echo " + hex(0)[2:] + " > /proc/stb/vmpeg/0/dst_left")
		os.system("echo " + hex(720)[2:] + " > /proc/stb/vmpeg/0/dst_width")
		os.system("echo " + hex(576)[2:] + " > /proc/stb/vmpeg/0/dst_height")
		open("/proc/sys/vm/drop_caches", "w").write(str("3"))
		if self.can_osd_alpha:
			try:
				if config.plugins.mc_global.vfd.value == "on":
					trans = commands.getoutput('cat /etc/enigma2/settings | grep config.av.osd_alpha | cut -d "=" -f2')
				else:
					trans = commands.getoutput('cat /etc/enigma2/settings | grep config.osd.alpha | cut -d "=" -f2')
				open("/proc/stb/video/alpha", "w").write(str(trans))
			except:
				print "Set OSD Transparacy failed"
		if config.plugins.mc_global.vfd.value == "on":
			evfd.getInstance().vfd_write_string(_("Media Center"))
		#configfile.save()
		#command('umount /media/upnp')
		self.close()
#-------------------------------------------------------#
def main(session, **kwargs):
	session.open(DMC_MainMenu)
def menu(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(_("Media Center"), main, "dmc_mainmenu", 44)]
	return []
def Plugins(**kwargs):
	if config.plugins.mc_globalsettings.showinmainmenu.value == True and config.plugins.mc_globalsettings.showinextmenu.value == True:
		return [
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your STB_BOX", icon="plugin.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main),
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your STB_BOX", where = PluginDescriptor.WHERE_MENU, fnc = menu),
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your STB_BOX", icon="plugin.png", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)]	
	elif config.plugins.mc_globalsettings.showinmainmenu.value == True and config.plugins.mc_globalsettings.showinextmenu.value == False:
		return [
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your STB_BOX", icon="plugin.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main),
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your STB_BOX", where = PluginDescriptor.WHERE_MENU, fnc = menu)]
	elif config.plugins.mc_globalsettings.showinmainmenu.value == False and config.plugins.mc_globalsettings.showinextmenu.value == True:
		return [
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your STB_BOX", icon="plugin.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main),
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your STB_BOX", icon="plugin.png", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)]
	else:
		return [
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your STB_BOX", icon="plugin.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main)]