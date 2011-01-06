from Screens.PictureInPicture import PictureInPicture
from Components.SystemInfo import SystemInfo

class BackgroundAdapter:
	def __init__(self, session):
		if SystemInfo.get("NumVideoDecoders", 1) < 2:
			self.pipAvail = False
			return

		self.session = session
		self.pipAvail = True
		if session.pipshown:
			# Hijack PiP
			self.wasShown = True
			self.previousService = self.session.pip.getCurrentService()
			self.previousPath = self.session.pip.servicePath
		else:
			self.wasShown = False
			self.initPiP()

	def initPiP(self):
		# Instantiate PiP
		self.session.pip = self.session.instantiateDialog(PictureInPicture)
		self.session.pip.show()
		self.session.pipshown = True # Always pretends it's shown (since the ressources are present)
		newservice = self.session.nav.getCurrentlyPlayingServiceReference()
		if self.session.pip.playService(newservice):
			self.session.pip.servicePath = newservice.getPath()

	def play(self, service):
		print "[EPGRefresh.BackgroundAdapter.play]"
		if not self.pipAvail: return False

		if not self.session.pipshown: # make sure pip still exists
			self.initPiP()

		if self.session.pip.playService(service):
			self.session.pip.servicePath = service.getPath()
			return True
		return False

	def stop(self):
		if not self.pipAvail: return

		if self.wasShown:
			# reset pip and remove it if unable to play service
			if self.session.pipshown and self.session.pip.playService(self.previousService):
				self.session.pip.servicePath = self.previousPath
			else:
				self.session.pipshown = False
				del self.session.pip
		else:
			# remove pip
			self.session.pipshown = False
			try: del self.session.pip
			except Exception: pass

