#
#  Partnerbox E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2009
#  Support: www.dreambox-tools.info
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#

from Components.EpgList import EPGList
from enigma import eEPGCache, eListbox, eListboxPythonMultiContent, loadPNG, gFont, getDesktop, eRect, eSize, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_VALIGN_TOP, RT_WRAP, BT_SCALE, BT_KEEP_ASPECT_RATIO
from Components.config import config
from time import localtime, strftime, ctime, time
from skin import parameters as skinparameter

from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN, SCOPE_ACTIVE_SKIN
from Tools.LoadPixmap import LoadPixmap
import PartnerboxFunctions as partnerboxfunctions
from PartnerboxFunctions import getServiceRef

baseEPGList__init__ = None
basebuildSingleEntry = None
basebuildSimilarEntry = None
basebuildMultiEntry = None

picDY = 0
sf = 1


def Partnerbox_EPGListInit():
	global baseEPGList__init__, basebuildSingleEntry, basebuildSimilarEntry, basebuildMultiEntry
	if baseEPGList__init__ is None:
		baseEPGList__init__ = EPGList.__init__
	if basebuildSingleEntry is None:
		basebuildSingleEntry = EPGList.buildSingleEntry
	if basebuildSimilarEntry is None:
		basebuildSimilarEntry = EPGList.buildSimilarEntry
	if basebuildMultiEntry is None:
		basebuildMultiEntry = EPGList.buildMultiEntry
	if partnerboxfunctions.remote_timer_list is None:
		partnerboxfunctions.remote_timer_list = []
	EPGList.__init__ = Partnerbox_EPGList__init__
	EPGList.buildSingleEntry = Partnerbox_SingleEntry
	EPGList.buildSimilarEntry = Partnerbox_SimilarEntry
	EPGList.buildMultiEntry = Partnerbox_MultiEntry
	EPGList.getClockTypesEntry = getClockTypesEntry
	EPGList.isInTimer = isInTimer
	EPGList.iconSize = 0
	EPGList.space = 0
	EPGList.iconDistance = 0

def Partnerbox_EPGList__init__(self, type=0, selChangedCB=None, timer=None, time_epoch=120, overjump_empty=False, graphic=False):
	baseEPGList__init__(self, type, selChangedCB, timer, time_epoch, overjump_empty, graphic)

	self.clocks = [ LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_add.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_pre.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_prepost.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_post.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_add.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_pre.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_zap.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_prepost.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_post.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_add.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_pre.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_zaprec.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_prepost.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_post.png'))]

	self.selclocks = [ LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_add.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_selpre.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_selprepost.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_selpost.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_add.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_selpre.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_zap.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_selprepost.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_selpost.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_add.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_selpre.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_zaprec.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_selprepost.png')),
		LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_selpost.png'))]

	self.autotimericon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_ACTIVE_SKIN, 'icons/epgclock_autotimer.png'))

	self.nowEvPix = None
	self.nowSelEvPix = None
	self.othEvPix = None
	self.selEvPix = None
	self.othServPix = None
	self.nowServPix = None
	self.recEvPix = None
	self.recSelEvPix = None
	self.recordingEvPix= None
	self.zapEvPix = None
	self.zapSelEvPix = None

	self.borderTopPix = None
	self.borderBottomPix = None
	self.borderLeftPix = None
	self.borderRightPix = None
	self.borderSelectedTopPix = None
	self.borderSelectedLeftPix = None
	self.borderSelectedBottomPix = None
	self.borderSelectedRightPix = None
	self.InfoPix = None
	self.selInfoPix = None
	self.graphicsloaded = False

	self.borderColor = 0xC0C0C0
	self.borderColorService = 0xC0C0C0

	self.foreColor = 0xffffff
	self.foreColorSelected = 0xffffff
	self.backColor = 0x2D455E
	self.backColorSelected = 0xd69600
	self.foreColorService = 0xffffff
	self.backColorService = 0x2D455E
	self.foreColorNow = 0xffffff
	self.foreColorNowSelected = 0xffffff
	self.backColorNow = 0x00825F
	self.backColorNowSelected = 0xd69600
	self.foreColorPast = 0x808080
	self.foreColorPastSelected = 0x808080
	self.backColorPast = 0x2D455E
	self.backColorPastSelected = 0xd69600
	self.foreColorServiceNow = 0xffffff
	self.backColorServiceNow = 0x00825F

	self.foreColorRecord = 0xffffff
	self.backColorRecord = 0xd13333
	self.foreColorRecordSelected = 0xffffff
	self.backColorRecordSelected = 0x9e2626
	self.foreColorZap = 0xffffff
	self.backColorZap = 0x669466
	self.foreColorZapSelected = 0xffffff
	self.backColorZapSelected = 0x436143

	self.serviceFontNameGraph = "Regular"
	self.eventFontNameGraph = "Regular"
	self.eventFontNameSingle = "Regular"
	self.eventFontNameMulti = "Regular"
	self.serviceFontNameInfobar = "Regular"
	self.eventFontNameInfobar = "Regular"

	if self.screenwidth and self.screenwidth == 1920:
		global sf
		sf = 1.5
		self.posx, self.posy , self.picx, self.picy, self.gap = skinparameter.get("EpgListIcon", (2,13,25,25,2))
	else:
		self.posx, self.posy , self.picx, self.picy, self.gap = skinparameter.get("EpgListIcon", (1,11,23,23,1))

	self.serviceFontSizeGraph = int(20 * sf)
	self.eventFontSizeGraph = int(18 * sf)
	self.eventFontSizeSingle = int(22 * sf)
	self.eventFontSizeMulti = int(22 * sf)
	self.serviceFontSizeInfobar = int(20 * sf)
	self.eventFontSizeInfobar = int(22 * sf)

	self.listHeight = None
	self.listWidth = None
	self.serviceBorderWidth = 1
	self.serviceNamePadding = 3
	self.eventBorderWidth = 1
	self.eventNamePadding = 3
	self.eventNameAlign = 'left'
	self.eventNameWrap = 'yes'
	self.NumberOfRows = None

