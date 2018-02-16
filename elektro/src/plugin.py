#
# Power Save Plugin by gutemine
#
# Rewritten by Morty (morty@gmx.net)
#
# Profiles, HDD, IP, NAS Mod by joergm6
#
# Small fixes by awl (3.4.6):
#   * ElektroWakeUpTime must be recalculated after parameter change 
#     before shutdown in getNextWakeup() in order to allow
#     for correct detection of automated wakeup
#   * elektroTimerWakeupThreshold increased from 6 to 14.75 minutes
#     (> 12 minutes is needed e.g. on Optimuss OS 2 plus)
#   * Extensive debug output added (enclosed by "if debug" - 
#     set debug to true in order to see what really happens...)
#   * Minor code cleanup
#   * Debug output now correctly prints all times in local time
#     (rather than partly local time, partly UTC)
#
# Deep standby will be called sleep. Normal standby will be named standby!
# All calculations are in the local timezone, or in the relative Timezone.
# In the relative timezone the day starts at "nextday". If it is before nextday the last day will be used.
#
#


from __init__ import _

from Screens.InfoBarGenerics import *

import calendar

# Plugin
from Plugins.Plugin import PluginDescriptor

# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Screens.MessageBox import MessageBox
from Screens.Console import Console
from Screens import Standby

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Language import language
from Components.Harddisk import harddiskmanager
from Components.Sources.StaticText import StaticText

# Configuration
from Components.config import configfile, getConfigListEntry, ConfigEnableDisable, \
	ConfigYesNo, ConfigText, ConfigClock, ConfigNumber, ConfigSelection, \
	config, ConfigSubsection, ConfigSubList, ConfigSubDict, ConfigIP

# Startup/shutdown notification
from Tools import Notifications

import ping
import os

# Timer, etc
from time import localtime, asctime, time, gmtime, sleep

# Enigma system functions
from enigma import quitMainloop, eTimer


###############################################################################

# Globals
pluginPrintname = "[Elektro]"
debug = False # If set True, plugin will print some additional status info to track logic flow
session = None
ElektroWakeUpTime = -1
elektro_pluginversion = "3.4.6"
elektrostarttime = 60
elektrosleeptime = 5
elektroTimerWakeupThreshold = 60 * 14 + 45 # any wakeup from sleep within 14.75 minutes around the wakeup time/a recording timer is regarded to be automatic (as opposed to manual)
elektroShutdownThreshold = 60 * 20 # we only go to sleep if and only if we won't need to wake up for a timer within the next 20 minutes
###############################################################################

#Configuration
if debug:
	print pluginPrintname, "Setting config defaults"
config.plugins.elektro = ConfigSubsection()
config.plugins.elektro.nextday = ConfigClock(default = ((6 * 60 + 0) * 60) )
config.plugins.elektro.nextday2 = ConfigClock(default = ((6 * 60 + 0) * 60) )
config.plugins.elektro.profile = ConfigSelection(choices = [("1", "Profile 1"), ("2", "Profile 2")], default = "1")
config.plugins.elektro.profileShift = ConfigYesNo(default = False)

config.plugins.elektro.sleep = ConfigSubDict()
for i in range(7):
	config.plugins.elektro.sleep[i] = ConfigClock(default = ((1 * 60 + 0) * 60) )

config.plugins.elektro.wakeup = ConfigSubDict()
for i in range(7):
	config.plugins.elektro.wakeup[i] = ConfigClock(default = ((9 * 60 + 0) * 60) )

config.plugins.elektro.sleep2 = ConfigSubDict()
for i in range(7):
	config.plugins.elektro.sleep2[i] = ConfigClock(default = ((1 * 60 + 0) * 60) )

config.plugins.elektro.wakeup2 = ConfigSubDict()
for i in range(7):
	config.plugins.elektro.wakeup2[i] = ConfigClock(default = ((9 * 60 + 0) * 60) )

config.plugins.elektro.ip = ConfigSubDict()
for i in range(10):
	config.plugins.elektro.ip[i] = ConfigIP(default = [0, 0, 0, 0])

config.plugins.elektro.name = ConfigText(default = _("Elektro Power Save"), fixed_size = False, visible_width = 20)
config.plugins.elektro.description = ConfigText(default = _("Automatically shut down to deep standby"), fixed_size = False, visible_width = 80)
config.plugins.elektro.menu = ConfigSelection(default = "plugin", choices = [("plugin", _("Plugin menu")), ("extensions", _("Extensions menu"))])
config.plugins.elektro.enable = ConfigEnableDisable(default = False)
config.plugins.elektro.standbyOnBoot = ConfigYesNo(default = False)
config.plugins.elektro.standbyOnManualBoot = ConfigYesNo(default = True)
config.plugins.elektro.standbyOnBootTimeout = ConfigNumber(default = 60)
config.plugins.elektro.nextwakeup = ConfigNumber(default = 0)
config.plugins.elektro.force = ConfigYesNo(default = False)
config.plugins.elektro.dontwakeup = ConfigEnableDisable(default = False)
config.plugins.elektro.holiday = ConfigEnableDisable(default = False)
config.plugins.elektro.hddsleep = ConfigYesNo(default = False)
config.plugins.elektro.IPenable = ConfigYesNo(default = False)

