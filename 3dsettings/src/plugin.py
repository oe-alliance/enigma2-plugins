#
#  3D Settings E2-Plugin
#
#  Coded by TheDOC and Dr.Best (c) 2011
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

from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, ConfigYesNo, getConfigListEntry,\
	ConfigSlider, ConfigSelection
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.PluginComponent import plugins
from Components.ServiceEventTracker import ServiceEventTracker
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from enigma import iPlayableService, iServiceInformation, eServiceCenter, eServiceReference, eDBoxLCD
from ServiceReference import ServiceReference
from os.path import basename as os_basename
from boxbranding import getImageDistro

# for localized messages
from . import _

THREE_D_OFF = 0
THREE_D_SIDE_BY_SIDE = 1
THREE_D_TOP_BOTTOM = 2

modes = {	THREE_D_OFF: "off",
			THREE_D_SIDE_BY_SIDE: "sbs",
			THREE_D_TOP_BOTTOM: "tab" }
reversemodes = dict((value, key) for key, value in modes.iteritems())

def setZOffset(configElement):
	open("/proc/stb/fb/primary/zoffset", "w").write(str(configElement.value))

def getmode():
	mode = reversemodes.get(open("/proc/stb/fb/primary/3d", "r").read().strip(), None)
	return mode

def toggleDisplay(configElement):
	from Components.Lcd import LCD
	if configElement.value == False: # turn display on
		print "[3D Settings] turning display on"
		LCD().setBright(config.lcd.bright.value)
	elif (config.plugins.threed.disableDisplay.value == True) and (getmode() != THREE_D_OFF): # turn display off
		print "[3D Settings] turning display off"
		LCD().setBright(0)
	eDBoxLCD.getInstance().update()

def leaveStandby():
	toggleDisplay(config.plugins.threed.toggleState)

def standbyCounterChanged(configElement):
	from Screens.Standby import inStandby
	inStandby.onClose.append(leaveStandby)

config.plugins.threed = ConfigSubsection()
config.plugins.threed.showSBSmenu = ConfigYesNo(default = False)
config.plugins.threed.showTBmenu = ConfigYesNo(default = False)
config.plugins.threed.zoffset = ConfigSlider(default = 0, increment = 1, limits = [0, 10])
config.plugins.threed.zoffset.addNotifier(setZOffset)
config.plugins.threed.autothreed = ConfigSelection(default="0", choices = [("0", _("off")),("1", _("on with side by side")),("2", _("on with top/bottom"))])

def switchmode(mode):
	if mode in modes.keys():
		print "[3D Settings] switching to mode ", mode
		open("/proc/stb/fb/primary/3d", "w").write(modes[mode])
		AutoThreeD.instance.setLastMode(mode)
		if eDBoxLCD.getInstance().detected(): # display found, update it
			config.plugins.threed.toggleState.setValue(getmode() != THREE_D_OFF)
			toggleDisplay(config.plugins.threed.toggleState)

def switchsbs(session, **kwargs):
	switchmode(THREE_D_SIDE_BY_SIDE)

def switchtb(session, **kwargs):
	switchmode(THREE_D_TOP_BOTTOM)

def switchoff(session, **kwargs):
	switchmode(THREE_D_OFF)

class AutoThreeD(Screen):
	instance = None
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.__event_tracker = ServiceEventTracker(screen = self, eventmap =
			{
				iPlayableService.evUpdatedInfo: self.__evUpdatedInfo,
				iPlayableService.evStart: self.__evStart
			})
		self.newService = False
		self.lastmode = getmode()
		assert not AutoThreeD.instance, "only one AutoThreeD instance is allowed!"
		AutoThreeD.instance = self # set instance

		if eDBoxLCD.getInstance().detected(): # display found
			from Components.config import NoSave
			config.plugins.threed.disableDisplay = ConfigYesNo(default = False)
			config.plugins.threed.disableDisplay.addNotifier(toggleDisplay, initial_call = False)
			from Components.config import NoSave
			config.plugins.threed.toggleState = NoSave(ConfigYesNo(default = True)) # True = display on, False = display off
			config.misc.standbyCounter.addNotifier(standbyCounterChanged, initial_call = False)

	def __evStart(self):
		self.newService = True

	def __evUpdatedInfo(self):
		if self.newService and config.plugins.threed.autothreed.value != "0" and self.session.nav.getCurrentlyPlayingServiceReference():
			self.newService = False
			ref = self.session.nav.getCurrentService()
			serviceRef = self.session.nav.getCurrentlyPlayingServiceReference()
			spath = serviceRef.getPath()
			if spath:
				if spath[0] == '/':
					serviceHandler = eServiceCenter.getInstance()
					r = eServiceReference(ref.info().getInfoString(iServiceInformation.sServiceref))
					info = serviceHandler.info(r)
					if info:
						name = ServiceReference(info.getInfoString(r, iServiceInformation.sServiceref)).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
					else:
						name = os_basename(spath) # filename
				else:
					name = serviceRef.getName() # partnerbox servicename
			else:
				name =  ServiceReference(ref.info().getInfoString(iServiceInformation.sServiceref)).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
			if "3d" in name.lower():
				if config.plugins.threed.autothreed.value == "1":
					mode = THREE_D_SIDE_BY_SIDE
				else:
					mode = THREE_D_TOP_BOTTOM
			else:
				mode = THREE_D_OFF
			if self.lastmode != mode:
				switchmode(mode)

	def setLastMode(self, mode):
		self.lastmode = mode

