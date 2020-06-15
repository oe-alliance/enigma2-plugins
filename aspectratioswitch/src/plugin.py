# -*- coding: UTF-8 -*-

###############################################################################  
# Quick'n'easy switching of aspect ratio setting via configurable remote control keys (Enigma2)
# © 2007 schaumkeks <schaumkeks@yahoo.de>
# This is free software. You are allowed to modify and use it as long as you leave the copyright.
###############################################################################  

# for localized messages
from __future__ import print_function
from . import _

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# MessageBox
from Screens.MessageBox import MessageBox
from Tools import Notifications

# Configuration
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSubDict, ConfigEnableDisable, ConfigYesNo, ConfigSelection
from Components.Sources.StaticText import StaticText
from Components.Label import Label

# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components
from Components.AVSwitch import AVSwitch

# ActionMap
from GlobalActions import globalActionMap
from Components.ActionMap import ActionMap

# KeyMap
import keymapparser

# OS
import os.path

############################################################################### 
# History:
# 0.4 First public version (schaumkeks)
# 0.5 Die Anzeige des aktuellen Seitenverhältnis kann über das Konfigurationsmenü abgeschaltet werden. (schaumkeks)
# 0.6 Abhängigkeit Enigma2 2.2cvs20070620 (schaumkeks)
#	Nicht benutzte Seitenverhältnisse können im Konfigurationsmenü deaktiviert werden
# 0.7 Es kann im Konfigurationsmenü zwischen Tastenbelegungen gewählt werden. 
#	Derzeit: Bouquet oder Shift-TV (eine Richtung) (schaumkeks)
# 0.8 Help-Taste als Möglichkeit zum Umschalten hinzugefügt (schaumkeks)
#	Aktivierung bei Keymap-wechsel im deaktivierten Zustand behoben
# 0.9 Option added to set a specific aspect ratio on enigma startup (kay_71)
# 1.0 Switch keys assigned to Bouquet long, Help long, Radio long and PVR long (JuSt611)
#	Keymap modified to enable Quickbuttons with long key press
#	Plugin Setup Start optionally shown in Plugin Menu or Extensions Menu
#	German localization added       
VERSION = "1.0"
###############################################################################
pluginPrintname = "[AspectRatioSwitch Ver. %s]" %VERSION

ASPECT = ["4_3_letterbox", "4_3_panscan", "16_9", "16_9_always", "16_10_letterbox", "16_10_panscan", "16_9_letterbox"]
ASPECTMSG = {
		"4_3_letterbox": _("4:3 Letterbox"),
		"4_3_panscan": _("4:3 PanScan"), 
		"16_9": _("16:9"), 
		"16_9_always": _("16:9 always"),
		"16_10_letterbox": _("16:10 Letterbox"),
		"16_10_panscan": _("16:10 PanScan"), 
		"16_9_letterbox": _("16:9 Letterbox")}

PACKAGE_PATH = os.path.dirname(str((globals())["__file__"]))
KEYMAPPINGS = {'bouquet': os.path.join(PACKAGE_PATH, 'keymap-bouquet.xml'), 'help': os.path.join(PACKAGE_PATH, 'keymap-help.xml'), 'radio': os.path.join(PACKAGE_PATH, 'keymap-radio.xml'), 'video': os.path.join(PACKAGE_PATH, 'keymap-video.xml')}

config.plugins.AspectRatioSwitch = ConfigSubsection()
config.plugins.AspectRatioSwitch.enabled = ConfigEnableDisable(default = False)
config.plugins.AspectRatioSwitch.keymap = ConfigSelection({'bouquet': _('Bouquet +/- long'), 'help': _('Help key long'), 'radio': _('Radio key long'), 'video': _('PVR key long')}, default='bouquet')
config.plugins.AspectRatioSwitch.autostart_ratio_enabled = ConfigEnableDisable(default = False)
config.plugins.AspectRatioSwitch.autostart_ratio = ConfigSelection(choices = [("0", _("4:3 Letterbox")), ("1", _("4:3 PanScan")), ("2", _("16:9")), ("3", _("16:9 always")), ("4", _("16:10 Letterbox")), ("5", _("16:10 PanScan")), ("6", _("16:9 Letterbox"))], default = "6")
config.plugins.AspectRatioSwitch.showmsg = ConfigYesNo(default = True)
config.plugins.AspectRatioSwitch.modes = ConfigSubDict()
config.plugins.AspectRatioSwitch.menu = ConfigSelection(default = 'plugin', choices = [('plugin', _('Plugin menu')), ('extensions', _('Extensions menu'))])

for aspect in ASPECT:
	config.plugins.AspectRatioSwitch.modes[aspect] = ConfigYesNo(default = True)

aspect_ratio_switch = None

