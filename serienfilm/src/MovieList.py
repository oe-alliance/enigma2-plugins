# -*- coding: utf-8 -*-

# for localized messages     
from __future__ import print_function
from . import _x

from Components.GUIComponent import GUIComponent
from Tools.FuzzyDate import FuzzyTime
from ServiceReference import ServiceReference
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.config import config
from Tools.LoadPixmap import LoadPixmap
from Components.UsageConfig import preferredPath, defaultMoviePath
from enigma import eEnv
import copy
import os.path

from enigma import eListboxPythonMultiContent, eListbox, gFont, iServiceInformation

from six.moves import reload_module


RT_HALIGN_LEFT, RT_HALIGN_RIGHT, eServiceReference, eServiceCenter

class MovieList(GUIComponent):
	SORT_ALPHANUMERIC = 1
	SORT_RECORDED = 2

	LISTTYPE_ORIGINAL = 0x10
	LISTTYPE_COMPACT_TAGS = 0x20
	LISTTYPE_COMPACT_SERVICE = 0x40
	LISTTYPE_MINIMAL = 0x80
	LISTTYPE_COMPACT = LISTTYPE_COMPACT_TAGS | LISTTYPE_COMPACT_SERVICE

	HIDE_DESCRIPTION = 1
	SHOW_DESCRIPTION = 2

	SHOW_NO_TIMES = 0
	SHOW_RECORDINGTIME = 1
	SHOW_DURATION = 2
	SHOW_DIRECTORIES = 4

	# tinfo types:
	REAL_DIR = 1
	REAL_UP = 2
	VIRT_DIR = 4
	VIRT_UP = 8
	VIRT_ENTRY = (VIRT_DIR | VIRT_UP)

	MAXTIME = 0x7fffffff

	gsflists = []


	def __init__(self, root, list_type=None, sort_type=None, show_times=None, sftitle_episode_separator = None, MovieSelectionSelf = None):
		GUIComponent.__init__(self)
#		print "[SF-Plugin] class SF:MovieList init, lstt=%x, srt=%x, sht=%s, sft=>%s<, root=%s" % ( list_type, sort_type, show_times, str(sftitle_episode_separator), str(root))
		self.list_type = list_type or self.LISTTYPE_MINIMAL
		self.show_times = show_times or self.SHOW_DURATION | self.SHOW_DIRECTORIES
		self.sort_type = sort_type or self.SORT_RECORDED
		self.sftitle_episode_separator = sftitle_episode_separator

		self.l = eListboxPythonMultiContent()

		self.tags = set()
		self.list = None
		self.sflists = None
		self.MovieSelectionSelf = MovieSelectionSelf
		self.MselTitle = ""

		if root is not None:
			self.reload(root)

		self.pdirIcon = LoadPixmap(cached=True, path=eEnv.resolve('${libdir}/enigma2/python/Plugins/Extensions/SerienFilm/icons/folder_20.png'))
		self.rdirIcon = LoadPixmap(cached=True, path=eEnv.resolve('${libdir}/enigma2/python/Plugins/Extensions/SerienFilm/icons/folder_red.png'))
		self.fupIcon = LoadPixmap(cached=True, path=eEnv.resolve('${libdir}/enigma2/python/Plugins/Extensions/SerienFilm/icons/folderup_20.png'))
		self.pdirMap = MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(20, 20), png=self.pdirIcon)
		self.rdirMap = MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(20, 20), png=self.rdirIcon)
		self.fupMap = MultiContentEntryPixmapAlphaTest(pos=(0, 0), size=(20, 20), png=self.fupIcon)

		self.redrawList()
		self.l.setBuildFunc(self.buildMovieListEntry)

		self.onSelectionChanged = [ ]

	def connectSelChanged(self, fnc):
		if not fnc in self.onSelectionChanged:
			self.onSelectionChanged.append(fnc)

	def disconnectSelChanged(self, fnc):
		if fnc in self.onSelectionChanged:
			self.onSelectionChanged.remove(fnc)

	def selectionChanged(self):
		for x in self.onSelectionChanged:
