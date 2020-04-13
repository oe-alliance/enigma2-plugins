# for localized messages
from . import _, allowShowOrbital, getOrbposConfList

from enigma import eEPGCache, eTimer, eServiceReference, eServiceCenter, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, eListboxPythonMultiContent, getDesktop, getBestPlayableServiceReference
import NavigationInstance

from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from Tools.Alternatives import GetWithAlternative
from ServiceReference import ServiceReference

from EPGSearchSetup import EPGSearchSetup
from Screens.InfoBar import MoviePlayer
from Screens.ChannelSelection import ChannelSelection, SimpleChannelSelection, MODE_RADIO
from Screens.ChoiceBox import ChoiceBox
from Screens.EpgSelection import EPGSelection
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.Button import Button
from Components.Label import Label
from Components.config import config
from Components.EpgList import EPGList, Rect, EPG_TYPE_SINGLE, EPG_TYPE_MULTI
from Components.TimerList import TimerList
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.Event import Event

from Tools.BoundFunction import boundFunction

from time import localtime, strftime
from operator import itemgetter
from collections import defaultdict

from skin import parameters as skinparameter

# Partnerbox installed and icons in epglist enabled?
try:
	from Plugins.Extensions.Partnerbox.PartnerboxEPGList import isInRemoteTimer, getRemoteClockPixmap
	from Plugins.Extensions.Partnerbox.plugin import showPartnerboxIconsinEPGList
	PartnerBoxIconsEnabled = showPartnerboxIconsinEPGList()
except ImportError:
	PartnerBoxIconsEnabled = False

# AutoTimer installed?
try:
	from Plugins.Extensions.AutoTimer.AutoTimerEditor import addAutotimerFromEvent, addAutotimerFromSearchString
	autoTimerAvailable = True
except ImportError:
	autoTimerAvailable = False

rootbouquet_tv = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.tv" ORDER BY bouquet'
rootbouquet_radio = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.radio" ORDER BY bouquet'

