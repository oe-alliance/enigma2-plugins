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
from enigma import eListboxPythonMultiContent, \
	RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, RT_HALIGN_CENTER
from Components.config import config
from time import localtime, strftime, ctime, time

from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
import PartnerboxFunctions as partnerboxfunctions
from PartnerboxFunctions import getServiceRef

baseEPGList__init__ = None
basebuildSingleEntry = None
basebuildSimilarEntry = None
basebuildMultiEntry = None

picDY = 0

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

def Partnerbox_EPGList__init__(self, type=0, selChangedCB=None, timer = None):
	baseEPGList__init__(self, type, selChangedCB, timer)
	def loadPixmap(name):
		pixmap = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/%s" % name))
		if pixmap is None:
			pixmap = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/%s" % name)
		return pixmap

	# Partnerbox remote clock icons
	self.remote_clock_pixmap = loadPixmap("remote_epgclock.png")
	self.remote_clock_add_pixmap = loadPixmap("remote_epgclock_add.png")
	self.remote_clock_pre_pixmap = loadPixmap("remote_epgclock_pre.png")
	self.remote_clock_post_pixmap = loadPixmap("remote_epgclock_post.png")
	self.remote_clock_prepost_pixmap = loadPixmap("remote_epgclock_prepost.png")

	# Partnerbox remote zap clock icons
	self.remote_zapclock_pixmap = loadPixmap("remote_zapclock.png")
	self.remote_zapclock_add_pixmap = loadPixmap("remote_zapclock_add.png")
	self.remote_zapclock_pre_pixmap = loadPixmap("remote_zapclock_pre.png")
	self.remote_zapclock_post_pixmap = loadPixmap("remote_zapclock_post.png")
	self.remote_zapclock_prepost_pixmap = loadPixmap("remote_zapclock_prepost.png")

	# Partnerbox remote repeat icons
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

def Partnerbox_SingleEntry(self, service, eventId, beginTime, duration, EventName):
	rec1 = self.getClockTypesEntry(service, eventId, beginTime, duration)
	rec2 = beginTime and (isInRemoteTimer(self, beginTime, duration, service))
	r1=self.weekday_rect
	r2=self.datetime_rect
	r3=self.descr_rect
	s=self.iconSize
	space=self.space
	distance=self.iconDistance
	times=80
	dy=self.dy

	t = localtime(beginTime)
	if config.plugins.Partnerbox.showremaingepglist.value:
		nowTime = int(time())
		Time = ""
		if beginTime is not None:
			if nowTime < beginTime:
				Time = _("%d min") % (duration / 60)
			else:
				prefix = "+"
				remaining = ((beginTime+duration) - int(time())) / 60
				if remaining <= 0:
					prefix = ""
				Time = _("%s%d min") % (prefix, remaining)
		res = [
			None,
			(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, self.days[t[6]]),
			(eListboxPythonMultiContent.TYPE_TEXT, r2.left(), r2.top(), r2.width(), r1.height(), 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, "%02d.%02d, %02d:%02d"%(t[2],t[1],t[3],t[4]))
		]
		if rec1 or rec2:
			if rec1:
				clock_types = rec1
				if rec2:
					clock_pic_partnerbox = getRemoteClockZapPixmap(self, service, beginTime, duration, eventId)
			else:
				clock_pic = getRemoteClockZapPixmap(self, service, beginTime, duration, eventId)
			if rec1 and rec2:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), times, r3.height(), 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, Time))
				for i in range(len(clock_types)):
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + times + 10 + i * space, r3.top()+dy, s, s, self.clocks[clock_types[i]]))
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + times + 10 + i * space + space, r3.top()+dy, s, s, clock_pic_partnerbox))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left() + times + 10 + (i + 1) * space + space + distance, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), times, r3.height(), 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, Time))
				if rec1:
					for i in range(len(clock_types)):
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + times + 10 + i * space, r3.top()+dy, s, s, self.clocks[clock_types[i]]))
					res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left() + times + 10 + (i + 1) * space + distance, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName))
				else:
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + times + 10, r3.top()+dy, s, s, clock_pic))
					res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left() + times + 10 + space + distance, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName))
		else:
			res.extend((
				(eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), times, r3.height(), 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, Time),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.left() + times + 10, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName)))
		return res
	else:
		res = [
			None,
			(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, self.days[t[6]]),
			(eListboxPythonMultiContent.TYPE_TEXT, r2.left(), r2.top(), r2.width(), r1.height(), 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, "%02d.%02d, %02d:%02d"%(t[2],t[1],t[3],t[4]))
		]
		if rec1 or rec2:
			if rec1:
				clock_types = rec1
				if rec2:
					clock_pic_partnerbox = getRemoteClockZapPixmap(self, service, beginTime, duration, eventId)
			else:
				clock_pic = getRemoteClockZapPixmap(self, service, beginTime, duration, eventId)
			if rec1 and rec2:
				for i in range(len(clock_types)):
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + i * space, r3.top()+dy, s, s, self.clocks[clock_types[i]]))
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + i * space + space, r3.top()+dy, s, s, clock_pic_partnerbox))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left() + (i + 1) * space + space + distance, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName))
			else:
				if rec1:
					for i in range(len(clock_types)):
						res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + i * space, r3.top()+dy, s, s, self.clocks[clock_types[i]]))
					res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left() + (i + 1) * space + distance, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName))
				else:
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left(), r3.top()+dy, s, s, clock_pic))
					res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left() + space + distance, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName))
		return res

