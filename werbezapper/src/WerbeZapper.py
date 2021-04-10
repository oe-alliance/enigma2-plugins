import math

# for localized messages
from . import _

# GUI (Screens)
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Notifications import AddPopup

# Timer
from enigma import eTimer

# For monitoring
from enigma import iPlayableService
from Components.ServiceEventTracker import ServiceEventTracker

# Get remaining time if timer is already active
from time import time

# Get event for monitoring
from enigma import eEPGCache

# Config
from Components.config import *


class WerbeZapperChoiceBox(ChoiceBox):
	def __init__(self, session, title="", list=[], keys=None, selection=0, zap_time=0, zap_service=None, monitored_event=None, monitored_service=None, skin_name=[]):
		ChoiceBox.__init__(self, session, title, list, keys, selection, skin_name)
		
		self.update_timer = eTimer()
		self.update_timer.callback.append(self.update)
		
		self.zap_time = zap_time
		self.zap_service = zap_service
		self.monitored_event = monitored_event
		self.monitored_service = monitored_service
		
		# Start timer to update the ChoiceBox every second
		self.update_timer.start(1000)
		self.setTitle("WerbeZapper")
		self.update()

	def update(self):
		#TODO getServiceName() begin end
		text = ""
		if self.monitored_event:
			name = self.monitored_event and self.monitored_event.getEventName()
			remaining = (self.monitored_event.getDuration() - (time() - self.monitored_event.getBeginTime()))
			if remaining > 0:
				text += _("Monitoring: %s (%d:%02d Min)") % (name, remaining/60, remaining%60)
		if self.zap_time:
			remaining = int(math.floor(self.zap_time - time()))
			if remaining > 0:
				remainstr = ("%d:%02d") % (remaining/60, remaining%60)
				text += "\n" + _("Zapping back in %d:%02d Min") % (remaining/60, remaining%60)
		if text:
			self.setText(text)

	def setText(self, text):
		self["text"].setText(text)

	def close(self, param=None):
		self.update_timer.stop()
		ChoiceBox.close(self, param)


