from __future__ import print_function

import Screens.Standby

# MessageBox
from Screens.MessageBox import MessageBox
from Tools import Notifications

# Config
from Components.config import config

class MainPictureAdapter:
	backgroundCapable = True
	def __init__(self, session):
		self.navcore = session.nav

	def prepare(self):
		if config.plugins.epgrefresh.enablemessage.value:
			Notifications.AddNotification(MessageBox, _("EPG refresh starts scanning channels."), type=MessageBox.TYPE_INFO, timeout=4)
		self.previousService = self.navcore.getCurrentlyPlayingServiceReference()
		return True

	def play(self, service):
		print("[EPGRefresh.MainPictureAdapter.play]")
		return self.navcore.playService(service)

	def stop(self):
		if self.previousService is not None or Screens.Standby.inStandby:
			self.navcore.playService(self.previousService)

