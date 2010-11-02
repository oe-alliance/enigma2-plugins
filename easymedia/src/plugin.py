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
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Tools.Directories import fileExists
from Tools.LoadPixmap import LoadPixmap
from enigma import RT_HALIGN_LEFT, eListboxPythonMultiContent, gFont



EMbaseInfoBarPlugins__init__ = None
EMStartOnlyOneTime = False
EMsession = None



def Plugins(**kwargs):
	return [PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = EasyMediaAutostart)]



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
		self["EasyMediaActions"] = ActionMap(["EasyMediaActions"],
			{"video_but": self.pvr}, -1)
	else:
		InfoBarPlugins.__init__ = InfoBarPlugins.__init__
		InfoBarPlugins.green = None
		InfoBarPlugins.yellow = None
		InfoBarPlugins.red = None
		InfoBarPlugins.blue = None
		InfoBarPlugins.pvr = None
		InfoBarPlugins.radio = None
	EMbaseInfoBarPlugins__init__(self)



def pvr(self):
	MPaskList = [(_("Movies"), "PLAYMOVIES"),
				(_("Pictures"), "PICTURES"),
				(_("Music"), "MUSIC"),
				(_("Weather"), "WEATHER"),
				(_("Files"), "FILES")]
	self.session.openWithCallback(MPcallbackFunc, EasyMedia, list=MPaskList)



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



class EasyMedia(Screen):
	skin = """
	<screen position="center,center" size="420,320" title="Easy Media">
		<widget name="list" position="10,10" size="400,300" scrollbarMode="showOnDemand" />
	</screen>"""
	def __init__(self, session, list = []):
		Screen.__init__(self, session)
		self.list = []
		self.__keys = [ "movies", "pictures", "music", "weather", "files" ] #+ (len(list) - 4) * [""]
		self.keymap = {}
		pos = 0
		for x in list:
			strpos = str(self.__keys[pos])
			self.list.append(MPanelEntryComponent(key = strpos, text = x))
			if self.__keys[pos] != "":
				self.keymap[self.__keys[pos]] = list[pos]
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
		if InfoBar and InfoBar.instance:
			InfoBar.showMovies(InfoBar.instance)
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
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/DreamExplorer/plugin.pyo"):
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
	


