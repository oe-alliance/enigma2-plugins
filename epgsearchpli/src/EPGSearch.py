# -*- coding: UTF-8 -*-

from . import _
from enigma import eEPGCache, eServiceReference, eServiceCenter, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, eRect, getDesktop, \
		RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_WRAP, eListboxPythonMultiContent, gFont, ePicLoad
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN, SCOPE_SKIN_IMAGE, fileExists
from Tools.LoadPixmap import LoadPixmap
from Tools.Alternatives import GetWithAlternative
from ServiceReference import ServiceReference
from EPGSearchSetup import EPGSearchSetup
from Screens.ChannelSelection import SimpleChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.EpgSelection import EPGSelection
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config
from Components.EpgList import EPGList, EPG_TYPE_SINGLE, EPG_TYPE_MULTI, Rect
from Components.TimerList import TimerList
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.Event import Event

from Components.GUIComponent import GUIComponent
from skin import parseFont

try:
	from Components.Renderer.Picon import getPiconName
	getPiconsName = True
except:
	getPiconsName = False
from time import localtime, time
from operator import itemgetter

typeMap = {
	"exact": eEPGCache.EXAKT_TITLE_SEARCH,
	"partial": eEPGCache.PARTIAL_TITLE_SEARCH,
	"start": eEPGCache.START_TITLE_SEARCH
}

caseMap = {
	"sensitive": eEPGCache.CASE_CHECK,
	"insensitive": eEPGCache.NO_CASE_CHECK
}

def GetTypeMap():
	search_type = config.plugins.epgsearch.search_type.value
	return typeMap.get(search_type, eEPGCache.PARTIAL_TITLE_SEARCH)

def GetCaseMap():
	search_case = config.plugins.epgsearch.search_case.value
	return caseMap.get(search_case, eEPGCache.NO_CASE_CHECK)

# Partnerbox installed and icons in epglist enabled?
try:
	from Plugins.Extensions.Partnerbox.PartnerboxEPGList import \
			isInRemoteTimer, getRemoteClockPixmap
	from Plugins.Extensions.Partnerbox.plugin import \
			showPartnerboxIconsinEPGList
	PartnerBoxIconsEnabled = showPartnerboxIconsinEPGList()
except ImportError:
	PartnerBoxIconsEnabled = False

try:
	from Plugins.Extensions.Partnerbox.PartnerboxEPGList import getRemoteClockZapPixmap
	from Plugins.Extensions.Partnerbox.plugin import showPartnerboxZapRepIconsinEPGList
	PartnerBoxZapRepIcons = showPartnerboxZapRepIconsinEPGList()
except ImportError:
	PartnerBoxZapRepIcons = False

# AutoTimer installed?
try:
	from Plugins.Extensions.AutoTimer.AutoTimerEditor import \
			addAutotimerFromEvent, addAutotimerFromSearchString
	autoTimerAvailable = True
except ImportError:
	autoTimerAvailable = False

