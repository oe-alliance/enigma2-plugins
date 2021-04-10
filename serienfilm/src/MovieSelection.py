# -*- coding: utf-8 -*-
# for localized messages     
from __future__ import print_function
from __future__ import absolute_import
from . import _x

from Screens.Screen import Screen
from Components.Button import Button
from Components.ActionMap import HelpableActionMap, ActionMap
from Components.MenuList import MenuList
from .MovieList import MovieList
from Components.DiskInfo import DiskInfo
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.PluginComponent import plugins
from Components.config import config, ConfigSubsection, ConfigText, ConfigInteger, ConfigLocations, ConfigSet
from Components.Sources.ServiceEvent import ServiceEvent
from Components.UsageConfig import defaultMoviePath

from Plugins.Plugin import PluginDescriptor

from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.LocationBox import MovieLocationBox
from Screens.HelpMenu import HelpableScreen

from Tools.Directories import *
from Tools.BoundFunction import boundFunction

from enigma import eServiceReference, eServiceCenter, eTimer, eSize, iServiceInformation
from .SerienFilm import EpiSepCfg

config.movielist.sfmoviesort = ConfigInteger(default=MovieList.SORT_RECORDED)
config.movielist.sflisttype = ConfigInteger(default=MovieList.LISTTYPE_MINIMAL)
config.movielist.sftimes = ConfigInteger(default=MovieList.SHOW_DURATION | MovieList.SHOW_DIRECTORIES)
config.movielist.sftitle_episode_separator = ConfigText(default=_x(": "))

def setPreferredTagEditor(te):
	global preferredTagEditor
	try:
		if preferredTagEditor == None:
			preferredTagEditor = te
			print("Preferred tag editor changed to ", preferredTagEditor)
		else:
			print("Preferred tag editor already set to ", preferredTagEditor)
			print("ignoring ", te)
	except:
		preferredTagEditor = te
		print("Preferred tag editor set to ", preferredTagEditor)

def getPreferredTagEditor():
	global preferredTagEditor
	return preferredTagEditor

setPreferredTagEditor(None)

class MovieContextMenu(Screen):
	def __init__(self, session, csel, service):
#		print("[SF-Plugin] SF:MovieContextMenu init")
		Screen.__init__(self, session)
		self.csel = csel
		self.service = service

		self["actions"] = ActionMap(["OkCancelActions"],
			{
				"ok": self.okbuttonClick,
				"cancel": self.cancelClick
			})

		menu = [(_("delete..."), self.delete)]
		menu.extend([(p.description, boundFunction(self.execPlugin, p)) for p in plugins.getPlugins(PluginDescriptor.WHERE_MOVIELIST)])

		if config.movielist.sfmoviesort.value == MovieList.SORT_ALPHANUMERIC:
			menu.append((_x("sort by date  (quick toggle by key 0)"), boundFunction(self.sortBy, MovieList.SORT_RECORDED)))
		else:
			menu.append((_x("alphabetic sort  (quick toggle by key 0)"), boundFunction(self.sortBy, MovieList.SORT_ALPHANUMERIC)))
		
		menu.extend((
			(_x("list style elaborately"), boundFunction(self.listType, MovieList.LISTTYPE_ORIGINAL)),
			(_x("list style compact with service  (quick toggle by key 8)"), boundFunction(self.listType, MovieList.LISTTYPE_COMPACT_SERVICE)),
			(_x("list style compact with tags  (quick toggle by key 8)"), boundFunction(self.listType, MovieList.LISTTYPE_COMPACT_TAGS)),
			(_x("list style single line  (key = service, 8 = tags)"), boundFunction(self.listType, MovieList.LISTTYPE_MINIMAL))
		))

		if config.movielist.sftimes.value & MovieList.SHOW_RECORDINGTIME:
			menu.append((_x("hide recordingtime"), boundFunction(self.showTimes, MovieList.SHOW_RECORDINGTIME)))
		else:
			menu.append((_x("show recordingtime"), boundFunction(self.showTimes, MovieList.SHOW_RECORDINGTIME)))
		if config.movielist.sftimes.value & MovieList.SHOW_DURATION:
			menu.append((_x("hide duration"), boundFunction(self.showTimes, MovieList.SHOW_DURATION)))
		else:
			menu.append((_x("show duration"), boundFunction(self.showTimes, MovieList.SHOW_DURATION)))
		menu.append((_x("Configuration of the title:episode separator"), boundFunction(self.sfconfigure, None)))
		if config.movielist.sftimes.value & MovieList.SHOW_DIRECTORIES:
			menu.append((_x("hide the read real directories"), boundFunction(self.showTimes, MovieList.SHOW_DIRECTORIES)))
		else:
			menu.append((_x("show real directories in red"), boundFunction(self.showTimes, MovieList.SHOW_DIRECTORIES)))

		self["menu"] = MenuList(menu)

	def okbuttonClick(self):
		self["menu"].getCurrent()[1]()

	def cancelClick(self):
		self.close(False)

	def sortBy(self, newType):
		config.movielist.sfmoviesort.value = newType
		self.csel.setSortType(newType)
		if not self.csel["list"].sortLists():	# no reload required if sflists sorted
			self.csel.reloadList()
		self.close()

	def listType(self, newType):
		config.movielist.sflisttype.value = newType
		self.csel.toggletype = 0
		self.csel.setListType(newType)
		self.close()

	def showTimes(self, newType):