config.plugins.elektro.NASenable = ConfigSelection(choices = [("false", "no"), ("true", "yes"), ("1", _("yes, Profile 1")), ("2", _("yes, Profile 2"))], default="false")
config.plugins.elektro.NASname = ConfigText(default = "", fixed_size = False, visible_width = 50)
config.plugins.elektro.NASuser = ConfigText(default = "", fixed_size = False, visible_width = 50)
config.plugins.elektro.NASpass = ConfigText(default = "", fixed_size = False, visible_width = 50)
config.plugins.elektro.NAScommand = ConfigText(default = "poweroff", fixed_size = False, visible_width = 50)
config.plugins.elektro.NASport = ConfigNumber(default = 23)
config.plugins.elektro.NASwait = ConfigYesNo(default = False)

weekdays = [
	_("Monday"),
	_("Tuesday"),
	_("Wednesday"),
	_("Thursday"),
	_("Friday"),
	_("Saturday"),
	_("Sunday"),
	]


#global ElektroWakeUpTime
ElektroWakeUpTime = -1

def NASpowerdown(Nname,Nuser,Npass,Ncommand,Nport):
	from telnetlib import Telnet
	if Nname == "":
		return _("no Name")
	l=_("Connection Error")
	try:
		tn = Telnet(Nname, Nport, 5)
		l=""
		if Nuser != "":
			l = l + tn.expect(['ogin:','sername'],10)[2]
			l = l + tn.read_very_lazy()
			tn.write('%s\r' % Nuser)
		if Npass != "":
			l = l + tn.read_until('assword:',10)
			l = l + tn.read_very_lazy()
			tn.write('%s\r' % Npass)
		l = l + tn.expect(['#',">"],10)[2]
		l = l + tn.read_very_lazy()
		tn.write('%s\r' % Ncommand)
		l = l + tn.expect(['#',">"],20)[2]
		l = l + tn.read_very_lazy()
		if config.plugins.elektro.NASwait.value == True:
			tt = time() + 90
			l = l + "\n waiting...\n"
			while tt>time() and ping.doOne(Nname,1) != None:
				sleep(2)
		tn.write('exit\r')
		l = l + tn.expect(['#',">"],5)[2]
		l = l + tn.read_very_lazy()
		tn.close()
	finally:
		return l


def autostart(reason, **kwargs):
	global session
	if reason == 0 and kwargs.has_key("session"):
		session = kwargs["session"]
		session.open(DoElektro)


def clkToTime(clock):
	return ( (int)(clock.value[0]) * 60 + (int)(clock.value[1]) ) * 60

def getTime():
	ltime = localtime();
	return ( (int)(ltime.tm_hour) * 60 + (int)(ltime.tm_min) ) * 60

def getPrintTime(secs):
	return strftime("%H:%M:%S", gmtime(secs))


# This function converts the time into the relative Timezone where the day starts at "nextday"
# This is done by substracting nextday from the current time. Negative times are corrected using the mod-operator
def getReltime(time):
	if config.plugins.elektro.profile.value == "1":
		nextday = clkToTime(config.plugins.elektro.nextday)
	else:
		nextday = clkToTime(config.plugins.elektro.nextday2)
	return (time - nextday) % (24 * 60 * 60)


