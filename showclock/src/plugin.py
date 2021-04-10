# -*- coding: utf-8 -*-
#
#  Show Clock E2
#
#  $Id$
#
#  Coded by JuSt611 © 2011
#  Derived from Permanent Clock plugin written by AliAbdul
#  and placed in the public domain. He has my thanks.
#  Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=???
#
#  Provided with no warranties of any sort.
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

from enigma import ePoint, eTimer, getDesktop

# MessageBox
from Screens.MessageBox import MessageBox
from Tools import Notifications

# ActionMap
from Components.ActionMap import ActionMap
from GlobalActions import globalActionMap

# GUI (Components)
from Components.Sources.StaticText import StaticText

# KeynMap
from keymapparser import readKeymap, removeKeymap

# Configuration
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSelection, ConfigText, ConfigNumber
from Components.Sources.StaticText import StaticText

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Screens.PiPSetup import clip

# GUI (Summary)
from Screens.Setup import SetupSummary


###############################################################################
VERSION = "0.6"
# History:
# 0.4 First public version
# 0.5 Minor code optimization
# 0.6 Simplify translation code: Setting the os LANGUAGE variable isn't needed anymore
pluginPrintname = "[ShowClock Ver. %s]" % VERSION
debug = False # If set True, plugin will print some additional status info to track logic flow
###############################################################################

config.plugins.ShowClock = ConfigSubsection()
config.plugins.ShowClock.name = ConfigText(default=_('Show Clock setup'), fixed_size=False, visible_width=80)
config.plugins.ShowClock.description = ConfigText(default=_('Push "Exit" long to show/hide clock'), fixed_size=False, visible_width=80)
config.plugins.ShowClock.menu = ConfigSelection(default='plugin', choices=[('plugin', _('Plugin menu')), ('extensions', _('Extensions menu'))])
config.plugins.ShowClock.showTimeout = ConfigNumber(default=10)

width = getDesktop(0).size().width()
height = getDesktop(0).size().height()
config.plugins.ShowClock.position_x = ConfigNumber(default=int(width * 0.7))
config.plugins.ShowClock.position_y = ConfigNumber(default=45)
if debug:
	print pluginPrintname, "Clock X,Y position: %d,%d" % (config.plugins.ShowClock.position_x.value, config.plugins.ShowClock.position_y.value)

##############################################################################


class ShowClockSetup(Screen, ConfigListScreen): # config

	skin = """
		<screen name="ShowClock" position="center,center" size="600,290" title="Show Clock Setup" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="5,5" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="155,5" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="305,5" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="455,5" zPosition="0" size="140,40" transparent="1" alphatest="on" />

			<widget render="Label" source="key_red" position="5,5" size="140,40" zPosition="2" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_green" position="155,5" size="140,40" zPosition="2" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_yellow" position="305,5" size="140,40" zPosition="2" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget render="Label" source="key_blue" position="455,5" size="140,40" zPosition="2" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />

			<widget name="config" position="5,60" size="590,105" scrollbarMode="showOnDemand" />

			<ePixmap pixmap="skin_default/div-h.png" position="0,170" zPosition="1" size="600,2" />
			<widget source="help" render="Label" position="5,185" size="590,100" font="Regular;21" />
		</screen>"""

	def __init__(self, session):

		Screen.__init__(self, session)
		self.session = session
		#Summary
		self.setup_title = _("Show Clock Setup")

		self.onChangedEntry = []

		self.list = [
			getConfigListEntry(_('Clock show timeout'), config.plugins.ShowClock.showTimeout,
				_('Specify how long (seconds) the clock shall be shown before it disappears. Set to "0" to show clock until hidden manually.')),
			getConfigListEntry(_('Show in'), config.plugins.ShowClock.menu,
				_('Specify whether plugin shall show up in plugin menu or extensions menu (needs GUI restart)')),
			getConfigListEntry(_('Name'), config.plugins.ShowClock.name,
				_('Specify plugin name to be used in menu (needs GUI restart).')),
			getConfigListEntry(_("Description"), config.plugins.ShowClock.description,
				_('Specify plugin description to be used in menu (needs GUI restart).')),
			]

		ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changed)

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

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("Help"))
		self["key_blue"] = StaticText(_("Move clock"))

		self["help"] = StaticText()

		# Define Actions
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
			{
			"red": self.keyCancel,
			"green": self.keySave,
			"yellow": self.keyHelp,
			"blue": self.keyMove,
			"cancel": self.keyCancel,
			"save": self.keySave,
			"ok": self.keySave,
			}, -2)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(' '.join((_("Show Clock Setup"), _("Ver."), VERSION)))

	def configHelp(self):
		self["help"].text = self["config"].getCurrent()[2]

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

	def keyCancel(self):
		self.hideKeypad() # close help window if open
		ConfigListScreen.keyCancel(self)

	def keySave(self):
		self.hideKeypad() # close help window if open
		ConfigListScreen.keySave(self)

	def hideKeypad(self):
		try:
			self["config"].getCurrent()[1].help_window.instance.hide()
		except AttributeError:
			pass

	def createSummary(self):
		return SetupSummary

	def keyHelp(self):
		self.hideKeypad() # close help window if open
		self.session.open(MessageBox,
			_('Modify the settings to match your preferences. To change the clock position, select "Move clock" and relocate using the direction keys. Press OK to store current position and return to the setup menu or EXIT to cancel the moving.\n\nPush key "Exit long" to show the clock while watching TV. Clock will disappear after the specified timeout or by pushing key "Exit long" again.\n\nIf GP3 is installed, weekday shows up in selected language, otherwise always in english.'),
			MessageBox.TYPE_INFO)

	def keyMove(self):
		if debug:
			print pluginPrintname, "Move Clock"
		self.hideKeypad() # close help window if open
		self.session.openWithCallback(
			self.startPositioner, MessageBox,
			_("Please use direction keys to move the clock.\n\nPress OK to store current position and return to the setup menu or EXIT to cancel the moving."),
			type=MessageBox.TYPE_INFO, timeout=10
		)

	def startPositioner(self, answer):
 		self.session.open(ShowClockPositioner)

