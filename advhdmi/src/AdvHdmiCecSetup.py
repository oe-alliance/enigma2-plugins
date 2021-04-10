# -*- coding: utf-8 -*-

# Screens
from __future__ import absolute_import
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Screens.Setup import SetupSummary
from Components.Button import Button

# for localized messages
from . import _

# Plugin
from Plugins.Plugin import PluginDescriptor
from Components.config import config, configfile, ConfigSelection, ConfigSubsection, getConfigListEntry, ConfigSubList, \
	ConfigClock, ConfigInteger, ConfigYesNo 
from Components.ConfigList import ConfigListScreen
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER
from Components.MenuList import MenuList
from Tools.BoundFunction import boundFunction

import six


class AdvHdmiCecSetup(Screen, ConfigListScreen):
	skin = """
		<screen name="adv_hdmi_setup" position="center,center" size="580,480" title="Advanced HDMI-Cec Setup" >
			<widget name="config" position="10,0" size="560,250" scrollbarMode="showOnDemand" enableWrapAround="1" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,250" zPosition="1" size="550,2" />
			<widget source="help" render="Label" position="5,250" size="580,120" font="Regular;21" />
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,430" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="10,430" size="140,40" transparent="1" halign="center" valign="center" zPosition="2" foregroundColor="white" font="Regular;18" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="180,430" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_green" position="180,430" size="140,40" transparent="1" halign="center" valign="center" zPosition="2" foregroundColor="white" font="Regular;18" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="350,430" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_yellow" position="350,430" size="140,40" transparent="1" halign="center" valign="center" zPosition="2" foregroundColor="white" font="Regular;18" />
			<ePixmap pixmap="skin_default/buttons/key_info.png" position="520,440" size="40,40" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.onChangedEntry = []
		
		self.list = []
		ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changed)
		
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Timespans"))
		self["key_info"] = StaticText()
		self["help"] = StaticText()
		
		self.getConfig()
		
		def selectionChanged():
			current = self["config"].getCurrent()
			if self["config"].current != current:
				if self["config"].current:
					self["config"].current[1].onDeselect(self.session)
				if current:
					current[1].onSelect(self.session)
				self["config"].current = current
			for x in self["config"].onSelectionChanged:
				x()

		self["config"].selectionChanged = selectionChanged
		self["config"].onSelectionChanged.append(self.updateHelp)
		
		# Actions
		self["actions"] = ActionMap(["SetupActions", "AdvHdmiConfigActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
				"yellowshort": self.EditTimeSpanEntries,
				"infoshort": self.showInfo,
				"nextBouquet": self.bouquetPlus,
				"prevBouquet": self.bouquetMinus,
			}
		)

		# Trigger change
		self.changed()
		self.onLayoutFinish.append(self._layoutFinished)
	
	def _layoutFinished(self):
		self.setTitle(_("Advanced HDMI-Cec Setup"))
		
	def getConfig(self):
		from Plugins.SystemPlugins.AdvHdmi.plugin import g_AdvHdmi_webif_available
		
		self.list = [ getConfigListEntry(_("partially disable HdmiCec"), config.plugins.AdvHdmiCec.enable, _("Partially disable HDMI-Cec?\nIt can be prevented only the signals that are sent from the Dreambox. Signals received by the Dreambox will not be prevented.")) ]
		if config.plugins.AdvHdmiCec.enable.value:
			self.list.append(getConfigListEntry(_("disable at GUI-start"), config.plugins.AdvHdmiCec.disable_after_enigmastart, _("Should HDMI-Cec be disabled when GUI service startup?")))
			if g_AdvHdmi_webif_available:
				self.list.append(getConfigListEntry(_("disable from webinterface"), config.plugins.AdvHdmiCec.disable_from_webif, _("Should HDMI-Cec be disabled when the commands are sent from the web interface?")))
			self.list.append(getConfigListEntry(_("enable Power On"), config.plugins.AdvHdmiCec.enable_power_on, _("Should HDMI-Cec be send on Power On?")))
			self.list.append(getConfigListEntry(_("enable Power Off"), config.plugins.AdvHdmiCec.enable_power_off, _("Should HDMI-Cec be send on Power Off?")))
			self.list.append(getConfigListEntry(_("enable debug"), config.plugins.AdvHdmiCec.debug, _("Schould debugmessages be printed?")))
		self.list.append(getConfigListEntry(_("show in"), config.plugins.AdvHdmiCec.show_in, _("Where should this setup be displayed?")))

		self["config"].list = self.list
		self["config"].setList(self.list)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.getConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.getConfig()

	def bouquetPlus(self):
		self["config"].instance.moveSelection(self["config"].instance.pageUp)

	def bouquetMinus(self):
		self["config"].instance.moveSelection(self["config"].instance.pageDown)

	def updateHelp(self):
		cur = self["config"].getCurrent()
		if cur:
			self["help"].text = cur[2]

	def keySave(self):
		for x in self["config"].list:
			x[1].save()

		self.close(self.session)

	def EditTimeSpanEntries(self):
		self.session.open(TimeSpanListScreen)

	def showInfo(self):
		from Plugins.SystemPlugins.AdvHdmi.plugin import advhdmiHooks, ADVHDMI_VERSION
		
		infoMsg = _("Version: ") + ADVHDMI_VERSION + "\n\n"
		if advhdmiHooks:
			infoMsg += _("Registered HDMI-Cec-Hooks:") + "\n"
			for hookKey, hook in six.iteritems(advhdmiHooks):
				infoMsg += _("Hook") + " '" + str(hookKey) + "':\n"
				infoMsg += str(hook.hookDescription) + "\n\n"
		else:
			infoMsg += _("No HDMI-Cec-Hooks are registered!")
		self.session.open(MessageBox, infoMsg, MessageBox.TYPE_INFO, title=_("Advanced HDMI-Cec Control"))

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass

# Timespans
class TimeSpanEntryList(MenuList):
	def __init__(self, list, enableWrapAround=True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))

	def postWidgetCreate(self, instance):
		MenuList.postWidgetCreate(self, instance)
		instance.setItemHeight(30)
		
	def buildList(self, entryselect=None):
		from Plugins.SystemPlugins.AdvHdmi.plugin import TimeSpanPresenter
		self.list=[]
		if entryselect == None:
			try:
				aktidx = self.l.getCurrentSelectionIndex()
			except:
				aktidx = 0
		else:
			aktidx = entryselect
		for e in config.plugins.AdvHdmiCec.Entries:
			entr = [e]
			presenter = TimeSpanPresenter(e)
			entr.append((eListboxPythonMultiContent.TYPE_TEXT, 5, 0, 165, 30, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, presenter[0]))
			entr.append((eListboxPythonMultiContent.TYPE_TEXT, 175, 0, 165, 30, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, presenter[1]))
			entr.append((eListboxPythonMultiContent.TYPE_TEXT, 345, 0, 80, 30, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, presenter[2]))
			entr.append((eListboxPythonMultiContent.TYPE_TEXT, 510, 0, 80, 30, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, presenter[3]))
			self.list.append(entr)
		self.l.setList(self.list)
		if aktidx >= config.plugins.AdvHdmiCec.entriescount.value:
			aktidx = (config.plugins.AdvHdmiCec.entriescount.value - 1)
		self.moveToIndex(aktidx)

class TimeSpanListScreen(Screen):
	skin = """
		<screen name="adv_hdmi_timespan_list" position="center,center" size="645,400" title="disable chronologically" >
			<widget name="fromwd" position="5,0" size="165,50" halign="left" font="Regular;21"/>
			<widget name="towd" position="175,0" size="165,50" halign="left" font="Regular;21"/>
			<widget name="begin" position="345,0" size="80,50" halign="left" font="Regular;21"/>
			<widget name="end" position="510,0" size="80,50" halign="left" font="Regular;21"/>
			<widget name="entrylist" position="5,50" size="635,300" scrollbarMode="showOnDemand"/>

			<widget name="key_red" position="5,350" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="170,350" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="green" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="335,350" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="yellow" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="500,350" zPosition="5" size="140,40" valign="center" halign="center" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<ePixmap name="red" position="5,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="170,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="335,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue" position="500,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self["fromwd"] = Button(_("From WD"))
		self["towd"] = Button(_("To WD"))
		self["begin"] = Button(_("From"))
		self["end"] = Button(_("To"))
		self["entrylist"] = TimeSpanEntryList([])

		self["key_red"] = Button(_("Add"))
		self["key_green"] = Button(_("Close"))
		self["key_yellow"] = Button(_("Edit"))
		self["key_blue"] = Button(_("Delete"))

		self["actions"] = ActionMap(["WizardActions", "MenuActions", "ShortcutActions"],
		{
			"ok": self.keyOK,
			"back": self.keyClose,
			"red": self.keyAdd,
			"green": self.keyClose,
			"yellow": self.keyEdit,
			"blue": self.keyDelete,
		}, -1)
		
		self._updateList()
		self.onLayoutFinish.append(self._layoutFinished)

	def _updateList(self, entryselect=None):		
		self["entrylist"].buildList(entryselect)

	def _layoutFinished(self):
		self.setTitle(_("Disable HDMI-CEC chronologically"))

	def keyClose(self):
		self.close(self.session)

	def keyOK(self):
		self.keyEdit()

	def keyAdd(self):
		self.session.open(TimeSpanConfigScreen, None, self._updateList)

	def keyEdit(self):
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		if sel is None:
			return
		self.session.openWithCallback(self._updateList, TimeSpanConfigScreen, sel)

	def keyDelete(self):
		try:
			sel = self["entrylist"].l.getCurrentSelection()[0]
		except:
			sel = None
		if sel is None:
			return
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this HDMI-Cec-Timespan Entry?"))

	def deleteConfirm(self, result):
		if not result:
			return
		sel = self["entrylist"].l.getCurrentSelection()[0]
		config.plugins.AdvHdmiCec.entriescount.value = config.plugins.AdvHdmiCec.entriescount.value - 1
		config.plugins.AdvHdmiCec.entriescount.save()
		config.plugins.AdvHdmiCec.Entries.remove(sel)
		config.plugins.AdvHdmiCec.Entries.save()
		config.plugins.AdvHdmiCec.save()
		configfile.save()
		self._updateList()

