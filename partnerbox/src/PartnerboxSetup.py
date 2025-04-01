# -*- coding: utf-8 -*-
#
#  Partnerbox E2
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
from __future__ import absolute_import
from . import _
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER, getDesktop
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList
from Components.Button import Button
from Components.config import config
from Components.ActionMap import ActionMap, NumberActionMap
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import ConfigSubsection, ConfigSubList, ConfigIP, ConfigInteger, ConfigSelection, ConfigText, ConfigYesNo, getConfigListEntry, configfile
from xml.etree.cElementTree import tostring, parse
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from skin import fonts, parameters
from .PartnerboxFunctions import readSkin, applySkinVars, FHD, SCALE, SKINFILE, PLUGINPATH


def initPartnerboxEntryConfig():
	config.plugins.Partnerbox.Entries.append(ConfigSubsection())
	i = len(config.plugins.Partnerbox.Entries) - 1
	config.plugins.Partnerbox.Entries[i].name = ConfigText(default="Remote box", visible_width=50, fixed_size=False)
	config.plugins.Partnerbox.Entries[i].ip = ConfigIP(default=[192, 168, 0, 98])
	config.plugins.Partnerbox.Entries[i].port = ConfigInteger(default=80, limits=(1, 65555))
	config.plugins.Partnerbox.Entries[i].enigma = ConfigSelection(default="0", choices=[("0", _("Enigma 2")), ("1", _("Enigma 1"))])
	config.plugins.Partnerbox.Entries[i].password = ConfigText(default="root", visible_width=50, fixed_size=False)
	config.plugins.Partnerbox.Entries[i].useinternal = ConfigSelection(default="1", choices=[("0", _("use external")), ("1", _("use internal"))])
	config.plugins.Partnerbox.Entries[i].zaptoservicewhenstreaming = ConfigYesNo(default=True)
	return config.plugins.Partnerbox.Entries[i]


def initConfig():
	count = config.plugins.Partnerbox.entriescount.value
	if count != 0:
		i = 0
		while i < count:
			initPartnerboxEntryConfig()
			i += 1


class PartnerboxSetup(ConfigListScreen, Screen):
	skin = readSkin("PartnerboxSetup")

	def __init__(self, session, args=None):
		self.skin = applySkinVars(PartnerboxSetup.skin, {'picpath': PLUGINPATH + 'buttons/'})
		Screen.__init__(self, session)
		self.setTitle(_("Partnerbox Setup"))
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button(_("Partnerbox Entries"))
		self["key_blue"] = Button("")
		ConfigListScreen.__init__(self, [])
		self.initConfig()
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"cancel": self.keyClose,
			"red": self.keyClose,
			"ok": self.keySave,
			"yellow": self.PartnerboxEntries,
		}, -2)

	def initConfig(self):
		self.list = []
		self.list.append(getConfigListEntry(_("Show 'RemoteTimer' in Eventinfo menu"), config.plugins.Partnerbox.enablepartnerboxeventinfomenu))
		if config.plugins.Partnerbox.enablepartnerboxeventinfomenu.value:
			self.list.append(getConfigListEntry(_("Show 'RemoteTimer' in Event View context menu"), config.plugins.Partnerbox.enablepartnerboxeventinfocontextmenu))
		self.list.append(getConfigListEntry(_("Show 'RemoteTimer' in E-Menu"), config.plugins.Partnerbox.showremotetimerinextensionsmenu))
		self.list.append(getConfigListEntry(_("Show 'RemoteTV Player' in E-Menu"), config.plugins.Partnerbox.showremotetvinextensionsmenu))
		self.list.append(getConfigListEntry(_("Show 'Stream current Service' in E-Menu"), config.plugins.Partnerbox.showcurrentstreaminextensionsmenu))
		self.list.append(getConfigListEntry(_("Enable Partnerbox-Function in TimerEvent"), config.plugins.Partnerbox.enablepartnerboxintimerevent))
		if config.plugins.Partnerbox.enablepartnerboxintimerevent.value:
			self.list.append(getConfigListEntry(_("Enable first Partnerbox-entry in Timeredit as default"), config.plugins.Partnerbox.enabledefaultpartnerboxintimeredit))
			self.list.append(getConfigListEntry(_("Enable VPS-Function in TimerEvent"), config.plugins.Partnerbox.enablevpsintimerevent))
		self.list.append(getConfigListEntry(_("Enable Partnerbox-Function in EPGList"), config.plugins.Partnerbox.enablepartnerboxepglist))
		if config.plugins.Partnerbox.enablepartnerboxepglist.value:
			self.list.append(getConfigListEntry(_("Enable Red Button-Function in single/multi EPG"), config.plugins.Partnerbox.enablepartnerboxzapbuton))
			self.list.append(getConfigListEntry(_("Show duration time for event"), config.plugins.Partnerbox.showremaingepglist))
			self.list.append(getConfigListEntry(_("Show all icon for event in EPGList"), config.plugins.Partnerbox.allicontype))
		self.list.append(getConfigListEntry(_("Enable Partnerbox-Function in Channel Selector"), config.plugins.Partnerbox.enablepartnerboxchannelselector))
		self["config"].l.setList(self.list)

	def keySave(self):
		config.plugins.Partnerbox.showremotetvinextensionsmenu.save()
		config.plugins.Partnerbox.showcurrentstreaminextensionsmenu.save()
		config.plugins.Partnerbox.showremotetimerinextensionsmenu.save()
		config.plugins.Partnerbox.enablepartnerboxintimerevent.save()
		config.plugins.Partnerbox.enablepartnerboxepglist.save()
		config.plugins.Partnerbox.enablepartnerboxzapbuton.save()
		config.plugins.Partnerbox.enablepartnerboxchannelselector.save()
		config.plugins.Partnerbox.enabledefaultpartnerboxintimeredit.save()
		config.plugins.Partnerbox.enablepartnerboxeventinfomenu.save()
		config.plugins.Partnerbox.enablepartnerboxeventinfocontextmenu.save()
		config.plugins.Partnerbox.allicontype.save()
		config.plugins.Partnerbox.showremaingepglist.save()
		configfile.save()
		self.refreshPlugins()
		self.close(self.session)

	def keyClose(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close(self.session)

	def PartnerboxEntries(self):
		self.session.open(PartnerboxEntriesListConfigScreen)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.initConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.initConfig()

	def refreshPlugins(self):
		from Components.PluginComponent import plugins
		plugins.clearPluginList()
		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))


