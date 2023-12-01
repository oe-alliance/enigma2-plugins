##
## Permanent Clock
## by AliAbdul
##
from Components.ActionMap import ActionMap
from Components.config import config, ConfigInteger, ConfigSubsection, ConfigYesNo, ConfigSelection
from Components.Language import language
from Components.MenuList import MenuList
from Components.Input import Input
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from enigma import ePoint, eTimer, getDesktop
from GlobalActions import globalActionMap
from keymapparser import readKeymap, removeKeymap
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS
import gettext
from os import system, path
from sys import version_info

try:
	from Components.SystemInfo import BoxInfo
	IMAGEDISTRO = BoxInfo.getItem("distro")
except:
	from boxbranding import getImageDistro
	IMAGEDISTRO = getImageDistro()

PY3 = version_info[0] == 3

if PY3:
	PTime = "/usr/lib/enigma2/python/Plugins/Extensions/PermanentClock/PermanentClockTime.pyc"
	ConverterTime = "/usr/lib/enigma2/python/Components/Converter/PermanentClockTime.pyc"
	PWatches = "/usr/lib/enigma2/python/Plugins/Extensions/PermanentClock/PermanentClockWatches.pyc"
	RendererWatches = "/usr/lib/enigma2/python/Components/Renderer/PermanentClockWatches.pyc"
else:
	PTime = "/usr/lib/enigma2/python/Plugins/Extensions/PermanentClock/PermanentClockTime.pyo"
	ConverterTime = "/usr/lib/enigma2/python/Components/Converter/PermanentClockTime.pyo"
	PWatches = "/usr/lib/enigma2/python/Plugins/Extensions/PermanentClock/PermanentClockWatches.pyo"
	RendererWatches = "/usr/lib/enigma2/python/Components/Renderer/PermanentClockWatches.pyo"

if not path.exists(ConverterTime):
	system("cp " + PTime + " " + ConverterTime)
if not path.exists(RendererWatches):
	system("cp " + PWatches + " " + RendererWatches)

_session = None


