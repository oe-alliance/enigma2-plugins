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


class WerbeZapper(Screen):
	"""Simple Plugin to automatically zap back to a Service after a given amount
	   of time."""
	def __init__(self, session, servicelist, cleanupfnc = None):
		Screen.__init__(self, session)
		
		# Save Session&Servicelist
		self.session = session
		self.servicelist = servicelist
		
		# Create Timer
		self.zap_time = None
		self.zap_timer = eTimer()
		self.zap_timer.callback.append(self.zap)

		# Create Event Monitoring End Timer
		self.monitor_timer = eTimer()
		self.monitor_timer.callback.append(self.stopMonitoring)

		# Initialize services
		self.zap_service = None
		self.move_service = None
		self.root = None
		
		#	Initialize monitoring
		self.monitor_service = None
		self.event = None
		self.duration = 5
		self.__event_tracker = None
		
		# Keep Cleanup
		self.cleanupfnc = cleanupfnc

	def showSelection(self):
		title = _("When to Zap back?")
		select = 4 # 5 Minutes
		keys = []	
			
		# Number keys
		choices = [
								('1 ' + _('minute'), 1),
								('2 ' + _('minutes'), 2),
								('3 ' + _('minutes'), 3),
								('4 ' + _('minutes'), 4),
								('5 ' + _('minutes'), 5),
								('6 ' + _('minutes'), 6),
								('7 ' + _('minutes'), 7),
								('8 ' + _('minutes'), 8),
								('9 ' + _('minutes'), 9),
								( _("Custom"), 'custom'),	# Key 0
							]
		keys.extend( [ "1", "2", "3", "4", "5", "6", "7", "8", "9", "0" ] )
		
		# Dummy entry to seperate the color keys
		choices.append( ( "------", 'close' ) )
		keys.append( "" )  # No key
		
		# Blue key - Covers the monitoring functions without closing Werbezapper
		if self.monitor_timer.isActive():
			#TODO what is monitored
			# Number Channel Name Remaining
			name = ""
			if self.event:
				name = self.event and self.event.getEventName()
				duration = ( self.event.getDuration() - ( time() - self.event.getBeginTime() ) ) / 60
				title += "\n\n" + _("Monitoring:\n%s (%d Min)") % (name, duration)  #TODO Add remaining ?
			choices.append( ( _("Stop monitoring: %s") % (name), 'stopmonitoring' ) )
		else:
			choices.append( ( _("Start monitoring..."), 'startmonitoring' ) )
		keys.append( "blue" )

		# Red key - Covers all stop and close functions
		#if self.zap_timer.isActive() and self.monitor_timer.isActive():
		#	choices.append( ( _("Stop all"), 'stopall' ) )
		#	keys.append( "red" )
		#el
		if self.zap_timer.isActive() and self.zap_time:
			remaining = int( math.floor( self.zap_time - time() ) )
			remaining = remaining if remaining > 0 else 0
			remain = ("%d:%02d") % (remaining/60, remaining%60)
			title += "\n\n" + _("Zap back in %s") % (remain)
			remaining /= 60
			select = (remaining-1) if 1 < remaining and remaining < 10 else select
			choices.append( ( _("Stop timer (%s)") % (remain), 'stoptimer' ) )
			keys.append( "red" )
		#elif self.monitor_timer.isActive():
		#	choices.append( ( _("Stop monitoring"), 'stopmonitoring' ) )
		#	keys.append( "red" )
		else:
			choices.append( ( "------", 'close' ) )
			keys.append( "" )  # No key
		
		# Green key - Manual rezap
		if self.zap_timer.isActive():
			choices.append( ( _("Rezap"), 'rezap' ) )
			keys.append( "green" )
		else:
			choices.append( ( "------", 'close' ) )
			keys.append( "" )  # No key
		
		#TEST if monitoring not in title
		#if self.event:
		# Dummy entry to seperate the color keys
		#choices.append( ( "------", 'close' ) )
		#keys.append( "" )  # No key
		# Monitoring
		#choices.append( ( _("Monitoring:\n%s") %s ("self.event.getEventName()"), 'reopen' ) )
		#keys.append( "" )  # No key
				
		# Select Timer Length
		print keys
		print choices
		self.session.openWithCallback(
			self.choicesCallback,
			ChoiceBox,
			title,
			choices,
			keys,
			select
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
			
		elif result == "startmonitoring":
			self.startMonitoring()
		
		elif result == "stopmonitoring":
			self.stopMonitoring(False)
		
		elif result == "rezap":
			self.zap_timer.stop()
			self.zap_time = None
			self.zap()
		
		elif result == "stoptimer":
			# Stop Timer
			self.zap_timer.stop()
			self.zap_time = None
			
			# Reset Vars
			self.zap_service = None
			self.move_service = None
			self.root = None
		
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

	def startTimer(self, duration=0, notify=True, zapto=None):
		if duration > 0:
			# Save the last selected rezap time for using for monitorint rezap time
			self.duration = duration
		else:
			# Reuse last duration
			duration = self.duration
		
		# Keep any service related information (zap_service might not equal move_service -> subservices)
		self.zap_service = zapto or self.session.nav.getCurrentlyPlayingServiceReference()
		self.move_service = self.servicelist.getCurrentSelection()
		self.root = self.servicelist.getRoot()

		#import ServiceReference
		#print [str(ServiceReference.ServiceReference(x)) for x in self.servicelist.getCurrentServicePath()]
		#print ServiceReference.ServiceReference(self.servicelist.getRoot())

		# Start Timer
		self.zap_time = time() + ( duration * 60 )
		self.zap_timer.startLongTimer( int( duration * 60 ) )
		
		if notify:
			# Remind the User of what he just did
			#TEST deactivate message on zap because of monitoring
			AddPopup(
								_("Zapping back in %d Minute(s)") % (duration),
								MessageBox.TYPE_INFO,
								3,
								"WerbeZapperZapStarted"
							)

	def startMonitoring(self, notify=True):
		# Get current service and event
		service = self.session.nav.getCurrentService()
		ref = self.session.nav.getCurrentlyPlayingServiceReference()
		self.monitor_service = ref

		# Notify us on new services
		# ServiceEventTracker will remove itself on close
		# evStart won't work, no service reference available
		if not self.__event_tracker:
			self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
			{
				iPlayableService.evTunedIn: self.serviceStarted,
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
			self.event = event
			duration = event.getDuration() - ( time() - event.getBeginTime() )
			self.monitor_timer.startLongTimer( int( duration ) )
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
		self.monitor_timer.stop()
		
		if notify:
			# Notify the User that the monitoring is ending
			#TODO get event channelnumber and channelname
			#number = 
			#channel = 
			#_("Monitoring\n%d %s %s\nends") % (number, channel, name),
			name = self.event and self.event.getEventName()
			AddPopup(
								_("WerbeZapper\nMonitoring ends\n%s") % (name),
								MessageBox.TYPE_INFO,
								3,
								"WerbeZapperMonitoringStopped"
							)
		
		self.monitor_service = None
		self.event = None

	def serviceStarted(self):
		# Verify monitoring is active
		if self.monitor_service:
			# Verify there is no active zap timer			
			if not self.zap_timer.isActive():
				# Verify that the currently played service has changed
				# Avoid that we trigger on a background recording or streaming service
				#ref = self.session.nav.getCurrentlyPlayingServiceReference()
				#if ref and self.monitor_service != ref:
					# Start zap timer
					self.startTimer(zapto=self.monitor_service)

	def zap(self, notify= False):
		#TODO add notify ?
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