def setNextWakeuptime():
	if debug:
		print pluginPrintname, "Entering setNextWakeuptime()"
	# Do not set a wakeup time if
	#  - Elektro isn't enabled
	#  - Elektro shouldn't wake up
	#  - Holiday mode is turned on
	if ((config.plugins.elektro.enable.value == False)
				or (config.plugins.elektro.dontwakeup.value == True)
				or config.plugins.elektro.holiday.value == True):
		global ElektroWakeUpTime
		ElektroWakeUpTime = -1
		print pluginPrintname, "ElektroWakeUpTime is now", ElektroWakeUpTime
		return

	time_s = getTime()
	ltime = localtime()
	if debug:
		print pluginPrintname, "Current time in seconds since midnight", time_s
		print pluginPrintname, "Local time", strftime("%a, %d %b %Y %H:%M:%S", ltime)
	if config.plugins.elektro.profile.value == "1":
		config_wakeup = config.plugins.elektro.wakeup
		config_sleep = config.plugins.elektro.sleep
		config_nextday = config.plugins.elektro.nextday
	else:
		config_wakeup = config.plugins.elektro.wakeup2
		config_sleep = config.plugins.elektro.sleep2
		config_nextday = config.plugins.elektro.nextday2
	if debug:
		print pluginPrintname, "Wakeup", config_wakeup
		print pluginPrintname, "Sleep", config_sleep
		print pluginPrintname, "Nextday", config_nextday

	# If it isn't past next-day time we need yesterday's settings
	#
	if time_s < clkToTime(config_nextday):
		day = (ltime.tm_wday - 1) % 7
		if debug:
			print pluginPrintname, "Yesterday's settings"
	else:
		day = ltime.tm_wday
		if debug:
			print pluginPrintname, "Today's settings"
	if debug:
		print pluginPrintname, "Resulting day of Week (Monday=0)", day

	# Check whether we wake up today or tomorrow
	# Relative Time is needed for this
	time_s = getReltime(time_s)
	if debug:
		print pluginPrintname, "Current Time in seconds since nextday", time_s
	wakeuptime = getReltime(clkToTime(config_wakeup[day]))

	# Lets see if we already woke up today
	if time_s > (wakeuptime + elektroTimerWakeupThreshold):
		#yes we did -> Next wakeup is tomorrow
		if debug:
			print pluginPrintname, "Wakeup tomorrow"
		day = (day + 1) % 7
		wakeuptime = getReltime(clkToTime(config_wakeup[day]))

	# Tomorrow we'll wake up early-> Add a full day.
	if time_s > (wakeuptime + elektroTimerWakeupThreshold):
		wakeuptime = wakeuptime + 24 * 60 * 60
	if debug:
		print pluginPrintname, "Wakeup Time in seconds since nextday", wakeuptime

	# The next wakeup will be in wakupin seconds
	wakeupin = wakeuptime - time_s
	if debug:
		print pluginPrintname, "Next wakeup in seconds", wakeupin
	# Now add this to the current time to get the wakeuptime
	wakeuptime = (int)(time()) + wakeupin

	#Write everything to the global variable
	ElektroWakeUpTime = wakeuptime
	print pluginPrintname, "ElektroWakeUpTime is now", ElektroWakeUpTime


def getNextWakeup():
	global ElektroWakeUpTime

	if debug:
		print pluginPrintname, "Entering getNextWakeup()"

	# Update wakeup time from potential most recent changes in parameters.
	setNextWakeuptime()

	#it might happen, that session does not exist. I don't know why. :-(
	if session is None:
		print pluginPrintname, "No session found; Will wake up at", strftime("%a:%H:%M:%S", localtime(ElektroWakeUpTime))
		return ElektroWakeUpTime;

	nextTimer = session.nav.RecordTimer.getNextRecordingTime()
	if debug:
		print pluginPrintname, "Now:", strftime("%a:%H:%M:%S", localtime(time()))
	if (nextTimer < 1):
		if debug:
			print pluginPrintname, "No next recording timer configured"
	else:
		if debug:
			print pluginPrintname, "Next recording timer:", strftime("%a:%H:%M:%S", localtime(nextTimer))
	if (nextTimer < 1) or (nextTimer > ElektroWakeUpTime):
		print pluginPrintname, "Wake up due to Elektro at", strftime("%a:%H:%M:%S", localtime(ElektroWakeUpTime))
		return ElektroWakeUpTime

	#We have to make sure, that the Box will wake up because of us
	# and not because of the timer
	print pluginPrintname, "Wake up due to next recording timer at", strftime("%a:%H:%M:%S", localtime(nextTimer))
	return nextTimer - 1

def Plugins(**kwargs):
	if debug:
		print pluginPrintname, "Setting entry points"
	list = [
		PluginDescriptor(
			name = config.plugins.elektro.name.value,
			description = config.plugins.elektro.description.value + " " + _("Ver.") + " " + elektro_pluginversion,
			where = [
				PluginDescriptor.WHERE_SESSIONSTART,
				PluginDescriptor.WHERE_AUTOSTART
			],
			fnc = autostart,
			wakeupfnc = getNextWakeup)
		]
	if config.plugins.elektro.menu.value == "plugin":
		list.append (PluginDescriptor(
			name = config.plugins.elektro.name.value,
			description = config.plugins.elektro.description.value + " " + _("Ver.") + " " + elektro_pluginversion,
			where = PluginDescriptor.WHERE_PLUGINMENU,
			icon = "elektro.png",
			fnc=main)
		)
	else:
		list.append (PluginDescriptor(
			name = config.plugins.elektro.name.value,
			description = config.plugins.elektro.description.value + " " + _("Ver.") + " " + elektro_pluginversion,
			where = PluginDescriptor.WHERE_EXTENSIONSMENU,
			fnc=main)
		)

	return list


