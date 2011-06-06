# -*- coding: utf-8 -*-
#
#  Weather Plugin E2
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

# for localized messages
from . import _

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, \
	RT_VALIGN_CENTER
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import ConfigSubsection, ConfigText, \
	getConfigListEntry, config, configfile


def initWeatherPluginEntryConfig():
	s = ConfigSubsection()
	s.city = ConfigText(default = "Heidelberg", visible_width = 50, fixed_size = False)
	s.language = ConfigText(default = "de", visible_width = 50, fixed_size = False)
	config.plugins.WeatherPlugin.Entries.append(s)
	return s

def initConfig():
	count = config.plugins.WeatherPlugin.entriescount.value
	if count != 0:
		i = 0
		while i < count:
			initWeatherPluginEntryConfig()
			i += 1

class WeatherPluginEntriesListConfigScreen(Screen):
	skin = """
		<screen position="center,center" size="550,400" title="%s" >
			<widget render="Label" source="city" position="5,0" size="150,50" font="Regular;20" halign="left"/>
			<widget render="Label" source="language" position="155,0" size="150,50" font="Regular;20" halign="left"/>
			<widget name="entrylist" position="0,50" size="550,300" scrollbarMode="showOnDemand"/>
			<widget render="Label" source="key_red" position="0,350" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="140,350" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="green" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_yellow" position="280,350" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="yellow" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_blue" position="420,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<ePixmap position="0,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="420,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		</screen>""" % _("WeatherPlugin: List of Entries")

	def __init__(self, session):
		Screen.__init__(self, session)

		self["city"] = StaticText(_("City"))
		self["language"] = StaticText(_("Language"))
		self["key_red"] = StaticText(_("Back"))
		self["key_green"] = StaticText(_("Add"))		
		self["key_yellow"] = StaticText(_("Edit"))
		self["key_blue"] = StaticText(_("Delete"))
		self["entrylist"] = WeatherPluginEntryList([])
		self["actions"] = ActionMap(["WizardActions","MenuActions","ShortcutActions"],
			{
			 "ok"	:	self.keyOK,
			 "back"	:	self.keyClose,
			 "red"	:	self.keyClose,
			 "green":	self.keyGreen,			 
			 "yellow":	self.keyYellow,
			 "blue": 	self.keyDelete,
			 }, -1)
		self.updateList()

	def updateList(self):
		self["entrylist"].buildList()

	def keyClose(self):
		self.close(-1, None)

	def keyGreen(self):
		self.session.openWithCallback(self.updateList,WeatherPluginEntryConfigScreen,None)

	def keyOK(self):
		try:sel = self["entrylist"].l.getCurrentSelection()[0]
		except: sel = None
		self.close(self["entrylist"].getCurrentIndex(), sel)

	def keyYellow(self):
		try:sel = self["entrylist"].l.getCurrentSelection()[0]
		except: sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.updateList,WeatherPluginEntryConfigScreen,sel)

	def keyDelete(self):
		try:sel = self["entrylist"].l.getCurrentSelection()[0]
		except: sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this WeatherPlugin Entry?"))

	def deleteConfirm(self, result):
		if not result:
			return
		sel = self["entrylist"].l.getCurrentSelection()[0]
		config.plugins.WeatherPlugin.entriescount.value -= 1
		config.plugins.WeatherPlugin.entriescount.save()
		config.plugins.WeatherPlugin.Entries.remove(sel)
		config.plugins.WeatherPlugin.Entries.save()
		config.plugins.WeatherPlugin.save()
		configfile.save()
		self.updateList()

class WeatherPluginEntryList(MenuList):
	def __init__(self, list, enableWrapAround = True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 18))

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(20)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def buildList(self):
		list = []
		for c in config.plugins.WeatherPlugin.Entries:
			res = [
				c,
				(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 150, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(c.city.value)),
				(eListboxPythonMultiContent.TYPE_TEXT, 155, 0, 150, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(c.language.value)),
			]
			list.append(res)
		self.list = list
		self.l.setList(list)
		self.moveToIndex(0)

class WeatherPluginEntryConfigScreen(ConfigListScreen, Screen):
	skin = """
		<screen name="WeatherPluginEntryConfigScreen" position="center,center" size="550,400" title="%s">
			<widget name="config" position="20,10" size="520,330" scrollbarMode="showOnDemand" />
			<ePixmap position="0,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="420,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />

			<widget source="key_red" render="Label" position="0,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="140,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_blue" render="Label" position="420,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>""" % _("WeatherPlugin: Edit Entry")

	def __init__(self, session, entry):
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"blue": self.keyDelete,
			"cancel": self.keyCancel
		}, -2)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_blue"] = StaticText(_("Delete"))

		if entry is None:
			self.newmode = 1
			self.current = initWeatherPluginEntryConfig()
		else:
			self.newmode = 0
			self.current = entry

		cfglist = [
			getConfigListEntry(_("City or Postal Code"), self.current.city),
			getConfigListEntry(_("Language"), self.current.language)
		]

		ConfigListScreen.__init__(self, cfglist, session)

	def keySave(self):
		if self.newmode == 1:
			config.plugins.WeatherPlugin.entriescount.value = config.plugins.WeatherPlugin.entriescount.value + 1
			config.plugins.WeatherPlugin.entriescount.save()
		ConfigListScreen.keySave(self)
		config.plugins.WeatherPlugin.save()
		configfile.save()
		self.close()

	def keyCancel(self):
		if self.newmode == 1:
			config.plugins.WeatherPlugin.Entries.remove(self.current)
		ConfigListScreen.cancelConfirm(self, True)

	def keyDelete(self):
		if self.newmode == 1:
			self.keyCancel()
		else:		
			self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this WeatherPlugin Entry?"))

	def deleteConfirm(self, result):
		if not result:
			return
		config.plugins.WeatherPlugin.entriescount.value = config.plugins.WeatherPlugin.entriescount.value - 1
		config.plugins.WeatherPlugin.entriescount.save()
		config.plugins.WeatherPlugin.Entries.remove(self.current)
		config.plugins.WeatherPlugin.Entries.save()
		config.plugins.WeatherPlugin.save()
		configfile.save()
		self.close()