def Partnerbox_SingleEntry(self, service, eventId, beginTime, duration, EventName):
	if self.listSizeWidth != self.l.getItemSize().width(): #recalc size if scrollbar is shown
		self.recalcEntrySize()

	if (beginTime is not None) and (beginTime+duration < time()):
		foreColor = self.foreColorPast
		backColor = self.backColorPast
		foreColorSel = self.foreColorPastSelected
		backColorSel = self.backColorPastSelected
	elif (beginTime is not None) and (beginTime < time()):
		foreColor = self.foreColorNow
		backColor = self.backColorNow
		foreColorSel = self.foreColorNowSelected
		backColorSel = self.backColorNowSelected
	else:
		foreColor = self.foreColor
		backColor = self.backColor
		foreColorSel = self.foreColorSelected
		backColorSel = self.backColorSelected
	#don't apply new defaults to old skins:
	if not self.skinUsingForeColorByTime:
		foreColor = None
		foreColorSel = None
	if not self.skinUsingBackColorByTime:
		backColor = None
		backColorSel = None

	clock_types = self.getPixmapForEntry(service, eventId, beginTime, duration)
	r1 = self.weekday_rect
	r2 = self.datetime_rect
	r3 = self.descr_rect
	t = localtime(beginTime)
	res = [
		None, # no private data needed
		(eListboxPythonMultiContent.TYPE_TEXT, r1.x, r1.y, r1.w, r1.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, _(strftime(_("%a"), t)), foreColor, foreColorSel, backColor, backColorSel),
		(eListboxPythonMultiContent.TYPE_TEXT, r2.x, r2.y, r2.w, r1.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, strftime(_("%e/%m, %-H:%M"), t), foreColor, foreColorSel, backColor, backColorSel)
	]
	if clock_types:
		if self.wasEntryAutoTimer and clock_types in (2,7,12):
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, r3.x+r3.w-self.picx - self.posx, (r3.h/2-self.posy), self.picx, self.picy, self.clocks[clock_types]),
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, r3.x+r3.w-self.picx*2 - self.gap - self.posx, (r3.h/2-self.posy), self.picx, self.picy, self.autotimericon),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.x, r3.y, r3.w-self.picx*2 - (self.gap*2) - self.posx, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName, foreColor, foreColorSel, backColor, backColorSel)
				))
		else:
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, r3.x+r3.w-self.picx - self.posx, (r3.h/2-self.posy), self.picx, self.picy, self.clocks[clock_types]),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.x, r3.y, r3.w-self.picx - self.posx, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName, foreColor, foreColorSel, backColor, backColorSel)
				))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.x, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName, foreColor, foreColorSel, backColor, backColorSel))
	return res