# Modified EPGSearchList with support for PartnerBox
class EPGSearchList(EPGList):
	searchPiconPaths = ['/usr/share/enigma2/picon/', '/media/hdd/picon/', '/media/usb/picon/']

	def __init__(self, type=EPG_TYPE_SINGLE, selChangedCB=None, timer=None):
		EPGList.__init__(self, type, selChangedCB, timer)
		if config.plugins.epgsearch.picons.value:
			self.l.setItemHeight(34)
		self.l.setFont(1, gFont("Regular", 18))
		self.l.setBuildFunc(self.buildEPGSearchEntry)
		self.picon = ePicLoad()
		self.iconSize = 21
		self.iconDistance = 2
		self.nextIcon = self.iconSize + 2 * self.iconDistance
		self.colGap = 10
		self.skinColumns = False
		self.tw = 90
		self.dy = 0
		self.piconSize = 50,30
		self.piconDistance = 5
		self.pboxDistance = 80

		def loadPixmap(name):
			pixmap = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/%s" % name))
			if pixmap is None:
				pixmap = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/EPGSearch/icons/%s" % name)
			return pixmap

		if PartnerBoxIconsEnabled:
			self.remote_clock_pixmap = loadPixmap("remote_epgclock.png")
			self.remote_clock_add_pixmap = loadPixmap("remote_epgclock_add.png")
			self.remote_clock_pre_pixmap = loadPixmap("remote_epgclock_pre.png")
			self.remote_clock_post_pixmap = loadPixmap("remote_epgclock_post.png")
			self.remote_clock_prepost_pixmap = loadPixmap("remote_epgclock_prepost.png")

			if PartnerBoxZapRepIcons:
				self.remote_zapclock_pixmap = loadPixmap("remote_zapclock.png")
				self.remote_zapclock_add_pixmap = loadPixmap("remote_zapclock_add.png")
				self.remote_zapclock_pre_pixmap = loadPixmap("remote_zapclock_pre.png")
				self.remote_zapclock_post_pixmap = loadPixmap("remote_zapclock_post.png")
				self.remote_zapclock_prepost_pixmap = loadPixmap("remote_zapclock_prepost.png")
				self.remote_repclock_pixmap = loadPixmap("remote_repepgclock.png")
				self.remote_repclock_add_pixmap = loadPixmap("remote_repepgclock_add.png")
				self.remote_repclock_pre_pixmap = loadPixmap("remote_repepgclock_pre.png")
				self.remote_repclock_post_pixmap = loadPixmap("remote_repepgclock_post.png")
				self.remote_repclock_prepost_pixmap = loadPixmap("remote_repepgclock_prepost.png")
				self.remote_repzapclock_pixmap = loadPixmap("remote_repzapclock.png")
				self.remote_repzapclock_add_pixmap = loadPixmap("remote_repzapclock_add.png")
				self.remote_repzapclock_pre_pixmap = loadPixmap("remote_repzapclock_pre.png")
				self.remote_repzapclock_post_pixmap = loadPixmap("remote_repzapclock_post.png")
				self.remote_repzapclock_prepost_pixmap = loadPixmap("remote_repzapclock_prepost.png")

	def getClockTypesForEntry(self, service, eventId, beginTime, duration):
		if not beginTime:
			return None
		rec = self.isInTimer(eventId, beginTime, duration, service)
		if rec is not None:
			return rec[1]
		else:
			return None

	def isInTimer(self, eventid, begin, duration, service):
		returnValue = None
		type = 0
		time_match = 0
		bt = None
		check_offset_time = not config.recording.margin_before.value and not config.recording.margin_after.value
		end = begin + duration
		refstr = ':'.join(service.split(':')[:11])
		for x in self.timer.timer_list:
			check = ':'.join(x.service_ref.ref.toString().split(':')[:11]) == refstr
			if not check:
				sref = x.service_ref.ref
				parent_sid = sref.getUnsignedData(5)
				parent_tsid = sref.getUnsignedData(6)
				if parent_sid and parent_tsid:
					# check for subservice
					sid = sref.getUnsignedData(1)
					tsid = sref.getUnsignedData(2)
					sref.setUnsignedData(1, parent_sid)
					sref.setUnsignedData(2, parent_tsid)
					sref.setUnsignedData(5, 0)
					sref.setUnsignedData(6, 0)
					check = sref.toCompareString() == refstr
					num = 0
					if check:
						check = False
						event = eEPGCache.getInstance().lookupEventId(sref, eventid)
						num = event and event.getNumOfLinkageServices() or 0
					sref.setUnsignedData(1, sid)
					sref.setUnsignedData(2, tsid)
					sref.setUnsignedData(5, parent_sid)
					sref.setUnsignedData(6, parent_tsid)
					for cnt in range(num):
						subservice = event.getLinkageService(sref, cnt)
						if sref.toCompareString() == subservice.toCompareString():
							check = True
							break
			if check:
				timer_end = x.end
				timer_begin = x.begin
				type_offset = 0
				if not x.repeated and check_offset_time:
					if 0 < end - timer_end <= 59:
						timer_end = end
					elif 0 < timer_begin - begin <= 59:
						timer_begin = begin
				if x.justplay:
					type_offset = 5
					if (timer_end - x.begin) <= 1:
						timer_end += 60
				if x.always_zap:
					type_offset = 10

				timer_repeat = x.repeated
				# if set 'don't stop current event but disable coming events' for repeat timer
				running_only_curevent = x.disabled and x.isRunning() and timer_repeat
				if running_only_curevent:
					timer_repeat = 0
					type_offset += 15

				if timer_repeat != 0:
					type_offset += 15
					if bt is None:
						bt = localtime(begin)
						bday = bt.tm_wday
						begin2 = 1440 + bt.tm_hour * 60 + bt.tm_min
						end2 = begin2 + duration / 60
					xbt = localtime(x.begin)
					xet = localtime(timer_end)
					offset_day = False
					checking_time = x.begin < begin or begin <= x.begin <= end
					if xbt.tm_yday != xet.tm_yday:
						oday = bday - 1
						if oday == -1: oday = 6
						offset_day = x.repeated & (1 << oday)
					xbegin = 1440 + xbt.tm_hour * 60 + xbt.tm_min
					xend = xbegin + ((timer_end - x.begin) / 60)
					if xend < xbegin:
						xend += 1440
					if x.repeated & (1 << bday) and checking_time:
						if begin2 < xbegin <= end2:
							if xend < end2:
								# recording within event
								time_match = (xend - xbegin) * 60
								type = type_offset + 3
							else:
								# recording last part of event
								time_match = (end2 - xbegin) * 60
								type = type_offset + 1
						elif xbegin <= begin2 <= xend:
							if xend < end2:
								# recording first part of event
								time_match = (xend - begin2) * 60
								type = type_offset + 4
							else:
								# recording whole event
								time_match = (end2 - begin2) * 60
								type = type_offset + 2
						elif offset_day:
							xbegin -= 1440
							xend -= 1440
							if begin2 < xbegin <= end2:
								if xend < end2:
									# recording within event
									time_match = (xend - xbegin) * 60
									type = type_offset + 3
								else:
									# recording last part of event
									time_match = (end2 - xbegin) * 60
									type = type_offset + 1
							elif xbegin <= begin2 <= xend:
								if xend < end2:
									# recording first part of event
									time_match = (xend - begin2) * 60
									type = type_offset + 4
								else:
									# recording whole event
									time_match = (end2 - begin2) * 60
									type = type_offset + 2
					elif offset_day and checking_time:
						xbegin -= 1440
						xend -= 1440
						if begin2 < xbegin <= end2:
							if xend < end2:
								# recording within event
								time_match = (xend - xbegin) * 60
								type = type_offset + 3
							else:
								# recording last part of event
								time_match = (end2 - xbegin) * 60
								type = type_offset + 1
						elif xbegin <= begin2 <= xend:
							if xend < end2:
								# recording first part of event
								time_match = (xend - begin2) * 60
								type = type_offset + 4
							else:
								# recording whole event
								time_match = (end2 - begin2) * 60
								type = type_offset + 2
				else:
					if begin < timer_begin <= end:
						if timer_end < end:
							# recording within event
							time_match = timer_end - timer_begin
							type = type_offset + 3
						else:
							# recording last part of event
							time_match = end - timer_begin
							type = type_offset + 1
					elif timer_begin <= begin <= timer_end:
						if timer_end < end:
							# recording first part of event
							time_match = timer_end - begin
							type = type_offset + 4
						else:
							# recording whole event
							time_match = end - begin
							type = type_offset + 2
				if time_match:
					#if type in (2,7,12):
						# When full recording do not look further
					#	returnValue = (time_match, [type])
					#	break
					if returnValue:
						if type not in returnValue[1]:
							returnValue[1].append(type)
					else:
						returnValue = (time_match, [type])
		return returnValue

	def buildEPGSearchEntry(self, service, eventId, beginTime, duration, EventName):
		rec1 = self.getClockTypesForEntry(service, eventId, beginTime, duration)
		# Partnerbox 
		if PartnerBoxIconsEnabled:
			rec2 = beginTime and isInRemoteTimer(self, beginTime, duration, service)
		else:
			rec2 = False
		r1 = self.weekday_rect
		r2 = self.datetime_rect
		r3 = self.descr_rect
		dx = self.piconSize[0] + self.piconDistance
		nowTime = int(time())
		remaining = ""
		if beginTime is not None:
			if nowTime < beginTime:
				remaining = _(" (%d min)") % (duration / 60)
			else:
				prefix = "+"
				total = ((beginTime+duration) - nowTime) / 60
				if total <= 0:
					prefix = ""
				remaining = _(" (%s%d min)") % (prefix, total)
		t = localtime(beginTime)
		serviceref = ServiceReference(service) # for Servicename
		if config.plugins.epgsearch.picons.value:
			if getPiconsName:
				picon = getPiconName(service)
			else:
				picon = self.findPicon(service)
			if picon != "":
				self.picon.setPara((self.piconSize[0], self.piconSize[1], 1, 1, False, 1, '#000f0f0f'))
				self.picon.startDecode(picon, 0, 0, False)
				png = self.picon.getData()
				dy = int((self.height - self.piconSize[1])/2.)
				res = [
					None, # no private data needed
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r1.left(), r1.top()+ dy, self.piconSize[0], self.piconSize[1], png),
					(eListboxPythonMultiContent.TYPE_TEXT, r1.left() + dx, r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_RIGHT, self.days[t[6]]),
					(eListboxPythonMultiContent.TYPE_TEXT, r2.left() + dx, r2.top(), r2.width(), r1.height(), 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, "%02d.%02d, %02d:%02d"%(t[2],t[1],t[3],t[4]))
				]
			else:
				res = [
					None, # no private data needed
					(eListboxPythonMultiContent.TYPE_TEXT, r1.left() + dx, r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_RIGHT, self.days[t[6]]),
					(eListboxPythonMultiContent.TYPE_TEXT, r2.left() + dx, r2.top(), r2.width(), r1.height(), 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, "%02d.%02d, %02d:%02d"%(t[2],t[1],t[3],t[4]))
				]
		else:
			res = [
				None, # no private data needed
				(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_RIGHT, self.days[t[6]]),
				(eListboxPythonMultiContent.TYPE_TEXT, r2.left(), r2.top(), r2.width(), r1.height(), 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, "%02d.%02d, %02d:%02d"%(t[2],t[1],t[3],t[4]))
			]
		if config.plugins.epgsearch.picons.value:
			if rec1 or rec2:
				if rec1:
					clock_types = rec1
					# maybe Partnerbox too
					if rec2:
						if PartnerBoxZapRepIcons:
							clock_pic_partnerbox = getRemoteClockZapPixmap(self, service, beginTime, duration, eventId)
						else:
							clock_pic_partnerbox = getRemoteClockPixmap(self, service, beginTime, duration, eventId)
				else:
					if PartnerBoxZapRepIcons:
						clock_pic = getRemoteClockZapPixmap(self, service, beginTime, duration, eventId)
					else:
						clock_pic = getRemoteClockPixmap(self, service, beginTime, duration, eventId)
				if rec1 and rec2:
					# Partnerbox and local
					for i in range(len(clock_types)):
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + i * self.space + dx, r3.top() + self.dy, self.iconSize, self.iconSize, self.clocks[clock_types[i]]))
					res.extend((
						(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + (i + 1) * self.space + dx, r3.top() + self.dy, self.iconSize, self.iconSize, clock_pic_partnerbox),
						(eListboxPythonMultiContent.TYPE_TEXT, r3.left() + (i + 1) * self.space + self.pboxDistance + self.nextIcon, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceref.getServiceName() + ": " + EventName + remaining)))
				else:
					if rec1:
						for i in range(len(clock_types)):
							res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + i * self.space + dx, r3.top() + self.dy, self.iconSize, self.iconSize, self.clocks[clock_types[i]]))
						res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left() + (i + 1) * self.space + dx + self.nextIcon, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceref.getServiceName() + ": " + EventName + remaining))
					else:
						res.extend((
						(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + dx, r3.top() + self.dy, self.iconSize, self.iconSize, clock_pic),
						(eListboxPythonMultiContent.TYPE_TEXT, r3.left() + self.pboxDistance + self.nextIcon, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceref.getServiceName() + ": " + EventName + remaining)))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left() + dx, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceref.getServiceName() + ": " + EventName + remaining))
		else:
			if rec1 or rec2:
				if rec1:
					clock_types = rec1
					# maybe Partnerbox too
					if rec2:
						if PartnerBoxZapRepIcons:
							clock_pic_partnerbox = getRemoteClockZapPixmap(self, service, beginTime, duration, eventId)
						else:
							clock_pic_partnerbox = getRemoteClockPixmap(self, service, beginTime, duration, eventId)
				else:
					if PartnerBoxZapRepIcons:
						clock_pic = getRemoteClockZapPixmap(self, service, beginTime, duration, eventId)
					else:
						clock_pic = getRemoteClockPixmap(self, service, beginTime, duration, eventId)
				if rec1 and rec2:
					# Partnerbox and local
					for i in range(len(clock_types)):
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + i * self.space, r3.top() + self.dy, self.iconSize, self.iconSize, self.clocks[clock_types[i]]))
					res.extend((
						(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + (i + 1) * self.space, r3.top() + self.dy, self.iconSize, self.iconSize, clock_pic_partnerbox),
						(eListboxPythonMultiContent.TYPE_TEXT, r3.left() + (i + 1) * self.space + self.nextIcon, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceref.getServiceName() + ": " + EventName + remaining)))
				else:
					if rec1:
						for i in range(len(clock_types)):
							res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + i * self.iconSize, r3.top() + self.dy, self.iconSize, self.iconSize, self.clocks[clock_types[i]]))
						res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left() + (i + 1) * self.space + self.nextIcon, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceref.getServiceName() + ": " + EventName + remaining))
					else:
						res.extend((
						(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left(), r3.top() + self.dy, self.iconSize, self.iconSize, clock_pic),
						(eListboxPythonMultiContent.TYPE_TEXT, r3.left() + self.space + self.nextIcon, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceref.getServiceName() + ": " + EventName + remaining)))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceref.getServiceName() + ": " + EventName + remaining))
		return res

	def recalcEntrySize(self):
		esize = self.l.getItemSize()
		width = esize.width()
		height = esize.height()
		try:
			self.iconSize = self.clocks[0].size().height()
		except:
			pass
		self.space = self.iconSize + self.iconDistance
		self.nextIcon = self.iconSize + 2 * self.iconDistance
		self.height = height
		self.dy = int((height - self.iconSize)/2.)

		if self.type == EPG_TYPE_SINGLE:
			if self.skinColumns:
				x = 0
				self.weekday_rect = Rect(0, 0, self.gap(self.col[0]), height)
				x += self.col[0]
				self.datetime_rect = Rect(x, 0, self.gap(self.col[1]), height)
				x += self.col[1]
				self.descr_rect = Rect(x, 0, width-x, height)
			else:
				self.weekday_rect = Rect(0, 0, width/20*2-10, height)
				self.datetime_rect = Rect(width/20*2, 0, width/20*5-15, height)
				self.descr_rect = Rect(width/20*7, 0, width/20*13, height)
		elif self.type == EPG_TYPE_MULTI:
			if self.skinColumns:
				x = 0
				self.service_rect = Rect(x, 0, self.gap(self.col[0]), height)
				x += self.col[0]
				self.progress_rect = Rect(x, 8, self.gap(self.col[1]), height-16)
				self.start_end_rect = Rect(x, 0, self.gap(self.col[1]), height)
				x += self.col[1]
				self.descr_rect = Rect(x, 0, width-x, height)
			else:
				xpos = 0;
				w = width/10*3;
				self.service_rect = Rect(xpos, 0, w-10, height)
				xpos += w;
				w = width/10*2;
				self.start_end_rect = Rect(xpos, 0, w-10, height)
				self.progress_rect = Rect(xpos, 4, w-10, height-8)
				xpos += w
				w = width/10*5;
				self.descr_rect = Rect(xpos, 0, width, height)
		else: # EPG_TYPE_SIMILAR
			if self.skinColumns:
				x = 0
				self.weekday_rect = Rect(0, 0, self.gap(self.col[0]), height)
				x += self.col[0]
				self.datetime_rect = Rect(x, 0, self.gap(self.col[1]), height)
				x += self.col[1]
				self.descr_rect = Rect(x, 0, width-x, height)
			else:
				self.weekday_rect = Rect(0, 0, width/20*2-10, height)
				self.datetime_rect = Rect(width/20*2, 0, width/20*5-15, height)
				self.service_rect = Rect(width/20*7, 0, width/20*13, height)

	def findPicon(self, service=None):
		if service is not None:
			sname = ':'.join(service.split(':')[:11])
			pos = sname.rfind(':')
			if pos != -1:
				sname = sname[:pos].rstrip(':').replace(':','_')
				for path in self.searchPiconPaths:
					pngname = path + sname + ".png"
					if fileExists(pngname):
						return pngname
		return ""

	def applySkin(self, desktop, parent):
		def warningWrongSkinParameter(string):
			print "[EPGList] wrong '%s' skin parameters" % string
		def setEventItemFont(value):
			self.eventItemFont = parseFont(value, ((1,1),(1,1)))
		def setEventTimeFont(value):
			self.eventTimeFont = parseFont(value, ((1,1),(1,1)))
		def setIconDistance(value):
			self.iconDistance = int(value)
		def setIconShift(value):
			self.dy = int(value)
		def setTimeWidth(value):
			self.tw = int(value)
		def setColWidths(value):
			self.col = map(int, value.split(','))
			if len(self.col) == 2:
				self.skinColumns = True
			else:
				warningWrongSkinParameter(attrib)
		def setPiconSize(value):
			self.piconSize = map(int, value.split(','))
			if len(self.piconSize) == 2:
				self.skinColumns = True
			else:
				warningWrongSkinParameter(attrib)
		def setPiconDistance(value):
			self.piconDistance = int(value)
		def setColGap(value):
			self.colGap = int(value)
		def setPboxDistance(value):
			self.pboxDistance = int(value)
		for (attrib, value) in self.skinAttributes[:]:
			try:
				locals().get(attrib)(value)
				self.skinAttributes.remove((attrib, value))
			except:
				pass
		self.l.setFont(0, self.eventItemFont)
		self.l.setFont(1, self.eventTimeFont)
		return GUIComponent.applySkin(self, desktop, parent)

