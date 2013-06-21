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



from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.InfoBar import MoviePlayer as MP_parent
from Screens.InfoBar import InfoBar
from Screens.Console import Console
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.EventView import EventViewSimple
from Components.ActionMap import ActionMap
from Components.FileList import FileList
from Components.MenuList import MenuList
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap
from Components.AVSwitch import AVSwitch
from Components.config import config, ConfigSubsection, ConfigText
from Tools.Directories import fileExists, pathExists
from Tools.HardwareInfo import HardwareInfo
from ServiceReference import ServiceReference
from myFileList import FileList as myFileList
#from vInputBox import vInputBox
from Screens.InputBox import InputBox
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/PicturePlayer/plugin.pyo") or fileExists("/usr/lib/enigma2/python/Plugins/Extensions/PicturePlayer/plugin.pyc"):
	from Plugins.Extensions.PicturePlayer.plugin import Pic_Thumb, picshow
	PicPlayerAviable = True
else:
	PicPlayerAviable = False
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/plugin.pyo") or fileExists("/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/plugin.pyc"):
	from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
	DVDPlayerAviable = True
else:
	DVDPlayerAviable = False
if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/plugin.pyo") or fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/plugin.pyc"):
	from Plugins.Extensions.MerlinMusicPlayer.plugin import MerlinMusicPlayerScreen, Item
	MMPavaiable = True
else:
	MMPavaiable = False
from enigma import eConsoleAppContainer, eServiceReference, ePicLoad, getDesktop, eServiceCenter
from os import system as os_system
from os import stat as os_stat
from os import walk as os_walk
from os import popen as os_popen
from os import rename as os_rename
from os import mkdir as os_mkdir
from os import path as os_path
from os import listdir as os_listdir
from time import strftime as time_strftime
from time import localtime as time_localtime



config.plugins.DreamExplorer = ConfigSubsection()
config.plugins.DreamExplorer.startDir = ConfigText(default="/")
config.plugins.DreamExplorer.MediaFilter = ConfigText(default="off")
config.plugins.DreamExplorer.CopyDest = ConfigText(default="/")



explSession = None
HDSkn = False
sz_w = getDesktop(0).size().width()
if sz_w > 800:
	HDSkn = True
else:
	HDSkn = False