#			print "[SF-Plugin] MovieList.selectionChanged: " + str(x)
			x()

	def setListType(self, type):
		self.list_type = type
		self.redrawList()
		self.l.setList(self.list)				# redraw

	def setShowTimes(self, val):
		self.show_times = val

	def setSortType(self, type):
		self.sort_type = type

	def setTitleEpiSep(self, sftitle_episode_separator):
		self.sftitle_episode_separator = sftitle_episode_separator


	def redrawList(self):
		if self.list_type & MovieList.LISTTYPE_ORIGINAL:
			self.l.setFont(0, gFont("Regular", 22))
			self.l.setFont(1, gFont("Regular", 18))
			self.l.setFont(2, gFont("Regular", 16))
			self.l.setItemHeight(75)
			if self.sflists and self.sflists[0] != self.list:
				self.l.setItemHeight(41)
		elif self.list_type & MovieList.LISTTYPE_COMPACT:
			self.l.setFont(0, gFont("Regular", 20))
			self.l.setFont(1, gFont("Regular", 16))
			self.l.setItemHeight(39)
#			self.l.setFont(1, gFont("Regular", 14))
#			self.l.setItemHeight(37)
		else:
			self.l.setFont(0, gFont("Regular", 20))	# MINIMAL
			self.l.setFont(1, gFont("Regular", 16))
			self.l.setItemHeight(25)

	#
	# | name of movie              |
	#
	def buildMovieListEntry(self, serviceref, info, begin, tinfo):
#		print "[SF-Plugin] SF:MovieList.buildMovieListEntry, lst_type=%x, show_tims=%x" % (self.list_type, self.show_times)

		width = self.l.getItemSize().width()
		len = tinfo[5]			#tinfo = [type, pixmap, txt, description, service, len]

		if len <= 0: #recalc len when not already done
			cur_idx = self.l.getCurrentSelectionIndex()
			x = self.list[cur_idx]
			if config.usage.load_length_of_movies_in_moviellist.value:
				len = x[1].getLength(x[0]) #recalc the movie length...
			else:
				len = 0		#dont recalc movielist to speedup loading the list
			self.list[cur_idx][3][5] = len	#update entry in list... so next time we don't need to recalc

		if len > 0:
			len = "%d:%02d" % (len / 60, len % 60)
		else:
			len = ""

		res = [ None ]
		begin_string = ""
		date_string = ""

		pixmap = tinfo[1]
		typ = tinfo[0]
		service = None
		if typ & (self.VIRT_UP | self.REAL_UP):
			txt = tinfo[3]	# [2] == " " for alpha-sort to top
		else:
			txt = tinfo[2]
			if begin > 0:
				t = FuzzyTime(begin)
				begin_string = t[0] + ", " + t[1]
				date_string = t[0]
		if not typ & (self.REAL_DIR | self.VIRT_ENTRY):
			service = tinfo[4]
		description = tinfo[3]
		tags = self.tags and info.getInfoString(serviceref, iServiceInformation.sTags)

		if isinstance(pixmap, str):
			pixmap = MultiContentEntryText(pos=(0, 0), size=(25, 20), font = 0, flags = RT_HALIGN_LEFT, text = pixmap)
		if pixmap is not None:
			res.append(pixmap)

		XPOS = 25

		if self.list_type & MovieList.LISTTYPE_ORIGINAL:
			res.append(MultiContentEntryText(pos=(XPOS, 0), size=(width, 30), font = 0, flags = RT_HALIGN_LEFT, text=txt))
			line2 = 20
			if self.list == self.sflists[0]:
				line2 = 50
				if not typ & (self.REAL_DIR | self.VIRT_ENTRY):
					res.append(MultiContentEntryText(pos=(XPOS, 30), size=(width, 20), font=1, flags=RT_HALIGN_LEFT, text=description))
			res.append(MultiContentEntryText(pos=(XPOS, line2), size=(150, 20), font=1, flags=RT_HALIGN_LEFT, text=begin_string))
			if service:
				res.append(MultiContentEntryText(pos=(XPOS+150, line2), size=(180, 20), font = 2, flags = RT_HALIGN_RIGHT, text = service))
			if tags:
				res.append(MultiContentEntryText(pos=(width - 250, line2), size=(180, 20), font = 2, flags = RT_HALIGN_RIGHT, text = tags))
			if not typ & (self.REAL_DIR | self.VIRT_ENTRY):
				res.append(MultiContentEntryText(pos=(width-60, line2), size=(60, 20), font=2, flags=RT_HALIGN_RIGHT, text=len))
			return res

		tslen = 80
		if self.show_times & self.SHOW_RECORDINGTIME:
			tslen += 50
			date_string = begin_string
		dusz = 0
		if self.show_times & self.SHOW_DURATION and not tinfo[0] & (self.VIRT_ENTRY | self.REAL_UP):
			dusz = 57

		if self.list_type  & MovieList.LISTTYPE_COMPACT:
			res.append(MultiContentEntryText(pos=(XPOS, 4), size=(tslen-5, 20), font=1, flags=RT_HALIGN_RIGHT, text=date_string))
			res.append(MultiContentEntryText(pos=(XPOS + tslen, 0), size=(width-XPOS-tslen, 20), font = 0, flags = RT_HALIGN_LEFT, text = txt))
			other = None
			if self.list_type & MovieList.LISTTYPE_COMPACT_TAGS:
				if tags:
					res.append(MultiContentEntryText(pos=(width-dusz-185, 20), size=(180, 17), font=1, flags=RT_HALIGN_RIGHT, text=tags))
				otherend = dusz+185
				other = service
			else:
				if service:
					res.append(MultiContentEntryText(pos=(width-dusz-155, 20), size=(153, 17), font=1, flags=RT_HALIGN_RIGHT, text=service))
				otherend = dusz+160
				other = tags
			if self.list == self.sflists[0]:
				if not typ & (self.REAL_DIR | self.VIRT_ENTRY):
					res.append(MultiContentEntryText(pos=(XPOS, 20), size=(width-(XPOS+otherend), 17), font=1, flags=RT_HALIGN_LEFT, text=description))
				elif other:
					res.append(MultiContentEntryText(pos=(XPOS, 20), size=(width-(XPOS+otherend), 17), font=1, flags=RT_HALIGN_LEFT, text=other))
			if dusz:
				res.append(MultiContentEntryText(pos=(width-dusz, 20), size=(dusz-2, 20), font=1, flags=RT_HALIGN_RIGHT, text=len))
		else:
#			assert(self.list_type == MovieList.LISTTYPE_MINIMAL)
			res.append(MultiContentEntryText(pos=(XPOS, 3), size=(tslen-5, 20), font=1, flags=RT_HALIGN_RIGHT, text=date_string))
			res.append(MultiContentEntryText(pos=(XPOS + tslen, 0), size=(width-XPOS-tslen-dusz, 20), font = 0, flags = RT_HALIGN_LEFT, text = txt))
			if dusz:
				res.append(MultiContentEntryText(pos=(width-dusz, 3), size=(dusz, 20), font=1, flags=RT_HALIGN_RIGHT, text=len))

		return res

	def moveToIndex(self, index):
		if index <0:
			index += len(self.list)			# standard python list behaviour
		self.instance.moveSelectionTo(index)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def getCurrentEvent(self):
		l = self.l.getCurrentSelection()
		return l and l[0] and l[1] and l[1].getEvent(l[0])

	def getCurrent(self):
		l = self.l.getCurrentSelection()
		return l and l[0]

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		instance.selectionChanged.get().append(self.selectionChanged)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		instance.selectionChanged.get().remove(self.selectionChanged)

	def reload_module(self, root = None, filter_tags = None):
		if root is not None:
			self.load(root, filter_tags)
		else:
			self.load(self.root, filter_tags)
		self.l.setList(self.list)

	def removeService(self, service):
		for l in self.list[:]:
			repnr = tinfo = None
			if l[0] == service:
				tinfo = l[3]
				if not service.flags & eServiceReference.canDescent and isinstance(tinfo[1], str) and tinfo[1][0] == "#":
					repnr = int(tinfo[1][1:])
				self.list.remove(l)
				break
		self.l.setList(self.list)
		if len(self.list) == 1 and self.list[0][3][0] & self.VIRT_UP:	# last movie of a series is gone
			service = self.list[0][0]
			self.moveTo(service, True)
			assert service.flags == eServiceReference.canDescent
			self.removeService(service)
			return
		if repnr is None:
			return
		repeats = 0		# update repeatcount "#x" of surviving movies
		ele0 = 0
