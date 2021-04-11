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