def Plugins(**kwargs):
	list = [PluginDescriptor(name="Dream-Explorer", description=_("Explore your Dreambox."), where = [PluginDescriptor.WHERE_PLUGINMENU], icon="dreamexplorer.png", fnc=main)]
 	list.append(PluginDescriptor(name=_("Dream-Explorer"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main))
	#list.append(PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART],fnc = autostart))
	return list



def main(session, **kwargs):
	session.open(DreamExplorerII)



def autostart(reason, **kwargs):
	if reason == 0:
		if kwargs.has_key("session"):
			global explSession
			explSession = kwargs["session"]
			InfoBar.showMovies = showExpl

def showExpl(dummy_self = None):
	global explSession
	explSession.open(DreamExplorerII)



######## DREAM-EXPLORER START #######################
class DreamExplorerII(Screen):
	global HDSkn
	if HDSkn:
		if (getDesktop(0).size().width()) > 1030:
			skin = """
				<screen position="center,80" size="1180,590" title="Dream-Explorer">
				<widget name="filelist" position="5,10" scrollbarMode="showOnDemand" size="942,552" zPosition="4"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/red.png" position="995,20" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/green.png" position="995,60" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/yellow.png" position="995,100" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/blue.png" position="995,140" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/menu.png" position="995,180" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/info.png" position="995,220" size="35,25" zPosition="5"/>
				<eLabel font="Regular;18" halign="left" position="1040,20" size="140,25" text="Delete" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="1040,60" size="140,25" text="Rename" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="1040,100" size="140,25" text="Move/Copy" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="1040,140" size="140,25" text="Bookmarks" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="1040,180" size="140,25" text="Options" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="1040,220" size="140,25" text="Info" transparent="1" valign="center" zPosition="6"/>
				</screen>"""
		else:
			skin = """
				<screen position="center,77" size="900,450" title="Dream-Explorer">
				<widget name="filelist" position="5,2" scrollbarMode="showOnDemand" size="890,416" zPosition="4"/>
				<eLabel backgroundColor="#555555" position="5,420" size="890,2" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/red.png" position="0,425" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/green.png" position="155,425" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/yellow.png" position="310,425" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/blue.png" position="465,425" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/menu.png" position="620,425" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/info.png" position="775,425" size="35,25" zPosition="5"/>
				<eLabel font="Regular;18" halign="left" position="35,425" size="120,25" text="Delete" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="190,425" size="120,25" text="Rename" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="345,425" size="120,25" text="Move/Copy" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="500,425" size="120,25" text="Bookmarks" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="655,425" size="120,25" text="Options" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="810,425" size="90,25" text="Info" transparent="1" valign="center" zPosition="6"/>
				</screen>"""
	else:
		skin = """
			<screen position="center,77" size="620,450" title="Dream-Explorer">
			<widget name="filelist" position="5,2" scrollbarMode="showOnDemand" size="610,416" zPosition="4"/>
			<eLabel backgroundColor="#555555" position="5,420" size="610,2" zPosition="5"/>
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/red.png" position="0,425" size="35,25" zPosition="5"/>
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/green.png" position="145,425" size="35,25" zPosition="5"/>
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/yellow.png" position="290,425" size="35,25" zPosition="5"/>
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/blue.png" position="430,425" size="35,25" zPosition="5"/>
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/info.png" position="555,425" size="35,25" zPosition="5"/>
			<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/menu.png" position="585,425" size="35,25" zPosition="5"/>
			<eLabel font="Regular;16" halign="left" position="35,425" size="100,25" text="Delete" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;16" halign="left" position="180,425" size="100,25" text="Rename" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;16" halign="left" position="325,425" size="100,25" text="Move/Copy" transparent="1" valign="center" zPosition="6"/>
			<eLabel font="Regular;16" halign="left" position="465,425" size="100,25" text="Bookmarks" transparent="1" valign="center" zPosition="6"/>
			</screen>"""

	def __init__(self, session, args = None):
		self.skin = DreamExplorerII.skin
		Screen.__init__(self, session)
		self.sesion = session
		self.altservice = self.session.nav.getCurrentlyPlayingServiceReference()
		self.MyBox = HardwareInfo().get_device_name()
		self.commando = [ "ls" ]
		self.selectedDir = "/tmp/"
		self.booklines = []
		self.MediaPattern = "^.*\.(ts|m2ts|mp3|wav|ogg|jpg|jpeg|jpe|png|bmp|mpg|mpeg|mkv|mp4|mov|divx|wmv|avi|mp2|m4a|flac|ifo|vob|iso|sh|flv|3gp|mod)"
		if pathExists(config.plugins.DreamExplorer.startDir.value):
			StartMeOn = config.plugins.DreamExplorer.startDir.value
		else:
			StartMeOn = None
		if (config.plugins.DreamExplorer.MediaFilter.value == "off"):
			self.MediaFilter = False
			self["filelist"] = myFileList(StartMeOn, showDirectories = True, showFiles = True, matchingPattern = None, useServiceRef = False)
		else:
			self.MediaFilter = True
			self["filelist"] = myFileList(StartMeOn, showDirectories = True, showFiles = True, matchingPattern = self.MediaPattern, useServiceRef = False)
		self["TEMPfl"] = FileList("/", matchingPattern = "(?i)^.*\.(jpeg|jpg|jpe|png|bmp)")
		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions", "MenuActions", "EPGSelectActions", "InfobarActions"],
		{
			"ok": self.ok,
			"back": self.explExit,
			"green": self.ExecRename,
			"red": self.ExecDelete,
			"blue": self.goToBookmark,
			"yellow": self.go2CPmaniger,
			"menu": self.explContextMenu,
			"info": self.Info,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
			"nextBouquet": self.sortName,
			"prevBouquet": self.sortDate,
			"showMovies": self.CloseAndPlay
		}, -1)
		self.onLayoutFinish.append(self.byLayoutEnd)

	def ok(self):
		global DVDPlayerAviable
		if self["filelist"].canDescent():
			self["filelist"].descent()
			self.updateLocationInfo()
		else:
			filename = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
			testFileName = self["filelist"].getFilename()
			testFileName = testFileName.lower()
			if filename != None:
				if testFileName.endswith(".ts"):
					fileRef = eServiceReference("1:0:0:0:0:0:0:0:0:0:" + filename)
					self.session.open(MoviePlayer, fileRef)
				elif (testFileName.endswith(".mpg")) or (testFileName.endswith(".mpeg")) or (testFileName.endswith(".mkv")) or (testFileName.endswith(".m2ts")) or (testFileName.endswith(".vob")) or (testFileName.endswith(".mod")):
					fileRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + filename)
					self.session.open(MoviePlayer, fileRef)
				elif (testFileName.endswith(".avi")) or (testFileName.endswith(".mp4")) or (testFileName.endswith(".divx")) or (testFileName.endswith(".wmv")) or (testFileName.endswith(".mov")) or (testFileName.endswith(".flv")) or (testFileName.endswith(".3gp")):
					if not(self.MyBox=="dm7025"):	
						fileRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + filename)
						self.session.open(MoviePlayer, fileRef)
				elif (testFileName.endswith(".mp3")) or (testFileName.endswith(".wav")) or (testFileName.endswith(".ogg")) or (testFileName.endswith(".m4a")) or (testFileName.endswith(".mp2")) or (testFileName.endswith(".flac")):
					if (self.MyBox=="dm7025") and ((testFileName.endswith(".m4a")) or (testFileName.endswith(".mp2")) or (testFileName.endswith(".flac"))):
						return
					if MMPavaiable:
						SongList,SongIndex = self.searchMusic()
						try:
							self.session.open(MerlinMusicPlayerScreen, SongList, SongIndex, False, self.altservice, None)
						except:
							self.session.open(MessageBox, _("Incompatible MerlinMusicPlayer version!"), MessageBox.TYPE_INFO)
					else:
						fileRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + filename)
						m_dir = self["filelist"].getCurrentDirectory()
						self.session.open(MusicExplorer, fileRef, m_dir, testFileName)
				elif (testFileName.endswith(".jpg")) or (testFileName.endswith(".jpeg")) or (testFileName.endswith(".jpe")) or (testFileName.endswith(".png")) or (testFileName.endswith(".bmp")):
					if self["filelist"].getSelectionIndex()!=0:
						Pdir = self["filelist"].getCurrentDirectory()
						self.session.open(PictureExplorerII, filename, Pdir)
				elif (testFileName.endswith(".mvi")):
					self.session.nav.stopService()
					self.session.open(MviExplorer, filename)
				elif (testFileName == "video_ts.ifo"):
					if DVDPlayerAviable:
						if (self["filelist"].getCurrentDirectory()).lower().endswith("video_ts/"):
							self.session.open(DVDPlayer, dvd_filelist=[self["filelist"].getCurrentDirectory()])
				elif testFileName.endswith(".iso"):
					if DVDPlayerAviable:
						self.session.open(DVDPlayer, dvd_filelist=[filename])
				elif testFileName.endswith(".bootlogo.tar.gz"):
					self.commando = ["mount -rw /boot -o remount", "sleep 3","tar -xzvf " + filename + " -C /", "mount -ro /boot -o remount"]
					askList = [(_("Cancel"), "NO"),(_("Install new bootlogo..."), "YES2ALL")]
					dei = self.session.openWithCallback(self.SysExecution, ChoiceBox, title=_("Bootlogo-package:\\n"+filename), list=askList)
					dei.setTitle(_("Dream-Explorer : Install..."))
				elif testFileName.endswith(".tar.gz"):
					self.commando = [ "tar -xzvf " + filename + " -C /" ]
					askList = [(_("Cancel"), "NO"),(_("Install this package"), "YES")]
					dei = self.session.openWithCallback(self.SysExecution, ChoiceBox, title=_("GZ-package:\\n"+filename), list=askList)
					dei.setTitle(_("Dream-Explorer : Install..."))
				elif testFileName.endswith(".tar.bz2"):
					self.commando = [ "tar -xjvf " + filename + " -C /" ]
					askList = [(_("Cancel"), "NO"),(_("Install this package"), "YES")]
					dei = self.session.openWithCallback(self.SysExecution, ChoiceBox, title=_("BZ2-package:\\n"+filename), list=askList)
					dei.setTitle(_("Dream-Explorer : Install..."))
				elif testFileName.endswith(".ipk"):
					if fileExists("/usr/bin/opkg"):
						self.commando = [ "opkg install " + filename ]
					else:
						self.commando = [ "ipkg install " + filename ]
					askList = [(_("Cancel"), "NO"),(_("Install this package"), "YES")]
					dei = self.session.openWithCallback(self.SysExecution, ChoiceBox, title=_("IPKG-package:\\n"+filename), list=askList)
					dei.setTitle(_("Dream-Explorer : Install..."))
				elif testFileName.endswith(".pyc") or testFileName.endswith(".pyo"):
					self.commando = [ "/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/pyc2xml " + filename ]
					askList = [(_("Cancel"), "NO"),(_("Disassemble to bytecode..."), "YES")]
					dei = self.session.openWithCallback(self.SysExecution, ChoiceBox, title=_("Pyc-Script:\\n"+filename), list=askList)
					dei.setTitle(_("Dream-Explorer : Disassemble..."))
				elif testFileName.endswith(".sh"):
					self.commando = [ filename ]
					askList = [(_("Cancel"), "NO"),(_("View this shell-script"), "VIEW"),(_("Start execution"), "YES")]
					self.session.openWithCallback(self.SysExecution, ChoiceBox, title=_("Do you want to execute?\\n"+filename), list=askList)
				else:
					xfile=os_stat(filename)
					if (xfile.st_size < 61440):
						self.session.open(vEditor, filename)

	def byLayoutEnd(self):
		self.updateLocationInfo()
		if fileExists("/etc/myBookmarks"):
			try:
				booklist = open("/etc/myBookmarks", "r")
			except:
				dei = self.session.open(MessageBox, _("Error by reading bookmarks !!!"), MessageBox.TYPE_ERROR)
				dei.setTitle(_("Dream-Explorer"))
			if booklist is not None:
				for oneline in booklist:
					self.booklines.append(oneline)
				booklist.close()

	def updateLocationInfo(self):
		try:
			if self.MediaFilter:
				self.setTitle(_("[Media files] " + self["filelist"].getCurrentDirectory()))
			else:
				self.setTitle(_("[All files] " + self["filelist"].getCurrentDirectory()))	
		except:
			self.setTitle(_("Dream-Explorer"))

	def explContextMenu(self):
		if self.MediaFilter:
			mftext="Disable"
		else:
			mftext="Enable"
		if self["filelist"].canDescent():
			if self["filelist"].getSelectionIndex()!=0:
				self.selectedDir = self["filelist"].getSelection()[0]
				if self.selectedDir + "\n" in self.booklines:
					BMtext = "Remove directory from Bookmarks"
					BMstring = "DELLINK"
				else:
					BMtext = "Add directory to Bookmarks"
					BMstring = "ADDLINK"
				contextDirList = [(_("Cancel"), "NO"),
						(_(mftext + " Media-filter"), "FILTER"),
						(_("Sort by name (bouquet+)"), "SORTNAME"),
						(_("Sort by date (bouquet-)"), "SORTDATE"),
						(_(BMtext), BMstring),
						(_("Create new file"), "NEWFILE"),
						(_("Create new directory"), "NEWDIR"),
						(_("Set start directory"), "SETSTARTDIR"),
						(_("About"), "HELP")]
				dei = self.session.openWithCallback(self.SysExecution, ChoiceBox, title=_("Options:\n"), list=contextDirList)
				dei.setTitle(_("Dream-Explorer"))
			else:
				contextFileList = [(_("Cancel"), "NO"),
						(_(mftext + " Media-filter"), "FILTER"),
						(_("Sort by name (bouquet+)"), "SORTNAME"),
						(_("Sort by date (bouquet-)"), "SORTDATE"),
						(_("Pack my bootlogo"), "PACKLOGOS"),
						(_("About"), "HELP")]
				dei = self.session.openWithCallback(self.SysExecution, ChoiceBox, title=_("Options:\n"), list=contextFileList)
				dei.setTitle(_("Dream-Explorer"))
		else:
			contextFileList = [(_("Cancel"), "NO"),
						(_(mftext + " Media-filter"), "FILTER"),
						(_("Sort by name (bouquet+)"), "SORTNAME"),
						(_("Sort by date (bouquet-)"), "SORTDATE"),
						(_("Preview all pictures"), "PLAYDIRPICTURE"),
						(_("Create new file"), "NEWFILE"),
						(_("Create new directory"), "NEWDIR"),
						(_("Create softlink..."), "SOFTLINK"),
						(_("Set archive mode (644)"), "CHMOD644"),
						(_("Set executable mode (755)"), "CHMOD755"),
						(_("About"), "HELP")]
			dei = self.session.openWithCallback(self.SysExecution, ChoiceBox, title=_("Options:\n"), list=contextFileList)
			dei.setTitle(_("Dream-Explorer"))

	def SysExecution(self, answer):
		global PicPlayerAviable
		answer = answer and answer[1]
		if answer == "YES":
			self.session.open(Console, cmdlist = [ self.commando[0] ])
		elif answer == "YES2ALL":
			self.session.open(Console, cmdlist = self.commando)
		elif answer == "PACKLOGOS":
			self.session.open(Console, cmdlist = ["cd /tmp/", "tar -czf /tmp/dreambox.bootlogo.tar.gz /usr/share/bootlogo.mvi /usr/share/bootlogo_wait.mvi /usr/share/backdrop.mvi /boot/bootlogo.jpg"])
		elif answer == "VIEW":
			yfile=os_stat(self.commando[0])
			if (yfile.st_size < 61440):
				self.session.open(vEditor, self.commando[0])
		elif answer == "PLAYDIRPICTURE":
			if PicPlayerAviable:
				self["TEMPfl"].changeDir(self["filelist"].getCurrentDirectory())
				self.session.open(Pic_Thumb, self["TEMPfl"].getFileList(), 0, self["filelist"].getCurrentDirectory())
			else:
				dei = self.session.open(MessageBox, _("Picture-Player not aviable."), MessageBox.TYPE_ERROR)
				dei.setTitle(_("Dream-Explorer"))
		elif answer == "ADDLINK":
			try:
				newbooklist = open("/etc/myBookmarks", "w")
			except:
				dei = self.session.open(MessageBox, _("Error by writing bookmarks !!!"), MessageBox.TYPE_ERROR)
				dei.setTitle(_("Dream-Explorer"))
			if newbooklist is not None:
				self.booklines.append(self.selectedDir+"\n")
				for one_line in self.booklines:
					newbooklist.write(one_line)
				newbooklist.close()
		elif answer == "DELLINK":
			temp_book = []
			for bidx in range(len(self.booklines)-1):
				if not(self.selectedDir in self.booklines[bidx]):
					temp_book.append(self.booklines[bidx])
			self.booklines = []
			self.booklines = temp_book
			try:
				newbooklist = open("/etc/myBookmarks", "w")
			except:
				dei = self.session.open(MessageBox, _("Error by writing bookmarks !!!"), MessageBox.TYPE_ERROR)
				dei.setTitle(_("Dream-Explorer"))
			if newbooklist is not None:
				for one_line in self.booklines:
					newbooklist.write(one_line)
				newbooklist.close()
		elif answer == "FILTER":
			if self.MediaFilter:
				self.MediaFilter=False
				config.plugins.DreamExplorer.MediaFilter.value = "off"
				config.plugins.DreamExplorer.MediaFilter.save()
				self["filelist"].matchingPattern = None
				self["filelist"].refresh()
				self.updateLocationInfo()
			else:
				self.MediaFilter=True
				config.plugins.DreamExplorer.MediaFilter.value = "on"
				config.plugins.DreamExplorer.MediaFilter.save()
				self["filelist"].matchingPattern = self.MediaPattern
				self["filelist"].refresh()
				self.updateLocationInfo()
		elif answer == "NEWFILE":
			self.session.openWithCallback(self.callbackNewFile, vInputBox, title=_(self["filelist"].getCurrentDirectory()), windowTitle=_("Create new file in..."), text="name")
		elif answer == "NEWDIR":
			self.session.openWithCallback(self.callbackNewDir, vInputBox, title=_(self["filelist"].getCurrentDirectory()), windowTitle=_("Create new directory in..."), text="name")
		elif answer == "SETSTARTDIR":
			newStartDir = self["filelist"].getSelection()[0]
			dei = self.session.openWithCallback(self.callbackSetStartDir,MessageBox,_("Do you want to set\n"+newStartDir+"\nas start directory?"), MessageBox.TYPE_YESNO)
			dei.setTitle(_("Dream-Explorer..."))
		elif answer == "SORTNAME":
			list = self.sortName()
		elif answer == "SORTDATE":
			list = self.sortDate()
		elif answer == "HELP":
			hilfe = "Dreambox-Explorer\ncoded 2010 by Vali\n\nSupport & Help on\nwww.dreambox-tools.info"
			dei = self.session.open(MessageBox, _(hilfe), MessageBox.TYPE_INFO)
			dei.setTitle(_("Info..."))
		elif answer == "SOFTLINK":
			if not(self.MediaFilter):
				self.session.openWithCallback(self.callbackCPmaniger, SoftLinkScreen, self["filelist"].getCurrentDirectory())
		elif answer == "CHMOD644":
			os_system("chmod 644 " + self["filelist"].getCurrentDirectory() + self["filelist"].getFilename())
		elif answer == "CHMOD755":
			os_system("chmod 755 " + self["filelist"].getCurrentDirectory() + self["filelist"].getFilename())

	def up(self):
		self["filelist"].up()
		self.updateLocationInfo()

	def down(self):
		self["filelist"].down()
		self.updateLocationInfo()

	def left(self):
		self["filelist"].pageUp()
		self.updateLocationInfo()

	def right(self):
		self["filelist"].pageDown()
		self.updateLocationInfo()

	def Humanizer(self, size):
		if (size < 1024):
			humansize = str(size)+" B"
		elif (size < 1048576):
			humansize = str(size/1024)+" KB"
		else:
			humansize = str(size/1048576)+" MB"
		return humansize

	def Info(self):
		if self["filelist"].canDescent():
			if self["filelist"].getSelectionIndex()!=0:
				curSelDir = self["filelist"].getSelection()[0]
				dir_stats = os_stat(curSelDir)
				dir_infos = "size "+str(self.Humanizer(dir_stats.st_size))+"    "
				dir_infos = dir_infos+"last-mod "+time_strftime("%d.%m.%Y %H:%M:%S",time_localtime(dir_stats.st_mtime))+"    "
				dir_infos = dir_infos+"mode "+str(dir_stats.st_mode)
				self.setTitle(_(dir_infos))
			else:
				dei = self.session.open(MessageBox, _("Dreambox: " + self.MyBox + "\n\n" + ScanSysem_str()), MessageBox.TYPE_INFO)
				dei.setTitle(_("Dream-Explorer"))
		else:
			curSelFile = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
			file_stats = os_stat(curSelFile)
			file_infos = "size "+str(self.Humanizer(file_stats.st_size))+"    "
			file_infos = file_infos+"last-mod "+time_strftime("%d.%m.%Y %H:%M:%S",time_localtime(file_stats.st_mtime))+"    "
			file_infos = file_infos+"mode "+str(file_stats.st_mode)
			self.setTitle(_(file_infos))
			if curSelFile.endswith(".ts"):
				serviceref = eServiceReference("1:0:0:0:0:0:0:0:0:0:" + curSelFile)
				serviceHandler = eServiceCenter.getInstance()
				info = serviceHandler.info(serviceref)
				evt = info.getEvent(serviceref)
				if evt:
					self.session.open(EventViewSimple, evt, ServiceReference(serviceref))

	def setBookmark(self, answer):
		answer = answer and answer[1]
		try:
			if answer[0] == "/":
				self["filelist"].changeDir(answer[:-1])
				self.updateLocationInfo()
		except:
			pass

	def goToBookmark(self):
		bml = [(_("Cancel"), "BACK")]
		for onemark in self.booklines:
			bml.append((_(onemark), onemark))
		dei = self.session.openWithCallback(self.setBookmark, ChoiceBox, title=_("My Bookmarks"), list=bml)
		dei.setTitle(_("Dream-Explorer"))

	def ExecDelete(self):
		if self.MediaFilter:
			dei = self.session.open(MessageBox,_('Turn off the media-filter first.'), MessageBox.TYPE_INFO)
			dei.setTitle(_("Dream-Explorer..."))
			return
		if not(self["filelist"].canDescent()):
			DELfilename = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
			dei = self.session.openWithCallback(self.callbackExecDelete,MessageBox,_("Do you realy want to DELETE:\n"+DELfilename), MessageBox.TYPE_YESNO)
			dei.setTitle(_("Dream-Explorer - DELETE file..."))
		elif (self["filelist"].getSelectionIndex()!=0) and (self["filelist"].canDescent()):
			DELDIR = self["filelist"].getSelection()[0]
			dei = self.session.openWithCallback(self.callbackDelDir,MessageBox,_("Do you realy want to DELETE:\n"+DELDIR+'\n\nYou do it at your own risk!'), MessageBox.TYPE_YESNO)
			dei.setTitle(_("Dream-Explorer - DELETE DIRECTORY..."))

	def callbackExecDelete(self, answer):
		if answer is True:
			DELfilename = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
			order = 'rm -f \"' + DELfilename + '\"'
			try:
				os_system(order)
				self["filelist"].refresh()
			except:
				dei = self.session.open(MessageBox,_("%s \nFAILED!" % order), MessageBox.TYPE_ERROR)
				dei.setTitle(_("Dream-Explorer"))
				self["filelist"].refresh()

	def callbackDelDir(self, answer):
		if answer is True:
			DELDIR = self["filelist"].getSelection()[0]
			order = 'rm -r \"' + DELDIR + '\"'
			try:
				os_system(order)
				self["filelist"].refresh()
			except:
				dei = self.session.open(MessageBox,_("%s \nFAILED!" % order), MessageBox.TYPE_ERROR)
				dei.setTitle(_("Dream-Explorer"))
				self["filelist"].refresh()

	def ExecRename(self):
		if self.MediaFilter:
			dei = self.session.open(MessageBox,_('Turn off the media-filter first.'), MessageBox.TYPE_INFO)
			dei.setTitle(_("Dream-Explorer..."))
			return
		if not(self["filelist"].canDescent()):
			RENfilename = self["filelist"].getFilename()
			self.session.openWithCallback(self.callbackExecRename, vInputBox, title=_("old:  "+RENfilename), windowTitle=_("Rename file..."), text=RENfilename)
		elif (self["filelist"].getSelectionIndex()!=0) and (self["filelist"].canDescent()):
			RENDIR = self["filelist"].getSelection()[0]
			self.session.openWithCallback(self.callbackRenDir, vInputBox, title=_("old:  "+RENDIR), windowTitle=_("Rename directory..."), text=RENDIR)

	def callbackExecRename(self, answer):
		if answer is not None:
			source = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
			dest = self["filelist"].getCurrentDirectory() + answer
			try:
				os_rename(source, dest)
				self["filelist"].refresh()
			except:
				dei = self.session.open(MessageBox,_("Rename: %s \nFAILED!" % answer), MessageBox.TYPE_ERROR)
				dei.setTitle(_("Dream-Explorer"))
				self["filelist"].refresh()

	def callbackRenDir(self, answer):
		if answer is not None:
			source = self["filelist"].getSelection()[0]
			dest = answer
			try:
				os_rename(source, dest)
				self["filelist"].refresh()
			except:
				dei = self.session.open(MessageBox,_("Rename: %s \nFAILED!" % answer), MessageBox.TYPE_ERROR)
				dei.setTitle(_("Dream-Explorer"))
				self["filelist"].refresh()

	def callbackNewFile(self, answer):
		if answer is None:
			return
		dest = self["filelist"].getCurrentDirectory()
		if (" " in answer) or (" " in dest) or (answer==""):
			dei = self.session.open(MessageBox,_("File name error !"), MessageBox.TYPE_ERROR)
			dei.setTitle(_("Dream-Explorer"))
			return
		else:
			order = 'touch ' + dest + answer
			try:
				if not fileExists(dest + answer):
					os_system(order)
				self["filelist"].refresh()
			except:
				dei = self.session.open(MessageBox,_("%s \nFAILED!" % order), MessageBox.TYPE_ERROR)
				dei.setTitle(_("Dream-Explorer"))
				self["filelist"].refresh()

	def callbackNewDir(self, answer):
		if answer is None:
			return
		dest = self["filelist"].getCurrentDirectory()
		if (" " in answer) or (" " in dest) or (answer==""):
			dei = self.session.open(MessageBox,_("Directory name error !"), MessageBox.TYPE_ERROR)
			dei.setTitle(_("Dream-Explorer"))
			return
		else:
			order = dest + answer
			try:
				if not pathExists(dest + answer):
					os_mkdir(order)
				self["filelist"].refresh()
			except:
				dei = self.session.open(MessageBox,_("%s \nFAILED!" % order), MessageBox.TYPE_ERROR)
				dei.setTitle(_("Dream-Explorer"))
				self["filelist"].refresh()

	def go2CPmaniger(self):
		if self.MediaFilter:
			dei = self.session.open(MessageBox,_('Turn off the media-filter first.'), MessageBox.TYPE_INFO)
			dei.setTitle(_("Dream-Explorer..."))
			return
		if not(self["filelist"].canDescent()):
			source = self["filelist"].getCurrentDirectory() + self["filelist"].getFilename()
			self.session.openWithCallback(self.callbackCPmaniger, CPmaniger, source)
		elif (self["filelist"].getSelectionIndex()!=0) and (self["filelist"].canDescent()): #NEW
			source = self["filelist"].getSelection()[0]
			self.session.openWithCallback(self.callbackCPmaniger, CPmaniger, source)

	def callbackCPmaniger(self, answer):
		self["filelist"].refresh()

	def callbackSetStartDir(self, answerSD):
		if answerSD is True:
			config.plugins.DreamExplorer.startDir.value = self["filelist"].getSelection()[0]
			config.plugins.DreamExplorer.startDir.save()

	def sortName(self):
		list = self["filelist"].sortName()
		try:
			if self.MediaFilter:
				self.setTitle(_("[sort by Name] " + self["filelist"].getCurrentDirectory()))
			else:
				self.setTitle(_("[sort by Name] " + self["filelist"].getCurrentDirectory()))	
		except:
			self.setTitle(_("Dream-Explorer"))

	def sortDate(self):
		list = self["filelist"].sortDate()
		try:
			if self.MediaFilter:
				self.setTitle(_("[sort by Date] " + self["filelist"].getCurrentDirectory()))
			else:
				self.setTitle(_("[sort by Date] " + self["filelist"].getCurrentDirectory()))	
		except:
			self.setTitle(_("Dream-Explorer"))

	def searchMusic(self):
		slist = []
		foundIndex = 0
		index = 0
		files = os_listdir(self["filelist"].getCurrentDirectory())
		files.sort()
		for name in files:
			testname = name.lower()
			if testname.endswith(".mp3") or name.endswith(".m4a") or name.endswith(".ogg") or name.endswith(".flac"):
				slist.append((Item(text = name, filename = os_path.join(self["filelist"].getCurrentDirectory(),name)),))
				if self["filelist"].getFilename() == name:
					foundIndex = index
				index = index + 1
		return slist,foundIndex

	def explExit(self):
		self.session.nav.playService(self.altservice)
		try:
			if self.MediaFilter:
				config.plugins.DreamExplorer.MediaFilter.value = "on"
			else:
				config.plugins.DreamExplorer.MediaFilter.value = "off"
			config.plugins.DreamExplorer.MediaFilter.save()
		except:
			pass
		self.close()

	def CloseAndPlay(self):
		try:
			if self.MediaFilter:
				config.plugins.DreamExplorer.MediaFilter.value = "on"
			else:
				config.plugins.DreamExplorer.MediaFilter.value = "off"
			config.plugins.DreamExplorer.MediaFilter.save()
		except:
			pass
		self.close()

