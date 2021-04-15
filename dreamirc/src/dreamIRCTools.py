#!/usr/bin/env python
from enigma import *
from Screens.Screen import Screen

from Components.Pixmap import *
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap, NumberActionMap
from Components.ScrollLabel import ScrollLabel
from Components.GUIComponent import *
from Components.MenuList import MenuList
from Components.Input import Input
from Components.Label import Label
from Components.config import *
from Components.ConfigList import ConfigList
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from Plugins.Plugin import PluginDescriptor
from Tools.NumericalTextInput import *
from Tools.Directories import *

import skin
from Components.HTMLComponent import *
from Components.GUIComponent import *
from enigma import eLabel, eWidget, eSlider, fontRenderClass, ePoint, eSize

import os
import string
import time
import datetime
import sys

import plugin
from plugin import *

import ircsupport
import xml.dom.minidom
from xml.dom.minidom import Node
from Tools import XMLTools
from Tools.XMLTools import elementsWithTag, mergeText

ChatText = str()
OutTextTmp = str()
BuddyList = str()
NewMsg = str()
Channel = str("ChatBox")

x = 0
y = 0

accounts_xml = "/etc/dreamIRC.xml"


class ChatWindow(ScrollLabel):
	def __init__(self, session):
		ScrollLabel.__init__(self, text="")
		self.timer = eTimer()
		self.timer.timeout.get().append(self.updateChatWindow)
		self.timer.start(250)
		self.pipe = MessagePipe()
		self.oldText = ""

	def updateChatWindow(self):
		if (len(self.pipe.LastMsg()) > 0) or (self.oldText != self.pipe.getChatText()):
			self.oldText = self.pipe.getChatText()
			self.setText(self.pipe.getChatText())
			self.lastPage()
			self.pipe.setLastMsg("")


class BuddyWindow(ScrollLabel):
	def __init__(self, session):
		ScrollLabel.__init__(self, text="")
		self.timer = eTimer()
		self.timer.timeout.get().append(self.updateBuddyWindow)
		self.timer.start(500)
		self.oldlist = ""

	def updateBuddyWindow(self):
		if (self.oldlist != BuddyList):
			self.setText(BuddyList)
			self.oldlist = BuddyList


class ChanName(Label):
	def __init__(self, session):
		Label.__init__(self, text=Channel)
		self.timer = eTimer()
		self.timer.timeout.get().append(self.updateChanName)
		self.timer.start(500)
		self.oldname = self.text
		self.pipe = MessagePipe()

	def updateChanName(self):
		self.newname = self.pipe.updateDesc()
		if (self.oldname != self.newname):
			self.setText(self.newname)
			self.oldname = self.newname


class MessagePipe():
	def __init__(self):
		global BuddyList
		self.logger = MessageLogger(open("/var/log/dreamIRC.log", "a"))
		self.debug_state = debug()
		if self.debug_state == True:
			self.debuglogger = MessageLogger(open("/var/log/dreamIRC_debug.log", "a"))

	def updateBuddyWindow(self):
		global BuddyList
		return BuddyList

	def getChatText(self):
		global ChatText
		return ChatText

	def LastMsg(self):
		global NewMsg
		return NewMsg

	def setLastMsg(self, text):
		global NewMsg
		NewMsg = str(text)

	def getOutText(self):
		global OutTextTmp
		return OutTextTmp

	def addOutText(self, text):
		global OutTextTmp
		OutTextTmp = str(text)

	def clearOutText(self):
		global OutTextTmp
		OutTextTmp = str("")
		return OutTextTmp

	def add(self, text):
		timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
		global ChatText, NewMsg
		ChatText = ChatText + "%s %s\n" % (timestamp, text)
		NewMsg = "%s %s" % (timestamp, text)
		self.logger.log("%s %s" % (timestamp, text))
		if self.debug_state == True:
			self.debuglogger.log("%s %s" % (timestamp, text))

	def debug(self, text):
		if self.debug_state == True:
			timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
			self.debuglogger.log("%s %s" % (timestamp, text))
		else:
			print text

	def clear(self):
		global ChatText
		ChatText = str("")

	def close(self):
		self.logger.close()
		if self.debug_state == True:
			self.debuglogger.close()

	def buildBuddyList(self, text):
		global BuddyList
		BuddyList = BuddyList + "%s\n" % text

	def clearBuddyList(self):
		global BuddyList
		BuddyList = ""

	def showBuddyList(self):
		global BuddyList

		return BuddyList

	def updateDesc(self):
		global Channel
		return Channel

	def getCannelName(self, text):
		global Channel
		Channel = "ChatBox #" + "%s\n" % text

	def resetDesc(self):
		global Channel
		Channel = "ChatBox"


class MessageLogger:
	def __init__(self, file):
		self.file = file
		print '[dreamIRC] %s  MESSAGE LOGGER = %s \n' % (time.strftime("[%H:%M:%S]", time.localtime(time.time())), self.file)

	def log(self, message):
		print '[dreamIRC] %s\n' % (message)
		self.file.write('%s\n' % (message))
		self.file.flush()

	def close(self):
		self.file.close()


def readLogFile(args):
	try:
		fp = file(args[0], 'r')
		lines = fp.readlines()
		fp.close()
		output = ""
		for x in lines:
			output += x
	except IOError:
		output = args[1]
	return output


def getMacAddress():
	for line in os.popen("/sbin/ifconfig"):
		if line.find('Ether') > -1:
			mac = line.split()[4]
			new_mac = mac.replace(":", "")
			break
	return new_mac


def debug():
	try:
		doc = xml.dom.minidom.parse(accounts_xml)
		root = doc.childNodes[0]
		for node in elementsWithTag(root.childNodes, "account"):
			debug = node.getAttribute("debug")
		if debug == "False":
			return False
		else:
			return True
	except IOError:
		return False
