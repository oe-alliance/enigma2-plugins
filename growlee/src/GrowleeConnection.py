from Components.config import config
from Tools import Notifications
from Screens.MessageBox import MessageBox

from . import NOTIFICATIONID

def emergencyDisable(*args, **kwargs):
	global growleeConnection
	if growleeConnection:
		growleeConnection.stop()

	if gotNotification in Notifications.notificationAdded:
		Notifications.notificationAdded.remove(gotNotification)
	Notifications.AddPopup(
		_("Network error.\nDisabling Growlee until next restart!"),
		MessageBox.TYPE_ERROR,
		10
	)

def gotNotification():
	notifications = Notifications.notifications
	if notifications:
		_, screen, args, kwargs, id = notifications[-1]
		if screen is MessageBox and id != NOTIFICATIONID and id not in config.plugins.growlee.blacklist.value:

			# NOTE: priority is in [-2; 2] but type is [0; 3] so map it
			# XXX: maybe priority==type-2 would be more appropriate
			priority = kwargs.get("type", 0) - 1
			timeout = kwargs.get("timeout", -1)

			if "text" in kwargs:
				description = kwargs["text"]
			else:
				description = args[0]
			description = description.decode('utf-8')

			growleeConnection.sendNotification(title="Dreambox", description=description, priority=priority, timeout=timeout)

class GrowleeConnection:
	connection = None

	def sendNotification(self, title="Dreambox", description='', priority=-1, timeout=-1):
		try:
			level = int(config.plugins.growlee.level.value)
		except ValueError:
			level = -1

		if self.connection and not priority < level:
			self.connection.sendNotification(title=title, description=description, priority=priority, timeout=timeout)

	def listen(self):
		if self.connection:
			return

		proto = config.plugins.growlee.protocol.value
		if proto == "prowl":
			from Prowl import ProwlAPI
			self.connection = ProwlAPI()
		elif proto == "growl":
			from GrowlTalk import GrowlTalkAbstraction
			self.connection = GrowlTalkAbstraction()
		else: # proto == "snarl":
			from SNP import SnarlNetworkProtocolAbstraction
			self.connection = SnarlNetworkProtocolAbstraction()

	def stop(self):
		if self.connection:
			d = self.connection.stop()
			self.connection = None
			return d
		return None

growleeConnection = GrowleeConnection()

