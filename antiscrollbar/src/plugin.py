from __future__ import print_function
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Plugins.Plugin import PluginDescriptor
from enigma import iPlayableService, ePoint, eSize
from Components.ServiceEventTracker import ServiceEventTracker
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSubList, ConfigInteger, ConfigYesNo, ConfigText
from Components.ConfigList import ConfigListScreen


# Translation support (dummy if no locale)
import gettext
_ = gettext.gettext

myname = "AntiScrollbar"

config.plugins.antiscrollbar = ConfigSubsection()
config.plugins.antiscrollbar.autostart = ConfigYesNo(default=True)
config.plugins.antiscrollbar.modescount = ConfigInteger(0)
config.plugins.antiscrollbar.mode = ConfigSubList()


def readConfig():
	srefs = {}
	for mode in config.plugins.antiscrollbar.mode:
		sref = mode.sref.value
		if not sref:
			continue
		sizex = mode.sizex.value
		sizey = mode.sizey.value
		posx = mode.posx.value
		posy = mode.posy.value
		enabled = mode.enabled.value
		srefs[sref] = [sizex, sizey, posx, posy, enabled]
	return srefs


class AntiScrollOverlay(Screen):
	def __init__(self, session):
		self.size = [0, 0]
		self.position = [0, 0]
		ss = "<screen position=\"0,0\" size=\"0,0\" title=\"AntiScrollOverlay\" flags=\"wfNoBorder\" zPosition=\"-1\" backgroundColor=\"#FF000000\">"
		ss += "<widget name=\"label\" position=\"1,1\" size=\"0,0\" backgroundColor=\"#00000000\" />"
		ss += "</screen>"
		self.skin = ss
		self.session = session
		Screen.__init__(self, session)
		self["label"] = Label()
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
			iPlayableService.evUpdatedInfo: self.evStart,
			iPlayableService.evEOF: self.hide}
		)
		self.hide()

	def evStart(self):
		service = self.session.nav.getCurrentlyPlayingServiceReference()
		if service is None:
			return
		srefs = readConfig()
		sref_str = service.toString()
		if sref_str in srefs:
			data = srefs[sref_str]
			if data[4]:
				self.resize(data[0], data[1])
				self.move(data[2], data[3])
				self.show()
			else:
				self.hide()
		else:
			self.hide()

	def move(self, x, y):
		self.instance.move(ePoint(x, y))

	def resize(self, w, h):
		self.instance.resize(eSize(w, h))
		self["label"].instance.resize(eSize(w - 2, h - 2))


