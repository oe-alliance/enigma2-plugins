#
#  MerlinEPGCenter E2 Plugin
#
#  $Id: EpgTabs.py,v 1.0 2011-06-13 11:05:00 shaderman Exp $
#
#  Coded by Shaderman (c) 2011
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#

# ENIGMA IMPORTS
from Components.config import config
from enigma import eServiceReference, eServiceCenter
import NavigationInstance
from ServiceReference import ServiceReference

# OWN IMPORTS
from EpgCenterList import EpgCenterList, TIMERLIST
from MerlinEPGCenter import LIST_MODE_AUTOTIMER


############################################################################################
# EPG TAB CLASSES

# base class for all epg tab classes
class EpgBaseTab():
	# instance of the parent (MerlinEPGCenter)
	parentInstance = None
	
	def __init__(self):
		pass
		
	# activate this tab
	def show(self):
		self.tabList.show()
		
	# inactivate this tab
	def hide(self):
		self.tabList.hide()
		
	# show similar events
	def showSimilar(self):
		cur = self.tabList.getCurrent()
		self.lastIndex = self.tabList.instance.getCurrentIndex()
		self.similarServiceRef = cur[2]
		self.similarEventId = cur[1]
		self.tabList.fillSimilar(self.similarServiceRef, self.similarEventId)
		self.tabList.instance.moveSelectionTo(0)
		
	# refresh similar events
	def refreshSimilar(self):
		self.tabList.fillSimilar(self.similarServiceRef, self.similarEventId)
		
	# hide similar events
	def hideSimilar(self):
		self.refresh()
		self.tabList.instance.moveSelectionTo(self.lastIndex)
		
	# refresh the current list
	def refresh(self):
		pass
		
# epg now tab
class EpgNowTab(EpgBaseTab):
	def __init__(self, tabList):
		self.tabList = tabList
		EpgBaseTab.__init__(self)
		self.__shown = False
		
	def show(self, currentBouquet, currentBouquetIndex, currentMode):
		# save the last state
		self.__currentBouquet = currentBouquet
		self.__currentBouquetIndex = currentBouquetIndex
		self.__currentMode = currentMode
		
		self.__shown = True
		
		self.tabList.fillMultiEPG(currentBouquet, currentBouquetIndex, currentMode, -1)
		self.tabList.show()
		
	def refresh(self):
		if not self.__shown:
			return
		self.tabList.fillMultiEPG(self.__currentBouquet, self.__currentBouquetIndex, self.__currentMode, -1)
		self.tabList.l.invalidate()
		
# epg next tab
class EpgNextTab(EpgBaseTab):
	def __init__(self, tabList):
		self.tabList = tabList
		EpgBaseTab.__init__(self)
		self.__shown = False
		
	def show(self, currentBouquet, currentBouquetIndex, currentMode):
		# save the last state
		self.__currentBouquet = currentBouquet
		self.__currentBouquetIndex = currentBouquetIndex
		self.__currentMode = currentMode
		
		self.__shown = True
		
		self.tabList.fillMultiEPG(currentBouquet, currentBouquetIndex, currentMode, -1)
		self.tabList.show()
		
	def refresh(self):
		if not self.__shown:
			return
		self.tabList.fillMultiEPG(self.__currentBouquet, self.__currentBouquetIndex, self.__currentMode, -1)
		self.tabList.l.invalidate()
		
