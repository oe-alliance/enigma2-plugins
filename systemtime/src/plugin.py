from . import _
from enigma import eTimer, eDVBLocalTimeHandler, eEPGCache, getDesktop
try:
	from Tools.StbHardware import setRTCtime
except:
	from Tools.DreamboxHardware import setRTCtime
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, ConfigSelection, getConfigListEntry, ConfigYesNo, configfile, ConfigText, ConfigInteger
from Components.ConfigList import ConfigListScreen
from Components.Input import Input
from Components.Label import Label
from Plugins.Plugin import PluginDescriptor
from Screens.Console import Console
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Screens.Screen import Screen
from Tools.Directories import fileExists
from NTPSyncPoller import NTPSyncPoller
import os
import time
from calendar import isleap


config.plugins.SystemTime = ConfigSubsection()
config.plugins.SystemTime.choiceSystemTime = ConfigSelection(default="0", choices=[("0", _("Transponder")), ("1", _("NTP"))])
config.plugins.SystemTime.useNTPminutes = ConfigSelection(default="60", choices=[("5", _("5 mins")), ("15", _("15 mins")), ("30", _("30 mins")), ("60", _("1 hour")), ("120", _("2 hours")), ("240", _("4 hours")), ("720", _("12 hours")), ("1440", _("24 hours")), ("2880", _("48 hours"))])
config.plugins.SystemTime.syncNTPcoldstart = ConfigYesNo(default=False)
config.plugins.SystemTime.useRTCstart = ConfigYesNo(default=False)
config.plugins.SystemTime.wifi_delay = ConfigInteger(0, limits=(0, 120))
config.plugins.SystemTime.syncNTPtime = ConfigSelection(default="1", choices=[("1", _("Press OK"))])
config.plugins.SystemTime.syncDVBtime = ConfigSelection(default="1", choices=[("1", _("Press OK"))])
config.plugins.SystemTime.syncManually = ConfigSelection(default="1", choices=[("1", _("Press OK"))])
config.plugins.SystemTime.ip = ConfigText(default="pool.ntp.org", fixed_size=False)

ntpsyncpoller = None

fullHD = False
if getDesktop(0).size().width() >= 1920:
	fullHD = True


