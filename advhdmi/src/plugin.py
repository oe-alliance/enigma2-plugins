# -*- coding: utf-8 -*-

from traceback import print_exc
from sys import stdout, exc_info
from . import _

# Plugin
from Plugins.Plugin import PluginDescriptor
from Components.config import config, configfile, ConfigSelection, ConfigSubsection, getConfigListEntry, ConfigSubList, \
	ConfigClock, ConfigInteger, ConfigYesNo
from Components.ConfigList import ConfigListScreen

# for function
from time import localtime, mktime
from Components.HdmiCec import hdmi_cec

from boxbranding import getImageDistro

def _print(outtxt):
	ltim = localtime()
	headerstr = "[AdvHdmiCec] %04d%02d%02d-%02d%02d%02d " %(ltim[0],ltim[1],ltim[2],ltim[3],ltim[4],ltim[5])
	outtxt = headerstr + outtxt
	print outtxt

try:
	from Plugins.SystemPlugins.AdvHdmi.AdvHdmiCecSetup import AdvHdmiCecSetup
	g_AdvHdmi_setup_available = True
except ImportError:
	g_AdvHdmi_setup_available = False
	_print("error while loading AdvHdmiCecSetup")
	print_exc(file=stdout)

# overwrite functions
from Plugins.SystemPlugins.HdmiCec.plugin import Cec
try:
	from Plugins.Extensions.WebInterface.WebComponents.Sources.RemoteControl import RemoteControl
	from Plugins.Extensions.WebInterface.WebComponents.Sources.PowerState import PowerState
	g_AdvHdmi_webif_available = True
except ImportError:
	_print("No Webinterface-Plugin installed")
	g_AdvHdmi_webif_available = False

WEEKDAYS = [
	_("Monday"),
	_("Tuesday"),
	_("Wednesday"),
	_("Thursday"),
	_("Friday"),
	_("Saturday"),
	_("Sunday")]

# Timespans
def initTimeSpanEntryList():
	count = config.plugins.AdvHdmiCec.entriescount.value
	if count != 0:
		i = 0
		while i < count:
			TimeSpanEntryInit()
			i += 1

def TimeSpanEntryInit():
	now = localtime()
	begin = mktime((now.tm_year, now.tm_mon, now.tm_mday, 8, 00, 0, now.tm_wday, now.tm_yday, now.tm_isdst))
	end = mktime((now.tm_year, now.tm_mon, now.tm_mday, 16, 00, 0, now.tm_wday, now.tm_yday, now.tm_isdst))

	config.plugins.AdvHdmiCec.Entries.append(ConfigSubsection())
	i = len(config.plugins.AdvHdmiCec.Entries) -1
	config.plugins.AdvHdmiCec.Entries[i].fromWD = ConfigSelection(choices=[
		("0", WEEKDAYS[0]),
		("1", WEEKDAYS[1]),
		("2", WEEKDAYS[2]),
		("3", WEEKDAYS[3]),
		("4", WEEKDAYS[4]),
		("5", WEEKDAYS[5]),
		("6", WEEKDAYS[6]),
	], default = "0")
	config.plugins.AdvHdmiCec.Entries[i].toWD = ConfigSelection(choices=[
		("0", WEEKDAYS[0]),
		("1", WEEKDAYS[1]),
		("2", WEEKDAYS[2]),
		("3", WEEKDAYS[3]),
		("4", WEEKDAYS[4]),
		("5", WEEKDAYS[5]),
		("6", WEEKDAYS[6]),
	], default = "6")
	config.plugins.AdvHdmiCec.Entries[i].begin = ConfigClock(default = int(begin))
	config.plugins.AdvHdmiCec.Entries[i].end = ConfigClock(default = int(end))
	return config.plugins.AdvHdmiCec.Entries[i]

config.plugins.AdvHdmiCec = ConfigSubsection()
config.plugins.AdvHdmiCec.enable = ConfigYesNo(default = False)
config.plugins.AdvHdmiCec.debug = ConfigYesNo(default = False)
config.plugins.AdvHdmiCec.enable_power_on = ConfigYesNo(default = True)
config.plugins.AdvHdmiCec.enable_power_off = ConfigYesNo(default = True)
config.plugins.AdvHdmiCec.disable_after_enigmastart = ConfigYesNo(default = False)
config.plugins.AdvHdmiCec.disable_from_webif = ConfigYesNo(default = False)
config.plugins.AdvHdmiCec.entriescount =  ConfigInteger(0)
config.plugins.AdvHdmiCec.Entries = ConfigSubList()
config.plugins.AdvHdmiCec.show_in = ConfigSelection(choices=[
		("system", _("systemmenue")),
		("plugin", _("pluginmenue")),
		("extension", _("extensions")),
	], default = "system")
