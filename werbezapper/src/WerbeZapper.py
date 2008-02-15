# GUI (Screens)
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import InputBox

# GUI (Components)
from Components.Input import Input

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
			# Select Timer Length
			self.session.openWithCallback(
				self.choiceCallback,
				ChoiceBox,
				_("When to Zap back?"),
				[
				 	(
						' '.join([str(x), _("minutes")]),
						x
					)
				 	for x in range(1, 10)
				 ] + [
					( _("Custom"), 'custom')
				]
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
		# Show Information to User, Save Service, Start Timer
		self.session.open(
			MessageBox,
			_("Zapping back in %d Minutes") % (duration),
			type = MessageBox.TYPE_INFO,
			timeout = 3
		)

		# Keep playing and selected service as we might be playing a service not in servicelist
		self.zap_service = self.session.nav.getCurrentlyPlayingServiceReference()
		self.move_service = self.servicelist.getCurrentSelection()

		# Start Timer
		self.zap_timer.startLongTimer(duration*60)

	def zap(self):
		if self.zap_service is not None:
			# Check if we know where to move in Servicelist
			if self.move_service is not None:
				self.servicelist.setCurrentSelection(self.move_service)
				self.servicelist.zap()

			# Play zap_service if it is different from move_service
			if self.zap_service != self.move_service:
				# Play Service
				self.session.nav.playService(self.zap_service)

			# Reset services
			self.zap_service = None
			self.move_service = None

		# Clean up if possible
		if self.cleanupfnc:
			self.cleanupfnc()

	def shutdown(self):
		self.zap_timer.callback.remove(self.zap)
		self.zap_timer = None
