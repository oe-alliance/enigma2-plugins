
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
from PartnerboxSetup import PartnerboxEntriesListConfigScreen, PartnerboxSetup
from Screens.EpgSelection import EPGSelection
from Components.EpgList import EPG_TYPE_SINGLE, EPG_TYPE_SIMILAR, EPG_TYPE_MULTI
from Screens.ChoiceBox import ChoiceBox
from Tools.BoundFunction import boundFunction
from Tools.Directories import fileExists
from PartnerboxFunctions import  SetPartnerboxTimerlist, isInTimerList, isInRepeatTimer, sendPartnerBoxWebCommand, FillE1TimerList, FillE2TimerList
import PartnerboxFunctions as partnerboxfunctions
from enigma import eServiceReference, eServiceCenter

# for localized messages
from . import _

baseEPGSelection__init__ = None
baseEPGSelection_zapTo = None
baseonSelectionChanged = None
basetimerAdd = None
basefinishedAdd = None
baseonCreate = None

def Partnerbox_EPGSelectionInit():
	global baseEPGSelection__init__, baseEPGSelection_zapTo, baseonSelectionChanged, basetimerAdd, basefinishedAdd, baseonCreate
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
	if baseonCreate is None:
		baseonCreate = EPGSelection.onCreate

	EPGSelection.__init__ = Partnerbox_EPGSelection__init__
	EPGSelection.zapTo = Partnerbox_EPGSelection_zapTo
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
	EPGSelection.RedCallback = RedCallback
	EPGSelection.setRedbutton = setRedbutton
	EPGSelection.remoteTimerMenu = remoteTimerMenu
	EPGSelection.PartnerboxInit = PartnerboxInit

def Partnerbox_EPGSelection__init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None, parent=None):
	#check if alternatives are defined
	#if isinstance(service, eServiceReference):
	#	if service.flags & (eServiceReference.isGroup):
	#		service = eServiceCenter.getInstance().list(eServiceReference("%s" %(service.toString()))).getContent("S")[0]
	baseEPGSelection__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB, parent)
	self.PartnerboxInit(True)

def PartnerboxInit(self, filterRef):
	self.filterRef = filterRef
	self.isTMBD = fileExists("/usr/lib/enigma2/python/Plugins/Extensions/TMBD/plugin.pyo")
	self.AutoTimer = fileExists("/usr/lib/enigma2/python/Plugins/Extensions/AutoTimer/SimpleThread.pyo")
	self.partnerboxentry = None
	partnerboxfunctions.remote_timer_list = []
	if int(config.plugins.Partnerbox.entriescount.value) >= 1:
		try:
			self.partnerboxentry = config.plugins.Partnerbox.Entries[0]
			partnerboxfunctions.CurrentIP = self.partnerboxentry.ip.value
		except:
			self.partnerboxentry = None
		self.setRedbutton()

def setRedbutton(self):
	if not hasattr(self, 'partnerboxentry'):
		self.PartnerboxInit(True)
	if not hasattr(self, 'zapFunc'):
		self.zapFunc = None
	if hasattr(self, 'partnerboxentry') and self.partnerboxentry is None:
		return
	if self.zapFunc:
		if config.plugins.Partnerbox.enablepartnerboxzapbuton.value:
			try:
				if int(config.plugins.Partnerbox.entriescount.value) > 1:
					self["key_red"].setText("PartnerBox")
				else:
					name_red = _("Zap/") + config.plugins.Partnerbox.Entries[0].name.value
					self["key_red"].setText(name_red)
			except: pass
	elif self.type == EPG_TYPE_SINGLE and not self.zapFunc and not self.isTMBD and not self.AutoTimer:
		try:
			if int(config.plugins.Partnerbox.entriescount.value) > 1:
				self["key_red"].setText("PartnerBox")
			else:
				self["key_red"].setText(config.plugins.Partnerbox.Entries[0].name.value)
		except: pass


