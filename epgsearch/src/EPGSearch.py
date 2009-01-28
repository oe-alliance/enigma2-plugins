from enigma import eEPGCache, eServiceReference

from Screens.ChoiceBox import ChoiceBox
from Screens.EpgSelection import EPGSelection
from Screens.InputBox import InputBox
from Screens.Screen import Screen

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.config import config
from Components.TimerList import TimerList

class EPGSearch(EPGSelection):
	def __init__(self, session):
		EPGSelection.__init__(self, session, '')  # Empty string serviceref so we get EPG_TYPE_SINGLE
		self.skinName = "EPGSelection"

		# XXX: we lose sort begin/end here
		self["key_yellow"].setText(_("New Search"))
		self["key_blue"].setText(_("History"))

	def onCreate(self):
		l = self["list"]
		l.recalcEntrySize()
		l.list = []
		l.l.setList(l.list)

	def closeScreen(self):
		# Save our history
		config.plugins.epgsearch.save()
		EPGSelection.closeScreen(self)

	def yellowButtonPressed(self):
		self.session.openWithCallback(
			self.searchEPG,
			InputBox,
			title = _("Enter text to search for")
		)

	def blueButtonPressed(self):
		options = [(x, x) for x in config.plugins.epgsearch.history.value]
		options.insert(0, (_("From Timer"), "xxImportFromTimer"))

		self.session.openWithCallback(
			self.searchEPGWrapper,
			ChoiceBox,
			title = _("Select text to search for"),
			list = options
		)

	def searchEPGWrapper(self, ret):
		if ret:
			ret = ret[1]
			if ret is "xxImportFromTimer":
				self.session.openWithCallback(
					self.searchEPG,
					EPGSearchTimerImport
				)
			else:
				self.searchEPG(ret)

	def searchEPG(self, searchString):
		if searchString:
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

