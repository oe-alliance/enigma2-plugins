import Screens.Standby

# MessageBox
from Screens.MessageBox import MessageBox
from Tools import Notifications

# Config
from Components.config import config

from . import _, STARTNOTIFICATIONID, NOTIFICATIONDOMAIN


class MainPictureAdapter:
	backgroundCapable = True

	def __init__(self, session):
		self.navcore = session.nav

	def prepare(self):
		if config.plugins.epgrefresh.enablemessage.value:
			Notifications.AddPopup(_("EPG refresh starts scanning channels."), MessageBox.TYPE_INFO, 4, STARTNOTIFICATIONID)
		self.previousService = self.navcore.getCurrentlyPlayingServiceReference()
		print(f"[EPGRefresh] DEBUG prepare.previousService={str(self.previousService)}")
		return True

	def play(self, service):
		print("[EPGRefresh.MainPictureAdapter.play]")
		try:
			res = self.navcore.playService(service, ignoreStreamRelay=True)
		except:
			res = self.navcore.playService(service)
		return res

	def stop(self):
		if self.previousService is not None or Screens.Standby.inStandby:
			self.navcore.playService(self.previousService)
