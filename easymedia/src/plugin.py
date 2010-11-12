#######################################################################
#
#    EasyMedia for Dreambox-Enigma2
#    Coded by Vali (c)2010
#    Support: www.dreambox-tools.info
#
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#  To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#  or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
#
#######################################################################



from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InfoBarGenerics import InfoBarPlugins
from Screens.InfoBar import InfoBar
from Screens.ChoiceBox import ChoiceBox
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.config import config
from Tools.Directories import fileExists
from Tools.LoadPixmap import LoadPixmap
from enigma import RT_HALIGN_LEFT, eListboxPythonMultiContent, gFont, getDesktop



EMbaseInfoBarPlugins__init__ = None
EMStartOnlyOneTime = False
EMsession = None
InfoBar_instance = None



def Plugins(**kwargs):
	return [PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = EasyMediaAutostart),
			PluginDescriptor(name="EasyMedia", description=_("Not easy way to start EasyMedia"), where = PluginDescriptor.WHERE_PLUGINMENU, fnc=notEasy),]



def EasyMediaAutostart(reason, **kwargs):
	global EMbaseInfoBarPlugins__init__
	if "session" in kwargs:
		global EMsession
		EMsession = kwargs["session"]
		if EMbaseInfoBarPlugins__init__ is None:
			EMbaseInfoBarPlugins__init__ = InfoBarPlugins.__init__
		InfoBarPlugins.__init__ = InfoBarPlugins__init__
		InfoBarPlugins.pvr = pvr



def InfoBarPlugins__init__(self):
	global EMStartOnlyOneTime
	if not EMStartOnlyOneTime: 
		EMStartOnlyOneTime = True
		global InfoBar_instance
		InfoBar_instance = self
		self["EasyMediaActions"] = ActionMap(["EasyMediaActions"],
			{"video_but": self.pvr}, -1)
	else:
		InfoBarPlugins.__init__ = InfoBarPlugins.__init__
		InfoBarPlugins.pvr = None
	EMbaseInfoBarPlugins__init__(self)



def pvr(self):
	self.session.openWithCallback(MPcallbackFunc, EasyMedia)



def notEasy(session, **kwargs):
	session.openWithCallback(MPcallbackFunc, EasyMedia)



def MPanelEntryComponent(key, text):
	res = [ text ]
	res.append((eListboxPythonMultiContent.TYPE_TEXT, 160, 15, 300, 60, 0, RT_HALIGN_LEFT, text[0]))
	png = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/' + key + ".png")
	if png is not None:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 30, 5, 100, 50, png))
	return res



class MPanelList(MenuList):
	def __init__(self, list, selection = 0, enableWrapAround=True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 24))
		self.l.setItemHeight(60)
		self.selection = selection
	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		self.moveToIndex(self.selection)



def BookmarksCallback(choice):
	choice = choice and choice[1]
	if choice:
		config.movielist.last_videodir.value = choice
		config.movielist.last_videodir.save()
		if InfoBar_instance:
			InfoBar_instance.showMovies()



class EasyMedia(Screen):
	sz_w = getDesktop(0).size().width()
	if sz_w > 1100:
		skin = """
		<screen flags="wfNoBorder" position="0,0" size="450,720" title="Easy Media">
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/bg.png" position="0,0" size="450,576"/>
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/bg.png" position="0,576" size="450,145"/>
			<widget name="list" position="60,30" size="350,660" scrollbarMode="showNever" transparent="1" zPosition="2"/>
		</screen>"""
	elif sz_w > 1000:
		skin = """
		<screen flags="wfNoBorder" position="-20,0" size="450,576" title="Easy Media">
			<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/EasyMedia/bg.png" position="0,0" size="450,576"/>
			<widget name="list" position="70,48" size="320,480" scrollbarMode="showNever" transparent="1" zPosition="2"/>
		</screen>"""
	else:
		skin = """
		<screen position="center,center" size="320,440" title="Easy Media">
			<widget name="list" position="10,10" size="300,420" scrollbarMode="showOnDemand" />
		</screen>"""
	def __init__(self, session):
		Screen.__init__(self, session)
		self.list = []
		self.__keys = [ "movies", "bookmarks", "pictures", "music" ]
		MPaskList = [(_("Movies"), "PLAYMOVIES"),(_("Bookmarks"), "BOOKMARKS"),(_("Pictures"), "PICTURES"),(_("Music"), "MUSIC")]
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/plugin.pyo"):
			self.__keys.append("dvd")
			MPaskList.append((_("DVD Player"), "DVD"))
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/WeatherPlugin/plugin.pyo"):
			self.__keys.append("weather")
			MPaskList.append((_("Weather"), "WEATHER"))
		if True:
			self.__keys.append("files")
			MPaskList.append((_("Files"), "FILES"))
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/SHOUTcast/plugin.pyo"):
			self.__keys.append("shoutcast")
			MPaskList.append((_("SHOUTcast"), "SHOUTCAST"))
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/plugin.pyo"):
			self.__keys.append("idream")
			MPaskList.append((_("iDream"), "IDREAM"))
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MyTube/plugin.pyo"):
			self.__keys.append("mytube")
			MPaskList.append((_("MyTube Player"), "MYTUBE"))
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/VlcPlayer/plugin.pyo"):
			self.__keys.append("vlc")
			MPaskList.append((_("VLC Player"), "VLC"))
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/ZDFMediathek/plugin.pyo"):
			self.__keys.append("zdf")
			MPaskList.append((_("ZDFmediathek"), "ZDF"))
		self.keymap = {}
		pos = 0
		for x in MPaskList:
			strpos = str(self.__keys[pos])
			self.list.append(MPanelEntryComponent(key = strpos, text = x))
			if self.__keys[pos] != "":
				self.keymap[self.__keys[pos]] = MPaskList[pos]
			pos += 1
		self["list"] = MPanelList(list = self.list, selection = 0)
		self["actions"] = ActionMap(["WizardActions"],
		{
			"ok": self.go,
			"back": self.cancel
		}, -1)

	def cancel(self):
		self.close(None)

	def go(self):
		cursel = self["list"].l.getCurrentSelection()
		if cursel:
			self.goEntry(cursel[0])
		else:
			self.cancel()

	def goEntry(self, entry):
		if len(entry) > 2 and isinstance(entry[1], str) and entry[1] == "CALLFUNC":
			arg = self["list"].l.getCurrentSelection()[0]
			entry[2](arg)
		else:
			self.close(entry)



