from Components.MenuList import MenuList

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, \
	RT_WRAP

from skin import parseFont

class RSSFeedList(MenuList):
	def __init__(self, entries):
		MenuList.__init__(self, entries, False, content=eListboxPythonMultiContent)

		l = self.l
		l.setFont(0, gFont("Regular", 22))
		self.descriptionFont = gFont("Regular", 18)
		l.setFont(1, self.descriptionFont)
		l.setItemHeight(100)
		l.setBuildFunc(self.buildListboxEntry)

	def applySkin(self, desktop, parent):
		attribs = [] 
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

	def invalidate(self):
		self.l.invalidate()

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
			(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, titleHeight, 0, RT_HALIGN_LEFT | RT_WRAP, feed.title),
			(eListboxPythonMultiContent.TYPE_TEXT, 0, titleHeight, width, descriptionHeight, 1, RT_HALIGN_LEFT, feed.description)
		]

	def getCurrent(self):
		# We know that the list will never be empty...
		return self.l.getCurrentSelection()[0]

