# for localized messages
from . import _

# GUI (Screens)
from Screens.MessageBox import MessageBox

# Timer
from enigma import eTimer

class WerbeZapper:
	"""Simple Plugin to automatically zap back to a Service after a given amount
	   of time."""

	def __init__(self, session, servicelist, cleanupfnc = None):
		# Save Session&Servicelist
		self.session = session
		self.servicelist = servicelist

		# Create Timer
		self.zap_timer = eTimer()
		self.zap_timer.callback.append(self.zap)

		# Initialize services
		self.zap_service = None
		self.move_service = None
		self.root = None

		# Keep Cleanup
		self.cleanupfnc = cleanupfnc

	def showSelection(self):
		# Check if timer is active
		if self.zap_timer.isActive():
			# Ask if we should stop the running timer
			self.session.openWithCallback(
				self.confirmStop,
				MessageBox,
				_("Timer already running.\nStop it?")
			)
		else:
			from Screens.ChoiceBox import ChoiceBox

			# Select Timer Length
			self.session.openWithCallback(
				self.choiceCallback,
				ChoiceBox,
				_("When to Zap back?"),
				(
					('1 ' + _('minute'), 1),
					('2 ' + _('minutes'), 2),
					('3 ' + _('minutes'), 3),
					('4 ' + _('minutes'), 4),
					('5 ' + _('minutes'), 5),
					('6 ' + _('minutes'), 6),
					('7 ' + _('minutes'), 7),
					('8 ' + _('minutes'), 8),
					('9 ' + _('minutes'), 9),
					( _("Custom"), 'custom')
				)
			)

	def confirmStop(self, result):
		if result:
			# Stop Timer
			self.zap_timer.stop()

			# Reset Vars
			self.zap_service = None
			self.move_service = None

			# Clean up if possible
			if self.cleanupfnc:
				self.cleanupfnc()

	def choiceCallback(self, result):
		result = result and result[1]
		if result == "custom":
			from Screens.InputBox import InputBox
			from Components.Input import Input

			self.session.openWithCallback(
				self.inputCallback,
				InputBox,
				title=_("How many minutes to wait until zapping back?"),
				text="10",
				maxSize=False,
				type=Input.NUMBER
			)
		elif result is not None:
			self.confirmStart(result)
		# Clean up if possible
		elif self.cleanupfnc:
			self.cleanupfnc()

	def inputCallback(self, result):
		if result is not None:
			self.confirmStart(int(result))
		# Clean up if possible
		elif self.cleanupfnc:
			self.cleanupfnc()


	def confirmStart(self, duration):
		# Remind the User of what he just did
		self.session.open(
			MessageBox,
			_("Zapping back in %d Minutes") % (duration),
			type = MessageBox.TYPE_INFO,
			timeout = 3
		)

		# Keep any service related information (zap_service might not equal move_service -> subservices)
		self.zap_service = self.session.nav.getCurrentlyPlayingServiceReference()
		self.move_service = self.servicelist.getCurrentSelection()
		self.root = self.servicelist.getRoot()

		#import ServiceReference
		#print [str(ServiceReference.ServiceReference(x)) for x in self.servicelist.getCurrentServicePath()]
		#print ServiceReference.ServiceReference(self.servicelist.getRoot())

		# Start Timer
		self.zap_timer.startLongTimer(duration*60)

	def zap(self):
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

			# Reset services
			self.zap_service = None
			self.move_service = None
			self.root = None

		# Clean up if possible
		if self.cleanupfnc:
			self.cleanupfnc()

	def shutdown(self):
		self.zap_timer.callback.remove(self.zap)
		self.zap_timer = None