#		print "[SF-Plugin] removeService: searching " + tinfo[2]
		for i in range(1, len(self.list)):
			m = self.list[i]
			t = m[3]
#			print "[SF-Plugin] removeService try: %x, %s -- %s" % (m[0].flags,  str(t[1]), str(t[2]))
			if not m[0].flags & eServiceReference.canDescent and t[2] == tinfo[2] and isinstance(t[1], str) and t[1][0] == "#":
				repeats += 1
				rc = int(t[1][1:])
				if rc > repnr:
					rc -= 1
					t[1] = "#" + str(rc)
#					print "[SF-Plugin] removeService: %s --> %s" % (t[2], t[1])
				if rc == 0:
					ele0 = i
		if ele0 > 0 and repeats == 1:
			self.list[ele0][3][1] = None	# remove "#0" from only lonely surviving movie
#			print "[SF-Plugin] removeService: remove #0 from " + self.list[ele0][3][2]


	def __len__(self):
		return len(self.list)


	def playDirectory(self, serviceref):
		if serviceref.type == (eServiceReference.idUser | eServiceReference.idDVB) and serviceref.flags == eServiceReference.canDescent:
			self.moveTo(serviceref)		# virtual Directory
			return ""
		if serviceref.flags & eServiceReference.mustDescent:
			info = self.serviceHandler.info(serviceref)
			if info is None:
				name = ""
			else:
				name = info.getName(serviceref)
#			print "[SF-Plugin] MovieList.playDirectory: %s nicht spielbar" ,(name)
			return name

	def realDirUp(self, root):
		parent = None
		info = self.serviceHandler.info(root)
		pwd = info and info.getName(root)
		print("[SF-Plugin] MovieList.realDirUp: pwd = >%s<" % (str(pwd)))
		if pwd and os.path.exists(pwd) and not os.path.samefile(pwd, defaultMoviePath()):
			parentdir = pwd[:pwd.rfind("/", 0, -1)] + "/"
			parent = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + parentdir)
			info = self.serviceHandler.info(parent)
			if info is not None:
				txt = info.getName(parent)																# Titel
				service = ServiceReference(info.getInfoString(parent, iServiceInformation.sServiceref)).getServiceName()	# Sender
				description = info.getInfoString(parent, iServiceInformation.sDescription)				# Beschreibung
#				begin = info.getInfo(root, iServiceInformation.sTimeCreate)
				begin = self.MAXTIME
				parent.flags = eServiceReference.flagDirectory | eServiceReference.sort1
				tinfo = [self.REAL_DIR | self.REAL_UP, self.fupMap, "  0", txt, service, 1]	# "  0" sorts before VIRT_UP
				return ((parent, info, begin, tinfo))



	def load(self, root, filter_tags):
		# this lists our root service, then building a 
		# nice list

		self.serviceHandler = eServiceCenter.getInstance()
		parentLstEntry = self.realDirUp(root)

		self.rootlst = [ ]

		self.root = root
		list = self.serviceHandler.list(root)
		if list is None:
			print("[SF-Plugin] listing of movies failed")
			list = [ ]	
			return
		tags = set()

		while True:
			serviceref = list.getNext()
			if not serviceref.valid():
				break
			pixmap = None
			type = 0
			if serviceref.flags & eServiceReference.mustDescent:
				if not self.show_times & self.SHOW_DIRECTORIES:
					continue				# hide Directories
				type = self.REAL_DIR		# show Directories
				pixmap = self.rdirMap

			info = self.serviceHandler.info(serviceref)
			if info is None:
				continue
			begin = info.getInfo(serviceref, iServiceInformation.sTimeCreate)
			this_tags = info.getInfoString(serviceref, iServiceInformation.sTags).split(' ')

			# convert space-seperated list of tags into a set
			if this_tags == ['']:
				this_tags = []
			this_tags = set(this_tags)
			tags |= this_tags

			# filter_tags is either None (which means no filter at all), or 
			# a set. In this case, all elements of filter_tags must be present,
			# otherwise the entry will be dropped.			
			if filter_tags is not None and not this_tags.issuperset(filter_tags):
				continue

			txt = info.getName(serviceref)
			service = ServiceReference(info.getInfoString(serviceref, iServiceInformation.sServiceref)).getServiceName()	# Sender
			description = info.getInfoString(serviceref, iServiceInformation.sDescription)
			tinfo = [type, pixmap, txt, description, service, -1]

			self.rootlst.append((serviceref, info, begin, tinfo))

		self.rootlst.sort(key=lambda x: -x[2])						# movies of same name stay sortet by time
		self.rootlst.sort(key=lambda x: (x[3][2]+x[3][3]).lower())
		self.list = self.rootlst
		self.createSublists()


		if self.sort_type == self.SORT_RECORDED:
			self.sortLists()

		# finally, store a list of all tags which were found. these can be presented
		# to the user to filter the list
		self.tags = tags
		if parentLstEntry:
#			print "[SF-Plugin] SF:MovieList.load: parentLstEntry %s" % (self.debPrtEref(parentLstEntry[0]))
			self.list.insert(0, parentLstEntry)

	def moveTo(self, serviceref, descend_virtdirs=True, search_all_lists=True):
		count = 0
		for x in self.list:
			if x[0] == serviceref:

				if descend_virtdirs:
					l = self.list[count]
					tinfo = l[3]
					if tinfo[0] & self.VIRT_ENTRY:
						assert tinfo[4][:6] == "SFLIDX"
						self.list = self.sflists[int(tinfo[4][6:])]
						self.l.setList(self.list)
						self.MovieSelectionSelf.setTitle(self.MselTitle)
						self.redrawList()
					if tinfo[0] & self.VIRT_DIR:
						count = 0							# select VIRT_UP in sublist
						self.MovieSelectionSelf.setTitle("%s: %s" % (_x("Series"), tinfo[2]))
					elif tinfo[0] & self.VIRT_UP:
						rv = self.moveTo(serviceref, False)
						return rv

				self.instance.moveSelectionTo(count)
				return True
			count += 1
	# InfoBar:leavePlayerConfirmed(movielist) should find movies in virtual directories
		if search_all_lists and descend_virtdirs and self.sflists:
			savelist = self.list
			for l in self.sflists:
				if l == savelist:
					continue
				self.list = l
				self.l.setList(l)
				if self.moveTo(serviceref, descend_virtdirs=True, search_all_lists=False):
					return True
			self.list = savelist
			self.l.setList(self.list)

# enigmas list:		(serviceref, info, begin, len)	# len is replaced by tinfo
# tinfo:			[type, pixmap, txt, description, service, len]

# pixmap:			pixmap (DIR_UP...) or String (#0, #1 ... for multiple recordings)
# SFLIDX0...999		entry# in serlst, 0 == rootlist


	def serflm(self, film, episode):
		fdate = film[2]
		tinfo = film[3]
		dsc = tinfo[3]
		service = tinfo[4]
		epi = len(episode) == 2 and episode[1]
		if epi:
			txt = ": ".join((epi, dsc))
		else:
			txt = dsc or service
		if self.serdate < fdate:
			self.serdate = fdate
		tinfo[2] = txt
		tinfo[3] = dsc
		return film

	def update_repcnt(self, serlst, repcnt):
		for i in range(repcnt + 1):
			serlst[-( i+1 )][3][1] =  "#" + str(i)

	def createSublists(self):
		self.serdate = 0
		serie = serlst = None
		self.sflists = [self.rootlst]
		txt = ("", "")
		rootlidx = repcnt = 0
		global gsflists
		sflidx = 0
		if self.sftitle_episode_separator:
			splitTitle = lambda s: s.split(self.sftitle_episode_separator, 1)
		else:
			splitTitle = lambda s: [s]
#		print "[SF-Plugin] MovieList.createSublists: self.sftitle_episode_separator = %d = >%s<" % (len(self.sftitle_episode_separator), self.sftitle_episode_separator)
		for tinfo in self.rootlst[:]:
