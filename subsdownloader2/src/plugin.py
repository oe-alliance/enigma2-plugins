from __future__ import print_function
import os
try:
	is_libmediainfo = True
	from Plugins.Extensions.SubsDownloader2.SourceCode.GetFPS_MI import GetFPS
except:
	is_libmediainfo = False
	from Plugins.Extensions.SubsDownloader2.SourceCode.GetFPS import GetFPS
import chardet

from Plugins.Extensions.SubsDownloader2.SourceCode.anysub2srt import SubConv
# jak zmienie sciezke SubsDownloader2 (nazwe katalogu to trzeba ja tez zmienic w pliku OpenSubtitles.py
#from Plugins.Extensions.SubsDownloader2.SourceCode.periscope.services.OpenSubtitle.services import OpenSubtitle
from Plugins.Extensions.SubsDownloader2.SourceCode.xbmc_subtitles.XBMC_search import list_XBMC_Periscope_plugins  # , XBMCSubtitle

from Plugins.Extensions.SubsDownloader2.SourceCode.periscope import SubtitleDatabase
from Plugins.Extensions.SubsDownloader2.SourceCode.NapiProjekt import NapiProjekt  # *
from Plugins.Extensions.SubsDownloader2.SourceCode.Napisy24_pl import Napisy24_pl, GuessFileData_from_FileName, CompareMovie_and_Subtite_FileData
from Plugins.Extensions.SubsDownloader2.SourceCode.chardet_OutpuyTranslation import chardetOutputTranslation
from Plugins.Extensions.SubsDownloader2.SourceCode.myFileList import EXTENSIONS, FileList  # *
from Plugins.Extensions.SubsDownloader2.pluginOnlineContent import Subtitle_Downloader_temp_dir, CommertialBannerDownload  # flagcounetr,
from Screens.VirtualKeyBoard import VirtualKeyBoard
from os import system as os_system
from os import stat as os_stat
from os import walk as os_walk
from Screens.Screen import Screen
from Components.config import config, ConfigSubList, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText, getConfigListEntry, ConfigDirectory, ConfigSelection, ConfigPassword
from Components.ConfigList import ConfigListScreen
from Components.MenuList import MenuList
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.SystemInfo import BoxInfo
from Screens.MessageBox import MessageBox
from Screens.InfoBar import MoviePlayer as MP_parent
from Components.ActionMap import ActionMap
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import fileExists
from time import strftime as time_strftime
from time import localtime as time_localtime
from re import compile as re_compile
from os import path as os_path, listdir
from enigma import eServiceReference, ePicLoad, getDesktop, eTimer

#import players like Picture player, dvd player, music palyer
if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/PicturePlayer/plugin.pyo") or os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/PicturePlayer/plugin.pyc"):
	from Plugins.Extensions.PicturePlayer.plugin import Pic_Thumb, picshow
	PicPlayerAviable = True
else:
	PicPlayerAviable = False
if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/plugin.pyo") or os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/plugin.pyc"):
	from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
	DVDPlayerAviable = True
else:
	DVDPlayerAviable = False
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/plugin.pyo") or fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/plugin.pyc"):
	from Plugins.Extensions.MerlinMusicPlayer.plugin import MerlinMusicPlayerScreen, Item
	MMPavaiable = True
else:
	MMPavaiable = False
# END of import players like Picture player, dvd player, music palyer


###########################################################################

#define config:
config.plugins.subsdownloader = ConfigSubsection()
config.plugins.subsdownloader.path = ConfigText(default="/", fixed_size=False)
config.plugins.subsdownloader.pathSave = ConfigYesNo(default=True)
config.plugins.subsdownloader.BlueButtonMenu = ConfigYesNo(default=True)
config.plugins.subsdownloader.pathUseMediaPaternFilter = ConfigYesNo(default=False)
config.plugins.subsdownloader.extendedMenuConfig = ConfigYesNo(default=False)
config.plugins.subsdownloader.ItasaUser = ConfigText(default="login", fixed_size=False)
config.plugins.subsdownloader.ItasaPassword = ConfigPassword(default="password", fixed_size=False)
#config.plugins.subsdownloader.del_sub_after_conv = ConfigYesNo(default = False)

#Create Subtitle Server plugin list
PERISCOPE_PLUGINS = list_XBMC_Periscope_plugins('/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/SourceCode/periscope/services/')
SUBTITLE_SERVER_LIST = [(("NapiProjekt"), "NapiProjekt"), (("Napisy24"), "Napisy24")]
for server in PERISCOPE_PLUGINS:
	SUBTITLE_SERVER_LIST.append((server, server))
XBMC_PLUGINS = list_XBMC_Periscope_plugins('/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/SourceCode/xbmc_subtitles/services/')
for server in XBMC_PLUGINS:
	SUBTITLE_SERVER_LIST.append((server, server))
config.plugins.subsdownloader.subtitleserver = ConfigSelection(default="OpenSubtitle", choices=SUBTITLE_SERVER_LIST)
if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/DMnapi/DMnapi.py'):
	try:
		from Plugins.Extensions.DMnapi.DMnapi import DMnapi, dmnapi_version
		SUBTITLE_SERVER_LIST.append(('DMnapi', 'DMnapi'))
		global supported_DMnapi_versions
		supported_DMnapi_versions = {"12.8.8"}
	except:
		pass


from Plugins.Extensions.SubsDownloader2.SourceCode.xbmc_subtitles.utilities import LANGUAGES  # , languageTranslate #toScriptLang
SubsDownloaderLangs = []
SubsDownloaderLangs.append(getConfigListEntry("None", "None"))
for x in LANGUAGES:
	#SubsDownloaderLangs.append(getConfigListEntry(toScriptLang(str(x)),toScriptLang(str(x))))
	SubsDownloaderLangs.append(getConfigListEntry(x[0], x[0]))
SubsDownloaderLangs.append(getConfigListEntry("All", "All"))
config.plugins.subsdownloader.SubsDownloader1stLang = ConfigSelection(default="English", choices=SubsDownloaderLangs)
config.plugins.subsdownloader.SubsDownloader2ndLang = ConfigSelection(default="Polish", choices=SubsDownloaderLangs)
config.plugins.subsdownloader.SubsDownloader3rdLang = ConfigSelection(default="German", choices=SubsDownloaderLangs)
config.plugins.subsdownloader.Napisy24SearchMethod = ConfigSelection(default="IMDB", choices=[(_("IMDB"), "IMDB"), (_("IMDB then movie filname"), "IMDB then movie filname"), (_("movie filname"), "movie filname")])
config.plugins.subsdownloader.Napisy24MovieNameMethod = ConfigYesNo(default=True)


