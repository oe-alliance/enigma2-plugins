#######################################################################
#
#    Channel Number Renderer for Dreambox/Enigma-2
#    Coded by Vali (c)2010
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#  To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#  or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
#######################################################################

from Components.VariableText import VariableText
from enigma import eLabel, eServiceCenter
from Renderer import Renderer
from Screens.InfoBar import InfoBar

MYCHANSEL = InfoBar.instance.servicelist

class vRendChNumber(Renderer, VariableText):
	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)
	GUI_WIDGET = eLabel
	
	def changed(self, what):
		if not self.suspended:
			service = self.source.service
			info = service and service.info()
			if info is None:
				self.text = " "
				return
			markersOffset = 0
			myRoot = MYCHANSEL.getRoot()
			mySrv = MYCHANSEL.servicelist.getCurrent()
			chx = MYCHANSEL.servicelist.l.lookupService(mySrv)
			if not MYCHANSEL.inBouquet():
				pass
			else:
				serviceHandler = eServiceCenter.getInstance()
				mySSS = serviceHandler.list(myRoot)
				SRVList = mySSS and mySSS.getContent("SN", True)
				for i in list(range(len(SRVList))):
					if chx == i:
						break
					testlinet = SRVList[i]
					testline = testlinet[0].split(":")
					if testline[1] == "64":
						markersOffset = markersOffset + 1
			chx = (chx - markersOffset) + 1
			rx = MYCHANSEL.getBouquetNumOffset(myRoot)
			self.text = str(chx + rx)