class ThreeDSettings(Screen, ConfigListScreen):
	skin = """
		<screen position="center,center" size="570,420" title="3D settings" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<widget source="red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
			<widget source="blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />

			<widget name="config" position="10,50" size="550,320" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, args = None):
		Screen.__init__(self, session)

		self["red"] = StaticText(_("Cancel"))
		self["green"] = StaticText(_("OK"))
		self["yellow"] = StaticText("")
		self["blue"] = StaticText("")
		self.updateButtons()

		self.list = []
		ConfigListScreen.__init__(self, self.list, session = self.session)
		self.createSetup()

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.save,
			"cancel": self.cancel,
			"red": self.cancel,
			"green": self.save,
			"yellow": self.sideBySide,
			"blue": self.topBottom,

		}, -1)

	def updateButtons(self):
		currentmode = getmode()
		if currentmode == THREE_D_OFF:
			self["yellow"].setText(_("Side by side"))
			self["blue"].setText(_("Top/Bottom"))
		elif currentmode == THREE_D_SIDE_BY_SIDE:
			self["yellow"].setText(_("2D mode"))
			self["blue"].setText("")
		elif currentmode == THREE_D_TOP_BOTTOM:
			self["blue"].setText(_("2D mode"))
			self["yellow"].setText("")

	def createSetup(self):
		self.list = []
		self.list.append(getConfigListEntry(_("Show side by side option in extension menu"), config.plugins.threed.showSBSmenu))
		self.list.append(getConfigListEntry(_("Show top/bottom option in extension menu"), config.plugins.threed.showTBmenu))
		self.list.append(getConfigListEntry(_("Switch OSD automatically"), config.plugins.threed.autothreed))
		if eDBoxLCD.getInstance().detected(): # display found
			self.list.append(getConfigListEntry(_("Turn off display"), config.plugins.threed.disableDisplay))
		currentmode = getmode()
		if currentmode in [THREE_D_SIDE_BY_SIDE, THREE_D_TOP_BOTTOM]:
			self.list.append(getConfigListEntry(_("Offset"), config.plugins.threed.zoffset))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def cancel(self):
		config.plugins.threed.zoffset.save()
		self.keyCancel()

	def save(self):
		self.saveAll()
		config.plugins.threed.zoffset.save()
		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
		self.close()

	def sideBySide(self):
		currentmode = getmode()
		if currentmode == THREE_D_OFF:
			switchmode(THREE_D_SIDE_BY_SIDE)
		elif currentmode == THREE_D_SIDE_BY_SIDE:
			switchmode(THREE_D_OFF)
		self.updateButtons()
		self.createSetup()

	def topBottom(self):
		currentmode = getmode()
		if currentmode == THREE_D_OFF:
			switchmode(THREE_D_TOP_BOTTOM)
		elif currentmode == THREE_D_TOP_BOTTOM:
			switchmode(THREE_D_OFF)
		self.updateButtons()
		self.createSetup()

def opensettings(session, **kwargs):
	session.open(ThreeDSettings)

def settings(menuid, **kwargs):
	if getImageDistro() in ('openhdf'):
		if menuid != "video_menu":
			return [ ]
	else:
		if menuid != "system":
			return []
	return [(_("3D settings"), opensettings, "3d_settings", 10)]

def autostart(session, **kwargs):
	AutoThreeD(session)

def Plugins(**kwargs):
	pluginlist = []
	if config.plugins.threed.showSBSmenu.value:
		pluginlist.append(PluginDescriptor(name = _("3D: Enable side by side menu"), description = _("3D: Enable side by side menu"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = switchsbs, needsRestart = False))
	if config.plugins.threed.showTBmenu.value:
		pluginlist.append(PluginDescriptor(name = _("3D: Enable top/bottom menu"), description = _("3D: Enable top/bottom menu"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = switchtb, needsRestart = False))
	if config.plugins.threed.showSBSmenu.value or config.plugins.threed.showTBmenu.value:
		pluginlist.append(PluginDescriptor(name = _("3D: disable 3D menu"), description = _("3D: 2D menu"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = switchoff, needsRestart = False))
	pluginlist.append(PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart))
	pluginlist.append(PluginDescriptor(name = _("3D settings"), description = _("Change 3D settings"), icon = "plugin.png", where = PluginDescriptor.WHERE_MENU, fnc = settings))
	return pluginlist