class SubsDownloaderApplication(Screen):
	def __init__(self, session, args=0):

		global Skin_width
		global Skin_height
		global Screen_width
		global Screen_height
		global is_libmediainfo
		#global Subtitle_Downloader_temp_dir
		#Subtitle_Downloader_temp_dir = '/tmp/SubsDownloader_cache/'

		Screen_width = getDesktop(0).size().width()  # 1280
		Screen_height = getDesktop(0).size().height()  # 720
		Skin_width = int(0.9 * Screen_width)  # 1152
		Skin_height = int(0.9 * Screen_height)  # 648
		widget_name_height = int(0.3 * Skin_height)
		widget_name_width = int(0.74827 * Skin_width)
		widget_name_x_position = int(0.0087 * Skin_width)
		widget_name_y_position = int(0.0156 * Skin_height)
		widget_source_x_position = int(0.766 * Skin_width)
		widget_source_y_position = int(0.1081 * Skin_height)
		widget_source_x_size = int(0.191 * Skin_width)
		widget_source_y_size = int(26)
		font_size = int(int(0.0174 * Skin_width))

		self.skin = "<screen position=\"center," + str(int(0.078 * Skin_height)) + "\" size=\"" + str(Skin_width) + "," + str(Skin_height) + "\" title= \"Subtitle downloader\" > \
			<widget name=\"fileList\" position=\"" + str(widget_name_x_position) + "," + str(1 * widget_name_y_position) + "\" size=\"" + str(widget_name_width) + "," + str(widget_name_height) + "\" scrollbarMode=\"showOnDemand\" /> \
			<widget name=\"subsList\" position=\"" + str(widget_name_x_position) + "," + str(2 * widget_name_y_position + 1 * widget_name_height) + "\" size=\"" + str(widget_name_width) + "," + str(widget_name_height) + "\" scrollbarMode=\"showOnDemand\" /> \
			<widget name=\"commertialPicture\" position=\"" + str(widget_name_x_position) + "," + str(3 * widget_name_y_position + 2 * widget_name_height) + "\" size=\"" + str(int(0.98 * Skin_width)) + "," + str(widget_name_height) + "\" zPosition=\"1\" alphatest=\"on\" /> \
			<widget name=\"serverPicture\" position=\"" + str(widget_source_x_position) + "," + str(widget_name_x_position) + "\" size=\"" + str(int(0.252 * Skin_width)) + "," + str(int(0.0849 * Skin_height)) + "\" zPosition=\"1\" alphatest=\"on\" /> \
			<ePixmap pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/pic/buttons/HD/key_menu.png\" position=\"" + str(widget_source_x_position) + "," + str(widget_source_y_position) + "\" size=\"36,26\" zPosition=\"1\" alphatest=\"on\" /> \
			<widget source=\"key_menu\" render=\"Label\" position=\"" + str(widget_source_x_position + 43) + "," + str(widget_source_y_position) + "\" zPosition=\"1\" size=\"" + str(widget_source_x_size) + "," + str(widget_source_y_size) + "\" font=\"Regular;" + str(font_size) + "\" halign=\"left\" valign=\"center\" transparent=\"1\" /> \
			<ePixmap pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/pic/buttons/HD/key_help.png\" position=\"" + str(widget_source_x_position) + "," + str(widget_source_y_position + widget_source_y_size) + "\" size=\"36," + str(widget_source_y_size) + "\" zPosition=\"1\" alphatest=\"on\" /> \
			<widget source=\"key_help\" render=\"Label\" position=\"" + str(widget_source_x_position + 43) + "," + str(widget_source_y_position + widget_source_y_size) + "\" zPosition=\"1\" size=\"" + str(widget_source_x_size) + "," + str(widget_source_y_size) + "\" font=\"Regular;" + str(font_size) + "\" halign=\"left\" valign=\"center\" transparent=\"1\" /> \
			<ePixmap pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/pic/buttons/HD/key_text.png\" position=\"" + str(widget_source_x_position) + "," + str(widget_source_y_position + widget_source_y_size * 2) + "\" size=\"36," + str(widget_source_y_size) + "\" zPosition=\"1\" alphatest=\"on\" /> \
			<widget source=\"key_text\" render=\"Label\" position=\"" + str(widget_source_x_position + 43) + "," + str(widget_source_y_position + widget_source_y_size * 2) + "\" zPosition=\"1\" size=\"" + str(widget_source_x_size) + "," + str(widget_source_y_size) + "\" font=\"Regular;" + str(font_size) + "\" halign=\"left\" valign=\"center\" transparent=\"1\" /> \
			<ePixmap pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/pic/buttons/HD/key_next.png\" position=\"" + str(widget_source_x_position) + "," + str(widget_source_y_position + widget_source_y_size * 3) + "\" size=\"36," + str(widget_source_y_size) + "\" zPosition=\"1\" alphatest=\"on\" /> \
			<widget source=\"key_next\" render=\"Label\" position=\"" + str(widget_source_x_position + 43) + "," + str(widget_source_y_position + widget_source_y_size * 3) + "\" zPosition=\"1\" size=\"" + str(widget_source_x_size) + "," + str(widget_source_y_size) + "\" font=\"Regular;" + str(font_size) + "\" halign=\"left\" valign=\"center\" transparent=\"1\" /> \
			<ePixmap pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/pic/buttons/HD/key_last.png\" position=\"" + str(widget_source_x_position) + "," + str(widget_source_y_position + widget_source_y_size * 4) + "\" size=\"36," + str(widget_source_y_size) + "\" zPosition=\"1\" alphatest=\"on\" /> \
			<widget source=\"key_last\" render=\"Label\" position=\"" + str(widget_source_x_position + 43) + "," + str(widget_source_y_position + widget_source_y_size * 4) + "\" zPosition=\"1\" size=\"" + str(widget_source_x_size) + "," + str(widget_source_y_size) + "\" font=\"Regular;" + str(font_size) + "\" halign=\"left\" valign=\"center\" transparent=\"1\" /> \
			<ePixmap pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/pic/buttons/HD/key_info.png\" position=\"" + str(widget_source_x_position) + "," + str(widget_source_y_position + widget_source_y_size * 5) + "\" size=\"36," + str(widget_source_y_size) + "\" zPosition=\"1\" alphatest=\"on\" /> \
			<widget source=\"key_info\" render=\"Label\" position=\"" + str(widget_source_x_position + 43) + "," + str(widget_source_y_position + widget_source_y_size * 5) + "\" zPosition=\"1\" size=\"" + str(widget_source_x_size) + "," + str(widget_source_y_size) + "\" font=\"Regular;" + str(font_size) + "\" halign=\"left\" valign=\"center\" transparent=\"1\" /> \
			<ePixmap pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/pic/buttons/HD/key_0.png\" position=\"" + str(widget_source_x_position) + "," + str(widget_source_y_position + widget_source_y_size * 6) + "\" size=\"36," + str(widget_source_y_size) + "\" zPosition=\"1\" alphatest=\"on\" /> \
			<widget source=\"key_0\" render=\"Label\" position=\"" + str(widget_source_x_position + 43) + "," + str(widget_source_y_position + widget_source_y_size * 6) + "\" zPosition=\"1\" size=\"" + str(widget_source_x_size) + "," + str(widget_source_y_size) + "\" font=\"Regular;" + str(font_size) + "\" halign=\"left\" valign=\"center\" transparent=\"1\" /> \
			<ePixmap pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/pic/buttons/HD/key_blue.png\" position=\"" + str(widget_source_x_position) + "," + str(widget_source_y_position + widget_source_y_size * 7) + "\" size=\"36," + str(widget_source_y_size) + "\" zPosition=\"1\" alphatest=\"on\" /> \
			<widget source=\"key_blue\" render=\"Label\" position=\"" + str(widget_source_x_position + 43) + "," + str(widget_source_y_position + widget_source_y_size * 7) + "\" zPosition=\"1\" size=\"" + str(widget_source_x_size) + "," + str(widget_source_y_size) + "\" font=\"Regular;" + str(font_size) + "\" halign=\"left\" valign=\"center\" transparent=\"1\" /> \
		</screen>"

		os.system('mkdir /tmp/SubsDownloader_cache')
		self.subsListDownloaded = 0
		self.localConvertion = False
		self.MyBox = BoxInfo.getItem("model")
		self.textEXTENSIONS = {
			"srt": "text",
			"txt": "text",
			"sub": "text",
			"nfo": "text",
			"cuts": "movie_timer",
			"zip": "package",
			"rar": "package"
		}
		#TODO OBSLUGA PLIKOW BZIP, ZIP, RAR
		#TODO File manager (delete, copy, move, rename
		self["key_menu"] = StaticText("Config menu")
		self["key_help"] = StaticText("About...")
		self["key_text"] = StaticText("Subtitle download")
		self["key_next"] = StaticText("SubsList enable")
		self["key_last"] = StaticText("FileList enable")
		self["key_info"] = StaticText("File size")
		self["key_0"] = StaticText("Show/Hide")
		self["key_blue"] = StaticText("Enable FileManager")
		self.mediaPatern = self.make_media_patern()

		try:
			fileListPath = config.plugins.subsdownloader.path.value
		except:
			fileListPath = "/"

		self.session = session
		Screen.__init__(self, session)
		self.altservice = self.session.nav.getCurrentlyPlayingServiceReference()
		list = []
		if config.plugins.subsdownloader.pathUseMediaPaternFilter.value is True:
			self["fileList"] = FileList(fileListPath, matchingPattern=None)
		else:
			self["fileList"] = FileList(fileListPath, matchingPattern=self.mediaPatern)
		self.selectedList = self["fileList"]
		self["subsList"] = MenuList(list)
		self.fileManagerEnabled = False
		self.showFilemanagerScreen_command = None
		self.clearSubList()
		self.set_listFile_enabled()

		self.isVisible = True
		#self.fileManager_orders = []

		self["myActionMap_showned"] = ActionMap(["ChannelSelectBaseActions", "WizardActions", "DirectionActions", "MenuActions", "NumberActions", "ColorActions", "SubsDownloaderApplication_actions"], {
			"ok": self.ok,
			"back": self.closeApplication,
			"about": self.showAboutScreen,
			"subSelect": self.downloadSubtitle,
			"menu": self.showConfigScreen,
			"nextMarker": self.set_listSubs_enabled,
			"prevMarker": self.set_listFile_enabled,
			"up": self.goUp,
			"down": self.goDown,
			"left": self.goLeft,
			"right": self.goRight,
			"info": self.showFilemanagerScreen_file_info_on_screen_title,  # self.FM_file_Info,
			"localConv": self.localConvertionSublist,
			"0": self.skinVisibility,
			#"red": self.goRed,
			#"green": self.goGreen,
			#"yellow": self.goYellow,
			"blue": self.showFilemanagerScreen_without_callback,
		}, -1)

		self["myActionMap_hidded"] = ActionMap(["ChannelSelectBaseActions", "WizardActions", "DirectionActions", "MenuActions", "NumberActions", "ColorActions", "SubsDownloaderApplication_actions"], {
			"0": self.skinVisibility,
		}, -1)
		self["myActionMap_showned"].setEnabled(True)
		self["myActionMap_hidded"].setEnabled(False)

		#PICTURE INITIALIZATION
		#1st picture
		self.ServerPicture = ePicLoad()
		self["serverPicture"] = Pixmap()
		self.ServerPicture.PictureData.get().append(self.DecodeServerPictureAction)
		self.serverPicturePath = "/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/pic/none1.jpg"
		self.onLayoutFinish.append(self.Show_Server_Picture)

		self.display_Server_Picture()

		#2nd picture
		self.CommertialPicture = ePicLoad()
		self["commertialPicture"] = Pixmap()
		self.CommertialPicture.PictureData.get().append(self.DecodeCommertialPictureAction)
		self.CommertialPicturePath = "/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/pic/none1.jpg"
		self.onLayoutFinish.append(self.Show_Commertial_Picture)

		self.download_commertial_pictures = CommertialBannerDownload()
		self.download_commertial_pictures.start()
		self.__commertial_pictures_display_counter = 0
		self.__commertial_pictures = []
		self.CommertialBannerTimer = eTimer()
		self.CommertialBannerTimer.callback.append(self.CommertialBannerDisplayTimerAction)
		self.CommertialBannerTimer.start(120, False)
		"""Oczywiscie trzeba stworzyc widget i pokopiowac odpowiednie funkcje inicjalizujace"""
		#PICTURE INITIALIZATION
		self.set_title()

	def CommertialBannerDisplayTimerAction(self):
		if self.download_commertial_pictures.is_alive() is False and self.__commertial_pictures == []:
			self.__commertial_pictures = self.Find_Commertial_Picure()
			self.__commertial_pictures.sort()
			self.CommertialBannerTimer.start(10, False)
		else:
			self.CommertialBannerTimer.start(120, False)
		if self.__commertial_pictures != []:
			if self.__commertial_pictures_display_counter > len(self.__commertial_pictures) - 1:
				self.__commertial_pictures_display_counter = 0
			self.display_Commmertial_Picture(self.__commertial_pictures[self.__commertial_pictures_display_counter])
			self.__commertial_pictures_display_counter = self.__commertial_pictures_display_counter + 1
			if len(self.__commertial_pictures) == 1:
				self.CommertialBannerTimer.stop()
			else:
				self.CommertialBannerTimer.start(7500, False)

	def skinVisibility(self):
		if self.isVisible is True:
			self.isVisible = False
			self["myActionMap_showned"].setEnabled(False)
			self["myActionMap_hidded"].setEnabled(True)
			self.hide()
		else:
			self.isVisible = True
			self["myActionMap_showned"].setEnabled(True)
			self["myActionMap_hidded"].setEnabled(False)
			self.show()

	def set_title(self):
		if is_libmediainfo is False:
			self.setTitle("Subtitle downloader (without libmediainfo)")
		elif is_libmediainfo is True:
			self.setTitle("Subtitle downloader (with libmediainfo)")

	def showFilemanagerScreen_file_info_on_screen_title(self):
		self.showFilemanagerScreen(("file_info_on_screen_title"))

	def showFilemanagerScreen_without_callback(self):
		if isinstance(self.showFilemanagerScreen_command, type(None)):
			self.showFilemanagerScreen(("None"))
		else:
			order = None
			if self.showFilemanagerScreen_command[0] == "Do_nothing":
				order = None
			elif self.showFilemanagerScreen_command[0] == "delete":
				#order = 'rm -f \"' + self.showFilemanagerScreen_command[1] + '\" &'
				if os.path.isfile(self.showFilemanagerScreen_command[1]):
					order = 'rm -f \"' + self.showFilemanagerScreen_command[1] + '\"'
				elif os.path.isdir(self.showFilemanagerScreen_command[1]):
					order = 'rm -r \"' + self.showFilemanagerScreen_command[1] + '\"'
			elif self.showFilemanagerScreen_command[0] == "copy":
				dest = self["subsList"].getCurrent()[1]
				if self.showFilemanagerScreen_command[1][len(self.showFilemanagerScreen_command[1]) - 1] == '/':
					order = 'cp -af \"' + self.showFilemanagerScreen_command[1] + '\" \"' + dest + '\"'
				else:
					order = 'cp \"' + self.showFilemanagerScreen_command[1] + '\" \"' + dest + '\"'
			elif self.showFilemanagerScreen_command[0] == "move":
				dest = self["subsList"].getCurrent()[1]
				if self.showFilemanagerScreen_command[1][len(self.showFilemanagerScreen_command[1]) - 1] == '/':
					order = 'mv \"' + self.showFilemanagerScreen_command[1] + '\" \"' + dest + '\"'
				else:
					order = 'mv \"' + self.showFilemanagerScreen_command[1] + '\" \"' + dest + '\"'
			elif self.showFilemanagerScreen_command[0] == "rename":
				dest = self.showFilemanagerScreen_command[2]
				if self.showFilemanagerScreen_command[1][len(self.showFilemanagerScreen_command[1]) - 1] == '/':
					order = 'mv \"' + self.showFilemanagerScreen_command[1] + '\" \"' + dest + '\"'
				else:
					order = 'mv \"' + self.showFilemanagerScreen_command[1] + '\" \"' + dest + '\"'

				#order = "ls"
				#self.session.open(MessageBox,_("%s \n %s \n %s!" % (self.showFilemanagerScreen_command[0],self.showFilemanagerScreen_command[1],self.showFilemanagerScreen_command[2])), MessageBox.TYPE_ERROR)

			if order is not None:
				try:
					os.system(order)
				except:
					self.session.open(MessageBox, _("%s \nFAILED!" % order), MessageBox.TYPE_ERROR)
			self.set_FileManager_disabled()
			self["fileList"].refresh()

	def showFilemanagerScreen(self, callback):
		self.showFilemanagerScreen_command = callback

		def FM_file_Info(self):
			if self["fileList"].canDescent():
				if self["fileList"].getSelectionIndex() != 0:
					curSelDir = self["fileList"].getSelection()[0]
					dir_stats = os_stat(curSelDir)
					dir_infos = "DIR:    size " + str(FM_Humanizer(dir_stats.st_size)) + "    "
					self.setTitle(_(dir_infos))
				else:
					dei = self.session.open(MessageBox, _("Dreambox: " + self.MyBox + "\n\n"), MessageBox.TYPE_INFO)
					dei.setTitle(_("Device"))

			else:
				curSelFile = self["fileList"].getCurrentDirectory() + self["fileList"].getFilename()
				file_stats = os_stat(curSelFile)
				file_infos = self.return_media_kind(self.return_extention(curSelFile)).upper() + ":    "
				file_infos = file_infos + "size " + str(FM_Humanizer(file_stats.st_size))
				self.setTitle(_(file_infos))

		def FM_Humanizer(size):
			if (size < 1024):
				humansize = str(size) + " B"
			elif (size < 1048576):
				humansize = str(size / 1024) + " KB"
			else:
				humansize = str(size / 1048576) + " MB"
			return humansize

		def VirtualKeyboart_dir_rename_Callback(callback):
			if callback is None or callback == "":
				self.showFilemanagerScreen_command = ("Do_nothing", self.showFilemanagerScreen_command[1])
				self.showFilemanagerScreen_without_callback()
			else:
				self.showFilemanagerScreen_command = ("rename", self.showFilemanagerScreen_command[1], "/".join(self.showFilemanagerScreen_command[1].split("/")[0:-2]) + "/" + callback + "/")
				self.showFilemanagerScreen_without_callback()

		def VirtualKeyboart_file_rename_Callback(callback):
			if callback is None or callback == "":
				self.showFilemanagerScreen_command = ("Do_nothing", self.showFilemanagerScreen_command[1])
				self.showFilemanagerScreen_without_callback()
			else:
				self.showFilemanagerScreen_command = ("rename", self.showFilemanagerScreen_command[1], "/".join(self.showFilemanagerScreen_command[1].split("/")[0:-1]) + "/" + callback)
				self.showFilemanagerScreen_without_callback()

		def get_FileManagerCommands_callback(callback):
			self.showFilemanagerScreen_command = callback

			if self.fileManagerEnabled is True:
				if self.showFilemanagerScreen_command[0] == "copy" or self.showFilemanagerScreen_command[0] == "move":
					pass  # do nothing execute command during blue button press
				elif self.showFilemanagerScreen_command[0] == "rename":
					if os.path.isdir(self.showFilemanagerScreen_command[1]):
						self.session.openWithCallback(VirtualKeyboart_dir_rename_Callback, VirtualKeyBoard, title=_("Oryginal dir name: %s" % self.showFilemanagerScreen_command[1].split("/")[-2]), text=self.showFilemanagerScreen_command[1].split("/")[-2])
					elif os.path.isfile(self.showFilemanagerScreen_command[1]):
						self.session.openWithCallback(VirtualKeyboart_file_rename_Callback, VirtualKeyBoard, title=_("Oryginal file name: %s" % self.showFilemanagerScreen_command[1].split("/")[-1]), text=self.showFilemanagerScreen_command[1].split("/")[-1])
				elif self.showFilemanagerScreen_command[0] == "Do_nothing":
					self.set_FileManager_disabled()
				else:
					#for Do_nothing and delete
					self.showFilemanagerScreen_without_callback()

		if self.fileManagerEnabled is False and callback != "file_info_on_screen_title":
			if self["fileList"].canDescent():
				current_dir = self["fileList"].getCurrentDirectory()
				current_selection = self["fileList"].getSelection()[0]
			else:
				current_dir = self["fileList"].getCurrentDirectory()
				current_selection = self["fileList"].getCurrentDirectory() + self["fileList"].getSelection()[0]  # ('/hdd/Net_HDD/Filmy/Seriale/Boardwalk Empire Season 2/', True)

			if os.path.exists(str(current_selection)) and "/".join(str(current_dir).split("/")[:-2]) + "/" != current_selection and not isinstance(current_dir, type(None)):
				self.set_FileManager_enabled()
				self.setServerAvailableSubtitles_for_dirList(current_dir)
				self.session.openWithCallback(get_FileManagerCommands_callback, FileManagerCommands, current_selection)

		if self.showFilemanagerScreen_command == "file_info_on_screen_title":
			FM_file_Info(self)
			self.set_listFile_enabled()


