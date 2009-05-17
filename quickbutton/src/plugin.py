
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
config.plugins.Quickbutton.red = ConfigText(default = "", visible_width = 50, fixed_size = False)
config.plugins.Quickbutton.green = ConfigText(default = "", visible_width = 50, fixed_size = False)
config.plugins.Quickbutton.yellow = ConfigText(default = "", visible_width = 50, fixed_size = False)
config.plugins.Quickbutton.blue = ConfigText(default = "", visible_width = 50, fixed_size = False)

EPGListTitle = _("EPG List")

def autostart(reason, **kwargs):
	if "session" in kwargs:
		session = kwargs["session"]
		Quickbutton(session)

def setup(session,**kwargs):
	session.open(QuickbuttonSetup)

def Plugins(**kwargs):

	list = [PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart)]	
	list.append(PluginDescriptor(name="Setup Quickbutton", description=_("setup for Quickbutton"), where = [PluginDescriptor.WHERE_PLUGINMENU], fnc=setup))
	return list

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
		red_selectedindex = "0"
		if config.plugins.Quickbutton.red.value == EPGListTitle:
			red_selectedindex = "1"
		green_selectedindex = "0"
		if config.plugins.Quickbutton.green.value == EPGListTitle:
			green_selectedindex = "1"
		yellow_selectedindex = "0"
		if config.plugins.Quickbutton.yellow.value == EPGListTitle:
			yellow_selectedindex = "1"
		blue_selectedindex = "0"
		if config.plugins.Quickbutton.blue.value == EPGListTitle:
			blue_selectedindex = "1"
		# feste Vorgaben...koennte man noch erweitern, da hole ich mir sinnvolle Vorschlaege aus Foren noch ein...
		self.entryguilist.append(("0",_("Nothing")))
		self.entryguilist.append(("1",EPGListTitle))
		# Vorgaben aus EXTENSIONSMENU
		index = 2
		for p in plugins.getPlugins(where = PluginDescriptor.WHERE_EXTENSIONSMENU):
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

class Quickbutton(object):
	def __init__(self, session):
		self.session = session
		QuickbuttonActionMap = ActionMap(["QuickbuttonActions"])
		QuickbuttonActionMap.execBegin()
		QuickbuttonActionMap.actions["green_l"] = self.greenlong
		QuickbuttonActionMap.actions["yellow_l"] = self.yellowlong
		QuickbuttonActionMap.actions["red_l"] = self.redlong 
		QuickbuttonActionMap.actions["blue_l"] = self.bluelong

	def greenlong(self):
		self.getPlugin(str(config.plugins.Quickbutton.green.value))
	
	def yellowlong(self):
		self.getPlugin(str(config.plugins.Quickbutton.yellow.value))
	
	def redlong(self):
		self.getPlugin(str(config.plugins.Quickbutton.red.value))

	def bluelong(self):
		self.getPlugin(str(config.plugins.Quickbutton.blue.value))
	
	def getPlugin(self, pname):
		msgText = _("Unknown Error")
		error = True
		if pname != "":
			if pname == EPGListTitle:
				print "[Quickbutton] EPG List"
				from Screens.EpgSelection import EPGSelection
				self.session.open(EPGSelection, self.session.nav.getCurrentlyPlayingServiceReference())
				error = False
			else:
				ca = None
				for p in plugins.getPlugins(where = PluginDescriptor.WHERE_EXTENSIONSMENU):
					if pname == str(p.name):
						print "[Quickbutton] %s"%p.name
						ca = p
				if ca is not None:
					try: 
						servicelist = self.session.instantiateDialog(ChannelSelection)
						ca(session = self.session, servicelist = servicelist)
						error = False
					except Exception, e:
						msgText = _("Error!\nError Text: %s"%e)
				else: 
					msgText = _("Plugin not found!")
		else:
			msgText = _("No plugin assigned!")
		if error:
			self.session.open(MessageBox,msgText, MessageBox.TYPE_INFO)

