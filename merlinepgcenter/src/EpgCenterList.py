#
#  MerlinEPGCenter E2 Plugin
#
#  $Id: EpgCenterList.py,v 1.0 2011-02-14 21:53:00 shaderman Exp $
#
#  Coded by Shaderman (c) 2011
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons
#  Attribution-NonCommercial-ShareAlike 3.0 Unported
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially
#  distributed other than under the conditions noted above.
#


# for localized messages
from . import _

# PYTHON IMPORTS
from datetime import datetime
from time import localtime, strftime, time

# ENIGMA IMPORTS
from Components.config import config
from Components.GUIComponent import GUIComponent
from Components.TimerList import TimerList
from enigma import eEPGCache, eServiceReference, eServiceCenter, eListbox, eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_HALIGN_CENTER, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, RT_VALIGN_TOP, RT_VALIGN_BOTTOM, getDesktop
from math import fabs
import NavigationInstance
from RecordTimer import RecordTimerEntry
from ServiceReference import ServiceReference
from skin import parseColor
from timer import TimerEntry
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN
from Tools.LoadPixmap import LoadPixmap

# OWN IMPORTS
from ConfigTabs import KEEP_OUTDATED_TIME, STYLE_SIMPLE_BAR, STYLE_PIXMAP_BAR, STYLE_MULTI_PIXMAP, STYLE_PERCENT_TEXT, STYLE_SIMPLE_BAR_LIST_OFF, STYLE_PIXMAP_BAR_LIST_OFF, STYLE_MULTI_PIXMAP_LIST_OFF, STYLE_PERCENT_TEXT_LIST_OFF
from HelperFunctions import getFuzzyDay, LIST_TYPE_EPG, LIST_TYPE_UPCOMING, TimerListObject
from MerlinEPGCenter import STYLE_SINGLE_LINE, STYLE_SHORT_DESCRIPTION


MODE_HD = 0
MODE_XD = 1
MODE_SD = 2

MULTI_EPG_NOW = 0
MULTI_EPG_NEXT = 1
SINGLE_EPG = 2
MULTI_EPG_PRIMETIME = 3
TIMERLIST = 4
EPGSEARCH_HISTORY = 5
EPGSEARCH_RESULT = 6
EPGSEARCH_MANUAL = 7
UPCOMING = 8

TIMER_TYPE_EID_MATCH = 1
TIMER_TYPE_COVERS_FULL = 2
TIMER_TYPE_COVERS_END = 4
TIMER_TYPE_COVERS_BEGIN = 8
TIMER_TYPE_EID_REPEATED = 16
TIMER_TYPE_INSIDE_EVENT = 32
TIMER_TYPE_ADD = 64
TIMER_TYPE_ADD_INSIDE_EVENT = 128
TIMER_TYPE_ADD_COVERS_FULL = 256
TIMER_TYPE_ADD_COVERS_END = 512
TIMER_TYPE_ADD_COVERS_BEGIN = 1024