# !!!!!!!!!!!! PICTURE FUNCTIONS !!!!!!!!!!!!!!

	def display_Server_Picture(self):
		"""Function display suittalbe picture in ["serverPicture"] (based on subtitle server)"""
		self.serverPicturePath = "/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/pic/%s.jpg" % config.plugins.subsdownloader.subtitleserver.value
		self.ServerPicture.startDecode(self.serverPicturePath)

	def Show_Server_Picture(self):
		"""This function is required to init witget ["serverPicture"] and picture class [self.ServerPicture]"""
		self.ServerPicture.setPara([self["serverPicture"].instance.size().width(), self["serverPicture"].instance.size().height(), 1, 1, 0, 1, "#002C2C39"])
		self.ServerPicture.startDecode(self.serverPicturePath)

	def DecodeServerPictureAction(self, pictureInfo=""):
		"""This function is required to init witget ["serverPicture"] and picture class [self.ServerPicture]"""
		ptr = self.ServerPicture.getData()
		self["serverPicture"].instance.setPixmap(ptr)
		#text = picInfo.split('\n',1)    #WYSWIETLA INFORMACJE NA TEMAT OBRAZKA
		#self["label"].setText(text[1])  #WYSWIETLA INFORMACJE NA TEMAT OBRAZKA

	def Find_Commertial_Picure(self):
		commertial_pictures = []
		for x in os.listdir(Subtitle_Downloader_temp_dir):
			if self.return_media_kind(self.return_extention(x)) == "picture":
				commertial_pictures.append(Subtitle_Downloader_temp_dir + x)
		if commertial_pictures == []:
			return ["/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/pic/none1.jpg"]
		else:
			return commertial_pictures

	def Show_Commertial_Picture(self):
		"""This function is required to init witget ["commertialPicture"] and picture class self.CommertialPicture"""
		self.CommertialPicture.setPara([self["commertialPicture"].instance.size().width(), self["commertialPicture"].instance.size().height(), 1, 1, 0, 1, "#002C2C39"])
		self.CommertialPicture.startDecode(self.CommertialPicturePath)

	def DecodeCommertialPictureAction(self, pictureInfo=""):
		"""This function is required to init witget ["serverPicture"] and picture class [self.ServerPicture]"""
		ptr = self.CommertialPicture.getData()
		self["commertialPicture"].instance.setPixmap(ptr)
		#text = picInfo.split('\n',1)    #WYSWIETLA INFORMACJE NA TEMAT OBRAZKA
		#self["label"].setText(text[1])  #WYSWIETLA INFORMACJE NA TEMAT OBRAZKA

	def display_Commmertial_Picture(self, picture_path):
		self.CommertialPicturePath = picture_path
		self.CommertialPicture.startDecode(self.CommertialPicturePath)

	def executeDMnapi(self, media_file_path):
		try:
			#self.session.openWithCallback(self.__movie_Callback, DMnapi, sel[B_FULL]) #oryginal Gemini File Browser execution line
			self.session.openWithCallback(self.__executeDMnapi_callback, DMnapi, media_file_path)

		except:
			self.session.open(MessageBox, _("There is problem with DMnapi execution.\nCheck if Your SubsDownloader supports DMnapi %s version.", dmnapi_version), MessageBox.TYPE_INFO, timeout=10)

	def __executeDMnapi_callback(self, callback=None):
		self["fileList"].refresh()

