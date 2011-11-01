#
#  MerlinEPGCenter E2 Plugin
#
#  $Id: HelperFunctions.py,v 1.0 2011-02-14 21:53:00 shaderman Exp $
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

#PYTHON IMPORTS
from datetime import timedelta as dt_timedelta, date as dt_date
from time import localtime, time

# ENIGMA IMPORTS
from Components.config import config
from Components.ScrollLabel import ScrollLabel
from enigma import eEnv, eSize, fontRenderClass, ePoint, eSlider, eTimer, iRecordableService
import NavigationInstance
from RecordTimer import RecordTimerEntry, AFTEREVENT
from Screens.MessageBox import MessageBox
import Screens.Standby
from Tools.Directories import fileExists, resolveFilename, SCOPE_SKIN_IMAGE, SCOPE_CURRENT_SKIN, SCOPE_CURRENT_PLUGIN
from Tools.LoadPixmap import LoadPixmap

# for localized messages
from . import _


LIST_TYPE_EPG = 0
LIST_TYPE_UPCOMING = 1


class ResizeScrollLabel(ScrollLabel):
	def __init__(self, text = ""):
		ScrollLabel.__init__(self, text)
		
	def resize(self, s):
		lineheight=fontRenderClass.getInstance().getLineHeight( self.long_text.getFont() )
		if not lineheight:
			lineheight = 30 # assume a random lineheight if nothing is visible
		lines = (int)(s.height() / lineheight)
		self.pageHeight = (int)(lines * lineheight)
		self.instance.resize(eSize(s.width(), self.pageHeight+(int)(lineheight/6)))
		self.scrollbar.move(ePoint(s.width()-20,0))
		self.scrollbar.resize(eSize(20,self.pageHeight+(int)(lineheight/6)))
		self.long_text.resize(eSize(s.width()-30, self.pageHeight*16))
		self.setText(self.message)

class PiconLoader():
	def __init__(self):
		self.nameCache = { }
		config.plugins.merlinEpgCenter.epgPaths.addNotifier(self.piconPathChanged, initial_call = False)
		
	def getPiconFilename(self, sRef):
		pngname = ""
		# strip all after last :
		pos = sRef.rfind(':')
		if pos != -1:
			sRef = sRef[:pos].rstrip(':').replace(':','_')
		pngname = self.nameCache.get(sRef, "")
		if pngname == "":
			pngname = self.findPicon(sRef)
			if pngname != "":
				self.nameCache[sRef] = pngname
			if pngname == "": # no picon for service found
				pngname = self.nameCache.get("default", "")
				if pngname == "": # no default yet in cache..
					pngname = self.findPicon("picon_default")
					if pngname == "":
						pngname = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/PiconMissing_small.png")
					self.nameCache["default"] = pngname
		return pngname
		
	def getPicon(self, pngname):
		return LoadPixmap(cached = True, path = self.getPiconFilename(pngname))
		
	def findPicon(self, sRef):
		pngname = config.plugins.merlinEpgCenter.epgPaths.value + sRef + ".png"
		if not fileExists(pngname):
			pngname = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/PiconMissing_small.png")
		return pngname
		
	def piconPathChanged(self, configElement = None):
		self.nameCache.clear()
		
	def removeNotifier(self):
		config.plugins.merlinEpgCenter.epgPaths.notifiers.remove(self.piconPathChanged)
		
def findDefaultPicon(serviceName):
	searchPaths = (eEnv.resolve('${datadir}/enigma2/%s/'), '/media/cf/%s/', '/media/usb/%s/')
	
	pos = serviceName.rfind(':')
	if pos != -1:
		serviceName = serviceName[:pos].rstrip(':').replace(':','_')
	
	for path in searchPaths:
		pngname = (path % "picon") + serviceName + ".png"
		if fileExists(pngname):
			return pngname
	return resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/PiconMissing.png")
	
