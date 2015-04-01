from os import path

# -*- coding: UTF-8 -*-
# for localized messages
from . import _

# GUI (Components)
from Components.MenuList import MenuList
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, RT_VALIGN_TOP, RT_VALIGN_BOTTOM, getDesktop
from Tools.LoadPixmap import LoadPixmap
from ServiceReference import ServiceReference

from Tools.FuzzyDate import FuzzyTime
from time import localtime, time, strftime, mktime

from Tools.Directories import resolveFilename, SCOPE_SKIN_IMAGE
try:
	from Tools.Directories import SCOPE_ACTIVE_SKIN
except:
	from Tools.Directories import SCOPE_CURRENT_SKIN
	
from skin import parseColor, parseFont

class DAYS:
	MONDAY = 0
	TUESDAY = 1
	WEDNESDAY = 2
	THURSDAY = 3
	FRIDAY = 4
	SATURDAY = 5
	SUNDAY = 6
	WEEKEND = 'weekend'
	WEEKDAY = 'weekday'

class AutoTimerList(MenuList):
	"""Defines a simple Component to show Timer name"""

	def __init__(self, entries):
		MenuList.__init__(self, entries, False, content = eListboxPythonMultiContent)
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 18))
		self.l.setFont(2, gFont("Regular", 30))
		self.l.setFont(3, gFont("Regular", 27))
		self.l.setItemHeight(50)
		if path.exists(resolveFilename(SCOPE_ACTIVE_SKIN, "icons/lock_off.png")):
			self.iconDisabled = LoadPixmap(resolveFilename(SCOPE_ACTIVE_SKIN, "icons/lock_off.png"))
		else:
			self.iconDisabled = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/lock_off.png"))
		if path.exists(resolveFilename(SCOPE_ACTIVE_SKIN, "icons/lock_on.png")):
			self.iconEnabled = LoadPixmap(resolveFilename(SCOPE_ACTIVE_SKIN, "icons/lock_on.png"))
		else:
			self.iconEnabled = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/lock_on.png"))
		if path.exists(resolveFilename(SCOPE_ACTIVE_SKIN, "icons/timer_rec.png")):
			self.iconRecording = LoadPixmap(resolveFilename(SCOPE_ACTIVE_SKIN, "icons/timer_rec.png"))
		else:
			self.iconRecording = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/timer_rec.png"))
		if path.exists(resolveFilename(SCOPE_ACTIVE_SKIN, "icons/timer_zap.png")):
			self.iconZapped = LoadPixmap(resolveFilename(SCOPE_ACTIVE_SKIN, "icons/timer_zap.png"))
		else:
			self.iconZapped = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/timer_zap.png"))

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
	def buildListboxEntry(self, timer):
		screenwidth = getDesktop(0).size().width()
		if not timer.enabled:
			icon = self.iconDisabled
		else:
			icon = self.iconEnabled
		if timer.justplay:
			rectypeicon = self.iconZapped
		else:
			rectypeicon = self.iconRecording

		channel = []
		for t in timer.services:
			channel.append(ServiceReference(t).getServiceName())
		if len(channel) >0 :
			channel = ", ".join(channel)
		else:
			channel = _('All channels')
		height = self.l.getItemSize().height()
		width = self.l.getItemSize().width()
		res = [ None ]
		x = (2*width) // 3
		if screenwidth and screenwidth == 1920:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 78, 3, x-39, 38, 2, RT_HALIGN_LEFT|RT_VALIGN_BOTTOM, timer.name))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 3, 39, width-6, 35, 3, RT_HALIGN_LEFT|RT_VALIGN_BOTTOM, channel))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 52, 3, x-26, 25, 0, RT_HALIGN_LEFT|RT_VALIGN_BOTTOM, timer.name))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 2, 26, width-4, 23, 1, RT_HALIGN_LEFT|RT_VALIGN_BOTTOM, channel))

		if timer.include[3]:
			total = len(timer.include[3])
			count = 0
			days = []
			while count+1 <= total:
				day = timer.include[3][count]
				day = {
					'0': _("Mon"),
					'1': _("Tue"),
					'2': _("Wed"),
					'3': _("Thur"),
					'4': _("Fri"),
					'5': _("Sat"),
					'6': _("Sun"),
					"weekend": _("Weekend"),
					"weekday": _("Weekday")
					}[day]
				days.append(day)
				count += 1
			days = ', '.join(days)
		else:
			days = _("Everyday")
		if screenwidth and screenwidth == 1920:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, float(width)/10*4.5+1, 39, float(width)/10*5.5-5, 35, 3, RT_HALIGN_RIGHT|RT_VALIGN_BOTTOM, days))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, float(width)/10*4.5+1, 26, float(width)/10*5.5-5, 23, 1, RT_HALIGN_RIGHT|RT_VALIGN_BOTTOM, days))

		if timer.hasTimespan():
			nowt = time()
			now = localtime(nowt)
			begintime = int(mktime((now.tm_year, now.tm_mon, now.tm_mday, timer.timespan[0][0], timer.timespan[0][1], 0, now.tm_wday, now.tm_yday, now.tm_isdst)))
			endtime = int(mktime((now.tm_year, now.tm_mon, now.tm_mday, timer.timespan[1][0], timer.timespan[1][1], 0, now.tm_wday, now.tm_yday, now.tm_isdst)))
			timespan = ((" %s ... %s") % (FuzzyTime(begintime)[1], FuzzyTime(endtime)[1]))
		else:
			timespan = _("Any time")
		if screenwidth and screenwidth == 1920:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width-225-4, 3, 225, 35, 3, RT_HALIGN_RIGHT|RT_VALIGN_BOTTOM, timespan))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, width-150-4, 3, 150, 23, 1, RT_HALIGN_RIGHT|RT_VALIGN_BOTTOM, timespan))

		if timer.hasTimeframe():
			begin = strftime("%a, %d %b", localtime(timer.getTimeframeBegin()))
			end = strftime("%a, %d %b", localtime(timer.getTimeframeEnd()))
			timespan = (("%s ... %s") % (begin, end))
			if screenwidth and screenwidth == 1920:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 3, 39, float(width)/10*4.5-5, 35, 3, RT_HALIGN_LEFT|RT_VALIGN_BOTTOM, timespan))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, 3, 26, float(width)/10*4.5-5, 23, 1, RT_HALIGN_LEFT|RT_VALIGN_BOTTOM, timespan))

		if icon:
			if screenwidth and screenwidth == 1920:
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 3, 0, 36, 38, icon))
			else:
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 2, 0, 24, 25, icon))
			if screenwidth and screenwidth == 1920:
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 42, 5, 30, 30, rectypeicon))
			else:
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 28, 3, 20, 20, rectypeicon))
		try:
			devide = LoadPixmap(resolveFilename(SCOPE_ACTIVE_SKIN, "div-h.png"))
		except:
			devide = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/div-h.png"))
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 0, height-2, width, 2, devide))
		return res

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