# !!!!!!!!!!!! PICTURE FUNCTIONS !!!!!!!!!!!!!!

	def clearSubList(self):
		"""Clear subList and prevent to download unwanted subtitle"""
		self.serverAvailableSubtitles = []
		self["subsList"].setList(self.serverAvailableSubtitles)
		self.subsListDownloaded = 0
		#self.set_listFile_enabled()

	def setServerAvailableSubtitles_for_PERISCOPE(self, serverList):
		"""Function preper (appends) serverAvailableSubtitles which is seted by
		comend self["subsList"].setList(self.serverAvailableSubtitles)"""
		self.serverAvailableSubtitles = []
		position = 0
		for x in serverList:
			self.serverAvailableSubtitles.append(("[" + str(x['lang']) + "]___" + str(x['release']), str(position)))
			position = position + 1
		self.subsListDownloaded = 1
		self["subsList"].setList(self.serverAvailableSubtitles)
		self.set_listSubs_enabled()

	def setServerAvailableSubtitles_for_XBMC_SUBTITLES(self, serverList):
		"""Function preper (appends) serverAvailableSubtitles which is seted by
		comend self["subsList"].setList(self.serverAvailableSubtitles)"""
		self.serverAvailableSubtitles = []
		position = 0
		if 'no_files' in serverList[0]:
			for x in serverList:
				self.serverAvailableSubtitles.append(("[" + str(x['language_name']) + "]_" + str(x['no_files']) + "cd__" + str(x['filename']), position))
				position = position + 1
		else:
			for x in serverList:
				self.serverAvailableSubtitles.append(("[" + str(x['language_name']) + "]_" + str(x['filename']), position))
				position = position + 1
		self.subsListDownloaded = 1
		self["subsList"].setList(self.serverAvailableSubtitles)
		self.set_listSubs_enabled()

	def setServerAvailableSubtitles_for_dirList(self, current_dir):
		if os.path.exists(str(current_dir)):
			a = sorted(os.listdir(current_dir))
			self.serverAvailableSubtitles = []
			self.serverAvailableSubtitles.append(("/..", "/".join(current_dir.split("/")[0:-2]) + "/"))
			for x in a:
				if os.path.isdir(os.path.join(current_dir, x)):
					self.serverAvailableSubtitles.append(("/" + x + "/", os.path.join(current_dir, x) + "/"))
			self.subsListDownloaded = 1
			self["subsList"].setList(self.serverAvailableSubtitles)
			self["subsList"].moveToIndex(0)
			self.set_listSubs_enabled()

	def setServerAvailableSubtitles_for_Napisy24(self, serverList):
		"""Function preper (appends) serverAvailableSubtitles which is seted by
		comend self["subsList"].setList(self.serverAvailableSubtitles)"""
		self.serverAvailableSubtitles = []
		position = 0
		for x in serverList:
			self.serverAvailableSubtitles.append((str(x['language']).replace("u'", "").replace("'", "") + "_" + str(x['cd']).replace("u'", "").replace("'", "") + "cd__" + str(x['title']).replace("u'", "").replace("'", "") + " " + str(x['release']).replace("u'", "").replace("'", ""), position))  # makes list of subtitles
			position = position + 1
		self.subsListDownloaded = 1
		self["subsList"].setList(self.serverAvailableSubtitles)
		self.set_listSubs_enabled()

	def saveSubtitleasSRT(self, subtitleFile, fps, subtitleCodePage):
		"""Function converts and saves downloaded subtitle in suitable ditectory"""
		subtitle_codepade = codePageDecoded = chardetOutputTranslation(subtitleCodePage)
		if codePageDecoded != "None":
			convertedSubtitle = SubConv(subtitleFile, codePageDecoded)
			subtitleFormat = convertedSubtitle.detect_format(convertedSubtitle.subs_file)
		#TODO IN TERMINAF SHOW PROGRESS
		if subtitleFile != "None" and fps != "None" and codePageDecoded != "None" and subtitleFormat != "None":
			progress_message = "Saved subtitle file: %s \nDetected oryginal subtitle format:  %s \nDetected subtitle CodePage: %s (%s) with probability %s \nDetected movie FPS: %s \n   PRES OK KEY TO CONTINUE..." % (subtitleFile, subtitleFormat, subtitleCodePage['encoding'], codePageDecoded, subtitleCodePage['confidence'], fps)
			self.session.open(MessageBox, _(progress_message), MessageBox.TYPE_INFO)
			if subtitleFormat == "mdvd":
				convertedSubtitle.subs_file = convertedSubtitle.read_mdvd(convertedSubtitle.subs_file, fps)
			elif subtitleFormat == "tmp":
				convertedSubtitle.subs_file = convertedSubtitle.read_tmp(convertedSubtitle.subs_file)
			elif subtitleFormat == "sub2":
				convertedSubtitle.subs_file = convertedSubtitle.read_sub2(convertedSubtitle.subs_file)
			elif subtitleFormat == "srt":
				convertedSubtitle.subs_file = convertedSubtitle.read_srt(convertedSubtitle.subs_file)
			elif subtitleFormat == "mpl2":
				convertedSubtitle.subs_file = convertedSubtitle.read_mpl2(convertedSubtitle.subs_file)
			convertedSubtitle.subs_file = convertedSubtitle.check_subs_long(convertedSubtitle.subs_file, fps)
			#convertedSubtitle.save_subtitle(subtitleFile, convertedSubtitle.subs_file)
			convertedSubtitle.save_subtitle(convertedSubtitle.subs_file)
		else:
			if subtitleFile == "None":
				self.session.open(MessageBox, _("Can't find subtitle file on storage device.\n Check:\n -network connection,\n - subtitle server availability,\n - storage device access."), MessageBox.TYPE_INFO)
			if fps == "None":
				self.session.open(MessageBox, _("Can't detect movie FPS. Please install libMediaInfor from ConfigurationMenu."), MessageBox.TYPE_INFO)
				#TODO automatic send email with: subtitle, filn hash sume to developer - if user allow for this - for developement reaseons
			if codePageDecoded == "None":
				self.session.open(MessageBox, _("Can't detect downloaded subtitle code page. Please contact with developer to correct this in future versions."), MessageBox.TYPE_INFO)
				#TODO automatic send email with: subtitle, filn hash sume to developer - if user allow for this - for developement reaseons
				self.session.open(MessageBox, _("Can't detect downloaded subtitle format. Please contact with developer to correct this in future versions."), MessageBox.TYPE_INFO)
				#TODO automatic send email with: subtitle, filn hash sume to developer - if user allow for this - for developement reaseons
		return subtitleFormat

	def getSubtitleCodepade(self, subtitle):
		"""Function gets subtitle file codepage using Chardet library"""
		subtitleFile = open(subtitle, 'r')
		data = subtitleFile.read()
		subtitleFile.close()
		return chardet.detect(data)

	def goLeft(self):
		self.selectedList.pageUp()

	def goRight(self):
		self.selectedList.pageDown()

	def getMovieFPS(self, movie):
		try:
			choosen_movie = GetFPS(movie)
			#return float(str(round(choosen_movie.fps(),3))[0:-1])
			return round(choosen_movie.fps(), 3)  # JESLI NAPISY NIE BEDA W CZASIE PADSOWAC TO POKOMBINOWAC Z TA LINIJKA
		except:
			self.session.open(MessageBox, _("I can't detect movie FPS!!!"), MessageBox.TYPE_INFO, timeout=5)
			return "None"

	def __defaults_before_subtitle_download_and_convertion(self):
		self.subtitle_database = 0
		self.movie_filename = 0
		self.subtitles = 0
		self.subtitle_filename = 0
		self.clearSubList()

	def localConvertionSublist(self):
		"""Search dir for subtitle file and converts it to given movie file"""
		selected_movie_dir = self["fileList"].getCurrentDirectory()
		selected_movie_file = self["fileList"].getFilename()
		local_subtitle = []
		if self.selectedList == self["fileList"] and self.return_media_kind(self.return_extention(selected_movie_file)) == "movie":
			self.localConvertion = True
			self.session.open(MessageBox, _("Local subtitle convertion for:\n%s." % (str(selected_movie_file))), MessageBox.TYPE_INFO, timeout=15)
			self.__defaults_before_subtitle_download_and_convertion()
			self.movie_filename = selected_movie_dir + selected_movie_file
			file_list = self["fileList"].getFileList()
			for x in file_list:
				if x[0][-1] is not True:  # not directory
					if self.return_media_kind(self.return_extention(x[0][0])) == "text":  # and LocalConvertedSubtitle.detect_format(LocalConvertedSubtitle.subs_file) != "None":
						#localCodePageDecoded= self.chardetOutputTranslation(self.getSubtitleCodepade(selected_movie_dir+x[0][0]))
						self.subtitle_codepade = localCodePageDecoded = chardetOutputTranslation(self.getSubtitleCodepade(selected_movie_dir + x[0][0]))
						LocalConvertedSubtitle = SubConv((selected_movie_dir + x[0][0]), localCodePageDecoded)
						if LocalConvertedSubtitle.detect_format(LocalConvertedSubtitle.subs_file) != "None":
							local_subtitle.append((x[0][0], str(selected_movie_dir + x[0][0])))  # makes list of subtitles"""
							self.subsListDownloaded = 1
			self["subsList"].setList(local_subtitle)
			self.set_listSubs_enabled()
		else:
			self.session.open(MessageBox, _("I can't convert subtitle for this kind of media!!!"), MessageBox.TYPE_INFO, timeout=5)

	def convert_subtitle_to_movie(self, movie_filename, subtitle_filename):
		if (movie_filename.rsplit(".", 1)[0] + ".srt") == subtitle_filename:
			pass
		else:
			rename_filename = (movie_filename.rsplit(".", 1)[0] + ".srt")
			os.rename(subtitle_filename, rename_filename)
			subtitle_filename = rename_filename
		try:
			subtitle_codepade = self.getSubtitleCodepade(subtitle_filename)
			movie_fps = self.getMovieFPS(movie_filename)
			subtitle_filename_type = self.saveSubtitleasSRT(subtitle_filename, movie_fps, subtitle_codepade)
			self["fileList"].refresh()
		except:
			try:
				self.failed_to_download_subtitle_nfo(subtitle_filename, subtitle_codepade, subtitle_filename_type, movie_fps)
			except:
				self.failed_to_download_subtitle_nfo(subtitle_filename, subtitle_codepade, "unsupported", movie_fps)

	def downloadSubtitle(self):
		"""Download Subtitle for movie variable self.textEXTENSIONS has defived all supported files and their king.
		Variable self.textEXTENSIONS is self.textEXTENSIONS and EXTENSIONS union"""

		self.__defaults_before_subtitle_download_and_convertion()
		self.localConvertion = False
		if self["fileList"].canDescent():
			self.session.open(MessageBox, _("I can't download subtitle for this kind of media!!!"), MessageBox.TYPE_INFO, timeout=5)
		else:
			self.movie_filename = self["fileList"].getCurrentDirectory() + self["fileList"].getFilename()
			if self.return_media_kind(self.return_extention(self.movie_filename)) == "movie":
				if config.plugins.subsdownloader.subtitleserver.value in PERISCOPE_PLUGINS:  # == "OpenSubtitle":
					exec('from Plugins.Extensions.SubsDownloader2.SourceCode.periscope.services.%s.services import %s as SERVICE') % (config.plugins.subsdownloader.subtitleserver.value, config.plugins.subsdownloader.subtitleserver.value)
					self.subtitles = SERVICE(None, Subtitle_Downloader_temp_dir)
					#try:
					self.subtitle_database = self.subtitles.process(self.movie_filename, [config.plugins.subsdownloader.SubsDownloader1stLang.value, config.plugins.subsdownloader.SubsDownloader2ndLang.value, config.plugins.subsdownloader.SubsDownloader3rdLang.value])
					#except:
					#	pass
					#TODO TU BY SIE PRZYDALA OBSLUGA WYJATKOW Z KOMENDY POWYZEJ
					#if len(self.subtitle_database) == 0:
					if self.subtitle_database == []:
						self.clearSubList()
						self.session.open(MessageBox, _("There is no subtitle on this server to Your movie. \nPlease try another language or subtitle server.\n\nIf error still appears please check network connection with server."), MessageBox.TYPE_INFO, timeout=5)
					else:
						self.setServerAvailableSubtitles_for_PERISCOPE(self.subtitle_database)
				elif config.plugins.subsdownloader.subtitleserver.value in XBMC_PLUGINS:

					exec('from Plugins.Extensions.SubsDownloader2.SourceCode.xbmc_subtitles.services.%s import *' % config.plugins.subsdownloader.subtitleserver.value)
					exec('from Plugins.Extensions.SubsDownloader2.SourceCode.xbmc_subtitles.services.%s import service as SERVICE' % config.plugins.subsdownloader.subtitleserver.value)

					temp_struct = GuessFileData_from_FileName(SubtitleDatabase.tvshowRegex, SubtitleDatabase.tvshowRegex2, SubtitleDatabase.movieRegex)
					show_name, show_type, show_season, show_episode = temp_struct.return_movie_data_to_XBMC(self.movie_filename)
					lang1 = config.plugins.subsdownloader.SubsDownloader1stLang.value
					lang2 = config.plugins.subsdownloader.SubsDownloader2ndLang.value
					lang3 = config.plugins.subsdownloader.SubsDownloader3rdLang.value
					self.subtitle_database, self.__session_id, self.__msg = SERVICE.search_subtitles(self.movie_filename, show_name, show_type, "year", show_season, show_episode, Subtitle_Downloader_temp_dir, False, lang1, lang2, lang3, True, self.session)

					#self.subtitle_database= self.subtitles.XBMC_search_subtitles(self.movie_filename,config.plugins.subsdownloader.SubsDownloader1stLang.value,config.plugins.subsdownloader.SubsDownloader2ndLang.value,config.plugins.subsdownloader.SubsDownloader3rdLang.value)
					if self.subtitle_database == []:
						self.clearSubList()
						self.session.open(MessageBox, _("There is no subtitle on this server to Your movie. \nPlease try another language or subtitle server.\n\nIf error still appears please check network connection with server."), MessageBox.TYPE_INFO, timeout=5)
					else:
						#os.system('echo "%s" >> /text' % str(self.subtitle_database))
						self.setServerAvailableSubtitles_for_XBMC_SUBTITLES(self.subtitle_database)
				elif config.plugins.subsdownloader.subtitleserver.value == "NapiProjekt":
					#self.isSubtitleDowloaded=0
					#self.whichSubtitleDownload="None"
					subtitle_filename = []
					#self.movie_fps = "None"
					#self.subtitle_codepade = "None"
					#self.subtitle_filename_type = "None"

					self.movie_filename = self["fileList"].getCurrentDirectory() + self["fileList"].getFilename()
					self.NapiSubtitle = NapiProjekt()
					self.NapiSubtitle.getnapi(self.movie_filename)

					subtitle_filename.append(self.NapiSubtitle.save())
					if subtitle_filename[0] != "None":
						self.convert_subtitle_to_movie(self.movie_filename, subtitle_filename[0])
					else:
						self.session.open(MessageBox, _("There is problem with downloading or saveing subtitles on storage device."), MessageBox.TYPE_INFO, timeout=5)

					"""try:
						self.NapiSubtitle.getnapi(self.movie_filename)
						self.subtitle_filename = self.NapiSubtitle.save()


						self.subtitle_codepade = self.getSubtitleCodepade(self.subtitle_filename)
						self.movie_fps = self.getMovieFPS(self.movie_filename)
						self.subtitle_filename_type = self.saveSubtitleasSRT(self.subtitle_filename, self.movie_fps, self.subtitle_codepade)
					except:
						self.failed_to_download_subtitle_nfo(self.subtitle_filename,self.subtitle_codepade,self.subtitle_filename_type,self.movie_fps)"""
					#self["fileList"].refresh()
					#TODO SUBTITLE SELECTION AND DOWNLOAD OTHER SERVERS
				elif config.plugins.subsdownloader.subtitleserver.value == "DMnapi":
					#self.isSubtitleDowloaded=0
					#self.whichSubtitleDownload="None"
					subtitle_filename = []
					#self.movie_fps = "None"
					#self.subtitle_codepade = "None"
					#self.subtitle_filename_type = "None"
					self.movie_filename = self["fileList"].getCurrentDirectory() + self["fileList"].getFilename()
					self.executeDMnapi(self.movie_filename)
				elif config.plugins.subsdownloader.subtitleserver.value == "Napisy24":
					N24_movie_name = None
					N24_imdb_search = None
					self.virtualKeyboardOpen()
			elif config.plugins.subsdownloader.subtitleserver.value == "Napisy24":
				pass
			else:
				self.session.open(MessageBox, _("I can't download subtitle for this kind of media!!!"), MessageBox.TYPE_INFO, timeout=5)

	def virtualKeyboardOpen(self):
		if config.plugins.subsdownloader.Napisy24SearchMethod.value == "IMDB then movie filname" or config.plugins.subsdownloader.Napisy24SearchMethod.value == "movie filname":
			if config.plugins.subsdownloader.Napisy24MovieNameMethod.value is False:
				movie_name = self["fileList"].getFilename().rsplit(".", 1)[0]
			elif config.plugins.subsdownloader.Napisy24MovieNameMethod.value is True:
				temp_struct = GuessFileData_from_FileName(SubtitleDatabase.tvshowRegex, SubtitleDatabase.tvshowRegex2, SubtitleDatabase.movieRegex)
				movie_name = temp_struct.return_data_string(self["fileList"].getFilename())
			self.session.openWithCallback(self.VirtualKeyboartCallback, VirtualKeyBoard, title=("Search subtitle(s) for:\n%s" % self["fileList"].getFilename()), text=movie_name)
		else:
			self.VirtualKeyboartCallback(callback=None)

	def VirtualKeyboartCallback(self, callback=None):
		N24_movie_name = None
		N24_imdb_search = None
		IMDM_results = None
		if config.plugins.subsdownloader.Napisy24SearchMethod.value == "IMDB":
			N24_imdb_search = True
			#N24_movie_name = None
		elif config.plugins.subsdownloader.Napisy24SearchMethod.value == "IMDB then movie filname":
			N24_imdb_search = True
			N24_movie_name = callback
		elif config.plugins.subsdownloader.Napisy24SearchMethod.value == "movie filname" and callback is not None:
			N24_imdb_search = False
			N24_movie_name = callback
		self.subtitles = Napisy24_pl(self.movie_filename, N24_movie_name)
		if N24_imdb_search is True:
			#IMDB search method - seek NFO file
			IMDM_results = self.subtitles.IMDB_idenifier_search()
			if IMDM_results is not False:
				#IMDB search method - if NFO contains IMBD try to download XML by IMBD number
				if self.subtitles.getNapisy24_SubtitleListXML("downloada_subtitle_list_by_IMDB") is False and N24_movie_name is not None:
					#IMDB then movie filname dearch method - If XML download by IMBD number fails try to download by movie name
					self.subtitles.getNapisy24_SubtitleListXML("downloada_subtitle_list_by_film_name")
			elif IMDM_results is False:
				#IMDB then movie filname dearch method - in case there is no NFO file
				self.subtitles.getNapisy24_SubtitleListXML("downloada_subtitle_list_by_film_name")
		if N24_imdb_search is False and N24_movie_name is not None:
			#movie filname search method
			self.subtitles.getNapisy24_SubtitleListXML("downloada_subtitle_list_by_film_name")
		if self.subtitles.subtitle_dict != []:
			self.setServerAvailableSubtitles_for_Napisy24(self.subtitles.subtitle_dict)
		else:
			if (IMDM_results is False or IMDM_results is None) and N24_movie_name is None:
				if config.plugins.subsdownloader.Napisy24SearchMethod.value == "IMDB":
					self.session.open(MessageBox, _("NAPISY24 searching method error:\n\nCan't find IMDB identifier for this movie.\nPlease try another searching method."), MessageBox.TYPE_INFO, timeout=10)
				elif config.plugins.subsdownloader.Napisy24SearchMethod.value == "IMDB then movie filname":
					self.session.open(MessageBox, _("NAPISY24 searching method error:\n\nBoth IMDB and movie name haven't values. \nPlease give at least one correct searching value."), MessageBox.TYPE_INFO, timeout=10)
				elif config.plugins.subsdownloader.Napisy24SearchMethod.value == "movie filname":
					self.session.open(MessageBox, _("NAPISY24 searching method error:\n\nPlease enter movie name to search."), MessageBox.TYPE_INFO, timeout=10)
			else:
				self.session.open(MessageBox, _("There is no subtitle on this server to Your movie. \nPlease try another search method or subtitle server.\n\nIf error still appears please check network connection with server."), MessageBox.TYPE_INFO, timeout=10)

	def failed_to_download_subtitle_nfo(self, subtitle_filename, subtitle_codepade_, subtitle_filename_type, movie_fps):
		self.session.open(MessageBox, _("Failed to download or save file.\nPossible problems:\n- Subtitle filname:\n%s\n- Subtitle codepage:\n%s\n- Subtitle filetype:\n%s\n- Movie fsp:\n%s\n.") % (subtitle_filename, subtitle_codepade_, subtitle_filename_type, movie_fps), MessageBox.TYPE_INFO, timeout=15)

	def make_media_patern(self):
		"""Creare media patern to file browser based on self.textEXTENSIONS from this module
		and EXTENSIONS fron FileList module"""
		self.textEXTENSIONS.update(EXTENSIONS)
		return r"^.*\.(" + str.join('|', self.textEXTENSIONS.keys()) + ")"

	def return_extention(self, file_path):
		"""get filename and return file extention"""
		extention = file_path
		return extention.split('.')[-1]

	def return_media_kind(self, file_extention):
		"""Function returns what kind of file is it: text, movie, sysyem, picture"""
		try:
			return self.textEXTENSIONS[file_extention]
		except:
			return 'not_supported'

	def showConfigScreen(self):
		""" Display config screen for Subs Downloader"""
		self.set_listFile_enabled()
		self.subsListDownloaded = 0
		self.serverAvailableSubtitles = []
		self["subsList"].setList(self.serverAvailableSubtitles)
		#self.session.open(SubsDownloaderConfig)
		#self.session.openWithCallback(self.display_Server_Picture, SubsDownloaderConfig)
		self.session.openWithCallback(self.MainMenuCallback, SubsDownloaderConfig)

		#TODO POPRAWIC TO PONIEWAZ NIE ZMIENIA SIE PO POWROCIE Z self.session.open(SubsDownloaderConfig)
		#self.display_Server_Picture()

	def MainMenuCallback(self):
		self.display_Server_Picture()
		if config.plugins.subsdownloader.pathUseMediaPaternFilter.value is True:
			self["fileList"].matchingPattern = self.mediaPatern
		else:
			self["fileList"].matchingPattern = None
		self["fileList"].refresh()

	def set_listFile_enabled(self):
		"""Function makes self["fileList"] as active"""
		if self.fileManagerEnabled is False:
			self["fileList"].selectionEnabled(1)
			self["subsList"].selectionEnabled(0)
			self.selectedList = self["fileList"]
		elif self.fileManagerEnabled is True:
			self.set_FileManager_disabled()
			self.clearSubList()

	def set_FileManager_enabled(self):
		self["fileList"].selectionEnabled(0)
		self["subsList"].selectionEnabled(1)
		self.localConvertion = False
		self.fileManagerEnabled = True
		self["key_last"].setText("Disable FileManager")
		self["key_info"].setText("Disable FileManager")
		self["key_blue"].setText("Execute command")

	def set_FileManager_disabled(self):
		self.fileManagerEnabled = False
		self["key_last"].setText("FileList enable")
		self["key_info"].setText("File size")
		self["key_blue"].setText("Enable FileManager")
		self.set_listFile_enabled()
		self.showFilemanagerScreen_command = None
		self.clearSubList()

	def set_listSubs_enabled(self):
		"""If subtitle was found and list was generated function makes self["subsList"] as active.
		The condition is that self.subsListDownloaded is "1". Condition is seted in downloadSubtitle function.
		Not alvays seting of self["subsList"] is required."""
		if self.subsListDownloaded == 1:
			#self.localConvertion = True
			self["fileList"].selectionEnabled(0)
			self["subsList"].selectionEnabled(1)
			self.selectedList = self["subsList"]

	def __pass__(self):
		pass

	def ok(self):
		global DVDPlayerAviable
		if self.selectedList == self["fileList"] and self.fileManagerEnabled is False:
			if self["fileList"].canDescent():
				"""If dir makes cd"""
				self["fileList"].descent()
			else:
				filename = self["fileList"].getCurrentDirectory() + self["fileList"].getFilename()
				testFileName = self["fileList"].getFilename()
				testFileName = testFileName.lower()
				if filename is not None:
					if self.return_media_kind(self.return_extention(testFileName)) == "movie":
						#self.session.open(MoviePlayer, filename)
						self.session.openWithCallback(self["fileList"].refresh, MoviePlayer, filename)
					elif (testFileName.endswith(".mp3")) or (testFileName.endswith(".wav")) or (testFileName.endswith(".ogg")) or (testFileName.endswith(".m4a")) or (testFileName.endswith(".mp2")) or (testFileName.endswith(".flac")):
						if (self.MyBox == "dm7025") and ((testFileName.endswith(".m4a")) or (testFileName.endswith(".mp2")) or (testFileName.endswith(".flac"))):
							return
						if MMPavaiable:
							SongList, SongIndex = self.searchMusic()
							try:
								self.session.open(MerlinMusicPlayerScreen, SongList, SongIndex, False, self.altservice, None)
							except:
								self.session.open(MessageBox, _("Incompatible MerlinMusicPlayer version!"), MessageBox.TYPE_INFO)
						else:
							fileRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + filename)
							m_dir = self["fileList"].getCurrentDirectory()
							self.session.open(MusicExplorer, fileRef, m_dir, testFileName)
					elif (testFileName.endswith(".jpg")) or (testFileName.endswith(".jpeg")) or (testFileName.endswith(".jpe")) or (testFileName.endswith(".png")) or (testFileName.endswith(".bmp")):
						if self["fileList"].getSelectionIndex() != 0:
							Pdir = self["fileList"].getCurrentDirectory()
							self.session.open(PictureExplorerII, filename, Pdir)
					elif (testFileName.endswith(".mvi")):
						self.session.nav.stopService()
						self.session.open(MviExplorer, filename)
					elif (testFileName == "video_ts.ifo"):
						if DVDPlayerAviable:
							if (self["fileList"].getCurrentDirectory()).lower().endswith("video_ts/"):
								self.session.open(DVDPlayer, dvd_filelist=[self["fileList"].getCurrentDirectory()])
					elif testFileName.endswith(".iso"):
						if DVDPlayerAviable:
							self.session.open(DVDPlayer, dvd_filelist=[filename])
					elif testFileName.endswith(".tar.gz"):
						self.commando = ["tar -xzvf " + filename + " -C /"]
						askList = [(_("Cancel"), "NO"), (_("Install this package"), "YES")]
						dei = self.session.openWithCallback(self.SysExecution, ChoiceBox, title=_("GZ-package:\\n" + filename), list=askList)
						dei.setTitle(_("Subtitle Downloader : Install..."))
					elif testFileName.endswith(".tar.bz2"):
						self.commando = ["tar -xjvf " + filename + " -C /"]
						askList = [(_("Cancel"), "NO"), (_("Install this package"), "YES")]
						dei = self.session.openWithCallback(self.SysExecution, ChoiceBox, title=_("BZ2-package:\\n" + filename), list=askList)
						dei.setTitle(_("SubsDownloader : Install..."))
					elif testFileName.endswith(".ipk"):
						if fileExists("/usr/bin/opkg"):
							self.commando = ["opkg install " + filename]
						else:
							self.commando = ["ipkg install " + filename]
							askList = [(_("Cancel"), "NO"), (_("Install this package"), "YES")]
							dei = self.session.openWithCallback(self.SysExecution, ChoiceBox, title=_("IPKG-package:\\n" + filename), list=askList)
							dei.setTitle(_("SubsDownloader : Install..."))
					elif testFileName.endswith(".sh"):
						self.commando = [filename]
						askList = [(_("Cancel"), "NO"), (_("View this shell-script"), "VIEW"), (_("Start execution"), "YES")]
						self.session.openWithCallback(self.SysExecution, ChoiceBox, title=_("Do you want to execute?\\n" + filename), list=askList)
					else:
						xfile = os_stat(filename)
						if (xfile.st_size < 61440):
							self.session.open(vEditor, filename)
						else:
							self.session.open(MessageBox, _("File size is bigger than 61440.\n\n Subs Downloader can't manage it with vEditor."), MessageBox.TYPE_INFO, timeout=5)
		if self.selectedList == self["subsList"] and self.fileManagerEnabled is False:
			whichSubtitleDownload = "None"
			subtitle_filename = []
			if self.localConvertion is False:
				#download subtitle from server\
				if config.plugins.subsdownloader.subtitleserver.value in PERISCOPE_PLUGINS:  # == "OpenSubtitle":
					whichSubtitleDownload = self["subsList"].getCurrent()[1]
					subtitle_filename = self.subtitles.createFile(self.subtitle_database[int(whichSubtitleDownload)], self.movie_filename)
				if config.plugins.subsdownloader.subtitleserver.value == "NapiProjekt":
					pass  # PASS BECAUSE NAPI PROJECT DOWNLOAD ONLY PL FILE AND IT'S DIRECTLY IN DOWNLOAD SUBTITLE FUNCTION.
				if config.plugins.subsdownloader.subtitleserver.value == "DMnapi":
					pass  # PASS BECAUSE DMnapi DOWNLOAD ONLY PL FILE AND IT'S DIRECTLY IN DOWNLOAD SUBTITLE FUNCTION.
				if config.plugins.subsdownloader.subtitleserver.value in XBMC_PLUGINS:
					exec('from Plugins.Extensions.SubsDownloader2.SourceCode.xbmc_subtitles.services.%s import *' % config.plugins.subsdownloader.subtitleserver.value)
					exec('from Plugins.Extensions.SubsDownloader2.SourceCode.xbmc_subtitles.services.%s import service as SERVICE' % config.plugins.subsdownloader.subtitleserver.value)
					pos = self["subsList"].getCurrent()[1]
					tmp_sub_dir = sub_folder = self.movie_filename.rsplit("/", 1)[0]
					zipped_subs_path = self.movie_filename.rsplit(".", 1)[0] + ".zip"  # for some plugins
					TRUE_FALSE, language, subtitle_filename = SERVICE.download_subtitles(self.subtitle_database, pos, zipped_subs_path, tmp_sub_dir, sub_folder, self.__session_id, self.session)

				if config.plugins.subsdownloader.subtitleserver.value == "Napisy24":
					whichSubtitleDownload = self["subsList"].getCurrent()[1]
					if self.subtitles.save_downloaded_zip(whichSubtitleDownload) is True:
						subtitle_filename = self.subtitles.extract_zip_file()
						try:
							os.remove(self.subtitles.ZipFilePath)  # remove downloaded zip file
						except:
							print("Can't delete file: %s" % self.subtitles.ZipFilePath)

				if isinstance(subtitle_filename, type("string")):
					self.convert_subtitle_to_movie(self.movie_filename, subtitle_filename)
				elif isinstance(subtitle_filename, type([])) or subtitle_filename is None:
					if len(subtitle_filename) == 1:
						self.convert_subtitle_to_movie(self.movie_filename, subtitle_filename[0])
					elif len(subtitle_filename) > 1:
						CompareMovie_and_Subtite = CompareMovie_and_Subtite_FileData(SubtitleDatabase.tvshowRegex, SubtitleDatabase.tvshowRegex2, SubtitleDatabase.movieRegex, EXTENSIONS)
						mathing_movie_subtitles = CompareMovie_and_Subtite.give_movie_subtitle_consistent_data(CompareMovie_and_Subtite.moviePath_and_movieFileData(self.movie_filename), CompareMovie_and_Subtite.subtitlePath_and_subtitleFileData(subtitle_filename))
						if mathing_movie_subtitles != []:
							for x in mathing_movie_subtitles:
								self.convert_subtitle_to_movie(x['movie'], x['subtitle'])
						else:
							self["fileList"].refresh()
							self.session.open(MessageBox, _("%i file(s) was extracted and I didn't match them automatically this time. \n Please make local convertion (long TEXT).") % (len(subtitle_filename)), MessageBox.TYPE_INFO, timeout=10)
				if subtitle_filename == [] or subtitle_filename == "":
					self.session.open(MessageBox, _("There is problem with downloading or saveing subtitles on storage device."), MessageBox.TYPE_INFO, timeout=5)

			elif self.localConvertion is True:
				#local convertion in progress
				whichSubtitleDownload = self["subsList"].getCurrent()[1]
				subtitle_filename.append(whichSubtitleDownload)
				self.convert_subtitle_to_movie(self.movie_filename, subtitle_filename[0])
			#TODO OTHER SUBTITLE SERVERS HANDLE
		if self.selectedList == self["subsList"] and self.fileManagerEnabled is True:
			a = os.listdir(self["subsList"].getCurrent()[1])
			dir_count = 0
			for x in a:
				if os.path.isdir(os.path.join(self["subsList"].getCurrent()[1], x) + "/"):
					dir_count = dir_count + 1
			if dir_count > 0:
				self.setServerAvailableSubtitles_for_dirList(self["subsList"].getCurrent()[1])

	def closeApplication(self):
		os.system('rm -r %s' % Subtitle_Downloader_temp_dir)
		print("\n[SubsDownloaderApplication] cancel\n")
		self.session.nav.playService(self.altservice)
		if config.plugins.subsdownloader.pathSave.value is True:
			config.plugins.subsdownloader.path.value = self["fileList"].getCurrentDirectory()
			config.plugins.subsdownloader.path.save()
		self.close(None)

	def goUp(self):
		self.set_title()
		self.selectedList.up()

	def goDown(self):
		self.set_title()
		self.selectedList.down()

	def showAboutScreen(self):
		self.session.open(vEditor, '/usr/lib/enigma2/python/Plugins/Extensions/SubsDownloader2/about.nfo')

	def searchMusic(self):
		slist = []
		foundIndex = 0
		index = 0
		files = sorted(os_listdir(self["fileList"].getCurrentDirectory()))
		for name in files:
			testname = name.lower()
			if testname.endswith(".mp3") or name.endswith(".m4a") or name.endswith(".ogg") or name.endswith(".flac"):
				slist.append((Item(text=name, filename=os_path.join(self["fileList"].getCurrentDirectory(), name)),))
				if self["fileList"].getFilename() == name:
					foundIndex = index
				index = index + 1
		return slist, foundIndex