def Partnerbox_EPGSelection_zapTo(self):
	if hasattr(self, 'partnerboxentry') and self.partnerboxentry is None:
		baseEPGSelection_zapTo(self)
		return
	try:
		if int(config.plugins.Partnerbox.entriescount.value) >= 1:
			if self.key_red_choice == self.ZAP and self.zapFunc:
				if config.plugins.Partnerbox.enablepartnerboxzapbuton.value:
					list = [
					(_("Standard Zap"), "zap"),
					(_("Partnerbox Entries"), "partnerboxentry"),
					(_("Partnerbox RemoteTimer"), "partnerboxremotetimer"),
					(_("Partnerbox Setup"), "partnerboxsetup"),
					]
					dlg = self.session.openWithCallback(self.RedCallback,ChoiceBox,title= _("Select action:"), list = list)
					dlg.setTitle(_("Choice list Partnerbox"))
				else:
					baseEPGSelection_zapTo(self)
			elif not (self.zapFunc and self.key_red_choice == self.ZAP):
				self.session.openWithCallback(self.NewPartnerBoxSelected, PartnerboxEntriesListConfigScreen, 0)
			else:
				baseEPGSelection_zapTo(self)
	except: 
		pass

def RedCallback(self, ret):
	ret = ret and ret[1]
	if ret:
		if ret == "zap":
			try:
				baseEPGSelection_zapTo(self)
			except:
				pass
		elif ret == "partnerboxentry":
			try:
				self.session.openWithCallback(self.NewPartnerBoxSelected, PartnerboxEntriesListConfigScreen, 0)
			except:
				pass
		elif ret == "partnerboxremotetimer":
			try:
				if hasattr(self, 'partnerboxentry') and self.partnerboxentry is not None:
					from plugin import RemoteTimer
					self.session.openWithCallback(self.DeleteTimerCallback, RemoteTimer, self.partnerboxentry, not_epg=True)
			except:
				pass
		elif ret == "partnerboxsetup":
			try:
				self.session.open(PartnerboxSetup)
			except:
				pass
		else:
			pass

def NewPartnerBoxSelected(self, session, what, partnerboxentry = None):
	try:
		if partnerboxentry is not None:
			self.partnerboxentry = partnerboxentry
			curService = None
			if self.type == EPG_TYPE_SINGLE and self.filterRef:
				curService = self.currentService.ref.toString()
			SetPartnerboxTimerlist(partnerboxentry, curService)
			Partnerbox_onSelectionChanged(self)
			name_red = ''
			if int(config.plugins.Partnerbox.entriescount.value) > 1:
				name_red = _("Zap/") + partnerboxentry.name.value
			else:
				if self.zapFunc:
					if config.plugins.Partnerbox.enablepartnerboxzapbuton.value:
						name_red = _("Zap/") + partnerboxentry.name.value
					else:
						name_red = _("Zap")
				else:
					name_red = partnerboxentry.name.value
			self["key_red"].setText(name_red)
			self["list"].l.invalidate()
	except:
		pass

def Partnerbox_onSelectionChanged(self):
	try:
		baseonSelectionChanged(self)
		self.CheckRemoteTimer()
		self.setRedbutton()
	except:
		pass

def Partnerbox_timerAdd(self):
	try:
		proceed = True
		if self.key_green_choice == self.REMOVE_TIMER:
			cur = self["list"].getCurrent()
			if cur is None: return
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
						self.session.openWithCallback(boundFunction(self.DeleteTimerConfirmed, timerentry), MessageBox, _("Do you really want to delete the remote timer \n%s ?") % name)
						return
					isRecordEvent = False
					eventid = event.getEventId()
					begin = event.getBeginTime()
					end = begin + event.getDuration()
					refstr = ':'.join(serviceref.ref.toString().split(':')[:11])
					for timer in self.session.nav.RecordTimer.timer_list:
						needed_ref = ':'.join(timer.service_ref.ref.toString().split(':')[:11]) == refstr
						if needed_ref and timer.eit == eventid and (begin < timer.begin <= end or timer.begin <= begin <= timer.end):
							isRecordEvent = True
							break
						elif needed_ref and timer.repeated and self.session.nav.RecordTimer.isInRepeatTimer(timer, event):
							isRecordEvent = True
							break
					if isRecordEvent:
						action = _("Edit internal timer")
					else:
						action = _("Add internal timer")
					menu = [(_("Edit remote timer"), "remote"), (action, "internal")]
					buttons = ["red", "green"]
					def timerAction(choice):
						if choice is not None:
							if choice[1] == "remote":
								self.remoteTimerMenu(timerentry)
							elif choice[1] == "internal":
								basetimerAdd(self)
					self.session.openWithCallback(timerAction, ChoiceBox, title= _("Select action for timer '%s':") % name, list=menu, keys=buttons)
		if proceed:
			basetimerAdd(self)
	except:
		pass