class PartnerboxEntriesListConfigScreen(Screen):
	skin = readSkin("PartnerboxEntriesListConfigScreen")

	def __init__(self, session, what=None):
		self.skin = applySkinVars(PartnerboxEntriesListConfigScreen.skin, {'picpath': PLUGINPATH + 'buttons/'})
		Screen.__init__(self, session)
		self.session = session
		self.setTitle(_("Partnerbox: List of Entries"))
		self["name"] = Button(_("Name"))
		self["ip"] = Button(_("IP"))
		self["port"] = Button(_("Port"))
		self["type"] = Button(_("Enigma Type"))
		self["key_red"] = Button(_("Add"))
		self["key_yellow"] = Button(_("Edit"))
		self["key_green"] = Button(_("Power"))
		self["key_blue"] = Button(_("Delete"))
		self["entrylist"] = PartnerboxEntryList([])
		self["actions"] = ActionMap(["WizardActions", "MenuActions", "ShortcutActions"],
		{
			"ok": self.keyOK,
			"back": self.keyClose,
			"red": self.keyRed,
			"yellow": self.keyYellow,
			"blue": self.keyDelete,
			"green": self.powerMenu,
		}, -1)
		self.what = what
		self.onLayoutFinish.append(self.updateList)

	def updateList(self):
		self["entrylist"].buildList()

	def keyClose(self):
		self.close(self.session, self.what, None)

	def keyRed(self):
		self.session.openWithCallback(self.updateList, PartnerboxEntryConfigScreen, None)

	def keyOK(self):
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		nr = int(config.plugins.Partnerbox.entriescount.value)
		if nr > 1 and self.what == 2 or nr >= 1 and self.what is None:
			from .plugin import RemoteTimer
			self.session.open(RemoteTimer, sel)
		else:
			self.close(self.session, self.what, sel)

	def keyYellow(self):
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.updateList, PartnerboxEntryConfigScreen, sel)

	def keyDelete(self):
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this Partnerbox Entry?"))

	def deleteConfirm(self, result):
		if not result:
			return
		sel = self["entrylist"].l.getCurrentSelection()[0]
		config.plugins.Partnerbox.entriescount.value = config.plugins.Partnerbox.entriescount.value - 1
		config.plugins.Partnerbox.entriescount.save()
		config.plugins.Partnerbox.Entries.remove(sel)
		config.plugins.Partnerbox.Entries.save()
		config.plugins.Partnerbox.save()
		configfile.save()
		self.updateList()

	def powerMenu(self):
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		if sel is None:
			return
		menu = []
		menu.append((_("Wakeup"), 0))
		menu.append((_("Standby"), 1))
		menu.append((_("Restart enigma"), 2))
		menu.append((_("Restart"), 3))
		if int(sel.enigma.value) == 0:
			menu.append((_("Toggle Standby"), 4))
			menu.append((_("Deep Standby"), 5))
		else:
			menu.append((_("Shutdown"), 4))
		from Screens.ChoiceBox import ChoiceBox
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=(_("Select operation for partnerbox") + ": " + "%s" % (sel.name.value)), list=menu)

	def menuCallback(self, choice):
		if choice is None:
			return
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		if sel is None:
			return
		password = sel.password.value
		username = "root"
		ip = "%d.%d.%d.%d" % tuple(sel.ip.value)
		port = sel.port.value
		http = "http://%s:%d" % (ip, port)
		enigma_type = int(sel.enigma.value)
		sCommand = http
		sCommand += enigma_type and "/cgi-bin/admin?command=" or "/web/powerstate?newstate="
		if choice[1] == 0:
			sCommand += enigma_type and "wakeup" or "4"
		elif choice[1] == 1:
			sCommand += enigma_type and "standby" or "5"
		elif choice[1] == 2:
			sCommand += enigma_type and "restart" or "3"
		elif choice[1] == 3:
			sCommand += enigma_type and "reboot" or "2"
		elif choice[1] == 4:
			sCommand += enigma_type and "shutdown" or "0"
		elif choice[1] == 5:
			if enigma_type:
				return
			sCommand += "1"
		else:
			return
		from .PartnerboxFunctions import sendPartnerBoxWebCommand
		sendPartnerBoxWebCommand(sCommand, None, 3, username, password)


