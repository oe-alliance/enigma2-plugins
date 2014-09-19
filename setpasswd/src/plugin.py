from enigma import eConsoleAppContainer

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Screens.Setup import SetupSummary
from Components.ConfigList import ConfigList
from Components.config import config, getConfigListEntry, ConfigSelection, ConfigSubsection, ConfigText

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List
from Plugins.Plugin import PluginDescriptor

from __init__ import _

import string
import sys 
import time
from random import Random 

from boxbranding import getImageDistro
title=_("Change Root Password")

class ChangePasswdScreen(Screen):
	skin = """
		<screen position="65,160" size="585,250" title="%s" >
		<widget name="passwd" position="10,10" size="565,200" scrollbarMode="showOnDemand" />
		<ePixmap pixmap="skin_default/div-h.png" position="10,205" size="565,2" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/red.png" position="5,210" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="150,210" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="295,210" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="440,210" size="140,40" alphatest="on" />
		<widget source="key_red" render="Label" position="5,210" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
		<widget source="key_green" render="Label" position="150,210" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		<widget source="key_yellow" render="Label" position="295,210" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		<widget source="key_blue" render="Label" position="440,210" zPosition="1" size="140,40" font="Regular;17" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
	</screen>""" % title

	def __init__(self, session, args = 0):
		Screen.__init__(self, session)
		self.skin = ChangePasswdScreen.skin

		self.user="root"
		self.output_line = ""
		self.list = []
		
		self["passwd"] = ConfigList(self.list)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Set Password"))
		self["key_yellow"] = StaticText(_("new Random"))
		self["key_blue"] = StaticText(_("virt. Keyboard"))

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
				{
						"red": self.close,
						"green": self.SetPasswd,
						"yellow": self.newRandom,
						"blue": self.bluePressed,
						"cancel": self.close
				}, -1)
	
		self.buildList(self.GeneratePassword())

	def newRandom(self):
		self.buildList(self.GeneratePassword())
	
	def buildList(self, password):
		self.password=password
		self.list = []
		self.list.append(getConfigListEntry(_('Enter new Password'), ConfigText(default = self.password, fixed_size = False)))
		self["passwd"].setList(self.list)
		
	def GeneratePassword(self): 
		passwdChars = string.letters + string.digits
		passwdLength = 8
		return ''.join(Random().sample(passwdChars, passwdLength)) 

	def SetPasswd(self):
		print "Changing password for %s to %s" % (self.user,self.password) 
		self.container = eConsoleAppContainer()
		self.container.appClosed.append(self.runFinished)
		self.container.dataAvail.append(self.dataAvail)
		retval = self.container.execute("passwd %s" % self.user)
		if retval==0:
			message=_("Sucessfully changed password for root user to: ") + self.password
		else:
			message=_("Unable to change/reset password for root user")
		self.session.open(MessageBox, message , MessageBox.TYPE_ERROR)

	def dataAvail(self,data):
		self.output_line += data
		while True:
			i = self.output_line.find('\n')
			if i == -1:
				break
			self.processOutputLine(self.output_line[:i+1])
			self.output_line = self.output_line[i+1:]

	def processOutputLine(self,line):
		if line.find('password: '):
			self.container.write("%s\n"%self.password)

	def runFinished(self,retval):
		del self.container.dataAvail[:]
		del self.container.appClosed[:]
		del self.container
		self.close()
		
	def bluePressed(self):
		self.session.openWithCallback(self.VirtualKeyBoardTextEntry, VirtualKeyBoard, title = (_("Enter your password here:")), text = self.password)
	
	def VirtualKeyBoardTextEntry(self, callback = None):
		if callback is not None and len(callback):
			self.buildList(callback)

def startChange(menuid):
	if getImageDistro() in ('openmips'):
		if menuid != "general_menu":
			return [ ]
	else:
		if menuid != "system":
			return []
	return [(title, main, "change_root_passwd", 50)]

def main(session, **kwargs):
	session.open(ChangePasswdScreen)

def Plugins(**kwargs):
	return PluginDescriptor(
		name=title, 
		description=_("Change or reset the root password of your Receiver"),
		where = [PluginDescriptor.WHERE_MENU], fnc = startChange)
	