class FileManagerCommands(Screen):
	def __init__(self, session, file_to_manage):
		self.file_to_manage = file_to_manage
		self.skin = "<screen position=\"center,80\" size=\"" + str(int(0.644 * Skin_width)) + "," + str(int(0.644 * Skin_height)) + "\" title=\"What to do with file:\" > \
		<widget name=\"myCommands\" position=\"10,10\" size=\"" + str(int(0.625 * Skin_width)) + "," + str(int(0.385 * Skin_height)) + "\" scrollbarMode=\"showOnDemand\" /> \
		</screen>"
		self.session = session
		Screen.__init__(self, session)
		self.list = []
		self["myCommands"] = MenuList(self.list)
		self["setupActions"] = ActionMap(["SetupActions", "DirectionActions", "WizardActions", "SubsDownloaderConfig_actions"], {
			"ok": self.ExitWithDoingSomething,
			"cancel": self.ExitWithoutDoingNothing
		}, -1)
		self.createCommandsMenu()

	def createCommandsMenu(self):
		self.list.append((_("Exit"), "exit"))
		self.list.append((_("Delete"), "delete"))
		self.list.append((_("Copy"), "copy"))
		self.list.append((_("Move"), "move"))
		self.list.append((_("Rename"), "rename"))
		#self.list.append((_(str(self.file_to_manage)), "exit"))
		self["myCommands"].setList(self.list)

	def ExitWithoutDoingNothing(self):
		self.close(["Do_nothing", self.file_to_manage])

	def ExitWithDoingSomething(self):
		def delete_command_notification(callback):
			if callback is True:
				self.close(("delete", self.file_to_manage))

			else:
				self.ExitWithoutDoingNothing()

		returnValue = self["myCommands"].l.getCurrentSelection()[1]
		if returnValue == "exit":
			self.ExitWithoutDoingNothing()
		elif returnValue == "delete":
			self.session.openWithCallback(delete_command_notification, MessageBox, _("Do You realy want to delete: /n %s" % self.file_to_manage), MessageBox.TYPE_YESNO, default=False)
		elif returnValue == "copy":
			self.close(("copy", self.file_to_manage))
		elif returnValue == "move":
			self.close(("move", self.file_to_manage))
		elif returnValue == "rename":
			self.close(("rename", self.file_to_manage))