class SystemTimeSetupScreen(Screen, ConfigListScreen):

	skin = """
		<screen position="center,center" size="700,400" title="System time setup">
			<widget name="key_red" position="0,0" size="175,33" font="Regular;17" halign="center" valign="center" transparent="1" />
			<widget name="key_green" position="175,0" size="175,33" font="Regular;17" halign="center" valign="center" transparent="1" />
			<widget name="key_yellow" position="350,0" size="175,33" font="Regular;17" halign="center" valign="center" transparent="1" />
			<widget name="key_blue" position="525,0" size="175,33" font="Regular;17" halign="center" valign="center" transparent="1" />
			<ePixmap position="0,33" size="175,2" pixmap="/usr/lib/enigma2/python/Plugins/SystemPlugins/SystemTime/images/red.png" alphatest="blend" />
			<ePixmap position="175,33" size="175,2" pixmap="/usr/lib/enigma2/python/Plugins/SystemPlugins/SystemTime/images/green.png" alphatest="blend" />
			<ePixmap position="350,33" size="175,2" pixmap="/usr/lib/enigma2/python/Plugins/SystemPlugins/SystemTime/images/yellow.png" alphatest="blend" />
			<ePixmap position="525,33" size="175,2" pixmap="/usr/lib/enigma2/python/Plugins/SystemPlugins/SystemTime/images/blue.png" alphatest="blend" />
			<widget name="config" scrollbarMode="showOnDemand" position="0,45" size="700,225" />
			<widget name="description" position="5,290" size="690,75" font="Regular;17" />
			<ePixmap pixmap="div-h.png" position="0,280" size="700,2" />
			<ePixmap pixmap="div-h.png" position="0,362" size="700,2" />
			<widget source="global.CurrentTime" render="Label" position="150,370" size="430,25" font="Regular;20" halign="left" transparent="1">
				<convert type="ClockToText">Date</convert>
			</widget>
			<ePixmap alphatest="on" pixmap="icons/clock.png" position="590,375" size="14,14" />
			<widget source="global.CurrentTime" render="Label" position="610,370" size="55,25" font="Regular;20" halign="left" transparent="1">
				<convert type="ClockToText">Default</convert>
			</widget>
			<widget source="global.CurrentTime" render="Label" position="662,373" size="27,20" font="Regular;15" halign="left" transparent="1">
				<convert type="ClockToText">Format::%S</convert>
			</widget>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("System time setup"))
		self.skinName = ["SystemTimeSetupScreen", "Setup"]
		self.syncTimer = eTimer()
		self.syncTimer.callback.append(self.showMessage)
		self["description"] = Label("")
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label(_("Save"))
		self["key_yellow"] = Label(_("Restart GUI"))
		self["key_blue"] = Label("")

		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.keyGo,
			"save": self.keyGreen,
			"cancel": self.cancel,
			"red": self.keyRed,
			"yellow":self.keyYellow,
			"blue": self.keyBlue,
			"left": self.keyLeft,
			"right": self.keyRight,
		}, -2)

		ConfigListScreen.__init__(self, [])
		self.prev_ip = config.plugins.SystemTime.ip.value
		self.prev_wifi_delay = config.plugins.SystemTime.wifi_delay.value
		if config.plugins.SystemTime.syncNTPcoldstart.value and not fileExists("/etc/init.d/ntpdate"):
			config.plugins.SystemTime.syncNTPcoldstart.value = False
			config.plugins.SystemTime.syncNTPcoldstart.save()
		if config.plugins.SystemTime.useRTCstart.value and not fileExists("/etc/init.d/set-rtctime"):
			config.plugins.SystemTime.useRTCstart.value = False
			config.plugins.SystemTime.useRTCstart.save()
		if config.plugins.SystemTime.choiceSystemTime.value == "1" and config.misc.useTransponderTime.value:
			config.plugins.SystemTime.choiceSystemTime.value = "0"
			config.plugins.SystemTime.choiceSystemTime.save()
		elif config.plugins.SystemTime.choiceSystemTime.value == "0" and not config.misc.useTransponderTime.value:
			config.plugins.SystemTime.choiceSystemTime.value = "1"
			config.plugins.SystemTime.choiceSystemTime.save()
		self.initConfig()
		self.createSetup()
		self.servicelist = self.messagebox = None
		self["config"].onSelectionChanged.append(self.configPosition)

	def initConfig(self):
		def getPrevValues(section):
			res = {}
			for (key, val) in section.content.items.items():
				if isinstance(val, ConfigSubsection):
					res[key] = getPrevValues(val)
				else:
					res[key] = val.value
			return res

		self.ST = config.plugins.SystemTime
		self.prev_values = getPrevValues(self.ST)
		self.cfg_choiceSystemTime = getConfigListEntry(_("Sync time using"), self.ST.choiceSystemTime, _("Select the preferred method for syncing time on your receiver. Network Time Protocol requires internet connection. Transponder time might not be very accurate."))
		self.cfg_useNTPminutes = getConfigListEntry(_("Sync NTP every"), self.ST.useNTPminutes, _("Set how often the receiver will connect to the NTP server to sync time."))
		self.cfg_syncNTPcoldstart = getConfigListEntry(_("NTP cold start"), self.ST.syncNTPcoldstart, _("On receiver 'cold start', allow any required time adjustments to be 'stepped'."))
		self.cfg_wifi_delay = getConfigListEntry(_("Delay (in seconds) when using Wi-Fi"), self.ST.wifi_delay, _("After receiver's boot, wait for the specified delay before connecting to the NTP server. This allows the Wi-Fi connection to be fully established."))
		self.cfg_syncNTPtime = getConfigListEntry(_("Sync now with NTP server"), self.ST.syncNTPtime, _("Get current time from the specified NTP server."))
		self.cfg_syncDVBtime = getConfigListEntry(_("Sync now with current transponder"), self.ST.syncDVBtime, _("Get current time from the specified DVB transponder."))
		self.cfg_syncManually = getConfigListEntry(_("Set system time manually"), self.ST.syncManually, _("Enter a user defined date and time."))
		self.cfg_useRTCstart = getConfigListEntry(_("Use RTC time from deep standby"), self.ST.useRTCstart, _("When the receiver starts from deep standby, use the time provided by the Real Time Clock, if it appears to be valid."))
		self.cfg_ip = getConfigListEntry(_("NTP server"), self.ST.ip, _("Set the IP address of the preferred NTP server. Default is pool.ntp.org."))

	def createSetup(self):
		cfg_list = [self.cfg_choiceSystemTime]
		if self.ST.choiceSystemTime.value == "1":
			cfg_list.append(self.cfg_useNTPminutes)
		cfg_list.append(self.cfg_syncNTPcoldstart)
		if self.ST.syncNTPcoldstart.value:
			cfg_list.append(self.cfg_wifi_delay)
		if self.ST.choiceSystemTime.value == "1" or self.ST.syncNTPcoldstart.value:
			cfg_list.append(self.cfg_ip)
		if fileExists("/proc/stb/fp/rtc"):
			cfg_list.append(self.cfg_useRTCstart)
		cfg_list.append(self.cfg_syncNTPtime)
		cfg_list.append(self.cfg_syncDVBtime)
		cfg_list.append(self.cfg_syncManually)
		self["config"].list = cfg_list
		self["config"].l.setList(cfg_list)

	def newConfig(self):
		cur = self["config"].getCurrent()
		if cur in (self.cfg_choiceSystemTime, self.cfg_useNTPminutes, self.cfg_syncNTPcoldstart):
			self.createSetup()

	def keyGo(self):
		ConfigListScreen.keyOK(self)
		sel = self["config"].getCurrent() and self["config"].getCurrent()[1]
		if sel == self.ST.syncNTPtime:
			if os.path.exists("/usr/sbin/ntpdate"):
				cmd = '/usr/sbin/ntpdate -v -u %s && echo "\n"' % self.ST.ip.value
				self.session.open(SystemTimeConsole, _("Syncing with NTP server..."), [cmd])
			elif os.path.exists("/usr/sbin/ntpd"):
				cmd = '/usr/sbin/ntpd -dnqp %s' % self.ST.ip.value
				self.session.open(SystemTimeConsole, _("Syncing with NTP server..."), [cmd])
			else:
				self.session.open(MessageBox, "'ntpd' / " + _("'ntpdate' is not installed!"), MessageBox.TYPE_ERROR, timeout=3)
		elif sel == self.ST.syncDVBtime:
			try:
				if not self.syncTimer.isActive():
					self.old_time = time.time()
					self.oldtime = time.strftime("%Y:%m:%d %H:%M", time.localtime())
					eDVBLocalTimeHandler.getInstance().syncDVBTime()
					self.messagebox = self.session.openWithCallback(self.messageboxSessionClose, MessageBox, _("Syncing... Please wait."), MessageBox.TYPE_INFO)
					self.syncTimer.start(5000, True)
			except:
				if os.path.exists("/usr/bin/dvbdate"):
					cmd = '/usr/bin/dvbdate -p -s -f && echo "\n"'
					self.session.open(SystemTimeConsole, _("Syncing with current transponder..."), [cmd])
				else:
					self.session.open(MessageBox, _("'dvbdate' is not installed!"), MessageBox.TYPE_ERROR, timeout=3)
		elif sel == self.ST.syncManually:
			ChangeTimeWizzard(self.session)

	def messageboxSessionClose(self, answer=None):
		self.messagebox = None

	def showMessage(self):
		offset = (time.time() - 5.1) - self.old_time
		newtime = time.strftime("%Y:%m:%d %H:%M", time.localtime())
		if self.messagebox:
			self.messagebox["text"].setText(_("Old time: %(oldtime)s\nNew time: %(newtime)s\n\nOffset: %(offset)s seconds") % ({'oldtime' : self.oldtime, 'newtime' : newtime, 'offset' : offset}))

	def configPosition(self):
		self["description"].setText(self.getCurrentDescription())
		self["key_blue"].setText("")
		idx = self["config"].getCurrent() and self["config"].getCurrent()[1]
		if idx == self.ST.syncDVBtime:
			self["key_blue"].setText(_("Select transponder"))

	def keyRed(self):
		def setPrevValues(section, values):
			for (key, val) in section.content.items.items():
				value = values.get(key, None)
				if value is not None:
					if isinstance(val, ConfigSubsection):
						setPrevValues(val, value)
					else:
						val.value = value
		setPrevValues(self.ST, self.prev_values)
		self.ST.save()

	def addNTPcoldstart(self):
		if os.path.exists("/usr/sbin/ntpdate") or os.path.exists("/usr/sbin/ntpd"):
			if os.path.exists("/usr/sbin/ntpdate"):
				cmd = "echo -e '#!/bin/sh\n\nsleep %s\n\n[ -x /usr/sbin/ntpdate ] && /usr/sbin/ntpdate -s -u %s\n\nexit 0' >> /etc/init.d/ntpdate" % (str(self.ST.wifi_delay.value), self.ST.ip.value)
			elif os.path.exists("/usr/sbin/ntpd"):
				cmd = "echo -e '#!/bin/sh\n\nsleep %s\n\n[ -x usr/sbin/ntpd ] && /usr/sbin/ntpd -dnqp %s\n\nexit 0' >> /etc/init.d/ntpdate" % (str(self.ST.wifi_delay.value), self.ST.ip.value)
			if fileExists("/etc/init.d/ntpdate"):
				os.chmod("/etc/init.d/ntpdate", 0755)
				os.system("update-rc.d ntpdate defaults 99")
			else:
				os.system(cmd)
				if fileExists("/etc/init.d/ntpdate"):
					os.chmod("/etc/init.d/ntpdate", 0755)
					os.system("update-rc.d ntpdate defaults 99")
				else:
					self.ST.syncNTPcoldstart.value = False
		else:
			self.session.open(MessageBox, "'ntpd' / " + _("'ntpdate' is not installed!"), MessageBox.TYPE_ERROR, timeout=3)
			self.ST.syncNTPcoldstart.value = False

	def removeNTPcoldstart(self):
		os.system("update-rc.d -f ntpdate remove")
		if fileExists("/etc/init.d/ntpdate"):
			os.system("rm -rf /etc/init.d/ntpdate")

	def addUseRTC(self):
		if fileExists("/etc/init.d/set-rtctime"):
			os.chmod("/etc/init.d/set-rtctime", 0755)
			os.system("update-rc.d set-rtctime defaults 40")
		else:
			os.system("cp /usr/lib/enigma2/python/Plugins/SystemPlugins/SystemTime/set-rtctime /etc/init.d/set-rtctime")
			if fileExists("/etc/init.d/set-rtctime"):
				os.chmod("/etc/init.d/set-rtctime", 0755)
				os.system("update-rc.d set-rtctime defaults 40")
			else:
				self.session.open(MessageBox, _("Script 'set-rtctime' not found!"), MessageBox.TYPE_ERROR, timeout=3)
				self.ST.useRTCstart.value = False

	def removeUseRTC(self):
		os.system("update-rc.d -f set-rtctime remove")

	def keyGreen(self):
		if self.ST.syncNTPcoldstart.value:
			if self.prev_ip != self.ST.ip.value or self.prev_wifi_delay != config.plugins.SystemTime.wifi_delay.value:
				self.removeNTPcoldstart()
			self.addNTPcoldstart()
		else:
			self.removeNTPcoldstart()
		if self.ST.useRTCstart.value:
			self.addUseRTC()
		else:
			self.removeUseRTC()
		if self.ST.choiceSystemTime.value == "0":
			eDVBLocalTimeHandler.getInstance().setUseDVBTime(True)
			config.misc.useTransponderTime.value = True
			config.misc.useTransponderTime.save()
		else:
			eDVBLocalTimeHandler.getInstance().setUseDVBTime(False)
			config.misc.useTransponderTime.value = False
			config.misc.useTransponderTime.save()
		removeNetworkStart()
		self.ST.save()
		configfile.save()
		self.close()

	def cancel(self):
		self.keyRed()
		self.close()

	def keyYellow(self):
		self.session.openWithCallback(self.restartGui, MessageBox, _("Restart GUI now?"), MessageBox.TYPE_YESNO)

	def restartGui(self, answer):
		if answer:
			self.session.open(TryQuitMainloop, 3)

	def keyBlue(self):
		idx = self["config"].getCurrent() and self["config"].getCurrent()[1]
		if idx == self.ST.syncDVBtime:
			for (dlg, flag) in self.session.dialog_stack:
				if dlg.__class__.__name__ == "InfoBar":
					self.servicelist = dlg.servicelist
					break
			if not self.servicelist is None:
				self.session.execDialog(self.servicelist)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.newConfig()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.newConfig()


class SystemTimeConsole(Console):
	if fullHD:
		skin = """<screen position="center,center" size="750,360" title="Command execution..." >
			<widget name="text" position="10,10" size="732,445" font="Regular;30" />
		</screen>"""
	else:
		skin = """<screen position="center,center" size="500,240" title="Command execution..." >
			<widget name="text" position="10,10" size="485,230" font="Regular;20" />
		</screen>"""

	def __init__(self, session, title="System time console...", cmdlist=None):
		Console.__init__(self, session, title, cmdlist)
		self.skinName = ["SystemTimeConsole", "Console"]

	def cancel(self):
		nowTime = time.time()
		if nowTime > 1514808000:
			setRTCtime(nowTime)
			if config.plugins.SystemTime.choiceSystemTime.value == "0":
				eDVBLocalTimeHandler.getInstance().setUseDVBTime(True)
			else:
				eDVBLocalTimeHandler.getInstance().setUseDVBTime(False)
			try:
				eEPGCache.getInstance().timeUpdated()
			except:
				pass
		Console.cancel(self)


class ChangeTimeWizzard(Screen):

	def __init__(self, session):
		Screen.__init__(self, session)
		self.oldtime = time.strftime("%Y:%m:%d %H:%M", time.localtime())
		self.session.openWithCallback(self.askForNewTime, InputBox, title=_("Enter new system time and press OK!"), text="%s" % (self.oldtime), maxSize=16, type=Input.NUMBER)

	def askForNewTime(self, newclock):
		try:
			length = len(newclock)
		except:
			length = 0
		if newclock is None:
			self.skipChangeTime(_("No change detected."))
		elif length != 16:
			self.skipChangeTime(_("Time string too short."))
		elif newclock.count(" ") < 1:
			self.skipChangeTime(_("Invalid time format."))
		elif newclock.count(":") < 3:
			self.skipChangeTime(_("Invalid time format."))
		else:
			full = []
			full = newclock.split(" ", 1)
			newdate = full[0]
			newtime = full[1]
			parts = []
			parts = newdate.split(":", 2)
			newyear = parts[0]
			newmonth = parts[1]
			newday = parts[2]
			parts = newtime.split(":", 1)
			newhour = parts[0]
			newmin = parts[1]
			maxmonth = 31
			if (int(newmonth) == 4) or (int(newmonth) == 6) or (int(newmonth) == 9) or (int(newmonth) == 11):
				maxmonth = 30
			elif int(newmonth) == 2:
				if isleap(int(newyear)):
					maxmonth = 29
				else:
					maxmonth = 28
			if (int(newyear) < 2019) or (int(newyear) > 2029) or (len(newyear) < 4):
				self.skipChangeTime(_("Invalid input in year: %s") %newyear)
			elif (int(newmonth) < 1) or (int(newmonth) > 12) or (len(newmonth) < 2):
				self.skipChangeTime(_("Invalid input in month: %s") %newmonth)
			elif (int(newday) < 1) or (int(newday) > maxmonth) or (len(newday) < 2):
				self.skipChangeTime(_("Invalid input in day: %s") %newday)
			elif (int(newhour) < 0) or (int(newhour) > 23) or (len(newhour) < 2):
				self.skipChangeTime(_("Invalid input in hour: %s") %newhour)
			elif (int(newmin) < 0) or (int(newmin) > 59) or (len(newmin) < 2):
				self.skipChangeTime(_("Invalid input in minute: %s") %newmin)
			else:
				self.newtime = "%s%s%s%s%s" % (newmonth, newday, newhour, newmin, newyear)
				self.session.openWithCallback(self.DoChangeTimeRestart, MessageBox, _("Apply new system time?"), MessageBox.TYPE_YESNO)

	def DoChangeTimeRestart(self, answer):
		if answer is None:
			self.skipChangeTime(_("No answer given."))
		if answer is False:
			self.skipChangeTime(_("No confirmation given."))
		else:
			os.system("date %s" % (self.newtime))
			nowTime = time.time()
			if nowTime > 1514808000:
				setRTCtime(nowTime)
				if config.plugins.SystemTime.choiceSystemTime.value == "0":
					eDVBLocalTimeHandler.getInstance().setUseDVBTime(True)
				else:
					eDVBLocalTimeHandler.getInstance().setUseDVBTime(False)
				try:
					eEPGCache.getInstance().timeUpdated()
				except:
					pass

	def skipChangeTime(self, reason):
		self.session.open(MessageBox, _("System time was not applied.\n%s") % reason, MessageBox.TYPE_WARNING)


def removeNetworkStart():
	if os.path.exists("/usr/bin/ntpdate-sync"):
		os.system("rm -rf /usr/bin/ntpdate-sync && rm -rf /etc/network/if-up.d/ntpdate-sync")


def startup(reason=0, **kwargs):
	if reason == 0:
		global ntpsyncpoller
		if ntpsyncpoller is None:
			ntpsyncpoller = NTPSyncPoller()
			ntpsyncpoller.start()
			removeNetworkStart()
	elif reason == 1:
		nowTime = time.time()
		if nowTime > 1514808000:
			setRTCtime(nowTime)


def main(menuid, **kwargs):
	if menuid == "system":
		return [(_("System time"), OpenSetup, "system_time_setup", None)]
	else:
		return []


def OpenSetup(session, **kwargs):
	session.open(SystemTimeSetupScreen)


def Plugins(**kwargs):
	return [PluginDescriptor(name="System time", description=_("Change system time in enigma2 box"), where=PluginDescriptor.WHERE_MENU, fnc=main),
			PluginDescriptor(name="System time", where=PluginDescriptor.WHERE_AUTOSTART, fnc=startup)]
