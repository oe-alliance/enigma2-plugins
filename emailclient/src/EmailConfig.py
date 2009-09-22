from Screens.Screen import Screen
from Components.config import config, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.ActionMap import ActionMap

from . import _
import plugin

from enigma import getDesktop
DESKTOP_WIDTH = getDesktop(0).size().width()
DESKTOP_HEIGHT = getDesktop(0).size().height()
def scaleH(y2, y1):
	if y2 == -1:
		y2 = y1*1280/720
	elif y1 == -1:
		y1 = y2*720/1280
	return scale(y2, y1, 1280, 720, DESKTOP_WIDTH)
def scaleV(y2, y1):
	if y2 == -1:
		y2 = y1*720/576
	elif y1 == -1:
		y1 = y2*576/720
	return scale(y2, y1, 720, 576, DESKTOP_HEIGHT)
def scale(y2, y1, x2, x1, x):
	return (y2 - y1) * (x - x1) / (x2 - x1) + y1

class EmailConfigScreen(ConfigListScreen,Screen):
	width = max(2*140+100, 550)
	height = 5*30+50
	buttonsGap = (width-2*140)/3
	skin = """
		<screen position="%d,%d" size="%d,%d" title="Email Setup" >
		<widget name="config" position="0,0" size="%d,%d" scrollbarMode="showOnDemand" />
		<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<widget name="buttonred" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="buttongreen" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="info" position="%d,%d" size="100,40" halign="right" zPosition="2"  foregroundColor="white" font="Regular;%d"/> 
		</screen>""" %(
					(DESKTOP_WIDTH-width)/2, (DESKTOP_HEIGHT-height)/2, width, height,
					width, height-50,  # config
					buttonsGap, height-45,
					2*buttonsGap+140, height-45,
					buttonsGap, height-45, scaleV(22,18),
					2*buttonsGap+140, height-45, scaleV(22,18),
					3*buttonsGap+2*140, height-45, scaleV(22,18)
					)

	def __init__(self, session, args = 0):
		Screen.__init__(self, session)
		self.list = []
		ConfigListScreen.__init__(self, self.list)
		self["buttonred"] = Label(_("cancel"))
		self["buttongreen"] = Label(_("ok"))
		self["info"] = Label('by 3c5x9')
		self["setupActions"] = ActionMap(["SetupActions"],
		{
			"green": self.save,
			"red": self.cancel,
			"save": self.save,
			"cancel": self.cancel,
			"ok": self.save,
		}, -2)
		self.createSetup()

	def createSetup(self):
		self.list = [
			getConfigListEntry(_("Username"), config.plugins.emailimap.username),
			getConfigListEntry(_("Password"), config.plugins.emailimap.password),
			getConfigListEntry(_("IMAP Server"), config.plugins.emailimap.server),
			getConfigListEntry(_("IMAP Port"), config.plugins.emailimap.port),
			getConfigListEntry(_("max of Headers to load"), config.plugins.emailimap.maxheadertoload),
			getConfigListEntry(_("show deleted entries"), config.plugins.emailimap.showDeleted),
			getConfigListEntry(_("notify about new mails"), config.plugins.emailimap.checkForNewMails)
		]
		if config.plugins.emailimap.checkForNewMails.value:
			self.list.append(getConfigListEntry(_("interval to check for new mails (minutes)"), config.plugins.emailimap.checkPeriod))
			self.list.append(getConfigListEntry(_("timeout displaying new mails (seconds)"), config.plugins.emailimap.timeout))
		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()

	def save(self):
		print "saving"
		for x in self["config"].list:
			x[1].save()
		if plugin.mailChecker:
			plugin.mailChecker.exit()
		if config.plugins.emailimap.checkForNewMails.value:
			plugin.mailChecker = plugin.CheckMail()
			
		self.close(True)

	def cancel(self):
		print "cancel"
		for x in self["config"].list:
			x[1].cancel()
		self.close(False)