class SubsDownloaderConfig(ConfigListScreen, Screen):
	def __init__(self, session):
		self.skin = "<screen position=\"center,80\" size=\"" + str(int(0.644 * Skin_width)) + "," + str(int(0.644 * Skin_height)) + "\" title=\"Subtitle downloader: Configuration screen\" > \
		<widget name=\"config\" position=\"10,10\" size=\"" + str(int(0.625 * Skin_width)) + "," + str(int(0.385 * Skin_height)) + "\" scrollbarMode=\"showOnDemand\" /> \
		<widget name=\"extendLibMediaInfo\" position=\"" + str(int(0.0434 * Skin_width)) + "," + str(int(0.6095 * Skin_height)) + "\" size=\"" + str(int(0.6076 * Skin_width)) + ",26\" valign=\"center\" halign=\"left\" zPosition=\"2\"  foregroundColor=\"yellow\" font=\"Regular;20\"/> \
		</screen>"
		self.session = session
		Screen.__init__(self, session)
		self["extendLibMediaInfo"] = Label()
		if is_libmediainfo is False and os.popen("unrar").readlines() != []:
			self["extendLibMediaInfo"].setText("Press YELLOW button to install libmediainfo.")
		elif is_libmediainfo is False and os.popen("unrar").readlines() == []:
			self["extendLibMediaInfo"].setText("Press YELLOW button to install libmediainfo and unrar.")
		elif os.popen("unrar").readlines() == []:
			self["extendLibMediaInfo"].setText("Press YELLOW button to install unrar.")
		else:
			self["extendLibMediaInfo"].setText("")
		self.list = []
		ConfigListScreen.__init__(self, self.list, session)
		self["setupActions"] = ActionMap(["SetupActions", "DirectionActions", "WizardActions", "SubsDownloaderConfig_actions"], {
			"left": self.keyLeft,
			"right": self.keyRight,
			"ok": self.saveConfig,
			"cancel": self.cancelWithoutSave  # add the RC Command "cancel" to close your Screen
		}, -1)
		self.createConfigMenu()

	def keyLeft(self):  # ABY DZIALALA AUTOMATYCZNA ZMIANA LIST WYSWIETLANEJ TA FUNKCJA MUSI SIE TAK NAZYWAC
		ConfigListScreen.keyLeft(self)
		self.createConfigMenu()

	def keyRight(self):  # ABY DZIALALA AUTOMATYCZNA ZMIANA LIST WYSWIETLANEJ TA FUNKCJA MUSI SIE TAK NAZYWAC
		ConfigListScreen.keyRight(self)
		self.createConfigMenu()

	def createConfigMenu(self):
		self.list = []
		self.list.append(getConfigListEntry(_("Choose subtitle server:"), config.plugins.subsdownloader.subtitleserver))
		if config.plugins.subsdownloader.subtitleserver.value in PERISCOPE_PLUGINS or config.plugins.subsdownloader.subtitleserver.value in XBMC_PLUGINS:  # == "OpenSubtitle":
			if config.plugins.subsdownloader.subtitleserver.value == "Itasa":
				self.list.append(getConfigListEntry(_("Itasa server user:"), config.plugins.subsdownloader.ItasaUser))
				self.list.append(getConfigListEntry(_("Itasa server password:"), config.plugins.subsdownloader.ItasaPassword))
			#TODO LOGIN AND PASSWORD TO OPENSUBTITLE
			self.list.append(getConfigListEntry(_("1st subtitle language:"), config.plugins.subsdownloader.SubsDownloader1stLang))
			self.list.append(getConfigListEntry(_("2nd subtitle language:"), config.plugins.subsdownloader.SubsDownloader2ndLang))
			self.list.append(getConfigListEntry(_("3rd subtitle language:"), config.plugins.subsdownloader.SubsDownloader3rdLang))
		if config.plugins.subsdownloader.subtitleserver.value == "NapiProjekt":
			pass
		if config.plugins.subsdownloader.subtitleserver.value == "Napisy24":
			self.list.append(getConfigListEntry(_("Choose Napisy24 search method:"), config.plugins.subsdownloader.Napisy24SearchMethod))
			self.list.append(getConfigListEntry(_("Use \"guessFileData\" method for movie filname:"), config.plugins.subsdownloader.Napisy24MovieNameMethod))
			pass
		self.list.append(getConfigListEntry(_("Extended configuratin menu:"), config.plugins.subsdownloader.extendedMenuConfig))
		if config.plugins.subsdownloader.extendedMenuConfig.value is True:
			self.list.append(getConfigListEntry(_("Save last FileList path:"), config.plugins.subsdownloader.pathSave))
			self.list.append(getConfigListEntry(_("Use media patern filter in FileList:"), config.plugins.subsdownloader.pathUseMediaPaternFilter))
			self.list.append(getConfigListEntry(_("Add Subs Downloader to BlueButton menu:"), config.plugins.subsdownloader.BlueButtonMenu))
			#self.list.append(getConfigListEntry(_("Delete oryginal subtitle after local convertion:"), config.plugins.subsdownloader.del_sub_after_conv))
		self["config"].list = self.list
		self["config"].setList(self.list)

	def cancelWithoutSave(self):
		#TODO RETURN TO APPLICATION AND NOTIFICATRION ABOIUT NOT SAVEING
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def saveConfig(self):
		for x in self["config"].list:
			x[1].save()
		self.close()