class PartnerboxEntryList(MenuList):
	def __init__(self, list, enableWrapAround=True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		font = fonts.get("PartnerBoxEntryList0", ("Regular", int(20 * SCALE), int(20 * SCALE)))
		self.l.setFont(0, gFont(font[0], font[1]))
		self.ItemHeight = int(font[2])
		font = fonts.get("PartnerBoxEntryList1", ("Regular", int(18 * SCALE)))
		self.l.setFont(1, gFont(font[0], font[1]))

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(self.ItemHeight)

	def buildList(self):
		self.list = []
		for c in config.plugins.Partnerbox.Entries:
			res = [c]
			x, y, w, h = parameters.get("PartnerBoxEntryListName", (int(5 * SCALE), 0, int(200 * SCALE), int(24 * SCALE)))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(c.name.value)))
			ip = "%d.%d.%d.%d" % tuple(c.ip.value)
			x, y, w, h = parameters.get("PartnerBoxEntryListIP", (int(214 * SCALE), 0, int(230 * SCALE), int(24 * SCALE)))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(ip)))
			port = "%d" % (c.port.value)
			x, y, w, h = parameters.get("PartnerBoxEntryListPort", (int(400 * SCALE), 0, int(70 * SCALE), int(24 * SCALE)))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(port)))
			if int(c.enigma.value) == 0:
				e_type = "Enigma2"
			else:
				e_type = "Enigma1"
			x, y, w, h = parameters.get("PartnerBoxEntryListType", (int(550 * SCALE), 0, int(100 * SCALE), int(24 * SCALE)))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, str(e_type)))
			self.list.append(res)
		self.l.setList(self.list)
		self.moveToIndex(0)


class PartnerboxEntryConfigScreen(ConfigListScreen, Screen):
	skin = readSkin("PartnerboxEntryConfigScreen")

	def __init__(self, session, entry):
		self.session = session
		self.skin = applySkinVars(PartnerboxEntryConfigScreen.skin, {'picpath': PLUGINPATH + 'buttons/'})
		Screen.__init__(self, session)
		self.setTitle(_("Partnerbox: Edit Entry"))
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
			self.current = initPartnerboxEntryConfig()
		else:
			self.newmode = 0
			self.current = entry

		cfglist = [
			getConfigListEntry(_("Name"), self.current.name),
			getConfigListEntry(_("IP"), self.current.ip),
			getConfigListEntry(_("Port"), self.current.port),
			getConfigListEntry(_("Enigma Type"), self.current.enigma),
			getConfigListEntry(_("Password"), self.current.password),
			getConfigListEntry(_("Servicelists/EPG"), self.current.useinternal),
			getConfigListEntry(_("Zap to service when streaming"), self.current.zaptoservicewhenstreaming)
		]

		ConfigListScreen.__init__(self, cfglist, session)

	def keySave(self):
		if self.newmode == 1:
			config.plugins.Partnerbox.entriescount.value = config.plugins.Partnerbox.entriescount.value + 1
			config.plugins.Partnerbox.entriescount.save()
		ConfigListScreen.keySave(self)
		config.plugins.Partnerbox.save()
		configfile.save()
		self.close()

	def keyCancel(self):
		if self.newmode == 1:
			config.plugins.Partnerbox.Entries.remove(self.current)
		ConfigListScreen.cancelConfirm(self, True)

	def keyDelete(self):
		if self.newmode == 1:
			self.keyCancel()
		else:
			self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this Partnerbox Entry?"))

	def deleteConfirm(self, result):
		if not result:
			return
		config.plugins.Partnerbox.entriescount.value = config.plugins.Partnerbox.entriescount.value - 1
		config.plugins.Partnerbox.entriescount.save()
		config.plugins.Partnerbox.Entries.remove(self.current)
		config.plugins.Partnerbox.Entries.save()
		config.plugins.Partnerbox.save()
		configfile.save()
		self.close()
