#
#  MovieSelectionQuickButton E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2009
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MovieSelection import MovieSelection, MovieContextMenu
from Components.MovieList import MovieList
from Components.ActionMap import HelpableActionMap, ActionMap
from Components.Button import Button
from Components.PluginComponent import plugins
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import ConfigSubsection, ConfigText, ConfigYesNo, configfile, ConfigSelection, getConfigListEntry
from Components.config import config
from Screens.MessageBox import MessageBox
# for localized messages
from . import _

config.plugins.MovieSelectionQuickButton = ConfigSubsection()
config.plugins.MovieSelectionQuickButton.red = ConfigText(default=_("Delete"), visible_width=50, fixed_size=False)
config.plugins.MovieSelectionQuickButton.green = ConfigText(default=_("Nothing"), visible_width=50, fixed_size=False)
config.plugins.MovieSelectionQuickButton.yellow = ConfigText(default=_("Nothing"), visible_width=50, fixed_size=False)
config.plugins.MovieSelectionQuickButton.blue = ConfigText(default=_("Nothing"), visible_width=50, fixed_size=False)
config.plugins.MovieSelectionQuickButton.buttoncaption = ConfigSelection(default="0", choices=[("0", _("display plugin name")), ("1", _("display plugin description"))])
config.plugins.MovieSelectionQuickButton.show_in_extensionsmenu = ConfigYesNo(default=False)

###########################################
# MovieSelection
###########################################
baseMovieSelection__init__ = None
baseupdateTags = None
def MovieSelectionInit():
	global baseMovieSelection__init__, baseupdateTags
	if baseMovieSelection__init__ is None:
		baseMovieSelection__init__ = MovieSelection.__init__
	if baseupdateTags is None:
		baseupdateTags = MovieSelection.updateTags
	MovieSelection.__init__ = MovieSelection__init__
	MovieSelection.updateTags = noUpdateTages
	# new methods
	MovieSelection.redpressed = redpressed
	MovieSelection.greenpressed = greenpressed
	MovieSelection.yellowpressed = yellowpressed
	MovieSelection.bluepressed = bluepressed
	MovieSelection.getPluginCaption = getPluginCaption

def MovieSelection__init__(self, session, selectedmovie=None):
	baseMovieSelection__init__(self, session, selectedmovie)
	self["key_red"] = Button(self.getPluginCaption(str(config.plugins.MovieSelectionQuickButton.red.value)))
	self["key_green"] = Button(self.getPluginCaption(str(config.plugins.MovieSelectionQuickButton.green.value)))
	self["key_yellow"] = Button(self.getPluginCaption(str(config.plugins.MovieSelectionQuickButton.yellow.value)))
	self["key_blue"] = Button(self.getPluginCaption(str(config.plugins.MovieSelectionQuickButton.blue.value)))
	self["ColorActions"] = HelpableActionMap(self, "ColorActions",
	{
		"red": (self.redpressed, _("Assign plugin to red key pressed")),
		"green": (self.greenpressed, _("Assign plugin to green key pressed")),
		"yellow": (self.yellowpressed, _("Assign plugin to yellow key pressed")),
		"blue": (self.bluepressed, _("Assign plugin to blue key pressed")),
	})

def redpressed(self):
	startPlugin(self, str(config.plugins.MovieSelectionQuickButton.red.value), 0)

def greenpressed(self):
	startPlugin(self, str(config.plugins.MovieSelectionQuickButton.green.value), 1)

def yellowpressed(self):
	startPlugin(self, str(config.plugins.MovieSelectionQuickButton.yellow.value), 2)

def bluepressed(self):
	startPlugin(self, str(config.plugins.MovieSelectionQuickButton.blue.value), 3)

def getPluginCaption(self, pname):
	if pname != _("Nothing"):
		if pname == _("Delete"):
			return _("Delete")
		elif pname == _("Home"):
			return _("Home")
		elif pname == _("Sort"):
			if config.movielist.moviesort.value == MovieList.SORT_ALPHANUMERIC:
				return _("sort by date")
			else:
				return _("alphabetic sort")
		else:
			for p in plugins.getPlugins(where=[PluginDescriptor.WHERE_MOVIELIST]):
				if pname == str(p.name):
					if config.plugins.MovieSelectionQuickButton.buttoncaption.value == "1":
						return p.description
					else:
						return p.name
	return ""

def startPlugin(self, pname, index):
	plugin = None
	no_plugin = True
	msgText = _("Unknown Error")
	current = self.getCurrent()
	if current is not None:
		if pname != _("Nothing"):
			if pname == _("Delete"):
				MCM = MovieContextMenu(self.session, self, current)
				MCM.delete()
				no_plugin = False
			elif pname == _("Home"):
				self.gotFilename(config.usage.default_path.value)
				no_plugin = False
			elif pname == _("Sort"):
				if config.movielist.moviesort.value == MovieList.SORT_ALPHANUMERIC:
					newType = MovieList.SORT_RECORDED
					newCaption = _("alphabetic sort")
				else:
					newType = MovieList.SORT_ALPHANUMERIC
					newCaption = _("sort by date")
				config.movielist.moviesort.value = newType
				self.setSortType(newType)
				self.reloadList()
				if index == 0:
					self["key_red"].setText(newCaption)
				elif index == 1:
					self["key_green"].setText(newCaption)
				elif index == 2:
					self["key_yellow"].setText(newCaption)
				elif index == 3:
					self["key_blue"].setText(newCaption)
				no_plugin = False
			else:
				for p in plugins.getPlugins(where=[PluginDescriptor.WHERE_MOVIELIST]):
					if pname == str(p.name):
						plugin = p
				if plugin is not None:
					try:
						plugin(self.session, current)
						no_plugin = False
					except Exception as e:
						msgText = _("Error!\nError Text: %s" % e)
				else: 
					msgText = _("Plugin not found!")
		else:
			msgText = _("No plugin assigned!")
		if no_plugin:
			self.session.open(MessageBox, msgText, MessageBox.TYPE_INFO)