##############################################################################


class ShowClockPositioner(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin = clockSkin()
		self["actions"] = ActionMap(["PiPSetupActions"],
		{
			"left": self.left,
			"up": self.up,
			"right": self.right,
			"down": self.down,
			"ok": self.ok,
			"cancel": self.cancel
		}, -1)

		self.onShow.append(self.setPosition)

	def setPosition(self):
		self.pos = (config.plugins.ShowClock.position_x.value, config.plugins.ShowClock.position_y.value)
		self.limit = (width - self.instance.size().width(), height - self.instance.size().height())
		if debug:
			print pluginPrintname, "Clock X,Y limit: %d,%d" % (self.limit[0], self.limit[1])
		self.instance.move(ePoint(min(self.pos[0], self.limit[0]), min(self.pos[1], self.limit[1]))) # ensure clock visabilty even if resolution has changed

	def moveRelative(self, x=0, y=0):
		self.pos = (clip(self.pos[0] + x, 0, self.limit[0]), clip(self.pos[1] + y, 0, self.limit[1]))
		self.instance.move(ePoint(self.pos[0], self.pos[1]))

	def left(self):
		self.moveRelative(x=- 10)

	def up(self):
		self.moveRelative(y=- 10)

	def right(self):
		self.moveRelative(x=+ 10)

	def down(self):
		self.moveRelative(y=+ 10)

	def ok(self):
		config.plugins.ShowClock.position_x.value = self.pos[0]
		config.plugins.ShowClock.position_x.save()
		config.plugins.ShowClock.position_y.value = self.pos[1]
		config.plugins.ShowClock.position_y.save()
		self.close()

	def cancel(self):
		self.close()

##############################################################################


class ShowClock(Screen):

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin = clockSkin()
		self.onShow.append(self.setPosition)

	def setPosition(self):
		self.instance.move(ePoint(
			min(config.plugins.ShowClock.position_x.value, width - self.instance.size().width()),
			min(config.plugins.ShowClock.position_y.value, height - self.instance.size().height())
			)) # ensure clock visabilty even if resolution has changed

##############################################################################


class ShowClockMain():
	def __init__(self):
		self.dialog = None
		self.clockShown = False

	def gotSession(self, session):
		self.timer = eTimer() # check timer
		self.timer.callback.append(self.ShowHide)
		global globalActionMap
		readKeymap("/usr/lib/enigma2/python/Plugins/Extensions/ShowClock/keymap.xml")
		self.dialog = session.instantiateDialog(ShowClock)
		globalActionMap.actions['showClock'] = self.ShowHide

	def ShowHide(self):
		if self.clockShown:
			if self.timer.isActive(): # stop timer if running
				self.timer.stop()
			self.clockShown = False
			showClock.dialog.hide()
		else:
			self.clockShown = True
			if config.plugins.ShowClock.showTimeout.value > 0:
				self.timer.startLongTimer(config.plugins.ShowClock.showTimeout.value)
			showClock.dialog.show()


showClock = ShowClockMain()

##############################################################################


def clockSkin():
	if width < 1280:
		if width < 1024: # SD
			currentSkin = """
				<screen name="ShowClock" size="190,60" zPosition="10" backgroundColor="#50202020" flags="wfNoBorder">
					<widget source="global.CurrentTime" render="Label" position="55,12" size="58,17" font="Regular;21" halign="left" valign="center" transparent="1">
						<convert type="ClockToText">Default</convert>
					</widget>
					<widget source="global.CurrentTime" render="Label" position="111,15" size="30,15" font="Regular;16" halign="left" valign="center" transparent="1">
						<convert type="ClockToText">Format::%S</convert>
					</widget>
					<widget source="global.CurrentTime" render="Label" position="0,37" size="190,13" font="Regular;15" halign="center" valign="center" foregroundColor="#999999" transparent="1">
						<convert type="ClockToText">Format:%A, %d.%m.%Y</convert>
					</widget>
				</screen>"""
		else: # XD
			currentSkin = """
				<screen name="ShowClock" size="250,70" zPosition="10" backgroundColor="#50202020" flags="wfNoBorder">
					<widget source="global.CurrentTime" render="Label" position="80,10" size="80,25" font="Regular;24" halign="left" valign="center" transparent="1">
						<convert type="ClockToText">Default</convert>
					</widget>
					<widget source="global.CurrentTime" render="Label" position="142,15" size="40,18" font="Regular;20" halign="left" valign="center" transparent="1">
						<convert type="ClockToText">Format::%S</convert>
					</widget>
					<widget source="global.CurrentTime" render="Label" position="0,40" size="250,25" font="Regular;19" halign="center" valign="center" foregroundColor="#999999" transparent="1">
						<convert type="ClockToText">Format:%A, %d.%m.%Y</convert>
					</widget>
				</screen>"""
	else: # HD
		currentSkin = """
				<screen name="ShowClock" size="280,80" zPosition="10" backgroundColor="#50202020" flags="wfNoBorder">
					<widget source="global.CurrentTime" render="Label" position="85,15" size="80,25" font="Regular;30" halign="left" valign="center" transparent="1">
						<convert type="ClockToText">Default</convert>
					</widget>
					<widget source="global.CurrentTime" render="Label" position="162,20" size="40,18" font="Regular;24" halign="left" valign="center" transparent="1">
						<convert type="ClockToText">Format::%S</convert>
					</widget>
					<widget source="global.CurrentTime" render="Label" position="0,45" size="280,30" font="Regular;23" halign="center" valign="center" foregroundColor="#999999" transparent="1">
						<convert type="ClockToText">Format:%A, %d.%m.%Y</convert>
					</widget>
				</screen>"""

	try: # try to import DateToText converter (GP3 component) to check for its existence
		from Components.Converter.DateToText import DateToText # change converter to obtain localized weekdays
		currentSkin = currentSkin.replace('<convert type="ClockToText">Format:%A, %d.%m.%Y</convert>', '<convert type="DateToText">NNNN, DD.MM.YYYY</convert>')
	except ImportError, ie:
		print pluginPrintname, "DateToText converter not installed:", ie
	return currentSkin

##############################################################################


def sessionstart(reason, **kwargs):
	if reason == 0:
		showClock.gotSession(kwargs["session"])


def setup(session, **kwargs):
	try:
	 	session.open(ShowClockSetup)
	except:
		print pluginPrintname, "Pluginexecution failed"

##############################################################################


def Plugins(**kwargs):

	if debug:
		print pluginPrintname, "Setting entry points"

	list = [
		PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart)
		]
	if config.plugins.ShowClock.menu.value == "plugin":
		list.append(PluginDescriptor(
			name=config.plugins.ShowClock.name.value + " " + _("Ver.") + " " + VERSION,
			description=config.plugins.ShowClock.description.value,
			where=PluginDescriptor.WHERE_PLUGINMENU,
			icon="plugin.png",
			fnc=setup)
		)
	else:
		list.append(PluginDescriptor(
			name=config.plugins.ShowClock.name.value + " " + _("Ver.") + " " + VERSION,
			description=config.plugins.ShowClock.description.value,
			where=PluginDescriptor.WHERE_EXTENSIONSMENU,
			fnc=setup)
		)

	return list
