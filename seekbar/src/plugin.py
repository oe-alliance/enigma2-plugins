# -*- coding: utf-8 -*-
##
## Seekbar
## by AliAbdul
##
from __future__ import print_function
from Components.ActionMap import ActionMap
from Components.config import config, ConfigInteger, ConfigNumber, ConfigSelection, ConfigSubsection, ConfigYesNo, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Language import language
from Components.Pixmap import MovingPixmap
from enigma import eTimer
from keyids import KEYIDS
from Screens.InfoBar import MoviePlayer
from Screens.Screen import Screen
from Tools.Directories import fileExists, resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS
from Tools.KeyBindings import addKeyBinding
import os
import gettext
import keymapparser

##############################################

config.plugins.Seekbar = ConfigSubsection()
config.plugins.Seekbar.overwrite_left_right = ConfigYesNo(default=True)
config.plugins.Seekbar.sensibility = ConfigInteger(default=10, limits=(1, 10))

##############################################

PluginLanguageDomain = "Seekbar"
PluginLanguagePath = "Extensions/Seekbar/locale/"


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print("[" + PluginLanguageDomain + "] fallback to default translation for " + txt)
		return gettext.gettext(txt)


language.addCallback(localeInit())

##############################################


class Seekbar(ConfigListScreen, Screen):
	skin = """
	<screen position="center,center" size="560,160" title="%s">
		<widget name="config" position="10,10" size="540,100" scrollbarMode="showOnDemand" />
		<widget name="cursor" position="0,125" size="8,18" pixmap="skin_default/position_arrow.png" alphatest="on" />

		<widget source="session.CurrentService" render="PositionGauge" position="145,140" size="270,10" zPosition="2" pointer="skin_default/position_pointer.png:540,0" transparent="1" foregroundColor="#20224f">
			<convert type="ServicePosition">Gauge</convert>
		</widget>
		<widget name="time" position="50,130" size="100,20" font="Regular;20" halign="left" backgroundColor="#4e5a74" transparent="1" />
		<widget source="session.CurrentService" render="Label" position="420,130" size="90,24" font="Regular;20" halign="right" backgroundColor="#4e5a74" transparent="1">
			<convert type="ServicePosition">Length</convert>
		</widget>
	</screen>""" % _("Seek")

	def __init__(self, session, instance, fwd):
		Screen.__init__(self, session)
		
		self.session = session
		self.infobarInstance = instance
		self.fwd = fwd
		if isinstance(session.current_dialog, MoviePlayer):
			self.dvd = False
			self.vdb = False
		elif DVDPlayer is not None and isinstance(session.current_dialog, DVDPlayer):
			self.dvd = True
			self.vdb = False
		else:
			self.dvd = False
			self.vdb = True
		self.percent = 0.0
		self.length = None
		service = session.nav.getCurrentService()
		if service:
			self.seek = service.seek()
			if self.seek:
				self.length = self.seek.getLength()
				position = self.seek.getPlayPosition()
				if self.length and position:
					if int(position[1]) > 0:
						self.percent = float(position[1]) * 100.0 / float(self.length[1])
		
		self.minuteInput = ConfigNumber(default=5)
		self.positionEntry = ConfigSelection(choices=["<>"], default="<>")
		if self.fwd:
			txt = _("Jump x minutes forward:")
		else:
			txt = _("Jump x minutes back:")
		ConfigListScreen.__init__(self, [
			getConfigListEntry(txt, self.minuteInput),
			getConfigListEntry(_("Go to position:"), self.positionEntry),
			getConfigListEntry(_("Sensibility:"), config.plugins.Seekbar.sensibility),
			getConfigListEntry(_("Overwrite left and right buttons:"), config.plugins.Seekbar.overwrite_left_right)])
		
		self["cursor"] = MovingPixmap()
		self["time"] = Label()
		
		self["actions"] = ActionMap(["WizardActions"], {"back": self.exit}, -1)
		
		self.cursorTimer = eTimer()
		self.cursorTimer.callback.append(self.updateCursor)
		self.cursorTimer.start(200, False)
		
		self.onLayoutFinish.append(self.firstStart)

	def firstStart(self):
		self["config"].setCurrentIndex(1)

	def updateCursor(self):
		if self.length:
			x = 145 + int(2.7 * self.percent)
			self["cursor"].moveTo(x, 125, 1)

			self["cursor"].startMoving()
			pts = int(float(self.length[1]) / 100.0 * self.percent)
			self["time"].setText("%d:%02d" % ((pts / 60 / 90000), ((pts / 90000) % 60)))

	def exit(self):
		self.cursorTimer.stop()
		ConfigListScreen.saveAll(self)
		self.close()

	def keyOK(self):
		sel = self["config"].getCurrent()[1]
		if sel == self.positionEntry:
			if self.length:
				if self.dvd: # seekTo() doesn't work for DVD Player
					oldPosition = self.seek.getPlayPosition()[1]
					newPosition = int(float(self.length[1]) / 100.0 * self.percent)
					if newPosition > oldPosition:
						pts = newPosition - oldPosition
					else:
						pts = -1 * (oldPosition - newPosition)
					DVDPlayer.doSeekRelative(self.infobarInstance, pts)
				else:
					self.seek.seekTo(int(float(self.length[1]) / 100.0 * self.percent))
				self.exit()
		elif sel == self.minuteInput:
			pts = self.minuteInput.value * 60 * 90000
			if self.fwd == False:
				pts = -1 * pts
			if self.dvd:
				DVDPlayer.doSeekRelative(self.infobarInstance, pts)
			elif self.vdb:
				VideoDBPlayer.doSeekRelative(self.infobarInstance, pts)
			else:
				MoviePlayer.doSeekRelative(self.infobarInstance, pts)
			self.exit()

	def keyLeft(self):
		sel = self["config"].getCurrent()[1]
		if sel == self.positionEntry:
			self.percent -= float(config.plugins.Seekbar.sensibility.value) / 10.0
			if self.percent < 0.0:
				self.percent = 0.0
		else:
			ConfigListScreen.keyLeft(self)

	def keyRight(self):
		sel = self["config"].getCurrent()[1]
		if sel == self.positionEntry:
			self.percent += float(config.plugins.Seekbar.sensibility.value) / 10.0
			if self.percent > 100.0:
				self.percent = 100.0
		else:
			ConfigListScreen.keyRight(self)

	def keyNumberGlobal(self, number):
		sel = self["config"].getCurrent()[1]
		if sel == self.positionEntry:
			self.percent = float(number) * 10.0
		else:
			ConfigListScreen.keyNumberGlobal(self, number)

