#
#  MerlinEPGCenter E2 Plugin
#
#  $Id: plugin.py,v 1.0 2011-02-14 21:53:00 shaderman Exp $
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


# for localized messages
from . import _

# ENIGMA IMPORTS
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import InfoBar

# OWN IMPORTS
from MerlinEPGCenter import MerlinEPGCenter
from EpgCenterList import MULTI_EPG_NOW, SINGLE_EPG


infoBarFunctionSaver = None

class MerlinEPGCenterStarter(object):
	instance = None
	merlinEPGCenter = None
	
	def __init__(self, session):
		self.session = session
		assert not MerlinEPGCenterStarter.instance, "only one MerlinEPGCenterStarter instance is allowed!"
		MerlinEPGCenterStarter.instance = self # set instance
		
	def openMerlinEPGCenter(self, startTab = None, doSearch = False):
		servicelist, currentBouquet, bouquetList, currentIndex = getBouquetInformation()
		if MerlinEPGCenterStarter.merlinEPGCenter is None:
			MerlinEPGCenterStarter.merlinEPGCenter = self.session.instantiateDialog(MerlinEPGCenter, servicelist, currentBouquet, bouquetList, currentIndex, startTab, doSearch)
		else:
			MerlinEPGCenterStarter.merlinEPGCenter.resume()
			if startTab != None:
				MerlinEPGCenterStarter.merlinEPGCenter.setStartTab(startTab, doSearch)
			elif config.plugins.merlinEpgCenter.rememberLastTab.value:
				MerlinEPGCenterStarter.merlinEPGCenter.setStartTab(config.plugins.merlinEpgCenter.lastUsedTab.value, doSearch)
			else:
				MerlinEPGCenterStarter.merlinEPGCenter.setStartTab(MULTI_EPG_NOW, doSearch)
		self.session.execDialog(MerlinEPGCenterStarter.merlinEPGCenter)
		
# open "single epg" tab
def startMerlinEPGCenterSingle(self):
	MerlinEPGCenterStarter.instance.openMerlinEPGCenter(SINGLE_EPG)
	
# open "multi epg now" tab
def startMerlinEPGCenterMulti(self, withCallback=None): # withCallback is an extra parameter which is passed when called form a service without EPG data
	MerlinEPGCenterStarter.instance.openMerlinEPGCenter(MULTI_EPG_NOW)
	
class InfoBarFunctionSaver:
	def __init__(self):
		self.infoBarSingleEpg = InfoBar.openSingleServiceEPG
		self.infoBarMultiEpg = InfoBar.openMultiServiceEPG
		from Components.config import config
		config.plugins.merlinEpgCenter.replaceInfobarEpg.addNotifier(self.changeFunctions, initial_call = True)
			
	def changeFunctions(self, configElement):
		if configElement.value: # replace InfoBar EPG functions
			InfoBar.openSingleServiceEPG = startMerlinEPGCenterSingle # Info -> yellow
			InfoBar.openMultiServiceEPG = startMerlinEPGCenterMulti # Info -> blue
		else: # revert functions
			InfoBar.openSingleServiceEPG = self.infoBarSingleEpg # Info -> yellow
			InfoBar.openMultiServiceEPG = self.infoBarMultiEpg # Info -> blue
			
	def saveInfoBarChannelFunctions(self):
		self.infoBarSwitchChannelUp = InfoBar.instance["ChannelSelectActions"].actions["switchChannelUp"]
		self.infoBarSwitchChannelDown = InfoBar.instance["ChannelSelectActions"].actions["switchChannelDown"]
		
	def saveInfoBarEventViewFunctions(self):
		self.infoBarEventView = InfoBar.instance["EPGActions"].actions["showEventInfo"]
		
	def setInfoBarActionMap(self, configElement = None):
		if configElement == config.plugins.merlinEpgCenter.replaceInfobarChannelUp:
			value = int(config.plugins.merlinEpgCenter.replaceInfobarChannelUp.value)
			if value == -1: # disabled
				if InfoBar.instance["ChannelSelectActions"].actions["switchChannelUp"] is not self.infoBarSwitchChannelUp:
					InfoBar.instance["ChannelSelectActions"].actions["switchChannelUp"] = self.infoBarSwitchChannelUp
			else:
				InfoBar.instance["ChannelSelectActions"].actions["switchChannelUp"] = self.channelUpStarter
		elif configElement == config.plugins.merlinEpgCenter.replaceInfobarChannelDown:
			value = int(config.plugins.merlinEpgCenter.replaceInfobarChannelDown.value)
			if value == -1:
				if InfoBar.instance["ChannelSelectActions"].actions["switchChannelDown"] is not self.infoBarSwitchChannelDown:
					InfoBar.instance["ChannelSelectActions"].actions["switchChannelDown"] = self.infoBarSwitchChannelDown
			else:
				InfoBar.instance["ChannelSelectActions"].actions["switchChannelDown"] = self.channelDownStarter
		elif configElement == config.plugins.merlinEpgCenter.replaceShowEventView:
			value = int(config.plugins.merlinEpgCenter.replaceShowEventView.value)
			if value == -1:
				if InfoBar.instance["EPGActions"].actions["showEventInfo"] is not self.infoBarEventView:
					InfoBar.instance["EPGActions"].actions["showEventInfo"] = self.infoBarEventView
			else:
				InfoBar.instance["EPGActions"].actions["showEventInfo"] = self.showEventInfoStarter
				
	@staticmethod
	def channelUpStarter():
		value = int(config.plugins.merlinEpgCenter.replaceInfobarChannelUp.value)
		doSearch = value == 5
		MerlinEPGCenterStarter.instance.openMerlinEPGCenter(value, doSearch)
		
	@staticmethod
	def channelDownStarter():
		value = int(config.plugins.merlinEpgCenter.replaceInfobarChannelDown.value)
		doSearch = value == 5
		MerlinEPGCenterStarter.instance.openMerlinEPGCenter(value, doSearch)
		
	@staticmethod
	def showEventInfoStarter():
		value = int(config.plugins.merlinEpgCenter.replaceShowEventView.value)
		doSearch = value == 5
		MerlinEPGCenterStarter.instance.openMerlinEPGCenter(value, doSearch)
		
