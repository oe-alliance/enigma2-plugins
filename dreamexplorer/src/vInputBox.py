#######################################################################
#
#    vInputBox with grafical text view
#    based on InputBox(Enigma-2)
#
#    Coded by Vali (c)2010
#    Support: www.dreambox-tools.info
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################



from Screens.Screen import Screen
from Screens.NumericalTextInputHelpDialog import NumericalTextInputHelpDialog
from Components.ActionMap import NumberActionMap
from Components.Label import Label
from Components.Input import Input
from Tools.BoundFunction import boundFunction
from myNumericalTextInput import myNumericalTextInput
from enigma import eRCInput, getPrevAsciiCode, getDesktop



class vInputBox(Screen, myNumericalTextInput):
	vibnewx = str(getDesktop(0).size().width()-80)
	sknew = '<screen name="vInputBox" position="center,center" size="'+vibnewx+',70" title="Input...">\n'
	sknew = sknew + '<widget name="text" position="5,5" size="1270,25" font="Console;16"/>\n<widget name="input" position="0,40" size="'
	sknew = sknew + vibnewx + ',30" font="Console;22"/>\n</screen>'
	skin = sknew
	def __init__(self, session, title = "", windowTitle = _("Input"), useableChars = None, **kwargs):
		Screen.__init__(self, session)
		myNumericalTextInput.__init__(self, nextFunc = None, handleTimeout = False)
		self.session = session
		self["text"] = Label(title)
		self["input"] = Input(**kwargs)
		self.onShown.append(boundFunction(self.setTitle, windowTitle))
		if useableChars is not None:
			self["input"].setUseableChars(useableChars)
		self["actions"] = NumberActionMap(["WizardActions", "InputBoxActions", "InputAsciiActions", "KeyboardInputActions"], 
		{
			"gotAsciiCode": self.gotAsciiCode,
			"ok": self.go,
			"back": self.cancel,
			"left": self.keyLeft,
			"right": self.keyRight,
			"home": self.keyHome,
			"end": self.keyEnd,
			"deleteForward": self.keyDelete,
			"deleteBackward": self.keyBackspace,
			"tab": self.keyTab,
			"toggleOverwrite": self.keyInsert,
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
		if self["input"].type == Input.TEXT:
			rcinput = eRCInput.getInstance()
			rcinput.setKeyboardMode(rcinput.kmAscii)
		self.onLayoutFinish.append(self.NumDlgInit)

	def NumDlgInit(self):
		self.help_window = self.session.instantiateDialog(NumericalTextInputHelpDialog, self)
		self.help_window.show()

	def gotAsciiCode(self):
		self["input"].handleAscii(getPrevAsciiCode())

	def keyLeft(self):
		self["input"].left()

	def keyRight(self):
		self["input"].right()

	def keyNumberGlobal(self, number):
		self["input"].number(number)

	def keyDelete(self):
		self["input"].delete()

	def go(self):
		rcinput = eRCInput.getInstance()
		rcinput.setKeyboardMode(rcinput.kmNone)
		self.session.deleteDialog(self.help_window)
		self.help_window = None
		self.close(self["input"].getText())

	def cancel(self):
		rcinput = eRCInput.getInstance()
		rcinput.setKeyboardMode(rcinput.kmNone)
		self.session.deleteDialog(self.help_window)
		self.help_window = None
		self.close(None)

	def keyHome(self):
		self["input"].home()

	def keyEnd(self):
		self["input"].end()

	def keyBackspace(self):
		self["input"].deleteBackward()

	def keyTab(self):
		self["input"].tab()

	def keyInsert(self):
		self["input"].toggleOverwrite()