class AntiScrollConfig(ConfigListScreen, Screen):
	skin = """
		<screen position="100,100" size="550,400" title="%s">
			<widget name="config" position="5,5" size="540,360" scrollbarMode="showOnDemand" zPosition="1"/>
			<widget name="key_red" position="0,360" size="140,40" valign="center" halign="center" zPosition="5" transparent="1" foregroundColor="white" font="Regular;18"/>
			<widget name="key_green" position="140,360" size="140,40" valign="center" halign="center" zPosition="5" transparent="1" foregroundColor="white" font="Regular;18"/>
			<widget name="key_yellow" position="280,360" size="140,40" valign="center" halign="center" zPosition="5" transparent="1" foregroundColor="white" font="Regular;18"/>
			<ePixmap name="red" pixmap="skin_default/buttons/red.png" position="0,360" size="140,40" zPosition="4" transparent="1" alphatest="on"/>
			<ePixmap name="green" pixmap="skin_default/buttons/green.png" position="140,360" size="140,40" zPosition="4" transparent="1" alphatest="on"/>
			<ePixmap name="yellow" pixmap="skin_default/buttons/yellow.png" position="280,360" size="140,40" zPosition="4" transparent="1" alphatest="on"/>
		</screen>""" % _(myname + ": Main Setup")

	def __init__(self, session, args=0):
		Screen.__init__(self, session)
		lst = [
			getConfigListEntry(_("Start on Sessionstart"), config.plugins.antiscrollbar.autostart),
		]
		ConfigListScreen.__init__(self, lst)
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button(_("current Service"))
		self["setupActions"] = ActionMap(
			["SetupActions", "ColorActions"],
			{
				"red": self.cancel,
				"green": self.save,
				"yellow": self.openCurrentSeviceConfig,
				"save": self.save,
				"cancel": self.cancel,
				"ok": self.save,
			}, -2
		)

	def openCurrentSeviceConfig(self):
		print("yellow")
		current_ref = self.session.nav.getCurrentlyPlayingServiceReference()
		if current_ref is None:
			return
		current_ref_str = current_ref.toString()
		existing_mode = None
		for mode in config.plugins.antiscrollbar.mode:
			if mode.sref.value == current_ref_str:
				existing_mode = mode
				break
		if existing_mode is not None:
			# Controlla e correggi valori zero
			if existing_mode.sizex.value == 0:
				existing_mode.sizex.value = 200
				existing_mode.sizex.save()
			if existing_mode.sizey.value == 0:
				existing_mode.sizey.value = 200
				existing_mode.sizey.save()
			if existing_mode.posx.value == 0:
				existing_mode.posx.value = 100
				existing_mode.posx.save()
			if existing_mode.posy.value == 0:
				existing_mode.posy.value = 50
				existing_mode.posy.save()
			self.session.open(CurrentSeviceConfig, existing_mode)
			return

		print("new config " * 40)
		new_mode = ConfigSubsection()
		new_mode.sref = ConfigText(default=current_ref_str)
		new_mode.sizex = ConfigInteger(default=200, limits=(1, 1920))
		new_mode.sizey = ConfigInteger(default=200, limits=(1, 1080))
		new_mode.posx = ConfigInteger(default=100, limits=(0, 1920))
		new_mode.posy = ConfigInteger(default=50, limits=(0, 1080))
		new_mode.enabled = ConfigYesNo(default=True)

		config.plugins.antiscrollbar.mode.append(new_mode)

		new_mode.sref.save()
		new_mode.sizex.save()
		new_mode.sizey.save()
		new_mode.posx.save()
		new_mode.posy.save()
		new_mode.enabled.save()

		config.plugins.antiscrollbar.save()
		config.plugins.antiscrollbar.modescount.value = len(config.plugins.antiscrollbar.mode)
		config.plugins.antiscrollbar.modescount.save()

		self.session.open(CurrentSeviceConfig, new_mode)

	def save(self):
		print("saving")
		for x in self["config"].list:
			x[1].save()
		self.close(True, self.session)

	def cancel(self):
		print("cancel")
		for x in self["config"].list:
			x[1].cancel()
		self.close(False, self.session)


