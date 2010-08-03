# -*- coding: utf-8 -*-
#
#  AutomaticVolumeAdjustment E2
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

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, \
	RT_VALIGN_CENTER
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import ConfigSubsection, ConfigText, \
	getConfigListEntry, config, ConfigInteger, Config, ConfigSubList, ConfigDirectory, NoSave, ConfigYesNo
from os import path as os_path, open as os_open, close as os_close, O_RDWR as os_O_RDWR, O_CREAT  as os_O_CREAT 
from Screens.ChannelSelection import SimpleChannelSelection
from enigma import eServiceReference
from ServiceReference import ServiceReference

import plugin as AutomaticVolumeAdjustmentPlugin # import to submit config-values
	
class AutomaticVolumeAdjustmentConfig():
	def __init__(self):
		self.CONFIG_FILE = '/usr/lib/enigma2/python/Plugins/SystemPlugins/AutomaticVolumeAdjustment/config'
		# load config file
		self.loadConfigFile()

	# load config file and initialize 
	def loadConfigFile(self):
		print "[AutomaticVolumeAdjustmentConfig] Loading config file..."
		self.config = Config()
		if not os_path.exists(self.CONFIG_FILE):
			fd = os_open( self.CONFIG_FILE, os_O_RDWR|os_O_CREAT)
			os_close( fd )
		self.config.loadFromFile(self.CONFIG_FILE)
		self.config.entriescount =  ConfigInteger(0)
		self.config.Entries = ConfigSubList()
		self.config.enable = ConfigYesNo(default = False)
		self.config.adustvalue = ConfigInteger(default=25, limits=(0,50))
		self.initConfig()

	def initConfig(self):
		count = self.config.entriescount.value
		if count != 0:
			i = 0
			while i < count:
				self.initEntryConfig()
				i += 1
		print "[AutomaticVolumeAdjustmentConfig] Loaded %s entries from config file..." % count

	def initEntryConfig(self):
		self.config.Entries.append(ConfigSubsection())
		i = len(self.config.Entries) - 1
		self.config.Entries[i].servicereference = ConfigText(default = "")
		self.config.Entries[i].name = NoSave(ConfigDirectory(default = _("Press OK to select a service")))
		self.config.Entries[i].adjustvalue = ConfigInteger(default=25, limits=(5,50))
		return self.config.Entries[i]
	
	def remove(self, configItem):
		self.config.entriescount.value = self.config.entriescount.value - 1
		self.config.entriescount.save()
		self.config.Entries.remove(configItem)
		self.config.Entries.save()
		self.save()
	
	def save(self):
		print "[AutomaticVolumeAdjustmentConfig] saving config file..."
		self.config.saveToFile(self.CONFIG_FILE)
		
class AutomaticVolumeAdjustmentConfigScreen(ConfigListScreen, Screen):
	skin = """
		<screen name="AutomaticVolumeAdjustmentConfigScreen" position="center,center" size="550,400">
			<widget name="config" position="20,10" size="520,330" scrollbarMode="showOnDemand" />
			<ePixmap position="0,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="420,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />

			<widget source="key_red" render="Label" position="0,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="140,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_blue" position="420,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.title = _("Automatic Volume Adjustment - Config")
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"blue": self.blue,
			"cancel": self.keyCancel,
		}, -2)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_blue"] = StaticText(_("Services"))
		self.configVA = AutomaticVolumeAdjustmentConfig()
		self.list = []
		self.list.append(getConfigListEntry(_("Enable"), self.configVA.config.enable))
		self.list.append(getConfigListEntry(_("Default volume adjustment value for AC3/DTS"), self.configVA.config.adustvalue))
		ConfigListScreen.__init__(self, self.list, session)
		
	def blue(self):
		self.session.open(AutomaticVolumeAdjustmentEntriesListConfigScreen, self.configVA)

	def keySave(self):
		for x in self["config"].list:
			x[1].save()
		self.configVA.save()
		if AutomaticVolumeAdjustmentPlugin.automaticvolumeadjustment is not None:
			AutomaticVolumeAdjustmentPlugin.automaticvolumeadjustment.initializeConfigValues(self.configVA, True) # submit config values
		self.close()

	def keyCancel(self):
		ConfigListScreen.cancelConfirm(self, True)
		

class AutomaticVolumeAdjustmentEntriesListConfigScreen(Screen):
	skin = """
		<screen position="center,center" size="550,400">
			<widget render="Label" source="name" position="5,0" size="350,50" font="Regular;20" halign="left"/>
			<widget render="Label" source="adjustvalue" position="355,0" size="200,50" font="Regular;20" halign="left"/>
			<widget name="entrylist" position="0,50" size="550,300" scrollbarMode="showOnDemand"/>
			<widget render="Label" source="key_red" position="0,350" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="140,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_yellow" position="280,350" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="yellow" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_blue" position="420,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<ePixmap position="0,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="420,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session, configVA):
		Screen.__init__(self, session)
		self.title = _("Automatic Volume Adjustment - Service Config")
		self["name"] = StaticText(_("Servicename"))
		self["adjustvalue"] = StaticText(_("Adjustment value"))
		self["key_red"] = StaticText(_("Add"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("Edit"))
		self["key_blue"] = StaticText(_("Delete"))
		self["entrylist"] = AutomaticVolumeAdjustmentEntryList([])
		self["actions"] = ActionMap(["WizardActions","MenuActions","ShortcutActions"],
			{
			 "ok"	:	self.keyOK,
			 "back"	:	self.keyClose,
			 "red"	:	self.keyRed,
			 "green":	self.keyClose,
			 "yellow":	self.keyYellow,
			 "blue": 	self.keyDelete,
			 }, -1)
		self["entrylist"].setConfig(configVA)
		self.updateList()

	def updateList(self):
		self["entrylist"].buildList()

	def keyClose(self):
		self.close(-1, None)

	def keyRed(self):
		self.session.openWithCallback(self.updateList,AutomaticVolumeAdjustmentEntryConfigScreen,None, self["entrylist"].configVA)

	def keyOK(self):
		try:sel = self["entrylist"].l.getCurrentSelection()[0]
		except: sel = None
		self.close(self["entrylist"].getCurrentIndex(), sel)

	def keyYellow(self):
		try:sel = self["entrylist"].l.getCurrentSelection()[0]
		except: sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.updateList,AutomaticVolumeAdjustmentEntryConfigScreen,sel, self["entrylist"].configVA)

	def keyDelete(self):
		try:sel = self["entrylist"].l.getCurrentSelection()[0]
		except: sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Do you really want to delete this entry?"))

	def deleteConfirm(self, result):
		if not result:
			return
		sel = self["entrylist"].l.getCurrentSelection()[0]
		self["entrylist"].configVA.remove(sel)
		if AutomaticVolumeAdjustmentPlugin.automaticvolumeadjustment is not None:
			AutomaticVolumeAdjustmentPlugin.automaticvolumeadjustment.initializeConfigValues(self["entrylist"].configVA, True) # submit config values
		self.updateList()

