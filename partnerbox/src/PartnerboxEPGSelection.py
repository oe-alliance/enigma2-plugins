
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
from Tools.BoundFunction import boundFunction
from PartnerboxFunctions import  SetPartnerboxTimerlist, isInTimerList, sendPartnerBoxWebCommand
import PartnerboxFunctions as partnerboxfunctions

baseEPGSelection__init__ = None
baseEPGSelection_zapTo = None
baseonSelectionChanged = None
basetimerAdd = None
basefinishedAdd = None

def Partnerbox_EPGSelectionInit():
	global baseEPGSelection__init__, baseEPGSelection_zapTo, baseonSelectionChanged, basetimerAdd, basefinishedAdd
	if baseEPGSelection__init__ is None:
		baseEPGSelection__init__ = EPGSelection.__init__
	if baseEPGSelection_zapTo is None:
		baseEPGSelection_zapTo = EPGSelection.zapTo
	if baseonSelectionChanged is None:
		baseonSelectionChanged = EPGSelection.onSelectionChanged
	if basetimerAdd is None:
		basetimerAdd = EPGSelection.timerAdd
	if basefinishedAdd is None:
		basefinishedAdd = EPGSelection.finishedAdd
	if partnerboxfunctions.remote_timer_list is None:
		partnerboxfunctions.remote_timer_list = []
	EPGSelection.__init__ = Partnerbox_EPGSelection__init__
	EPGSelection.zapTo = Partnerbox_EPGSelection_zapTo
	EPGSelection.onSelectionChanged = Partnerbox_onSelectionChanged
	EPGSelection.timerAdd = Partnerbox_timerAdd
	EPGSelection.finishedAdd = Partnerbox_finishedAdd


def Partnerbox_EPGSelection__init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None):

	if int(config.plugins.Partnerbox.entriescount.value) >= 1:
		try: self.partnerboxentry = config.plugins.Partnerbox.Entries[0]
		except: self.partnerboxentry = None
	baseEPGSelection__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB)
	try:self["key_red"].setText(config.plugins.Partnerbox.Entries[0].name.value)
	except: pass
	

def Partnerbox_EPGSelection_zapTo(self): # just used in multiepg
	if not (self.zapFunc and self.key_red_choice == self.ZAP):
		self.session.openWithCallback(boundFunction(NewPartnerBoxSelected,self), PartnerboxEntriesListConfigScreen, 0)
	else:
		baseEPGSelection_zapTo(self)

def NewPartnerBoxSelected(self, session, what, partnerboxentry = None):
	if partnerboxentry is not None:
		self.partnerboxentry = partnerboxentry
		SetPartnerboxTimerlist(partnerboxentry)
		Partnerbox_onSelectionChanged(self)
		self["key_red"].setText(partnerboxentry.name.value)
		self["list"].l.invalidate()

def Partnerbox_onSelectionChanged(self):
	baseonSelectionChanged(self)
	CheckRemoteTimer(self)

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
				self.session.openWithCallback(boundFunction(DeleteTimerConfirmed,self, timerentry), MessageBox, _("Do you really want to delete the timer \n%s ?") % name)
	if proceed:basetimerAdd(self)

def Partnerbox_finishedAdd(self, answer):
	basefinishedAdd(self,answer)
	CheckRemoteTimer(self)

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
		sendPartnerBoxWebCommand(sCommand, None,3, "root", self.partnerboxentry.password.value).addCallback(boundFunction(DeleteTimerCallback,self)).addErrback(boundFunction(DeleteTimerCallbackError,self))

def DeleteTimerCallback(self, callback = None):
	SetPartnerboxTimerlist(self.partnerboxentry)
	Partnerbox_onSelectionChanged(self)
	self["list"].l.invalidate()

def DeleteTimerCallbackError(self, error = None):
	if error is not None:
		self.session.open(MessageBox, str(error.getErrorMessage()),MessageBox.TYPE_INFO)

