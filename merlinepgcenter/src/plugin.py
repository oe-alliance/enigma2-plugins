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

# ENIGMA IMPORTS
#from Components.config import config
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import InfoBar

# OWN IMPORTS
from MerlinEPGCenter import MerlinEPGCenter
from EpgCenterList import MULTI_EPG_NOW, SINGLE_EPG

# for localized messages
from . import _


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

def autostart(session, **kwargs):
	infoBarFunctionSaver = InfoBarFunctionSaver()
	
# open "single epg" tab
def startMerlinEPGCenterSingle(self):
	openMerlinEPGCenterTab(self.session, SINGLE_EPG)
	
# open "multi epg now" tab
def startMerlinEPGCenterMulti(self):
	openMerlinEPGCenterTab(self.session, MULTI_EPG_NOW)
	
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
	servicelist, currentBouquet, bouquetList, currentIndex = getBouquetInformation()
	session.open(MerlinEPGCenter, servicelist, currentBouquet, bouquetList, currentIndex)
	
def openMerlinEPGCenterTab(session, startWithTab, **kwargs):
	servicelist, currentBouquet, bouquetList, currentIndex = getBouquetInformation()
	session.open(MerlinEPGCenter, servicelist, currentBouquet, bouquetList, currentIndex, startWithTab)
	
def Plugins(**kwargs):
	p = PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart)
	list = [PluginDescriptor(name = "Merlin EPG Center", description = _("More than just an EPG..."), where = [PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EVENTINFO], fnc = openMerlinEPGCenter)]
	list.append(p)
	return list
	
