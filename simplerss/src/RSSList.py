from Components.GUIComponent import GUIComponent
from Components.MultiContent import MultiContentEntryText
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_WRAP

class RSSList(GUIComponent):
	def __init__(self, entries):
		GUIComponent.__init__(self)
		self.list = entries
		self.l = eListboxPythonMultiContent()
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setFont(1, gFont("Regular", 18))
		self.l.setBuildFunc(self.buildListboxEntry)
		self.l.setList(entries)
		
		self.onSelectionChanged = [ ]
		
	def connectSelChanged(self, fnc):
		if not fnc in self.onSelectionChanged:
			self.onSelectionChanged.append(fnc)

	def disconnectSelChanged(self, fnc):
		if fnc in self.onSelectionChanged:
			self.onSelectionChanged.remove(fnc)

	def selectionChanged(self):
		for x in self.onSelectionChanged:
			x()

	GUI_WIDGET = eListbox

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		instance.setItemHeight(100)
		instance.selectionChanged.get().append(self.selectionChanged)

	def buildListboxEntry(self, title, link, summary, enclosures):
		res = [ None ]
		width = self.l.getItemSize().width()
		res.append(MultiContentEntryText(pos=(0, 0), size=(width, 75), font=0, flags = RT_HALIGN_LEFT|RT_WRAP, text = title))
		res.append(MultiContentEntryText(pos=(0, 75), size=(width, 20), font=1, flags = RT_HALIGN_LEFT, text = link))
		return res

	def getCurrentEntry(self):
		return self.l.getCurrentSelection()

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)

	def moveToEntry(self, entry):
		if entry is None:
			return

		count = 0
		for x in self.list:
			if entry[0] == x[0]:
				self.instance.moveSelectionTo(count)
				break
			count += 1

	def moveDown(self):
		self.instance.moveSelection(self.instance.moveDown)

	def moveUp(self):
		self.instance.moveSelection(self.instance.moveUp)