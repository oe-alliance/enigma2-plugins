from enigma import eEPGCache, eServiceReference

from Screens.ChannelSelection import SimpleChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.EpgSelection import EPGSelection
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config
from Components.TimerList import TimerList

from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.Sources.ServiceEvent import ServiceEvent
from Components.Sources.Event import Event
from Components.EpgList import EPGList, EPG_TYPE_SINGLE, EPG_TYPE_MULTI
from ServiceReference import ServiceReference
from Components.GUIComponent import GUIComponent
from enigma import eEPGCache, eListbox, eListboxPythonMultiContent, gFont, \
	RT_HALIGN_LEFT, RT_HALIGN_RIGHT
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_SKIN_IMAGE
from time import localtime, time


# Partnerbox installed?
try:
	from Plugins.Extensions.Partnerbox.PartnerboxEPGList import isInRemoteTimer, getRemoteClockPixmap
	from Plugins.Extensions.Partnerbox.PartnerboxFunctions import  SetPartnerboxTimerlist, isInTimerList, sendPartnerBoxWebCommand, FillE1TimerList, FillE2TimerList
	import Plugins.Extensions.Partnerbox.PartnerboxFunctions as partnerboxfunctions
	from Plugins.Extensions.Partnerbox.PartnerboxSetup import PartnerboxEntriesListConfigScreen
	PartnerBoxInstalled = True
except:
	PartnerBoxInstalled = False

#AutoTimer installed?
try:
	from Plugins.Extensions.AutoTimer.AutoTimerEditor import addAutotimerFromEvent
	AutoTimerInstalled = True
except:
	AutoTimerInstalled = False

baseEPGSelection__init__ = None
def EPGSelectionInit():
	global baseEPGSelection__init__
	if baseEPGSelection__init__ is None:
		baseEPGSelection__init__ = EPGSelection.__init__
	EPGSelection.__init__ = EPGSelection__init__
	EPGSelection.bluePressed = bluePressed

def EPGSelection__init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None):
	baseEPGSelection__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB)
	if self.type != EPG_TYPE_MULTI:
		self["epgsearch_actions"] = ActionMap(["EPGSelectActions"],
				{
					"blue": self.bluePressed,
				})
		self["key_blue"].setText(_("EPG Search"))

def bluePressed(self):
	try: 	# EPGList could be empty
		cur = self["list"].getCurrent()
		event = cur[0]
		name = event.getEventName()
	except:
		name = ''
	self.session.open(EPGSearch,name , False)

class EPGSearchList(EPGList):
	def __init__(self, type=EPG_TYPE_SINGLE, selChangedCB=None, timer = None):
		self.days = (_("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun"))
		self.timer = timer
		self.onSelChanged = [ ]
		if selChangedCB is not None:
			self.onSelChanged.append(selChangedCB)
		GUIComponent.__init__(self)
		self.type=type
		self.l = eListboxPythonMultiContent()
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setFont(1, gFont("Regular", 16))
		self.l.setBuildFunc(self.buildEPGSearchEntry)
		self.epgcache = eEPGCache.getInstance()
		self.clock_pixmap = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, 'skin_default/icons/epgclock.png'))
		self.clock_add_pixmap = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, 'skin_default/icons/epgclock_add.png'))
		self.clock_pre_pixmap = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, 'skin_default/icons/epgclock_pre.png'))
		self.clock_post_pixmap = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, 'skin_default/icons/epgclock_post.png'))
		self.clock_prepost_pixmap = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, 'skin_default/icons/epgclock_prepost.png'))

		if PartnerBoxInstalled:
			# Partnerbox Clock Icons
			self.remote_clock_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock.png')
			self.remote_clock_add_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_add.png')
			self.remote_clock_pre_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_pre.png')
			self.remote_clock_post_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_post.png')
			self.remote_clock_prepost_pixmap = LoadPixmap('/usr/lib/enigma2/python/Plugins/Extensions/Partnerbox/icons/remote_epgclock_prepost.png')

	def buildEPGSearchEntry(self, service, eventId, beginTime, duration, EventName):
		rec1=beginTime and (self.timer.isInTimer(eventId, beginTime, duration, service))
		# Partnerbox 
		if PartnerBoxInstalled:
			rec2=beginTime and (isInRemoteTimer(self,beginTime, duration, service))
		else:rec2=False
		r1=self.weekday_rect
		r2=self.datetime_rect
		r3=self.descr_rect
		t = localtime(beginTime)
		serviceref = ServiceReference(service) # for Servicename
		res = [
			None, # no private data needed
			(eListboxPythonMultiContent.TYPE_TEXT, r1.left(), r1.top(), r1.width(), r1.height(), 0, RT_HALIGN_RIGHT, self.days[t[6]]),
			(eListboxPythonMultiContent.TYPE_TEXT, r2.left(), r2.top(), r2.width(), r1.height(), 0, RT_HALIGN_RIGHT, "%02d.%02d, %02d:%02d"%(t[2],t[1],t[3],t[4]))
		]
		if rec1 or rec2:
			if rec1:			
				clock_pic = self.getClockPixmap(service, beginTime, duration, eventId)
				# maybe Partnerbox too
				if rec2:
					clock_pic_partnerbox = getRemoteClockPixmap(self,service, beginTime, duration, eventId)
			else:
				clock_pic = getRemoteClockPixmap(self,service, beginTime, duration, eventId)
			if rec1 and rec2:
				# Partnerbox and local
				res.extend((
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left(), r3.top(), 21, 21, clock_pic),
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left() + 25, r3.top(), 21, 21, clock_pic_partnerbox),
					(eListboxPythonMultiContent.TYPE_TEXT, r3.left() + 50, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, serviceref.getServiceName() + ": " + EventName)))
			else:
				res.extend((
					(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, r3.left(), r3.top(), 21, 21, clock_pic),
					(eListboxPythonMultiContent.TYPE_TEXT, r3.left() + 25, r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, serviceref.getServiceName() + ": " + EventName)))
		else:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, r3.left(), r3.top(), r3.width(), r3.height(), 0, RT_HALIGN_LEFT, serviceref.getServiceName() + ": " + EventName))
		return res