# derived from Tools.FuzzyDate
def getFuzzyDay(t):
	d = localtime(t)
	nt = time()
	n = localtime()
	
	if d[:3] == n[:3]:
		# same day
		date = _("Today")
	elif dt_date.fromtimestamp(t) == dt_date.today() + dt_timedelta(days = 1):
		# next day
		date = _("Tomorrow")
	elif ((t - nt) < 7*86400) and (nt < t):
		# same week
		date = (_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"), _("Friday"), _("Saturday"), _("Sunday"))[d[6]]
	elif d[0] == n[0]:
		# same year
		date = "%d.%d.%d" % (d[2], d[1], d[0])
	else:
		date = _("Unknown date")
		
	return date
	
# used to let timer pixmaps blink in our lists
class BlinkTimer():
	def __init__(self, session):
		self.session = session
		self.state = False # blinking state
		self.lists = [] # epg list, upcoming list
		self.listSets = [set(), set()] # 1st set for epg list, 2nd for upcoming list
		self.delay = 0
		self.stopping = False
		self.timerRunning = False
		self.timer = eTimer()
		self.timer.callback.append(self.changeBlinkState)
		self.session.nav.record_event.append(self.gotRecordEvent)
		self.callbacks = []
		
	def gotRecordEvent(self, service, event):
		if event in (iRecordableService.evEnd, iRecordableService.evStart, None):
			numRecs = len(self.session.nav.getRecordings())
			if numRecs and not self.timerRunning:
				self.timer.start(1000)
				self.timerRunning = True
				# notify the EpgCenterList instances, they need to invalidate to start blinking
				for x in self.callbacks:
					x()
			elif not numRecs and self.timerRunning and not self.stopping:
				self.stopping = True
				
	def shutdown(self):
		self.session.nav.record_event.remove(self.gotRecordEvent)
		self.timer.callback.remove(self.changeBlinkState)
			
	def appendList(self, l):
		self.lists.append(l)
		
	def changeBlinkState(self):
		self.state = not self.state
		
		i = 0
		while i < 2:
			for idx in self.listSets[i]:
				self.lists[i].l.invalidateEntry(idx)
			i += 1
			
		if self.stopping:
			self.delayStop()
			
	def getBlinkState(self):
		return self.state
		
	def getIsRunning(self):
		return self.timerRunning
		
	def getIsStopping(self):
		return self.stopping
		
	def getIsInList(self, idx):
		return idx in self.listSets[LIST_TYPE_EPG]
		
	def gotListElements(self):
		if len(self.listSets[LIST_TYPE_EPG]) or len(self.listSets[LIST_TYPE_UPCOMING]):
			return True
		else:
			return False
			
	# make one more tick befor stopping the timer to show the picon again
	def delayStop(self):
		self.stopping = True
		self.delay += 1
		
		if self.delay > 1:
			self.timer.stop()
			self.delay = 0
			self.stopping = False
			self.state = False
			self.timerRunning = False
			
	def updateEntry(self, listType, idx, isRunning):
		if idx in self.listSets[listType]:
			if not isRunning:
				self.listSets[listType].discard(idx)
		elif isRunning:
			self.listSets[listType].add(idx)
			if not self.timerRunning and self.gotListElements():
				self.delay = 0
				self.stopping = False
				
	def reset(self):
		if not self.timerRunning:
			return
			
		self.listSets[LIST_TYPE_EPG].clear()
		self.listSets[LIST_TYPE_UPCOMING].clear()
		
class RecTimerEntry(RecordTimerEntry):
	def __init__(self, session, serviceref, begin, end, name, description, eit, disabled = False, justplay = False, afterEvent = AFTEREVENT.AUTO, checkOldTimers = False, dirname = None, tags = None):
		self.session = session
		RecordTimerEntry.__init__(self, serviceref, begin, end, name, description, eit, disabled = False, justplay = False, afterEvent = AFTEREVENT.AUTO, checkOldTimers = False, dirname = None, tags = None)
		
	def activate(self):
		next_state = self.state + 1
		self.log(5, "activating state %d" % next_state)

		if next_state == self.StatePrepared:
			if self.tryPrepare():
				self.log(6, "prepare ok, waiting for begin")
				# create file to "reserve" the filename
				# because another recording at the same time on another service can try to record the same event
				# i.e. cable / sat.. then the second recording needs an own extension... when we create the file
				# here than calculateFilename is happy
				if not self.justplay:
					open(self.Filename + ".ts", "w").close() 
				# fine. it worked, resources are allocated.
				self.next_activation = self.begin
				self.backoff = 0
				return True

			self.log(7, "prepare failed")
			if self.first_try_prepare:
				self.first_try_prepare = False
				cur_ref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
				if cur_ref and not cur_ref.getPath():
					if not config.recording.asktozap.value:
						self.log(8, "asking user to zap away")
						if config.plugins.merlinEpgCenter.showTimerMessages.value:
							self.session.openWithCallback(self.failureCB, MessageBox, _("A timer failed to record!\nDisable TV and try again?\n"), timeout=20)
					else: # zap without asking
						self.log(9, "zap without asking")
						if config.plugins.merlinEpgCenter.showTimerMessages.value:
							self.session.open(MessageBox, _("In order to record a timer, the TV was switched to the recording service!\n"), type=MessageBox.TYPE_INFO, timeout=config.merlin2.timeout_message_channel_switch.value)
						self.failureCB(True)
				elif cur_ref:
					self.log(8, "currently running service is not a live service.. so stop it makes no sense")
				else:
					self.log(8, "currently no service running... so we dont need to stop it")
			return False
		elif next_state == self.StateRunning:
			# if this timer has been cancelled, just go to "end" state.
			if self.cancelled:
				return True

			if self.justplay:
				if Screens.Standby.inStandby:
					self.log(11, "wakeup and zap")
					#set service to zap after standby
					Screens.Standby.inStandby.prev_running_service = self.service_ref.ref
					#wakeup standby
					Screens.Standby.inStandby.Power()
				else:
					self.log(11, "zapping")
					NavigationInstance.instance.playService(self.service_ref.ref)
				return True
			else:
				self.log(11, "start recording")
				record_res = self.record_service.start()
				
				if record_res:
					self.log(13, "start record returned %d" % record_res)
					self.do_backoff()
					# retry
					self.begin = time() + self.backoff
					return False

				return True
		elif next_state == self.StateEnded:
			old_end = self.end
			if self.setAutoincreaseEnd():
				self.log(12, "autoincrase recording %d minute(s)" % int((self.end - old_end)/60))
				self.state -= 1
				return True
			self.log(12, "stop recording")
			if not self.justplay:
				NavigationInstance.instance.stopRecordService(self.record_service)
				self.record_service = None
			if self.afterEvent == AFTEREVENT.STANDBY:
				if not Screens.Standby.inStandby and config.plugins.merlinEpgCenter.showTimerMessages.value: # not already in standby
					self.session.openWithCallback(self.sendStandbyNotification, MessageBox, _("A finished record timer wants to set your\nDreambox to standby. Do that now?"), timeout = 20)
			elif self.afterEvent == AFTEREVENT.DEEPSTANDBY:
				if not Screens.Standby.inTryQuitMainloop: # not a shutdown messagebox is open
					if Screens.Standby.inStandby: # in standby
						RecordTimerEntry.TryQuitMainloop() # start shutdown handling without screen
					elif config.plugins.merlinEpgCenter.showTimerMessages.value:
						self.session.openWithCallback(self.sendTryQuitMainloopNotification, MessageBox, _("A finished record timer wants to shut down\nyour Dreambox. Shutdown now?"), timeout = 20)
			return True
			
