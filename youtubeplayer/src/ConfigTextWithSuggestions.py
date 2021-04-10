############################################################################
#    Copyright (C) 2008 by Volker Christian                                #
#    Volker.Christian@fh-hagenberg.at                                      #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
#                                                                          #
#    This program is distributed in the hope that it will be useful,       #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#    GNU General Public License for more details.                          #
#                                                                          #
#    You should have received a copy of the GNU General Public License     #
#    along with this program; if not, write to the                         #
#    Free Software Foundation, Inc.,                                       #
#    59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             #
############################################################################

from GoogleSuggestions import GoogleSuggestions

from Screens.Screen import Screen
from Components.config import ConfigText
from Components.config import KEY_DELETE, KEY_BACKSPACE, KEY_LEFT, KEY_RIGHT
from Components.config import KEY_HOME, KEY_END, KEY_TOGGLEOW, KEY_ASCII, KEY_TIMEOUT
from Components.MenuList import MenuList
from enigma import eListboxPythonMultiContent, RT_HALIGN_LEFT, gFont

from threading import Thread
from threading import Condition


def SuggestionListEntry(suggestion):
	res = [ suggestion ]
	res.append((eListboxPythonMultiContent.TYPE_TEXT, 5, 1, 370, 20, 0, RT_HALIGN_LEFT, suggestion[0]))
	return res


class SuggestionsList(MenuList):
	def __init__(self):
		MenuList.__init__(self, list, False, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 18))
		self.l.setItemHeight(23)


	def update(self, suggestions):
		self.list = []
		if suggestions:
			suggests = suggestions[1]
			for suggestion in suggests:
				self.list.append(SuggestionListEntry(suggestion))
			self.l.setList(self.list)
			self.moveToIndex(0)


	def getSelection(self):
		if self.getCurrent() is None:
			return None
		return self.l.getCurrentSelection()[0][0]


class SuggestionsListScreen(Screen):
	def __init__(self, session, configTextWithSuggestion):
		Screen.__init__(self, session)
		self.suggestionlist = SuggestionsList()
		self["suggestionslist"] = self.suggestionlist
		self.configTextWithSuggestion = configTextWithSuggestion


	def update(self, suggestions):
		if suggestions and len(suggestions[1]) > 0:
			if not self.shown:
				self.show()
			self.suggestionlist.update(suggestions)
		else:
			self.hide()


	def up(self):
		self.suggestionlist.up()
		return self.suggestionlist.getSelection()


	def down(self):
		self.suggestionlist.down()
		return self.suggestionlist.getSelection()

	
	def pageUp(self):
		self.suggestionlist.pageUp()
		return self.suggestionlist.getSelection()


	def pageDown(self):
		self.suggestionlist.pageDown()
		return self.suggestionlist.getSelection()


	def activate(self):
		self.suggestionlist.selectionEnabled(1)
		return self.suggestionlist.getSelection()


	def deactivate(self):
		self.suggestionlist.selectionEnabled(0)
		return self.suggestionlist.getSelection()


class ConfigTextWithSuggestions(ConfigText):
	class SuggestionsThread(Thread):
		def __init__(self, suggestionsService):
			Thread.__init__(self)
			self.suggestionsService = suggestionsService
			self.value = None
			self.running = True
			self.condition = Condition()

		def run(self):
			while self.running:
				self.condition.acquire()
				if self.value is None:
					self.condition.wait()
				value = self.value
				self.value = None
				self.condition.release()
				if value is not None:
					self.suggestionsService.getSuggestions(value)

		def stop(self):
			self.running = False
			self.condition.acquire()
			self.condition.notify()
			self.condition.release()
			self.join()

		def getSuggestions(self, value):
			self.condition.acquire()
			self.value = value
			self.condition.notify()
			self.condition.release()

	def __init__(self, default="", fixed_size=True, visible_width=False, threaded=False):
		ConfigText.__init__(self, default, fixed_size, visible_width)
		self.suggestions = GoogleSuggestions(self.propagateSuggestions, ds="yt", hl="en")
		self.suggestionsThread = None
		self.threaded = threaded
		self.suggestionsListActivated = False


	def propagateSuggestions(self, suggestionsList):
		if self.suggestionsWindow:
			self.suggestionsWindow.update(suggestionsList)


	def getSuggestions(self):
		if self.suggestionsThread is not None:
			self.suggestionsThread.getSuggestions(self.value)
		else:
			self.suggestions.getSuggestions(self.value)


	def handleKey(self, key):
		if not self.suggestionsListActivated:
			ConfigText.handleKey(self, key)
			if key in [KEY_DELETE, KEY_BACKSPACE, KEY_ASCII, KEY_TIMEOUT]:
				self.getSuggestions()


	def onSelect(self, session):
		if self.threaded:
			self.suggestionsThread = ConfigTextWithSuggestions.SuggestionsThread(self.suggestions)
			try:
				self.suggestionsThread.start()
			except:
				pass
		else:
			self.suggestionsThread = None
		ConfigText.onSelect(self, session)
		if session is not None:
			self.suggestionsWindow = session.instantiateDialog(SuggestionsListScreen, self)
			self.suggestionsWindow.deactivate()
			self.suggestionsWindow.hide()
		self.suggestions.getSuggestions(self.value)


	def onDeselect(self, session):
		if self.suggestionsThread is not None:
			self.suggestionsThread.stop()
		ConfigText.onDeselect(self, session)
		if self.suggestionsWindow:
			session.deleteDialog(self.suggestionsWindow)
			self.suggestionsWindow = None


	def suggestionListUp(self):
		self.value = self.suggestionsWindow.up()


	def suggestionListDown(self):
		self.value = self.suggestionsWindow.down()


	def suggestionListPageDown(self):
		self.value = self.suggestionsWindow.pageDown()


	def suggestionListPageUp(self):
		self.value = self.suggestionsWindow.pageUp()


	def activateSuggestionList(self):
		ret = False
		if self.suggestionsWindow is not None and self.suggestionsWindow.shown:
			self.tmpValue = self.value
			self.value = self.suggestionsWindow.activate()
			self.allmarked = False
			self.marked_pos = -1
			self.suggestionsListActivated = True
			ret = True
		return ret


	def deactivateSuggestionList(self):
		ret = False
		if self.suggestionsWindow is not None:
			self.suggestionsWindow.deactivate()
			self.getSuggestions()
			self.allmarked = True
			self.suggestionsListActivated = False
			ret = True
		return ret


	def cancelSuggestionList(self):
		self.value = self.tmpValue
		return self.deactivateSuggestionList()
