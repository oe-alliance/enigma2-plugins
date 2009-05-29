
#  Quickbutton
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

from Screens.Screen import Screen
from Screens.ChannelSelection import ChannelSelection
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import ConfigSubsection, ConfigText, configfile, ConfigSelection, getConfigListEntry
from Components.config import config
from Components.Button import Button
from Screens.MessageBox import MessageBox

config.plugins.Quickbutton = ConfigSubsection()
config.plugins.Quickbutton.red = ConfigText(default = _("Nothing"), visible_width = 50, fixed_size = False)
config.plugins.Quickbutton.green = ConfigText(default = _("Nothing"), visible_width = 50, fixed_size = False)
config.plugins.Quickbutton.yellow = ConfigText(default = _("Nothing"), visible_width = 50, fixed_size = False)
config.plugins.Quickbutton.blue = ConfigText(default = _("Nothing"), visible_width = 50, fixed_size = False)


from  Screens.InfoBarGenerics import InfoBarPlugins
baseInfoBarPlugins__init__ = None
baserunPlugin = None
StartOnlyOneTime = False


def autostart(reason, **kwargs):
	global baseInfoBarPlugins__init__, baserunPlugin
	if "session" in kwargs:
		session = kwargs["session"]
		if baseInfoBarPlugins__init__ is None:
			baseInfoBarPlugins__init__ = InfoBarPlugins.__init__
		if baserunPlugin is None:
			baserunPlugin = InfoBarPlugins.runPlugin
		InfoBarPlugins.__init__ = InfoBarPlugins__init__
		InfoBarPlugins.runPlugin = runPlugin
		InfoBarPlugins.greenlong = greenlong
		InfoBarPlugins.yellowlong = yellowlong
		InfoBarPlugins.redlong = redlong
		InfoBarPlugins.bluelong = bluelong

def setup(session,**kwargs):
	session.open(QuickbuttonSetup)

def Plugins(**kwargs):

	list = [PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart)]	
	list.append(PluginDescriptor(name="Setup Quickbutton", description=_("setup for Quickbutton"), where = [PluginDescriptor.WHERE_PLUGINMENU], fnc=setup))
	return list

def InfoBarPlugins__init__(self):
	global StartOnlyOneTime
	if not StartOnlyOneTime: 
		StartOnlyOneTime = True # nur einmal...z.b. wegen dem Movieplayer...
		QuickbuttonActionMap = ActionMap(["QuickbuttonActions"])
		QuickbuttonActionMap.execBegin()
		QuickbuttonActionMap.actions["green_l"] = self.greenlong
		QuickbuttonActionMap.actions["yellow_l"] = self.yellowlong
		QuickbuttonActionMap.actions["red_l"] = self.redlong 
		QuickbuttonActionMap.actions["blue_l"] = self.bluelong
		
	else:
		InfoBarPlugins.__init__ = InfoBarPlugins.__init__
		InfoBarPlugins.runPlugin = InfoBarPlugins.runPlugin
		InfoBarPlugins.greenlong = None
		InfoBarPlugins.yellowlong = None
		InfoBarPlugins.redlong = None
		InfoBarPlugins.bluelong = None
	baseInfoBarPlugins__init__(self)

def runPlugin(self, plugin):
	baserunPlugin(self,plugin)

def greenlong(self):
	startPlugin(self,str(config.plugins.Quickbutton.green.value))

def yellowlong(self):
	startPlugin(self, str(config.plugins.Quickbutton.yellow.value))

def redlong(self):
	startPlugin(self, str(config.plugins.Quickbutton.red.value))

def bluelong(self):
	startPlugin(self, str(config.plugins.Quickbutton.blue.value))