##############################################
# This hack overwrites the functions seekFwdManual and seekBackManual of the InfoBarSeek class (MoviePlayer, DVDPlayer, VideoDB)


def seekbar(instance, fwd=True):
	if instance and instance.session:
		instance.session.open(Seekbar, instance, fwd)


def seekbarBack(instance):
	seekbar(instance, False)


MoviePlayer.seekFwdManual = seekbar
MoviePlayer.seekBackManual = seekbarBack

dvdPlayer = "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/DVDPlayer/plugin.py")
if fileExists(dvdPlayer) or fileExists("%sc" % dvdPlayer):
	from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
	DVDPlayer.seekFwdManual = seekbar
	DVDPlayer.seekBackManual = seekbarBack
else:
	DVDPlayer = None

videodb = "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/VideoDB/plugin.py")
if fileExists(videodb):
	from Plugins.Extensions.VideoDB.Player import VideoDBPlayer
	VideoDBPlayer.seekFwdManual = seekbar
	VideoDBPlayer.seekBackManual = seekbarBack


##############################################
# This hack puts the functions seekFwdManual and seekBackManual to the maped keys to seekbarRight and seekbarLeft

DoBind = ActionMap.doBind


def doBind(instance):
	if not instance.bound:
		for ctx in instance.contexts:
			if ctx == "InfobarSeekActions":
				if "seekFwdManual" in instance.actions:
					instance.actions["seekbarRight"] = instance.actions["seekFwdManual"]
				if "seekBackManual" in instance.actions:
					instance.actions["seekbarLeft"] = instance.actions["seekBackManual"]
			DoBind(instance)


if config.plugins.Seekbar.overwrite_left_right.value:
	ActionMap.doBind = doBind

##############################################
# This hack maps the keys left and right to seekbarRight and seekbarLeft in the InfobarSeekActions-context

KeymapError = keymapparser.KeymapError
ParseKeys = keymapparser.parseKeys


def parseKeys(context, filename, actionmap, device, keys):
	if context == "InfobarSeekActions":
		if device == "generic":
			for x in keys.findall("key"):
				get_attr = x.attrib.get
				mapto = get_attr("mapto")
				id = get_attr("id")
				if id == "KEY_LEFT":
					mapto = "seekbarLeft"
				if id == "KEY_RIGHT":
					mapto = "seekbarRight"
				flags = get_attr("flags")
				flag_ascii_to_id = lambda x: {'m': 1, 'b': 2, 'r': 4, 'l': 8}[x]
				flags = sum(map(flag_ascii_to_id, flags))
				assert mapto, "%s: must specify mapto in context %s, id '%s'" % (filename, context, id)
				assert id, "%s: must specify id in context %s, mapto '%s'" % (filename, context, mapto)
				assert flags, "%s: must specify at least one flag in context %s, id '%s'" % (filename, context, id)
				if len(id) == 1:
					keyid = ord(id) | 0x8000
				elif id[0] == '\\':
					if id[1] == 'x':
						keyid = int(id[2:], 0x10) | 0x8000
					elif id[1] == 'd':
						keyid = int(id[2:]) | 0x8000
					else:
						raise KeymapError("key id '" + str(id) + "' is neither hex nor dec")
				else:
					try:
						keyid = KEYIDS[id]
					except:
						raise KeymapError("key id '" + str(id) + "' is illegal")
				actionmap.bindKey(filename, device, keyid, flags, context, mapto)
				addKeyBinding(filename, keyid, context, mapto, flags)
		else:
			ParseKeys(context, filename, actionmap, device, keys)
	else:
		ParseKeys(context, filename, actionmap, device, keys)


if config.plugins.Seekbar.overwrite_left_right.value:
	keymapparser.parseKeys = parseKeys
	keymapparser.removeKeymap(config.usage.keymap.value)
	keymapparser.readKeymap(config.usage.keymap.value)

##############################################


def Plugins(**kwargs):
	return []