class EpgCenterList(GUIComponent):
	# some static stuff used by ["list"] and ["upcoming"] widgets
	infoBarInstance = None
	eServiceCenterInstance = None
	bouquetList = []
	bouquetServices = []
	currentBouquetIndex = 0
	bouquetIndexRanges = []
	allServicesNameDict = {}
	recordTimer = None
	lenChannelDigits = 0

	def __init__(self, blinkTimer, listType, videoMode, piconLoader, bouquetList, currentIndex, piconSize, listStyle, epgList):
		self.blinkTimer = blinkTimer
		self.listType = listType
		self.videoMode = videoMode
		self.piconLoader = piconLoader
		self.piconSize = piconSize
		self.baseHeight = self.piconSize.height()
		self.listStyle = listStyle
		self.epgList = epgList

		GUIComponent.__init__(self)

		from Screens.InfoBar import InfoBar
		EpgCenterList.infoBarInstance = InfoBar.instance
		EpgCenterList.eServiceCenterInstance = eServiceCenter.getInstance()

		self.l = eListboxPythonMultiContent()
		self.l.setBuildFunc(self.buildEpgEntry)
		self.onSelectionChanged = []

		if self.videoMode == MODE_SD or self.videoMode == MODE_XD:
			self.overallFontHeight = 36
		elif self.videoMode == MODE_HD:
			self.overallFontHeight = 44

		#initialize
		self.list = []
		self.mode = None
		self.similarShown = False

		config.plugins.merlinEpgCenter.listItemHeight.addNotifier(self.changeHeight, initial_call=True)
		config.plugins.merlinEpgCenter.adjustFontSize.addNotifier(self.setFontSizes, initial_call=True)

		if listType == LIST_TYPE_EPG:
			EpgCenterList.bouquetList = bouquetList
			EpgCenterList.currentBouquetIndex = currentIndex
			EpgCenterList.updateBouquetServices()
			EpgCenterList.recordTimer = NavigationInstance.instance.RecordTimer

		# zap timer pixmaps
		self.zap_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/zap.png"))
		self.zap_pre_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/zap_pre.png"))
		self.zap_post_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/zap_post.png"))
		self.zap_event_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/zap_event.png"))
		self.zap_repeated_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/zap_repeated.png"))
		self.zap_add_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/zap_add.png"))

		# record timer pixmaps
		self.timer_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/timer.png"))
		self.timer_pre_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/timer_pre.png"))
		self.timer_post_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/timer_post.png"))
		self.timer_event_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/timer_event.png"))
		self.timer_repeated_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/timer_repeated.png"))
		self.timer_add_pixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/timer_add.png"))

		# progress pixmaps
		self.progressPixmap = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/Progress.png"))
		self.progressPixmap_0 = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/Progress_0.png"))
		self.progressPixmap_1 = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/Progress_1.png"))
		self.progressPixmap_2 = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/Progress_2.png"))
		self.progressPixmap_3 = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/Progress_3.png"))
		self.progressPixmap_4 = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/Progress_4.png"))
		self.progressPixmapWidth = self.progressPixmap.size().width()

		self.epgcache = eEPGCache.getInstance()

		self.blinkTimer.callbacks.append(self.invalidateList)

	def onShow(self):
		self.maxWidth = self.l.getItemSize().width()

	def setFontSizes(self, configElement=None):
		diff = configElement.getValue()

		if self.videoMode == MODE_SD:
			self.l.setFont(0, gFont("Regular", 18 + diff))
			self.l.setFont(1, gFont("Regular", 16 + diff))
			self.l.setFont(2, gFont("Regular", 14 + diff))
			self.l.setFont(3, gFont("Regular", 12 + diff))
		elif self.videoMode == MODE_XD:
			self.l.setFont(0, gFont("Regular", 18 + diff))
			self.l.setFont(1, gFont("Regular", 16 + diff))
			self.l.setFont(2, gFont("Regular", 14 + diff))
			self.l.setFont(3, gFont("Regular", 12 + diff))
		elif self.videoMode == MODE_HD:
			self.l.setFont(0, gFont("Regular", 22 + diff))
			self.l.setFont(1, gFont("Regular", 20 + diff))
			self.l.setFont(2, gFont("Regular", 18 + diff))
			self.l.setFont(3, gFont("Regular", 16 + diff))

	def setMaxWidth(self, newSize):
		self.maxWidth = newSize.width()

	def changeHeight(self, configElement=None):
		self.listStyle = config.plugins.merlinEpgCenter.listStyle.value
		if self.listStyle == STYLE_SINGLE_LINE:
			self.singleLineBorder = 2
		else:
			self.singleLineBorder = 0

		if self.listStyle == STYLE_SHORT_DESCRIPTION or (self.listStyle == STYLE_SINGLE_LINE and (self.mode == SINGLE_EPG or self.mode == EPGSEARCH_RESULT or self.similarShown)):
			if self.overallFontHeight > self.baseHeight:
				self.itemHeight = self.overallFontHeight + int(config.plugins.merlinEpgCenter.listItemHeight.value)
			else:
				self.itemHeight = self.baseHeight + int(config.plugins.merlinEpgCenter.listItemHeight.value)
		elif self.videoMode == MODE_HD and config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_PERCENT_TEXT: # HD skin adjustment for text size
			self.itemHeight = self.baseHeight + int(config.plugins.merlinEpgCenter.listItemHeight.value) + 4
		else:
			self.itemHeight = self.baseHeight + int(config.plugins.merlinEpgCenter.listItemHeight.value)
		self.halfItemHeight = self.itemHeight / 2
		self.l.setItemHeight(self.itemHeight)

	def buildEpgEntry(self, ignoreMe, eventid, sRef, begin, duration, title, short, desc):
		columnSpace = config.plugins.merlinEpgCenter.columnSpace.getValue()
		progressPixmap = None
		offsetLeft = 5
		offsetRight = self.maxWidth - 5 - 8 # 8 = timer pixmap width, 5 = border
		secondLineColor = 0x00909090 # grey
		border = int(config.plugins.merlinEpgCenter.listItemHeight.value) / 2
		percent = 0

		if begin != None and duration != None:
			timeString = strftime("%H:%M", localtime(begin)) + "-" + strftime("%H:%M", localtime(begin + duration))
			now = int(time())
			if now > begin:
				percent = (now - begin) * 100 / duration

			if self.mode == MULTI_EPG_NOW:
				timeValue = (begin + duration - now) / 60 + 1
			elif self.mode == MULTI_EPG_NEXT or self.mode == UPCOMING:
				timeValue = (now - begin) / 60
			elif self.mode == MULTI_EPG_PRIMETIME or self.mode == EPGSEARCH_RESULT:
				if now >= begin:
					timeValue = (begin + duration - now) / 60 + 1
				else:
					timeValue = (now - begin) / 60
			elif self.mode == SINGLE_EPG:
				if self.instance.getCurrentIndex() == 0:
					timeValue = (begin + duration - now) / 60 + 1
				else:
					timeValue = (now - begin) / 60

			if config.plugins.merlinEpgCenter.showBeginRemainTime.value:
				if (KEEP_OUTDATED_TIME == 0 and (begin + duration) > now) or (KEEP_OUTDATED_TIME != 0 and (begin + duration) > now):
					if config.plugins.merlinEpgCenter.showDuration.value:
						remainBeginString = " I "
					else:
						remainBeginString = ""

					if timeValue >= 0:
						remainBeginString += "+"
					if fabs(timeValue) >= 120 and fabs(timeValue) < 1440:
						timeValue /= 60
						remainBeginString += "%0dh" % timeValue
					elif fabs(timeValue) >= 1440:
						timeValue = (timeValue / 1440) + 1
						remainBeginString += "%02dd" % timeValue
					else:
						if timeValue < 0:
							remainBeginString += "%03d" % timeValue
						else:
							remainBeginString += "%02d" % timeValue
				else:
					if config.plugins.merlinEpgCenter.showDuration.value:
						remainBeginString = " I <->"
					else:
						remainBeginString = "<->"
			else:
				remainBeginString = ""

			if config.plugins.merlinEpgCenter.showDuration.value:
				duraString = "%d" % (duration / 60)

			if self.mode == MULTI_EPG_NOW:
				if config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_MULTI_PIXMAP:
					part = int(round(percent / 25)) + 1
					progressPixmap = eval('self.progressPixmap_' + str(part))
				elif config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_PIXMAP_BAR:
					progressPixmap = self.progressPixmap
		else:
			timeString = ""
			duraString = ""
			remainBeginString = ""

		if remainBeginString.endswith('>'): # KEEP_OUTDATED_TIME
			outdated = True
			try:
				progColor = parseColor("eventNotAvailable").argb()
			except:
				progColor = 0x777777
		elif config.plugins.merlinEpgCenter.showBeginRemainTime.value and config.plugins.merlinEpgCenter.showColoredEpgTimes.value:
			outdated = False
			if remainBeginString.endswith('h'): # begins in... hours
				progColor = 0x00ef7f1a # brown
			elif remainBeginString.endswith('d'): # begins in... days
				progColor = 0x00e31e24 # red
			elif remainBeginString.startswith(' I +') or remainBeginString.startswith('+'): # already running
				progColor = 0x0074de0a # green
			elif remainBeginString.startswith(' I -') or remainBeginString.startswith('-'): # begins in... minutes
				progColor = 0x00ffed00 # yellow
			else: # undefined, shouldn't happen
				progColor = 0x00ffffff # white
		else:
			outdated = False
			progColor = 0x00ffed00 # yellow

		if outdated:
			textColor = progColor
		elif self.epgList != None:
			textColor = self.epgList.getColorEventAvailable(sRef, begin, duration)
		else:
			textColor = None

		res = [None]

		if config.plugins.merlinEpgCenter.showListNumbers.value:
			if ((self.mode == SINGLE_EPG and not self.similarShown) or self.mode == UPCOMING) and self.instance.getCurrentIndex() != 0:
				chNumber = ""
			else:
				# check if the service is found in our bouquets (or don't show the channel number if not found)
				if self.mode == EPGSEARCH_RESULT:
					if sRef in EpgCenterList.allServicesNameDict:
						i = 0
						while i < len(EpgCenterList.bouquetServices):
							if sRef in EpgCenterList.bouquetServices[i]:
								chOffset = EpgCenterList.bouquetIndexRanges[i]
								chNumber = str(EpgCenterList.bouquetServices[i].index(sRef) + chOffset)
								break
							i += 1
					else:
						chNumber = ""
				else:
					if sRef in EpgCenterList.bouquetServices[EpgCenterList.currentBouquetIndex]:
						chOffset = EpgCenterList.bouquetIndexRanges[EpgCenterList.currentBouquetIndex]
						chNumber = str(EpgCenterList.bouquetServices[EpgCenterList.currentBouquetIndex].index(sRef) + chOffset)
					else:
						chNumber = ""

			if EpgCenterList.lenChannelDigits < 3:
				width = self.maxWidth * 3 / 100
			else:
				width = self.maxWidth * 4 / 100
			res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, 0, width, self.itemHeight, 1, RT_HALIGN_RIGHT | RT_VALIGN_CENTER, chNumber))
			offsetLeft = offsetLeft + width + columnSpace

		if config.plugins.merlinEpgCenter.showPicons.value:
			if ((self.mode == SINGLE_EPG and not self.similarShown) or self.mode == UPCOMING) and self.instance.getCurrentIndex() != 0:
				picon = None
			else:
				picon = self.piconLoader.getPicon(sRef)

			width = self.piconSize.width()
			if picon:
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetLeft, (self.itemHeight - self.baseHeight) / 2, width, self.itemHeight, picon))
			offsetLeft = offsetLeft + width + columnSpace

		if config.plugins.merlinEpgCenter.showServiceName.value:
			extraWidth = int(config.plugins.merlinEpgCenter.serviceNameWidth.value)
			if self.videoMode == MODE_SD:
				width = self.maxWidth * (12 + extraWidth) / 100
			elif self.videoMode == MODE_XD:
				width = self.maxWidth * (14 + extraWidth) / 100
			elif self.videoMode == MODE_HD:
				width = self.maxWidth * (16 + extraWidth) / 100

			if not (((self.mode == SINGLE_EPG and not self.similarShown) or self.mode == UPCOMING) and self.instance.getCurrentIndex() != 0):
				if sRef in EpgCenterList.allServicesNameDict:
					serviceName = EpgCenterList.allServicesNameDict[sRef]
				else:
					serviceName = ServiceReference(sRef).getServiceName()

				res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, 0, width, self.itemHeight, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, serviceName))
			offsetLeft = offsetLeft + width + columnSpace

		if self.mode == MULTI_EPG_NOW and not self.similarShown:
			extraWidth = int(config.plugins.merlinEpgCenter.adjustFontSize.value)
			if extraWidth < 0:
				extraWidth = 0
			if self.videoMode == MODE_SD:
				width = self.maxWidth * (18 + extraWidth) / 100
			else:
				width = self.maxWidth * (14 + extraWidth) / 100
			progressHeight = 6

			if config.plugins.merlinEpgCenter.listProgressStyle.value < STYLE_SIMPLE_BAR_LIST_OFF: # show progress in lists
				res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, border, width, self.halfItemHeight - border + (self.singleLineBorder * 2), 1, RT_HALIGN_CENTER | RT_VALIGN_TOP, timeString))
			else: # don't show progress in lists
				res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, 0, width, self.itemHeight, 1, RT_HALIGN_CENTER | RT_VALIGN_CENTER, timeString))

			if config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_MULTI_PIXMAP and progressPixmap is not None:
				if width > self.progressPixmapWidth:
					progressOffset = int((width - self.progressPixmapWidth) / 2)
				else:
					progressOffset = 0
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetLeft + progressOffset, self.halfItemHeight + (self.halfItemHeight - progressHeight) / 2 + self.singleLineBorder, width, progressHeight, progressPixmap))
			elif config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_SIMPLE_BAR:
				res.append((eListboxPythonMultiContent.TYPE_PROGRESS, offsetLeft, self.halfItemHeight + (self.halfItemHeight - progressHeight) / 2 + self.singleLineBorder, width, progressHeight, percent, 1, secondLineColor))
			elif config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_PIXMAP_BAR and progressPixmap is not None:
				if width > self.progressPixmapWidth:
					progressOffset = int((width - self.progressPixmapWidth) / 2)
				else:
					progressOffset = 0
				res.append((eListboxPythonMultiContent.TYPE_PROGRESS_PIXMAP, offsetLeft + progressOffset, self.halfItemHeight + (self.halfItemHeight - progressHeight) / 2 + self.singleLineBorder, width, progressHeight, percent, progressPixmap, 0))
			elif config.plugins.merlinEpgCenter.listProgressStyle.value == STYLE_PERCENT_TEXT:
				if self.videoMode == MODE_SD: # we need a bigger font for SD skins
					font = 2
				else:
					font = 3
				res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, self.halfItemHeight, width, self.halfItemHeight - border, font, RT_HALIGN_CENTER | RT_VALIGN_TOP, str(percent) + "%", secondLineColor))

			offsetLeft = offsetLeft + width + columnSpace
		else:
			extraWidth = int(config.plugins.merlinEpgCenter.adjustFontSize.value)
			if extraWidth < 0:
				extraWidth = 0
			if self.videoMode == MODE_SD:
				width = self.maxWidth * (18 + extraWidth) / 100
			else:
				width = self.maxWidth * (14 + extraWidth) / 100
			if self.mode == SINGLE_EPG or self.mode == EPGSEARCH_RESULT or self.similarShown:
				fd = getFuzzyDay(begin)
				res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, border, width, self.halfItemHeight - border, 1, RT_HALIGN_CENTER | RT_VALIGN_TOP, timeString, textColor))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, self.halfItemHeight, width, self.halfItemHeight - border, 2, RT_HALIGN_CENTER | RT_VALIGN_TOP, fd, secondLineColor))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, 0, width, self.itemHeight, 1, RT_HALIGN_CENTER | RT_VALIGN_CENTER, timeString, textColor))
			offsetLeft = offsetLeft + width + columnSpace

		if begin != None and duration != None:
			(timerPixmaps, zapPixmaps, isRunning) = self.getTimerPixmapsForEntry(sRef, eventid, begin, duration)
		else:
			timerPixmaps = 0
			zapPixmaps = 0
			isRunning = 0

		idx = self.instance.getCurrentIndex()
		self.blinkTimer.updateEntry(self.listType, idx, isRunning)

		if zapPixmaps:
			if (zapPixmaps & TIMER_TYPE_EID_MATCH) or (zapPixmaps & TIMER_TYPE_COVERS_FULL) or (zapPixmaps & TIMER_TYPE_EID_REPEATED) or (zapPixmaps & TIMER_TYPE_ADD_COVERS_FULL):
				posY = 2
				height = self.itemHeight - 4
				if (zapPixmaps & TIMER_TYPE_EID_MATCH):
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.zap_event_pixmap))
				elif (zapPixmaps & TIMER_TYPE_COVERS_FULL):
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.zap_pixmap))
				elif (zapPixmaps & TIMER_TYPE_EID_REPEATED):
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.zap_repeated_pixmap))
				elif (zapPixmaps & TIMER_TYPE_ADD_COVERS_FULL):
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.zap_add_pixmap))
			elif (zapPixmaps & TIMER_TYPE_INSIDE_EVENT) or (zapPixmaps & TIMER_TYPE_ADD_INSIDE_EVENT):
				posY = self.itemHeight / 2 - 6
				height = 12
				if (zapPixmaps & TIMER_TYPE_INSIDE_EVENT):
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.zap_pixmap))
				elif (zapPixmaps & TIMER_TYPE_ADD_INSIDE_EVENT):
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.zap_add_pixmap))
			else:
				if zapPixmaps & TIMER_TYPE_COVERS_END:
					posY = self.itemHeight / 2 + 2
					height = self.itemHeight - posY - 2
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.zap_pre_pixmap))
				elif zapPixmaps & TIMER_TYPE_ADD_COVERS_END:
					posY = self.itemHeight / 2 + 2
					height = self.itemHeight - posY - 2
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.zap_add_pixmap))
				if zapPixmaps & TIMER_TYPE_COVERS_BEGIN:
					posY = 2
					height = self.itemHeight / 2 - 2
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.zap_post_pixmap))
				elif zapPixmaps & TIMER_TYPE_ADD_COVERS_BEGIN:
					posY = 2
					height = self.itemHeight / 2 - 2
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.zap_add_pixmap))
				if zapPixmaps & TIMER_TYPE_ADD:
					posY = 2
					height = self.itemHeight - 4
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.zap_add_pixmap))

		offsetRight -= 10

		if timerPixmaps:
			if (timerPixmaps & TIMER_TYPE_EID_MATCH) or (timerPixmaps & TIMER_TYPE_COVERS_FULL) or (timerPixmaps & TIMER_TYPE_EID_REPEATED) or (timerPixmaps & TIMER_TYPE_ADD_COVERS_FULL):
				posY = 2
				height = self.itemHeight - 4
				if (timerPixmaps & TIMER_TYPE_EID_MATCH):
					if (isRunning & TIMER_TYPE_EID_MATCH) and not self.blinkTimer.getBlinkState():
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, None))
					else:
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.timer_event_pixmap))
				elif (timerPixmaps & TIMER_TYPE_COVERS_FULL):
					if (isRunning & TIMER_TYPE_COVERS_FULL) and not self.blinkTimer.getBlinkState():
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, None))
					else:
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.timer_pixmap))
				elif (timerPixmaps & TIMER_TYPE_EID_REPEATED):
					if (isRunning & TIMER_TYPE_EID_REPEATED) and not self.blinkTimer.getBlinkState():
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, None))
					else:
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.timer_repeated_pixmap))
				elif (timerPixmaps & TIMER_TYPE_ADD_COVERS_FULL):
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.timer_add_pixmap))
			elif (timerPixmaps & TIMER_TYPE_INSIDE_EVENT) or (timerPixmaps & TIMER_TYPE_ADD_INSIDE_EVENT):
				posY = self.itemHeight / 2 - 6
				height = 12
				if (timerPixmaps & TIMER_TYPE_INSIDE_EVENT):
					if (isRunning & TIMER_TYPE_INSIDE_EVENT) and not self.blinkTimer.getBlinkState():
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, None))
					else:
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.timer_pixmap))
				elif (timerPixmaps & TIMER_TYPE_ADD_INSIDE_EVENT):
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.timer_add_pixmap))
			else:
				if timerPixmaps & TIMER_TYPE_COVERS_END:
					posY = self.itemHeight / 2 + 2
					height = self.itemHeight - posY - 2
					if (isRunning & TIMER_TYPE_COVERS_END) and not self.blinkTimer.getBlinkState():
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, None))
					else:
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.timer_pre_pixmap))
				elif timerPixmaps & TIMER_TYPE_ADD_COVERS_END:
					posY = self.itemHeight / 2 + 2
					height = self.itemHeight - posY - 2
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.timer_add_pixmap))
				if timerPixmaps & TIMER_TYPE_COVERS_BEGIN:
					posY = 2
					height = self.itemHeight / 2 - 2
					if (isRunning & TIMER_TYPE_COVERS_BEGIN) and not self.blinkTimer.getBlinkState():
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, None))
					else:
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.timer_post_pixmap))
				elif timerPixmaps & TIMER_TYPE_ADD_COVERS_BEGIN:
					posY = 2
					height = self.itemHeight / 2 - 2
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.timer_add_pixmap))
				if timerPixmaps & TIMER_TYPE_ADD:
					posY = 2
					height = self.itemHeight - 4
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetRight, posY, 8, height, self.timer_add_pixmap))

		if config.plugins.merlinEpgCenter.showBeginRemainTime.value and config.plugins.merlinEpgCenter.showDuration.value:
			width = self.maxWidth * 8 / 100
			offsetRight = offsetRight - width
			res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetRight, 0, width, self.itemHeight, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, remainBeginString, progColor))
		elif config.plugins.merlinEpgCenter.showBeginRemainTime.value:
			width = self.maxWidth * 6 / 100
			offsetRight = offsetRight - width
			res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetRight, 0, width, self.itemHeight, 1, RT_HALIGN_RIGHT | RT_VALIGN_CENTER, remainBeginString, progColor))

		if config.plugins.merlinEpgCenter.showDuration.value:
			width = self.maxWidth * 6 / 100
			offsetRight = offsetRight - width
		elif not config.plugins.merlinEpgCenter.showDuration.value and not config.plugins.merlinEpgCenter.showBeginRemainTime.value:
			width = self.maxWidth * 1 / 100
			offsetRight = offsetRight - width

		titleWidth = offsetRight - offsetLeft - columnSpace
		if self.listStyle == STYLE_SINGLE_LINE:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, 0, titleWidth, self.itemHeight, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, title, config.plugins.merlinEpgCenter.titleColor.value, config.plugins.merlinEpgCenter.titleColorSelected.value))
		elif self.listStyle == STYLE_SHORT_DESCRIPTION:
			if short and title != short:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, border, titleWidth, self.halfItemHeight - border, 1, RT_HALIGN_LEFT | RT_VALIGN_TOP, title, textColor))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, self.halfItemHeight, titleWidth, self.halfItemHeight - border, 2, RT_HALIGN_LEFT | RT_VALIGN_TOP, short, secondLineColor))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, 0, titleWidth, self.itemHeight, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, title, textColor))

		if config.plugins.merlinEpgCenter.showDuration.value:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetRight, 0, width, self.itemHeight, 1, RT_HALIGN_RIGHT | RT_VALIGN_CENTER, duraString, textColor))

		return res

	GUI_WIDGET = eListbox

	def selectionChanged(self):
		for x in self.onSelectionChanged:
			x()

	def postWidgetCreate(self, instance):
		instance.setWrapAround(True)
		instance.setContent(self.l)
		instance.selectionChanged.get().append(self.selectionChanged)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		instance.selectionChanged.get().remove(self.selectionChanged)
		config.plugins.merlinEpgCenter.listItemHeight.removeNotifier(self.changeHeight)
		config.plugins.merlinEpgCenter.adjustFontSize.removeNotifier(self.setFontSizes)
		self.blinkTimer.callbacks.remove(self.invalidateList)

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)

	def moveUp(self):
		self.instance.moveSelection(self.instance.moveUp)

	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)

	def pageUp(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.pageUp)

	def pageDown(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.pageDown)

	def getCurrent(self):
		return self.l.getCurrentSelection()

	def invalidate(self, entry):
		# when the entry to invalidate does not exist, just ignore the request.
		# this eases up conditional setup screens a lot.
		if entry in self.list:
			self.l.invalidateEntry(self.list.index(entry))

	def invalidateList(self):
		self.l.invalidate()

	def setList(self, l):
		self.list = l
		self.l.setList(self.list)

	def queryEPG(self, servicelist):
		if self.epgcache is not None:
			return self.epgcache.lookupEvent(servicelist)
		return []

	def fillMultiEPG(self, bouquet, bouquetIndex, mode, stime=-1):
		EpgCenterList.currentBouquetIndex = bouquetIndex

		# 1. if oldmode is MULTI_EPG_NOW and new mode is MULTI_EPG_NEXT --> use old list for querying EPG (speed up! :-) )
		# 2. otherwise build servicelist from bouquet, and
		#	a) if MULTI_EPG_NOW/MULTI_EPG_PRIMETIME --> query epg
		#	b) if MULTI_EPG_NEXT --> build query-list with servicelist for epg
		oldmode = self.mode
		self.mode = mode
		self.similarShown = False

		if ((mode == MULTI_EPG_NOW or mode == MULTI_EPG_PRIMETIME) or (oldmode != MULTI_EPG_NOW and mode == MULTI_EPG_NEXT)):
			servicelist = EpgCenterList.getServiceList(bouquet, stime)

		returnTuples = '0IRBDTSEX'
		if mode == MULTI_EPG_NOW or mode == MULTI_EPG_PRIMETIME:
			servicelist.insert(0, returnTuples)
		else:
			if oldmode != MULTI_EPG_NOW:
				servicelist.insert(0, returnTuples)
				tmpList = self.queryEPG(servicelist)
			else:
				tmpList = self.list

			servicelist = [x[3] and (x[2], 1, x[3]) or (x[2], 1, 0) for x in tmpList] # build servicelist with "event after given start_time" and set the start time
			servicelist.insert(0, returnTuples)

		if self.listStyle == STYLE_SINGLE_LINE:
			self.changeHeight()
		self.list = self.queryEPG(servicelist)
		self.l.setList(self.list)

	def fillSingleEPG(self, bouquet, bouquetIndex, mode, sRef, showOutdated):
		self.mode = mode
		EpgCenterList.currentBouquetIndex = bouquetIndex
		EpgCenterList.getServiceList(bouquet)
		self.similarShown = False

		if sRef:
			if showOutdated:
				now = time()
				queryString = ['0IRBDTSE', (sRef, 0, now - KEEP_OUTDATED_TIME * 60, KEEP_OUTDATED_TIME)]
			else:
				queryString = ['0IRBDTSE', (sRef, 0, -1, -1)]
			self.list = self.queryEPG(queryString)

		if self.listStyle == STYLE_SINGLE_LINE:
			self.changeHeight()
		if showOutdated:
			self.list.sort(key=lambda x: x[3], reverse=True) # sort by time
		self.l.setList(self.list)

	def fillSimilar(self, sRef, eventId):
		if eventId is None:
			return

		self.similarShown = True
		self.list = self.epgcache.search(('0IRBDTSE', 1024, eEPGCache.SIMILAR_BROADCASTINGS_SEARCH, sRef, eventId))
		if self.list is not None:
			if config.plugins.merlinEpgCenter.limitSearchToBouquetServices.value:
				for item in self.list[:]:
					if not item[2] in EpgCenterList.allServicesNameDict:
						self.list.remove(item)

			if self.listStyle == STYLE_SINGLE_LINE:
				self.changeHeight()

			self.list.sort(key=lambda x: x[3]) # sort by time
			self.l.setList(self.list)

	def fillEpgSearch(self, searchString, mode):
		self.mode = mode
		self.similarShown = False

		if searchString == None:
			self.list = []
		else:
			searchString = searchString.decode('utf-8').encode("iso-8859-1", "replace")
			self.list = self.epgcache.search(('0IRBDTSE', 1024, eEPGCache.PARTIAL_TITLE_SEARCH, searchString, eEPGCache.NO_CASE_CHECK)) or []
			if config.plugins.merlinEpgCenter.limitSearchToBouquetServices.value:
				for item in self.list[:]:
					if not item[2] in EpgCenterList.allServicesNameDict:
						self.list.remove(item)
			self.list.sort(key=lambda x: x[3]) # sort by time

		if self.listStyle == STYLE_SINGLE_LINE:
			self.changeHeight()
		self.l.setList(self.list)

	@staticmethod
	def getServiceList(bouquet, stime=-1, sRefOnly=False):
		services = []
		servicelist = eServiceCenter.getInstance().list(bouquet)
		if not servicelist is None:
			while True:
				service = servicelist.getNext()
				if not service.valid(): # check if end of list
					break
				if service.flags & (eServiceReference.isDirectory | eServiceReference.isMarker): # ignore non playable services
					continue
				# alternative service?
				if service.flags & (eServiceReference.isGroup):
					altRoot = eServiceReference(service.toCompareString())
					altList = EpgCenterList.eServiceCenterInstance.list(altRoot)
					if altList:
						while True:
							nextService = altList.getNext()
							if not nextService.valid():
								break
							service = nextService
							break

				if sRefOnly:
					services.append(service.toCompareString())
				else:
					services.append((service.toCompareString(), 0, stime))
		return services

	# get a list of all services in all bouquets
	@staticmethod
	def getAllServices():
		allServices = {}
		index = 1
		EpgCenterList.lenChannelDigits = 0
		totalServices = 0 # the number of services in all bouquets
		for bouquetEntry in EpgCenterList.bouquetList:
			servicelist = eServiceCenter.getInstance().list(bouquetEntry[1])
			if not servicelist is None:
				numServices = 0
				while True:
					service = servicelist.getNext()
					if not service.valid(): # check if end of list
						break
					if service.flags & (eServiceReference.isDirectory | eServiceReference.isMarker): # ignore non playable services
						continue
					info = EpgCenterList.eServiceCenterInstance.info(service)
					serviceName = info.getName(service) or ServiceReference(service).getServiceName() or ""
					allServices[service.toCompareString()] = serviceName
					numServices += 1
				indexEntry = index
				index += numServices
				totalServices += numServices
				EpgCenterList.bouquetIndexRanges.append(indexEntry)
		EpgCenterList.lenChannelDigits = len(str(totalServices))
		return allServices

	@staticmethod
	def updateBouquetServices():
		EpgCenterList.bouquetIndexRanges = []
		EpgCenterList.allServicesNameDict = EpgCenterList.getAllServices()
		EpgCenterList.bouquetServices = []

		for bouquet in EpgCenterList.bouquetList:
			EpgCenterList.bouquetServices.append(EpgCenterList.getServiceList(bouquet[1], sRefOnly=True))

	def selectionEnabled(self, enabled):
		if self.instance is not None:
			self.instance.setSelectionEnable(enabled)

	def getTimerPixmapsForEntry(self, sRef, eventId, begin, duration):
		timerPixmaps = 0
		zapPixmaps = 0
		isRunning = 0

		for timer in self.recordTimer.timer_list:
			if timer.service_ref.ref.toString() == sRef:
				end = begin + duration
				if timer.begin > begin and timer.end < end: # the timer is inside the events bounds
					if timer.justplay:
						zapPixmaps |= TIMER_TYPE_INSIDE_EVENT
					else:
						timerPixmaps |= TIMER_TYPE_INSIDE_EVENT
						if timer.isRunning():
							isRunning |= TIMER_TYPE_INSIDE_EVENT
				elif end >= timer.begin and begin <= timer.end: # this event touches the timer
					if eventId == timer.eit: # exact event match
						if timer.repeated:
							if timer.justplay:
								zapPixmaps |= TIMER_TYPE_EID_REPEATED
							else:
								timerPixmaps |= TIMER_TYPE_EID_REPEATED
								if timer.isRunning():
									isRunning |= TIMER_TYPE_EID_REPEATED
						else:
							if timer.justplay:
								zapPixmaps |= TIMER_TYPE_EID_MATCH
							else:
								timerPixmaps |= TIMER_TYPE_EID_MATCH
								if timer.isRunning():
									isRunning |= TIMER_TYPE_EID_MATCH
					elif begin < timer.begin and end > timer.begin: # this event overlaps the end of the timer
						if timer.justplay:
							zapPixmaps |= TIMER_TYPE_COVERS_END
						else:
							timerPixmaps |= TIMER_TYPE_COVERS_END
							if timer.isRunning():
								isRunning |= TIMER_TYPE_COVERS_END
					elif end > timer.end and begin < timer.end: # this event overlaps the begin of the timer
						if timer.justplay:
							zapPixmaps |= TIMER_TYPE_COVERS_BEGIN
						else:
							timerPixmaps |= TIMER_TYPE_COVERS_BEGIN
							if timer.isRunning():
								isRunning |= TIMER_TYPE_COVERS_BEGIN
					elif end > timer.begin and begin < timer.end: # this event fully overlaps the timer but itsn't nor the timer event
						if timer.justplay:
							zapPixmaps |= TIMER_TYPE_COVERS_FULL
						else:
							timerPixmaps |= TIMER_TYPE_COVERS_FULL
							if timer.isRunning():
								isRunning |= TIMER_TYPE_COVERS_FULL
				elif timerPixmaps == 0 and zapPixmaps == 0 and self.recordTimer.isInTimer(eventId, begin, duration, sRef): # timer repetition
					# TODO do we need to care about local times?

					timerBegin = datetime.fromtimestamp(timer.begin).time()
					timerEnd = datetime.fromtimestamp(timer.end).time()
					netTimerBegin = datetime.fromtimestamp(int(timer.begin) + 60 * config.recording.margin_before.getValue()).time()
					netTimerEnd = datetime.fromtimestamp(int(timer.end) - 60 * config.recording.margin_after.getValue()).time()
					eventBegin = datetime.fromtimestamp(begin).time()
					eventEnd = datetime.fromtimestamp(end).time()

					if netTimerBegin == eventBegin and netTimerEnd == eventEnd: # the main timer entry
						if timer.justplay:
							zapPixmaps |= TIMER_TYPE_ADD
						else:
							timerPixmaps |= TIMER_TYPE_ADD
					elif netTimerBegin >= eventBegin and netTimerEnd <= eventEnd: # the timer is inside the events bounds
						if timer.justplay:
							zapPixmaps |= TIMER_TYPE_ADD_INSIDE_EVENT
						else:
							timerPixmaps |= TIMER_TYPE_ADD_INSIDE_EVENT
					elif eventBegin < timerBegin and eventEnd > timerBegin: # this event overlaps the end of the timer
						if timer.justplay:
							zapPixmaps |= TIMER_TYPE_ADD_COVERS_END
						else:
							timerPixmaps |= TIMER_TYPE_ADD_COVERS_END
					elif eventEnd > timerEnd and eventBegin < timerEnd: # this event overlaps the begin of the timer
						if timer.justplay:
							zapPixmaps |= TIMER_TYPE_ADD_COVERS_BEGIN
						else:
							timerPixmaps |= TIMER_TYPE_ADD_COVERS_BEGIN
					elif eventEnd > timerBegin and eventBegin < timerEnd: # this event fully overlaps the timer but itsn't nor the timer event
						if timer.justplay:
							zapPixmaps |= TIMER_TYPE_ADD_COVERS_FULL
						else:
							timerPixmaps |= TIMER_TYPE_ADD_COVERS_FULL

		return timerPixmaps, zapPixmaps, isRunning