class CurrentSeviceConfig(Screen):
	step = 5

	def __init__(self, session, mode):
		print("editing " + mode.sref.value)
		self.mode = mode
		self.size = [mode.sizex.value, mode.sizey.value]
		self.enabled = mode.enabled.value
		self.position = [mode.posx.value, mode.posy.value]
		print("CurrentSeviceConfig: pos=%d,%d size=%d,%d enabled=%s" % (self.position[0], self.position[1], self.size[0], self.size[1], self.enabled))
		# Build dynamic skin
		ss = "<screen position=\"%i,%i\" size=\"%i,%i\" title=\"%s\" flags=\"wfNoBorder\">" % (self.position[0], self.position[1], self.size[0], self.size[1], myname)
		ss += "<widget name=\"label\" position=\"0,0\" size=\"%i,%i\" backgroundColor=\"black\"/>" % (self.size[0], self.size[1])
		ss += "<widget name=\"help\" position=\"0,%i\" size=\"%i,40\" font=\"Regular;16\" halign=\"center\" valign=\"center\" backgroundColor=\"#80000000\" foregroundColor=\"white\" zPosition=\"2\">" % (self.size[1] - 40, self.size[0])
		ss += "<text>Arrows=Move | 2/8/4/6=Resize | 0=Enable/Disable | OK=Save | EXIT=Cancel</text>"
		ss += "</widget>"
		ss += "</screen>"
		self.skin = ss
		self.session = session
		Screen.__init__(self, session)
		self["label"] = Label()
		self["help"] = Label()
		if not self.enabled:
			self["label"].setText("disabled")
		self["actions"] = ActionMap(
			["WizardActions", "DirectionActions", "MenuActions", "NumberActions"],
			{
				"ok": self.go,
				"back": self.cancel,
				"cancel": self.cancel,
				"down": self.down,
				"up": self.up,
				"left": self.left,
				"right": self.right,
				"2": self.key2,
				"8": self.key8,
				"4": self.key4,
				"6": self.key6,
				"0": self.key0,
			}, -1
		)

	def go(self):
		self.mode.posx.value = self.position[0]
		self.mode.posy.value = self.position[1]
		self.mode.sizex.value = self.size[0]
		self.mode.sizey.value = self.size[1]
		self.mode.enabled.value = self.enabled
		self.mode.save()

		if activebar is not None:
			activebar.evStart()
		self.close()

	def cancel(self):
		self.close()

	def key0(self):
		if self.enabled:
			self.enabled = False
			self["label"].setText("disabled")
		else:
			self.enabled = True
			self["label"].setText("")

	def key2(self):
		new_h = self.size[1] - self.step
		if new_h >= 10:
			self.size[1] = new_h
			self.resize(self.size[0], self.size[1])

	def key8(self):
		new_h = self.size[1] + self.step
		if new_h <= 1080:
			self.size[1] = new_h
			self.resize(self.size[0], self.size[1])

	def key4(self):
		new_w = self.size[0] - self.step
		if new_w >= 10:
			self.size[0] = new_w
			self.resize(self.size[0], self.size[1])

	def key6(self):
		new_w = self.size[0] + self.step
		if new_w <= 1920:
			self.size[0] = new_w
			self.resize(self.size[0], self.size[1])

	def down(self):
		new_y = self.position[1] + self.step
		if new_y <= 1080:
			self.position[1] = new_y
			self.move(self.position[0], self.position[1])

	def up(self):
		new_y = self.position[1] - self.step
		if new_y >= 0:
			self.position[1] = new_y
			self.move(self.position[0], self.position[1])

	def left(self):
		new_x = self.position[0] - self.step
		if new_x >= 0:
			self.position[0] = new_x
			self.move(self.position[0], self.position[1])

	def right(self):
		new_x = self.position[0] + self.step
		if new_x <= 1920:
			self.position[0] = new_x
			self.move(self.position[0], self.position[1])

	def move(self, x, y):
		self.instance.move(ePoint(x, y))

	def resize(self, w, h):
		self.instance.resize(eSize(w, h))
		self["label"].instance.resize(eSize(w, h))
		self["help"].instance.resize(eSize(w, 40))
		self["help"].instance.move(ePoint(0, h - 40))


activebar = None


def main(session, **kwargs):
	# global activebar
	if activebar is not None:
		activebar.hide()
	session.openWithCallback(mainCB, AntiScrollConfig)


def mainCB(saved, session):
	global activebar
	if activebar is None:
		activebar = session.instantiateDialog(AntiScrollOverlay)
	activebar.evStart()


def autostart(session, **kwargs):
	global activebar
	if config.plugins.antiscrollbar.autostart.value:
		activebar = session.instantiateDialog(AntiScrollOverlay)


def Plugins(**kwargs):
	return [
		PluginDescriptor(
			name=myname,
			description="overlay for scrolling bars",
			where=PluginDescriptor.WHERE_PLUGINMENU,
			fnc=main,
			icon="plugin.png"
		),
		PluginDescriptor(
			where=PluginDescriptor.WHERE_SESSIONSTART,
			fnc=autostart
		)
	]
