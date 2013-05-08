# -*- coding: utf-8 -*-

# Screens
from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Screens.Setup import SetupSummary

# for localized messages
from . import _

# Plugin
from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigYesNo, ConfigSelection, ConfigSubsection, ConfigClock, getConfigListEntry
from Components.ConfigList import ConfigListScreen

# for function
from time import localtime, mktime
from Components.HdmiCec import hdmi_cec
# overwrite functions
from Plugins.SystemPlugins.HdmiCec.plugin import Cec
from Plugins.Extensions.WebInterface.WebComponents.Sources.RemoteControl import RemoteControl
from Plugins.Extensions.WebInterface.WebComponents.Sources.PowerState import PowerState

global g_AdvHdmi_sessionstared
global g_AdvHdmi_fromwebif

now = localtime()
begin1 = mktime((now.tm_year, now.tm_mon, now.tm_mday, 1, 00, 0, now.tm_wday, now.tm_yday, now.tm_isdst))
end1 = mktime((now.tm_year, now.tm_mon, now.tm_mday, 6, 00, 0, now.tm_wday, now.tm_yday, now.tm_isdst))
begin2 = mktime((now.tm_year, now.tm_mon, now.tm_mday, 8, 00, 0, now.tm_wday, now.tm_yday, now.tm_isdst))
end2 = mktime((now.tm_year, now.tm_mon, now.tm_mday, 16, 00, 0, now.tm_wday, now.tm_yday, now.tm_isdst))

config.plugins.AdvHdmiCec = ConfigSubsection()
config.plugins.AdvHdmiCec.enable = ConfigYesNo(default = False)
config.plugins.AdvHdmiCec.disable_after_enigmastart = ConfigYesNo(default = False)
config.plugins.AdvHdmiCec.disable_from_webif = ConfigYesNo(default = False)
config.plugins.AdvHdmiCec.time_enable = ConfigYesNo(default = False)
config.plugins.AdvHdmiCec.fromWD = ConfigSelection(choices=[
		("0", _("Monday")),
		("1", _("Tuesday")),
		("2", _("Wednesday")),
		("3", _("Thursday")),
		("4", _("Friday")),
		("5", _("Saturday")),
		("6", _("Sunday")),
	], default = "0")
config.plugins.AdvHdmiCec.toWD = ConfigSelection(choices=[
		("0", _("Monday")),
		("1", _("Tuesday")),
		("2", _("Wednesday")),
		("3", _("Thursday")),
		("4", _("Friday")),
		("5", _("Saturday")),
		("6", _("Sunday")),
	], default = "6")
config.plugins.AdvHdmiCec.begin1 = ConfigClock(default = int(begin1))
config.plugins.AdvHdmiCec.end1 = ConfigClock(default = int(end1))
config.plugins.AdvHdmiCec.timespan2_enable = ConfigYesNo(default = False)
config.plugins.AdvHdmiCec.begin2 = ConfigClock(default = int(begin2))
config.plugins.AdvHdmiCec.end2 = ConfigClock(default = int(end2))
config.plugins.AdvHdmiCec.show_in = ConfigSelection(choices=[
		("system", _("systemmenue")),
		("plugin", _("pluginmenue")),
		("extension", _("extensions")),
	], default = "system")

