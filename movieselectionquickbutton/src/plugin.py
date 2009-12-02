#
#  MovieSelectionQuickButton E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2009
#  Support: www.dreambox-tools.info
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MovieSelection import MovieSelection, MovieContextMenu
from Components.ActionMap import HelpableActionMap, ActionMap
from Components.Button import Button
from Components.PluginComponent import plugins
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import ConfigSubsection, ConfigText, configfile, ConfigSelection, getConfigListEntry
from Components.config import config
from Screens.MessageBox import MessageBox
# for localized messages
from . import _

config.plugins.MovieSelectionQuickButton = ConfigSubsection()
config.plugins.MovieSelectionQuickButton.green = ConfigText(default = _("Nothing"), visible_width = 50, fixed_size = False)
config.plugins.MovieSelectionQuickButton.yellow = ConfigText(default = _("Nothing"), visible_width = 50, fixed_size = False)
config.plugins.MovieSelectionQuickButton.blue = ConfigText(default = _("Nothing"), visible_width = 50, fixed_size = False)
config.plugins.MovieSelectionQuickButton.buttoncaption = ConfigSelection(default="0", choices = [("0", _("display plugin name")),("1", _("display plugin description"))])

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

def MovieSelection__init__(self, session, selectedmovie = None):
	baseMovieSelection__init__ (self, session, selectedmovie)
	self["key_red"] = Button(_("Delete"))
	self["key_green"] = Button(self.getPluginCaption(str(config.plugins.MovieSelectionQuickButton.green.value)))
	self["key_yellow"] = Button(self.getPluginCaption(str(config.plugins.MovieSelectionQuickButton.yellow.value)))
	self["key_blue"] = Button(self.getPluginCaption(str(config.plugins.MovieSelectionQuickButton.blue.value)))
	self["ColorActions"] = HelpableActionMap(self, "ColorActions",
	{
		"red": (self.redpressed, _("delete movie")),
		"green": (self.greenpressed, _("Assign plugin to green key pressed")),
		"yellow": (self.yellowpressed, _("Assign plugin to yellow key pressed")),
		"blue": (self.bluepressed, _("Assign plugin to blue key pressed")),
	})

def redpressed(self):
	current = self.getCurrent()
	if current is not None:
		MCM = MovieContextMenu(self.session,self,current)
		MCM.delete()

def greenpressed(self):
	startPlugin(self,str(config.plugins.MovieSelectionQuickButton.green.value))

def yellowpressed(self):
	startPlugin(self,str(config.plugins.MovieSelectionQuickButton.yellow.value))

def bluepressed(self):
	startPlugin(self,str(config.plugins.MovieSelectionQuickButton.blue.value))

def getPluginCaption(self,pname):
	if pname != _("Nothing"):
		for p in plugins.getPlugins(where = [PluginDescriptor.WHERE_MOVIELIST]):
			if pname == str(p.name):
				if config.plugins.MovieSelectionQuickButton.buttoncaption.value == "1":
					return p.description
				else:
					return p.name
	return ""

def startPlugin(self,pname):
	plugin = None
	no_plugin = True
	msgText = _("Unknown Error")
	current = self.getCurrent()
	if current is not None:
		if pname != _("Nothing"):
			for p in plugins.getPlugins(where = [PluginDescriptor.WHERE_MOVIELIST]):
				if pname == str(p.name):
					plugin = p
			if plugin is not None:
				try:
					plugin(self.session, current)
					no_plugin = False
				except Exception, e:
					msgText = _("Error!\nError Text: %s"%e)
			else: 
				msgText = _("Plugin not found!")
		else:
			msgText = _("No plugin assigned!")
		if no_plugin:
			self.session.open(MessageBox,msgText, MessageBox.TYPE_INFO)

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

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self.entryguilist = []
		self.entryguilist.append(("0",_("Nothing")))
		index = 1
		green_selectedindex = "0"
		yellow_selectedindex = "0"
		blue_selectedindex = "0"
		for p in plugins.getPlugins(where = [PluginDescriptor.WHERE_MOVIELIST]):
			self.entryguilist.append((str(index),str(p.name)))
			if config.plugins.MovieSelectionQuickButton.green.value == str(p.name):
				green_selectedindex = str(index)
			if config.plugins.MovieSelectionQuickButton.yellow.value == str(p.name):
				yellow_selectedindex = str(index)
			if config.plugins.MovieSelectionQuickButton.blue.value == str(p.name):
				blue_selectedindex = str(index)
			index = index + 1
		self.greenchoice = ConfigSelection(default = green_selectedindex, choices = self.entryguilist)
		self.yellowchoice = ConfigSelection(default = yellow_selectedindex, choices = self.entryguilist)
		self.bluechoice = ConfigSelection(default = blue_selectedindex, choices = self.entryguilist)
		cfglist = [
			getConfigListEntry(_("assigned to green"), self.greenchoice),
			getConfigListEntry(_("assigned to yellow"), self.yellowchoice),
			getConfigListEntry(_("assigned to blue"), self.bluechoice),
			getConfigListEntry(_("button caption"), config.plugins.MovieSelectionQuickButton.buttoncaption),
			]
		ConfigListScreen.__init__(self, cfglist, session)
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"cancel": self.keyClose,
			"ok": self.keySave,
		}, -2)

	def keySave(self):
		config.plugins.MovieSelectionQuickButton.green.value = self.entryguilist[int(self.greenchoice.value)][1]
		config.plugins.MovieSelectionQuickButton.yellow.value = self.entryguilist[int(self.yellowchoice.value)][1]
		config.plugins.MovieSelectionQuickButton.blue.value = self.entryguilist[int(self.bluechoice.value)][1]
		config.plugins.MovieSelectionQuickButton.save()
		configfile.save()
		self.close()

	def keyClose(self):
		self.close()

def setup(session,**kwargs):
	session.open(MovieSelectionButtonSetup)

def main(session, **kwargs):
	try: MovieSelectionInit()
	except: pass

def Plugins(**kwargs):
	list = [PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = main)]	
	list.append(PluginDescriptor(name="Setup MovieSelection QuickButton", description=_("Setup for MovieSelection QuickButton"), where = [PluginDescriptor.WHERE_PLUGINMENU],
	icon = "plugin.png", fnc=setup))
	return list

