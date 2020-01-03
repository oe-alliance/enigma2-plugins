# -*- coding: utf-8 -*-
from enigma import *
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Components.Pixmap import Pixmap
from Components.ActionMap import HelpableActionMap, ActionMap, NumberActionMap
from Components.ScrollLabel import ScrollLabel
from Components.Input import Input
from Components.Label import Label
from Components.HTMLComponent import *
from Components.GUIComponent import *
from Plugins.Plugin import PluginDescriptor

from Tools.NumericalTextInput import *
from Tools.Directories import *

#from socket import socket

import e2reactor

from twisted.internet import reactor
from twisted.internet import protocol
from twisted.python import log
from twisted.internet.defer import *

from e2chat import *
from e2account import *
from e2support import *
from dreamIRCTools import *
from dreamIRCSetup import *
from protocols import irc
import ircsupport

import os 
import string
import time
import datetime
import sys
x=0
y=0

class dreamIRCMainMenu(Screen):

	from enigma import getDesktop
	desk = getDesktop(0)
	global x,y
	x= int(desk.size().width())
	y= int(desk.size().height())
	print "[dreamIRC] mainscreen: current desktop size: %dx%d" % (x,y)

	if (y>=720):
		skin = """
			<screen position="80,80" size="1120,600"  title="dreamIRC" >
				<widget name="buddy" position="940,35" size="170,450" font="Regular;14" />
				<widget name="chat" position="10,35" size="920,460" font="Regular;14" />
				<widget name="input" position="10,550" size="830,20" font="Regular;16" />
				<widget name="chat.desc" position="10,10" size="460,20" font="Regular;16" />
				<widget name="buddy.desc" position="940,10" size="120,20" font="Regular;16" />
				<widget name="input.desc" position="10,520" size="360,18" font="Regular;16" />
				<widget name="red.pic" position="910,511" size="15,15" pixmap="skin_default/buttons/button_red.png" transparent="1" alphatest="on"/>
				<widget name="green.pic" position="910,531" size="15,15" pixmap="skin_default/buttons/button_green.png" transparent="1" alphatest="on"/>
				<widget name="yellow.pic" position="910,551" size="15,15" pixmap="skin_default/buttons/button_yellow.png" transparent="1" alphatest="on"/>
				<widget name="blue.pic" position="910,571" size="15,15" pixmap="skin_default/buttons/button_blue.png" transparent="1" alphatest="on"/>
				<widget name="disconnect.desc" position="940,510" size="110,20" font="Regular;16" />
				<widget name="connect.desc" position="940,530" size="110,20" font="Regular;16" />
				<widget name="settings.desc" position="940,550" size="110,20" font="Regular;16" />
				<widget name="blue.desc" position="940,570" size="180,20" font="Regular;16" />                                
			</screen>"""
	else:	
		skin = """
			<screen position="60,80" size="600,450"  title="dreamIRC" >
				<widget name="buddy" position="480,35" size="120,310" font="Regular;14" />
				<widget name="chat" position="10,35" size="460,310" font="Regular;14" />
				<widget name="input" position="10,400" size="360,20" font="Regular;16" />
				<widget name="chat.desc" position="10,10" size="460,20" font="Regular;16" />
				<widget name="buddy.desc" position="480,10" size="120,20" font="Regular;16" />
				<widget name="input.desc" position="10,370" size="360,18" font="Regular;16" />
				<widget name="red.pic" position="470,362" size="15,15" pixmap="skin_default/buttons/button_red.png" transparent="1" alphatest="on"/>
				<widget name="green.pic" position="470,382" size="15,15" pixmap="skin_default/buttons/button_green.png" transparent="1" alphatest="on"/>
				<widget name="yellow.pic" position="470,402" size="15,15" pixmap="skin_default/buttons/button_yellow.png" transparent="1" alphatest="on"/>
				<widget name="blue.pic" position="470,422" size="15,15" pixmap="skin_default/buttons/button_blue.png" transparent="1" alphatest="on"/>
				<widget name="disconnect.desc" position="490,360" size="110,20" font="Regular;16" />
				<widget name="connect.desc" position="490,380" size="110,20" font="Regular;16" />
				<widget name="settings.desc" position="490,400" size="110,20" font="Regular;16" />
				<widget name="blue.desc" position="490,420" size="110,20" font="Regular;16" />
			</screen>"""
		
	
	def __init__(self, session, args = 0):
		global x,y
		self.skin = dreamIRCMainMenu.skin
		Screen.__init__(self, session)

		self.menu = args
		self.pipe=MessagePipe()
		self.account = AccountManager(self.session)

		self.list = []
		self.menuList = []
		
		self.connected = False

		self["buddy"] = BuddyWindow("")
		self["chat"] = ChatWindow("")
		self["input"] = Input("")

		self["buddy.desc"] = Label(_("User Online"))
		self["input.desc"] = Label(_("Type your text here and press OK to send:"))
		self["chat.desc"] = ChanName(_("ChatBox"))
		self["connect.desc"] = Label(_("Connect"))
		self["disconnect.desc"] = Label(_("Disconnect"))
		self["settings.desc"] = Label(_("Settings"))
		if y>=720:
				self["blue.desc"] = Label(_("virtual Keyboard"))
		else:
				self["blue.desc"] = Label(_("virtual Keyb."))				
		self["green.pic"] = Pixmap()
		self["red.pic"] = Pixmap()
		self["yellow.pic"] = Pixmap()
		self["blue.pic"] = Pixmap()
		
		self["actions"] = NumberActionMap(["dreamIRCActions", "InputBoxActions", "InputAsciiActions", "KeyboardInputActions"],
		{
			"gotAsciiCode": self.gotAsciiCode,
			"red": self.redPressed,
			"green": self.greenPressed,
			"yellow": self.yellowPressed,
			"blue": self.bluePressed,
			"ok": self.go,
			"cancel": self.closePlugin,
			"back": self.closePlugin,
			"right": self.keyRight,
			"left": self.keyLeft,
			"up": self["chat"].pageUp,
			"down": self["chat"].pageDown,
			"buddyUp": self["buddy"].pageUp,
			"buddyDown": self["buddy"].pageDown,
			"home": self.keyHome,                
			"end": self.keyEnd,
			"delete": self.keyDelete,
			"deleteForward": self.keyDeleteForward,
			"deleteBackward": self.keyDeleteBackward,
			"tab": self.keyTab,
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
			"0": self.keyNumberGlobal            
		}, -1)
		rcinput = eRCInput.getInstance()
		rcinput.setKeyboardMode(rcinput.kmAscii)
		
		self.checkStatus()

	def gotAsciiCode(self):
		self["input"].handleAscii(getPrevAsciiCode())
	
	def keyUp(self):
		self["input"].up()
	
	def keyDown(self):
		self["input"].down()
	
	def keyLeft(self):
		self["input"].left()
	
	def keyRight(self):
		self["input"].right()
	
	def keyTab(self):
		self["input"].tab()
	
	def keyHome(self):
		self["input"].home()
	
	def keyEnd(self):
		self["input"].end()

	def keyNumberGlobal(self, number):
		print "You pressed number " + str(number)
		self["input"].number(number)
		
	def keyDelete(self):
		self["input"].delete()
	
	def keyDeleteForward(self):
		self["input"].delete()
	
	def keyDeleteBackward(self):
		self["input"].left()
		self["input"].delete()
		
	def closePlugin(self):
		rcinput = eRCInput.getInstance()
		rcinput.setKeyboardMode(rcinput.kmNone)
		self.close(None)
		
	def greenPressed(self):
		if self.checkStatus()==0:
			self.pipe.add("connecting... pls wait...")
			self.account = AccountManager(self.session)    #reload accounts :)
			self.account.startConnect()
			self["disconnect.desc"].show()
			self["red.pic"].show()

	def redPressed(self):
		if self.checkStatus()==1:
			self.pipe.add("disconnecting... pls wait...")
			self.pipe.addOutText("/QUIT")
			try:
				timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime(time.time()))
				fp = file("/var/log/dreamIRC.log", 'r')
				fp.close()
				os.rename("/var/log/dreamIRC.log", "/var/log/dreamIRC_%s.log"%timestamp)
			except IOError:
				print "--- nothing to remove---"
			self.pipe.clear()
			self.pipe.add(" -- not connected.. pls press green to connect!!\n")
			self.pipe.clearBuddyList()
			self.pipe.resetDesc()
			self["disconnect.desc"].hide()
			self["red.pic"].hide()

	def checkStatus(self):
		status = self.account.getConnectionInfo()
		if status[0]==1 or len(self["buddy"].getText())>1:
			self["disconnect.desc"].show()
			self["red.pic"].show()
			status[0]=1
		elif status[0]==0:
			self["disconnect.desc"].hide()
			self["red.pic"].hide()
		return status[0]
	
	def bluePressed(self):
		self.checkStatus()
		self.session.openWithCallback(self.VirtualKeyBoardTextEntry, VirtualKeyBoard, title = (_("Enter your text here:")), text = "")
		
	def yellowPressed(self):
		self.checkStatus()
		self.session.openWithCallback(self.resetKeyboard,dreamIRCSetupScreen)
		
	def resetKeyboard(self):
		rcinput = eRCInput.getInstance()
		rcinput.setKeyboardMode(rcinput.kmAscii)
		
	def go(self):
		if self.checkStatus()==1:
#			self.pipe.debug(" TEXT = %s   - laenge = %d  !!!!" % (self["input"].getText(),len(self["input"].getText())))
			if (len(self["input"].getText()) >= 1):
				self.pipe.addOutText(self["input"].getText())
				self.clearInput()
			
	def clearInput(self):
		self["input"].setText("")
			
	def VirtualKeyBoardTextEntry(self, callback = None):
		if callback is not None and len(callback):
			print " TEXT = %s   - laenge = %d  !!!!" % (callback,len(callback))
			self.pipe.addOutText(callback)

def main(session, **kwargs):
        session.open(dreamIRCMainMenu)

def Plugins(**kwargs):
        return PluginDescriptor(
                name="dreamIRC",
                description="dreamIRC Client for Enigma2",
                icon="plugin.png",
                where=[ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
                fnc=main)