class AdvHdmiCecSetup(Screen, ConfigListScreen):
	skin = """
		<screen name="menu_system" position="center,center" size="550,480" title="Advanced HDMI-Cec Setup" >
			<widget name="config" position="10,0" size="530,310" scrollbarMode="showOnDemand" enableWrapAround="1" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,310" zPosition="1" size="550,2" />
			<widget source="help" render="Label" position="5,320" size="550,120" font="Regular;21" />
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,430" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="10,430" size="140,40" transparent="1" halign="center" valign="center" zPosition="2" foregroundColor="white" font="Regular;18" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="180,430" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_green" position="180,430" size="140,40" transparent="1" halign="center" valign="center" zPosition="2" foregroundColor="white" font="Regular;18" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setup_title = _("Advanced HDMI-Cec Setup")
		self.onChangedEntry = []
		
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)
		
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
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
				"nextBouquet":self.bouquetPlus,
				"prevBouquet":self.bouquetMinus,
			}
		)

		# Trigger change
		self.changed()
	
	def getConfig(self):
		self.list = [ getConfigListEntry(_("partially disabel HdmiCec"), config.plugins.AdvHdmiCec.enable, _("Partially disabel HDMI-Cec?\nIt can be prevented only the signals that are sent from the Dreambox. Signals received by the Dreambox will not be prevented.")) ]
		if config.plugins.AdvHdmiCec.enable.value:
			self.list.append(getConfigListEntry(_("disable at GUI-start"), config.plugins.AdvHdmiCec.disable_after_enigmastart, _("Should HDMI-Cec be disabled when GUI service startup?")))
			self.list.append(getConfigListEntry(_("disable from webinterface"), config.plugins.AdvHdmiCec.disable_from_webif, _("Should HDMI-Cec be disabled when the commands are sent from the web interface?")))
			self.list.append(getConfigListEntry(_("disable chronologically"), config.plugins.AdvHdmiCec.time_enable, _("Should HDMI-Cec be disabled at certain times?")))
			if config.plugins.AdvHdmiCec.time_enable.value:
				self.list.append(getConfigListEntry(_("from weekday"), config.plugins.AdvHdmiCec.fromWD, _("From which day of the week, HDMI-Cec should be disabled?")))
				self.list.append(getConfigListEntry(_("to weekday"), config.plugins.AdvHdmiCec.toWD, _("To what day of the week, HDMI-Cec should be disabled?")))
				self.list.append(getConfigListEntry(_("from (HH:MI)"), config.plugins.AdvHdmiCec.begin1, _("At which time, HDMI-Cec should be disabled?")))
				self.list.append(getConfigListEntry(_("to (HH:MI)"), config.plugins.AdvHdmiCec.end1, _("Until the time at which, HDMI-Cec should be disabled?")))
				self.list.append(getConfigListEntry(_("use second timespan"), config.plugins.AdvHdmiCec.timespan2_enable, _("Do you want a further period of time to be used?")))
				if config.plugins.AdvHdmiCec.timespan2_enable.value:
					self.list.append(getConfigListEntry(_("from (HH:MI)"), config.plugins.AdvHdmiCec.begin2, _("Second timespan from")))
					self.list.append(getConfigListEntry(_("to (HH:MI)"), config.plugins.AdvHdmiCec.end2, _("Second timespan to")))
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

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass

def sessionstart(reason, **kwargs):
	global g_AdvHdmi_sessionstared
	if reason == 0:
		g_AdvHdmi_sessionstared = True
		
def autostart(reason, **kwargs):
	if reason == 0:
		g_AdvHdmi_sessionstared = True

def main(session, **kwargs):
	session.open(AdvHdmiCecSetup)

def showinSetup(menuid):
	if menuid != "system":
		return []
	return [(_("Advanced HDMI Cec Setup"), main, "", 46)]

def Plugins(**kwargs):
	global g_AdvHdmi_sessionstared
	global g_AdvHdmi_fromwebif
	g_AdvHdmi_sessionstared = False
	g_AdvHdmi_fromwebif = False
	
	list = [
		PluginDescriptor(
			where = PluginDescriptor.WHERE_SESSIONSTART,
			fnc = sessionstart),
		PluginDescriptor(
			where = PluginDescriptor.WHERE_AUTOSTART,
			fnc = autostart)
	]
	if config.plugins.AdvHdmiCec.show_in.value == "system":
		list.append (PluginDescriptor(
			name="Advanced HDMI Cec Control", 
			description=_("manage when HDMI Cec is enabled"), 
			where = PluginDescriptor.WHERE_MENU, 
			fnc=showinSetup)
		)
	if config.plugins.AdvHdmiCec.show_in.value == "plugin":
		list.append (PluginDescriptor(
			name = "Advanced HDMI Cec Control",
			description = _("manage when HDMI Cec is enabled"),
			where = PluginDescriptor.WHERE_PLUGINMENU,
			fnc = main,
			needsRestart = False)
		)
	if config.plugins.AdvHdmiCec.show_in.value == "extension":
		list.append (PluginDescriptor(
				name = "Advanced HDMI Cec Control",
				description = _("manage when HDMI Cec is enabled"),
				where = PluginDescriptor.WHERE_EXTENSIONSMENU,
				fnc = main,
				needsRestart = False)
		)
	
	return list
	
def checkTimespan(lt, begin, end):
	# Check if we span a day
	if begin[0] > end[0] or (begin[0] == end[0] and begin[1] >= end[1]):
		# Check if begin of event is later than our timespan starts
		if lt.tm_hour > begin[0] or (lt.tm_hour == begin[0] and lt.tm_min >= begin[1]):
			# If so, event is in our timespan
			return True
		# Check if begin of event is earlier than our timespan end
		if lt.tm_hour < end[0] or (lt.tm_hour == end[0] and lt.tm_min <= end[1]):
			# If so, event is in our timespan
			return True
		return False
	else:
		# Check if event begins earlier than our timespan starts
		if lt.tm_hour < begin[0] or (lt.tm_hour == begin[0] and lt.tm_min < begin[1]):
			# Its out of our timespan then
			return False
		# Check if event begins later than our timespan ends
		if lt.tm_hour > end[0] or (lt.tm_hour == end[0] and lt.tm_min > end[1]):
			# Its out of our timespan then
			return False
		return True

def AdvHdiCecDOIT():
	global g_AdvHdmi_sessionstared
	global g_AdvHdmi_fromwebif
	ret_val = True
	if config.plugins.AdvHdmiCec.enable.value:
		if g_AdvHdmi_sessionstared and config.plugins.AdvHdmiCec.disable_after_enigmastart.value:
			print "[AdvHdmiCec] prevent sending HDMICec, because of enigmastart"
			ret_val = False

		if ret_val and g_AdvHdmi_fromwebif and config.plugins.AdvHdmiCec.disable_from_webif.value:
			print "[AdvHdmiCec] prevent sending HDMICec, because it was from webif"
			ret_val = False
		
		if ret_val and config.plugins.AdvHdmiCec.time_enable.value:
			lt = localtime()
			if int(lt[6]) < int(config.plugins.AdvHdmiCec.fromWD.getValue()) \
				or int(lt[6]) > int(config.plugins.AdvHdmiCec.toWD.getValue()):
					print "[AdvHdmiCec] do sending HDMICec, because of weekday"
			else:
				if checkTimespan(lt, config.plugins.AdvHdmiCec.begin1.getValue(), config.plugins.AdvHdmiCec.end1.getValue()):
					print "[AdvHdmiCec] prevent sending HDMICec, because of timespan 1"
					ret_val = False
		
				if ret_val and config.plugins.AdvHdmiCec.timespan2_enable.getValue() \
					and checkTimespan(lt, config.plugins.AdvHdmiCec.begin2.getValue(), config.plugins.AdvHdmiCec.end2.getValue()):
						print "[AdvHdmiCec] prevent sending HDMICec, because of timespan 2"
						ret_val = False
	g_AdvHdmi_sessionstared = False
	g_AdvHdmi_fromwebif = False

	return ret_val

# Overwrite CEC-Base
def Cec_powerOn(self):
	if config.plugins.cec.sendpower.value and AdvHdiCecDOIT():
		print "[AdvHdmiCec] power on"
		hdmi_cec.otp_source_enable()

def Cec_powerOff(self):
	if config.plugins.cec.sendpower.value and AdvHdiCecDOIT():
		print "[AdvHdmiCec] power off"
		hdmi_cec.ss_standby()

# Overwrite WebIf
def RemoteControl_handleCommand(self, cmd):
	global g_AdvHdmi_fromwebif
	g_AdvHdmi_fromwebif = True
	self.cmd = cmd
	self.res = self.sendEvent()

def PowerState_handleCommand(self, cmd):
	global g_AdvHdmi_fromwebif
	g_AdvHdmi_fromwebif = True
	self.cmd = cmd

if config.plugins.AdvHdmiCec.enable.value:
	cec = Cec()
	print "[AdvHdmiCec] enabled"
	Cec.powerOn = Cec_powerOn
	Cec.powerOff = Cec_powerOff
	RemoteControl.handleCommand = RemoteControl_handleCommand
	PowerState.handleCommand = PowerState_handleCommand
