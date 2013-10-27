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

from Components.config import config
from Components.EpgList import EPGList
from enigma import eListboxPythonMultiContent, \
	RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, RT_HALIGN_CENTER

from time import localtime, strftime

from Tools.LoadPixmap import LoadPixmap
import PartnerboxFunctions as partnerboxfunctions

baseEPGList__init__ = None
basebuildSingleEntry = None
basebuildSimilarEntry = None
basebuildMultiEntry = None

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

def Partnerbox_EPGList__init__(self, type=0, selChangedCB=None, timer = None, time_epoch = None, overjump_empty = False, graphic=False):
	baseEPGList__init__(self, type, selChangedCB, timer, time_epoch = time_epoch, overjump_empty = overjump_empty, graphic=False)
	# Partnerbox Clock Icons
	self.remote_clock_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock.png')
	self.remote_clock_add_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_add.png')
	self.remote_clock_pre_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_pre.png')
	self.remote_clock_post_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_post.png')
	self.remote_clock_prepost_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_prepost.png')

def Partnerbox_SingleEntry(self, service, eventId, beginTime, duration, EventName):
	clock_pic = self.getPixmapForEntry(service, eventId, beginTime, duration)
	clock_pic_partnerbox = None
	rec2=beginTime and (isInRemoteTimer(self,beginTime, duration, service))
	r1=self.weekday_rect
	r2=self.datetime_rect
	r3=self.descr_rect
	t = localtime(beginTime)
	res = [
		None, # no private data needed
		(eListboxPythonMultiContent.TYPE_TEXT, r1.x, r1.y, r1.w, r1.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, _(strftime("%a", t))),
		(eListboxPythonMultiContent.TYPE_TEXT, r2.x, r2.y, r2.w, r1.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, strftime("%e/%m, %-H:%M", t))
	]
	if rec2:
		clock_pic_partnerbox = getRemoteClockPixmap(self,service, beginTime, duration, eventId)
	if clock_pic or clock_pic_partnerbox:
		if clock_pic and clock_pic_partnerbox:
			# wenn sowohl lokal als auch auf Partnerbox
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.x, r3.y, 21, 21, clock_pic),
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.x + 25, r3.y, 21, 21, clock_pic_partnerbox),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.x + 50, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName)
			))
		elif clock_pic_partnerbox:
			# wenn sowohl lokal als auch auf Partnerbox
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.x, r3.y, 21, 21, clock_pic_partnerbox),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.x + 25, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName)
			))
		else:
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.x, r3.y, 21, 21, clock_pic),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.x + 25, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName)
			))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.x, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, EventName))
	return res


def Partnerbox_SimilarEntry(self, service, eventId, beginTime, service_name, duration):
	clock_pic = self.getPixmapForEntry(service, eventId, beginTime, duration)
	clock_pic_partnerbox = None
	rec2=beginTime and (isInRemoteTimer(self,beginTime, duration, service))
	r1=self.weekday_rect
	r2=self.datetime_rect
	r3=self.service_rect
	t = localtime(beginTime)
	res = [
		None,  # no private data needed
		(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_RIGHT, _(strftime("%a", t))),
		(eListboxPythonMultiContent.TYPE_TEXT, r2.left(), r2.top(), r2.width(), r1.height(), 0, RT_HALIGN_RIGHT, strftime("%e/%m, %-H:%M", t))
	]
	if rec2:
		clock_pic_partnerbox = getRemoteClockPixmap(self,service, beginTime, duration, eventId)
	if clock_pic or clock_pic_partnerbox:
		if clock_pic and clock_pic_partnerbox:
			# wenn sowohl lokal als auch auf Partnerbox
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.x, r3.y, 21, 21, clock_pic),
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.x + 25, r3.y, 21, 21, clock_pic_partnerbox),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.x + 50, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name)
			))
		elif clock_pic_partnerbox:
			# wenn sowohl lokal als auch auf Partnerbox
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.x, r3.y, 21, 21, clock_pic_partnerbox),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.x + 50, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name)
			))
		else:
			res.extend((
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.x, r3.y, 21, 21, clock_pic),
				(eListboxPythonMultiContent.TYPE_TEXT, r3.x + 25, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name)
			))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.x, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, service_name))
	return res

def Partnerbox_MultiEntry(self, changecount, service, eventId, begTime, duration, EventName, nowTime, service_name):
	# so wie es aussieht wird der MultiEPG ueber ein Plugin angefahren...lasse den Code dennoch mal drinnen...
	clock_pic = self.getPixmapForEntry(service, eventId, beginTime, duration)
	clock_pic_partnerbox = None
	rec2=begTime and (isInRemoteTimer(self,begTime, duration, service))
	r1=self.service_rect
	r2=self.progress_rect
	r3=self.descr_rect
	r4=self.start_end_rect
	res = [ None ] # no private data needed
	if rec2:
		clock_pic_partnerbox = getRemoteClockPixmap(self,service, beginTime, duration, eventId)
	if clock_pic or clock_pic_partnerbox:
		if clock_pic and clock_pic_partnerbox:
			# wenn sowohl lokal als auch auf Partnerbox
			res.extend((
				(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width()-41, r1.height(), 0, RT_HALIGN_LEFT, service_name),
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r1.left()+r1.width()-32, r1.top(), 21, 21, clock_pic),
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r1.left()+r1.width()-16, r1.top(), 21, 21, clock_pic_partnerbox)
			))
		elif clock_pic_partnerbox:
			# wenn sowohl lokal als auch auf Partnerbox
			res.extend((
				(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width()-41, r1.height(), 0, RT_HALIGN_LEFT, service_name),
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r1.left()+r1.width()-32, r1.top(), 21, 21, clock_pic_partnerbox),
			))
		else:
			res.extend((
				(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width()-21, r1.height(), 0, RT_HALIGN_LEFT, service_name),
				(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r1.left()+r1.width()-16, r1.top(), 21, 21, clock_pic)
			))
	else:
		res.append((eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_LEFT, service_name))
	if begTime is not None:
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



def isInRemoteTimer(self, begin, duration, service):
	time_match = 0
	chktime = None
	chktimecmp = None
	chktimecmp_end = None
	end = begin + duration
	for x in partnerboxfunctions.remote_timer_list:
		if x.servicereference.upper() == service.upper():
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
	for x in partnerboxfunctions.remote_timer_list:
		if x.servicereference.upper() == refstr.upper():
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