def Partnerbox_SimilarEntry(self, service, eventId, beginTime, service_name, duration):
	if self.listSizeWidth != self.l.getItemSize().width(): #recalc size if scrollbar is shown
		self.recalcEntrySize()
	clock_types = self.getPixmapForEntry(service, eventId, beginTime, duration)
	r1 = self.weekday_rect
	r2 = self.datetime_rect
	r3 = self.descr_rect
	t = localtime(beginTime)
	res = [
		None,  # no private data needed
		(eListboxPythonMultiContent.TYPE_TEXT, r1.x, r1.y, r1.w, r1.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, _(strftime(_("%a"), t))),
		(eListboxPythonMultiContent.TYPE_TEXT, r2.x, r2.y, r2.w, r1.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, strftime(_("%e/%m, %-H:%M"), t))
	]
	if clock_types:
		if self.wasEntryAutoTimer and clock_types in (2,7,12):
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, r3.x+r3.w-self.picx - self.posx, (r3.h/2-self.posy), self.picx, self.picy, self.clocks[clock_types]),
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, r3.x+r3.w-self.picx*2 - self.gap - self.posx, (r3.h/2-self.posy), self.picx, self.picy, self.autotimericon),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.x, r3.y, r3.w-self.picx*2 - (self.gap*2) - self.posx, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name)
			))
		else:
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, r3.x+r3.w-self.picx - self.posx, (r3.h/2-self.posy), self.picx, self.picy, self.clocks[clock_types]),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.x, r3.y, r3.w-self.picx - (self.gap*2) - self.posx, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name)
			))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.x, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name))
	return res


def Partnerbox_MultiEntry(self, changecount, service, eventId, beginTime, duration, EventName, nowTime, service_name):
	if self.listSizeWidth != self.l.getItemSize().width(): #recalc size if scrollbar is shown
		self.recalcEntrySize()
	r1 = self.service_rect
	r2 = self.progress_rect
	r3 = self.descr_rect
	r4 = self.start_end_rect
	fact1 = 70 * sf
	fact2 = 90 * sf
	fact3 = 20 * sf
	fact4 = 90 * sf
	borderw = 1 * sf
	res = [None, (eListboxPythonMultiContent.TYPE_TEXT, r1.x, r1.y, r1.w, r1.h, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, service_name)] # no private data needed
	if beginTime is not None:
		clock_types = self.getPixmapForEntry(service, eventId, beginTime, duration)
		if nowTime < beginTime:
			begin = localtime(beginTime)
			end = localtime(beginTime+duration)
			res.extend((
				(eListboxPythonMultiContent.TYPE_TEXT, r4.x, r4.y, r4.w, r4.h, 1, RT_HALIGN_CENTER|RT_VALIGN_CENTER, _("%02d.%02d - %02d.%02d")%(begin[3],begin[4],end[3],end[4])),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.x, r3.y, fact1, r3.h, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, _("%d min") % (duration / 60))
			))
		else:
			percent = (nowTime - beginTime) * 100 / duration
			prefix = "+"
			remaining = ((beginTime+duration) - int(time())) / 60
			if remaining <= 0:
				prefix = ""
			res.extend((
				(eListboxPythonMultiContent.TYPE_PROGRESS, r2.x+fact3, r2.y, r2.w-fact3*2, r2.h, percent, borderw),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.x, r3.y, fact1, r3.h, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, _("%s%d min") % (prefix, remaining))
			))
		if clock_types:
			pos = r3.x+r3.w
			if self.wasEntryAutoTimer and clock_types in (2,7,12):
				res.extend((
					(eListboxPythonMultiContent.TYPE_TEXT, r3.x + fact4, r3.y, r3.w-fact4-self.picx*2 - (self.gap*2) - self.posx, r3.h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName),
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, pos-self.picx - self.posx, (r3.h/2-self.posy), self.picx, self.picy, self.clocks[clock_types]),
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, pos-self.picx*2 - self.gap - self.posx, (r3.h/2-self.posy), self.picx, self.picy, self.autotimericon)
				))
			else:
				res.extend((
					(eListboxPythonMultiContent.TYPE_TEXT, r3.x + fact4, r3.y, r3.w-fact4-self.picx - (self.gap*2) - self.posx, r3.h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName),
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, pos-self.picx - self.posx, (r3.h/2-self.posy), self.picx, self.picy, self.clocks[clock_types])
				))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.x + fact2, r3.y, r3.w-fact2, r3.h, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName))
	return res


def getClockTypesEntry(self, service, eventId, beginTime, duration):
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
					event = self.epgcache.lookupEventId(sref, eventid)
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
					if oday == -1:
						oday = 6
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
				if not config.plugins.Partnerbox.allicontype.value:
					if type in (2,7,12,17,22,27):
						# When full recording do not look further
						returnValue = (time_match, [type])
						break
					elif returnValue:
						if type not in returnValue[1]:
							returnValue[1].append(type)
					else:
						returnValue = (time_match, [type])
				else:
					if returnValue:
						if type not in returnValue[1]:
							returnValue[1].append(type)
					else:
						returnValue = (time_match, [type])
	return returnValue