######## DREAM-EXPLORER END ####################### 



class vEditor(Screen):
	global HDSkn
	if HDSkn:
		if (getDesktop(0).size().width()) > 1030:
			skin = """
			<screen position="50,80" size="1180,590" title="File-Explorer">
				<widget name="filedata" position="5,7" size="1170,575" itemHeight="25"/>
			</screen>"""
		else:
			skin = """
			<screen position="center,77" size="900,450" title="File-Explorer">
				<widget name="filedata" position="2,0" size="896,450" itemHeight="25"/>
			</screen>"""
	else:
		skin = """
		<screen position="center,77" size="620,450" title="File-Explorer">
			<widget name="filedata" position="0,0" size="620,450" itemHeight="25"/>
		</screen>"""

	def __init__(self, session, file):
		self.skin = vEditor.skin
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
			dei = self.session.openWithCallback(self.SaveFile, MessageBox,_(self.file_name+warningtext), MessageBox.TYPE_YESNO)
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
			self.session.openWithCallback(self.callbackEditLine, vInputBox, title=_("old:  "+self.list[self.selLine]), windowTitle=_("Edit line "+str(self.selLine+1)), text=editableText)
		except:
			dei = self.session.open(MessageBox, _("This line is not editable!"), MessageBox.TYPE_ERROR)
			dei.setTitle(_("Error..."))

	def callbackEditLine(self, newline):
		if newline is not None:
			for x in self.list:
				if x == self.oldLine:
					self.isChanged = True
					self.list.remove(x)
					self.list.insert(self.selLine, newline+'\n')
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
		os_system("/usr/bin/showiframe " + self.file_name)