class WerbeZapper(Screen):
	"""Simple Plugin to automatically zap back to a Service after a given amount
	   of time."""
	def __init__(self, session, servicelist, cleanupfnc=None):
		Screen.__init__(self, session)
		
		# Save Session&Servicelist
		self.session = session
		self.servicelist = servicelist
		
		# Create zap timer
		self.zap_time = None
		self.zap_timer = eTimer()
		self.zap_timer.callback.append(self.zap)

		# Create event monitoring timer
		self.monitor_timer = eTimer()
		self.monitor_timer.callback.append(self.stopMonitoring)

		# Create delay timer
		self.delay_timer = eTimer()
		self.delay_timer.callback.append(self.zappedAway)

		# Initialize services
		self.zap_service = None
		self.move_service = None
		self.root = None
		
		#	Initialize monitoring
		self.monitored_service = None
		self.monitored_event = None
		self.__event_tracker = None
		
		# Keep Cleanup
		self.cleanupfnc = cleanupfnc

	def showSelection(self):
		title = _("When to Zap back?")
		select = int(config.werbezapper.duration.value)
		keys = []

		# Number keys
		choices = [
								(_("Custom"), 'custom'),
								('1 ' + _('minute'),  1),
								('2 ' + _('minutes'), 2),
								('3 ' + _('minutes'), 3),
								('4 ' + _('minutes'), 4),
								('5 ' + _('minutes'), 5),
								('6 ' + _('minutes'), 6),
								('7 ' + _('minutes'), 7),
								('8 ' + _('minutes'), 8),
								('9 ' + _('minutes'), 9),
							]
		keys.extend(["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"])

		# Dummy entry to seperate the color keys
		choices.append(("------", 'close'))
		keys.append("")  # No key

		# Blue key - Covers the monitoring functions without closing Werbezapper
		if self.monitor_timer.isActive():
			choices.append((_("Stop monitoring"), 'stopmonitoring'))
		else:
			choices.append((_("Start monitoring"), 'startmonitoring'))
		keys.append("blue")

		# Red key - Covers all stop and close functions
		if self.zap_timer.isActive():
			if self.zap_time:
				remaining = int(math.floor(self.zap_time - time()))
				remaining = remaining if remaining > 0 else 0
				remaining /= 60
				select = remaining if 0 < remaining and remaining < 10 else select
			choices.append((_("Stop timer"), 'stoptimer'))
			keys.append("red")
		else:
			choices.append(("------", 'close'))
			keys.append("")  # No key

		# Green key - Manual rezap
		if self.zap_timer.isActive():
			choices.append((_("Rezap"), 'rezap'))
			keys.append("green")
		else:
			choices.append(("------", 'close'))
			keys.append("")  # No key

		# Select Timer Length
		self.session.openWithCallback(
			self.choicesCallback,
			WerbeZapperChoiceBox,
			title,
			choices,
			keys,
			select,
			self.zap_time,
			self.zap_service,
			self.monitored_event,
			self.monitored_service
		)

	def choicesCallback(self, result):
		result = result and result[1]
		
		if result == "custom":
			from Screens.InputBox import InputBox
			from Components.Input import Input

			#TODO allow custom input in seconds or parts of a minute 1.5
			self.session.openWithCallback(
				self.inputCallback,
				InputBox,
				title=_("How many minutes to wait until zapping back?"),
				text="10",
				maxSize=False,
				type=Input.NUMBER
			)
			return
			
		elif result == "startmonitoring":
			self.startMonitoring()
		
		elif result == "stopmonitoring":
			self.stopMonitoring()
		
		elif result == "rezap":
			self.stopTimer()
			self.zap()
		
		elif result == "stoptimer":
			self.stopTimer()
		
		elif result == "reopen":
			self.showSelection()
		
		elif result == "close":
			pass
		
		elif isinstance(result, int):
			self.startTimer(result)
		
		self.cleanup()

	def inputCallback(self, result):
		if result is not None:
			self.startTimer(int(result))
		else:
			# Clean up if possible
			self.cleanup()

	def startMonitoring(self, notify=True):
		
		# Stop active zap timer
		self.stopTimer()
		
		# Get current service and event
		service = self.session.nav.getCurrentService()
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
		self.monitored_service = ref

		# Notify us on new services
		# ServiceEventTracker will remove itself on close
		if not self.__event_tracker:
			self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evStart: self.serviceStarted,
			})

		# Get event information
		info = service and service.info()
		event = info and info.getEvent(0)
		if not event:
			# Alternative to get the current event
			epg = eEPGCache.getInstance()
			event = ref and ref.valid() and epg.lookupEventTime(ref, -1)
		if event:
			# Set monitoring end time
			self.monitored_event = event
			duration = event.getDuration() - (time() - event.getBeginTime())
			self.monitor_timer.startLongTimer(int(duration))
			if notify:
				name = event and event.getEventName()
				AddPopup(
									_("WerbeZapper\nMonitoring started\n%s") % (name),
									MessageBox.TYPE_INFO,
									3,
									"WerbeZapperMonitoringStarted"
								)
		else:
			#TEST SF2 or something without an valid epg
			#IDEA detect event is finished
			#IDEA inputbox monitoring in minutes
			if notify:
				AddPopup(
									_("WerbeZapper\nMonitoring started unlimited\nHas to be deactivated manually"),
									MessageBox.TYPE_INFO,
									10,
									"WerbeZapperMonitoringStartedUnlimited"
								)

	def stopMonitoring(self, notify=True):
		
		# Stop active zap timer
		self.stopTimer()
		
		self.monitor_timer.stop()
		
		if notify:
			# Notify the User that the monitoring is ending
			name = self.monitored_event and self.monitored_event.getEventName()
			AddPopup(
								_("WerbeZapper\nMonitoring ends\n%s") % (name),
								MessageBox.TYPE_INFO,
								3,
								"WerbeZapperMonitoringStopped"
							)
		
		self.monitored_service = None
		self.monitored_event = None

	def serviceStarted(self):
		# Verify monitoring is active
		if self.monitor_timer.isActive():
			# Verify there is no active zap timer
			if not self.zap_timer.isActive():
				# Is the zap away check already running
				if not self.delay_timer.isActive():
					# Delay the zap away check only once
					self.delay_timer.startLongTimer(3)

	def zappedAway(self):
		# Verify that the currently played service has changed
		# Avoid that we trigger on a background recording or streaming service
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
		if ref and self.monitored_service != ref:
			# Start zap timer
			self.startTimer(zapto=self.monitored_service)

	def startTimer(self, duration=0, notify=True, zapto=None):
		if duration > 0:
			# Save the last selected zap time for reusing it later
			config.werbezapper.duration.value = duration
			config.werbezapper.duration.save()
		else:
			# Reuse last duration
			duration = int(config.werbezapper.duration.value)
		
		# Keep any service related information (zap_service might not equal move_service -> subservices)
		self.zap_service = zapto or self.session.nav.getCurrentlyPlayingServiceReference()
		self.move_service = None if zapto else self.servicelist.getCurrentSelection()
		self.root = self.servicelist.getRoot()

		#import ServiceReference
		#print [str(ServiceReference.ServiceReference(x)) for x in self.servicelist.getCurrentServicePath()]
		#print ServiceReference.ServiceReference(self.servicelist.getRoot())

		# Start Timer
		self.zap_time = time() + (duration * 60)
		self.zap_timer.startLongTimer(int(duration * 60))
		
		if notify:
			# Remind the User of what he just did
			AddPopup(
								_("Zapping back in %d Minute(s)") % (duration),
								MessageBox.TYPE_INFO,
								3,
								"WerbeZapperZapStarted"
							)
	def stopTimer(self):
		# Stop Timer
		self.zap_timer.stop()
		self.zap_time = None

	def zap(self, notify=True):
		if self.zap_service is not None:
			if self.root:
				import ServiceReference
				if not self.servicelist.preEnterPath(str(ServiceReference.ServiceReference(self.root))):
					if self.servicelist.isBasePathEqual(self.root):
						self.servicelist.pathUp()
						self.servicelist.enterPath(self.root)
					else:
						currentRoot = self.servicelist.getRoot()
						if currentRoot is None or currentRoot != self.root:
							self.servicelist.clearPath()
							self.servicelist.enterPath(self.root)

			if self.move_service:
				self.servicelist.setCurrentSelection(self.move_service)
				self.servicelist.zap()

			# Play zap_service (won't rezap if service equals to move_service)
			self.session.nav.playService(self.zap_service)

		if notify:
			# Remind the User what happens here
			AddPopup(
								_("Zapping back"),
								MessageBox.TYPE_INFO,
								3,
								"WerbeZapperZapBack"
							)

		# Cleanup if end timer is not running
		if not self.monitor_timer.isActive():
			
			# Reset services
			self.zap_service = None
			self.move_service = None
			self.root = None

	def cleanup(self):
		# Clean up if no timer is running
		if self.monitor_timer and not self.monitor_timer.isActive() \
			and self.zap_timer and not self.zap_timer.isActive():
			if self.cleanupfnc:
				self.cleanupfnc()

	def shutdown(self):
		self.zap_timer.callback.remove(self.zap)
		self.zap_timer = None
		self.monitor_timer.callback.remove(self.stopMonitoring)
		self.monitor_timer = None
