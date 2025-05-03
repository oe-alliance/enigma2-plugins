# -*- coding: utf-8 -*-
#
#  PipServiceRelation E2
#
#  Coded by Dr.Best (c) 2011
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
from Screens.PictureInPicture import PictureInPicture
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChannelSelection import SimpleChannelSelection
from enigma import eServiceCenter, getBestPlayableServiceReference, eServiceReference, eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from ServiceReference import ServiceReference
from Tools.BoundFunction import boundFunction
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry, config, ConfigDirectory, NoSave

from os import path as os_path
from pickle import load as pickle_load, dump as pickle_dump
from enigma import eEnv

basePictureInPicture__init__ = None
CONFIG_FILE = eEnv.resolve('${libdir}/enigma2/python/Plugins/SystemPlugins/PiPServiceRelation/psr_config')


def getRelationDict():
	if os_path.exists(CONFIG_FILE):
		pkl_file = open(CONFIG_FILE, 'rb')
		if pkl_file:
			volumedict = pickle_load(pkl_file)
			pkl_file.close()
			return volumedict
	return {}


def saveRelationDict(dict):
	pkl_file = open(CONFIG_FILE, 'wb')
	if pkl_file:
		pickle_dump(dict, pkl_file)
		pkl_file.close()


def autostart_PictureInPicture(session, **kwargs):
	init_pipservicerelation()


def setup(session, **kwargs):
	session.open(PipServiceRelationSetup)


