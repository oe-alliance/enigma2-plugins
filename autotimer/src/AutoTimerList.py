# -*- coding: UTF-8 -*-
# for localized messages
from . import _

# GUI (Components)
from Components.MenuList import MenuList
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT

from skin import parseColor, parseFont

class AutoTimerList(MenuList):
	"""Defines a simple Component to show Timer name"""

	def __init__(self, entries):
		MenuList.__init__(self, entries, False, content = eListboxPythonMultiContent)

		self.l.setFont(0, gFont("Regular", 22))
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setItemHeight(25)
		self.colorDisabled = 12368828

	def applySkin(self, desktop, parent):
		attribs = [ ] 
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "font":
					self.l.setFont(0, parseFont(value, ((1,1),(1,1))))
				elif attrib == "itemHeight":
					self.l.setItemHeight(int(value))
				elif attrib == "colorDisabled":
					self.colorDisabled = parseColor(value).argb()
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs
		return MenuList.applySkin(self, desktop, parent)

	#
	#  | <Name of AutoTimer> |
	#
	def buildListboxEntry(self, timer):
		size = self.l.getItemSize()

		color = None
		if not timer.enabled:
			color = self.colorDisabled

		return [
			None,
			(eListboxPythonMultiContent.TYPE_TEXT, 5, 0, size.width() - 5, size.height(), 0, RT_HALIGN_LEFT, timer.name, color, color)
		]

	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]

	def moveToEntry(self, entry):
		if entry is None:
			return

		idx = 0
		for x in self.list:
			if x[0] == entry:
				self.instance.moveSelectionTo(idx)
				break
			idx += 1