def MPcallbackFunc(answer):
	answer = answer and answer[1]
	if answer == "PLAYMOVIES":
		if InfoBar_instance:
			InfoBar_instance.showMovies()
	elif answer == "BOOKMARKS":
		tmpBookmarks = config.movielist.videodirs
		myBookmarks = tmpBookmarks and tmpBookmarks.value[:] or []
		if len(myBookmarks)>0:
			askBM = []
			for s in myBookmarks:
				askBM.append((s, s))
			EMsession.openWithCallback(BookmarksCallback, ChoiceBox, title="Select bookmark...", list = askBM)
	elif answer == "PICTURES":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/PicturePlayer/plugin.pyo"):
			from Plugins.Extensions.PicturePlayer.plugin import picshow
			EMsession.open(picshow)
		else:
			EMsession.open(MessageBox, text = _('Picture-player is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "MUSIC":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/plugin.pyo"):
			from Plugins.Extensions.MerlinMusicPlayer.plugin import MerlinMusicPlayerFileList
			servicelist = None
			EMsession.open(MerlinMusicPlayerFileList, servicelist)
		elif fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MediaPlayer/plugin.pyo"):
			from Plugins.Extensions.MediaPlayer.plugin import MediaPlayer
			EMsession.open(MediaPlayer)
		else:
			EMsession.open(MessageBox, text = _('No Music-Player installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "FILES":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Tuxcom/plugin.pyo"):
			from Plugins.Extensions.Tuxcom.plugin import TuxComStarter
			EMsession.open(TuxComStarter)
		elif fileExists("/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/plugin.pyo"):
			from Plugins.Extensions.DreamExplorer.plugin import DreamExplorerII
			EMsession.open(DreamExplorerII)
		elif fileExists("/usr/lib/enigma2/python/Plugins/Extensions/Filebrowser/plugin.pyo"):
			from Plugins.Extensions.Filebrowser.plugin import FilebrowserScreen
			EMsession.open(FilebrowserScreen)
		else:
			EMsession.open(MessageBox, text = _('No File-Manager installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "WEATHER":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/WeatherPlugin/plugin.pyo"):
			from Plugins.Extensions.WeatherPlugin.plugin import WeatherPlugin
			EMsession.open(WeatherPlugin)
		else:
			EMsession.open(MessageBox, text = _('Weather Plugin is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "DVD":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/plugin.pyo"):
			from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
			EMsession.open(DVDPlayer)
		else:
			EMsession.open(MessageBox, text = _('DVDPlayer Plugin is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "MYTUBE":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MyTube/plugin.pyo"):
			from Plugins.Extensions.MyTube.plugin import *
			MyTubeMain(EMsession)
		else:
			EMsession.open(MessageBox, text = _('MyTube Plugin is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "SHOUTCAST":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/SHOUTcast/plugin.pyo"):
			from Plugins.Extensions.SHOUTcast.plugin import SHOUTcastWidget
			EMsession.open(SHOUTcastWidget)
		else:
			EMsession.open(MessageBox, text = _('SHOUTcast Plugin is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "ZDF":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/ZDFMediathek/plugin.pyo"):
			from Plugins.Extensions.ZDFMediathek.plugin import ZDFMediathek
			EMsession.open(ZDFMediathek)
		else:
			EMsession.open(MessageBox, text = _('ZDFmediathek Plugin is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "VLC":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/VlcPlayer/plugin.pyo"):
			from Plugins.Extensions.VlcPlayer.plugin import *
			main(EMsession)
		else:
			EMsession.open(MessageBox, text = _('VLC Player is not installed!'), type = MessageBox.TYPE_ERROR)
	elif answer == "IDREAM":
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/MerlinMusicPlayer/plugin.pyo"):
			from Plugins.Extensions.MerlinMusicPlayer.plugin import iDreamMerlin
			servicelist = None
			EMsession.open(iDreamMerlin, servicelist)
		else:
			EMsession.open(MessageBox, text = _('Merlin iDream is not installed!'), type = MessageBox.TYPE_ERROR)














