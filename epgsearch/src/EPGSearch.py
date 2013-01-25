# for localized messages
from . import _

from enigma import eEPGCache, eTimer, eServiceReference, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, eListboxPythonMultiContent

from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from ServiceReference import ServiceReference

from EPGSearchSetup import EPGSearchSetup
from Screens.ChannelSelection import SimpleChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.EpgSelection import EPGSelection
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Plugins.SystemPlugins.Toolkit.NTIVirtualKeyBoard import NTIVirtualKeyBoard

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config
from Components.EpgList import EPGList, EPG_TYPE_SINGLE, EPG_TYPE_MULTI
from Components.TimerList import TimerList
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.Event import Event

from time import localtime, strftime
from operator import itemgetter

# Partnerbox installed and icons in epglist enabled?
try:
	from Plugins.Extensions.Partnerbox.PartnerboxEPGList import \
			isInRemoteTimer, getRemoteClockPixmap
	from Plugins.Extensions.Partnerbox.plugin import \
			showPartnerboxIconsinEPGList
	PartnerBoxIconsEnabled = showPartnerboxIconsinEPGList()
except ImportError:
	PartnerBoxIconsEnabled = False

# AutoTimer installed?
try:
	from Plugins.Extensions.AutoTimer.AutoTimerEditor import \
			addAutotimerFromEvent, addAutotimerFromSearchString
	autoTimerAvailable = True
except ImportError:
	autoTimerAvailable = False


# Modified EPGSearchList with support for PartnerBox
class EPGSearchList(EPGList):
	def __init__(self, type=EPG_TYPE_SINGLE, selChangedCB=None, timer=None):
		EPGList.__init__(self, type, selChangedCB, timer)
		self.l.setBuildFunc(self.buildEPGSearchEntry)

		if PartnerBoxIconsEnabled:
			# Partnerbox Clock Icons
			self.remote_clock_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock.png')
			self.remote_clock_add_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_add.png')
			self.remote_clock_pre_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_pre.png')
			self.remote_clock_post_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_post.png')
			self.remote_clock_prepost_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_prepost.png')

	def buildEPGSearchEntry(self, service, eventId, beginTime, duration, EventName):
		clock_pic = self.getPixmapForEntry(service, eventId, beginTime, duration)
		clock_pic_partnerbox = None
		# Partnerbox
		if PartnerBoxIconsEnabled:
			rec2=beginTime and (isInRemoteTimer(self,beginTime, duration, service))
			if rec2:
				clock_pic_partnerbox = getRemoteClockPixmap(self,service, beginTime, duration, eventId)
		else:
			rec2 = False
		r1 = self.weekday_rect
		r2 = self.datetime_rect
		r3 = self.descr_rect
		t = localtime(beginTime)
		serviceref = ServiceReference(service) # for Servicename
		res = [
			None, # no private data needed
			(eListboxPythonMultiContent.TYPE_TEXT, r1.x, r1.y, r1.w, r1.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, _(strftime("%a", t))),
			(eListboxPythonMultiContent.TYPE_TEXT, r2.x, r2.y, r2.w, r1.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, strftime("%e/%m, %-H:%M", t))
		]
		if clock_pic or clock_pic_partnerbox:
			if clock_pic and clock_pic_partnerbox:
				# Partnerbox and local
				res.extend((
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.x, r3.y, 21, 21, clock_pic),
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.x + 25, r3.y, 21, 21, clock_pic_partnerbox),
					(eListboxPythonMultiContent.TYPE_TEXT, r3.x + 50, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceref.getServiceName() + ": " + EventName)))
			elif clock_pic_partnerbox:
				# Partnerbox and local
				res.extend((
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.x, r3.y, 21, 21, clock_pic_partnerbox),
					(eListboxPythonMultiContent.TYPE_TEXT, r3.x + 25, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceref.getServiceName() + ": " + EventName)))
			else:
				res.extend((
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.x, r3.y, 21, 21, clock_pic),
					(eListboxPythonMultiContent.TYPE_TEXT, r3.x + 25, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceref.getServiceName() + ": " + EventName)))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.x, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, serviceref.getServiceName() + ": " + EventName))
		return res

# main class of plugin
class EPGSearch(EPGSelection):
	def __init__(self, session, *args):
		Screen.__init__(self, session)
		self.skinName = ["EPGSearch", "EPGSelection"]

		self.searchargs = args
		self.currSearch = ""
		self.longbuttonpressed = False

		# XXX: we lose sort begin/end here
		self["key_yellow"] = Button(_("New Search"))
		self["key_blue"] = Button(_("Add AutoTimer"))