class PipServiceRelationSetup(Screen):
	skin = """
		<screen position="center,center" size="655,400">
			<widget render="Label" source="name" position="5,0" size="320,50" font="Regular;20" halign="left"/>
			<widget render="Label" source="relationname" position="330,0" size="320,50" font="Regular;20" halign="left"/>
			<widget name="entrylist" position="0,50" size="655,300" scrollbarMode="showOnDemand"/>
			<widget render="Label" source="key_red" position="0,350" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="140,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_yellow" position="280,350" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="yellow" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_blue" position="420,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<ePixmap position="0,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="420,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.title = _("PipServiceRelation - Config")
		self["name"] = StaticText(_("Service"))
		self["relationname"] = StaticText(_("Related PiP Service"))
		self["key_red"] = StaticText(_("Delete"))
		self["key_green"] = StaticText(_("Close"))
		self["key_yellow"] = StaticText(_("Add"))
		self["key_blue"] = StaticText(_("Edit"))
		self["entrylist"] = PipServiceRelationEntryList([])
		self["actions"] = ActionMap(["WizardActions", "MenuActions", "ShortcutActions"], {
			"ok": self.keyBlue,
			"back": self.keyClose,
			"red": self.keyDelete,
			"green": self.keyClose,
			"yellow": self.keyYellow,
			"blue": self.keyBlue,
		}, -1)
		self["entrylist"].setConfig(getRelationDict())
		self.updateList()

	def updateList(self):
		self["entrylist"].buildList()

	def keyClose(self):
		self.close()

	def keyBlue(self):
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.updateList, PipServiceRelationEntryConfigScreen, sel, self["entrylist"].configPSR)

	def keyYellow(self):
		self.session.openWithCallback(self.updateList, PipServiceRelationEntryConfigScreen, None, self["entrylist"].configPSR)

	def keyDelete(self):
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Do you really want to delete this entry?"))

	def deleteConfirm(self, result):
		if not result:
			return
		sel = self["entrylist"].l.getCurrentSelection()[0]
		del self["entrylist"].configPSR[sel[0]]
		saveRelationDict(self["entrylist"].configPSR)
		self.updateList()


class PipServiceRelationEntryList(MenuList):
	def __init__(self, list, enableWrapAround=True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 18))
		self.configPSR = None

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(20)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def setConfig(self, configPSR):
		self.configPSR = configPSR

	def buildList(self):
		list = []
		for c in self.configPSR.items():
			res = [
				c,
				(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 320, 20, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, ServiceReference(eServiceReference(c[0])).getServiceName()),
				(eListboxPythonMultiContent.TYPE_TEXT, 330, 0, 320, 20, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, ServiceReference(eServiceReference(c[1])).getServiceName()),
			]
			list.append(res)
		self.list = list
		self.l.setList(list)
		self.moveToIndex(0)


class PipServiceRelationEntryConfigScreen(ConfigListScreen, Screen):
	skin = """
		<screen name="PipServiceRelationEntryConfigScreen" position="center,center" size="550,400">
			<widget name="config" position="20,10" size="520,330" scrollbarMode="showOnDemand" />
			<ePixmap position="0,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="140,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="280,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="420,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />

			<widget source="key_red" render="Label" position="0,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="140,350" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, entry, configPSR):
		self.session = session
		Screen.__init__(self, session)
		self.title = _("PipServiceRelation - Entry Config")
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"cancel": self.keyCancel,
			"ok": self.keySelect,
		}, -2)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self.configPSR = configPSR
		self.entry = entry
		if entry is None:
			self.currentKey = None
			self.ref1 = NoSave(ConfigDirectory(default=_("Press OK to select a service")))
			self.ref2 = NoSave(ConfigDirectory(default=_("Press OK to select a related PiP service")))
		else:
			self.currentKey = entry[0]
			self.ref1 = NoSave(ConfigDirectory(default=ServiceReference(eServiceReference(entry[0])).getServiceName()))
			self.ref2 = NoSave(ConfigDirectory(default=ServiceReference(eServiceReference(entry[1])).getServiceName()))
		self.list = []
		self.serviceref1 = getConfigListEntry(_("Service"), self.ref1)
		self.serviceref2 = getConfigListEntry(_("Related Pip Service"), self.ref2)
		self.list.append(self.serviceref1)
		self.list.append(self.serviceref2)
		ConfigListScreen.__init__(self, self.list, session)

	def keySelect(self):
		cur = self["config"].getCurrent()
		if cur == self.serviceref1:
			index = 1
			descr = _("Channel Selection")
		else:
			index = 2
			if self.entry and self.entry[0]:
				sname = ServiceReference(eServiceReference(self.entry[0])).getServiceName()
			else:
				sname = ""
			descr = _("Related PiP service for %s") % sname
		self.session.openWithCallback(boundFunction(self.channelSelected, index), SimpleChannelSelection, descr)

	def channelSelected(self, index, ref=None):
		if ref:
			if self.entry:
				val1 = self.entry[0]
				val2 = self.entry[1]
			else:
				val1 = val2 = None
			if index == 1:
				self.entry = (ref.toString(), val2)
				self.ref1.value = ServiceReference(ref).getServiceName()
			else:
				self.entry = (val1, ref.toString())
				self.ref2.value = ServiceReference(ref).getServiceName()

	def keySave(self):
		if self.entry and self.entry[0] and self.entry[1]:
			if self.currentKey is not None:
				del self.configPSR[self.currentKey]
			self.configPSR[self.entry[0]] = self.entry[1]
			saveRelationDict(self.configPSR)
		self.close()

	def keyCancel(self):
		ConfigListScreen.cancelConfirm(self, True)


def init_pipservicerelation():
	global basePictureInPicture__init__, basePictureInPicture_playService
	if basePictureInPicture__init__ is None:
		basePictureInPicture__init__ = PictureInPicture.__init__
	PictureInPicture.__init__ = PictureInPicture__init__
	PictureInPicture.playService = playService


def PictureInPicture__init__(self, session):
	basePictureInPicture__init__(self, session)
	self.pipServiceRelation = getRelationDict()


def playService(self, service):
	current_service = service
	n_service = self.pipServiceRelation.get(service.toString(), None) if service is not None else None
	if n_service is not None:
		service = eServiceReference(n_service)
	if service and (service.flags & eServiceReference.isGroup):
		ref = getBestPlayableServiceReference(service, eServiceReference())
	else:
		ref = service
	if ref:
		self.pipservice = eServiceCenter.getInstance().play(ref)
		if self.pipservice and not self.pipservice.setTarget(1):
			self.pipservice.start()
			self.currentService = current_service
			return True
		else:
			self.pipservice = None
	return False


def Plugins(**kwargs):
	list = []
	list.append(PluginDescriptor(name="Setup PiPServiceRelation", description=_("setup for PiPServiceRelation"), where=[PluginDescriptor.WHERE_PLUGINMENU], icon="PiPServiceRelation.png", fnc=setup))
	list.append(PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=autostart_PictureInPicture))
	return list