initTimeSpanEntryList()

ADVHDMI_VERSION = "1.4.3"

# HDMI-Hook-Events
# To implement a hook, just instantiate a AdvHdmiCecIF,
# and overwrite the methods before_event and/or after_event

# Events with boolean-return, that means if the CEC-signal has to be send / handled
ADVHDMI_BEFORE_POWERON = "BEFORE_POWERON"
ADVHDMI_BEFORE_POWEROFF = "BEFORE_POWEROFF"
ADVHDMI_BEFORE_RECEIVED_STANDBY = "BEFORE_RECEIVED_STANDBY"
ADVHDMI_BEFORE_RECEIVED_NOWACTIVE = "BEFORE_RECEIVED_NOWACTIVE"
# Events without return-value
ADVHDMI_AFTER_POWERON = "AFTER_POWERON"
ADVHDMI_AFTER_POWEROFF = "AFTER_POWEROFF"
ADVHDMI_AFTER_RECEIVED_STANDBY = "AFTER_RECEIVED_STANDBY"
ADVHDMI_AFTER_RECEIVED_NOWACTIVE = "AFTER_RECEIVED_NOWACTIVE"

# registered Hooks
advhdmiHooks = {}

def callHook(advhdmi_event):
	if config.plugins.AdvHdmiCec.debug.value: _print("Debug: call Hooks for Event '" + str(advhdmi_event) + "'")
	if advhdmiHooks:
		for hookKey,hook in advhdmiHooks.iteritems():
			if config.plugins.AdvHdmiCec.debug.value: _print("Debug: call Hook '" + str(hookKey) + "'")
			try:
				if advhdmi_event in (ADVHDMI_BEFORE_POWERON, ADVHDMI_BEFORE_POWEROFF, ADVHDMI_BEFORE_RECEIVED_STANDBY, ADVHDMI_BEFORE_RECEIVED_NOWACTIVE):
					if not hook.before_event(advhdmi_event):
						_print("Hook '" + str(hookKey) + "' prevents sending HDMI-Cec-signal!")
						return False
				else:
					hook.after_event(advhdmi_event)
			except:
				_print("Error while calling Hook " + str(hookKey))
				print_exc(file=stdout)
	if advhdmi_event in (ADVHDMI_BEFORE_POWERON, ADVHDMI_BEFORE_POWEROFF, ADVHDMI_BEFORE_RECEIVED_STANDBY, ADVHDMI_BEFORE_RECEIVED_NOWACTIVE):
		return True

def TimeSpanPresenter(confsection):
	presenter = [
		WEEKDAYS[int(confsection.fromWD.value)],
		WEEKDAYS[int(confsection.toWD.value)] ]
	timestr = "%02d:%02d" % tuple(confsection.begin.value)
	presenter.append(str(timestr))
	timestr = "%02d:%02d" % tuple(confsection.end.value)
	presenter.append(str(timestr))
	return presenter

# functionality
def autostart(reason, **kwargs):
	global g_AdvHdmi_sessionstarted
	if reason == 0:
		g_AdvHdmi_sessionstarted = True

def main(session, **kwargs):
	global g_AdvHdmi_setup_available
	if g_AdvHdmi_setup_available:
		session.open(AdvHdmiCecSetup)

def showinSetup(menuid):
	if getImageDistro() in ('openhdf'):
		if menuid != "video_menu":
			return [ ]
	else:
		if menuid != "system":
			return []
	return [(_("Advanced HDMI-Cec Setup"), main, "", 46)]

