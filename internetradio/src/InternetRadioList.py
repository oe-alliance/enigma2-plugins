#
# InternetRadio E2
#
# Coded by Dr.Best (c) 2012
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Multimedia GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Multimedia GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Multimedia GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#

from enigma import eListboxPythonMultiContent, eListbox, gFont, \
	RT_HALIGN_LEFT, RT_VALIGN_CENTER
from Components.GUIComponent import GUIComponent
	
	
class InternetRadioList(GUIComponent, object):
	def buildEntry(self, item):
		width = self.l.getItemSize().width()
		res = [ None ]
		if self.mode == 0: # GENRELIST
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 3, width, 23, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, item.name))
		elif self.mode == 1: # STATIONLIST
			if len(item.country) != 0:
				display = "%s (%s)" % (item.name, item.country)
			else:
				display = item.name
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 3, width, 23, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, display))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 27, width, 23, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, item.genre))
		elif self.mode == 2: # FAVORITELIST
			if len(item.configItem.country.value) != 0:
				display = "%s (%s)" % (item.configItem.name.value, item.configItem.country.value)
			else:
				display = item.configItem.name.value
				
			if item.configItem.type.value > 0:
				if item.configItem.type.value == 1:
					filtername = _("Genres")
				else:
					filtername = _("Countries")
				display2 = "%s %s" % (_("Filter:"),filtername)
			else:
				display2 = item.configItem.tags.value
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 3, width, 23, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, display))
			res.append((eListboxPythonMultiContent.TYPE_TEXT, 0, 27, width, 23, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, display2))
		return res

	def __init__(self):
		GUIComponent.__init__(self)
		self.l = eListboxPythonMultiContent()
		self.l.setFont(0, gFont("Regular", 22))
		self.l.setFont(1, gFont("Regular", 18))
		self.l.setBuildFunc(self.buildEntry)
		self.l.setItemHeight(29)
		self.onSelectionChanged = [ ]
		self.mode = 0
		self.list = []

	def setMode(self, mode):
		self.mode = mode
		if mode == 0: # GENRELIST
			self.l.setItemHeight(29)
		elif mode == 1 or mode == 2: # STATIONLIST OR FAVORITELIST
			self.l.setItemHeight(53)

	def connectSelChanged(self, fnc):
		if not fnc in self.onSelectionChanged:
			self.onSelectionChanged.append(fnc)

	def disconnectSelChanged(self, fnc):
		if fnc in self.onSelectionChanged:
			self.onSelectionChanged.remove(fnc)

	def selectionChanged(self):
		for x in self.onSelectionChanged:
			x()
	
	def getCurrent(self):
		cur = self.l.getCurrentSelection()
		return cur and cur[0]
	
	GUI_WIDGET = eListbox
	
	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		instance.selectionChanged.get().append(self.selectionChanged)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		instance.selectionChanged.get().remove(self.selectionChanged)

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)

	def getCurrentIndex(self):
		return self.instance.getCurrentIndex()

	currentIndex = property(getCurrentIndex, moveToIndex)
	currentSelection = property(getCurrent)

	def setList(self, list):
		self.list = list
		self.l.setList(list)

	def moveToFavorite(self, name, text):
		if self.mode == 2: # FAVORITELIST
			i = 0
			for favs in self.list:
				if favs[0].configItem.name.value == name and favs[0].configItem.text.value == text:
					self.moveToIndex(i)
					break
				i += 1
