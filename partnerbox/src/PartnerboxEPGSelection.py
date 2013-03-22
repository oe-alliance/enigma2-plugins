
#  Partnerbox E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2009
#  Support: www.dreambox-tools.info
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.config import config
from PartnerboxSetup import PartnerboxEntriesListConfigScreen
from Screens.EpgSelection import EPGSelection
from Components.EpgList import EPG_TYPE_SINGLE, EPG_TYPE_SIMILAR, EPG_TYPE_MULTI, EPG_TYPE_GRAPH
from Tools.BoundFunction import boundFunction
from PartnerboxFunctions import  SetPartnerboxTimerlist, isInTimerList, sendPartnerBoxWebCommand, FillE1TimerList, FillE2TimerList
import PartnerboxFunctions as partnerboxfunctions

# for localized messages
from . import _

baseEPGSelection__init__ = None
baseEPGSelection_ZapTo = None
baseonSelectionChanged = None
basetimerAdd = None
basefinishedAdd = None
baseonCreate = None

def Partnerbox_EPGSelectionInit():
	global baseEPGSelection__init__, baseEPGSelection_ZapTo, baseonSelectionChanged, basetimerAdd, basefinishedAdd, baseonCreate
	if baseEPGSelection__init__ is None:
		baseEPGSelection__init__ = EPGSelection.__init__
	if baseEPGSelection_ZapTo is None:
		baseEPGSelection_ZapTo = EPGSelection.ZapTo
	if baseonSelectionChanged is None:
		baseonSelectionChanged = EPGSelection.onSelectionChanged
	if basetimerAdd is None:
		basetimerAdd = EPGSelection.timerAdd
	if basefinishedAdd is None:
		basefinishedAdd = EPGSelection.finishedAdd
	if baseonCreate is None:
		baseonCreate = EPGSelection.onCreate

	EPGSelection.__init__ = Partnerbox_EPGSelection__init__
	EPGSelection.ZapTo = Partnerbox_EPGSelection_ZapTo
	EPGSelection.onSelectionChanged = Partnerbox_onSelectionChanged
	EPGSelection.timerAdd = Partnerbox_timerAdd
	EPGSelection.finishedAdd = Partnerbox_finishedAdd
	EPGSelection.onCreate = Partnerbox_onCreate
	# new methods
	EPGSelection.NewPartnerBoxSelected = NewPartnerBoxSelected
	EPGSelection.GetPartnerboxTimerlistCallback = GetPartnerboxTimerlistCallback
	EPGSelection.GetPartnerboxTimerlistCallbackError = GetPartnerboxTimerlistCallbackError
	EPGSelection.CheckRemoteTimer = CheckRemoteTimer
	EPGSelection.DeleteTimerConfirmed = DeleteTimerConfirmed
	EPGSelection.DeleteTimerCallback = DeleteTimerCallback
	EPGSelection.GetPartnerboxTimerlist = GetPartnerboxTimerlist
	EPGSelection.PartnerboxInit = PartnerboxInit

def Partnerbox_EPGSelection__init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None, EPGtype = None):
	baseEPGSelection__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB, EPGtype)
	self.PartnerboxInit(True)

def PartnerboxInit(self, filterRef):
	self.filterRef = filterRef
	self.partnerboxentry = None
	partnerboxfunctions.remote_timer_list = []
	if int(config.plugins.Partnerbox.entriescount.value) >= 1:
		try: 
			self.partnerboxentry = config.plugins.Partnerbox.Entries[0]
			partnerboxfunctions.CurrentIP = self.partnerboxentry.ip.value
		except: self.partnerboxentry = None
	#try:self["key_red"].setText(config.plugins.Partnerbox.Entries[0].name.value)
	#except: pass
	

def Partnerbox_EPGSelection_ZapTo(self): # just used in multiepg
	baseEPGSelection_ZapTo(self)

def NewPartnerBoxSelected(self, session, what, partnerboxentry = None):
	if partnerboxentry is not None:
		self.partnerboxentry = partnerboxentry
		curService = None
		if self.type == EPG_TYPE_SINGLE and self.filterRef:
			curService = self.currentService.ref.toString()
		SetPartnerboxTimerlist(partnerboxentry, curService)
		Partnerbox_onSelectionChanged(self)
		self["key_red"].setText(partnerboxentry.name.value)
		self["list"].l.invalidate() # immer zeichnen, da neue Box ausgewaehlt wurde

def Partnerbox_onSelectionChanged(self):
	baseonSelectionChanged(self)
	self.CheckRemoteTimer()