def Plugins(**kwargs):
	list = [
		PluginDescriptor(
			where = PluginDescriptor.WHERE_AUTOSTART,
			fnc = autostart)
	]
	if config.plugins.AdvHdmiCec.show_in.value == "system":
		list.append (PluginDescriptor(
			name="Advanced HDMI-Cec Control",
			description=_("manage when HDMI Cec is enabled"),
			where = PluginDescriptor.WHERE_MENU,
			fnc=showinSetup)
		)
	if config.plugins.AdvHdmiCec.show_in.value == "plugin":
		list.append (PluginDescriptor(
			name = "Advanced HDMI-Cec Control",
			description = _("manage when HDMI Cec is enabled"),
			where = PluginDescriptor.WHERE_PLUGINMENU,
			fnc = main,
			needsRestart = False)
		)
	if config.plugins.AdvHdmiCec.show_in.value == "extension":
		list.append (PluginDescriptor(
				name = "Advanced HDMI-Cec Control",
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

def AdvHdmiCecDOIT():
	global g_AdvHdmi_sessionstarted
	global g_AdvHdmi_fromwebif
	ret_val = True
	if config.plugins.AdvHdmiCec.enable.value:
		if g_AdvHdmi_sessionstarted and config.plugins.AdvHdmiCec.disable_after_enigmastart.value:
			_print("prevent sending HDMICec, because of enigmastart")
			ret_val = False

		if ret_val and g_AdvHdmi_fromwebif and config.plugins.AdvHdmiCec.disable_from_webif.value:
			_print("prevent sending HDMICec, because it was from webif")
			ret_val = False

		if ret_val and int(config.plugins.AdvHdmiCec.entriescount.value) > 0:
			lt = localtime()
			for e in config.plugins.AdvHdmiCec.Entries:
				entr = [e]
				if config.plugins.AdvHdmiCec.debug.value:
					presenter = TimeSpanPresenter(e)
					_print("Debug: Checking timespan '" + ", ".join( str(x) for x in presenter ) + "'")
				if int(e.fromWD.getValue()) <=  int(lt[6]) \
					and int(e.toWD.getValue()) >= int(lt[6]) :
					presenter = TimeSpanPresenter(e)
					if checkTimespan(lt, e.begin.getValue(), e.end.getValue()):
						_print("prevent sending HDMICec, because of timespan '" + ", ".join( str(x) for x in presenter ) + "'")
						ret_val = False
					else:
						if config.plugins.AdvHdmiCec.debug.value: _print("Debug: Local Time is not between " + str(presenter[2]) + " and " + str(presenter[3]))
				else:
					if config.plugins.AdvHdmiCec.debug.value: _print("Debug: Local weekday (" + str(lt[6]) + ") is not between " + str(presenter[0]) + " and " + str(presenter[1]))
				if not ret_val:
					if config.plugins.AdvHdmiCec.debug.value: _print("Debug: Found matching Timespan, exit loop!")
					break
	g_AdvHdmi_sessionstarted = False
	g_AdvHdmi_fromwebif = False

	return ret_val

# Overwrite CEC-Base
def Cec__receivedStandby(self):
	if config.cec.receivepower.value:
		from Screens.Standby import Standby, inStandby
		if not inStandby and self.session.current_dialog and self.session.current_dialog.ALLOW_SUSPEND and self.session.in_exec:
			if callHook(ADVHDMI_BEFORE_RECEIVED_STANDBY):
				self.session.open(Standby)
				callHook(ADVHDMI_AFTER_RECEIVED_STANDBY)

def Cec__receivedNowActive(self):
	if config.cec.receivepower.value:
		from Screens.Standby import inStandby
		if inStandby != None:
			if callHook(ADVHDMI_BEFORE_RECEIVED_NOWACTIVE):
				inStandby.Power()
				callHook(ADVHDMI_AFTER_RECEIVED_NOWACTIVE)

def Cec_powerOn(self):
	global g_AdvHdmi_initalized
	if config.cec.sendpower.value:
		if self.session.shutdown:
			self.idle_to_standby = True
		else:
			if config.plugins.AdvHdmiCec.enable_power_on.value and AdvHdmiCecDOIT():
				g_AdvHdmi_initalized = True
				if callHook(ADVHDMI_BEFORE_POWERON):
					_print("power on")
					hdmi_cec.otp_source_enable()
					callHook(ADVHDMI_AFTER_POWERON)

def Cec_powerOff(self):
	global g_AdvHdmi_initalized
	if config.cec.sendpower.value and config.plugins.AdvHdmiCec.enable_power_off.value and AdvHdmiCecDOIT():
		if callHook(ADVHDMI_BEFORE_POWEROFF):
			_print("power off")
			if not g_AdvHdmi_initalized:
				_print("Workaround: enable Hdmi-Cec-Source (^=poweron)")
				hdmi_cec.otp_source_enable()
			hdmi_cec.ss_standby()
			callHook(ADVHDMI_AFTER_POWEROFF)

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

g_AdvHdmi_sessionstarted = False
g_AdvHdmi_fromwebif = False
g_AdvHdmi_initalized = False

if config.plugins.AdvHdmiCec.enable.value:
	_print("enabled")
	Cec.__receivedStandby = Cec__receivedStandby
	Cec.__receivedNowActive = Cec__receivedNowActive
	Cec.powerOn = Cec_powerOn
	Cec.powerOff = Cec_powerOff
	if g_AdvHdmi_webif_available:
		RemoteControl.handleCommand = RemoteControl_handleCommand
		PowerState.handleCommand = PowerState_handleCommand