class PictureExplorerII(Screen):
	global HDSkn
	if HDSkn:
		if (getDesktop(0).size().width()) > 1030:
			skin="""
				<screen flags="wfNoBorder" position="0,0" size="1280,720" title="Picture-Explorer" backgroundColor="#00121214">
					<widget name="Picture" position="0,0" size="1280,720" zPosition="1" alphatest="on" />
					<widget name="State" font="Regular;20" halign="center" position="0,650" size="1280,70" backgroundColor="#01080911" foregroundColor="#fcc000" transparent="0" zPosition="9"/>
				</screen>"""
		else:
			skin = """
				<screen backgroundColor="#101214" flags="wfNoBorder" position="0,0" size="1024,576" title="Picture-Explorer">
					<widget alphatest="on" backgroundColor="#00141415" name="Picture" position="0,0" size="1024,576" zPosition="1"/>
					<widget name="State" font="Regular;20" halign="center" position="0,506" size="1024,70" backgroundColor="#01080911" foregroundColor="#fcc000" transparent="0" zPosition="9"/>
				</screen>"""
	else:
		skin="""
			<screen flags="wfNoBorder" position="0,0" size="720,576" title="Picture-Explorer" backgroundColor="#00121214">
				<widget name="Picture" position="0,0" size="720,576" zPosition="1" alphatest="on" />
				<widget name="State" font="Regular;20" halign="center" position="0,506" size="720,70" backgroundColor="#01080911" foregroundColor="#fcc000" transparent="0" zPosition="9"/>
			</screen>"""

	def __init__(self, session, whatPic = None, whatDir = None):
		self.skin = PictureExplorerII.skin
		Screen.__init__(self, session)
		self.session = session
		self.whatPic = whatPic
		self.whatDir = whatDir
		self.picList = []
		self.Pindex = 0
		self.EXscale = (AVSwitch().getFramebufferScale())
		self.EXpicload = ePicLoad()
		self["Picture"] = Pixmap()
		self["State"] = Label(_('loading... '+self.whatPic))
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
			self.EXpicload.setPara([self["Picture"].instance.size().width(), self["Picture"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#002C2C39"])
			self.EXpicload.startDecode(self.whatPic)
		if self.whatDir is not None:
			pidx = 0
			for root, dirs, files in os_walk(self.whatDir ):
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
		if len(self.picList)>2:
			if self.Pindex<(len(self.picList)-1):
				self.Pindex = self.Pindex + 1
				self.whatPic = self.whatDir + str(self.picList[self.Pindex])
				self["State"].visible = True
				self["State"].setText(_('loading... '+self.whatPic))
				self.EXpicload.startDecode(self.whatPic)
			else:
				self["State"].setText(_("wait..."))
				self["State"].visible = False
				self.session.open(MessageBox,_('No more picture-files.'), MessageBox.TYPE_INFO)

	def Pleft(self):
		if len(self.picList)>2:
			if self.Pindex>0:
				self.Pindex = self.Pindex - 1
				self.whatPic = self.whatDir + str(self.picList[self.Pindex])
				self["State"].visible = True
				self["State"].setText(_('loading... '+self.whatPic))
				self.EXpicload.startDecode(self.whatPic)
			else:
				self["State"].setText(_("wait..."))
				self["State"].visible = False
				self.session.open(MessageBox,_('No more picture-files.'), MessageBox.TYPE_INFO)

	def info(self):
		if self["State"].visible:
			self["State"].setText(_("wait..."))
			self["State"].visible = False
		else:
			self["State"].visible = True
			self["State"].setText(_(self.whatPic))



class MoviePlayer(MP_parent):
	def __init__(self, session, service):
		self.session = session
		self.WithoutStopClose = False
		MP_parent.__init__(self, self.session, service)

	def leavePlayer(self):
		self.is_closing = True
		self.close()

	def leavePlayerConfirmed(self, answer):
		pass

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing :
			return
		self.leavePlayer()

	def showMovies(self):
		self.WithoutStopClose = True
		self.close()

	def movieSelected(self, service):
		self.leavePlayer(self.de_instance)

	def __onClose(self):
		if not(self.WithoutStopClose):
			self.session.nav.playService(self.lastservice)



class MusicExplorer(MoviePlayer):
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
		MoviePlayer.__init__(self, session, service)
		self.MusicDir = MusicDir
		self.musicList = []
		self.Mindex = 0
		self.curFile = theFile
		self.searchMusic()
		self.onLayoutFinish.append(self.showMMI)
		MoviePlayer.WithoutStopClose = False

	def showMMI(self):
		os_system("/usr/bin/showiframe /usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/music.mvi")

	def searchMusic(self):
		midx = 0
		for root, dirs, files in os_walk(self.MusicDir ):
			for name in files:
				name = name.lower()
				if name.endswith(".mp3") or name.endswith(".mp2") or name.endswith(".ogg") or name.endswith(".wav") or name.endswith(".flac") or name.endswith(".m4a"):
					self.musicList.append(name)
					if self.curFile in name:
						self.Mindex = midx
					midx = midx + 1

	def seekFwd(self):
		if len(self.musicList)>2:
			if self.Mindex<(len(self.musicList)-1):
				self.Mindex = self.Mindex + 1
				nextfile = self.MusicDir + str(self.musicList[self.Mindex])
				nextRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + nextfile)
				self.session.nav.playService(nextRef)
			else:
				self.session.open(MessageBox,_('No more playable files.'), MessageBox.TYPE_INFO)

	def seekBack(self):
		if len(self.musicList)>2:
			if self.Mindex>0:
				self.Mindex = self.Mindex - 1
				nextfile = self.MusicDir + str(self.musicList[self.Mindex])
				nextRef = eServiceReference("4097:0:0:0:0:0:0:0:0:0:" + nextfile)
				self.session.nav.playService(nextRef)
			else:
				self.session.open(MessageBox,_('No more playable files.'), MessageBox.TYPE_INFO)

	def doEofInternal(self, playing):
		if not self.execing:
			return
		if not playing :
			return
		self.seekFwd()



def ScanSysem_str():
	try:
		ret = ""
		out_line = os_popen("uptime").readline()
		ret = ret  + "at" + out_line + "\n"
		out_lines = []
		out_lines = os_popen("cat /proc/meminfo").readlines()
		for lidx in range(len(out_lines)-1):
			tstLine = out_lines[lidx].split()
			if "MemTotal:" in tstLine:
				ret = ret + out_lines[lidx]
			elif "MemFree:" in tstLine:
				ret = ret + out_lines[lidx] + "\n"
		out_lines = []
		out_lines = os_popen("cat /proc/stat").readlines()
		for lidx in range(len(out_lines)-1):
			tstLine = out_lines[lidx].split()
			if "procs_running" in tstLine:
				ret = ret + "Running processes: " + tstLine[1]
		return ret
	except:
		return "N/A"



class vInputBox(InputBox):
	vibnewx = str(getDesktop(0).size().width()-80)
	sknew = '<screen name="vInputBox" position="center,center" size="'+vibnewx+',70" title="Input...">\n'
	sknew = sknew + '<widget name="text" position="5,5" size="1270,25" font="Regular;15"/>\n<widget name="input" position="0,40" size="'
	sknew = sknew + vibnewx + ',30" font="Regular;20"/>\n</screen>'
	skin = sknew
	def __init__(self, session, title = "", windowTitle = _("Input"), useableChars = None, **kwargs):
		InputBox.__init__(self, session, title, windowTitle, useableChars, **kwargs)



class CPmaniger(Screen):
	global HDSkn
	if HDSkn:
		if (getDesktop(0).size().width()) > 1030:
			skin = """
				<screen position="center,center" size="900,450" title="Select Copy/Move location...">
				<widget name="File" font="Regular;20" halign="center" position="5,0" size="890,100" transparent="1" valign="center" zPosition="4"/>
				<widget name="CPto" position="5,100" scrollbarMode="showOnDemand" size="890,312" zPosition="4"/>
				<eLabel backgroundColor="#555555" position="5,420" size="890,2" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/red.png" position="0,425" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/yellow.png" position="310,425" size="35,25" zPosition="5"/>
				<eLabel font="Regular;18" halign="left" position="35,425" size="120,25" text="MOVE" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="345,425" size="120,25" text="COPY" transparent="1" valign="center" zPosition="6"/>
				</screen>"""
		else:
			skin = """
				<screen position="center,77" size="900,450" title="Select Copy/Move location...">
				<widget name="File" font="Regular;20" halign="center" position="5,0" size="890,100" transparent="1" valign="center" zPosition="4"/>
				<widget name="CPto" position="5,100" scrollbarMode="showOnDemand" size="890,312" zPosition="4"/>
				<eLabel backgroundColor="#555555" position="5,420" size="890,2" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/red.png" position="0,425" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/yellow.png" position="310,425" size="35,25" zPosition="5"/>
				<eLabel font="Regular;18" halign="left" position="35,425" size="120,25" text="MOVE" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="345,425" size="120,25" text="COPY" transparent="1" valign="center" zPosition="6"/>
				</screen>"""
	else:
		skin = """
			<screen position="center,77" size="620,450" title="Select Copy/Move location...">
				<widget name="File" font="Regular;20" halign="center" position="5,0" size="610,100" transparent="1" valign="center" zPosition="4"/>
				<widget name="CPto" position="5,100" scrollbarMode="showOnDemand" size="610,312" zPosition="4"/>
				<eLabel backgroundColor="#555555" position="5,420" size="610,2" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/red.png" position="0,425" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/yellow.png" position="310,425" size="35,25" zPosition="5"/>
				<eLabel font="Regular;18" halign="left" position="35,425" size="120,25" text="MOVE" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="345,425" size="120,25" text="COPY" transparent="1" valign="center" zPosition="6"/>
			</screen>"""

	def __init__(self, session, source = "/tmp/none"):
		self.skin = CPmaniger.skin
		Screen.__init__(self, session)
		self.sesion = session
		self.src = source
		self["File"] = Label(_("WARNING! they doing now COPY or MOVE\n" + source + "\nto:"))
		self["CPto"] = myFileList(config.plugins.DreamExplorer.CopyDest.value, showDirectories = True, showFiles = False, matchingPattern = "^.*\.*", useServiceRef = False)
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"ok": self.ok,
			"back": self.NothingToDo,
			"red": self.MoveFile,
			"yellow": self.CopyFile
		}, -1)
		self.onLayoutFinish.append(self.OneDescent)

	def OneDescent(self):
		if self["CPto"].canDescent():
			self["CPto"].descent()
	
	def ok(self):
		if self["CPto"].canDescent():
			self["CPto"].descent()

	def NothingToDo(self):
		self.close(" ")

	def CopyFile(self):
		if self["CPto"].getSelectionIndex()!=0:
			dest = self["CPto"].getSelection()[0]
			if self.src[len(self.src)-1] == '/':
				order = 'cp -af \"' + self.src + '\" \"' + dest + '\"'
			else:
				order = 'cp \"' + self.src + '\" \"' + dest + '\"'
			try:
				config.plugins.DreamExplorer.CopyDest.value = dest
				config.plugins.DreamExplorer.CopyDest.save()
				os_system(order)
			except:
				dei = self.session.open(MessageBox,_("%s \nFAILED!" % order), MessageBox.TYPE_ERROR)
				dei.setTitle(_("Dream-Explorer"))
			self.close(" ")

	def MoveFile(self):
		if self["CPto"].getSelectionIndex()!=0:
			dest = self["CPto"].getSelection()[0]
			if self.src[len(self.src)-1] == '/':
				order = 'cp -af \"' + self.src + '\" \"' + dest + '\"'
				DELorder = 'rm -r \"' + self.src + '\"'
			else:
				order = 'cp \"' + self.src + '\" \"' + dest + '\"'
				DELorder = 'rm -f \"' + self.src + '\"'
			try:
				config.plugins.DreamExplorer.CopyDest.value = dest
				config.plugins.DreamExplorer.CopyDest.save()
				os_system(order)
			except:
				dei = self.session.open(MessageBox,_("%s \nFAILED!" % order), MessageBox.TYPE_ERROR)
				dei.setTitle(_("Dream-Explorer"))
			try:
				os_system(DELorder)
			except:
				dei = self.session.open(MessageBox,_("%s \nFAILED!" % DELorder), MessageBox.TYPE_ERROR)
				dei.setTitle(_("Dream-Explorer"))
			self.close(" ")