# Modified EPGSearchList with support for PartnerBox
class EPGSearchList(EPGList):
	def __init__(self, type=EPG_TYPE_SINGLE, selChangedCB=None, timer=None):
		EPGList.__init__(self, type, selChangedCB, timer)
		self.listSizeWidth = None
		self.screenwidth = getDesktop(0).size().width()
		if self.screenwidth and self.screenwidth == 1920:
			self.posx, self.posy , self.picx, self.picy, self.gap = skinparameter.get("EpgListIcon", (2,13,25,25,2))
		else:
			self.posx, self.posy , self.picx, self.picy, self.gap = skinparameter.get("EpgListIcon", (1,11,23,23,1))
		self.l.setBuildFunc(self.buildEPGSearchEntry)

		if PartnerBoxIconsEnabled:
			# Partnerbox Clock Icons
			self.partnerbox_clocks = [
				LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/EPGSearch/icons/epgclock_add.png")),
				LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/EPGSearch/icons/epgclock_pre.png")),
				LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/EPGSearch/icons/epgclock.png")),
				LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/EPGSearch/icons/epgclock_prepost.png")),
				LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/EPGSearch/icons/epgclock_post.png")),
				LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/EPGSearchicons/epgclock_add.png"))
			]

	def buildEPGSearchEntry(self, service, eventId, beginTime, duration, EventName):
		lsw = self.l.getItemSize().width()
		if self.listSizeWidth != lsw:  # recalc size if scrollbar is shown
			self.recalcEntrySize()

		r1 = self.weekday_rect
		r2 = self.datetime_rect
		r3 = self.orbpos_rect
		r4 = self.descr_rect

		if eventId < 0:
			res = [
				None,  # no private data needed
				(eListboxPythonMultiContent.TYPE_TEXT, r1.x, r1.y, r4.x + r4.w - r1.x, r1.h, 0, RT_HALIGN_CENTER | RT_VALIGN_CENTER, EventName)
			]
			return res

		# Pics in right-to-left order
		pics = []
		# Partnerbox
		if PartnerBoxIconsEnabled:
			rec2 = beginTime and (isInRemoteTimer(self, beginTime, duration, service))
			if rec2:
				clock_pic_partnerbox = getRemoteClockPixmap(self, service, beginTime, duration, eventId)
				if clock_pic_partnerbox:
					pics.append(self.clocks[clock_pic_partnerbox])
		clock_pic = self.getPixmapForEntry(service, eventId, beginTime, duration)
		if clock_pic:
			pics.append(self.clocks[clock_pic])
		if getattr(self, "wasEntryAutoTimer", False) and hasattr(self, "autotimericon"):
			pics.append(self.autotimericon)
		# Timer icons for timers set by IceTV (icetv.com.au)
		if getattr(self, "wasEntryIceTV", False) and hasattr(self, "icetvicon"):
			pics.append(self.icetvicon)

		t = localtime(beginTime)
		serviceref = ServiceReference(service)  # for Servicename and orbital position
		width = r4.x + r4.w
		if hasattr(self, "showend"):
			et = localtime(beginTime + duration)
			if hasattr(config.usage, "time"):
				split = int(r2.w * 0.55)
				res = [
					None,  # no private data needed
					(eListboxPythonMultiContent.TYPE_TEXT, r1.x, r1.y, r1.w, r1.h, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, strftime(config.usage.date.dayshort.value, t)),
					(eListboxPythonMultiContent.TYPE_TEXT, r2.x, r2.y, split, r2.h, 0, RT_HALIGN_RIGHT | RT_VALIGN_CENTER, strftime(config.usage.time.short.value + " -", t)),
					(eListboxPythonMultiContent.TYPE_TEXT, r2.x + split, r2.y, r2.w - split, r2.h, 0, RT_HALIGN_RIGHT | RT_VALIGN_CENTER, strftime(config.usage.time.short.value, et))
				]
			else:
				res = [
					None,  # no private data needed
					(eListboxPythonMultiContent.TYPE_TEXT, r1.x, r1.y, r1.w, r1.h, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, strftime("%a %d %b", t)),
					(eListboxPythonMultiContent.TYPE_TEXT, r2.x, r2.y, r2.w, r2.h, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, "%s ~ %s" % (strftime("%H:%M", t), strftime("%H:%M", et)))
				]
		else:
			if hasattr(config.usage, "time"):
				datetime = "%s, %s" % (strftime(config.usage.date.short.value, t), strftime(config.usage.time.short.value, t))
			else:
				datetime = strftime(_("%e/%m, %H:%M"), t)
			res = [
				None,  # no private data needed
				(eListboxPythonMultiContent.TYPE_TEXT, r1.x, r1.y, r1.w, r1.h, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, strftime("%a", t)),
				(eListboxPythonMultiContent.TYPE_TEXT, r2.x, r2.y, r2.w, r2.h, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, datetime)
			]
		if r3.w:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.x, r3.y, r3.w, r3.h, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, self.getOrbitalPos(serviceref)))
		picwidth = 0
		for pic in pics:
			if picwidth:
				picwidth += (self.picx + self.gap)
			else:
				picwidth = self.picx + self.posx
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, width - picwidth, (r4.h / 2 - self.posy), self.picx, self.picy, pic))
		if picwidth:
			picwidth += (self.gap*2)
		res.append((eListboxPythonMultiContent.TYPE_TEXT, r4.x, r4.y, r4.w - picwidth, r4.h, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, serviceref.getServiceName() + ": " + EventName))
		return res

	def recalcEntrySize(self):
		super(EPGSearchList, self).recalcEntrySize()
		self.listSizeWidth = self.l.getItemSize().width()
		width = self.descr_rect.x + self.descr_rect.w
		if allowShowOrbital and config.plugins.epgsearch.showorbital.value:
			fontSize = self.eventFontSizeSingle + config.epgselection.enhanced_eventfs.value
			orbitalPosWidth = int(fontSize * 4.4)
		else:
			orbitalPosWidth = 0

		self.orbpos_rect = Rect(self.descr_rect.x, self.descr_rect.y, orbitalPosWidth, self.descr_rect.h)
		orbpos_r = self.orbpos_rect.x + self.orbpos_rect.w
		self.descr_rect = Rect(orbpos_r, self.orbpos_rect.y, width - orbpos_r, self.orbpos_rect.h)

	def getOrbitalPos(self, ref):
		refstr = None
		if hasattr(ref, "sref"):
			refstr = str(ref.sref)
		else:
			refstr = str(ref)
		refstr = refstr and GetWithAlternative(refstr)
		if "%3a//" in refstr:
			return "%s" % _("Stream")
		op = int(refstr.split(":", 10)[6][:-4] or "0", 16)
		if op == 0xeeee:
			return "%s" % _("DVB-T")
		if op == 0xffff:
			return "%s" % _("DVB-C")
		direction = "E"
		if op > 1800:
			op = 3600 - op
			direction = "W"
		return ("%d.%d\xc2\xb0%s") % (op // 10, op % 10, direction)

# main class of plugin
class EPGSearch(EPGSelection):

	# Ignore these flags in services from bouquets
	SERVICE_FLAG_MASK = ~(eServiceReference.shouldSort | eServiceReference.hasSortKey | eServiceReference.sort1)

	@property
	def firstSearch(self):
		return hasattr(self, "searchargs")

	def __init__(self, session, *args, **kwargs):
		Screen.__init__(self, session)
		if not isinstance(self.skinName, list):
			self.skinName = [self.skinName]
		self.skinName.append("EPGSelection")
		if isinstance(self, HelpableScreen):
			HelpableScreen.__init__(self)

		self.searchargs = args
		self.currSearch = ""
		self.longbuttonpressed = False

		# XXX: we lose sort begin/end here
		self["key_yellow"] = Button(_("New Search"))
		self["key_blue"] = Button(_("Add AutoTimer"))

		# begin stripped copy of EPGSelection.__init__
		self.ChoiceBoxDialog = None
		self.bouquetChangeCB = None
		self.serviceChangeCB = None
		self.ask_time = -1  # now
		self.closeRecursive = False
		self.saved_title = None
		self.lastAsk = None
		self["Service"] = ServiceEvent()
		self["Event"] = Event()
		self["number"] = Label()
		self["number"].hide()
		self.type = EPG_TYPE_SINGLE
		self.currentService = None
		self.zapFunc = None
		self.currch = None
		self.sort_type = 0
		self.eventviewDialog = None
		self["key_red"] = Button(_("IMDb Search"))
		self["key_green"] = Button(_("Add Timer"))
		self.key_green_choice = self.ADD_TIMER
		self.key_red_choice = self.EMPTY
		self["list"] = EPGSearchList(type=self.type, selChangedCB=self.onSelectionChanged, timer=session.nav.RecordTimer)

		self["dialogactions"] = HelpableActionMap(self, "WizardActions", {
			"back": (self.closeChoiceBoxDialog, _("Close dialog")),
		}, -1)
		self["dialogactions"].csel = self
		self["dialogactions"].setEnabled(False)

		self["okactions"] = HelpableActionMap(self, "OkCancelActions", {
			"cancel": (self.closeScreen, _("Exit EPG Search")),
			"OK": (self.epgsearchOK, _("Zap to channel")),
			"OKLong": (self.epgsearchOKLong, _("Show detailed event information"))
		}, -1)
		self["okactions"].csel = self

		self["colouractions"] = HelpableActionMap(self, "ColorActions", {
			"red": (self.redButtonPressed, _("IMDB search for highlighted event")),
			"green": (self.timerAdd, _("Add/remove/edit timer for highlighted event")),
			"yellow": (self.yellowButtonPressed, _("Enter new search")),
			"yellowlong": (self.showHistory, _("Show search history")),
			"blue": (self.exportAutoTimer, _("Add an AutoTimer for highlighted event")),
			"bluelong": (self.blueButtonPressedLong, _("Show AutoTimer list"))
		}, -1)
		self["colouractions"].csel = self

		self["recordingactions"] = HelpableActionMap(self, "InfobarInstantRecord", {
			"ShortRecord": (self.doRecordTimer, _("Add a record timer for highlighted event")),
			"LongRecord": (self.doZapTimer, _("Add a zap timer for highlighted event"))
		}, -1)
		self["recordingactions"].csel = self

		self["epgactions"] = HelpableActionMap(self, "EPGSelectActions", {
			"nextBouquet": (self.nextPage, _("Move down a page")),
			"prevBouquet": (self.prevPage, _("Move up a page")),
			"nextService": (self.prevPage, _("Move up a page")),
			"prevService": (self.nextPage, _("Move down a page")),
			"epg": (self.Info, _("Show detailed event information")),
			"info": (self.Info, _("Show detailed event information")),
			"infolong": (self.infoKeyPressed, _("Show detailed event information")),
			"menu": (self.menu, _("Setup menu"))
		}, -1)
		self["epgactions"].csel = self

		self["epgcursoractions"] = HelpableActionMap(self, "DirectionActions", {
			"left": (self.prevPage, _("Move up a page")),
			"right": (self.nextPage, _("Move down a page")),
			"up": (self.moveUp, _("Move up")),
			"down": (self.moveDown, _("Move down"))
		}, -1)
		self["epgcursoractions"].csel = self

		self.openHistory = kwargs.get("openHistory", False)

		self.onLayoutFinish.append(self.onCreate)
		# end stripped copy of EPGSelection.__init__

		# Partnerbox
		if PartnerBoxIconsEnabled:
			EPGSelection.PartnerboxInit(self, False)

		self.refreshTimer = eTimer()
		self.refreshTimer.callback.append(self.refreshlist)

		self.startTimer = eTimer()
		self.startTimer.callback.append(self.startUp)
		self.startTimer.start(10, 1)

		self.searchStartTimer = eTimer()

		# Hook up actions for yttrailer if installed
		try:
			from Plugins.Extensions.YTTrailer.plugin import baseEPGSelection__init__
		except ImportError as ie:
			pass
		else:
			if baseEPGSelection__init__ is not None:
				self["trailerActions"] = ActionMap(["InfobarActions", "InfobarTeletextActions"], {
					"showTv": self.showTrailer,
					"showRadio": self.showTrailerList,
					"startTeletext": self.showConfig
				})

	def onCreate(self):
		self.setTitle(_("EPG Search"))

		# Partnerbox
		if PartnerBoxIconsEnabled:
			EPGSelection.GetPartnerboxTimerlist(self)

	def startUp(self):
		self.refreshlist()
		del self.startTimer

	def refreshlist(self):
		self.refreshTimer.stop()
		if self.firstSearch and self.openHistory:
			self.showHistory()
			return
		if self.firstSearch and self.searchargs:
			self.searchEPG(*self.searchargs)
		elif self.currSearch:
			self.searchEPG(self.currSearch, lastAsk=self.lastAsk)
		else:
			l = self["list"]
			l.instance.setSelectionEnable(True)
			l.list = []
			l.l.setList(l.list)
			l.recalcEntrySize()

	def closeScreen(self):
		# Save our history
		config.plugins.epgsearch.save()
		self.searchStartTimer.stop()
		EPGSelection.close(self)

	def closeChoiceBoxDialog(self):
		if "dialogactions" in self:
			self["dialogactions"].setEnabled(False)
		if self.ChoiceBoxDialog:
			self.ChoiceBoxDialog["actions"].execEnd()
			self.session.deleteDialog(self.ChoiceBoxDialog)
		if "okactions" in self:
			self["okactions"].setEnabled(True)
		if "epgcursoractions" in self:
			self["epgcursoractions"].setEnabled(True)
		if "colouractions" in self:
			self["colouractions"].setEnabled(True)
		if "recordingactions" in self:
			self["recordingactions"].setEnabled(True)
		if "epgactions" in self:
			self["epgactions"].setEnabled(True)
		if "input_actions" in self:
			self["input_actions"].setEnabled(True)

	def epgsearchOK(self):
		cur = self["list"].getCurrent()
		self.currentService = cur[1]
		if self.currentService:
			self.zap()

	def epgsearchOKLong(self):
		self.eventSelected()

	def zap(self):
		def serviceInBouquet(bouquet, serviceHandler, ref):
			servicelist = serviceHandler.list(bouquet)
			if servicelist is not None:
				serviceIterator = servicelist.getNext()
				while serviceIterator.valid():
					if ref == serviceIterator:
						# Servicerefs from the EPG don't (can't) have the
						# channel number set
						ref.setChannelNum(serviceIterator.getChannelNum())
						return True
					serviceIterator = servicelist.getNext()
			return False

		ChannelSelectionInstance = ChannelSelection.instance
		foundService = False
		if ChannelSelectionInstance:
			self.service_types = ChannelSelectionInstance.service_types
			serviceHandler = eServiceCenter.getInstance()
			bqrootstr = ChannelSelectionInstance.bouquet_rootstr
			if config.usage.multibouquet.value:
				rootbouquet = eServiceReference(bqrootstr)
				currentBouquet = ChannelSelectionInstance.getRoot()
				for searchCurrent in (True, False):
					bouquet = eServiceReference(bqrootstr)
					bouquetlist = serviceHandler.list(bouquet)
					if bouquetlist is not None:
						bouquet = bouquetlist.getNext()
						while bouquet.valid():
							if bouquet.flags & (eServiceReference.isDirectory | eServiceReference.isInvisible) == eServiceReference.isDirectory and (currentBouquet is None or (currentBouquet == bouquet) == searchCurrent):
								ChannelSelectionInstance.clearPath()
								ChannelSelectionInstance.setRoot(bouquet)
								foundService = serviceInBouquet(bouquet, serviceHandler, self.currentService.ref)
								if foundService:
									break
							bouquet = bouquetlist.getNext()
						if foundService:
							break
			else:
				rootbouquet = eServiceReference(bqrootstr)
				bouquet = eServiceReference(bqrootstr)
				if bouquet.valid() and bouquet.flags & (eServiceReference.isDirectory | eServiceReference.isInvisible) == eServiceReference.isDirectory:
					foundService = serviceInBouquet(bouquet, serviceHandler, self.currentService.ref)

		if foundService:
			ChannelSelectionInstance.enterPath(rootbouquet)
			ChannelSelectionInstance.enterPath(bouquet)
			ChannelSelectionInstance.saveRoot()
			ChannelSelectionInstance.saveChannel(self.currentService.ref)
			ChannelSelectionInstance.addToHistory(self.currentService.ref)
			NavigationInstance.instance.playService(self.currentService.ref)
		self.close()

	def yellowButtonPressed(self):
		self.session.openWithCallback(self.searchEPG, VirtualKeyBoard, title=_("Enter text to search for"), text=self.currSearch)

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
		options.append((_("Setup"), self.setup))

		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_("EPG Search setup"), list=options)

	def menuCallback(self, ret):
		ret and ret[1]()

	def importFromTimer(self):
		self.session.openWithCallback(self.searchEPG, EPGSearchTimerImport)

	def importFromEPG(self):
		self.session.openWithCallback(self.searchEPG, EPGSearchChannelSelection)

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
			self.session.open(MessageBox, _("Could not read AutoTimer timer list: %s") % e, type=MessageBox.TYPE_ERROR)
		else:
			# Fetch match strings
			# XXX: we could use the timer title as description
			options = [(x.match, x.match) for x in autotimer.getTimerList()]

			self.session.openWithCallback(self.searchEPGWrapper, ChoiceBox, title=_("Select text to search for"), list=options)
		finally:
			# Remove instance if there wasn't one before
			if removeInstance:
				autotimer = None

	def addAutoTimer(self):
		addAutotimerFromSearchString(self.session, self.currSearch)

	def exportAutoTimer(self):
		cur = self["list"].getCurrent()
		if cur is None:
			return
		addAutotimerFromEvent(self.session, cur[0], cur[1])

	def openImdb(self):
		cur = self["list"].getCurrent()
		if cur is None:
			return
		try:
			from Plugins.Extensions.IMDb.plugin import IMDB
			self.session.open(IMDB, cur[0].getEventName())
		except ImportError as ie:
			pass

	def getReSearchSetings(self):
		return (
			config.plugins.epgsearch.scope.value,
			config.plugins.epgsearch.search_type.value,
			config.plugins.epgsearch.search_case.value,
			config.plugins.epgsearch.enableorbpos.value,
			config.plugins.epgsearch.invertorbpos.value,
			allowShowOrbital and config.plugins.epgsearch.showorbital.value,
		) + tuple(set((orbposItem.orbital_position for orbposItem in getOrbposConfList())))

	def setup(self):
		self.__reSearchSettings = self.getReSearchSetings()
		self.session.openWithCallback(self.setupCallback, EPGSearchSetup)

	def setupCallback(self, *args):
		if (
			self.__reSearchSettings != self.getReSearchSetings() and (
				config.plugins.epgsearch.scope.value != "ask" or
				config.plugins.epgsearch.scope.value == "ask" and self.lastAsk
			) or
			self.firstSearch
		):
			self.refreshlist()
		del self.__reSearchSettings

	def showHistory(self):
		self._trimHistory()

		options = [(x, x) for x in config.plugins.epgsearch.history.value]

		if options:
			self.session.openWithCallback(self.searchEPGWrapper, ChoiceBox, title=_("Select text to search for"), list=options)
		else:
			self.session.open(MessageBox, _("No history"), type=MessageBox.TYPE_INFO)

	def _trimHistory(self):
		history = config.plugins.epgsearch.history.value
		maxLen = config.plugins.epgsearch.history_length.value
		if len(history) > maxLen:
			del history[maxLen:]

	def searchEPGWrapper(self, ret):
		if ret:
			self.searchEPG(ret[1])

	def searchEPG(self, searchString=None, searchSave=True, lastAsk=None):
		if isinstance(searchString, basestring) and searchString:
			if searchSave:
				# Maintain history
				history = config.plugins.epgsearch.history.value
				if searchString not in history:
					history.insert(0, searchString)
					self._trimHistory()
				else:
					history.remove(searchString)
					history.insert(0, searchString)

			if config.plugins.epgsearch.scope.value == "ask" and lastAsk is None:
				list = [
					(_("All services"), "all"),
					(_("All bouquets"), "allbouquets"),
					(_("Current bouquet"), "currentbouquet"),
					(_("Current service"), "currentservice"),
					(_("Setup"), "setup"),
				]
				selection = next((i for i, sel in enumerate(list) if sel[1] == config.plugins.epgsearch.defaultscope.value), 0)
				self.session.openWithCallback(boundFunction(self.searchEPGAskCallback, searchString), ChoiceBox, title=_("Search in..."), list=list, selection=selection)
			else:
				self.startSearchEPG(searchString, lastAsk if lastAsk is not None else config.plugins.epgsearch.scope.value)

	def searchEPGAskCallback(self, searchString, ret):
		if ret:
			if ret[1] == "setup":
				self.lastAsk = None
				self.setup()
			else:
				self.lastAsk = ret[1]
				self.startSearchEPG(searchString, ret[1])
		else:
			if self.firstSearch:
				# Don't save abandoned initial search,
				# so don't use closeScreen()
				EPGSelection.close(self)

	def startSearchEPG(self, searchString, searchScope):
		l = self["list"]
		l.instance.setSelectionEnable(False)
		# Match an RIBDT search for dummy entries
		invalSref = eServiceReference().toString()
		searching = [(invalSref, -1, -1, -1, "")] * (config.epgselection.enhanced_itemsperpage.value / 2)
		searching.append((invalSref, -1, -1, -1, _("Searching...")))
		l.list = searching
		l.l.setList(searching)
		l.recalcEntrySize()

		del self.searchStartTimer.callback[:]
		self.searchStartTimer.callback.append(lambda: self.doSearchEPG(searchString, searchScope))
		self.searchStartTimer.start(1, 1)

	def doSearchEPG(self, searchString, searchScope):
		if self.firstSearch:
			del self.searchargs

		self.currSearch = searchString

		# Workaround to allow search for umlauts if we know the encoding (pretty bad, I know...)
		encoding = config.plugins.epgsearch.encoding.value
		searchString = searchString.replace("\xc2\x86", "").replace("\xc2\x87", "")
		if encoding != "UTF-8":
			try:
				searchString = searchString.decode("UTF-8").encode(encoding)
			except (UnicodeDecodeError, UnicodeEncodeError):
				pass

		search_type = {
			"partial": eEPGCache.PARTIAL_TITLE_SEARCH,
			"exact": eEPGCache.EXAKT_TITLE_SEARCH,
			"start": eEPGCache.START_TITLE_SEARCH,
		}.get(config.plugins.epgsearch.search_type.value, eEPGCache.PARTIAL_TITLE_SEARCH)
		search_case = {
			"insensitive": eEPGCache.NO_CASE_CHECK,
			"sensitive": eEPGCache.CASE_CHECK,
		}.get(config.plugins.epgsearch.search_case.value, eEPGCache.NO_CASE_CHECK)
		searchFilter = {
			"all": self.allServiceRefMap,
			"allbouquets": self.allBouquetServiceRefMap,
			"currentbouquet": self.currentBouquetServiceRefMap,
			"currentservice": self.currentServiceServiceRefMap,
		}.get(searchScope, self.allServiceRefMap)()

		if len(searchFilter) > 5:
			runFilter = self._filteredSearchByName
		else:
			runFilter = self._filteredSearchByService

		ret = runFilter("RIBDT", 1000, search_type, searchString, search_case, searchFilter)

		ret.sort(key=itemgetter(2))  # sort by time

		# Update List
		l = self["list"]
		l.instance.setSelectionEnable(True)
		l.list = ret
		l.l.setList(ret)
		l.recalcEntrySize()

	def _filteredSearchByName(self, args, maxRet, search_type, searchString, search_case, searchFilter):
		srefEntry = args.index("R")
		if srefEntry < 0:
			return []
		eventIdEntry = args.index("I")
		if eventIdEntry < 0:
			return []

		ret = eEPGCache.getInstance().search((args, maxRet, search_type, searchString, search_case)) or []

		newRet = []
		triplesCache = {}
		processed = set()
		for event in ret:
			srefStr = event[srefEntry]
			if srefStr in triplesCache:
				triple = triplesCache[srefStr]
			else:
				sref = eServiceReference(srefStr)
				triple = tuple(sref.getUnsignedData(i) for i in range(1, 4))
				triplesCache[srefStr] = triple
			processing = triple + (event[eventIdEntry], )
			if processing not in processed:
				event1 = event[1:]
				newRet += ((newSrefStr,) + event1 for newSrefStr in searchFilter.get(triple, []))
				if len(newRet) >= maxRet:
					del newRet[maxRet:]
					break
				processed.add(processing)
		return newRet

	def _filteredSearchByService(self, args, maxRet, search_type, searchString, search_case, searchFilter):
		titleEntry = args.index("T")
		if titleEntry < 0:
			return []

		searchFilter = reduce(lambda acc, val: acc.union(val), searchFilter.itervalues(), set())

		partialMatchFunc = lambda s: searchString in s
		matchFunc = {
			eEPGCache.PARTIAL_TITLE_SEARCH: partialMatchFunc,
			eEPGCache.EXAKT_TITLE_SEARCH: lambda s: searchString == s,
			eEPGCache.START_TITLE_SEARCH: lambda s: s.startswith(searchString),
		}.get(search_type, partialMatchFunc)
		if search_case == eEPGCache.CASE_CHECK:
			caseMatchFunc = matchFunc
		else:
			searchString = searchString.lower()
			caseMatchFunc = lambda s: matchFunc(s.lower())

		ret = []
		for sref in self._sourceFilter(searchFilter):
			lookup = [args, (sref, 0, 0, -1)]
			# Enumerate EPG for service, defaulting to empty list
			# and apply search, accumulating results
			ret += [event for event in eEPGCache.getInstance().lookupEvent(lookup) or [] if caseMatchFunc(event[titleEntry])]
			if len(ret) > maxRet:
				del ret[maxRet:]
				break
		return ret

	def _processBouquetServiceRefMap(self, tempServiceRefMap):
		serviceHandler = eServiceCenter.getInstance()
		bouquetServiceRefMap = defaultdict(set)
		for srefId, srefDict in tempServiceRefMap.iteritems():
			if len(srefDict) > 1 and "" in srefDict:
				noName = srefDict[""]
				info = serviceHandler.info(noName)
				name = info and info.getName(noName) or ""
				if name and name in srefDict:
					del srefDict[""]
			bouquetServiceRefMap[srefId[2:5]].update(sref.toString() for sref in srefDict.itervalues())
		return bouquetServiceRefMap

	def _addBouquetTempServiceRefMap(self, bouquet, tempServiceRefMap):
		serviceHandler = eServiceCenter.getInstance()
		servicelist = serviceHandler.list(bouquet)
		if servicelist is not None:
			for sref in servicelist.getContent("R"):
				if sref.flags & eServiceReference.isGroup:
					sref = getBestPlayableServiceReference(sref, eServiceReference())
				if sref and not (sref.flags & self.SERVICE_FLAG_MASK):
					# Unroll tuple(sref.getUnsignedData(i) for i in range(8))
					# for extra speed...
					srefId = (sref.type, sref.getUnsignedData(0), sref.getUnsignedData(1), sref.getUnsignedData(2), sref.getUnsignedData(3), sref.getUnsignedData(4), sref.getUnsignedData(5), sref.getUnsignedData(6), sref.getUnsignedData(7), sref.getPath())
					tempServiceRefMap[srefId][sref.getName()] = sref

	def _allBouquetTempServiceRefMap(self, tempServiceRefMap):
		serviceHandler = eServiceCenter.getInstance()
		ChannelSelectionInstance = ChannelSelection.instance
		if ChannelSelectionInstance and ChannelSelectionInstance.mode == MODE_RADIO:
			bqrootstr = rootbouquet_radio
		else:
			bqrootstr = rootbouquet_tv
		rootbouquet = eServiceReference(bqrootstr)
		bouquetlist = serviceHandler.list(rootbouquet)
		if bouquetlist is not None:
			bouquet = bouquetlist.getNext()
			while bouquet.valid():
				if bouquet.flags & (eServiceReference.isDirectory | eServiceReference.isInvisible) == eServiceReference.isDirectory:
					self._addBouquetTempServiceRefMap(bouquet, tempServiceRefMap)
				bouquet = bouquetlist.getNext()

	def allServiceRefMap(self):
		tempServiceRefMap = defaultdict(dict)
		self._allBouquetTempServiceRefMap(tempServiceRefMap)
		ChannelSelectionInstance = ChannelSelection.instance
		if ChannelSelectionInstance:
			lamedbServices = eServiceReference(ChannelSelectionInstance.service_types)
			self._addBouquetTempServiceRefMap(lamedbServices, tempServiceRefMap)
		return self._processBouquetServiceRefMap(tempServiceRefMap)

	def allBouquetServiceRefMap(self):
		tempServiceRefMap = defaultdict(dict)
		self._allBouquetTempServiceRefMap(tempServiceRefMap)
		return self._processBouquetServiceRefMap(tempServiceRefMap)

	def currentBouquetServiceRefMap(self):
		tempServiceRefMap = defaultdict(dict)
		ChannelSelectionInstance = ChannelSelection.instance
		if ChannelSelectionInstance:
			bouquet = ChannelSelectionInstance.getRoot()
			self._addBouquetTempServiceRefMap(bouquet, tempServiceRefMap)
		return self._processBouquetServiceRefMap(tempServiceRefMap)

	def currentServiceServiceRefMap(self):
		service = MoviePlayer.instance and MoviePlayer.instance.lastservice or NavigationInstance.instance.getCurrentlyPlayingServiceReference()
		if not service or not service.valid:
			return None
		serviceRefMap = defaultdict(set)
		triple = tuple(service.getUnsignedData(i) for i in range(1, 4))
		serviceRefMap[triple] = set((service.toString(), ))
		return serviceRefMap

	def _sourceFilter(self, serviceRefSet):
		if not config.plugins.epgsearch.enableorbpos.value:
			return serviceRefSet

		filtSet = set((orbposItem.orbital_position << 16 for orbposItem in getOrbposConfList()))

		if not filtSet:
			return serviceRefSet

		filtServiceRefSet = set()
		include = config.plugins.epgsearch.invertorbpos.value == _("include")
		for srefstr in serviceRefSet:
			sref = eServiceReference(srefstr)
			if (sref.getUnsignedData(4) in filtSet) == include:
				filtServiceRefSet.add(srefstr)
		return filtServiceRefSet