def main(session,**kwargs):
	try:
	 	session.open(Elektro)
	except:
		print pluginPrintname, "Pluginexecution failed"

class ElektroProfile(ConfigListScreen,Screen):
	skin = """
			<screen position="center,center" size="600,400" title="Elektro Power Save Profile Times" >
			<widget name="config" position="0,0" size="600,360" scrollbarMode="showOnDemand" />

			<widget name="key_red" position="0,360" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1"/>
			<widget name="key_green" position="140,360" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1"/>

			<ePixmap name="red" position="0,360" zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="140,360" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session, args = 0):
		self.session = session
		Screen.__init__(self, session)

		self.list = []

		for i in range(7):
			self.list.append(getConfigListEntry(" 1. " + weekdays[i] + ": " + _("Wakeup"), config.plugins.elektro.wakeup[i]))
			self.list.append(getConfigListEntry(" 1. " + weekdays[i] + ": " + _("Sleep"), config.plugins.elektro.sleep[i]))
		self.list.append(getConfigListEntry(" 1. " + _("Next day starts at"), config.plugins.elektro.nextday,
			_("If the box is supposed to enter deep standby e.g. monday night at 1 AM, it actually is already tuesday. To enable this anyway, differing next day start time can be specified here.")))
		for i in range(7):
			self.list.append(getConfigListEntry(" 2. " + weekdays[i] + ": " + _("Wakeup"), config.plugins.elektro.wakeup2[i]))
			self.list.append(getConfigListEntry(" 2. " + weekdays[i] + ": " + _("Sleep"), config.plugins.elektro.sleep2[i]))
		self.list.append(getConfigListEntry(" 2. " + _("Next day starts at"), config.plugins.elektro.nextday2,
			_("If the box is supposed to enter deep standby e.g. monday night at 1 AM, it actually is already tuesday. To enable this anyway, differing next day start time can be specified here.")))

		ConfigListScreen.__init__(self, self.list)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Ok"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"green": self.save,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
		}, -2)

	def save(self):
		#print "saving"
		for x in self["config"].list:
			x[1].save()
		self.close(False,self.session)

	def cancel(self):
		#print "cancel"
		for x in self["config"].list:
			x[1].cancel()
		self.close(False,self.session)

class ElektroIP(ConfigListScreen,Screen):
	skin = """
			<screen position="center,center" size="600,400" title="Elektro Power Save IP Addresses to wait" >
			<widget name="config" position="0,0" size="600,360" scrollbarMode="showOnDemand" />

			<widget name="key_red" position="0,360" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1"/>
			<widget name="key_green" position="140,360" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1"/>

			<ePixmap name="red" position="0,360" zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="140,360" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session, args = 0):
		self.session = session
		Screen.__init__(self, session)

		self.list = []

		for i in range(10):
			self.list.append(getConfigListEntry(_("IP Address") , config.plugins.elektro.ip[i]))

		ConfigListScreen.__init__(self, self.list)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Ok"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"green": self.save,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
		}, -2)

	def save(self):
		#print "saving"
		for x in self["config"].list:
			x[1].save()
		self.close(False,self.session)

	def cancel(self):
		#print "cancel"
		for x in self["config"].list:
			x[1].cancel()
		self.close(False,self.session)

class ElektroNASrun(ConfigListScreen,Screen):
	skin = """
		<screen name="ElektroNASrun" position="center,center" size="600,400" zPosition="1" title="Powerdown...">
		<widget source="TextTest" render="Label" position="10,0" size="580,400" font="Regular;20" transparent="1" />
		</screen>"""

	def __init__(self, session, args = 0):
		self.session = session
		Screen.__init__(self, session)
		self["TextTest"] = StaticText()
		self["TextTest"].setText(_("please wait..."))
		self.timer = eTimer()
		self.timer.callback.append(self.DoNASrun)
		self.timer.start(1000, True)

		self["actions"] = ActionMap(["OkCancelActions"],
		{
			"ok": self.cancel,
			"cancel": self.cancel
		}, -1)

	def cancel(self):
		self.close(False,self.session)

	def DoNASrun(self):
		ret = NASpowerdown(config.plugins.elektro.NASname.value, config.plugins.elektro.NASuser.value, config.plugins.elektro.NASpass.value, config.plugins.elektro.NAScommand.value, config.plugins.elektro.NASport.value)
		self["TextTest"].setText(ret)