#		print "[SF-Plugin] MovieContextMenu:showTimes"
		config.movielist.sftimes.value ^= newType
		self.csel.setShowTimes(config.movielist.sftimes.value)
		if newType == MovieList.SHOW_DIRECTORIES:
			self.csel.reloadList()
#		self.csel.updateDescription()
		self.close()

	def sfconfigured(self, arg=None):
#		print "[SF-Plugin] MovieContextMenu.sfconfigure: arg = >%s<" % (arg)
		if config.movielist.sftitle_episode_separator.value != arg:
			config.movielist.sftitle_episode_separator.value = arg
			config.movielist.sftitle_episode_separator.save()
			self.csel.setTitleEpiSep(arg)

	def sfconfigure(self, arg):
		self.session.openWithCallback(self.sfconfigured, EpiSepCfg, config.movielist.sftitle_episode_separator.value)

	def execPlugin(self, plugin):
		plugin(session=self.session, service=self.service)

	def delete(self):
		serviceHandler = eServiceCenter.getInstance()
		offline = serviceHandler.offlineOperations(self.service)
		info = serviceHandler.info(self.service)
		name = info and info.getName(self.service) or _("this recording")
		if self.service.type == (eServiceReference.idUser | eServiceReference.idDVB) and self.service.flags == eServiceReference.canDescent:
			self.virtlist = self.csel["list"].getVirtDirList(name)
			if self.virtlist:
				self.session.openWithCallback(self.deleteVirtDirConfirmed, MessageBox,
					_x("Do you really want to delete series\n  %s\nwith %d movies?") % (self.virtlist[0][3][3], len(self.virtlist)-1))
			else:
				self.session.openWithCallback(self.close, MessageBox, _x("Please delete the files in this Directory!"), MessageBox.TYPE_ERROR)
			return
		dsc = info and info.getInfoString(self.service, iServiceInformation.sDescription)
		result = False
		if offline is not None:
			# simulate first
			if not offline.deleteFromDisk(1):
				result = True
		if result == True:
			self.session.openWithCallback(self.deleteConfirmed, MessageBox, _("Do you really want to delete %s\n%s?") % (name, dsc or ""))
		else:
			self.session.openWithCallback(self.close, MessageBox, _("You cannot delete this!"), MessageBox.TYPE_ERROR)

	def deleteVirtDirConfirmed(self, confirmed):
		if not confirmed:
#			for l in self.virtlist[1:]:
#				print "[SF-Plugin] MovieSelectin:deleteVirtDirConfirmed would delete " + l[3][2]
			return self.close()
		self.csel["list"].moveTo(self.service)	# put removeService in virtual Directory
		for l in self.virtlist[1:]:
#			print "[SF-Plugin] MovieSelectin:deleteVirtDirConfirmed deletes " + (l[3][2])
			self.service = l[0]
			self.deleteConfirmed(True)

	def deleteConfirmed(self, confirmed):
		if not confirmed:
			return self.close()
		
		serviceHandler = eServiceCenter.getInstance()
		offline = serviceHandler.offlineOperations(self.service)
		result = False
		if offline is not None:
			# really delete!
			if not offline.deleteFromDisk(0):
				result = True
		
		if result == False:
			self.session.openWithCallback(self.close, MessageBox, _("Delete failed!"), MessageBox.TYPE_ERROR)
		else:
			self.csel["list"].removeService(self.service)
			self.csel["freeDiskSpace"].update()
			self.close()

class SelectionEventInfo:
	def __init__(self):
		print("[SF-Plugin] SF:SelectionEventInfo init")
		self["Service"] = ServiceEvent()
		self.list.connectSelChanged(self.__selectionChanged)
		self.timer = eTimer()
		self.timer.callback.append(self.updateEventInfo)
		self.onShown.append(self.__selectionChanged)

	def __selectionChanged(self):
		if self.execing:
			self.timer.start(100, True)

	def updateEventInfo(self):
		serviceref = self.getCurrent()
		self["Service"].newService(serviceref)

class MovieSelection(Screen, HelpableScreen, SelectionEventInfo):
	def __init__(self, session, selectedmovie=None):
#		print "[SF-Plugin] SF:MovieSelection.init, PWD=%s; selmv=%s" % (config.movielist.last_videodir.value, str(selectedmovie))
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		self.tags = []
		if selectedmovie:
			self.selected_tags = config.movielist.last_selected_tags.value
		else:
			self.selected_tags = None
		self.selected_tags_ele = None
		self.toggletype = 0

		self.movemode = False
		self.bouquet_mark_edit = False

		self.delayTimer = eTimer()
		self.delayTimer.callback.append(self.updateHDDData)

		self["waitingtext"] = Label(_("Please wait... Loading list..."))

		# create optional description border and hide immediately
		self["DescriptionBorder"] = Pixmap()
		self["DescriptionBorder"].hide()

		if not fileExists(config.movielist.last_videodir.value):
			config.movielist.last_videodir.value = defaultMoviePath()
			config.movielist.last_videodir.save()