class EpgCenterTimerlist(TimerList):
	def __init__(self, list, videoMode, piconLoader, piconSize, listStyle):
		self.videoMode = videoMode
		self.piconLoader = piconLoader
		self.piconSize = piconSize
		self.baseHeight = self.piconSize.height()
		self.listStyle = listStyle

		GUIComponent.__init__(self)

		self.l = eListboxPythonMultiContent()
		self.l.setBuildFunc(self.buildTimerEntry)
		self.onSelectionChanged = []

		if self.videoMode == MODE_SD or self.videoMode == MODE_XD:
			self.overallFontHeight = 36
		elif self.videoMode == MODE_HD:
			self.overallFontHeight = 44

		self.l.setList(list)
		config.plugins.merlinEpgCenter.listItemHeight.addNotifier(self.changeHeight, initial_call=True)
		config.plugins.merlinEpgCenter.adjustFontSize.addNotifier(self.setFontSizes, initial_call=True)

		self.autoTimerPixmap = LoadPixmap(cached=False, path=resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/AutoTimerSmall.png"))

	def onShow(self):
		self.maxWidth = self.l.getItemSize().width()

	def setFontSizes(self, configElement=None):
		diff = configElement.getValue()

		if self.videoMode == MODE_SD:
			self.l.setFont(0, gFont("Regular", 18 + diff))
			self.l.setFont(1, gFont("Regular", 16 + diff))
			self.l.setFont(2, gFont("Regular", 14 + diff))
			self.l.setFont(3, gFont("Regular", 12 + diff))
		elif self.videoMode == MODE_XD:
			self.l.setFont(0, gFont("Regular", 18 + diff))
			self.l.setFont(1, gFont("Regular", 16 + diff))
			self.l.setFont(2, gFont("Regular", 14 + diff))
			self.l.setFont(3, gFont("Regular", 12 + diff))
		elif self.videoMode == MODE_HD:
			self.l.setFont(0, gFont("Regular", 22 + diff))
			self.l.setFont(1, gFont("Regular", 20 + diff))
			self.l.setFont(2, gFont("Regular", 18 + diff))
			self.l.setFont(3, gFont("Regular", 16 + diff))

	def setMaxWidth(self, newSize):
		self.maxWidth = newSize.width()

	def changeHeight(self, configElement=None):
		if self.overallFontHeight > self.baseHeight:
			self.itemHeight = self.overallFontHeight + int(config.plugins.merlinEpgCenter.listItemHeight.value)
		else:
			self.itemHeight = self.baseHeight + int(config.plugins.merlinEpgCenter.listItemHeight.value)
		self.halfItemHeight = self.itemHeight / 2
		self.l.setItemHeight(self.itemHeight)

	def selectionChanged(self):
		for x in self.onSelectionChanged:
			x()

	def postWidgetCreate(self, instance):
		instance.setWrapAround(True)
		instance.setContent(self.l)
		instance.selectionChanged.get().append(self.selectionChanged)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		instance.selectionChanged.get().remove(self.selectionChanged)
		config.plugins.merlinEpgCenter.listItemHeight.removeNotifier(self.changeHeight)
		config.plugins.merlinEpgCenter.adjustFontSize.removeNotifier(self.setFontSizes)

	def buildTimerEntry(self, timer, processed):
		columnSpace = config.plugins.merlinEpgCenter.columnSpace.getValue()
		width = self.l.getItemSize().width()
		offsetLeft = 5 # 5 = left border
		offsetRight = self.maxWidth - 5 # 5 = right border
		secondLineColor = 0x00909090 # grey
		border = int(config.plugins.merlinEpgCenter.listItemHeight.value) / 2
		timeString = strftime("%H:%M", localtime(timer.begin)) + "-" + strftime("%H:%M", localtime(timer.end))

		if not processed:
			if timer.state == TimerEntry.StateWaiting:
				state = _("waiting")
				color = 0x00ffed00 # yellow
			elif timer.state == TimerEntry.StatePrepared:
				state = _("about to start")
				color = parseColor("red").argb()
			elif timer.state == TimerEntry.StateRunning:
				if timer.justplay:
					state = _("zapped")
				else:
					state = _("recording...")
				color = parseColor("red").argb()
			elif timer.state == TimerEntry.StateEnded:
				state = _("done!")
				color = parseColor("green").argb()
			else:
				state = _("<unknown>")
				color = parseColor("red").argb()
		else:
			state = _("done!")
			color = parseColor("green").argb()

		if timer.disabled:
			state = _("disabled")
			color = 0x009a9a9a

		if timer.justplay:
			state = "(ZAP) " + state

		res = [None]

		if config.plugins.merlinEpgCenter.showListNumbers.value:
			number = str(self.instance.getCurrentIndex() + 1)
			width = self.maxWidth * 3 / 100
			# 30 breite
			res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, 0, width, self.itemHeight, 1, RT_HALIGN_RIGHT | RT_VALIGN_CENTER, number))
			offsetLeft = offsetLeft + width + columnSpace

		if config.plugins.merlinEpgCenter.showPicons.value:
			width = self.piconSize.width()
			height = self.piconSize.height()

			if isinstance(timer, TimerListObject) and self.autoTimerPixmap:
				picon = self.autoTimerPixmap
			else:
				picon = self.piconLoader.getPicon(str(timer.service_ref))
			if picon:
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, offsetLeft, (self.itemHeight - self.baseHeight) / 2, width, height, picon))
			offsetLeft = offsetLeft + width + columnSpace

		if config.plugins.merlinEpgCenter.showServiceName.value:
			extraWidth = int(config.plugins.merlinEpgCenter.serviceNameWidth.value)
			if self.videoMode == MODE_SD:
				width = self.maxWidth * (12 + extraWidth) / 100
			elif self.videoMode == MODE_XD:
				width = self.maxWidth * (14 + extraWidth) / 100
			elif self.videoMode == MODE_HD:
				width = self.maxWidth * (16 + extraWidth) / 100

			if isinstance(timer, RecordTimerEntry):
				res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, 0, width, self.itemHeight, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, timer.service_ref.getServiceName()))
			else: # AutoTimer entry
				res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, 0, width, self.itemHeight, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, "AutoTimer"))
			offsetLeft = offsetLeft + width + columnSpace

		extraWidth = int(config.plugins.merlinEpgCenter.adjustFontSize.value)
		if extraWidth < 0:
			extraWidth = 0
		if self.videoMode == MODE_SD:
			width = self.maxWidth * (18 + extraWidth) / 100
		else:
			width = self.maxWidth * (14 + extraWidth) / 100

		if isinstance(timer, RecordTimerEntry):
			fd = getFuzzyDay(timer.begin)

			res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, border, width, self.halfItemHeight - border, 1, RT_HALIGN_LEFT | RT_VALIGN_TOP, timeString))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, self.halfItemHeight, width, self.halfItemHeight - border, 2, RT_HALIGN_CENTER | RT_VALIGN_TOP, fd, secondLineColor))
		else: # AutoTimer entry
			res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, 0, width, self.itemHeight, 1, RT_HALIGN_CENTER | RT_VALIGN_CENTER, timeString))

		offsetLeft = offsetLeft + width + columnSpace

		width = self.maxWidth * 22 / 100
		offsetRight = offsetRight - width
		res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetLeft, 0, offsetRight - offsetLeft, self.itemHeight, 1, RT_HALIGN_LEFT | RT_VALIGN_CENTER, timer.name, config.plugins.merlinEpgCenter.titleColor.value, config.plugins.merlinEpgCenter.titleColorSelected.value))
		res.append((eListboxPythonMultiContent.TYPE_TEXT, offsetRight, 0, width, self.itemHeight, 1, RT_HALIGN_RIGHT | RT_VALIGN_CENTER, state, color))

		return res