# epg single tab
class EpgSingleTab(EpgBaseTab):

	SORT_MODE_TIME = 0
	SORT_MODE_NAME = 1
	
	def __init__(self, tabList):
		self.tabList = tabList
		EpgBaseTab.__init__(self)
		self.__shown = False
		self.sortMode = self.SORT_MODE_TIME
		
	def getFirstServiceRef(self, bouquet):
		servicelist = eServiceCenter.getInstance().list(bouquet[1])
		if not servicelist is None:
			while True:
				service = servicelist.getNext()
				if service.valid():
					return service.toString()
				if service.flags & (eServiceReference.isDirectory | eServiceReference.isMarker | eServiceReference.isGroup): # ignore non playable services
					continue
		else:
			return ""
			
	def getServiceRef(self, oldMode, bouquet):
		# set the marker to the currently running service on plugin start
		if config.plugins.merlinEpgCenter.selectRunningService.value and oldMode == None:
			sRef = NavigationInstance.instance.getCurrentlyPlayingServiceReference().toString()
		else:
			if oldMode == TIMERLIST:
				cur = self.parentInstance["timerlist"].getCurrent() # this could be solved better...
			else:
				cur = self.tabList.getCurrent()

			if cur:
				if oldMode == TIMERLIST:
					sRef = str(cur.service_ref)
				else:
					sRef = cur[2]
			else:
				sRef = self.getFirstServiceRef(bouquet)
				
		return sRef
		
	def show(self, oldMode, firstBouquet, currentBouquet, currentBouquetIndex, currentMode, showOutdated, sRef=None, timerListMode=None):
		# save the last state
		self.__currentBouquet = currentBouquet
		self.__currentBouquetIndex = currentBouquetIndex
		self.__currentMode = currentMode
		self.__showOutdated = showOutdated
		
		self.sortMode = self.SORT_MODE_TIME
		
		if timerListMode == LIST_MODE_AUTOTIMER: # we don't have a service ref from autotimers, let's get the first one in bouquets
			self.__sRef = self.getFirstServiceRef(firstBouquet)
		elif sRef == None:
			self.__sRef = self.getServiceRef(oldMode, firstBouquet)
		else:
			self.__sRef = sRef
			
		if self.__sRef == None:
			self.__sRef = self.getFirstServiceRef(firstBouquet)
		if self.__sRef != "":
			self.__shown = True
			self.tabList.fillSingleEPG(currentBouquet, currentBouquetIndex, currentMode, self.__sRef, showOutdated)
			self.tabList.instance.moveSelectionTo(0)
			
		if self.__sRef in EpgCenterList.bouquetServices[self.__currentBouquetIndex]:
			self.serviceIndex = EpgCenterList.bouquetServices[self.__currentBouquetIndex].index(self.__sRef)
		else:
			self.serviceIndex = 0
			
		self.tabList.show()
		
	def refresh(self):
		if not self.__shown:
			return
			
		if self.sortMode == self.SORT_MODE_NAME:
			cur = self.tabList.getCurrent()
			if cur:
				eventId = cur[1]
			else:
				eventId = None
		else:
			eventId = None
			
		self.tabList.fillSingleEPG(self.__currentBouquet, self.__currentBouquetIndex, self.__currentMode, self.__sRef, self.__showOutdated)
		
		if eventId != None:
			self.sort(eventId)
		else:
			self.tabList.l.invalidate()
			
	def changeService(self, direction): # +1 = next service, -1 = previous service
		self.sortMode = self.SORT_MODE_TIME # reset sorting
		
		numChannels = len(EpgCenterList.bouquetServices[self.__currentBouquetIndex])
		
		self.serviceIndex += direction
		if self.serviceIndex < 0 or self.serviceIndex == numChannels:
			changeBouquet = direction
		else:
			changeBouquet = None
			
		if changeBouquet != None:
			numBouquets = len(EpgCenterList.bouquetServices)
			
			self.__currentBouquetIndex += direction
			if self.__currentBouquetIndex < 0:
				self.__currentBouquetIndex = numBouquets - 1
				self.serviceIndex = len(EpgCenterList.bouquetServices[self.__currentBouquetIndex]) - 1
			elif self.__currentBouquetIndex == numBouquets:
				self.__currentBouquetIndex = 0
				self.serviceIndex = 0
			else:
				if direction == 1:
					self.serviceIndex = 0
				else:
					self.serviceIndex = len(EpgCenterList.bouquetServices[self.__currentBouquetIndex]) - 1
					
			EpgCenterList.currentBouquetIndex = self.__currentBouquetIndex
			self.parentInstance.currentBouquetIndex = self.__currentBouquetIndex
			self.parentInstance.setBouquetName()
			
		self.__sRef = EpgCenterList.bouquetServices[self.__currentBouquetIndex][self.serviceIndex]
		self.refresh()
		self.tabList.instance.moveSelectionTo(0)
		
		# we want to continue with the selected bouquet and service if we return to one of the MULTI_EPG modes
		self.parentInstance.currentBouquet = self.parentInstance.bouquetList[self.__currentBouquetIndex][1]
		self.parentInstance.currentBouquetIndex = self.__currentBouquetIndex
		self.parentInstance.lastMultiEpgIndex = self.serviceIndex
		
	def sort(self, eventId=None):
		if eventId == None:
			cur = self.tabList.getCurrent()
			eventId = cur[1]
			
		if self.sortMode == self.SORT_MODE_TIME: # sort by time (default)
			self.tabList.list.sort(key=lambda x: x[3])
		elif self.sortMode == self.SORT_MODE_NAME: # sort by name and time
			self.tabList.list.sort(key=lambda x: (x[5] and x[5].lower(), x[3]))
			
		self.tabList.setList(self.tabList.list)
		self.tabList.l.invalidate()
		
		index = 0
		for x in self.tabList.list:
			if x[1] == eventId:
				self.tabList.moveToIndex(index)
				break
			index += 1
			
