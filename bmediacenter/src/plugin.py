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
from MC_WeatherInfo import MC_WeatherInfo
from MC_Settings import MC_Settings
from __init__ import _
mcpath = "/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/skins/defaultHD/images/"
#-------------------------------------------------------#
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
		list.append(("My Music", "MC_AudioPlayer", "menu_music", "50"))
		list.append(("My Music", "MC_AudioPlayer", "menu_music", "50"))
		list.append(("My Videos", "MC_VideoPlayer", "menu_video", "50"))
		list.append(("My Pictures", "MC_PictureViewer", "menu_pictures", "50"))
		list.append(("Web Radio", "MC_WebRadio", "menu_radio", "50"))
		list.append(("VLC Player", "MC_VLCPlayer", "menu_vlc", "50"))
		list.append(("Weather Info", "MC_WeatherInfo", "menu_weather", "50"))
		list.append(("Settings", "MC_Settings", "menu_settings", "50"))
		list.append(("Exit", "Exit", "menu_exit", "50"))
		self["menu"] = List(list)
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"],
		{
			"cancel": self.Exit,
			"ok": self.okbuttonClick,
			"right": self.next,
			"down": self.next,
			"up": self.prev,
			"left": self.prev
		}, -1)
	def next(self):
		self["menu"].selectNext()
		if self["menu"].getIndex() == 1:
			self["menu"].setIndex(2)
		if self["menu"].getIndex() == 8:
			self["menu"].setIndex(1)
		self.update()
	def prev(self):
		self["menu"].selectPrevious()
		if self["menu"].getIndex() == 0:
			self["menu"].setIndex(7)
		self.update()
	def update(self):
		if self["menu"].getIndex() == 1:
			self["text"].setText(_("My Music"))
			self["left"].instance.setPixmapFromFile(mcpath +"MenuIconSettingssw.png")
			self["middle"].instance.setPixmapFromFile(mcpath +"MenuIconMusic.png")
			self["right"].instance.setPixmapFromFile(mcpath +"MenuIconVideosw.png")
		elif self["menu"].getIndex() == 2:
			self["text"].setText(_("My Videos"))
			self["left"].instance.setPixmapFromFile(mcpath +"MenuIconMusicsw.png")
			self["middle"].instance.setPixmapFromFile(mcpath +"MenuIconVideo.png")
			self["right"].instance.setPixmapFromFile(mcpath +"MenuIconPicturesw.png")
		elif self["menu"].getIndex() == 3:
			self["text"].setText(_("My Pictures"))
			self["left"].instance.setPixmapFromFile(mcpath +"MenuIconVideosw.png")
			self["middle"].instance.setPixmapFromFile(mcpath +"MenuIconPicture.png")
			self["right"].instance.setPixmapFromFile(mcpath +"MenuIconRadiosw.png")
		elif self["menu"].getIndex() == 4:
			self["text"].setText(_("Webradio"))
			self["left"].instance.setPixmapFromFile(mcpath +"MenuIconPicturesw.png")
			self["middle"].instance.setPixmapFromFile(mcpath +"MenuIconRadio.png")
			self["right"].instance.setPixmapFromFile(mcpath +"MenuIconVLCsw.png")
		elif self["menu"].getIndex() == 5:
			self["text"].setText("VLC Player")
			self["left"].instance.setPixmapFromFile(mcpath +"MenuIconRadiosw.png")
			self["middle"].instance.setPixmapFromFile(mcpath +"MenuIconVLC.png")
			self["right"].instance.setPixmapFromFile(mcpath +"MenuIconWeathersw.png")
		elif self["menu"].getIndex() == 6:
			self["text"].setText(_("Weather Info"))
			self["left"].instance.setPixmapFromFile(mcpath +"MenuIconVLCsw.png")
			self["middle"].instance.setPixmapFromFile(mcpath +"MenuIconWeather.png")
			self["right"].instance.setPixmapFromFile(mcpath +"MenuIconSettingssw.png")
		elif self["menu"].getIndex() == 7:
			self["text"].setText(_("Settings"))
			self["left"].instance.setPixmapFromFile(mcpath +"MenuIconWeathersw.png")
			self["middle"].instance.setPixmapFromFile(mcpath +"MenuIconSettings.png")
			self["right"].instance.setPixmapFromFile(mcpath +"MenuIconMusicsw.png")
	def okbuttonClick(self):
		selection = self["menu"].getCurrent()
		if selection is not None:
			if selection[1] == "MC_VideoPlayer":
				self.session.open(MC_VideoPlayer)
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
				self.session.open(MC_WeatherInfo)
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
				trans = commands.getoutput('cat /etc/enigma2/settings | grep config.osd.alpha | cut -d "=" -f2')
				open("/proc/stb/video/alpha", "w").write(str(trans))
			except:
				print "Set OSD Transparacy failed"
		#configfile.save()
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
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your OpenAAF box", icon="plugin.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main),
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your OpenAAF box", where = PluginDescriptor.WHERE_MENU, fnc = menu),
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your OpenAAF box", icon="plugin.png", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)]	
	elif config.plugins.mc_globalsettings.showinmainmenu.value == True and config.plugins.mc_globalsettings.showinextmenu.value == False:
		return [
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your OpenAAF box", icon="plugin.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main),
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your OpenAAF box", where = PluginDescriptor.WHERE_MENU, fnc = menu)]
	elif config.plugins.mc_globalsettings.showinmainmenu.value == False and config.plugins.mc_globalsettings.showinextmenu.value == True:
		return [
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your OpenAAF box", icon="plugin.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main),
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your OpenAAF box", icon="plugin.png", where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)]
	else:
		return [
			PluginDescriptor(name = "Media Center", description = "Media Center Plugin for your OpenAAF box", icon="plugin.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main)]