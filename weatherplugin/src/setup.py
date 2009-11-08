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

from enigma import eListboxPythonMultiContent, eListbox, gFont, \
	RT_HALIGN_LEFT, RT_VALIGN_CENTER
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList
from Components.Button import Button
from Components.config import config
from Components.ActionMap import ActionMap, NumberActionMap
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import ConfigSubsection, ConfigSubList, ConfigIP, ConfigInteger, ConfigSelection, ConfigText, ConfigYesNo, getConfigListEntry, configfile


def initWeatherPluginEntryConfig():
	config.plugins.WeatherPlugin.Entries.append(ConfigSubsection())
	i = len(config.plugins.WeatherPlugin.Entries) -1
	config.plugins.WeatherPlugin.Entries[i].city = ConfigText(default = "Heidelberg", visible_width = 50, fixed_size = False)
	config.plugins.WeatherPlugin.Entries[i].language = ConfigText(default = "de", visible_width = 50, fixed_size = False)
	return config.plugins.WeatherPlugin.Entries[i]

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
			<widget name="city" position="5,0" size="150,50" font="Regular;20" halign="left"/>
			<widget name="language" position="155,0" size="150,50" font="Regular;20" halign="left"/>
			<widget name="entrylist" position="0,50" size="550,300" scrollbarMode="showOnDemand"/>
			<widget name="key_red" position="0,350" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="280,350" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="yellow" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="420,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<ePixmap name="red" position="0,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue" position="420,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		</screen>""" % _("WeatherPlugin: List of Entries")

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self["city"] = Button(_("City"))
		self["language"] = Button(_("Language"))
		self["key_red"] = Button(_("Add"))
		self["key_yellow"] = Button(_("Edit"))
		self["key_blue"] = Button(_("Delete"))
		self["entrylist"] = WeatherPluginEntryList([])
		self["actions"] = ActionMap(["WizardActions","MenuActions","ShortcutActions"],
			{
			 "ok"	:	self.keyOK,
			 "back"	:	self.keyClose,
			 "red"	:	self.keyRed,
			 "yellow":	self.keyYellow,
			 "blue": 	self.keyDelete,
			 }, -1)
		self.updateList()

	def updateList(self):
		self["entrylist"].buildList()

	def keyClose(self):
		self.close(-1, None)

	def keyRed(self):
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
		config.plugins.WeatherPlugin.entriescount.value = config.plugins.WeatherPlugin.entriescount.value - 1
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
		self.list=[]
		for c in config.plugins.WeatherPlugin.Entries:
			res = [c]
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 150, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(c.city.value)))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 155, 0, 150, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(c.language.value)))
			self.list.append(res)
		self.l.setList(self.list)
		self.moveToIndex(0)

class WeatherPluginEntryConfigScreen(ConfigListScreen, Screen):
	skin = """
		<screen name="WeatherPluginEntryConfigScreen" position="center,center" size="550,400" title="%s">
			<widget name="config" position="20,10" size="520,330" scrollbarMode="showOnDemand" />
			<ePixmap name="red"	position="0,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="140,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="blue" position="420,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />

			<widget name="key_red" position="0,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="420,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>""" % _("WeatherPlugin: Edit Entry")

	def __init__(self, session, entry):
		self.session = session
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"blue": self.keyDelete,
			"cancel": self.keyCancel
		}, -2)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_blue"] = Button(_("Delete"))

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