class EPGSearch(EPGSelection):
	EMPTY = 0
	ADD_TIMER = 1
	REMOVE_TIMER = 2
	
	ZAP = 1
	def __init__(self, session, *args):
		Screen.__init__(self, session)
		self.skinName = "EPGSelection"
		self.bouquetChangeCB = None
		self.serviceChangeCB = None
		self.ask_time = -1 #now
		self["key_red"] = Button("")
		self.closeRecursive = False
		self.saved_title = None
		self["Service"] = ServiceEvent()
		self["Event"] = Event()
		self.type = EPG_TYPE_SINGLE
		# XXX: we lose sort begin/end here
		self["key_yellow"] = Button(_("New Search"))
		self["key_blue"] = Button(_("History"))
		self.currentService=None
		self.zapFunc = None
		self.sort_type = 0
		self.setSortDescription()
		self["key_green"] = Button(_("Add timer"))
		self.key_green_choice = self.ADD_TIMER
		self.key_red_choice = self.EMPTY
		self["list"] = EPGSearchList(type = self.type, selChangedCB = self.onSelectionChanged, timer = session.nav.RecordTimer)
		self["actions"] = ActionMap(["EPGSelectActions", "OkCancelActions"],
			{
				"cancel": self.closeScreen,
				"ok": self.eventSelected,
				"timerAdd": self.timerAdd,
				"yellow": self.yellowButtonPressed,
				"blue": self.blueButtonPressed,
				"info": self.infoKeyPressed,
				"red": self.zapTo, # needed --> Partnerbox
				"input_date_time": self.enterDateTime,
				"nextBouquet": self.nextBouquet, # just used in multi epg yet
				"prevBouquet": self.prevBouquet, # just used in multi epg yet
				"nextService": self.nextService, # just used in single epg yet
				"prevService": self.prevService, # just used in single epg yet
			})

		self["actions"].csel = self
		self.onLayoutFinish.append(self.onCreate)
		self["MenuActions"] = ActionMap(["MenuActions"],
		{
				"menu": self.menu,
		})
		self.searchargs = args
		# Partnerbox
		if PartnerBoxInstalled:
			EPGSelection.PartnerboxInit(self, False)

	def onCreate(self):
		if self.searchargs:
			self.searchEPG(*self.searchargs)
		else:
			l = self["list"]
			l.recalcEntrySize()
			l.list = []
			l.l.setList(l.list)
		del self.searchargs
		# Partnerbox
		if PartnerBoxInstalled:
			EPGSelection.GetPartnerboxTimerlist(self)

	def closeScreen(self):
		# Save our history
		config.plugins.epgsearch.save()
		EPGSelection.closeScreen(self)

	def yellowButtonPressed(self):
		self.session.openWithCallback(self.searchEPG, VirtualKeyBoard, title = _("Enter text to search for"))

	def menu(self):
		options = []
		options.append([_("Import from Timer"), "importFromTimer"])
		options.append([_("Import from EPG"), "importFromEPG"])
		# AutoTimer
		if AutoTimerInstalled:
			options.append([_("Add AutoTimer..."), "addAutoTimer"])
		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list = options
		)

	def menuCallback(self, ret):
		if ret:
			ret = ret[1]
			if ret is "importFromTimer":
				self.session.openWithCallback(
					self.searchEPG,
					EPGSearchTimerImport
				)
			elif ret is "importFromEPG":
				self.session.openWithCallback(
					self.searchEPG,
					EPGSearchChannelSelection
				)
			elif ret is "addAutoTimer":
				cur = self["list"].getCurrent()
				if cur is None:
					return
				serviceref = cur[1]
				event = cur[0]
				addAutotimerFromEvent(self.session, event,serviceref) 


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
				_("No history"),
				type = MessageBox.TYPE_INFO
			)

	def searchEPGWrapper(self, ret):
		if ret:
			self.searchEPG(ret[1])

	def searchEPG(self, searchString = None, searchSave = True):
		if searchString:
			if searchSave:
				# Maintain history
				history = config.plugins.epgsearch.history.value
				if searchString not in history:
					history.insert(0, searchString)
					if len(history) > 10:
						history.pop(10)
				else:
					history.remove(searchString)
					history.insert(0, searchString)

			# Workaround to allow search for umlauts if we know the encoding (pretty bad, I know...)
			encoding = config.plugins.epgsearch.encoding.value
			if encoding != 'UTF-8':
				try:
					searchString = searchString.decode('UTF-8', 'replace').encode(encoding)
				except UnicodeDecodeError:
					pass

			# Search EPG, default to empty list
			epgcache = eEPGCache.getInstance() # XXX: the EPGList also keeps an instance of the cache but we better make sure that we get what we want :-)
			ret = epgcache.search(('RIBDT', 200, eEPGCache.PARTIAL_TITLE_SEARCH, searchString, eEPGCache.NO_CASE_CHECK)) or []
			ret.sort(key = lambda x: x[2]) # sort by time

			# Update List
			l = self["list"]
			l.recalcEntrySize()
			l.list = ret
			l.l.setList(ret)

class EPGSearchTimerImport(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "TimerEditList"

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
		self.skinName = "SimpleChannelSelection"

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
		self.skinName = "EPGSelection"
		self["key_green"].setText(_("Search"))
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

