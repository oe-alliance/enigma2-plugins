# -*- coding: UTF-8 -*-
# for localized messages
from . import _

# GUI (Components)
from Components.MenuList import MenuList
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, \
	RT_HALIGN_RIGHT, RT_VALIGN_CENTER

from skin import parseColor, parseFont

from ServiceReference import ServiceReference
from Tools.FuzzyDate import FuzzyTime

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
					self.colorDisabled = int(parseColor(value))
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

class AutoTimerPreviewList(MenuList):
	"""Preview Timers, emulates TimerList"""

	def __init__(self, entries):
		MenuList.__init__(self, entries, False, content = eListboxPythonMultiContent)

		self.serviceNameFont = gFont("Regular", 20)
		self.l.setFont(0, self.serviceNameFont)
		self.font = gFont("Regular", 18)
		self.l.setFont(1, self.font)
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setItemHeight(70)

	def applySkin(self, desktop, parent):
		attribs = [ ] 
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "font":
					self.font = parseFont(value, ((1,1),(1,1)))
					self.l.setFont(1, self.font)
				elif attrib == "serviceNameFont":
					self.serviceNameFont = parseFont(value, ((1,1),(1,1)))
					self.l.setFont(0, self.serviceNameFont)
				elif attrib == "colorDisabled":
					self.colorDisabled = int(parseColor(value))
				elif attrib == "itemHeight":
					self.l.setItemHeight(int(value))
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs
		return MenuList.applySkin(self, desktop, parent)

	#
	#  | <Service>     <Name of the Event>  |
	#  | <start, end>  <Name of AutoTimer>  |
	#
	def buildListboxEntry(self, name, begin, end, serviceref, timername):
		size = self.l.getItemSize()
		width = size.width()
		snameHeight = self.serviceNameFont.pointSize + 10
		fontSize = self.font.pointSize + 2
		lastRow = snameHeight + fontSize

		return [
			None,
			(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, snameHeight, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, \
					ServiceReference(serviceref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')),
			(eListboxPythonMultiContent.TYPE_TEXT, 0, snameHeight, width, fontSize, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, name),
			(eListboxPythonMultiContent.TYPE_TEXT, 0, lastRow, 400, fontSize, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, \
					(("%s, %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(begin) + FuzzyTime(end)[1:] + ((end - begin) / 60,)))),
			(eListboxPythonMultiContent.TYPE_TEXT, width - 245, lastRow, 240, fontSize, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, timername)
		]

	def invalidate(self):
		self.l.invalidate()

	def moveToEntry(self, entry):
		if entry is None:
			return

		idx = 0
		for x in self.list:
			if x == entry:
				self.instance.moveSelectionTo(idx)
				break
			idx += 1