def isInRemoteTimer(self, begin, duration, service):
	time_match = 0
	chktime = None
	chktimecmp = None
	chktimecmp_end = None
	end = begin + duration
	service = getServiceRef(service)
	service_str = ':'.join(str(service).split(':')[:11])
	for x in partnerboxfunctions.remote_timer_list:
		servicereference_str = ':'.join(str(x.servicereference).split(':')[:11])
		if servicereference_str.upper() == service_str.upper():
			if x.repeated != 0:
				if chktime is None:
					chktime = localtime(begin)
					chktimecmp = chktime.tm_wday * 1440 + chktime.tm_hour * 60 + chktime.tm_min
					chktimecmp_end = chktimecmp + (duration / 60)
				time = localtime(x.timebegin)
				for y in range(7):
					if x.repeated & (2 ** y):
						timecmp = y * 1440 + time.tm_hour * 60 + time.tm_min
						if timecmp <= chktimecmp < (timecmp + ((x.timeend - x.timebegin) / 60)):
							time_match = ((timecmp + ((x.timeend - x.timebegin) / 60)) - chktimecmp) * 60
						elif chktimecmp <= timecmp < chktimecmp_end:
							time_match = (chktimecmp_end - timecmp) * 60
			else:
				if begin <= x.timebegin <= end:
					diff = end - x.timebegin
					if time_match < diff:
						time_match = diff
				elif x.timebegin <= begin <= x.timeend:
					diff = x.timeend - begin
					if time_match < diff:
						time_match = diff
			if time_match:
				break
	return time_match

def getRemoteClockPixmap(self, refstr, beginTime, duration, eventId):
	pre_clock = 1
	post_clock = 2
	clock_type = 0
	endTime = beginTime + duration
	refstr = getServiceRef(refstr)
	ref_str = ':'.join(str(refstr).split(':')[:11])
	for x in partnerboxfunctions.remote_timer_list:
		servicereference_str = ':'.join(str(x.servicereference).split(':')[:11])
		if servicereference_str.upper() == ref_str.upper():
			if x.eventId == eventId:
				return self.remote_clock_pixmap
			beg = x.timebegin
			end = x.timeend
			if beginTime > beg and beginTime < end and endTime > end:
				clock_type |= pre_clock
			elif beginTime < beg and endTime > beg and endTime < end:
				clock_type |= post_clock
	if clock_type == 0:
		return self.remote_clock_add_pixmap
	elif clock_type == pre_clock:
		return self.remote_clock_pre_pixmap
	elif clock_type == post_clock:
		return self.remote_clock_post_pixmap
	else:
		return self.remote_clock_prepost_pixmap

def getRemoteClockZapPixmap(self, refstr, beginTime, duration, eventId):
	type = 0
	time_match = 0
	justplay = 0
	repeated = 0
	endTime = beginTime + duration
	ref_str = ':'.join(str(refstr).split(':')[:11])
	for x in partnerboxfunctions.remote_timer_list:
		servicereference_str = ':'.join(str(x.servicereference).split(':')[:11])
		if servicereference_str.upper() == ref_str.upper():
			justplay = x.justplay
			repeated = x.repeated
			beg = x.timebegin
			end = x.timeend
			if x.justplay:
				if (end - beg) <= 1:
					end += 60
			if beginTime < beg <= endTime:
				if end < endTime:
					# recording within event
					time_match = end - beg
					type = 3
				else:
					# recording last part of event
					time_match = endTime - beg
					type = 1
			elif beg <= beginTime <= end:
				if end < endTime:
					# recording first part of event
					time_match = end - beginTime
					type = 4
				else:
					# recording whole event
					time_match = endTime - beginTime
					type = 2
			if time_match:
				if type == 2:
					if justplay:
						if repeated != 0:
							return self.remote_repzapclock_pixmap
						else:
							return self.remote_zapclock_pixmap
					else:
						if repeated != 0:
							return self.remote_repclock_pixmap
						else:
							return self.remote_clock_pixmap
				elif type == 3:
					if justplay:
						if repeated != 0:
							return self.remote_repzapclock_prepost_pixmap
						else:
							return self.remote_zapclock_prepost_pixmap
					else:
						if repeated != 0:
							return self.remote_repclock_prepost_pixmap
						else:
							return self.remote_clock_prepost_pixmap
				elif type == 4:
					if justplay:
						if repeated != 0:
							return self.remote_repzapclock_post_pixmap
						else:
							return self.remote_zapclock_post_pixmap
					else:
						if repeated != 0:
							return self.remote_repclock_post_pixmap
						else:
							return self.remote_clock_post_pixmap
				elif type == 1:
					if justplay:
						if repeated != 0:
							return self.remote_repzapclock_pre_pixmap
						else:
							return self.remote_zapclock_pre_pixmap
					else:
						if repeated != 0:
							return self.remote_repclock_pre_pixmap
						else:
							return self.remote_clock_pre_pixmap
	if justplay:
		if repeated != 0:
			return self.remote_repzapclock_add_pixmap
		else:
			return self.remote_zapclock_add_pixmap
	else:
		if repeated != 0:
			return self.remote_repclock_add_pixmap
		else:
			return self.remote_clock_add_pixmap