# epg prime time tab
class EpgPrimeTimeTab(EpgBaseTab):
	def __init__(self, tabList):
		self.tabList = tabList
		EpgBaseTab.__init__(self)
		self.__shown = False
		
	def show(self, currentBouquet, currentBouquetIndex, currentMode):
		# save the last state
		self.__currentBouquet = currentBouquet
		self.__currentBouquetIndex = currentBouquetIndex
		self.__currentMode = currentMode
		
		self.__shown = True
		
		self.tabList.fillMultiEPG(currentBouquet, currentBouquetIndex, currentMode, self.primeTime)
		self.tabList.show()
		
	def refresh(self):
		if not self.__shown:
			return
		self.tabList.fillMultiEPG(self.__currentBouquet, self.__currentBouquetIndex, self.__currentMode, self.primeTime)
		self.tabList.l.invalidate()
		
# epg timer list tab
class EpgTimerListTab(EpgBaseTab):
	def __init__(self, tabList):
		self.tabList = tabList
		EpgBaseTab.__init__(self)
		
# epg search history tab
class EpgSearchHistoryTab(EpgBaseTab):
	def __init__(self, tabList):
		self.tabList = tabList
		EpgBaseTab.__init__(self)
		
	def show(self):
		self.tabList.show()
		
# epg search manual tab
class EpgSearchManualTab(EpgBaseTab):
	def __init__(self, tabList, searchLabel):
		self.tabList = tabList
		self.searchLabel = searchLabel
		EpgBaseTab.__init__(self)
		
	def show(self):
		self.tabList.show()
		self.searchLabel.show()
		if config.plugins.merlinEpgCenter.showInputHelp.value:
			self.parentInstance.searchField.help_window.show()
			
	def hide(self):
		self.searchLabel.hide()
		self.tabList.hide()
		if config.plugins.merlinEpgCenter.showInputHelp.value:
			self.parentInstance.searchField.help_window.hide()
			
	def updateEpgSearchHistory(self):
		searchString = self.tabList.list[0][1].value
		history = config.plugins.merlinEpgCenter.searchHistory.value
		if searchString not in history:
			history.insert(0, searchString)
			if len(history) > 10:
				history.pop(10)
		else:
			history.remove(searchString)
			history.insert(0, searchString)
			
# epg search result tab
class EpgSearchResultTab(EpgBaseTab):
	def __init__(self, tabList):
		self.tabList = tabList
		EpgBaseTab.__init__(self)
		self.__shown = False
		
	def show(self, searchString, mode):
		# save the last state
		self.__searchString = searchString
		self.__mode = mode
		
		self.__shown = True
		
		self.tabList.fillEpgSearch(searchString, mode)
		self.tabList.instance.moveSelectionTo(0)
		
		self.tabList.show()
		
	def refresh(self):
		if not self.__shown:
			return
		self.tabList.fillEpgSearch(self.__searchString, self.__mode)
		self.tabList.l.invalidate()
		
	def updateEpgSearchHistory(self, searchString):
		history = config.plugins.merlinEpgCenter.searchHistory.value
		if searchString not in history:
			history.insert(0, searchString)
			if len(history) > 10:
				history.pop(10)
		else:
			history.remove(searchString)
			history.insert(0, searchString)
			