def autostart(reason, **kwargs):
	if reason == 1 and MerlinEPGCenterStarter.merlinEPGCenter:
		MerlinEPGCenterStarter.instance.merlinEPGCenter.shutdown()
		MerlinEPGCenterStarter.instance.merlinEPGCenter = None
		MerlinEPGCenterStarter.instance = None
		
def sessionstart(reason, session):
	global infoBarFunctionSaver
	infoBarFunctionSaver = InfoBarFunctionSaver()
	MerlinEPGCenterStarter(session)
	
# InfoBar is now initialised, our chance to occupy the ChannelSelectActions
def networkconfigread(reason = None):
	if not InfoBar.instance:
		return
	infoBarFunctionSaver.saveInfoBarChannelFunctions()
	infoBarFunctionSaver.saveInfoBarEventViewFunctions()
	config.plugins.merlinEpgCenter.replaceInfobarChannelUp.addNotifier(infoBarFunctionSaver.setInfoBarActionMap, initial_call = True)
	config.plugins.merlinEpgCenter.replaceInfobarChannelDown.addNotifier(infoBarFunctionSaver.setInfoBarActionMap, initial_call = True)
	config.plugins.merlinEpgCenter.replaceShowEventView.addNotifier(infoBarFunctionSaver.setInfoBarActionMap, initial_call = True)
	
def getBouquetInformation():
	# get current bouquet and bouquetlist from channelselection
	from Screens.InfoBar import InfoBar # if installed, nasty PTS Plugin overides Infobar class, so global import may not working to get instance, because maybe this plugin was imported from enigma2 before PTS ...import InfoBar now (just to be sure...) to get the correct instance member
	infoBarInstance = InfoBar.instance
	if infoBarInstance is not None:
		servicelist = infoBarInstance.servicelist
		currentBouquet = servicelist.getRoot()
		bouquetList = servicelist.getBouquetList()
		currentIndex = -1
		cnt = 0
		for bouquet in bouquetList: # is current bouquet in bouquetlist?
			if bouquet[1].toString() == currentBouquet.toString():
				currentIndex = cnt # yeah, set index
				break
			cnt += 1
		if currentIndex == -1: # current bouquet is not in bouquetlist (e.g. provider, new services a.s.o) --> set current bouquet to first boquet in bouquetlist
			currentBouquet = bouquetList[0][1]
			currentIndex = 0
			
	return servicelist, currentBouquet, bouquetList, currentIndex
	
def openMerlinEPGCenter(session, **kwargs):
	MerlinEPGCenterStarter.instance.openMerlinEPGCenter()
	
def Plugins(**kwargs):
	list = [
		PluginDescriptor(where = [PluginDescriptor.WHERE_AUTOSTART], fnc=autostart, weight=100),
		PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart, weight=100),
		PluginDescriptor(where = [PluginDescriptor.WHERE_NETWORKCONFIG_READ], fnc=networkconfigread, weight=100),
		PluginDescriptor(name = "Merlin EPG Center", description = _("More than just an EPG..."), where = [PluginDescriptor.WHERE_EXTENSIONSMENU,
		PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EVENTINFO], fnc = openMerlinEPGCenter, icon = "plugin.png")
		]
	return list
	
