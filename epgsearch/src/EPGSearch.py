# Plugins Config
from enigma import eEPGCache, eServiceReference

from Screens.EpgSelection import EPGSelection
from Screens.InputBox import InputBox
from Screens.ChoiceBox import ChoiceBox

from Components.config import config

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
		self.session.openWithCallback(
			self.searchEPGWrapper,
			ChoiceBox,
			title = _("Select text to search for"),
			list = [(x, x) for x in config.plugins.epgsearch.history.value]
		)

	def searchEPGWrapper(self, ret):
		if ret:
			self.searchEPG(ret[1])

	# Yeah, the encoding stuff is still pretty bad :-)
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

			# Workaround to allow search for umlauts if we know the encoding
			encoding = config.plugins.epgsearch.encoding.value
			if encoding != 'UTF-8':
				try:
					searchString = searchString.decode('UTF-8', 'replace').encode(encoding)
				except UnicodeDecodeError:
					pass

			# Search EPG, default to empty list
			epgcache = eEPGCache.getInstance() # XXX: the EPGList also keeps an instance of the cache but we better make sure that we get what we want :-)
			ret = epgcache.search(('RIBDT', 200, eEPGCache.PARTIAL_TITLE_SEARCH, searchString, eEPGCache.NO_CASE_CHECK)) or []
	
			# Update List
			l = self["list"]
			l.recalcEntrySize()
			l.list = ret
			l.l.setList(ret)