def Partnerbox_SimilarEntry(self, service, eventId, beginTime, service_name, duration):
	rec1 = self.getClockTypesEntry(service, eventId, beginTime, duration)
	rec2 = beginTime and (isInRemoteTimer(self, beginTime, duration, service))
	r1=self.weekday_rect
	r2=self.datetime_rect
	r3=self.service_rect
	s=self.iconSize
	space=self.space
	distance=self.iconDistance
	dy=self.dy

	t = localtime(beginTime)
	res = [
		None,
		(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, self.days[t[6]]),
		(eListboxPythonMultiContent.TYPE_TEXT, r2.left(), r2.top(), r2.width(), r1.height(), 0, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, "%02d.%02d, %02d:%02d"%(t[2],t[1],t[3],t[4]))
	]
	if rec1 or rec2:
		if rec1:
			clock_types = rec1
			if rec2:
				clock_pic_partnerbox = getRemoteClockZapPixmap(self, service, beginTime, duration, eventId)
		else:
			clock_pic = getRemoteClockZapPixmap(self, service, beginTime, duration, eventId)
		if rec1 and rec2:
			for i in range(len(clock_types)):
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + i * space, r3.top()+dy, s, s, self.clocks[clock_types[i]]))
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + space + i * space, r3.top()+dy, s, s, clock_pic_partnerbox))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left() + space + (i + 1) * space + distance, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name))
		else:
			if rec1:
				for i in range(len(clock_types)):
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + i * space, r3.top()+dy, s, s, self.clocks[clock_types[i]]))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left() + (i + 1) * space + distance, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name))
			else:
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left(), r3.top()+dy, s, s, clock_pic))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left() + space + distance, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name))
	return res

def Partnerbox_MultiEntry(self, changecount, service, eventId, begTime, duration, EventName, nowTime, service_name):
	rec1 = self.getClockTypesEntry(service, eventId, begTime, duration)
	rec2 = begTime and (isInRemoteTimer(self, begTime, duration, service))
	r1=self.service_rect
	r2=self.progress_rect
	r3=self.descr_rect
	r4=self.start_end_rect
	s=self.iconSize
	space=self.space
	distance=self.iconDistance
	dy=self.dy

	res = [ None ]
	if rec1 or rec2:
		if rec1:
			clock_types = rec1
			if rec2:
				clock_pic_partnerbox = getRemoteClockZapPixmap(self, service, begTime, duration, eventId)
		else:
			clock_pic = getRemoteClockZapPixmap(self, service, begTime, duration, eventId)
		if rec1 and rec2:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r1.x, r1.y, r1.w - (self.space * len(clock_types) + self.space + distance), r1.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name))
			for i in range(len(clock_types)):
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r1.x + r1.w - self.space * (i + 1) - self.space, r1.y + self.dy, s, s, self.clocks[clock_types[len(clock_types) - 1 - i]]))
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r1.left()+r1.width()-self.space, r1.top()+dy, s, s, clock_pic_partnerbox))
		else:
			if rec1:
				for i in range(len(clock_types)):
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r1.left()+r1.width()-self.space * (i + 1), r1.top()+dy, s, s, self.clocks[clock_types[len(clock_types) - 1 - i]]))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width()- (self.space * len(clock_types) + distance), r1.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name))
			else:
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r1.left()+r1.width()-self.space, r1.top()+dy, s, s, clock_pic))
				res.append((eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width()- self.space, r1.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name))
	if begTime is not None:
		if config.plugins.Partnerbox.showremaingepglist.value:
			if nowTime < begTime:
				begin = localtime(begTime)
				end = localtime(begTime+duration)
				res.extend((
					(eListboxPythonMultiContent.TYPE_TEXT, r4.x, r4.y, r4.w, r4.h, 1, RT_HALIGN_CENTER|RT_VALIGN_CENTER, "%02d.%02d - %02d.%02d"%(begin[3],begin[4],end[3],end[4])),
					(eListboxPythonMultiContent.TYPE_TEXT, r3.x, r3.y, self.gap(self.tw), r3.h, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, _("%d min") % (duration / 60)),
					(eListboxPythonMultiContent.TYPE_TEXT, r3.x + self.tw, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT, EventName)
				))
			else:
				percent = (nowTime - begTime) * 100 / duration
				prefix = "+"
				remaining = ((begTime+duration) - int(time())) / 60
				if remaining <= 0:
					prefix = ""
				res.extend((
					(eListboxPythonMultiContent.TYPE_PROGRESS, r2.x, r2.y, r2.w, r2.h, percent),
					(eListboxPythonMultiContent.TYPE_TEXT, r3.x, r3.y, self.gap(self.tw), r3.h, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, _("%s%d min") % (prefix, remaining)),
					(eListboxPythonMultiContent.TYPE_TEXT, r3.x + self.tw, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT, EventName)
				))
		else:
			if nowTime < begTime:
				begin = localtime(begTime)
				end = localtime(begTime+duration)
				res.extend((
					(eListboxPythonMultiContent.TYPE_TEXT, r4.left(), r4.top(), r4.width(), r4.height(), 1, RT_HALIGN_CENTER|RT_VALIGN_CENTER, "%02d.%02d - %02d.%02d"%(begin[3],begin[4],end[3],end[4])),
					(eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, EventName)
				))
			else:
				percent = (nowTime - begTime) * 100 / duration
				res.extend((
					(eListboxPythonMultiContent.TYPE_PROGRESS, r2.left(), r2.top(), r2.width(), r2.height(), percent),
					(eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, EventName)
				))
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
