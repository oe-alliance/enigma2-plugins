# -*- coding: iso-8859-1 -*-
#
# Babelzapper Plugin by gutemine
#
from __future__ import print_function
babelzapper_version = "0.9.6"
babelzapper_plugindir = "/usr/lib/enigma2/python/Plugins/Extensions/BabelZapper"
babelzapper_readme = "%s/readme.txt" % babelzapper_plugindir
babelzapper_menus = "/etc/babelzapper"
#
from RecordTimer import parseEvent
from Plugins.Plugin import PluginDescriptor
from enigma import eTimer, eServiceReference, eServiceCenter, iServiceInformation, eEPGCache, iTimeshiftServicePtr
from Screens.Screen import Screen
from Screens.Setup import SetupSummary
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Components.config import config, ConfigSubsection, ConfigEnableDisable, ConfigInteger, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Label import Label, MultiColorLabel
from Components.SystemInfo import BoxInfo
from Tools.Directories import *
from GlobalActions import globalActionMap
from Components.config import config, ConfigSubsection, ConfigInteger
import os
import keymapparser
from struct import pack
from keyids import KEYIDS

global babelkey
global babeldone
global babelon
babelkey = -1
babeldone = 0
babelon = 0

config.plugins.babelzapper = ConfigSubsection()
config.plugins.babelzapper.enabled = ConfigEnableDisable(default=False)
config.plugins.babelzapper.changetime = ConfigInteger(default=1000, limits=(200, 10000))
config.plugins.babelzapper.exit2escape = ConfigEnableDisable(default=False)


def main(session, **kwargs):
	session.open(BabelzapperConfiguration)


def autostart(reason, **kwargs):
#	global session
	if "session" in kwargs and reason == 0:
		session = kwargs["session"]
		print("[BABELZAPPER] autostart")
		session.open(BabelZapperStartup)


def Plugins(**kwargs):
	return [PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart),
		PluginDescriptor(name="Babelzapper", description=_("Mute button remote control"), where=PluginDescriptor.WHERE_PLUGINMENU, icon="babelzapper.png", fnc=main)]