class AutomaticVolumeAdjustmentEntryList(MenuList):
	def __init__(self, list, enableWrapAround = True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 18))
		self.configVA = None

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(20)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()
		
	def setConfig(self, configVA):
		self.configVA = configVA
		
	def buildList(self):
		list = []
		for c in self.configVA.config.Entries:
			c.name.value = ServiceReference(eServiceReference(c.servicereference.value)).getServiceName()
			res = [
				c,
				(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 350, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, c.name.value),
				(eListboxPythonMultiContent.TYPE_TEXT, 355, 0,200, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, str(c.adjustvalue.value)),
			]
			list.append(res)
		self.list = list
		self.l.setList(list)
		self.moveToIndex(0)

class AutomaticVolumeAdjustmentEntryConfigScreen(ConfigListScreen, Screen):
	skin = """
		<screen name="AutomaticVolumeAdjustmentEntryConfigScreen" position="center,center" size="550,400">
			<widget name="config" position="20,10" size="520,330" scrollbarMode="showOnDemand" />
			<ePixmap position="0,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="420,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />

			<widget source="key_red" render="Label" position="0,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="140,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, entry, configVA):
		Screen.__init__(self, session)
		self.title = _("Automatic Volume Adjustment - Entry Config")
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"cancel": self.keyCancel,
			"ok": self.keySelect,
		}, -2)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self.configVA = configVA
		if entry is None:
			self.newmode = 1
			self.current = self.configVA.initEntryConfig()
		else:
			self.newmode = 0
			self.current = entry
		self.list = [ ]
		self.service = getConfigListEntry(_("Servicename"), self.current.name)
		self.list.append(self.service)
		self.list.append(getConfigListEntry(_("Adjustment value"), self.current.adjustvalue))
		ConfigListScreen.__init__(self, self.list, session)
		
	def keySelect(self):
		cur = self["config"].getCurrent()
		if cur == self.service:
			self.session.openWithCallback(self.channelSelected, ConfigChannelSelection)
			
	def channelSelected(self, ref = None):
		if ref:
			self.current.name.value = ServiceReference(ref).getServiceName()
			self.current.servicereference.value = ref.toString()
			self.current.save()

	def keySave(self):
		if self.current.servicereference.value:
			if self.newmode == 1:
				self.configVA.config.entriescount.value = self.configVA.config.entriescount.value + 1
				self.configVA.config.entriescount.save()
			for x in self["config"].list:
				x[1].save()
			self.configVA.save()
			if AutomaticVolumeAdjustmentPlugin.automaticvolumeadjustment is not None:
				AutomaticVolumeAdjustmentPlugin.automaticvolumeadjustment.initializeConfigValues(self.configVA, True) # submit config values
			self.close()
		else:
			self.session.open(MessageBox, _("You must select a valid service!"), type = MessageBox.TYPE_INFO)

	def keyCancel(self):
		if self.newmode == 1:
			self.configVA.remove(self.current)
		ConfigListScreen.cancelConfirm(self, True)

class ConfigChannelSelection(SimpleChannelSelection):
	def __init__(self, session):
		SimpleChannelSelection.__init__(self, session, _("Channel Selection"))
		self.skinName = ["SimpleChannelSelection"]
		self["ChannelSelectEPGActions"] = ActionMap(["ChannelSelectEPGActions"],
		{
				"showEPGList": self.channelSelected
		})

	def channelSelected(self):
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.enterPath(ref)
		elif not (ref.flags & eServiceReference.isMarker):
			self.close(ref)