#######################################################################
#
#    Dream-ExplorerII for Dreambox-Enigma2
#    Coded by Vali (c)2009-2011
#    Support: www.dreambox-tools.info
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################

class vEditor(Screen):
	def __init__(self, session, file):
		self.skin = '<screen position="center,center" size="' + str(int(0.9 * Screen_width)) + ',' + str(int(0.9 * Screen_height)) + '" title="File-Explorer"> \
		<widget name="filedata" position="5,7" size="' + str(int(0.85 * Screen_width)) + ',' + str(int(0.85 * Screen_height)) + '" itemHeight="25"/> \
		</screen>'
		Screen.__init__(self, session)
		self.session = session
		self.file_name = file
		self.list = []
		self["filedata"] = MenuList(self.list)
		self["actions"] = ActionMap(["WizardActions"],
		{
			"ok": self.editLine,
			"back": self.exitEditor
		}, -1)
		self.selLine = None
		self.oldLine = None
		self.isChanged = False
		self.GetFileData(file)

	def exitEditor(self):
		if self.isChanged:
			warningtext = "\nhave been CHANGED! Do you want to save it?\n\nWARNING!"
			warningtext = warningtext + "\n\nThe Editor-Funktions are beta (not full tested) !!!"
			warningtext = warningtext + "\nThe author are NOT RESPONSIBLE\nfor DATA LOST OR DISORDERS !!!"
			dei = self.session.openWithCallback(self.SaveFile, MessageBox, _(self.file_name + warningtext), MessageBox.TYPE_YESNO)
			dei.setTitle(_("Dream-Explorer..."))
		else:
			self.close()

	def GetFileData(self, fx):
		try:
			flines = open(fx, "r")
			for line in flines:
				self.list.append(line)
			flines.close()
			self.setTitle(fx)
		except:
			pass

	def editLine(self):
		try:
			self.selLine = self["filedata"].getSelectionIndex()
			self.oldLine = self.list[self.selLine]
			editableText = self.list[self.selLine][:-1]
			self.session.openWithCallback(self.callbackEditLine, vInputBox, title=_("old:  " + self.list[self.selLine]), windowTitle=_("Edit line " + str(self.selLine + 1)), text=editableText)
		except:
			dei = self.session.open(MessageBox, _("This line is not editable!"), MessageBox.TYPE_ERROR)
			dei.setTitle(_("Error..."))

	def callbackEditLine(self, newline):
		if newline is not None:
			for x in self.list:
				if x == self.oldLine:
					self.isChanged = True
					self.list.remove(x)
					self.list.insert(self.selLine, newline + '\n')
		self.selLine = None
		self.oldLine = None

	def SaveFile(self, answer):
		if answer is True:
			try:
				eFile = open(self.file_name, "w")
				for x in self.list:
					eFile.writelines(x)
				eFile.close()
			except:
				pass
			self.close()
		else:
			self.close()