#			print "[SF-Plugin] MovieSelection.MovieSelection: save" + config.movielist.last_videodir.value
		self.current_ref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + config.movielist.last_videodir.value)

		self["list"] = MovieList(None,
			config.movielist.sflisttype.value,
			config.movielist.sfmoviesort.value,
			config.movielist.sftimes.value,
			config.movielist.sftitle_episode_separator.value,
			self)

		self.list = self["list"]
		self.selectedmovie = selectedmovie

		# Need list for init
		SelectionEventInfo.__init__(self)

		self["key_red"] = Button(_("All"))
		self["key_green"] = Button("")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		self["freeDiskSpace"] = self.diskinfo = DiskInfo(config.movielist.last_videodir.value, DiskInfo.FREE, update=False)

		if config.usage.setup_level.index >= 2: # expert+
			self["InfobarActions"] = HelpableActionMap(self, "InfobarActions", 
				{
					"showMovies": (self.doPathSelect, _("select the movie path")),
				})


		self["MovieSelectionActions"] = HelpableActionMap(self, "MovieSelectionActions",
			{
				"contextMenu": (self.doContext, _("menu")),
				"showEventInfo": (self.showEventInformation, _("show event details")),
			})

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
			{
				"red": (self.showAll, _("show all")),
				"green": (self.showTagsFirst, _("show first selected tag")),
				"yellow": (self.showTagsSecond, _("show second selected tag")),
				"blue": (self.showTagsSelect, _("show tag menu")),
			})

		self["OkCancelActions"] = HelpableActionMap(self, "OkCancelActions",
			{
				"cancel": (self.abort, _("exit movielist")),
				"ok": (self.movieSelected, _("select movie")),
			})

		self["NumberActions"] = HelpableActionMap(self, "SetupActions",
			{
				"0": (self.toggleSort, _x("Toggle date / alphabetic sort mode")),
				"deleteBackward": (self.moveToIndexStrt, _x("Jump to listbegin")),
				"deleteForward": (self.moveToIndexEnd, _x("Jump to listend")),
				"5": (self.toggleMinimal, _x("Toggle style minimal / compact")),
				"8": (self.toggleTags, _x("Toggle description / tags display")),
			})


		self.onShown.append(self.go)
		self.onLayoutFinish.append(self.saveListsize)
		self.inited = False

	def toggleSort(self):
		self["list"].toggleSort()

	def toggleMinimal(self):
		self.toggleTags(config.movielist.sflisttype.value & MovieList.LISTTYPE_COMPACT_TAGS or MovieList.LISTTYPE_COMPACT_SERVICE)

	def toggleTags(self, toggletype=MovieList.LISTTYPE_COMPACT):
		if self.toggletype == toggletype:
			self.toggletype = 0
		else:
			self.toggletype = toggletype
		self["list"].setListType(config.movielist.sflisttype.value ^ self.toggletype)

	def moveToIndexStrt(self):
		self["list"].moveToIndex(0)

	def moveToIndexEnd(self):
		self["list"].moveToIndex(-1)

	def updateDescription(self):
#		print "[SF-Plugin] MovieSelection.updateDescription DescriptionBorder height =" + str(self["DescriptionBorder"].instance.size().height())
		self["DescriptionBorder"].show()
		self["list"].instance.resize(eSize(self.listWidth, self.listHeight-self["DescriptionBorder"].instance.size().height()))

	def showEventInformation(self):
		from Screens.EventView import EventViewSimple
		from ServiceReference import ServiceReference
		evt = self["list"].getCurrentEvent()
		if evt:
			self.session.open(EventViewSimple, evt, ServiceReference(self.getCurrent()))

	def go(self):
		if not self.inited:
		# ouch. this should redraw our "Please wait..."-text.
		# this is of course not the right way to do this.
			self.delayTimer.start(10, 1)
			self.inited=True

	def saveListsize(self):
			listsize = self["list"].instance.size()
			self.listWidth = listsize.width()
			self.listHeight = listsize.height()
			self.updateDescription()

	def updateHDDData(self):
		self.reloadList(self.selectedmovie)
		self["waitingtext"].visible = False

	def moveTo(self):
		self["list"].moveTo(self.selectedmovie)

	def getCurrent(self):
		return self["list"].getCurrent()

	def movieSelected(self):
		current = self.getCurrent()
		if current is not None:
			dirname = self["list"].playDirectory(current)	# dont feed dirs to MoviePlayer
			if dirname is None:
				self.saveconfig()
				self.close(current)			# and play movie
			elif dirname:
				self.gotFilename(dirname)	# change to existing directory

	def doContext(self):
		current = self.getCurrent()
		if current is not None:
			self.session.open(MovieContextMenu, self, current)

	def abort(self):
		self.saveconfig()
		self.close(None)

	def saveconfig(self):
		config.movielist.last_selected_tags.value = self.selected_tags
		config.movielist.sfmoviesort.save()
		config.movielist.sflisttype.save()
		config.movielist.sftimes.save()

	def getTagDescription(self, tag):
		# TODO: access the tag database
		return tag

	def updateTags(self):
		# get a list of tags available in this list
		self.tags = list(self["list"].tags)

		if not self.tags:
			# by default, we do not display any filtering options
			self.tag_first = ""
			self.tag_second = ""
		else:
			tmp = config.movielist.first_tags.value
			if tmp in self.tags:
				self.tag_first = tmp
			else:
				self.tag_first = "<"+_("Tag 1")+">"
			tmp = config.movielist.second_tags.value
			if tmp in self.tags:
				self.tag_second = tmp
			else:
				self.tag_second = "<"+_("Tag 2")+">"
		self["key_green"].text = self.tag_first
		self["key_yellow"].text = self.tag_second
		
		# the rest is presented in a list, available on the
		# fourth ("blue") button
		if self.tags:
			self["key_blue"].text = _("Tags")+"..."
		else:
			self["key_blue"].text = ""

	def setListType(self, type):
		self["list"].setListType(type)

	def setShowTimes(self, val):
		self["list"].setShowTimes(val)

	def setSortType(self, type):
		self["list"].setSortType(type)

	def setTitleEpiSep(self, sftitle_episode_separator):
		self["list"].setTitleEpiSep(sftitle_episode_separator)
		self.reloadList()

	def reloadList(self, sel=None, home=False):
		if not fileExists(config.movielist.last_videodir.value):
			path = defaultMoviePath()
			config.movielist.last_videodir.value = path
			config.movielist.last_videodir.save()
			self.current_ref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + path)
			self["freeDiskSpace"].path = path
		if sel is None:
			sel = self.getCurrent()
		self["list"].reload(self.current_ref, self.selected_tags)
		title = _("Recorded files...")
		if config.usage.setup_level.index >= 2: # expert+
			title += "  " + config.movielist.last_videodir.value
		if self.selected_tags is not None:
			title += " - " + ','.join(self.selected_tags)
		self.setTitle(title)
		self["list"].saveTitle(title)
