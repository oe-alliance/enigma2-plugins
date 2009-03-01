from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, \
	RT_WRAP

from skin import parseFont

class RSSBaseList(MenuList):
	"""Base List Component for RSSFeeds."""

	def __init__(self, entries, itemheight):
		MenuList.__init__(self, entries, False, content = eListboxPythonMultiContent)

		l = self.l
		l.setFont(0, gFont("Regular", 22))
		self.descriptionFont = gFont("Regular", 18)
		l.setFont(1, self.descriptionFont)
		l.setItemHeight(itemheight)

	def applySkin(self, desktop, parent):
		attribs = [ ] 
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "font":
					self.l.setFont(0, parseFont(value, ((1,1),(1,1))))
				elif attrib == "descriptionFont":
					self.descriptionFont = parseFont(value, ((1,1),(1,1)))
					self.l.setFont(1, self.descriptionFont)
				elif attrib == "itemHeight":
					self.l.setItemHeight(int(value))
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs
		return MenuList.applySkin(self, desktop, parent)

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
		size = self.l.getItemSize()
		width = size.width()
		descriptionHeight = self.descriptionFont.pointSize + 2
		titleHeight = size.height() - descriptionHeight

		return [
			None,
			MultiContentEntryText(pos=(0, 0), size=(width, titleHeight), font=0, flags = RT_HALIGN_LEFT|RT_WRAP, text = feed.title),
			MultiContentEntryText(pos=(0, titleHeight), size=(width, descriptionHeight), font=1, flags = RT_HALIGN_LEFT, text = feed.description)
		]

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
		size = self.l.getItemSize()
		return [
			None,
			MultiContentEntryText(pos=(0, 3), size=(size.width(), size.height() - 3), font=0, flags = RT_HALIGN_LEFT|RT_WRAP, text = title)
		]