class MviExplorer(Screen):
	skin = """
		<screen position="-300,-300" size="10,10" title="mvi-Explorer">
		</screen>"""

	def __init__(self, session, file):
		self.skin = MviExplorer.skin
		Screen.__init__(self, session)
		self.file_name = file
		self["actions"] = ActionMap(["WizardActions"],
		{
			"ok": self.close,
			"back": self.close
		}, -1)
		self.onLayoutFinish.append(self.showMvi)

	def showMvi(self):
		os.system("/usr/bin/showiframe " + self.file_name)


class PictureExplorerII(Screen):
	def __init__(self, session, whatPic=None, whatDir=None):
		self.skin = '<screen flags="wfNoBorder" position="0,0" size="' + str(Screen_width) + ',' + str(Screen_height) + '" title="Picture-Explorer" backgroundColor="#00121214"> \
		<widget name="Picture" position="0,0" size="' + str(Screen_width) + ',' + str(Screen_height) + '" zPosition="1" alphatest="on" /> \
		<widget name="State" font="Regular;20" halign="center" position="0,' + str(int(0.904 * 720)) + '" size="' + str(Screen_width) + ',70" backgroundColor="#01080911" foregroundColor="#fcc000" transparent="0" zPosition="9"/> \
		</screen>'
		Screen.__init__(self, session)
		self.session = session
		self.whatPic = whatPic
		self.whatDir = whatDir
		self.picList = []
		self.Pindex = 0
		self.EXpicload = ePicLoad()
		self["Picture"] = Pixmap()
		self["State"] = Label(_('loading... ' + self.whatPic))
		self["actions"] = ActionMap(["WizardActions", "DirectionActions"],
		{
			"ok": self.info,
			"back": self.close,
			"up": self.info,
			"down": self.close,
			"left": self.Pleft,
			"right": self.Pright
		}, -1)
		self.EXpicload.PictureData.get().append(self.DecodeAction)
		self.onLayoutFinish.append(self.Show_Picture)

	def Show_Picture(self):
		if self.whatPic is not None:
			self.EXpicload.setPara([self["Picture"].instance.size().width(), self["Picture"].instance.size().height(), 1, 1, 0, 1, "#002C2C39"])
			self.EXpicload.startDecode(self.whatPic)
		if self.whatDir is not None:
			pidx = 0
			for root, dirs, files in os_walk(self.whatDir):
				for name in files:
					if name.endswith(".jpg") or name.endswith(".jpeg") or name.endswith(".Jpg") or name.endswith(".Jpeg") or name.endswith(".JPG") or name.endswith(".JPEG"):
						self.picList.append(name)
						if name in self.whatPic:
							self.Pindex = pidx
						pidx = pidx + 1
			files.sort()

	def DecodeAction(self, pictureInfo=""):
		if self.whatPic is not None:
			self["State"].setText(_("ready..."))
			self["State"].visible = False
			ptr = self.EXpicload.getData()
			self["Picture"].instance.setPixmap(ptr)

	def Pright(self):
		if len(self.picList) > 2:
			if self.Pindex < (len(self.picList) - 1):
				self.Pindex = self.Pindex + 1
				self.whatPic = self.whatDir + str(self.picList[self.Pindex])
				self["State"].visible = True
				self["State"].setText(_('loading... ' + self.whatPic))
				self.EXpicload.startDecode(self.whatPic)
			else:
				self["State"].setText(_("wait..."))
				self["State"].visible = False
				self.session.open(MessageBox, _('No more picture-files.'), MessageBox.TYPE_INFO)

	def Pleft(self):
		if len(self.picList) > 2:
			if self.Pindex > 0:
				self.Pindex = self.Pindex - 1
				self.whatPic = self.whatDir + str(self.picList[self.Pindex])
				self["State"].visible = True
				self["State"].setText(_('loading... ' + self.whatPic))
				self.EXpicload.startDecode(self.whatPic)
			else:
				self["State"].setText(_("wait..."))
				self["State"].visible = False
				self.session.open(MessageBox, _('No more picture-files.'), MessageBox.TYPE_INFO)

	def info(self):
		if self["State"].visible:
			self["State"].setText(_("wait..."))
			self["State"].visible = False
		else:
			self["State"].visible = True
			self["State"].setText(_(self.whatPic))


class MoviePlayer(MP_parent):
	def __init__(self, session, filename):
		self.moviename = filename
		if self.moviename.endswith(".ts"):
			fileRef = eServiceReference("1:0:0:0:0:0:0:0:0:0:" + self.moviename)
		elif (self.moviename.endswith(".mpg")) or (self.moviename.endswith(".mpeg")) or (self.moviename.endswith(".mkv")) or (self.moviename.endswith(".m2ts")) or (self.moviename.endswith(".vob")) or (self.moviename.endswith(".mod")):
			fileRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + self.moviename)
		elif (self.moviename.endswith(".avi")) or (self.moviename.endswith(".mp4")) or (self.moviename.endswith(".divx")) or (self.moviename.endswith(".mov")) or (self.moviename.endswith(".flv")) or (self.moviename.endswith(".3gp")):
			if not BoxInfo.getItem("model") == "dm7025":
				fileRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + self.moviename)
		self.session = session
		self.WithoutStopClose = False
		MP_parent.__init__(self, self.session, fileRef)
		self.cut_list = []
		self.downloadCuesheet()

	def addLastPosition(self):
		print(("", self, "I"))
		service = self.session.nav.getCurrentService()
		seek = service and service.seek()
		if seek is not None:
			pts = seek.getPlayPosition()[1]

			found = False
			for i in range(len(self.cut_list)):
				if self.cut_list[i][1] == self.CUT_TYPE_LAST:
					self.cut_list[i] = (pts, self.CUT_TYPE_LAST, )
					found = True
					break

			if found is False:
				self.cut_list.append((pts, self.CUT_TYPE_LAST, ))

	def uploadCuesheet(self):
		print(("", self, "I"))
		try:
			import struct
			packed = ''
			for cue in self.cut_list:
				print(cue)
				packed += struct.pack('>QI', cue[0], cue[1])

			if len(packed) > 0:
				f = open(self.moviename + ".cuts", "wb")
				f.write(packed)
				f.close()
			else:
				os.remove(self.moviename + ".cuts")
		except Exception as ex:
			print(("Exception (ef): " + str(ex), self, "E"))

	def downloadCuesheet(self):
		print(("", self, "I"))
		self.cut_list = []
		try:
			import struct
			f = open(self.moviename + ".cuts", "rb")
			packed = f.read()
			f.close()

			while len(packed) > 0:
				packedCue = packed[:12]
				packed = packed[12:]
				cue = struct.unpack('>QI', packedCue)
				self.cut_list.append(cue)
		except Exception as ex:
			print(("Exception (ef): " + str(ex), self, "E"))

	def leavePlayer(self, inst=None):
		self.addLastPosition()
		self.uploadCuesheet()
		self.is_closing = True
		self.close()

	def leavePlayerConfirmed(self, answer):
		pass

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing:
			return
		self.leavePlayer()

	def showMovies(self):
		self.WithoutStopClose = True
		self.close()

	def movieSelected(self, service):
		self.leavePlayer(self.de_instance)

	def __onClose(self):
		if not (self.WithoutStopClose):
			self.session.nav.playService(self.lastservice)


class MoviePlayer_4_MusicExploret(MP_parent):
	def __init__(self, session, service):
		self.session = session
		self.WithoutStopClose = False
		MP_parent.__init__(self, self.session, service)

	def leavePlayer(self):
		self.is_closing = True
		self.close()

	def leavePlayerConfirmed(self, answer):
		pass


class MusicExplorer(MoviePlayer_4_MusicExploret):
	skin = """
	<screen backgroundColor="#50070810" flags="wfNoBorder" name="MusicExplorer" position="center,center" size="720,30">
		<widget font="Regular;24" halign="right" position="50,0" render="Label" size="100,30" source="session.CurrentService" transparent="1" valign="center" zPosition="1">
			<convert type="ServicePosition">Remaining</convert>
		</widget>
		<widget font="Regular;24" position="170,0" render="Label" size="650,30" source="session.CurrentService" transparent="1" valign="center" zPosition="1">
			<convert type="ServiceName">Name</convert>
		</widget>
	</screen>"""

	def __init__(self, session, service, MusicDir, theFile):
		self.session = session
		MoviePlayer_4_MusicExploret.__init__(self, session, service)
		self.MusicDir = MusicDir
		self.musicList = []
		self.Mindex = 0
		self.curFile = theFile
		self.searchMusic()
		self.onLayoutFinish.append(self.showMMI)
		MoviePlayer_4_MusicExploret.WithoutStopClose = False

	def showMMI(self):
		try:
			os_system("/usr/bin/showiframe /usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/music.mvi")
			#TODO DAC wlasna
		except:
			pass  # TU DOROBIC WLASNA TAPETE

	def searchMusic(self):
		midx = 0
		for root, dirs, files in os_walk(self.MusicDir):
			for name in files:
				name = name.lower()
				if name.endswith(".mp3") or name.endswith(".mp2") or name.endswith(".ogg") or name.endswith(".wav") or name.endswith(".flac") or name.endswith(".m4a"):
					self.musicList.append(name)
					if self.curFile in name:
						self.Mindex = midx
					midx = midx + 1

	def seekFwd(self):
		if len(self.musicList) > 2:
			if self.Mindex < (len(self.musicList) - 1):
				self.Mindex = self.Mindex + 1
				nextfile = self.MusicDir + str(self.musicList[self.Mindex])
				nextRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + nextfile)
				self.session.nav.playService(nextRef)
			else:
				self.session.open(MessageBox, _('No more playable files.'), MessageBox.TYPE_INFO)

	def seekBack(self):
		if len(self.musicList) > 2:
			if self.Mindex > 0:
				self.Mindex = self.Mindex - 1
				nextfile = self.MusicDir + str(self.musicList[self.Mindex])
				nextRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + nextfile)
				self.session.nav.playService(nextRef)
			else:
				self.session.open(MessageBox, _('No more playable files.'), MessageBox.TYPE_INFO)

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing:
			return
		self.seekFwd()

###########################################################################


def main(session, **kwargs):
	print("\n[SubsDownloaderApplication] start\n")
	session.open(SubsDownloaderApplication)


#########################################################################


def Plugins(**kwargs):
	desc_plugin_menu = PluginDescriptor(name="SubsDownloader", description="Download subtitle to any movie", where=PluginDescriptor.WHERE_PLUGINMENU, icon="subsdownloader.png", fnc=main)
	desc_menu_Blue_button_menu = PluginDescriptor(name="SubsDownloader", description="Download subtitle to any movie", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)
	list = []
	list.append(desc_plugin_menu)
	if config.plugins.subsdownloader.BlueButtonMenu.value is True:
		list.append(desc_menu_Blue_button_menu)
	return list
