##
## Permanent Clock
## by AliAbdul
##
from Components.ActionMap import ActionMap
from Components.config import config, ConfigInteger, ConfigSubsection, ConfigYesNo
from Components.Language import language
from Components.MenuList import MenuList
from enigma import ePoint, eTimer, getDesktop
from os import environ
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE
import gettext

##############################################################################

SKIN = """
	<screen position="0,0" size="90,24" zPosition="10" title="Permanent Clock" flags="wfNoBorder">
		<widget source="global.CurrentTime" render="Label" position="0,0" size="90,24" font="Regular;24" valign="center" halign="center" transparent="1">
			<convert type="ClockToText">Default</convert>
		</widget>
	</screen>"""

##############################################################################

config.plugins.PermanentClock = ConfigSubsection()
config.plugins.PermanentClock.enabled = ConfigYesNo(default=True)
config.plugins.PermanentClock.position_x = ConfigInteger(default=590)
config.plugins.PermanentClock.position_y = ConfigInteger(default=35)

##############################################################################

lang = language.getLanguage()
environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("PermanentClock", resolveFilename(SCOPE_LANGUAGE))

def _(txt):
	t = gettext.dgettext("PermanentClock", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

##############################################################################

class TitleScreen(Screen):
	def __init__(self, session, parent=None):
		Screen.__init__(self, session, parent)
		self.onLayoutFinish.append(self.setScreenTitle)

	def setScreenTitle(self):
		self.setTitle(_("Permanent Clock"))

##############################################################################

class PermanentClockScreen(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin = SKIN
		self.onShow.append(self.movePosition)

	def movePosition(self):
		if self.instance:
			self.instance.move(ePoint(config.plugins.PermanentClock.position_x.value, config.plugins.PermanentClock.position_y.value))

##############################################################################

class PermanentClock():
	def __init__(self):
		self.dialog = None

	def gotSession(self, session):
		self.dialog = session.instantiateDialog(PermanentClockScreen)
		self.showHide()

	def changeVisibility(self):
		if config.plugins.PermanentClock.enabled.value:
			config.plugins.PermanentClock.enabled.value = False
		else:
			config.plugins.PermanentClock.enabled.value = True
		config.plugins.PermanentClock.enabled.save()
		self.showHide()

	def showHide(self):
		if config.plugins.PermanentClock.enabled.value:
			self.dialog.show()
		else:
			self.dialog.hide()

pClock = PermanentClock()

##############################################################################

class PermanentClockPositioner(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin = SKIN
		
		self["actions"] = ActionMap(["WizardActions"],
		{
			"left": self.left,
			"up": self.up,
			"right": self.right,
			"down": self.down,
			"ok": self.ok,
			"back": self.exit
		}, -1)
		
		desktop = getDesktop(0)
		self.desktopWidth = desktop.size().width()
		self.desktopHeight = desktop.size().height()
		
		self.moveTimer = eTimer()
		self.moveTimer.timeout.get().append(self.movePosition)
		self.moveTimer.start(50, 1)

	def movePosition(self):
		self.instance.move(ePoint(config.plugins.PermanentClock.position_x.value, config.plugins.PermanentClock.position_y.value))
		self.moveTimer.start(50, 1)

	def left(self):
		value = config.plugins.PermanentClock.position_x.value
		value -= 1
		if value < 0:
			value = 0
		config.plugins.PermanentClock.position_x.value = value

	def up(self):
		value = config.plugins.PermanentClock.position_y.value
		value -= 1
		if value < 0:
			value = 0
		config.plugins.PermanentClock.position_y.value = value

	def right(self):
		value = config.plugins.PermanentClock.position_x.value
		value += 1
		if value > self.desktopWidth:
			value = self.desktopWidth
		config.plugins.PermanentClock.position_x.value = value

	def down(self):
		value = config.plugins.PermanentClock.position_y.value
		value += 1
		if value > self.desktopHeight:
			value = self.desktopHeight
		config.plugins.PermanentClock.position_y.value = value

	def ok(self):
		config.plugins.PermanentClock.position_x.save()
		config.plugins.PermanentClock.position_y.save()
		self.close()

	def exit(self):
		config.plugins.PermanentClock.position_x.cancel()
		config.plugins.PermanentClock.position_y.cancel()
		self.close()

##############################################################################

class PermanentClockMenu(TitleScreen):
	skin = """
		<screen position="150,235" size="420,105" title="Permanent Clock">
			<widget name="list" position="10,10" size="400,85" />
		</screen>"""

	def __init__(self, session):
		TitleScreen.__init__(self, session)
		self.session = session
		self["list"] = MenuList([])
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.okClicked, "cancel": self.close}, -1)
		self.onLayoutFinish.append(self.showMenu)

	def showMenu(self):
		list = []
		if config.plugins.PermanentClock.enabled.value:
			list.append(_("Deactivate permanent clock"))
		else:
			list.append(_("Activate permanent clock"))
		list.append(_("Change permanent clock position"))
		self["list"].setList(list)

	def okClicked(self):
		sel = self["list"].getCurrent()
		if sel == _("Deactivate permanent clock") or sel == _("Activate permanent clock"):
			if pClock.dialog is None:
				pClock.gotSession(self.session)
			pClock.changeVisibility()
			self.showMenu()
		else:
			if pClock.dialog is None:
				pClock.gotSession(self.session)
			pClock.dialog.hide()
			self.session.openWithCallback(self.positionerCallback, PermanentClockPositioner)

	def positionerCallback(self, callback=None):
		pClock.showHide()

##############################################################################

def sessionstart(reason, **kwargs):
	if reason == 0:
		pClock.gotSession(kwargs["session"])

def main(session, **kwargs):
	session.open(PermanentClockMenu)

##############################################################################

def Plugins(**kwargs):
	return [
		PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart),
		PluginDescriptor(name=_("Permanent Clock"), description=_("Shows the clock permanent on the screen"), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main)]