# begin stripped copy of EPGSelection.__init__
		self.bouquetChangeCB = None
		self.serviceChangeCB = None
		self.ask_time = -1 #now
		self.closeRecursive = False
		self.saved_title = None
		self["Service"] = ServiceEvent()
		self["Event"] = Event()
		self.type = EPG_TYPE_SINGLE
		self.currentService=None
		self.zapFunc = None
		self.currch = None
		self.sort_type = 0
		self["key_red"] = Button(_("IMDb Search"))
		self["key_green"] = Button(_("Add timer"))
		self.key_green_choice = self.ADD_TIMER
		self.key_red_choice = self.EMPTY
		self["list"] = EPGSearchList(type = self.type, selChangedCB = self.onSelectionChanged, timer = session.nav.RecordTimer)
		self["actions"] = ActionMap(["EPGSelectActions", "OkCancelActions", "MenuActions", 'ColorActions', 'InfobarInstantRecord'],
			{
				"menu": self.menu,
				"cancel": self.closeScreen,
				"OK": self.epgsearchOK,
				"OKLong": self.epgsearchOKLong,
				"epg": self.Info,
				"info": self.Info,
				"timerAdd": self.timerAdd,
				"yellow": self.yellowButtonPressed,
				"yellowlong": self.showHistory,
				"blue": self.exportAutoTimer,
				"info": self.infoKeyPressed,
				"red": self.redButtonPressed,
				"nextBouquet": self.nextBouquet, # just used in multi epg yet
				"prevBouquet": self.prevBouquet, # just used in multi epg yet
				"nextService": self.nextService, # just used in single epg yet
				"prevService": self.prevService, # just used in single epg yet
				"ShortRecord": self.doRecordTimer,
				"LongRecord": self.doZapTimer,
			})

		self["actions"].csel = self
		self.onLayoutFinish.append(self.onCreate)
# end stripped copy of EPGSelection.__init__

		# Partnerbox
		if PartnerBoxIconsEnabled:
			EPGSelection.PartnerboxInit(self, False)

		self.refreshTimer = eTimer()
		self.refreshTimer.timeout.get().append(self.refreshData)

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

	def closeScreen(self):
		# Save our history
		config.plugins.epgsearch.save()
		EPGSelection.close(self)

	def epgsearchOK(self):
		cur = self["list"].getCurrent()
		self.currentService = cur[1]
		if config.epgselection.OK_enhanced.value == "Zap":
			self.zapTo()
		elif config.epgselection.OK_enhanced.value == "Zap + Exit":
			self.zap()
		else:
			self.eventSelected()

	def epgsearchOKLong(self):
		cur = self["list"].getCurrent()
		self.currentService = cur[1]
		if config.epgselection.OKLong_enhanced.value == "Zap":
			self.zapTo()
		elif config.epgselection.OKLong_enhanced.value == "Zap + Exit":
			self.zap()
		else:
			self.eventSelected()

	def yellowButtonPressed(self):
		self.session.openWithCallback(
			self.searchEPG,
			NTIVirtualKeyBoard,
			title = _("Enter text to search for")
		)

	def menu(self):
		options = [
			(_("Import from Timer"), self.importFromTimer),
			(_("Import from EPG"), self.importFromEPG),
			(_("Show search history"), self.showHistory),
		]

		if autoTimerAvailable:
			options.extend((
				(_("Import from AutoTimer"), self.importFromAutoTimer),
				(_("Save search as AutoTimer"), self.addAutoTimer),
			))
		if fileExists(resolveFilename(SCOPE_PLUGINS, "Extensions/IMDb/plugin.py")):
			options.append((_("Open selected in IMDb"), self.openImdb))
		options.append(
				(_("Setup"), self.setup)
		)

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
		cur = self['list'].getCurrent()
		if cur is None:
			return
		addAutotimerFromEvent(self.session, cur[0], cur[1])

	def openImdb(self):
		cur = self['list'].getCurrent()
		if cur is None:
			return
		try:
			from Plugins.Extensions.IMDb.plugin import IMDB
			self.session.open(IMDB, cur[0].getEventName())
		except ImportError as ie:
			pass

	def setup(self):
		self.session.open(EPGSearchSetup)

	def showHistory(self):
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
				_("No history"),
				type = MessageBox.TYPE_INFO
			)

	def searchEPGWrapper(self, ret):
		if ret:
			self.searchEPG(ret[1])

	def searchEPG(self, searchString = None, searchSave = True):
		if searchString:
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
			searchString = searchString.replace('\xc2\x86', '').replace('\xc2\x87', '')
			if encoding != 'UTF-8':
				try:
					searchString = searchString.decode('UTF-8').encode(encoding)
				except (UnicodeDecodeError, UnicodeEncodeError):
					pass

			# Search EPG, default to empty list
			epgcache = eEPGCache.getInstance() # XXX: the EPGList also keeps an instance of the cache but we better make sure that we get what we want :-)
			ret = epgcache.search(('RIBDT', 1000, eEPGCache.PARTIAL_TITLE_SEARCH, searchString, eEPGCache.NO_CASE_CHECK)) or []
			ret.sort(key=itemgetter(2)) # sort by time

			# Update List
			l = self["list"]
			l.recalcEntrySize()
			l.list = ret
			l.l.setList(ret)

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

class EPGSearchEPGSelection(EPGSelection):
	def __init__(self, session, ref, openPlugin):
		EPGSelection.__init__(self, session, ref)
		self.skinName = ["EPGSearchEPGSelection", "EPGSelection"]
		self["key_green"].text = _("Search")
		self.openPlugin = openPlugin

	def infoKeyPressed(self):
		self.timerAdd()

	def timerAdd(self):
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

