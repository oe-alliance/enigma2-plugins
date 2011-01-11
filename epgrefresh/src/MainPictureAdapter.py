import Screens.Standby

class MainPictureAdapter:
	def __init__(self, session):
		self.session = session
		self.previousService = session.nav.getCurrentlyPlayingServiceReference()

	def play(self, service):
		print "[EPGRefresh.MainPictureAdapter.play]"
		return self.session.nav.playService(service)

	def stop(self):
		if self.previousService is not None or Screens.Standby.inStandby:
			self.session.nav.playService(self.previousService)

