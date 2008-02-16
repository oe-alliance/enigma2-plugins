from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, \
	RT_WRAP

class RSSBaseList(MenuList):
	"""Base List Component for RSSFeeds."""

	def __init__(self, entries, itemheight):
		MenuList.__init__(self, entries, False, content = eListboxPythonMultiContent)

		self.l.setFont(0, gFont("Regular", 22))
		self.l.setFont(1, gFont("Regular", 18))
		self.l.setItemHeight(itemheight)

	def connectSelChanged(self, fnc):
		if not fnc in self.onSelectionChanged:
			self.onSelectionChanged.append(fnc)

	def disconnectSelChanged(self, fnc):
		if fnc in self.onSelectionChanged:
			self.onSelectionChanged.remove(fnc)

	def moveToEntry(self, identifier):
		pass

	def invalidate(self):
		self.l.invalidate()

class RSSFeedList(RSSBaseList):
	def __init__(self, entries):
		RSSBaseList.__init__(self, entries, 100)
		self.l.setBuildFunc(self.buildListboxEntry)

	def moveToEntry(self, feed):
		if feed is None:
			return

		idx = 0
		for x in self.list:
			if feed.uri == x[0].uri:
				self.instance.moveSelectionTo(idx)
				break
			idx += 1

	def buildListboxEntry(self, feed):
		res = [ None ]
		width = self.l.getItemSize().width()
		res.append(MultiContentEntryText(pos=(0, 0), size=(width, 75), font=0, flags = RT_HALIGN_LEFT|RT_WRAP, text = feed.title))
		res.append(MultiContentEntryText(pos=(0, 75), size=(width, 20), font=1, flags = RT_HALIGN_LEFT, text = feed.description))
		return res

	def getCurrent(self):
		# We know that the list will never be empty...
		return self.l.getCurrentSelection()[0]

class RSSEntryList(RSSBaseList):
	def __init__(self, entries):
		RSSBaseList.__init__(self, entries, 50)
		self.l.setBuildFunc(self.buildListboxEntry)

	def moveToEntry(self, entry):
		if entry is None:
			return

		idx = 0
		for x in self.list:
			if entry[0] == x[0]:
				self.instance.moveSelectionTo(idx)
				break
			idx += 1

	def buildListboxEntry(self, title, link, summary, enclosures):
		res = [ None ]
		width = self.l.getItemSize().width()
		res.append(MultiContentEntryText(pos=(0, 3), size=(width, 50), font=0, flags = RT_HALIGN_LEFT|RT_WRAP, text = title))
		return res