def remoteTimerMenu(self, timerentry):
	try:
		menu = [(_("Delete timer"), "delete"),(_("Timer Overview"), "timerlist")]
		buttons = ["red", "green"]
		title_text = timerentry.repeated and _("Attention, this is repeated timer!\n") or ""
		def remoteTimerAction(choice):
			if choice is not None:
				if choice[1] == "delete":
					self.session.openWithCallback(boundFunction(self.DeleteTimerConfirmed, timerentry), MessageBox, _("Do you really want to delete the timer \n%s ?") % timerentry.name)
				elif choice[1] == "timerlist":
					if hasattr(self, 'partnerboxentry') and self.partnerboxentry is not None:
						from plugin import RemoteTimer
						self.session.openWithCallback(self.DeleteTimerCallback, RemoteTimer, self.partnerboxentry, not_epg=True)
		self.session.openWithCallback(remoteTimerAction, ChoiceBox, title= title_text + _("Select action for remote timer '%s':") % timerentry.name, list=menu, keys=buttons)
	except:
		pass

def Partnerbox_finishedAdd(self, answer):
	try:
		basefinishedAdd(self,answer)
		self.CheckRemoteTimer()
		self.setRedbutton()
	except:
		pass

def Partnerbox_onCreate(self):
	try:
		if not hasattr(self, 'partnerboxentry'):
			self.PartnerboxInit(True)
		baseonCreate(self)
		self.GetPartnerboxTimerlist()
	except:
		pass

def GetPartnerboxTimerlist(self):
	try:
		if self.partnerboxentry is not None:
			ip = "%d.%d.%d.%d" % tuple(self.partnerboxentry.ip.value)
			port = self.partnerboxentry.port.value
			http = "http://%s:%d" % (ip,port)
			if int(self.partnerboxentry.enigma.value) == 0:
				sCommand = http + "/web/timerlist"
			else:
				sCommand = http + "/xml/timers"
			sendPartnerBoxWebCommand(sCommand, None,3, "root", self.partnerboxentry.password.value).addCallback(self.GetPartnerboxTimerlistCallback).addErrback(GetPartnerboxTimerlistCallbackError)
	except:
		pass

def GetPartnerboxTimerlistCallback(self, sxml = None):
	try:
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
		self.setRedbutton()
	except:
		pass

def GetPartnerboxTimerlistCallbackError(self, error = None):
	try:
		if error is not None:
			print str(error.getErrorMessage())
	except:
		pass

def CheckRemoteTimer(self):
	try:
		if self.key_green_choice != self.REMOVE_TIMER:
			cur = self["list"].getCurrent()
			if cur is None:
				return
			event = cur[0]
			serviceref = cur[1]
			if event is not None:
				timerentry = isInTimerList(event.getBeginTime(), event.getDuration(),serviceref.ref.toString(),event.getEventId(), partnerboxfunctions.remote_timer_list)
				if timerentry is not None:
					self["key_green"].setText(_("Timer menu"))
					self.key_green_choice = self.REMOVE_TIMER
	except:
		pass

def DeleteTimerConfirmed(self, timerentry, answer):
	try:
		if answer:
			ip = "%d.%d.%d.%d" % tuple(self.partnerboxentry.ip.value)
			port = self.partnerboxentry.port.value
			http = "http://%s:%d" % (ip,port)
			if int(self.partnerboxentry.enigma.value) == 0:
				refstr = ':'.join(str(timerentry.servicereference).split(':')[:11])
				sCommand = http + "/web/timerdelete?sRef=" + refstr + "&begin=" + ("%s"%(timerentry.timebegin)) + "&end=" +("%s"%(timerentry.timeend))
			else:
				sCommand = http + "/deleteTimerEvent?ref=" + timerentry.servicereference + "&start=" + ("%s"%(timerentry.timebegin)) + "&type=" +("%s"%(timerentry.type)) + "&force=yes"
			sendPartnerBoxWebCommand(sCommand, None,3, "root", self.partnerboxentry.password.value).addCallback(self.DeleteTimerCallback).addErrback(DeleteTimerCallbackError)
	except:
		pass

def DeleteTimerCallback(self, callback = None):
	try:
		curService = None
		if self.type == EPG_TYPE_SINGLE and self.filterRef:
			curService = self.currentService.ref.toString()
		SetPartnerboxTimerlist(self.partnerboxentry, curService)
		Partnerbox_onSelectionChanged(self)
		self["list"].l.invalidate()
	except:
		pass

def DeleteTimerCallbackError(self, error = None):
	try:
		if error is not None:
			self.session.open(MessageBox,str(_(error.getErrorMessage())),MessageBox.TYPE_INFO)
	except:
		pass