def localeInit():
	gettext.bindtextdomain("PermanentClock", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/PermanentClock/locale/"))


PluginLanguageDomain = "PermanentClock"
PluginLanguagePath = "Extensions/PermanentClock/locale/"


def _(txt):
	t = gettext.dgettext("PermanentClock", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


localeInit()
language.addCallback(localeInit)

config.plugins.PermanentClock = ConfigSubsection()
config.plugins.PermanentClock.enabled = ConfigYesNo(default=False)
config.plugins.PermanentClock.position_x = ConfigInteger(default=500)
config.plugins.PermanentClock.position_y = ConfigInteger(default=35)
config.plugins.PermanentClock.analog = ConfigYesNo(default=False)
config.plugins.PermanentClock.show_hide = ConfigYesNo(default=False)
config.plugins.PermanentClock.color_analog = ConfigSelection([("1", _("black-yellow")), ("2", _("black-blue")), ("3", _("blue")), ("4", _("black-white")), ("5", _("white")), ("6", _("transparent")), ("7", _("PLi-transparent"))], default="1")
config.plugins.PermanentClock.color_digital = ConfigSelection([("0", _("yellow")), ("1", _("white")), ("2", _("large yellow")), ("3", _("large white"))], default="1")

##############################################################################
SKIN1 = """
	<screen position="0,0" size="70,70" zPosition="-1" backgroundColor="#ff000000" title="Permanent Clock" flags="wfNoBorder">
		<ePixmap position="1,1" zPosition="1" size="70,70" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PermanentClock/trad/trad1.png" alphatest="on" />
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="7,7" size="58,58" zPosition="4" alphatest="on" foregroundColor="#00f23d21">
			<convert type="PermanentClockTime">secHand</convert>
		</widget>
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="12,13" size="47,47" zPosition="3"  foregroundColor="#00ffffff" alphatest="on">
			<convert type="PermanentClockTime">minHand</convert>
		</widget>
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="20,21" size="31,31" zPosition="2"  foregroundColor="#00ffffff" alphatest="on">
			<convert type="PermanentClockTime">hourHand</convert>
		</widget>
	</screen>"""
##############################################################################
SKIN2 = """
	<screen position="0,0" size="70,70" zPosition="-1" backgroundColor="#ff000000" title="Permanent Clock" flags="wfNoBorder">
		<ePixmap position="1,1" zPosition="1" size="70,70" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PermanentClock/trad/trad2.png" alphatest="on" />
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="7,7" size="58,58" zPosition="4" alphatest="on" foregroundColor="#00f23d21">
			<convert type="PermanentClockTime">secHand</convert>
		</widget>
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="12,13" size="47,47" zPosition="3"  foregroundColor="#00ffffff" alphatest="on">
			<convert type="PermanentClockTime">minHand</convert>
		</widget>
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="20,21" size="31,31" zPosition="2"  foregroundColor="#00ffffff" alphatest="on">
			<convert type="PermanentClockTime">hourHand</convert>
		</widget>
	</screen>"""
##############################################################################
SKIN3 = """
	<screen position="0,0" size="70,70" zPosition="-1" backgroundColor="#ff000000" title="Permanent Clock" flags="wfNoBorder">
		<ePixmap position="1,1" zPosition="1" size="70,70" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PermanentClock/trad/trad3.png" alphatest="on" />
			<widget source="global.CurrentTime" render="PermanentClockWatches" position="7,7" size="58,58" zPosition="4" alphatest="on" foregroundColor="#00f23d21">
				<convert type="PermanentClockTime">secHand</convert>
			</widget>
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="12,13" size="47,47" zPosition="3"  foregroundColor="#00ffffff" alphatest="on">
			<convert type="PermanentClockTime">minHand</convert>
		</widget>
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="20,21" size="31,31" zPosition="2"  foregroundColor="#00ffffff" alphatest="on">
			<convert type="PermanentClockTime">hourHand</convert>
		</widget>
	</screen>"""
##############################################################################
SKIN4 = """
	<screen position="0,0" size="70,70" zPosition="-1" backgroundColor="#ff000000" title="Permanent Clock" flags="wfNoBorder">
		<ePixmap position="1,1" zPosition="1" size="70,70" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PermanentClock/trad/trad4.png" alphatest="on" />
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="7,7" size="58,58" zPosition="4" alphatest="on" foregroundColor="#00f23d21">
			<convert type="PermanentClockTime">secHand</convert>
		</widget>
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="12,13" size="47,47" zPosition="3"  foregroundColor="#00ffffff" alphatest="on">
			<convert type="PermanentClockTime">minHand</convert>
		</widget>
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="20,21" size="31,31" zPosition="2"  foregroundColor="#00ffffff" alphatest="on">
			<convert type="PermanentClockTime">hourHand</convert>
		</widget>
	</screen>"""
##############################################################################
SKIN5 = """
	<screen position="0,0" size="70,70" zPosition="-1" backgroundColor="#ff000000" title="Permanent Clock" flags="wfNoBorder">
		<ePixmap position="1,1" zPosition="1" size="70,70" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PermanentClock/trad/trad5.png" alphatest="on" />
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="7,7" size="58,58" zPosition="4" alphatest="on" foregroundColor="#00f23d21">
			<convert type="PermanentClockTime">secHand</convert>
		</widget>
		<widget source="global.CurrentTime" render="PermanentClockPermanentClockWatches" position="12,13" size="47,47" zPosition="3"  foregroundColor="green"  alphatest="on">
			<convert type="PermanentClockTime">minHand</convert>
		</widget>
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="20,21" size="31,31" zPosition="2"  foregroundColor="green"  alphatest="on">
			<convert type="PermanentClockTime">hourHand</convert>
		</widget>
	</screen>"""
##############################################################################
SKIN6 = """
	<screen position="0,0" size="70,70" zPosition="-1" backgroundColor="#ff000000" title="Permanent Clock" flags="wfNoBorder">
		<ePixmap position="1,1" zPosition="1" size="70,70" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PermanentClock/trad/trad6.png" alphatest="on" />
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="7,7" size="58,58" zPosition="4" alphatest="on" foregroundColor="#00f23d21">
			<convert type="PermanentClockTime">secHand</convert>
		</widget>
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="12,13" size="47,47" zPosition="3"  foregroundColor="green"  alphatest="on">
			<convert type="PermanentClockTime">minHand</convert>
		</widget>
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="20,21" size="31,31" zPosition="2"  foregroundColor="green"  alphatest="on">
			<convert type="PermanentClockTime">hourHand</convert>
		</widget>
	</screen>"""
##############################################################################
SKIN7 = """
	<screen position="0,0" size="70,70" zPosition="-1" backgroundColor="#ff000000" title="Permanent Clock" flags="wfNoBorder">
		<ePixmap position="1,1" zPosition="1" size="70,70" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/PermanentClock/trad/trad7.png" alphatest="on" />
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="7,7" size="58,58" zPosition="4" alphatest="on" foregroundColor="#00f23d21">
			<convert type="PermanentClockTime">secHand</convert>
		</widget>
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="12,13" size="47,47" zPosition="3"  foregroundColor="#00f0f0f0"  alphatest="on">
			<convert type="PermanentClockTime">minHand</convert>
		</widget>
		<widget source="global.CurrentTime" render="PermanentClockWatches" position="20,21" size="31,31" zPosition="2"  foregroundColor="#00f0f0f0"  alphatest="on">
			<convert type="PermanentClockTime">hourHand</convert>
		</widget>
	</screen>"""
##############################################################################
SKIN = """
	<screen position="0,0" size="120,30" zPosition="-1" backgroundColor="#ff000000" title="Permanent Clock" flags="wfNoBorder">
		<widget source="global.CurrentTime" render="Label" position="1,1" size="120,30" backgroundColor="#ff000000" transparent="1" zPosition="0" foregroundColor="#00f0f0f0" borderWidth="2" font="Regular;26" borderColor="#00000000" valign="center" halign="center">
			<convert type="ClockToText">Default</convert>
		</widget>
	</screen>"""
##############################################################################
SKIN0 = """
	<screen position="0,0" size="120,30" zPosition="-1" backgroundColor="#ff000000" title="Permanent Clock" flags="wfNoBorder">
		<widget source="global.CurrentTime" render="Label" position="1,1" size="120,30" backgroundColor="#ff000000" transparent="1" zPosition="0" foregroundColor="#00ffc000" borderWidth="2" font="Regular;26" borderColor="#00000000" valign="center" halign="center">
			<convert type="ClockToText">Default</convert>
		</widget>
	</screen>"""
##############################################################################
SKINL = """
	<screen position="0,0" size="235,48" zPosition="-1" backgroundColor="#ff000000" title="Permanent Clock" flags="wfNoBorder">
		<widget source="global.CurrentTime" render="Label" position="1,1" size="180,45" backgroundColor="#ff000000" transparent="1" zPosition="0" foregroundColor="#00f0f0f0" borderWidth="2" font="Regular;39" borderColor="#00000000" valign="center" halign="right">
			<convert type="ClockToText">Default</convert>
		</widget>
		<widget source="global.CurrentTime" render="Label" position="181,14" size="50,30" font="Regular;22" backgroundColor="#ff000000" transparent="1" zPosition="0" foregroundColor="#00f0f0f0" borderWidth="2" borderColor="#00000000" halign="left">
			<convert type="ClockToText">Format::%S</convert>
		</widget>	</screen>"""
##############################################################################
SKIN0L = """
	<screen position="0,0" size="235,48" zPosition="-1" backgroundColor="#ff000000" title="Permanent Clock" flags="wfNoBorder">
		<widget source="global.CurrentTime" render="Label" position="1,1" size="180,45" backgroundColor="#ff000000" transparent="1" zPosition="0" foregroundColor="#00ffc000" borderWidth="2" font="Regular;39" borderColor="#00000000" valign="center" halign="right">
			<convert type="ClockToText">Default</convert>
		</widget>
		<widget source="global.CurrentTime" render="Label" position="181,14" size="50,30" font="Regular;22" backgroundColor="#ff000000" transparent="1" zPosition="0" foregroundColor="#00ffc000" borderWidth="2" borderColor="#00000000" halign="left">
			<convert type="ClockToText">Format::%S</convert>
		</widget>	</screen>"""
##############################################################################


class PermanentClockNewScreen(Screen):
	def __init__(self, session):
		if config.plugins.PermanentClock.analog.value:
			if config.plugins.PermanentClock.color_analog.value == "1":
				self.skin = SKIN1
			elif config.plugins.PermanentClock.color_analog.value == "2":
				self.skin = SKIN2
			elif config.plugins.PermanentClock.color_analog.value == "3":
				self.skin = SKIN3
			elif config.plugins.PermanentClock.color_analog.value == "4":
				self.skin = SKIN4
			elif config.plugins.PermanentClock.color_analog.value == "5":
				self.skin = SKIN5
			elif config.plugins.PermanentClock.color_analog.value == "6":
				self.skin = SKIN6
			elif config.plugins.PermanentClock.color_analog.value == "7":
				self.skin = SKIN7
		else:
			if config.plugins.PermanentClock.color_digital.value == "0":
				self.skin = SKIN0
			elif config.plugins.PermanentClock.color_digital.value == "1":
				self.skin = SKIN
			elif config.plugins.PermanentClock.color_digital.value == "2":
				self.skin = SKINL
			elif config.plugins.PermanentClock.color_digital.value == "3":
				self.skin = SKIN0L
		Screen.__init__(self, session)
		self.onShow.append(self.movePosition)

	def movePosition(self):
		if self.instance:
			self.instance.move(ePoint(config.plugins.PermanentClock.position_x.value, config.plugins.PermanentClock.position_y.value))


class PermanentClock():
	def __init__(self):
		self.dialog = None
		self.clockShown = False
		self.clockey = False

	def gotSession(self, session):
		self.dialog = session.instantiateDialog(PermanentClockNewScreen)
		self.showHide()
		self.unload_key(True)
		self.start_key()

	def start_key(self):
		if config.plugins.PermanentClock.show_hide.value and not self.clockey:
			if 'showClock' not in globalActionMap.actions:
				readKeymap("/usr/lib/enigma2/python/Plugins/Extensions/PermanentClock/keymap.xml")
				globalActionMap.actions['showClock'] = self.ShowHideKey
			self.clockey = True

	def unload_key(self, force=False):
		if not config.plugins.PermanentClock.show_hide.value and self.clockey or force:
			removeKeymap("/usr/lib/enigma2/python/Plugins/Extensions/PermanentClock/keymap.xml")
			if 'showClock' in globalActionMap.actions:
				del globalActionMap.actions['showClock']
			self.clockey = False

	def ShowHideKey(self):
		if config.plugins.PermanentClock.enabled.value:
			if self.clockShown:
				self.clockShown = False
				self.dialog.show()
			else:
				self.clockShown = True
				self.dialog.hide()
		return 0

	def changeVisibility(self):
		if config.plugins.PermanentClock.enabled.value:
			config.plugins.PermanentClock.enabled.value = False
		else:
			config.plugins.PermanentClock.enabled.value = True
		config.plugins.PermanentClock.enabled.save()
		self.showHide()

	def changeAnalog(self):
		if config.plugins.PermanentClock.analog.value:
			config.plugins.PermanentClock.analog.value = False
		else:
			config.plugins.PermanentClock.analog.value = True
		config.plugins.PermanentClock.analog.save()
		self.dialog = None

	def ColorAnalog(self):
		config.plugins.PermanentClock.color_analog.save()
		self.dialog = None

	def ColorDigital(self):
		config.plugins.PermanentClock.color_digital.save()
		self.dialog = None

	def changeKey(self):
		if config.plugins.PermanentClock.show_hide.value:
			config.plugins.PermanentClock.show_hide.value = False
		else:
			config.plugins.PermanentClock.show_hide.value = True
		config.plugins.PermanentClock.show_hide.save()

	def showHide(self):
		if config.plugins.PermanentClock.enabled.value:
			self.dialog.show()
		else:
			self.dialog.hide()


pClock = PermanentClock()


class PermanentClockPositioner(Screen):
	def __init__(self, session):
		if config.plugins.PermanentClock.analog.value:
			if config.plugins.PermanentClock.color_analog.value == "1":
				self.skin = SKIN1
			elif config.plugins.PermanentClock.color_analog.value == "2":
				self.skin = SKIN2
			elif config.plugins.PermanentClock.color_analog.value == "3":
				self.skin = SKIN3
			elif config.plugins.PermanentClock.color_analog.value == "4":
				self.skin = SKIN4
			elif config.plugins.PermanentClock.color_analog.value == "5":
				self.skin = SKIN5
			elif config.plugins.PermanentClock.color_analog.value == "6":
				self.skin = SKIN6
			elif config.plugins.PermanentClock.color_analog.value == "7":
				self.skin = SKIN7
		else:
			if config.plugins.PermanentClock.color_digital.value == "0":
				self.skin = SKIN0
			elif config.plugins.PermanentClock.color_digital.value == "1":
				self.skin = SKIN
			elif config.plugins.PermanentClock.color_digital.value == "2":
				self.skin = SKINL
			elif config.plugins.PermanentClock.color_digital.value == "3":
				self.skin = SKIN0L
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["WizardActions"],
		{
			"left": self.left,
			"up": self.up,
			"right": self.right,
			"down": self.down,
			"ok": self.ok,
			"back": self.exit
		}, -1)
		self.desktopWidth = getDesktop(0).size().width()
		self.desktopHeight = getDesktop(0).size().height()
		self.slider = 1
		self.onLayoutFinish.append(self.__layoutFinished)

	def __layoutFinished(self):
		self.movePosition()

	def movePosition(self):
		self.instance.move(ePoint(config.plugins.PermanentClock.position_x.value, config.plugins.PermanentClock.position_y.value))

	def left(self):
		value = config.plugins.PermanentClock.position_x.value
		value -= self.slider
		if value < 0:
			value = 0
		config.plugins.PermanentClock.position_x.value = value
		self.movePosition()

	def up(self):
		value = config.plugins.PermanentClock.position_y.value
		value -= self.slider
		if value < 0:
			value = 0
		config.plugins.PermanentClock.position_y.value = value
		self.movePosition()

	def right(self):
		value = config.plugins.PermanentClock.position_x.value
		value += self.slider
		if value > self.desktopWidth:
			value = self.desktopWidth
		config.plugins.PermanentClock.position_x.value = value
		self.movePosition()

	def down(self):
		value = config.plugins.PermanentClock.position_y.value
		value += self.slider
		if value > self.desktopHeight:
			value = self.desktopHeight
		config.plugins.PermanentClock.position_y.value = value
		self.movePosition()

	def ok(self):
		menu = [(_("Save"), "save"), (_("Set slider"), "slider")]

		def extraAction(choice):
			if choice is not None:
				if choice[1] == "slider":
					self.session.openWithCallback(self.setSliderStep, InputBox, title=_("Set slider step (1 - 20):"), text=str(self.slider), type=Input.NUMBER)
				elif choice[1] == "save":
					self.Save()
		self.session.openWithCallback(extraAction, ChoiceBox, list=menu)

	def setSliderStep(self, step):
		if step and (0 < int(step) < 21):
			self.slider = int(step)

	def Save(self):
		config.plugins.PermanentClock.position_x.save()
		config.plugins.PermanentClock.position_y.save()
		self.close()

	def exit(self):
		config.plugins.PermanentClock.position_x.cancel()
		config.plugins.PermanentClock.position_y.cancel()
		self.close()


class PermanentClockMenu(Screen):
	skin = """
		<screen position="center,center" size="420,145" title="%s">
			<widget name="list" position="10,10" size="400,135" />
		</screen>""" % _("Permanent Clock")

	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self["list"] = MenuList([])
		self.setTitle(_("Permanent Clock Setup"))
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.okClicked, "cancel": self.close}, -1)
		self.onLayoutFinish.append(self.showMenu)

	def showMenu(self):
		list = []
		if config.plugins.PermanentClock.enabled.value:
			list.append(_("Deactivate permanent clock"))
			list.append(_("Change permanent clock position"))
		else:
			list.append(_("Activate permanent clock"))
		if config.plugins.PermanentClock.enabled.value:
			if config.plugins.PermanentClock.analog.value:
				list.append(_("Show digital clock"))
				list.append(_("Color analog clock"))
			else:
				list.append(_("Show analog clock"))
				list.append(_("Color digital clock"))
		if config.plugins.PermanentClock.enabled.value:
			if config.plugins.PermanentClock.show_hide.value:
				list.append(_("Disable key 'long EXIT' show/hide"))
			else:
				list.append(_("Enable key 'long EXIT' show/hide"))
		self["list"].setList(list)

	def newConfig(self, digital=False):
		pClock.dialog.hide()
		if digital:
			pClock.ColorDigital()
		else:
			pClock.ColorAnalog()
		if pClock.dialog is None:
			pClock.gotSession(self.session)

	def okClicked(self):
		sel = self["list"].getCurrent()
		if pClock.dialog is None:
			pClock.gotSession(self.session)
		if sel == _("Deactivate permanent clock") or sel == _("Activate permanent clock"):
			pClock.changeVisibility()
			self.showMenu()
		if sel == _("Change permanent clock position"):
			pClock.dialog.hide()
			self.session.openWithCallback(self.positionerCallback, PermanentClockPositioner)
		if sel == _("Show analog clock") or sel == _("Show digital clock"):
			if pClock.dialog is not None:
				pClock.dialog.hide()
				pClock.changeAnalog()
				self.showMenu()
				if pClock.dialog is None:
					pClock.gotSession(self.session)
		if sel == _("Disable key 'long EXIT' show/hide"):
			if pClock.dialog is not None:
				pClock.changeKey()
				self.showMenu()
				pClock.unload_key()
		if sel == _("Enable key 'long EXIT' show/hide"):
			if pClock.dialog is not None:
				pClock.changeKey()
				self.showMenu()
				pClock.start_key()
		if sel == _("Color analog clock"):
			self.colorClock()
		if sel == _("Color digital clock"):
			self.colorClock(digital=True)

	def colorClock(self, digital=False):
		if digital:
			list = [
				(_("yellow"), self.skins0),
				(_("white"), self.skins),
				(_("large yellow"), self.skins0l),
				(_("large white"), self.skinsl),
			]
		else:
			list = [
				(_("black-yellow"), self.skins1),
				(_("black-blue"), self.skins2),
				(_("blue"), self.skins3),
				(_("black-white"), self.skins4),
				(_("white"), self.skins5),
				(_("transparent"), self.skins6),
				(_("PLi-transparent"), self.skins7),
			]
		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			title=_("Choice color clock:"),
			list=list,
		)

	def menuCallback(self, ret=None):
		ret and ret[1]()

	def positionerCallback(self, callback=None):
		pClock.showHide()

	def skins(self):
		config.plugins.PermanentClock.color_digital.value = "1"
		self.newConfig(digital=True)

	def skins0(self):
		config.plugins.PermanentClock.color_digital.value = "0"
		self.newConfig(digital=True)

	def skinsl(self):
		config.plugins.PermanentClock.color_digital.value = "2"
		self.newConfig(digital=True)

	def skins0l(self):
		config.plugins.PermanentClock.color_digital.value = "3"
		self.newConfig(digital=True)

	def skins1(self):
		config.plugins.PermanentClock.color_analog.value = "1"
		self.newConfig()

	def skins2(self):
		config.plugins.PermanentClock.color_analog.value = "2"
		self.newConfig()

	def skins3(self):
		config.plugins.PermanentClock.color_analog.value = "3"
		self.newConfig()

	def skins4(self):
		config.plugins.PermanentClock.color_analog.value = "4"
		self.newConfig()

	def skins5(self):
		config.plugins.PermanentClock.color_analog.value = "5"
		self.newConfig()

	def skins6(self):
		config.plugins.PermanentClock.color_analog.value = "6"
		self.newConfig()

	def skins7(self):
		config.plugins.PermanentClock.color_analog.value = "7"
		self.newConfig()


def sessionstart(reason, **kwargs):
	global _session
	if reason == 0 and _session is None:
		_session = kwargs["session"]
		if _session:
			pClock.gotSession(_session)


def startConfig(session, **kwargs):
	session.open(PermanentClockMenu)


def main(menuid):
	if IMAGEDISTRO in ('teamblue'):
		if menuid != "general_menu":
			return []
	elif IMAGEDISTRO in ('openhdf'):
		if menuid != "gui_menu":
			return []
	else:
		if menuid != "system":
			return []
	return [(_("Permanent Clock"), startConfig, "permanent_clock", None)]


def Plugins(**kwargs):
	return [
		PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart),
		PluginDescriptor(name=_("Permanent Clock"), description=_("Shows the clock permanent on the screen"), where=PluginDescriptor.WHERE_MENU, fnc=main)]