class EPGSearchTimerImport(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = [self.skinName, "TimerEditList"]

		self.list = []
		self.fillTimerList()

		self["timerlist"] = TimerList(self.list)
		self["description"] = Label()

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {
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
		l.sort(key=lambda x: x[0].begin)

	def search(self):
		cur = self["timerlist"].getCurrent()
		if cur:
			self.close(cur.name)

	def cancel(self):
		self.close(None)

class EPGSearchChannelSelection(SimpleChannelSelection):
	def __init__(self, session):
		SimpleChannelSelection.__init__(self, session, _("Channel Selection"))
		self.skinName = [self.skinName, "SimpleChannelSelection"]

		self["ChannelSelectEPGActions"] = ActionMap(["ChannelSelectEPGActions"], {
			"showEPGList": self.channelSelected
		})

	def channelSelected(self):
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.enterPath(ref)
		elif not (ref.flags & eServiceReference.isMarker):
			info = eServiceCenter.getInstance().info(ref)
			evt = info and info.getEvent(ref, -1)
			event_id = evt and evt.getEventId() or None
			self.session.openWithCallback(self.epgClosed, EPGSearchEPGSelection, ref, False, eventid=event_id)

	def epgClosed(self, ret=None):
		if ret:
			self.close(ret)

class EPGSearchEPGSelection(EPGSelection):
	def __init__(self, session, ref, openPlugin, eventid=None):
		EPGSelection.__init__(self, session, ref.toString(), eventid=eventid)
		if not isinstance(self.skinName, list):
			self.skinName = [self.skinName]
		self.skinName.append("EPGSelection")
		self["key_green"].text = _("Search")
		self.openPlugin = openPlugin

	def infoKeyPressed(self):
		self.greenButtonPressed()

	def timerAdd(self):
		self.greenButtonPressed()

	def greenButtonPressed(self):
		self.closeEventViewDialog()
		from Screens.InfoBar import InfoBar
		InfoBarInstance = InfoBar.instance
		if not InfoBarInstance.LongButtonPressed:
			cur = self["list"].getCurrent()
			evt = cur[0]
			sref = cur[1]
			if not evt:
				return

			if self.openPlugin:
				self.session.open(EPGSearch, evt.getEventName())
			else:
				self.close(evt.getEventName())

	def onSelectionChanged(self):
		super(EPGSearchEPGSelection, self).onSelectionChanged()
		self["key_green"].setText(_("Search"))