#		print "[SF-Plugin] MovieSelection:setTitle(%s)" % (str(title))
		if not (sel and self["list"].moveTo(sel)):
			if home:
				self["list"].moveToIndex(0)
		self.updateTags()
		self["freeDiskSpace"].update()

	def doPathSelect(self):
		self.session.openWithCallback(
			self.gotFilename,
			MovieLocationBox,
			_("Please select the movie path..."),
			config.movielist.last_videodir.value
		)

	def gotFilename(self, res):
		if res is not None and res is not config.movielist.last_videodir.value:
			if fileExists(res):
				config.movielist.last_videodir.value = res
				config.movielist.last_videodir.save()
#				print "[SF-Plugin] MovieSelection.gotFilename: save" + res
				self.current_ref = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + res)
				self["freeDiskSpace"].path = res
				self.reloadList(home=True)
			else:
				self.session.open(
					MessageBox,
					_("Directory %s nonexistent.") % (res),
					type=MessageBox.TYPE_ERROR,
					timeout=5
					)

	def showAll(self):
		self.selected_tags_ele = None
		self.selected_tags = None
		self.reloadList(home=True)

	def showTagsN(self, tagele):
		if not self.tags:
			self.showTagWarning()
		elif not tagele or (self.selected_tags and tagele.value in self.selected_tags) or not tagele.value in self.tags:
			self.showTagsMenu(tagele)
		else:
			self.selected_tags_ele = tagele
			self.selected_tags = set([tagele.value])
			self.reloadList(home=True)

	def showTagsFirst(self):
		self.showTagsN(config.movielist.first_tags)

	def showTagsSecond(self):
		self.showTagsN(config.movielist.second_tags)

	def showTagsSelect(self):
		self.showTagsN(None)

	def tagChosen(self, tag):
		if tag is not None:
			self.selected_tags = set([tag[0]])
			if self.selected_tags_ele:
				self.selected_tags_ele.value = tag[0]
				self.selected_tags_ele.save()
			self.reloadList(home=True)

	def showTagsMenu(self, tagele):
		self.selected_tags_ele = tagele
		list = [(tag, self.getTagDescription(tag)) for tag in self.tags]
		self.session.openWithCallback(self.tagChosen, ChoiceBox, title=_("Please select tag to filter..."), list=list)

	def showTagWarning(self):
		self.session.open(MessageBox, _("No tags are set on these movies."), MessageBox.TYPE_ERROR)