def startPlugin(self,pname):
	msgText = _("Unknown Error")
	no_plugin = True
	if pname != _("Nothing"):
		if pname == _("EPG List"):
			from Screens.EpgSelection import EPGSelection
			self.session.open(EPGSelection, self.session.nav.getCurrentlyPlayingServiceReference())
			no_plugin = False
		elif pname == _("MediaPlayer"):
			try: # falls es nicht installiert ist
				from Plugins.Extensions.MediaPlayer.plugin import MediaPlayer
				self.session.open(MediaPlayer)
				no_plugin = false
			except Exception, e:
				msgText = _("Error!\nError Text: %s"%e)
		elif pname == _("Plugin browser"):
			from Screens.PluginBrowser import PluginBrowser
			self.session.open(PluginBrowser)
			no_plugin = False
		elif pname == _("switch 4:3 content display"):
			ar = {	"pillarbox": _("Pillarbox"), 
				"panscan": _("Pan&Scan"),  
				"scale": _("Just Scale")}
			switch = { "pillarbox":"panscan", "panscan":"scale", "scale":"pillarbox" }
			config.av.policy_43.value =  switch[config.av.policy_43.value]
			config.av.policy_43.save()
			self.session.open(MessageBox,_("Display 4:3 content as") + " " + ar[config.av.policy_43.value], MessageBox.TYPE_INFO, timeout = 3)
			no_plugin = False
		else:
			plugin = None
			for p in plugins.getPlugins(where = [PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU]):
				if pname == str(p.name):
					plugin = p
			if plugin is not None:
				try:
					runPlugin(self,plugin)
					no_plugin = False
				except Exception, e:
					msgText = _("Error!\nError Text: %s"%e)
			else: 
				msgText = _("Plugin not found!")
	else:
		msgText = _("No plugin assigned!")
	if no_plugin:
		self.session.open(MessageBox,msgText, MessageBox.TYPE_INFO)


class QuickbuttonSetup(ConfigListScreen, Screen):
	skin = """
		<screen position="100,100" size="550,400" title="Quickbutton Setup" >
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
		red_selectedindex = self.getStaticPluginName(config.plugins.Quickbutton.red.value)
		green_selectedindex = self.getStaticPluginName(config.plugins.Quickbutton.green.value)
		yellow_selectedindex = self.getStaticPluginName(config.plugins.Quickbutton.yellow.value)
		blue_selectedindex = self.getStaticPluginName(config.plugins.Quickbutton.blue.value)
		# feste Vorgaben...koennte man noch erweitern, da hole ich mir sinnvolle Vorschlaege aus Foren noch ein...
		self.entryguilist.append(("0",_("Nothing")))
		self.entryguilist.append(("1",_("EPG List")))
		self.entryguilist.append(("2",_("MediaPlayer")))
		self.entryguilist.append(("3",_("Plugin browser")))
		self.entryguilist.append(("4",_("switch 4:3 content display")))
		# Vorgaben aus EXTENSIONSMENU, PLUGINMENU
		index = 5
		for p in plugins.getPlugins(where = [PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU]):
			self.entryguilist.append((str(index),str(p.name)))
			if config.plugins.Quickbutton.red.value == str(p.name):
				red_selectedindex = str(index)
			if config.plugins.Quickbutton.green.value == str(p.name):
				green_selectedindex = str(index)
			if config.plugins.Quickbutton.yellow.value == str(p.name):
				yellow_selectedindex = str(index)
			if config.plugins.Quickbutton.blue.value == str(p.name):
				blue_selectedindex = str(index)
			index = index + 1
		

		self.redchoice = ConfigSelection(default = red_selectedindex, choices = self.entryguilist)
		self.greenchoice = ConfigSelection(default = green_selectedindex, choices = self.entryguilist)
		self.yellowchoice = ConfigSelection(default = yellow_selectedindex, choices = self.entryguilist)
		self.bluechoice = ConfigSelection(default = blue_selectedindex, choices = self.entryguilist)

		cfglist = [
			getConfigListEntry(_("assigned to long red"), self.redchoice),
			getConfigListEntry(_("assigned to long green"), self.greenchoice),
			getConfigListEntry(_("assigned to long yellow"), self.yellowchoice),
			getConfigListEntry(_("assigned to long blue"), self.bluechoice)

			]
		ConfigListScreen.__init__(self, cfglist, session)
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"cancel": self.keyClose,
			"ok": self.keySave,
		}, -2)

	def getStaticPluginName(self,value):
		if value == _("EPG List"):
			return "1"
		elif value == _("MediaPlayer"):
			return "2"
		elif value == _("Plugin browser"):
			return "3"
		elif value == _("switch 4:3 content display"):
			return "4"
		else:
			return "0"

	def keySave(self):
		config.plugins.Quickbutton.red.value = self.entryguilist[int(self.redchoice.value)][1]
		config.plugins.Quickbutton.green.value = self.entryguilist[int(self.greenchoice.value)][1]
		config.plugins.Quickbutton.yellow.value = self.entryguilist[int(self.yellowchoice.value)][1]
		config.plugins.Quickbutton.blue.value = self.entryguilist[int(self.bluechoice.value)][1]
		config.plugins.Quickbutton.save()
		configfile.save()
		self.close()

	def keyClose(self):
		self.close()
