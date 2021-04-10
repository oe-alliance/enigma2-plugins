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


# for localized messages
from . import _

#PYTHON IMPORTS
from datetime import timedelta as dt_timedelta, date as dt_date
from time import localtime, time

# ENIGMA IMPORTS
from Components.config import config
from Components.ScrollLabel import ScrollLabel
from enigma import eEnv, eSize, fontRenderClass, ePoint, eSlider, eTimer, iRecordableService, eDVBVolumecontrol
import NavigationInstance
from RecordTimer import RecordTimerEntry, AFTEREVENT
from Screens.MessageBox import MessageBox
import Screens.Standby
from Tools.Directories import fileExists, resolveFilename, SCOPE_SKIN_IMAGE, SCOPE_CURRENT_SKIN, SCOPE_CURRENT_PLUGIN
from Tools.LoadPixmap import LoadPixmap


LIST_TYPE_EPG = 0
LIST_TYPE_UPCOMING = 1

WEEKSECONDS = 7 * 86400
WEEKDAYS = (_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"), _("Friday"), _("Saturday"), _("Sunday"))


# most functions were taken and modified from Components.VolumeControl
class EmbeddedVolumeControl():
	def __init__(self):
		self.volctrl = eDVBVolumecontrol.getInstance()
		self.hideVolTimer = eTimer()
		self.hideVolTimer.callback.append(self.volHide)
		
	def volSave(self):
		if self.volctrl.isMuted():
			config.audio.volume.value = 0
		else:
			config.audio.volume.value = self.volctrl.getVolume()
		config.audio.volume.save()
		
	def volUp(self):
		self.setVolume(+1)
		
	def volDown(self):
		self.setVolume(-1)
		
	def setVolume(self, direction):
		oldvol = self.volctrl.getVolume()
		if direction > 0:
			self.volctrl.volumeUp()
		else:
			self.volctrl.volumeDown()
		is_muted = self.volctrl.isMuted()
		vol = self.volctrl.getVolume()
		self["volume"].show()
		if is_muted:
			self.volMute() # unmute
		elif not vol:
			self.volMute(False, True) # mute but dont show mute symbol
		if self.volctrl.isMuted():
			self["volume"].setValue(0)
		else:
			self["volume"].setValue(self.volctrl.getVolume())
		self.volSave()
		self.hideVolTimer.start(3000, True)
		
	def volHide(self):
		self["volume"].hide()
		
	def volMute(self, showMuteSymbol=True, force=False):
		vol = self.volctrl.getVolume()
		if vol or force:
			self.volctrl.volumeToggleMute()
			if self.volctrl.isMuted():
				if showMuteSymbol:
					self["mute"].show()
				self["volume"].setValue(0)
			else:
				self["mute"].hide()
				self["volume"].setValue(vol)
				
	def getIsMuted(self):
		return self.volctrl.isMuted()
		
	def setMutePixmap(self):
		if self.volctrl.isMuted():
			self["mute"].show()
		else:
			self["mute"].hide()
			
class ResizeScrollLabel(ScrollLabel):
	def __init__(self, text=""):
		ScrollLabel.__init__(self, text)
		
	def resize(self, s):
		lineheight = fontRenderClass.getInstance().getLineHeight(self.long_text.getFont())
		if not lineheight:
			lineheight = 30 # assume a random lineheight if nothing is visible
		lines = (int)(s.height() / lineheight)
		self.pageHeight = (int)(lines * lineheight)
		self.instance.resize(eSize(s.width(), self.pageHeight + (int)(lineheight / 6)))
		self.scrollbar.move(ePoint(s.width() - 20, 0))
		self.scrollbar.resize(eSize(20, self.pageHeight + (int)(lineheight / 6)))
		self.long_text.resize(eSize(s.width() - 30, self.pageHeight * 16))
		self.setText(self.message)

class PiconLoader():
	def __init__(self):
		self.nameCache = {}
		config.plugins.merlinEpgCenter.epgPaths.addNotifier(self.piconPathChanged, initial_call=False)
		
	def getPiconFilename(self, sRef):
		pngname = ""
		# strip all after last :
		pos = sRef.rfind(':')
		if pos != -1:
			sRef = sRef[:pos].rstrip(':').replace(':', '_')
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
		return LoadPixmap(cached=True, path=self.getPiconFilename(pngname))
		
	def findPicon(self, sRef):
		pngname = config.plugins.merlinEpgCenter.epgPaths.value + sRef + ".png"
		if not fileExists(pngname):
			pngname = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinEPGCenter/images/PiconMissing_small.png")
		return pngname
		
	def piconPathChanged(self, configElement=None):
		self.nameCache.clear()
		
def findDefaultPicon(serviceName):
	searchPaths = (eEnv.resolve('${datadir}/enigma2/%s/'), '/media/cf/%s/', '/media/usb/%s/')
	
	pos = serviceName.rfind(':')
	if pos != -1:
		serviceName = serviceName[:pos].rstrip(':').replace(':', '_')
	
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
	elif dt_date.fromtimestamp(t) == dt_date.today() + dt_timedelta(days=1):
		# next day
		date = _("Tomorrow")
	elif nt < t and (t - nt) < WEEKSECONDS:
		# same week
		date = WEEKDAYS[d.tm_wday]
	else:
		date = "%d.%d.%d" % (d.tm_mday, d.tm_mon, d.tm_year)
		
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
		self.callbacks = []
		self.resume()
		
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
				
	def suspend(self):
		if self.gotRecordEvent in self.session.nav.record_event:
			self.session.nav.record_event.remove(self.gotRecordEvent)
		if self.changeBlinkState in self.timer.callback:
			self.timer.callback.remove(self.changeBlinkState)
		if self.getIsRunning():
			self.timer.stop()
			self.delay = 0
			self.stopping = False
			self.state = False
			self.timerRunning = False
			
	def resume(self):
		self.timer.callback.insert(0, self.changeBlinkState) # order is important, this callback must be called first!
		self.session.nav.record_event.append(self.gotRecordEvent)
		if self.session.nav.RecordTimer.isRecording():
			self.gotRecordEvent(None, None)
			
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
		
# interface between AutoTimer and our timer list
class TimerListObject(object):
	def __init__(self, begin, end, service_ref, name, justplay, disabled, autoTimerId, match, searchType, counter, counterLeft, destination, services, bouquets, includedDays, excludedDays):
		self.begin = begin
		self.end = end
		self.service_ref = service_ref
		self.name = name
		self.justplay = justplay
		self.disabled = disabled
		self.autoTimerId = autoTimerId
		self.state = 0 # TimerEntry.StateWaiting
		
		# additional information
		self.match = match
		self.searchType = searchType
		self.counter = counter
		self.counterLeft = counterLeft
		self.destination = destination
		self.services = services
		self.bouquets = bouquets
		self.includedDays = includedDays
		self.excludedDays = excludedDays
		
	def isRunning(self):
		return False
		
