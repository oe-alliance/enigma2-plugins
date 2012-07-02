#!/usr/bin/python
# -*- coding: utf-8 -*- 
#  Advanced Movie Selection for Dreambox-Enigma2
#
#  The plugin is developed on the basis from a lot of single plugins (thx for the code @ all)
#  Coded by JackDaniel (c)2011
#  Support: www.i-have-a-dreambox.com
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
from Tools.NumericalTextInput import NumericalTextInput
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import NumberActionMap

class NTIVirtualKeyBoard(VirtualKeyBoard, NumericalTextInput):
	def __init__(self, session, **kwargs):
		VirtualKeyBoard.__init__(self, session, **kwargs)
		NumericalTextInput.__init__(self, nextFunc=self.nextFunc)

		self.skinName = "VirtualKeyBoard"

		self["NumberActions"] = NumberActionMap(["NumberActions"],
		{
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
		})

		self.editing = False

	def backClicked(self):
		self.nextKey()
		self.editing = False
		self["text"].setMarkedPos(-1)
		VirtualKeyBoard.backClicked(self)

	def okClicked(self):
		self.nextKey()
		self.editing = False
		self["text"].setMarkedPos(-1)
		VirtualKeyBoard.okClicked(self)

	def keyNumberGlobal(self, number):
		unichar = self.getKey(number)
		if not self.editing:
			self.text = self["text"].getText()
			self.editing = True
			self["text"].setMarkedPos(len(self.text))
		self["text"].setText(self.text + unichar.encode('utf-8', 'ignore'))

	def nextFunc(self):
		self.text = self["text"].getText()
		self.editing = False
		self["text"].setMarkedPos(-1)