# main class of plugin
class EPGSearch(EPGSelection):
	def __init__(self, session, *args):
		Screen.__init__(self, session)
		self.skinName = ["EPGSearch", "EPGSelection"]

		self.searchargs = args
		self.currSearch = ""

		# XXX: we lose sort begin/end here
		self["key_yellow"] = Button(_("New Search"))
		self["key_blue"] = Button(_("History"))

# begin stripped copy of EPGSelection.__init__
		self.bouquetChangeCB = None
		self.serviceChangeCB = None
		self.ask_time = -1 #now
		self["key_red"] = Button("")
		self.closeRecursive = False
		self.saved_title = None
		self["Service"] = ServiceEvent()
		self["Event"] = Event()
		self.type = EPG_TYPE_SINGLE
		self.currentService=None
		self.zapFunc = None
		self.sort_type = 0
		self["key_green"] = Button(_("Add timer"))
		self.key_green_choice = self.ADD_TIMER
		self.key_red_choice = self.EMPTY
		self["list"] = EPGSearchList(type = self.type, selChangedCB = self.onSelectionChanged, timer = session.nav.RecordTimer)
		self["actions"] = ActionMap(["EPGSelectActions", "OkCancelActions", "MenuActions"],
			{
				"menu": self.menu,
				"cancel": self.closeScreen,
				"ok": self.eventSelected,
				"timerAdd": self.timerAdd,
				"yellow": self.yellowButtonPressed,
				"blue": self.blueButtonPressed,
				"info": self.infoKeyPressed,
				"red": self.zapToselect, # needed --> Partnerbox
				"nextBouquet": self.nextBouquet, # just used in multi epg yet
				"prevBouquet": self.prevBouquet, # just used in multi epg yet
				"nextService": self.nextService, # just used in single epg yet
				"prevService": self.prevService, # just used in single epg yet
			})

		self["actions"].csel = self
		self.onLayoutFinish.append(self.onCreate)
		# end stripped copy of EPGSelection.__init__
		self.select = False
		self.do_filter = None
		self.eventid = None
		self.isTMBD = fileExists("/usr/lib/enigma2/python/Plugins/Extensions/TMBD/plugin.pyo")
		# Partnerbox
		if PartnerBoxIconsEnabled:
			EPGSelection.PartnerboxInit(self, False)
			if self.isTMBD:
				self["key_red"].setText(_("Choice list"))
				self.select = True
		else:
			if self.isTMBD:
				self["key_red"].setText(_("Lookup in TMBD"))

		# Hook up actions for yttrailer if installed
		try:
			from Plugins.Extensions.YTTrailer.plugin import baseEPGSelection__init__
		except ImportError as ie:
			pass
		else:
			if baseEPGSelection__init__ is not None:
				self["trailerActions"] = ActionMap(["InfobarActions", "InfobarTeletextActions"],
				{
					"showTv": self.showTrailer,
					"showRadio": self.showTrailerList,
					"startTeletext": self.showConfig
				})

	def onCreate(self):
		self.setTitle(_("EPG Search"))

		if self.searchargs:
			self.searchEPG(*self.searchargs)
		else:
			l = self["list"]
			l.recalcEntrySize()
			l.list = []
			l.l.setList(l.list)
		del self.searchargs

		# Partnerbox
		if PartnerBoxIconsEnabled:
			EPGSelection.GetPartnerboxTimerlist(self)

	def eventSelected(self):
		cur = self['list'].getCurrent()
		event = cur[0]
		serviceref = cur[1]
		if event and serviceref:
			ref = eServiceReference(str(serviceref))
			id = event.getEventId()
			try:
				self.session.open(CurrentSearchSingleSelection, ref, event_id=id)
			except:
				pass

	def nextBouquet(self):
		if self.do_filter is None:
			self.show_filter()
		else:
			self.hide_filter()

	def prevBouquet(self):
		if self.do_filter is None:
			self.show_filter()
		else:
			self.hide_filter()

	def show_filter(self):
		if self.do_filter is not None:
			return
		cur = self['list'].getCurrent()
		event = cur[0]
		if event:
			l = self["list"]
			if len(l.list) > 1:
				description = event.getShortDescription()
				if description == "" or description == "no description available.":
					description = event.getExtendedDescription()
				if description:
					filter_list = []
					for x in l.list:
						event_id = x[1]
						if event_id:
							service = ServiceReference(x[0])
							ev = l.getEventFromId(service, event_id)
							if ev:
								if config.plugins.epgsearch.filter_type.value == "exact":
									if (ev.getShortDescription() and ev.getShortDescription() == description) or (ev.getExtendedDescription() and ev.getExtendedDescription() == description):
										filter_list.append(x)
								else:
									if (ev.getShortDescription() and ev.getShortDescription() in description) or (ev.getExtendedDescription() and ev.getExtendedDescription() in description):
										filter_list.append(x)
					if len(filter_list) > 0:
						self.eventid = event.getEventId()
						l.recalcEntrySize()
						self.do_filter = l.list
						l.list = filter_list
						l.l.setList(filter_list)
						l.instance.moveSelectionTo(0)

	def hide_filter(self):
		if self.do_filter is not None:
			l = self["list"]
			l.recalcEntrySize()
			l.list = self.do_filter
			l.l.setList(self.do_filter)
			if self.eventid is not None:
				l.moveToEventId(self.eventid)
			self.do_filter = None
			self.eventid = None

	def onSelectionChanged(self):
		self["Service"].newService(eServiceReference(str(self["list"].getCurrent()[1])))
		self["Event"].newEvent(self["list"].getCurrent()[0])
		EPGSelection.onSelectionChanged(self)
		if PartnerBoxZapRepIcons:
			if self.isTMBD:
				self["key_red"].setText(_("Choice list"))

	def zapToselect(self):
		if not PartnerBoxIconsEnabled:
			self.runTMBD()
		else:
			if self.select:
				list = [
				(_("Lookup in TMBD"), "runtmbd"),
				(_("Partnerbox Entries"), "partnerbox"),
				]
				dlg = self.session.openWithCallback(self.RedbuttonCallback,ChoiceBox,title= _("Select action:"), list = list)
				dlg.setTitle(_("Choice list RED Button"))
			else:
				self.zapTo()

	def RedbuttonCallback(self, ret):
		ret = ret and ret[1]
		if ret:
			if ret == "runtmbd":
				try:
					self.runTMBD()
				except:
					pass
			elif ret == "partnerbox":
				try:
					self.zapTo()
				except:
					pass
			else:
				pass

	def runTMBD(self):
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/TMBD/plugin.pyo"):
			from Plugins.Extensions.TMBD.plugin import TMBD
			cur = self["list"].getCurrent()
			if cur[0] is not None:
				name2 = cur[0].getEventName() or ''
				name3 = name2.split("(")[0].strip()
				eventname = name3.replace('"', '').replace('Õ/Ô', '').replace('Ì/Ô', '').replace('Õ/ô', '').replace('.', '')
				eventname = eventname.replace('0+', '').replace('(0+)', '').replace('6+', '').replace('(6+)', '').replace('7+', '').replace('(7+)', '').replace('12+', '').replace('(12+)', '').replace('16+', '').replace('(16+)', '').replace('18+', '').replace('(18+)', '')				
				try:
					tmbdsearch = config.plugins.tmbd.profile.value
				except:
					tmbdsearch = None
				if tmbdsearch != None:
					if config.plugins.tmbd.profile.value == "0":
						self.session.open(TMBD, eventname, False)
					else:
						try:
							from Plugins.Extensions.TMBD.plugin import KinoRu
							self.session.open(KinoRu, eventname, False)
						except:
							pass
				else:
					self.session.open(TMBD, eventname, False)

	def closeScreen(self):
		# Save our history
		config.plugins.epgsearch.save()
		EPGSelection.closeScreen(self)

	def yellowButtonPressed(self):
		self.session.openWithCallback(
			self.searchEPG,
			VirtualKeyBoard,
			title = _("Enter text to search for")
		)

	def menu(self):
		options = [
			(_("Import from Timer"), self.importFromTimer),
			(_("Import from EPG"), self.importFromEPG),
		]
		try:
			cur = self['list'].getCurrent()
			event = cur[0]
		except:
			event = None
		if event:
			options.append((_("Zap to selected service"), self.zapToSelectedService))
		if autoTimerAvailable:
			options.extend((
				(_("Import from AutoTimer"), self.importFromAutoTimer),
				(_("Save search as AutoTimer"), self.addAutoTimer),
				(_("Export selected as AutoTimer"), self.exportAutoTimer),
			))
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/TMDb/plugin.pyo"):
			options.append((_("Search for TMDb info"), self.opentmdb))
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/IMDb/plugin.py"):
			options.append((_("Open selected in IMDb"), self.openImdb))
		history = config.plugins.epgsearch.history.value
		if len(history) > 0:
			options.append((_("Clear history"), self.ClearHistory))
		options.append((_("Timers list"), self.openTimerslist))
		options.append((_("Setup"), self.setup))

		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list = options
		)

	def menuCallback(self, ret):
		ret and ret[1]()

	def importFromTimer(self):
		self.session.openWithCallback(
			self.searchEPG,
			EPGSearchTimerImport
		)
	def openTimerslist(self):
		try:
			from Screens.TimerEdit import TimerEditList
			self.session.open(TimerEditList)
		except:
			pass

	def importFromEPG(self):
		self.session.openWithCallback(
			self.searchEPG,
			EPGSearchChannelSelection
		)

	def importFromAutoTimer(self):
		removeInstance = False
		try:
			# Import Instance
			from Plugins.Extensions.AutoTimer.plugin import autotimer

			if autotimer is None:
				removeInstance = True
				# Create an instance
				from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
				autotimer = AutoTimer()

			# Read in configuration
			autotimer.readXml()
		except Exception as e:
			self.session.open(
				MessageBox,
				_("Could not read AutoTimer timer list: %s") % e,
				type = MessageBox.TYPE_ERROR
			)
		else:
			# Fetch match strings
			# XXX: we could use the timer title as description
			options = [(x.match, x.match) for x in autotimer.getTimerList()]

			self.session.openWithCallback(
				self.searchEPGWrapper,
				ChoiceBox,
				title = _("Select text to search for"),
				list = options
			)
		finally:
			# Remove instance if there wasn't one before
			if removeInstance:
				autotimer = None

	def addAutoTimer(self):
		addAutotimerFromSearchString(self.session, self.currSearch)

	def exportAutoTimer(self):
		try:
			cur = self['list'].getCurrent()
			event = cur[0]
		except:
			event = None
		if event is None:
			return
		addAutotimerFromEvent(self.session, cur[0], cur[1])

	def openImdb(self):
		try:
			cur = self['list'].getCurrent()
			event = cur[0]
		except:
			event = None
		if event is None:
			return
		try:
			from Plugins.Extensions.IMDb.plugin import IMDB
			self.session.open(IMDB, cur[0].getEventName())
		except ImportError as ie:
			pass
			
	def zapToSelectedService(self):
		cur = self["list"].getCurrent()
		serviceref = cur[1]
		if serviceref:
			try:
				from Screens.InfoBar import InfoBar
				InfoBarInstance = InfoBar.instance
				if InfoBarInstance is not None:
						InfoBarInstance.servicelist.clearPath()
						InfoBarInstance.servicelist.setRoot(serviceref.ref)
						InfoBarInstance.servicelist.enterPath(serviceref.ref)
						InfoBarInstance.servicelist.saveRoot()
						InfoBarInstance.servicelist.saveChannel(serviceref.ref)
						InfoBarInstance.servicelist.addToHistory(serviceref.ref)
				self.session.nav.playService(serviceref.ref)
			except:
				pass
		
	def opentmdb(self):
		cur = self['list'].getCurrent()
		event = cur[0]
		if event:
			try:
				from Plugins.Extensions.TMDb.plugin import TMDbMain
				self.session.open(TMDbMain, event.getEventName())
			except ImportError as ie:
				pass

	def ClearHistory(self):
		history = config.plugins.epgsearch.history.value
		if len(history) > 0:
			del history[0:]
			self.session.open(MessageBox, _("List of history is cleared !"), type = MessageBox.TYPE_INFO, timeout = 3)

	def setup(self):
		self.session.open(EPGSearchSetup)

	def blueButtonPressed(self):
		options = [(x, x) for x in config.plugins.epgsearch.history.value]

		if options:
			self.session.openWithCallback(
				self.searchEPGWrapper,
				ChoiceBox,
				title = _("Select text to search for"),
				list = options
			)
		else:
			self.session.open(
				MessageBox,
				_("No history !"),
				type = MessageBox.TYPE_INFO,
				timeout = 3
			)

	def searchEPGWrapper(self, ret):
		if ret:
			self.searchEPG(ret[1])

	def searchEPG(self, searchString = None, searchSave = True):
		if searchString:
			self.do_filter = None
			self.eventid = None
			if self.currSearch != "":
				l = self["list"]
				l.list = []
				l.l.setList(l.list)
			self.currSearch = searchString
			if searchSave:
				# Maintain history
				history = config.plugins.epgsearch.history.value
				if searchString not in history:
					history.insert(0, searchString)
					maxLen = config.plugins.epgsearch.history_length.value
					if len(history) > maxLen:
						del history[maxLen:]
				else:
					history.remove(searchString)
					history.insert(0, searchString)

			# Workaround to allow search for umlauts if we know the encoding (pretty bad, I know...)
			encoding = config.plugins.epgsearch.encoding.value
			if encoding != 'UTF-8':
				try:
					searchString = searchString.decode('UTF-8', 'replace').encode(encoding, 'replace')
				except (UnicodeDecodeError, UnicodeEncodeError):
					pass

			# Search EPG, default to empty list
			epgcache = eEPGCache.getInstance() # XXX: the EPGList also keeps an instance of the cache but we better make sure that we get what we want :-)
			ret = epgcache.search(('RIBDT', 1500, GetTypeMap(), searchString, GetCaseMap())) or []
			ret.sort(key=itemgetter(2)) # sort by time
			if config.plugins.epgsearch.bouquet.value:
				ret = self.sortEPGList(ret) # sort only user bouquets

			# Update List
			l = self["list"]
			l.recalcEntrySize()
			l.list = ret
			l.l.setList(ret)

	def sortEPGList(self, epglist):
		usr_ref_list = [ ]
		serviceHandler = eServiceCenter.getInstance()
		if not config.usage.multibouquet.value:
			service_types_tv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 22) || (type == 25) || (type == 134) || (type == 195)'
			bqrootstr = '%s FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet' % (service_types_tv)
			bouquet = eServiceReference(bqrootstr)
			servicelist = serviceHandler.list(bouquet)
			if not servicelist is None:
				while True:
					service = servicelist.getNext()
					if not service.valid(): break
					if not (service.flags & (eServiceReference.isMarker|eServiceReference.isDirectory)):
						usr_ref_list.append(service.toString())
		else:
			bqrootstr = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet'
			bouquet = eServiceReference(bqrootstr)
			bouquetlist = serviceHandler.list(bouquet)
			if not bouquetlist is None:
				while True:
					bouquet = bouquetlist.getNext()
					if not bouquet.valid(): break
					if bouquet.flags & eServiceReference.isDirectory and not bouquet.flags & eServiceReference.isInvisible:
						servicelist = serviceHandler.list(bouquet)
						if not servicelist is None:
							while True:
								service = servicelist.getNext()
								if not service.valid(): break
								if not (service.flags & (eServiceReference.isMarker|eServiceReference.isDirectory)):
									usr_ref_list.append(service.toString())
		result = [ ]
		if config.plugins.epgsearch.favorit_name.value:
			for e in epglist:
				for x in usr_ref_list:
					y = ':'.join(GetWithAlternative(x).split(':')[:11])
					if y == e[0]:
						new_e = (x, e[1], e[2], e[3], e[4])
						result.append(new_e)
		else:
			for e in epglist:
				for x in usr_ref_list:
					y = ':'.join(GetWithAlternative(x).split(':')[:11])
					if y == e[0]:
						result.append(e)
		return result