def Partnerbox_timerAdd(self):
	proceed = True
	if self.key_green_choice == self.REMOVE_TIMER:
		cur = self["list"].getCurrent()
		event = cur[0]
		serviceref = cur[1]
		if event is not None:
			timerentry = isInTimerList(event.getBeginTime(), event.getDuration(),serviceref.ref.toString(), event.getEventId(), partnerboxfunctions.remote_timer_list)
			if timerentry is not None:
				proceed = False
				if int(self.partnerboxentry.enigma.value) == 0:
					name = timerentry.name
				else:
					name = timerentry.description
				self.session.openWithCallback(boundFunction(self.DeleteTimerConfirmed,timerentry), MessageBox, _("Do you really want to delete the timer \n%s ?") % name)
	if proceed:basetimerAdd(self)

def Partnerbox_finishedAdd(self, answer):
	basefinishedAdd(self,answer)
	self.CheckRemoteTimer()

def Partnerbox_onCreate(self):
	baseonCreate(self)
	self.GetPartnerboxTimerlist()

def GetPartnerboxTimerlist(self):
	if self.partnerboxentry is not None:
		ip = "%d.%d.%d.%d" % tuple(self.partnerboxentry.ip.value)
		port = self.partnerboxentry.port.value
		http = "http://%s:%d" % (ip,port)
		if int(self.partnerboxentry.enigma.value) == 0:
			sCommand = http + "/web/timerlist"
		else:
			sCommand = http + "/xml/timers"
		print "[Partnerbox] %s"%sCommand
		sendPartnerBoxWebCommand(sCommand, None,3, "root", self.partnerboxentry.password.value).addCallback(self.GetPartnerboxTimerlistCallback).addErrback(GetPartnerboxTimerlistCallbackError)


def GetPartnerboxTimerlistCallback(self, sxml = None):
	if sxml is not None:
		curService = None
		if self.type == EPG_TYPE_SINGLE and self.filterRef:
			curService = self.currentService.ref.toString()
		if int(self.partnerboxentry.enigma.value) == 0:
			partnerboxfunctions.remote_timer_list = FillE2TimerList(sxml, curService)
		else:
			partnerboxfunctions.remote_timer_list = FillE1TimerList(sxml, curService)
	if len(partnerboxfunctions.remote_timer_list) != 0:
		Partnerbox_onSelectionChanged(self)
		self["list"].l.invalidate()

def GetPartnerboxTimerlistCallbackError(self, error = None):
	if error is not None:
		print str(error.getErrorMessage())

def CheckRemoteTimer(self):
	if self.key_green_choice != self.REMOVE_TIMER:
		cur = self["list"].getCurrent()
		if cur is None:
			return
		event = cur[0]
		serviceref = cur[1]
		if event is not None:
			timerentry = isInTimerList(event.getBeginTime(), event.getDuration(),serviceref.ref.toString(),event.getEventId(), partnerboxfunctions.remote_timer_list)
			if timerentry is not None:
				self["key_green"].setText(_("Remove timer"))
				self.key_green_choice = self.REMOVE_TIMER

def DeleteTimerConfirmed (self, timerentry, answer):
	if answer:
		ip = "%d.%d.%d.%d" % tuple(self.partnerboxentry.ip.value)
		port = self.partnerboxentry.port.value
		http = "http://%s:%d" % (ip,port)
		if int(self.partnerboxentry.enigma.value) == 0:
			sCommand = http + "/web/timerdelete?sRef=" + timerentry.servicereference + "&begin=" + ("%s"%(timerentry.timebegin)) + "&end=" +("%s"%(timerentry.timeend))
		else:
			sCommand = http + "/deleteTimerEvent?ref=" + timerentry.servicereference + "&start=" + ("%s"%(timerentry.timebegin)) + "&type=" +("%s"%(timerentry.type)) + "&force=yes"
		sendPartnerBoxWebCommand(sCommand, None,3, "root", self.partnerboxentry.password.value).addCallback(self.DeleteTimerCallback).addErrback(DeleteTimerCallbackError)

def DeleteTimerCallback(self, callback = None):
	curService = None
	if self.type == EPG_TYPE_SINGLE and self.filterRef:
		curService = self.currentService.ref.toString()
	SetPartnerboxTimerlist(self.partnerboxentry, curService)
	Partnerbox_onSelectionChanged(self)
	self["list"].l.invalidate() # immer zeichnen, da ja was geloescht wurde

def DeleteTimerCallbackError(self, error = None):
	if error is not None:
		self.session.open(MessageBox, str(error.getErrorMessage()),MessageBox.TYPE_INFO)