def noUpdateTages(self):
	pass #nothing to do here, just ovewrite the method

class MovieSelectionButtonSetup(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="550,400" title="MovieSelection QuickButton Setup" >
			<widget name="config" position="20,10" size="510,330" scrollbarMode="showOnDemand" />
			<widget name="key_red" position="0,350" size="140,40" valign="center" halign="center" zPosition="5" transparent="1" foregroundColor="white" font="Regular;18"/>
			<widget name="key_green" position="140,350" size="140,40" valign="center" halign="center" zPosition="5" transparent="1" foregroundColor="white" font="Regular;18"/>
			<ePixmap name="red" pixmap="skin_default/buttons/red.png" position="0,350" size="140,40" zPosition="4" transparent="1" alphatest="on"/>
			<ePixmap name="green" pixmap="skin_default/buttons/green.png" position="140,350" size="140,40" zPosition="4" transparent="1" alphatest="on"/>
		</screen>"""

	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self.entryguilist = []
		self.entryguilist.append(("0", _("Nothing")))
		self.entryguilist.append(("1", _("Delete")))
		self.entryguilist.append(("2", _("Home")))
		self.entryguilist.append(("3", _("Sort")))
		index = 4
		red_selectedindex = self.getStaticName(config.plugins.MovieSelectionQuickButton.red.value)
		green_selectedindex = self.getStaticName(config.plugins.MovieSelectionQuickButton.green.value)
		yellow_selectedindex = self.getStaticName(config.plugins.MovieSelectionQuickButton.yellow.value)
		blue_selectedindex = self.getStaticName(config.plugins.MovieSelectionQuickButton.blue.value)
		for p in plugins.getPlugins(where=[PluginDescriptor.WHERE_MOVIELIST]):
			self.entryguilist.append((str(index), str(p.name)))
			if config.plugins.MovieSelectionQuickButton.red.value == str(p.name):
				red_selectedindex = str(index)
			if config.plugins.MovieSelectionQuickButton.green.value == str(p.name):
				green_selectedindex = str(index)
			if config.plugins.MovieSelectionQuickButton.yellow.value == str(p.name):
				yellow_selectedindex = str(index)
			if config.plugins.MovieSelectionQuickButton.blue.value == str(p.name):
				blue_selectedindex = str(index)
			index = index + 1
		self.redchoice = ConfigSelection(default=red_selectedindex, choices=self.entryguilist)
		self.greenchoice = ConfigSelection(default=green_selectedindex, choices=self.entryguilist)
		self.yellowchoice = ConfigSelection(default=yellow_selectedindex, choices=self.entryguilist)
		self.bluechoice = ConfigSelection(default=blue_selectedindex, choices=self.entryguilist)
		cfglist = [
			getConfigListEntry(_("assigned to red"), self.redchoice),
			getConfigListEntry(_("assigned to green"), self.greenchoice),
			getConfigListEntry(_("assigned to yellow"), self.yellowchoice),
			getConfigListEntry(_("assigned to blue"), self.bluechoice),
			getConfigListEntry(_("button caption"), config.plugins.MovieSelectionQuickButton.buttoncaption),
			getConfigListEntry(_("Show Setup in Extensions menu"), config.plugins.MovieSelectionQuickButton.show_in_extensionsmenu)
			]
		ConfigListScreen.__init__(self, cfglist, session)
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"cancel": self.keyClose,
			"ok": self.keySave,
		}, -2)

	def keySave(self):
		config.plugins.MovieSelectionQuickButton.red.value = self.entryguilist[int(self.redchoice.value)][1]
		config.plugins.MovieSelectionQuickButton.green.value = self.entryguilist[int(self.greenchoice.value)][1]
		config.plugins.MovieSelectionQuickButton.yellow.value = self.entryguilist[int(self.yellowchoice.value)][1]
		config.plugins.MovieSelectionQuickButton.blue.value = self.entryguilist[int(self.bluechoice.value)][1]
		config.plugins.MovieSelectionQuickButton.save()
		configfile.save()
		self.close()

	def keyClose(self):
		self.close()

	def getStaticName(self, value):
		if value == _("Delete"):
			return "1"
		elif value == _("Home"):
			return "2"
		elif value == _("Sort"):
			return "3"
		else:
			return "0"

def setup(session,**kwargs):
	session.open(MovieSelectionButtonSetup)

def main(session, **kwargs):
	try:
		MovieSelectionInit()
	except:
		pass

def Plugins(**kwargs):
	list = [PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=main)]	
	list.append(PluginDescriptor(name="Setup MovieSelection QuickButton", description=_("Setup for MovieSelection QuickButton"),
	where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=setup))
	
	if config.plugins.MovieSelectionQuickButton.show_in_extensionsmenu.value:	
		list.append(PluginDescriptor(name="Setup MovieSelection QuickButton", description=_("Setup for MovieSelection QuickButton"),
		where=PluginDescriptor.WHERE_EXTENSIONSMENU, icon="plugin.png", fnc=setup))
	return list

