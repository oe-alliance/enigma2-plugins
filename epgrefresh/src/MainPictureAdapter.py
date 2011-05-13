import Screens.Standby
from Components.config import config

class MainPictureAdapter:
	def __init__(self, session):
		self.showNotification = config.plugins.epgrefresh.enablemessage.value
		self.session = session
		self.previousService = session.nav.getCurrentlyPlayingServiceReference()

	def play(self, service):
		print "[EPGRefresh.MainPictureAdapter.play]"
		if self.showNotification:
			Notifications.AddNotification(MessageBox, _("EPG refresh starts scanning channels."), type=MessageBox.TYPE_INFO, timeout=4)
			self.showNotification = False
		return self.session.nav.playService(service)

	def stop(self):
		if self.previousService is not None or Screens.Standby.inStandby:
			self.session.nav.playService(self.previousService)

