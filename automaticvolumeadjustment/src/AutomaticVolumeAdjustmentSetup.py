# -*- coding: utf-8 -*-
#
#  AutomaticVolumeAdjustment E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2010
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
# for localized messages
from . import _

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER, eServiceReference
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChannelSelection import SimpleChannelSelection
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry, config
from ServiceReference import ServiceReference
from AutomaticVolumeAdjustment import AutomaticVolumeAdjustment
from AutomaticVolumeAdjustmentConfig import AutomaticVolumeAdjustmentConfig

		
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
		self["key_blue"] = StaticText()
		self.configVA = AutomaticVolumeAdjustmentConfig()
		self.automaticVolumeAdjustmentInstance = AutomaticVolumeAdjustment.instance
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = session)
		self.createSetup("config")
		
	def createSetup(self, widget):
		self.list = []
		self.config_enable = getConfigListEntry(_("Enable"), self.configVA.config.enable)
		self.list.append(self.config_enable)
		if self.configVA.config.enable.value:
			self.config_modus = getConfigListEntry(_("Mode"), self.configVA.config.modus)
			self.list.append(self.config_modus)
			if self.configVA.config.modus.value == "0":
				self.list.append(getConfigListEntry(_("Default adjustment for AC3/DTS"), self.configVA.config.adustvalue))
				self.list.append(getConfigListEntry(_("Max. volume for MPEG audio"), self.configVA.config.mpeg_max_volume))
				self["key_blue"].text = _("Services")
			else:
				self["key_blue"].text = ""
			self.list.append(getConfigListEntry(_("Show volume bar on volume change"), self.configVA.config.show_volumebar))
		else:
			self.config_modus = None
		self[widget].list = self.list
		self[widget].l.setList(self.list)
	
	def newConfig(self):
		if self["config"].getCurrent() in (self.config_enable, self.config_modus):
			self.createSetup("config")

	def keyLeft(self):
			ConfigListScreen.keyLeft(self)
			self.newConfig()

	def keyRight(self):
			ConfigListScreen.keyRight(self)
			self.newConfig()
		
	def blue(self):
		if self.configVA.config.modus.value == "0":
			self.session.open(AutomaticVolumeAdjustmentEntriesListConfigScreen, self.configVA)

	def keySave(self):
		for x in self["config"].list:
			x[1].save()
		self.configVA.save()
		if self.automaticVolumeAdjustmentInstance is not None:
			self.automaticVolumeAdjustmentInstance.initializeConfigValues(self.configVA, True) # submit config values
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
		self["name"] = StaticText(_("Service"))
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
		self.automaticVolumeAdjustmentInstance = AutomaticVolumeAdjustment.instance
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
		if self.automaticVolumeAdjustmentInstance is not None:
			self.automaticVolumeAdjustmentInstance.initializeConfigValues(self["entrylist"].configVA, True) # submit config values
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
		self.session = session
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
			self.currentvalue = self.current.adjustvalue.value
		else:
			self.newmode = 0
			self.current = entry
			self.currentref = entry.servicereference.value
			self.currentvalue = entry.adjustvalue.value
		self.list = [ ]
		self.service = getConfigListEntry(_("Service"), self.current.name)
		self.list.append(self.service)
		self.adjustValue = getConfigListEntry(_("Adjustment value"), self.current.adjustvalue)
		self.list.append(self.adjustValue)
		ConfigListScreen.__init__(self, self.list, session)
		self.automaticVolumeAdjustmentInstance = AutomaticVolumeAdjustment.instance
		
	def keySelect(self):
		cur = self["config"].getCurrent()
		if cur == self.service:
			self.session.openWithCallback(self.channelSelected, SimpleChannelSelection, _("Channel Selection"))
			
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
			if self.automaticVolumeAdjustmentInstance is not None:
				self.automaticVolumeAdjustmentInstance.initializeConfigValues(self.configVA, True) # submit config values
			self.close()
		else:
			self.session.open(MessageBox, _("You must select a valid service!"), type = MessageBox.TYPE_INFO)

	def keyCancel(self):
		if self.newmode == 1:
			self.configVA.config.Entries.remove(self.current)
			self.configVA.config.Entries.save()
		else:
			self.current.servicereference.value = self.currentref
			self.current.adjustvalue.value = self.currentvalue
			self.current.save()
		ConfigListScreen.cancelConfirm(self, True)