#			ts = tinfo[3][2].split(": ", 1)
			ts = splitTitle(tinfo[3][2])
			if txt[0] == ts[0]:
				if txt[0] != serie:				# neue Serie
					sflidx += 1
					serie = txt[0]
					ser_serviceref = eServiceReference(eServiceReference.idUser | eServiceReference.idDVB, 
							eServiceReference.canDescent, "SFLIDX" + str(sflidx))
					ser_info = self.serviceHandler.info(ser_serviceref)
					# VIRT_UP should sort first, but after REAL_UP: MAXTIME-1 resp. "  1"
					serlst = [(ser_serviceref, ser_info, MovieList.MAXTIME-1,
						[self.VIRT_UP, self.fupMap, "  1", txt[0], "SFLIDX0", 1])]
					self.sflists.append(serlst)
					serlst.append(self.serflm(self.rootlst[rootlidx-1], txt))
					parent_list_index = rootlidx-1
				film = self.rootlst.pop(rootlidx)
				rootlidx -= 1
				film = self.serflm(film, ts)
				samefilm = False
				if serlst:
					if serlst and film[3][3] != "" and film[3][2] == serlst[-1][3][2]:		# perhaps same Movie?
						event1 = film[1].getEvent(film[0])
						event2 = serlst[-1][1].getEvent(serlst[-1][0])
						if event1 and event2 and event1.getExtendedDescription() == event2.getExtendedDescription():
							samefilm = True
					if samefilm:
						repcnt += 1
					elif repcnt:
						self.update_repcnt(serlst, repcnt)
						repcnt = 0
					serlst.append(film)
			elif serlst:
				self.rootlst[parent_list_index] = (ser_serviceref, ser_info, self.serdate, 
					[self.VIRT_DIR, self.pdirMap, txt[0], "", "SFLIDX" + str(sflidx), 1])
				self.serdate = 0
				if repcnt:
					self.update_repcnt(serlst, repcnt)
					repcnt = 0
				serlst = None
			rootlidx += 1
			txt = ts
		if serlst:
			self.rootlst[parent_list_index] = (ser_serviceref, ser_info, self.serdate, 
				[self.VIRT_DIR, self.pdirMap, txt[0], "", "SFLIDX" + str(sflidx), None, 1])
			if repcnt:
				self.update_repcnt(serlst, repcnt)
#		print "[SF-Plugin] sflist has %d entries" % (len(self.sflists))
		gsflists = self.sflists




	def sortLists(self):
		if self.sort_type == self.SORT_ALPHANUMERIC:
			key = lambda x: (x[3][2]+x[3][3]).lower()
		else: key=lambda x: -x[2]
		if self.sflists:
			for list in self.sflists:
				list.sort(key=key)
			return True

	def toggleSort(self):
		save_list = self.list
		current = self.getCurrent()
		self.sort_type ^= (self.SORT_ALPHANUMERIC | self.SORT_RECORDED)
		self.sortLists()
		self.list = save_list
		self.l.setList(self.list)				# redraw
		self.moveTo(current, False)

#	def toggleTags(self, toggle):
#		if toggle and self.list_type & (MovieList.LISTTYPE_COMPACT | MovieList.LISTTYPE_MINIMAL):
#			self.showtags ^= MovieList.LISTTYPE_COMPACT
#		else:
#			self.showtags = 0
#		self.redrawList()
#		self.l.setList(self.list)				# redraw

	def saveTitle(self, title):
		self.MselTitle = title

	def getVirtDirList(self, name):
		return name[:6] == "SFLIDX" and self.sflists[int(name[6:])]

	@staticmethod
	def getVirtDirStatistics(name):
		if name[:6] == "SFLIDX":
			list = gsflists[int(name[6:])]
			repcnt = 0
			for l in list:
				if isinstance(l[3][1], str) and l[3][1][0] == "#" and l[3][1] != "#0":
					repcnt += 1
			s = "%d %s" % (len(list)-1, _x("Movies"))
			if repcnt:
				s += ", %d %s" % (repcnt, _x("duplicated"))
			return s