class AspectRatioSwitchSetup(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="550,500" title="AspectRatioSwitch Setup">
			<widget name="config" position="10,0" size="530,335" scrollbarMode="showOnDemand" enableWrapAround="1" />
			<ePixmap pixmap="skin_default/div-h.png" position="0,340" zPosition="1" size="550,2" />
			<widget name="label" position="10,355" size="530,100" font="Regular;18" halign="left"  />
			<ePixmap pixmap="skin_default/buttons/red.png" position="10,460" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_red" position="10,460" size="140,40" transparent="1" halign="center" valign="center" zPosition="2" foregroundColor="white" font="Regular;18" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="180,460" size="140,40" transparent="1" alphatest="on" />
			<widget render="Label" source="key_green" position="180,460" size="140,40" transparent="1" halign="center" valign="center" zPosition="2" foregroundColor="white" font="Regular;18" />
 		</screen>"""

	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		#Summary
		self.setup_title = _("AspectRatioSwitch Setup")
		
		self.list = []
		self.list.append(getConfigListEntry(_("Quick switching via remote control"), config.plugins.AspectRatioSwitch.enabled))
		self.list.append(getConfigListEntry(_("Key mapping"), config.plugins.AspectRatioSwitch.keymap))
		self.list.append(getConfigListEntry(_("Show switch message"), config.plugins.AspectRatioSwitch.showmsg))
		for aspect in ASPECT:
			self.list.append(getConfigListEntry(_("Include %s") % ASPECTMSG[aspect], config.plugins.AspectRatioSwitch.modes[aspect]))
		self.list.append(getConfigListEntry(_("Set aspect ratio on startup"), config.plugins.AspectRatioSwitch.autostart_ratio_enabled))
		self.list.append(getConfigListEntry(_("Startup aspect ratio"), config.plugins.AspectRatioSwitch.autostart_ratio))
		self.list.append(getConfigListEntry(_('Show Setup in'), config.plugins.AspectRatioSwitch.menu,))
		
		ConfigListScreen.__init__(self, self.list)		

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))		
		self["label"] = Label(_("Use the configured key(s) on your remote control to switch aspect ratio modes. If any 'Quickbutton' actions were assigned to these keys, they will be disabled as long as this plugin is activated!"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions"],
		{
			"save": self.save,
			"ok": self.save,
			"cancel": self.keyCancel
		}, -2)

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(' '.join((_("AspectRatioSwitch Setup"), _("Ver."), VERSION)))

	def save(self):
		global aspect_ratio_switch
		
		if len([modeconf for modeconf in list(config.plugins.AspectRatioSwitch.modes.values()) if modeconf.value]) < 2:
			self.session.open(MessageBox, _("You need to include at least %d aspect ratio modes!") % 2, MessageBox.TYPE_ERROR)
			return

		if config.plugins.AspectRatioSwitch.enabled.isChanged():
			if config.plugins.AspectRatioSwitch.enabled.value:
				aspect_ratio_switch = AspectRatioSwitch()
				aspect_ratio_switch.enable()
			elif aspect_ratio_switch is not None:
				aspect_ratio_switch.disable()
		elif aspect_ratio_switch is not None:
			#TODO: if aspects changed (no isChanged() on ConfigSubDict?)
			aspect_ratio_switch.reload_enabledaspects()
			if config.plugins.AspectRatioSwitch.keymap.isChanged():
				aspect_ratio_switch.change_keymap(config.plugins.AspectRatioSwitch.keymap.value)

		for x in self["config"].list:
			x[1].save()
		
		self.close()

class AspectRatioSwitch:

	def __init__(self):
		self.reload_enabledaspects()

	def change_keymap(self, keymap):
		if keymap not in KEYMAPPINGS:
			return
		self.unload_keymap()
		try:
			keymapparser.readKeymap(KEYMAPPINGS[keymap])
		except IOError as xxx_todo_changeme:
			(errno, strerror) = xxx_todo_changeme.args
			config.plugins.AspectRatioSwitch.enabled.setValue(False)
			self.disable()
			Notifications.AddPopup(text=_("Changing keymap failed (%s).") % strerror, type=MessageBox.TYPE_ERROR, timeout=10, id='AspectRatioSwitch')
			return
		global globalActionMap
		globalActionMap.actions['switchAspectUp'] = self.switchAspectRatioUp
		globalActionMap.actions['switchAspectDown'] = self.switchAspectRatioDown

	def unload_keymap(self):
		for keymap in list(KEYMAPPINGS.values()):
			keymapparser.removeKeymap(keymap)
		
		global globalActionMap
		if 'switchAspectUp' in globalActionMap.actions:
			del globalActionMap.actions['switchAspectUp']
		if 'switchAspectDown' in globalActionMap.actions:
			del globalActionMap.actions['switchAspectDown']

	def reload_enabledaspects(self):
		self.enabledaspects = []
		for aspectnum, aspect in enumerate(ASPECT):
			if config.plugins.AspectRatioSwitch.modes[aspect].value:
				self.enabledaspects.append(aspectnum)
		print(pluginPrintname, "Aspect modes in cycle:", self.enabledaspects)

	def enable(self):
		self.change_keymap(config.plugins.AspectRatioSwitch.keymap.value)
		self.reload_enabledaspects()
	
	def disable(self):
		global aspect_ratio_switch
		self.unload_keymap()
		aspect_ratio_switch = None

	def switchAspectRatioUp(self):
		self.switchAspectRatio(+1)
		
	def switchAspectRatioDown(self):
		self.switchAspectRatio(-1)

	def switchAspectRatio(self, direction=1):
		if len(self.enabledaspects) < 2:
			return
		iAVSwitch = AVSwitch()
		aspectnum = iAVSwitch.getAspectRatioSetting()
		try:
			localaspectnum = self.enabledaspects.index(aspectnum)
		except ValueError:
			localaspectnum = 0
		newaspectnum = self.enabledaspects[(localaspectnum + direction) % len(self.enabledaspects)]
		iAVSwitch.setAspectRatio(newaspectnum)
		config.av.aspectratio.setValue(ASPECT[newaspectnum])
		if config.plugins.AspectRatioSwitch.showmsg.value:
			Notifications.AddPopup(text=_("Aspect ratio switched from:\n   %s\nto:\n   %s") % (ASPECTMSG[ASPECT[aspectnum]], ASPECTMSG[ASPECT[newaspectnum]]), type=MessageBox.TYPE_INFO, timeout=5, id='AspectRatioSwitch')
			print(pluginPrintname, "Aspect ratio switched from %d - %s to %d - %s" % (aspectnum, ASPECT[aspectnum], newaspectnum, ASPECT[newaspectnum]))
			
def autostart(reason, **kwargs):
	#STANDARD beim Systemstart	
	global aspect_ratio_switch
	if reason == 0: # startup
		keymappath = "/usr/share/enigma2/keymap.xml"
		if os.path.exists(keymappath):
			keymapfile = open(keymappath, "r")
			keymaptext = keymapfile.read()
			keymapfile.close()
			changed = False
			if '<key id="KEY_CHANNELUP" mapto="openServiceList" flags="m" />' in keymaptext:
				keymaptext = keymaptext.replace('<key id="KEY_CHANNELUP" mapto="openServiceList" flags="m" />', '<key id="KEY_CHANNELUP" mapto="openServiceList" flags="b" />')
				changed = True
			if '<key id="KEY_CHANNELDOWN" mapto="openServiceList" flags="m" />' in keymaptext:
				keymaptext = keymaptext.replace('<key id="KEY_CHANNELDOWN" mapto="openServiceList" flags="m" />', '<key id="KEY_CHANNELDOWN" mapto="openServiceList" flags="b" />')
				changed = True
			if '<key id="KEY_VIDEO" mapto="showMovies" flags="m" />' in keymaptext:
				keymaptext = keymaptext.replace('<key id="KEY_VIDEO" mapto="showMovies" flags="m" />', '<key id="KEY_VIDEO" mapto="showMovies" flags="b" />')
				changed = True
			if '<key id="KEY_RADIO" mapto="showRadio" flags="m" />' in keymaptext:
				keymaptext = keymaptext.replace('key id="KEY_RADIO" mapto="showRadio" flags="m" />', 'key id="KEY_RADIO" mapto="showRadio" flags="b" />')
				changed = True
			if '<key id="KEY_HELP" mapto="displayHelp" flags="m" />' in keymaptext:
				keymaptext = keymaptext.replace('<key id="KEY_HELP" mapto="displayHelp" flags="m" />', '<key id="KEY_HELP" mapto="displayHelp" flags="b" />')
				changed = True
			if changed:
				print(pluginPrintname, "Preparing keymap.xml...")
				keymapfile = open(keymappath, "w")
				keymapfile.write(keymaptext)
				keymapfile.close()
				keymapparser.removeKeymap(keymappath)
				keymapparser.readKeymap(keymappath)
		iAVSwitch = AVSwitch()
		if config.plugins.AspectRatioSwitch.autostart_ratio_enabled.value:
			iAVSwitch.setAspectRatio(int(config.plugins.AspectRatioSwitch.autostart_ratio.value))
			config.av.aspectratio.setValue(ASPECT[int(config.plugins.AspectRatioSwitch.autostart_ratio.value)])
			print(pluginPrintname, "startup, keymap =", config.plugins.AspectRatioSwitch.keymap)
			print(pluginPrintname, "Initially set to:", ASPECT[int(config.plugins.AspectRatioSwitch.autostart_ratio.value)])	
		else:
			print(pluginPrintname, "Initiation disabled")

		if config.plugins.AspectRatioSwitch.enabled.value and aspect_ratio_switch is None:
			aspect_ratio_switch = AspectRatioSwitch()
			aspect_ratio_switch.enable()
	elif reason == 1:
		print(pluginPrintname, "shutdown")
		if aspect_ratio_switch is not None:
			aspect_ratio_switch.disable()

def main(session, **kwargs):
	session.open(AspectRatioSwitchSetup)

def Plugins(**kwargs):
			
	list = [
		PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart)
		]
	if config.plugins.AspectRatioSwitch.menu.value == "plugin":
		list.append (PluginDescriptor(name=_("Aspect Ratio Switch setup"),	description=_("Quick switching of aspect ratio setting"),
		where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
	)
	else:
		list.append (PluginDescriptor(name=_("Aspect Ratio Switch setup"), description=_("Quick switching of aspect ratio setting"),
		where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main),
	)

	return list