class SoftLinkScreen(Screen):
	global HDSkn
	if HDSkn:
		if (getDesktop(0).size().width()) > 1030:
			skin = """
				<screen position="center,center" size="900,450" title="Make a softlink...">
				<widget name="File" font="Regular;20" halign="center" position="5,0" size="890,100" transparent="1" valign="center" zPosition="4"/>
				<widget name="SLto" position="5,100" scrollbarMode="showOnDemand" size="890,312" zPosition="4"/>
				<eLabel backgroundColor="#555555" position="5,420" size="890,2" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/red.png" position="0,425" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/yellow.png" position="310,425" size="35,25" zPosition="5"/>
				<eLabel font="Regular;18" halign="left" position="35,425" size="120,25" text="Set name" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="345,425" size="220,25" text="Make a softlink" transparent="1" valign="center" zPosition="6"/>
				</screen>"""
		else:
			skin = """
				<screen position="center,77" size="900,450" title="Make a softlink...">
				<widget name="File" font="Regular;20" halign="center" position="5,0" size="890,100" transparent="1" valign="center" zPosition="4"/>
				<widget name="SLto" position="5,100" scrollbarMode="showOnDemand" size="890,312" zPosition="4"/>
				<eLabel backgroundColor="#555555" position="5,420" size="890,2" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/red.png" position="0,425" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/yellow.png" position="310,425" size="35,25" zPosition="5"/>
				<eLabel font="Regular;18" halign="left" position="35,425" size="120,25" text="Set name" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="345,425" size="220,25" text="Make a softlink" transparent="1" valign="center" zPosition="6"/>
				</screen>"""
	else:
		skin = """
			<screen position="center,77" size="620,450" title="Make a softlink...">
				<widget name="File" font="Regular;20" halign="center" position="5,0" size="610,100" transparent="1" valign="center" zPosition="4"/>
				<widget name="SLto" position="5,100" scrollbarMode="showOnDemand" size="610,312" zPosition="4"/>
				<eLabel backgroundColor="#555555" position="5,420" size="610,2" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/red.png" position="0,425" size="35,25" zPosition="5"/>
				<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/res/yellow.png" position="310,425" size="35,25" zPosition="5"/>
				<eLabel font="Regular;18" halign="left" position="35,425" size="120,25" text="Set name" transparent="1" valign="center" zPosition="6"/>
				<eLabel font="Regular;18" halign="left" position="345,425" size="220,25" text="Make a softlink" transparent="1" valign="center" zPosition="6"/>
			</screen>"""
	def __init__(self, session, source = "/tmp/"):
		self.skin = SoftLinkScreen.skin
		Screen.__init__(self, session)
		self.sesion = session
		self.src = source
		self.newSLname = " "
		self["File"] = Label("Set first the Softlink name ...")
		self["SLto"] = myFileList('/', showDirectories=True, showFiles=True, matchingPattern = None, useServiceRef = False)
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"ok": self.ok,
			"back": self.NothingToDo,
			"red": self.GetSLname,
			"yellow": self.MakeSLnow
		}, -1)

	def GetSLname(self):
		self.session.openWithCallback(self.callbackSetLinkName, vInputBox, title=_("Write the new softlink name here:"), windowTitle=_("Dream Explorer..."), text="newname")

	def callbackSetLinkName(self, answer):
		if answer is None:
			return
		if (" " in answer) or (answer==""):
			dei = self.session.open(MessageBox,_("Softlink name error !"), MessageBox.TYPE_ERROR)
			dei.setTitle(_("Dream-Explorer"))
			return
		else:
			self.newSLname = self.src + answer
			self["File"].setText(_("WARNING! they make now a softlink from\n" + self.newSLname + "\nto:"))

	def ok(self):
		if self["SLto"].canDescent():
			self["SLto"].descent()

	def NothingToDo(self):
		self.close(" ")

	def MakeSLnow(self):
		if self.newSLname!=" ":
			if self["SLto"].getSelectionIndex()!=0:
				if self["SLto"].canDescent():
					order = 'ln -s \"' + self["SLto"].getSelection()[0] + '\" \"' + self.newSLname + '\"'
				else:
					order = 'ln -s \"' + (self["SLto"].getCurrentDirectory() + self["SLto"].getFilename()) + '\" \"' + self.newSLname + '\"'
				os_system(order)
				self.close(" ")
		else:
			dei = self.session.open(MessageBox,_("Softlink name error !"), MessageBox.TYPE_ERROR)
			dei.setTitle(_("Dream-Explorer"))