class EPGSearchTimerImport(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = ["EPGSearchTimerImport", "TimerEditList"]

		self.list = []
		self.fillTimerList()

		self["timerlist"] = TimerList(self.list)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"ok": self.search,
			"cancel": self.cancel,
			"green": self.search,
			"red": self.cancel
		}, -1)
		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Select a timer to search"))

	def fillTimerList(self):
		l = self.list
		del l[:]

		for timer in self.session.nav.RecordTimer.timer_list:
			l.append((timer, False))

		for timer in self.session.nav.RecordTimer.processed_timers:
			l.append((timer, True))
		l.sort(key = lambda x: x[0].begin)

	def search(self):
		cur = self["timerlist"].getCurrent()
		if cur:
			self.close(cur.name)

	def cancel(self):
		self.close(None)

class EPGSearchChannelSelection(SimpleChannelSelection):
	def __init__(self, session):
		SimpleChannelSelection.__init__(self, session, _("Channel Selection"))
		self.skinName = ["EPGSearchChannelSelection", "SimpleChannelSelection"]

		self["ChannelSelectEPGActions"] = ActionMap(["ChannelSelectEPGActions"],
		{
				"showEPGList": self.channelSelected
		})

	def channelSelected(self):
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.enterPath(ref)
		elif not (ref.flags & eServiceReference.isMarker):
			self.session.openWithCallback(
				self.epgClosed,
				EPGSearchEPGSelection,
				ref,
				False
			)

	def epgClosed(self, ret = None):
		if ret:
			self.close(ret)

class CurrentSearchSingleSelection(EPGSelection):
	def __init__(self, session, ref, event_id=None):
		self.event_id = event_id
		EPGSelection.__init__(self, session, ref)
		self.skinName = ["CurrentSearchSingleSelection", "EPGSelection"]

	def onCreate(self):
		try:
			EPGSelection.onCreate(self)
			if self.event_id is not None:
				self["list"].moveToEventId(self.event_id)
		except:
			pass

class EPGSearchEPGSelection(EPGSelection):
	def __init__(self, session, ref, openPlugin):
		EPGSelection.__init__(self, session, ref)
		self.skinName = ["EPGSearchEPGSelection", "EPGSelection"]
		self.openPlugin = openPlugin

	def eventSelected(self):
		cur = self["list"].getCurrent()
		evt = cur[0]
		sref = cur[1]
		if not evt:
			return

		if self.openPlugin:
			self.session.open(
				EPGSearch,
				evt.getEventName()
			)
		else:
			self.close(evt.getEventName())
