from os import path

# -*- coding: UTF-8 -*-
# for localized messages
from . import _

# GUI (Components)
from skin import parseFont
try:
	 from skin import parameters
	 skinparms = True
except:
	 skinparms = False
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
try:
	from Tools.TextBoundary import getTextBoundarySize
	TextBoundary = True
except:
	TextBoundary = False

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
		try:
			png = resolveFilename(SCOPE_ACTIVE_SKIN, "icons/lock_off.png")
		except:
			png = resolveFilename(SCOPE_CURRENT_SKIN, "skin-default/icons/lock_off.png")
		self.iconDisabled = LoadPixmap(cached=True, path=png)
		#currently intended that all icons have the same size
		try:
			png = resolveFilename(SCOPE_ACTIVE_SKIN, "icons/lock_on.png")
		except:
			png = resolveFilename(SCOPE_CURRENT_SKIN, "skin-default/icons/lock_on.png")
		self.iconEnabled = LoadPixmap(cached=True, path=png)
		try:
			png = resolveFilename(SCOPE_ACTIVE_SKIN, "icons/timer_rec.png")
		except:
			png = resolveFilename(SCOPE_CURRENT_SKIN, "skin-default/icons/timer_rec.png")
		self.iconRecording = LoadPixmap(cached=True, path=png)
		try:
			png = resolveFilename(SCOPE_ACTIVE_SKIN, "icons/timer_zap.png")
		except:
			png = resolveFilename(SCOPE_CURRENT_SKIN, "skin-default/icons/timer_zap.png")
		self.iconZapped = LoadPixmap(cached=True, path=png)

		self.serviceNameFont = gFont("Regular", 20)
		self.eventNameFont = gFont("Regular", 18)
		self.itemHeight = 75
		self.rowHeight = 24
		self.rowSplit1 = 26
		self.rowSplit2 = 47
		self.statusIconWidth = self.iconEnabled.size().width()
		self.statusIconHeight = self.iconEnabled.size().height()
		self.typeIconWidth = self.iconRecording.size().width()
		self.typeIconHeight = self.iconRecording.size().height()
		print 'iconWidth:',self.statusIconWidth
		print 'iconHeight:',self.statusIconHeight
		self.iconMargin = 2

	def applySkin(self, desktop, parent):
		def itemHeight(value):
			self.itemHeight = int(value)
		def ServiceNameFont(value):
			self.serviceNameFont = parseFont(value, ((1,1),(1,1)))
		def EventNameFont(value):
			self.eventNameFont = parseFont(value, ((1,1),(1,1)))
		def rowHeight(value):
			self.rowHeight = int(value)
		def rowSplit1(value):
			self.rowSplit1 = int(value)
		def rowSplit2(value):
			self.rowSplit2 = int(value)
		def iconMargin(value):
			self.iconMargin = int(value)
		for (attrib, value) in list(self.skinAttributes):
			try:
				locals().get(attrib)(value)
				self.skinAttributes.remove((attrib, value))
			except:
				pass
		self.l.setItemHeight(self.itemHeight)
		self.l.setFont(0, self.serviceNameFont)
		self.l.setFont(1, self.eventNameFont)
		return MenuList.applySkin(self, desktop, parent)

	def buildListboxEntry(self, timer):
		if not timer.enabled:
			icon = self.iconDisabled
		else:
			icon = self.iconEnabled
		if timer.justplay:
			rectypeicon = self.iconZapped
		else:
			rectypeicon = self.iconRecording

		height = self.l.getItemSize().height()
		width = self.l.getItemSize().width()
		iconMargin = self.iconMargin
		statusIconHeight = self.statusIconHeight
		statusIconWidth = self.statusIconWidth
		typeIconHeight = self.typeIconHeight
		typeIconWidth = self.typeIconWidth
		rowHeight = self.rowHeight
		rowSplit1 = self.rowSplit1
		rowSplit2 = self.rowSplit2
		channel = []
		for t in timer.services:
			channel.append(ServiceReference(t).getServiceName())
		if len(channel) >0 :
			channel = ", ".join(channel)
		else:
			channel = _('All channels')

		res = [ None ]
		if icon:
			if skinparms:
				x, y, w, h = parameters.get("AutotimerEnabledIcon",(iconMargin, 0, statusIconHeight, statusIconWidth))
			else:
				x, y, w, h = (iconMargin, 0, statusIconHeight, statusIconWidth)
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, x, y, w, h, icon))
		if rectypeicon:
			if skinparms:
				x, y, w, h = parameters.get("AutotimerRecordIcon",(iconMargin+statusIconWidth+iconMargin, 3, statusIconHeight, typeIconWidth))
			else:
				x, y, w, h = (iconMargin+statusIconWidth+iconMargin, 3, statusIconHeight, typeIconWidth)
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, x, y, w, h, rectypeicon))

		if timer.hasTimespan():
			nowt = time()
			now = localtime(nowt)
			begintime = int(mktime((now.tm_year, now.tm_mon, now.tm_mday, timer.timespan[0][0], timer.timespan[0][1], 0, now.tm_wday, now.tm_yday, now.tm_isdst)))
			endtime = int(mktime((now.tm_year, now.tm_mon, now.tm_mday, timer.timespan[1][0], timer.timespan[1][1], 0, now.tm_wday, now.tm_yday, now.tm_isdst)))
			timespan = (("  %s ... %s") % (FuzzyTime(begintime)[1], FuzzyTime(endtime)[1]))
		else:
			timespan = _("  Any time")
		res.append((eListboxPythonMultiContent.TYPE_TEXT, float(width)/10*4.5, 0, width-float(width)/10*4.5-5, rowHeight, 1, RT_HALIGN_RIGHT|RT_VALIGN_TOP, timespan))

		if TextBoundary:
			timespanWidth = getTextBoundarySize(self.instance, self.eventNameFont, self.l.getItemSize(), timespan).width()
		else:
			timespanWidth = float(width)/10*2
		res.append((eListboxPythonMultiContent.TYPE_TEXT, iconMargin+statusIconWidth+iconMargin+typeIconWidth+iconMargin, 2, width-(iconMargin+statusIconWidth+iconMargin+typeIconWidth+iconMargin)- timespanWidth, rowHeight, 0, RT_HALIGN_LEFT|RT_VALIGN_TOP, timer.name))

		if timer.hasTimeframe():
			begin = strftime("%a, %d %b", localtime(timer.getTimeframeBegin()))
			end = strftime("%a, %d %b", localtime(timer.getTimeframeEnd()))
			timeframe = (("%s ... %s") % (begin, end))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, iconMargin, rowSplit1, float(width)/10*4.5-5, rowHeight, 1, RT_HALIGN_LEFT|RT_VALIGN_TOP, timeframe))

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
		res.append((eListboxPythonMultiContent.TYPE_TEXT, float(width)/10*4.5+1, rowSplit1, float(width)/10*5.5-5, rowSplit1, 1, RT_HALIGN_RIGHT|RT_VALIGN_TOP, days))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, iconMargin, rowSplit2, width-(iconMargin*2), rowHeight, 1, RT_HALIGN_LEFT|RT_VALIGN_TOP, channel))
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

