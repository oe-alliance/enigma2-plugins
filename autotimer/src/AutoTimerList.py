# for localized messages
from . import _

# GUI (Components)
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, \
	RT_HALIGN_RIGHT, RT_VALIGN_CENTER

from ServiceReference import ServiceReference
from Tools.FuzzyDate import FuzzyTime

class AutoTimerList(MenuList):
	"""Defines a simple Component to show Timer name"""
	
	def __init__(self, entries):
		MenuList.__init__(self, entries, False, content = eListboxPythonMultiContent)

		self.l.setFont(0, gFont("Regular", 22))
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setItemHeight(25)

	#
	#  | <Name of AutoTimer> |
	#
	def buildListboxEntry(self, timer):
		res = [ None ]
		width = self.l.getItemSize().width()

		if timer.enabled:
			# Append with default color
			res.append(MultiContentEntryText(pos=(5, 0), size=(width, 25), font=0, flags = RT_HALIGN_LEFT, text = timer.name))
		else:
			# Append with grey as color
			res.append(MultiContentEntryText(pos=(5, 0), size=(width, 25), font=0, flags = RT_HALIGN_LEFT, text = timer.name, color = 12368828))

		return res

class AutoTimerPreviewList(MenuList):
	"""Preview Timers, emulates TimerList"""
	
	def __init__(self, entries):
		MenuList.__init__(self, entries, False, content = eListboxPythonMultiContent)

		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 18))
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setItemHeight(70)

	#
	#  | <Service>     <Name of the Event>  |
	#  | <start, end>  <Name of AutoTimer>  |
	#
	def buildListboxEntry(self, name, begin, end, serviceref, timername):
		res = [ None ]
		width = self.l.getItemSize().width()

		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, 30, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, ServiceReference(serviceref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 30, width, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, name))

		res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 50, 400, 20, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, (("%s, %s ... %s (%d " + _("mins") + ")") % (FuzzyTime(begin) + FuzzyTime(end)[1:] + ((end - begin) / 60,)))))

		res.append((eListboxPythonMultiContent.TYPE_TEXT, width-240, 50, 240, 20, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, timername))

		return res

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