class TimeSpanConfigScreen(Screen, ConfigListScreen):
	skin = """
		<screen name="adv_hdmi_timespan_config" position="center,center" size="550,430" title="ignoreit" >
			<widget name="config" position="10,0" size="530,210" scrollbarMode="showOnDemand" enableWrapAround="1" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,210" zPosition="1" size="550,2" />
			<widget source="help" render="Label" position="5,220" size="550,120" font="Regular;21" />
			
			<widget source="key_red" render="Label" position="10,380" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="180,380" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="green" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<ePixmap name="red" position="10,380" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="180,380" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session, entry, callbackfnc=None):
		from .plugin import TimeSpanEntryInit
		self.session = session
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions"],
		{
			"red"   : self.keyCancel,
			"ok"    : self.keySave,
			"green" : self.keySave,
			"cancel": self.keyCancel
		}, -2)

		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["help"] = StaticText()

		if entry is None:
			self.newmode = 1
			self.current = TimeSpanEntryInit()
		else:
			self.newmode = 0
			self.current = entry
		
		self.callbackfnc = callbackfnc
			
		cfglist = [
			getConfigListEntry(_("from weekday"), self.current.fromWD, _("From which day of the week, HDMI-Cec should be disabled?")),
			getConfigListEntry(_("to weekday"), self.current.toWD, _("To what day of the week, HDMI-Cec should be disabled?")),
			getConfigListEntry(_("from (HH:MI)"), self.current.begin, _("At which time, HDMI-Cec should be disabled?")),
			getConfigListEntry(_("to (HH:MI)"), self.current.end, _("Until the time at which, HDMI-Cec should be disabled?"))
		]

		ConfigListScreen.__init__(self, cfglist, session)
		self["config"].onSelectionChanged.append(self._updateHelp)
		self.onLayoutFinish.append(self._layoutFinished)

	def _updateHelp(self):
		cur = self["config"].getCurrent()
		if cur:
			self["help"].text = cur[2]

	def _layoutFinished(self):
		self.setTitle(_("Edit HDMI-Cec-Timespan"))

	def keySave(self):
		entryselect = None
		if self.newmode == 1:
			entryselect = int(config.plugins.AdvHdmiCec.entriescount.value)
			config.plugins.AdvHdmiCec.entriescount.value = config.plugins.AdvHdmiCec.entriescount.value + 1
			config.plugins.AdvHdmiCec.entriescount.save()
		ConfigListScreen.keySave(self)
		config.plugins.AdvHdmiCec.save()
		configfile.save()		
		if self.callbackfnc is not None:
			self.onClose.append(boundFunction(self.callbackfnc, entryselect))
		self.close(entryselect)

	def keyCancel(self):
		if self.newmode == 1:
			config.plugins.AdvHdmiCec.Entries.remove(self.current)
		ConfigListScreen.cancelConfirm(self, True)

# functionality
def sessionstart(reason, **kwargs):
	global g_AdvHdmi_sessionstarted
	if reason == 0:
		g_AdvHdmi_sessionstarted = True
		
def autostart(reason, **kwargs):
	global g_AdvHdmi_sessionstarted
	if reason == 0:
		g_AdvHdmi_sessionstarted = True

def main(session, **kwargs):
	session.open(AdvHdmiCecSetup)

def showinSetup(menuid):
	if menuid != "system":
		return []
	return [(_("Advanced HDMI-Cec Setup"), main, "", 46)]

def Plugins(**kwargs):
	list = [
		PluginDescriptor(
			where=PluginDescriptor.WHERE_SESSIONSTART,
			fnc=sessionstart),
		PluginDescriptor(
			where=PluginDescriptor.WHERE_AUTOSTART,
			fnc=autostart)
	]
	if config.plugins.AdvHdmiCec.show_in.value == "system":
		list.append (PluginDescriptor(
			name="Advanced HDMI-Cec Control", 
			description=_("manage when HDMI Cec is enabled"), 
			where=PluginDescriptor.WHERE_MENU, 
			fnc=showinSetup)
		)
	if config.plugins.AdvHdmiCec.show_in.value == "plugin":
		list.append (PluginDescriptor(
			name="Advanced HDMI-Cec Control",
			description=_("manage when HDMI Cec is enabled"),
			where=PluginDescriptor.WHERE_PLUGINMENU,
			fnc=main,
			needsRestart=False)
		)
	if config.plugins.AdvHdmiCec.show_in.value == "extension":
		list.append (PluginDescriptor(
				name="Advanced HDMI-Cec Control",
				description=_("manage when HDMI Cec is enabled"),
				where=PluginDescriptor.WHERE_EXTENSIONSMENU,
				fnc=main,
				needsRestart=False)
		)
	
	return list