class BabelzapperConfiguration(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="450,240" title="Babelzapper Plugin" >
		<widget name="config" position="0,0" size="450,200" scrollbarMode="showOnDemand" />
		<widget name="buttonred" position="10,200" size="100,40" backgroundColor="red" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/>
		<widget name="buttongreen" position="120,200" size="100,40" backgroundColor="green" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/>
		<widget name="buttonyellow" position="230,200" size="100,40" backgroundColor="yellow" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/>
		<widget name="buttonblue" position="340,200" size="100,40" backgroundColor="blue" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/>
		<ePixmap position="175,80" size="100,100" pixmap="%s/babel.png" transparent="1" alphatest="on" />
	</screen>""" % babelzapper_plugindir

	def __init__(self, session, args=0):
		Screen.__init__(self, session)
		self.list = []
		self.list.append(getConfigListEntry(_("Enable Babelzapper on Mute"), config.plugins.babelzapper.enabled))
		self.list.append(getConfigListEntry(_("Scroll Time [msec]"), config.plugins.babelzapper.changetime))
		self.list.append(getConfigListEntry(_("Send ESC for EXIT key"), config.plugins.babelzapper.exit2escape))
		self.onShown.append(self.setWindowTitle)
		ConfigListScreen.__init__(self, self.list)
		self.onChangedEntry = []
		self["buttonred"] = Label(_("Cancel"))
		self["buttongreen"] = Label(_("OK"))
		self["buttonyellow"] = Label(_("Info"))
		self["buttonblue"] = Label(_("About"))
		self["setupActions"] = ActionMap(["ColorActions", "SetupActions"],
			{
			"green": self.save,
			"red": self.cancel,
			"yellow": self.readme,
			"blue": self.about,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
			})

	def setWindowTitle(self):
		self.setTitle(_("Babelzapper Plugin"))

	def save(self):
		for x in self["config"].list:
			x[1].save()
		keymapfile = open("/usr/share/enigma2/keymap.xml", "r")
		text = keymapfile.read()
		keymapfile.close()
		keymapfile = open("/usr/share/enigma2/keymap.xml", "w")
		if config.plugins.babelzapper.enabled.value:
			text = text.replace("volumeMute", "babelzapperMute")
			text = text.replace("id=\"KEY_MUTE\" mapto=\"deleteForward\" flags=\"mr\"", "id=\"KEY_MUTE\" mapto=\"babelzapperMute\" flags=\"m\"")
			text = text.replace("id=\"KEY_MUTE\" mapto=\"delete\" flags=\"mr\"", "id=\"KEY_MUTE\" mapto=\"babelzapperMute\" flags=\"b\"")
		else:
			text = text.replace("id=\"KEY_MUTE\" mapto=\"babelzapperMute\" flags=\"b\"", "id=\"KEY_MUTE\" mapto=\"delete\" flags=\"mr\"")
			text = text.replace("id=\"KEY_MUTE\" mapto=\"babelzapperMute\" flags=\"m\"", "id=\"KEY_MUTE\" mapto=\"deleteForward\" flags=\"mr\"")
			text = text.replace("babelzapperMute", "volumeMute")
		keymapfile.write(text)
		keymapfile.close()
		keymapparser.removeKeymap("/usr/share/enigma2/keymap.xml")
		keymapparser.readKeymap("/usr/share/enigma2/keymap.xml")
		self.close(True)

	def cancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close(False)

	def readme(self):
		self.session.open(Console, _("Babelzapper readme.txt"), ["cat %s" % (babelzapper_readme)])

	def about(self):
		self.session.open(MessageBox, _("Babelzapper Version %s\nby gutemine and garbage") % babelzapper_version, MessageBox.TYPE_INFO)


class BabelZapperStartup(Screen):
	skin = ""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin = BabelZapperStartup.skin
		print("[BABELZAPPER] starting")
		global globalActionMap
		# overwrite Mute  for the handicaped
		globalActionMap.actions["babelzapperMute"] = self.setKey
		self.babelDialog = session.instantiateDialog(BabelZapper)

	def setKey(self):
		global babelmenu
		global babelkey
		global babeldone
		global babelon
		length = len(babelmenu) - 1
		self.nextKeyTimer = eTimer()
		self.nextKeyTimer.callback.append(self.nextKey)
		self.nextKeyTimer.stop()
		self.resetKeyTimer = eTimer()
		self.resetKeyTimer.callback.append(self.resetKey)
		self.resetKeyTimer.stop()
		self.delayedKeyTimer = eTimer()
		self.delayedKeyTimer.callback.append(self.setKey)
		self.delayedKeyTimer.stop()
		print("[BABELZAPPER] received mute key")
		if babelkey == -1:
			print("[BABELZAPPER] now starts from beginning\n")
			self.nextKeyTimer.start(200, True)
		elif babeldone == -1:
			print("[BABELZAPPER] now starts with last key\n")
			babeldone = 0
			babelkey = babelkey - 1
			self.nextKeyTimer.start(config.plugins.babelzapper.changetime.value, True)
#			self.nextKeyTimer.start(200, True)
		else:
			self.babelDialog.hide()
			cmdlen = len(babelmenu[babelkey])
			print("[BABELZAPPER] %i commands" % cmdlen)
			i = 1 + babeldone
			babeldone = 0
			# here comes the command line interpreter
			while i < cmdlen:
				cmd = babelmenu[babelkey][i]
				cmdname = cmd.lstrip("	 ")
				print("[BABELZAPPER] command: %s" % cmdname)
				if cmdname.startswith("$KEY_"):
					self.babelDialog.executeKey(cmdname)
				elif cmdname.startswith("END"):
					self.babelDialog.hide()
					print("[BABELZAPPER] ENDs\n")
					babelkey = -1
					return
				elif cmdname.startswith("IFON"):
					if babelon == 0:
						print("[BABELZAPPER] ON is off\n")
						# skip rest of commandline
						i = cmdlen
					else:
						print("[BABELZAPPER] ON is on executing rest and setting it off\n")
						babelon = 0
				elif cmdname.startswith("ON"):
					print("[BABELZAPPER] ON\n")
					babelon = 1
				elif cmdname.startswith("TOGGLE"):
					if babelon == 0:
						print("[BABELZAPPER] TOGGLE on\n")
						babelon = 1
					else:
						print("[BABELZAPPER] TOGGLE off\n")
						babelon = 0
				elif cmdname.startswith("OFF"):
					print("[BABELZAPPER] OFF\n")
					babelon = 0
				elif cmdname.startswith("GOTO"):
					try:
						babelkey = int(cmdname.replace("GOTO", ""))
						print("[BABELZAPPER] GOTO %i \n" % babelkey)
					except:
						babelkey = 0
					# skip rest of commandline
					i = cmdlen
				elif cmdname.startswith("STOP"):
					try:
						babelstop = int(cmdname.replace("STOP", ""))
					except:
						babelstop = 1000
					if babelstop < 1000:
						babelstop = 1000
					elif babelstop > 60000:
						babelstop = 60000
					print("[BABELZAPPER] STOP %i \n" % babelstop)
					self.babelDialog.show()
					babeldone = i
					self.delayedKeyTimer.start(babelstop, True)
					return
				elif cmdname.startswith("PRINT"):
					babeltext = cmd.replace("PRINT", "")
					print("[BABELZAPPER] PRINTs: %s \n" % babeltext)
					self.session.open(MessageBox, babeltext, MessageBox.TYPE_INFO)
				elif cmdname.startswith("LOAD") or cmdname.startswith("RUN"):
					babelkey = -1
					babeldone = 0
					i = len(babelmenu)
					while i > 1:
						i = i - 1
						babelmenu.pop(i)
					babelfile = "%s/%s.zbb" % (babelzapper_menus, cmdname.replace("LOAD", "").replace("RUN", "").replace(" ", "").replace("	", ""))
					print("[BABELZAPPER] LOADs: %s\n" % babelfile)
					if os.path.exists(babelfile):
						f = open(babelfile, 'r')
					else:
						f = open("%s/babelzapper.zbb" % babelzapper_menus, 'r')
					line = f.readline().replace("\r", "").replace("\n", "")
					while (line):
						bz = line.split(";")
						if len(bz) < 2:
							print("[BABELZAPPER] wrong line %s in babelzapper.zbb" % line)
							babelmenu.append(("????", "PRINT ???? %s" % line))
						else:
							babelmenu.append((bz))
						line = f.readline().replace("\r", "").replace("\n", "")
					f.close()
					# skip rest of commandline
					i = cmdlen
				elif cmdname.startswith("REM"):
					# skip rest of commandline
					i = cmdlen
				else:
					if len(cmd) > 0:
						print("[BABELZAPPER] unknown command %s\n" % cmd)
						babeltext = "???? %s\n" % cmd
					else:
						babeltext = "???? empty command found\n"
					self.session.open(MessageBox, babeltext, MessageBox.TYPE_ERROR)
					# skip rest of commandline
					i = cmdlen
				# next command
				i = i + 1
			# continue babelzapping but show last command again to make repeats easier
			babelkey = babelkey - 1
			self.nextKeyTimer.start(config.plugins.babelzapper.changetime.value, True)

	def resetKey(self):
		print("[BABELZAPPER] resets last key")
		self.resetKeyTimer.stop()
		self.babelDialog.hide()
		global babelkey
		global babeldone
		babelkey = -1
		babeldone = 0

	def nextKey(self):
		global babelmenu
		global babelkey
		global babelon
		if not config.plugins.babelzapper.enabled.value:
			self.babelDialog.hide()
			return
		length = len(babelmenu) - 1
		if babelkey < 0:
			babelkey = 0
		elif babelkey < length:
			babelkey = babelkey + 1
		else:
			babelkey = 0
		self.nextKeyTimer.stop()
		cmd = babelmenu[babelkey][1]
		cmdname = cmd.lstrip("	 ")
		if cmdname.startswith("RETURN"):
			try:
				babelkey = int(cmdname.replace("RETURN", "")) - 1
			except:
				babelkey = -1
			print("[BABELZAPPER] RETURN %i \n" % babelkey)
			self.nextKeyTimer.start(0, True)
			return
		elif cmdname.startswith("REM"):
			# skip this commandline
			self.nextKeyTimer.start(0, True)
			return
		elif cmdname.startswith("ON"):
			print("[BABELZAPPER] ON\n")
			babelon = 1
			# skip this commandline
			self.nextKeyTimer.start(0, True)
			return
		elif cmdname.startswith("OFF"):
			print("[BABELZAPPER] OFF\n")
			babelon = 0
			# skip this commandline
			self.nextKeyTimer.start(0, True)
			return
		elif cmdname.startswith("TOGGLE"):
			if babelon == 0:
				print("[BABELZAPPER] TOGGLE on\n")
				babelon = 0
			else:
				print("[BABELZAPPER] TOGGLE off\n")
				babelon = 1
			# skip this commandline
			self.nextKeyTimer.start(0, True)
			return
		elif cmdname.startswith("STOP"):
			try:
				babelstop = int(cmdname.replace("STOP", ""))
			except:
				babelstop = 1000
			if babelstop < 1000:
				babelstop = 1000
			elif babelstop > 60000:
				babelstop = 60000
			print("[BABELZAPPER] STOP %i \n" % babelstop)
			currentkey = babelmenu[babelkey][0]
			split = currentkey.split(":")
			currentkey = split[0]
			currentbg = 0
			currentfg = 1
			if len(split) > 1:
				currentbg = int(split[1])
			if len(split) > 2:
				currentfg = int(split[2])
			self.babelDialog.updateKey(currentkey, currentbg, currentfg)
			self.babelDialog.show()
			self.nextKeyTimer.start(babelstop, True)
			return
		elif cmdname.startswith("RUN"):
			i = len(babelmenu)
			while i > 1:
				i = i - 1
				babelmenu.pop(i)
			babelfile = "%s/%s.zbb" % (babelzapper_menus, cmdname.replace("RUN", "").replace(" ", "").replace("	", ""))
			print("[BABELZAPPER] RUNs: %s\n" % babelfile)
			if os.path.exists(babelfile):
				f = open(babelfile, 'r')
			else:
				f = open("/%s/babelzapper.zbb" % babelzapper_menus, 'r')
			line = f.readline().replace("\r", "").replace("\n", "")
			while (line):
				bz = line.split(";")
				if len(bz) < 2:
					print("[BABELZAPPER] wrong line %s in babelzapper.zbb" % line)
					babelmenu.append(("????", "PRINT ???? %s" % line))
				else:
					babelmenu.append((bz))
				line = f.readline().replace("\r", "").replace("\n", "")
			f.close()
			babelkey = -1
			self.babelDialog.updateKey(babelmenu[babelkey][0])
			self.babelDialog.show()
			self.nextKeyTimer.start(0, True)
			return
		else:
			pass
		currentkey = babelmenu[babelkey][0]
		split = currentkey.split(":")
		currentkey = split[0]
		currentbg = 0
		currentfg = 1
		if len(split) > 1:
			currentbg = int(split[1])
		if len(split) > 2:
			currentfg = int(split[2])
		self.babelDialog.updateKey(currentkey, currentbg, currentfg)
		self.babelDialog.show()
		self.nextKeyTimer.start(config.plugins.babelzapper.changetime.value, True)


class BabelZapper(Screen):
	skin = """
		<screen position="center,60" size="180,30" flags="wfNoBorder">
		<widget name="babelzapper" position="1,1" size="180,30" font="Regular;26" valign="center" halign="center" backgroundColors="black,white,#00AAAAAA,red,green,yellow,blue" foregroundColors="black,white,#00AAAAAA,red,green,yellow,blue">
		</widget>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin = BabelZapper.skin
		global babelmenu
		print("[BABELZAPPER] loading %s/babelzapper.zbb" % babelzapper_menus)
		global babelkey
		babelmenu = []
		babelmenu.append(("NONE", "END"))
		if os.path.exists("%s/babelzapper.zbb" % babelzapper_menus):
			f = open("%s/babelzapper.zbb" % babelzapper_menus, 'r')
			line = f.readline().replace("\r", "").replace("\n", "")
			while (line):
				bz = line.split(";")
				if len(bz) < 2:
					print("[BABELZAPPER] wrong line %s in babelzapper.zbb" % line)
					babelmenu.append(("????", "PRINT ???? %s" % line))

				else:
					babelmenu.append((bz))
				line = f.readline().replace("\r", "").replace("\n", "")
			f.close()
		babelkey = -1
		self["babelzapper"] = MultiColorLabel(babelmenu[babelkey][0])
		elf["babelzapper"].setForegroundColorNum(0)
	self["babelzapper"].setBackgroundColorNum(1)

	def updateKey(self, keyname, keybg=0, keyfg=1):
		self["babelzapper"].setText(keyname)
		self["babelzapper"].setForegroundColorNum(keyfg)
		self["babelzapper"].setBackgroundColorNum(keybg)

	def executeKey(self, keyname):
		keyname = keyname.replace("$", "").replace(" ", "").replace("\n", "")
		_long = False
		if keyname.startswith("KEY_EXIT") and config.plugins.babelzapper.exit2escape.value:
			keyname = keyname.replace("KEY_EXIT", "KEY_ESC")
		if keyname.startswith("KEY_"):
			if keyname.endswith("_LONG"):
				_long = True
				keyname = keyname.replace("_LONG", "")
			try:
				keycode = KEYIDS[keyname]
				print("[BABELZAPPER] found key %i" % keycode)
			except:
				print("[BABELZAPPER] found unknown key %s" % keyname)
				return
		else:
			print("[BABELZAPPER] found unknown key %s" % keyname)
			return
		if BoxInfo.getItem("model") == "dm8000":
			fp = open("/dev/input/event2", 'wb')
		else:
			fp = open("/dev/input/event1", 'wb')
		if _long:
			dataon = pack('iiHHi', 0, 0, 1, keycode, 1)
			fp.write(dataon)
			dataon = pack('iiHHi', 0, 0, 1, keycode, 2)
			fp.write(dataon)
			dataon = pack('iiHHi', 0, 0, 1, keycode, 2)
			fp.write(dataon)
			dataon = pack('iiHHi', 0, 0, 1, keycode, 2)
			fp.write(dataon)
			dataon = pack('iiHHi', 0, 0, 1, keycode, 2)
			fp.write(dataon)
		else:
			print("[BABELZAPPER] now writes out: %i\n" % (keycode))
			dataon = pack('iiHHi', 0, 0, 1, keycode, 1)
			fp.write(dataon)
		dataoff = pack('iiHHi', 0, 0, 1, keycode, 0)
		fp.write(dataoff)
		fp.close()