class ElektroNAS(ConfigListScreen,Screen):
	skin = """
			<screen name="ElektroNAS" position="center,center" size="600,400" title="Elektro Power Save IP Telnet - Poweroff" >
			<widget name="config" position="0,0" size="600,360" scrollbarMode="showOnDemand" />

			<widget name="key_red" position="0,360" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1"/>
			<widget name="key_green" position="140,360" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1"/>
			<widget name="key_yellow" position="280,360" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1"/>

			<ePixmap name="red" position="0,360" zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="140,360" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,360" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session, args = 0):
		self.session = session
		Screen.__init__(self, session)

		self.list = []
		self.list.append(getConfigListEntry(_("NAS/Server Name or IP"), config.plugins.elektro.NASname))
		self.list.append(getConfigListEntry(_("Username"), config.plugins.elektro.NASuser))
		self.list.append(getConfigListEntry(_("Password"), config.plugins.elektro.NASpass))
		self.list.append(getConfigListEntry(_("Command [poweroff, shutdown -h,...]"), config.plugins.elektro.NAScommand))
		self.list.append(getConfigListEntry(_("Telnet Port"), config.plugins.elektro.NASport))
		self.list.append(getConfigListEntry(_("Waiting until poweroff"), config.plugins.elektro.NASwait))

		ConfigListScreen.__init__(self, self.list)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Ok"))
		self["key_yellow"] = Button(_("Run"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"green": self.save,
			"yellow": self.run,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
		}, -2)

	def run(self):
		self.session.open(ElektroNASrun)

	def save(self):
		#print "saving"
		for x in self["config"].list:
			x[1].save()
		self.close(False,self.session)

	def cancel(self):
		#print "cancel"
		for x in self["config"].list:
			x[1].cancel()
		self.close(False,self.session)

class Elektro(ConfigListScreen,Screen):
	skin = """
		<screen name ="Elektro" position="center,center" size="630,480" title="Elektro Power Save" >
			<widget name="key_red" position="4,5" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1"/>
			<widget name="key_green" position="165,5" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1"/>
			<widget name="key_yellow" position="325,5" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1"/>
			<widget name="key_blue" position="485,5" size="140,40" valign="center" halign="center" zPosition="4" foregroundColor="white" font="Regular;18" transparent="1"/>

			<ePixmap name="red" position="5,5" zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green" position="165,5" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="325,5" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue" position="485,5" zPosition="2" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />

			<widget name="config" position="5,50" size="620,275" scrollbarMode="showOnDemand" />

			<ePixmap pixmap="skin_default/div-h.png" position="0,330" zPosition="1" size="630,2" />
			<widget source="help" render="Label" position="5,335" size="620,153" font="Regular;21" />
		</screen>"""


	def __init__(self, session, args = 0):
		self.session = session
		Screen.__init__(self, session)
		if debug:
			print pluginPrintname, "Displays config screen"

		self.onChangedEntry = []

		self.list = [
			getConfigListEntry(_("Active Time Profile"), config.plugins.elektro.profile,
				_("The active Time Profile is (1 or 2).")),
			getConfigListEntry(_("Enable Elektro Power Save"),config.plugins.elektro.enable,
				_("Unless this is enabled, this plugin won't run automatically.")),
			getConfigListEntry(_("Use both profiles alternately"), config.plugins.elektro.profileShift,
				_("Both profiles are used alternately. When shutting down the other profile is enabled. This allows two time cycles per day. Do not overlap the times.")),
			getConfigListEntry(_("Standby on boot"), config.plugins.elektro.standbyOnBoot,
				_("Puts the box in standby mode after boot.")),
			getConfigListEntry(_("Standby on manual boot"), config.plugins.elektro.standbyOnManualBoot,
				_("Whether to put the box in standby when booted manually. On manual boot the box will not go to standby before the next deep standby interval starts, even if this option is set. This option is only active if 'Standby on boot' option is set, too.")),
			getConfigListEntry(_("Standby on boot screen timeout"), config.plugins.elektro.standbyOnBootTimeout,
				_("Specify how long to show the standby query on boot screen. This value can be set to ensure the box does not shut down to deep standby again too fast when in standby mode.")),
			getConfigListEntry(_("Force sleep (even when not in standby)"), config.plugins.elektro.force,
				_("Forces deep standby, even when not in standby mode. Scheduled recordings remain unaffected.")),
			getConfigListEntry(_("Avoid deep standby when HDD is active, e.g. for FTP"), config.plugins.elektro.hddsleep,
				_("Wait for the HDD to enter sleep mode. Depending on the configuration this can prevent the box entirely from entering deep standby mode.")),
			getConfigListEntry(_("Check IPs (press OK to edit)"), config.plugins.elektro.IPenable,
				_("This list of IP addresses is checked. Elektro waits until addresses no longer responds to ping.")),
			getConfigListEntry(_("NAS Poweroff (press OK to edit)"), config.plugins.elektro.NASenable,
				_("A NAS/Server can be shut down. Is required activated Telnet.")),
			getConfigListEntry(_("Don't wake up"), config.plugins.elektro.dontwakeup,
				_("Do not wake up at the end of next deep standby interval.")),
			getConfigListEntry(_("Holiday mode (experimental)"), config.plugins.elektro.holiday,
				_("The box always enters deep standby mode, except for recording.")),
			getConfigListEntry(_("Show in"), config.plugins.elektro.menu,
				_("Specify whether plugin shall show up in plugin menu or extensions menu (needs GUI restart)")),
			getConfigListEntry(_("Name"), config.plugins.elektro.name,
				_("Specify plugin name to be used in menu (needs GUI restart).")),
			getConfigListEntry(_("Description"), config.plugins.elektro.description,
				_("Specify plugin description to be used in menu (needs GUI restart).")),
			]

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

		def selectionChanged():
			if self["config"].current:
				self["config"].current[1].onDeselect(self.session)
			self["config"].current = self["config"].getCurrent()
			if self["config"].current:
				self["config"].current[1].onSelect(self.session)
			for x in self["config"].onSelectionChanged:
				x()

		self["config"].selectionChanged = selectionChanged
		self["config"].onSelectionChanged.append(self.configHelp)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("Ok"))
		self["key_yellow"] = Button(_("Help"))
		self["key_blue"] = Button(_("Times"))
		self["help"] = StaticText()

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow": self.help,
			"blue": self.profile,
			"save": self.keySave,
			"cancel": self.keyCancel,
			"ok": self.keyOK,
		}, -2)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(config.plugins.elektro.name.value + " " + _("Ver.") + " " + elektro_pluginversion)

	def configHelp(self):
		cur = self["config"].getCurrent()
		self["help"].text = cur[2]

	def keyOK(self):
		ConfigListScreen.keyOK(self)
		sel = self["config"].getCurrent()[1]
		if sel == config.plugins.elektro.IPenable:
			self.session.open(ElektroIP)
		if sel == config.plugins.elektro.NASenable:
			self.session.open(ElektroNAS)

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except Exception:
				pass

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def help(self):
		self.session.open(Console,_("Showing Elektro readme.txt"),["cat /usr/lib/enigma2/python/Plugins/Extensions/Elektro/%s" % _("readme.txt")])

	def profile(self):
		self.session.open(ElektroProfile)

class DoElektro(Screen):
	skin = """ <screen position="center,center" size="300,300" title="Elektro Plugin Menu" > </screen>"""

	def __init__(self,session):
		Screen.__init__(self,session)

		print pluginPrintname, "Starting up Version", elektro_pluginversion

		self.session = session

		# Make sure wakeup time is set.
		setNextWakeuptime()

		# If we didn't wake up by a timer we don't want to go to sleep any more.
		# Unfortunately it is not possible to use getFPWasTimerWakeup()
		# Therefore we're checking whether there is a recording starting within
		# the next elektroTimerWakeupThreshold min
		self.dontsleep = False

		# Let's assume we got woken up manually
		timerWakeup = False

		# Is a recording already runniong -> woken up by a timer
		if self.session.nav.RecordTimer.isRecording():
			timerWakeup = True
		# Is the next timer within elektroTimerWakeupThreshold -> woken up by a timer
		if abs(self.session.nav.RecordTimer.getNextRecordingTime() - time()) <= elektroTimerWakeupThreshold:
			timerWakeup = True

		# Did we wake up by Elektro?
		# Is ElektroWakeUpTime within elektroTimerWakeupThreshold -> woken up by Elektro plugin
		if debug:
			print pluginPrintname, "ElektroWakeUpTime:", strftime("%a, %d %b %Y %H:%M:%S", localtime(ElektroWakeUpTime))
			print pluginPrintname, "Current Time:", strftime("%a, %d %b %Y %H:%M:%S", localtime(time()))
			print pluginPrintname, "Time Difference to ElektroWakeUpTime:", abs(ElektroWakeUpTime - time())
		if abs(ElektroWakeUpTime - time()) <= elektroTimerWakeupThreshold:
			timerWakeup = True

		print pluginPrintname, "Woken Up by a Timer?", timerWakeup

		# If the was a manual wakeup: Don't go to sleep
		if timerWakeup == False:
			self.dontsleep = True

		#Check whether we should try to sleep:
		trysleep = config.plugins.elektro.standbyOnBoot.value

		#Don't go to sleep when this was a manual wakeup and the box shouldn't go to standby
		if timerWakeup == False and	config.plugins.elektro.standbyOnManualBoot.value == False:
			trysleep = False


		#if waken up by timer and configured ask whether to go to sleep.
		if trysleep:
			self.TimerStandby = eTimer()
			self.TimerStandby.callback.append(self.CheckStandby)
			self.TimerStandby.startLongTimer(elektrosleeptime)
			print pluginPrintname, "Set up 'Go to standby now' timer (CheckStandby)"

		self.TimerSleep = eTimer()
		self.TimerSleep.callback.append(self.CheckElektro)
		self.TimerSleep.startLongTimer(elektrostarttime)
		print pluginPrintname, "Set up main timer (CheckElectro)"
		if debug:
			print pluginPrintname, "Translation test:", _("Standby on boot")

	def CheckStandby(self):
		print pluginPrintname, "Showing Standby Sceen"
		try:
			self.session.openWithCallback(self.DoElektroStandby,MessageBox,_("Go to Standby now?"),type = MessageBox.TYPE_YESNO,
					timeout = config.plugins.elektro.standbyOnBootTimeout.value)
		except:
			# Couldn't be shown. Restart timer.
			print pluginPrintname, "Failed Showing Standby Sceen"
			self.TimerStandby.startLongTimer(elektrostarttime)


	def DoElektroStandby(self,retval):
		if (retval):
			# Yes, go to standby
			Notifications.AddNotification(Standby.Standby)


	def CheckElektro(self):
		# first set the next wakeuptime - it would be much better to call that function on sleep. This will be a todo!
		setNextWakeuptime()

		# convert to seconds after midnight
		time_s = getTime()
		ltime = localtime()
		if config.plugins.elektro.profile.value == "1":
			config_wakeup = config.plugins.elektro.wakeup
			config_sleep = config.plugins.elektro.sleep
			config_nextday = config.plugins.elektro.nextday
		else:
			config_wakeup = config.plugins.elektro.wakeup2
			config_sleep = config.plugins.elektro.sleep2
			config_nextday = config.plugins.elektro.nextday2

		# Which day is it? The next day starts at nextday
		if debug:
			print pluginPrintname, "Current Weekday:", str(ltime.tm_wday)
		if time_s < clkToTime(config_nextday):
			day = (ltime.tm_wday - 1) % 7
		else:
			day = ltime.tm_wday
		if debug:
			print pluginPrintname, "Weekday after nextday processing:", str(day)

		# Let's get the day
		wakeuptime = clkToTime(config_wakeup[day])
		sleeptime = clkToTime(config_sleep[day])

		if debug:
			print pluginPrintname, "Profile:", config.plugins.elektro.profile.value
			print pluginPrintname, "Nextday:", getPrintTime(clkToTime(config.plugins.elektro.nextday))
			print pluginPrintname, "Current time:", getPrintTime(time_s)
			print pluginPrintname, "Wakeup time:", getPrintTime(wakeuptime)
			print pluginPrintname, "Sleep time:", getPrintTime(sleeptime)

		# Convert into relative Times (seconds after day start at nextday)
		time_s = getReltime(time_s)
		wakeuptime = getReltime(wakeuptime)
		sleeptime = getReltime(sleeptime)

		if debug:
			print pluginPrintname, "Current Rel-time:", getPrintTime(time_s)
			print pluginPrintname, "Wakeup Rel-time:", getPrintTime(wakeuptime)
			print pluginPrintname, "Sleep Rel-time:", getPrintTime(sleeptime)


		# let's see if we should be sleeping
		trysleep = False
		if time_s < (wakeuptime - elektroShutdownThreshold): # Wakeup is in the future -> sleep!
			trysleep = True
			print pluginPrintname, "Wakeup is in the future -> Sleep:", str(time_s), " <", str(wakeuptime)
		if sleeptime < time_s : #Sleep is in the past -> sleep!
			trysleep = True
			print pluginPrintname, "Sleep is in the past -> Sleep:", str(sleeptime), " <", str(time_s)

		if debug:
			print pluginPrintname, "(1) trysleep:", trysleep
		# We are not tying to go to sleep anymore -> maybe go to sleep again the next time
		if trysleep == False:
			self.dontsleep = False
			if debug:
				print pluginPrintname, "setting dontsleep to false"

		if debug:
			print pluginPrintname, "(2) trysleep:", trysleep
		# The User aborted to got to sleep -> Don't go to sleep.
		if self.dontsleep:
			print pluginPrintname, "dontsleep is true, setting trysleep to false"
			trysleep = False

		# If we are in holydaymode we should try to got to sleep anyway
		# This should be set after self.dontsleep has been handled
		if debug:
			print pluginPrintname, "(3) trysleep:", trysleep
		if config.plugins.elektro.holiday.value:
			print pluginPrintname, "holiday mode, setting trysleep to true"
			trysleep = True

		# We are not enabled -> Dont go to sleep (This could have been catched earlier!)
		if debug:
			print pluginPrintname, "(4) trysleep:", trysleep
		if config.plugins.elektro.enable.value == False:
			print pluginPrintname, "plugin not enabled, setting trysleep to false"
			trysleep = False

		# Only go to sleep if we are in standby or sleep is forced by settings
		if debug:
			print pluginPrintname, "(5) trysleep:", trysleep
			print pluginPrintname, "in standby returns", Standby.inStandby
			print pluginPrintname, "forecesleep is", config.plugins.elektro.force.value
		if not ((Standby.inStandby) or (config.plugins.elektro.force.value == True) ):
			print pluginPrintname, "not in standby and not enforcing to sleep, so setting trysleep to false"
			trysleep = False

		# No Sleep while recording
		if debug:
			print pluginPrintname, "(6) trysleep:", trysleep
		if self.session.nav.RecordTimer.isRecording():
			print pluginPrintname, "isRecording is true, setting trysleep to false"
			trysleep = False

		# Will there be a recording in a short while?
		if debug:
			print pluginPrintname, "(7) trysleep:", trysleep
		nextRecTime = self.session.nav.RecordTimer.getNextRecordingTime()
		if (nextRecTime > 0) and (nextRecTime - (long)(time()) < elektroShutdownThreshold):
			print pluginPrintname, "recording about to start", nextRecTime, "-> setting trysleep to false"
			trysleep = False

		if debug:
			print pluginPrintname, "(8) trysleep:", trysleep
		# No Sleep on HDD running - joergm6
		if (trysleep == True) and (config.plugins.elektro.hddsleep.value == True) and (harddiskmanager.HDDCount() > 0):
			hddlist = harddiskmanager.HDDList()
			if hddlist[0][1].model().startswith("ATA"):
				if not hddlist[0][1].isSleeping():
					print pluginPrintname, hddlist[0][1].model(), "online -> setting trysleep to false"
					trysleep = False

		if debug:
			print pluginPrintname, "(9) trysleep:", trysleep
		# No Sleep on Online IPs - joergm6
		if (trysleep == True) and (config.plugins.elektro.IPenable.value == True):
			for i in range(10):
				ip = "%d.%d.%d.%d" % tuple(config.plugins.elektro.ip[i].value)
				if ip != "0.0.0.0":
					if ping.doOne(ip,0.1) != None:
						print pluginPrintname, ip, "online -> don't sleep"
						trysleep = False
						break

		print pluginPrintname, "About to go to sleep now?", trysleep

		# Looks like there really is a reason to go to sleep -> Lets try it!
		if trysleep:
			try:
				self.session.openWithCallback(self.DoElektroSleep, MessageBox, _("Go to sleep now?"),type = MessageBox.TYPE_YESNO,timeout = 60)
			except:
				# reset the timer and try again
				self.TimerSleep.startLongTimer(elektrostarttime)

		# set Timer, which calls this function again.
		self.TimerSleep.startLongTimer(elektrostarttime)


	def DoElektroSleep(self,retval):
		config_NASenable = True if config.plugins.elektro.NASenable.value == config.plugins.elektro.profile.value else False
		if config.plugins.elektro.profileShift.value == True:
			config.plugins.elektro.profile.value = "1" if config.plugins.elektro.profile.value == "2" else "2"
			config.plugins.elektro.profile.save()
			setNextWakeuptime()
		if (retval):
			# os.system("wall 'Powermanagent does Deepsleep now'")
			# Notifications.AddNotification(TryQuitMainloop,1)
			# 1 = Deep Standby -> enigma2:/doc/RETURNCODES

			global inTryQuitMainloop
			if Standby.inTryQuitMainloop == False:
				if config.plugins.elektro.NASenable.value == "true" or config_NASenable:
					ret = NASpowerdown(config.plugins.elektro.NASname.value, config.plugins.elektro.NASuser.value, config.plugins.elektro.NASpass.value, config.plugins.elektro.NAScommand.value, config.plugins.elektro.NASport.value)
				configfile.save()
				self.session.open(Standby.TryQuitMainloop, 1) # <- This might not work reliably
				#quitMainloop(1)
		else:
			# Dont try to sleep until next wakeup
			self.dontsleep = True
			#Start the timer again
			self.TimerSleep.startLongTimer(elektrostarttime)
