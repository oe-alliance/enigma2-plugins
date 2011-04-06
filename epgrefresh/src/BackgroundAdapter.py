from Screens.PictureInPicture import PictureInPicture
from Components.SystemInfo import SystemInfo
from enigma import ePoint, eSize

# MessageBox
from Screens.MessageBox import MessageBox
from Tools import Notifications

# Config
from Components.config import config

class BackgroundAdapter:
	def __init__(self, session):
		if SystemInfo.get("NumVideoDecoders", 1) < 2:
			self.pipAvail = False
			return

		self.session = session
		self.pipAvail = True
		if config.plugins.epgrefresh.enablemessage.value:
			Notifications.AddNotification(MessageBox, _("EPG refresh started in background.\nPlease don't use PiP meanwhile!"), type=MessageBox.TYPE_INFO, timeout=4)
		if session.pipshown:
			# Hijack PiP
			self.hidePiP()
			self.wasShown = True
			self.previousService = self.session.pip.getCurrentService()
			self.previousPath = self.session.pip.servicePath
		else:
			self.wasShown = False
			self.initPiP()

	def hidePiP(self):
		# set PiP size to 1 pixel
		print "[EPGRefresh] Hide PiP"
		x = y = 0
		w = h = 1
		self.session.pip.instance.move(ePoint(x, y))
		self.session.pip.instance.resize(eSize(w, y))
		self.session.pip["video"].instance.resize(eSize(w, y))

	def initPiP(self):
		# Instantiate PiP
		self.session.pip = self.session.instantiateDialog(PictureInPicture)
		self.session.pip.show()
		self.hidePiP()
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

		if config.plugins.epgrefresh.enablemessage.value:
			Notifications.AddNotification(MessageBox, _("EPG refresh finished. PiP available now."), type=MessageBox.TYPE_INFO, timeout=4)

		# reset pip and remove it if unable to play service
		if self.wasShown:
			if self.session.pipshown and self.session.pip.playService(self.previousService):
				self.session.pip.servicePath = self.previousPath

				#Restore PiP values to their defaults after EPG refresh is finished
				print "[EPGRefresh] Restoring PiP"
				try:
					x = config.av.pip.value[0]
					y = config.av.pip.value[1]
					w = config.av.pip.value[2]
					h = config.av.pip.value[3]
				except Exception: # default location - can this actually happen?
					x = 400
					y = 60
					w = 240
					h = 192

				if x != -1 and y != -1 and w != -1 and h != -1:
					self.session.pip.move(x, y)
					self.session.pip.resize(w, h)
			else:
				self.session.pipshown = False
				del self.session.pip
		else:
			# remove pip
			self.session.pipshown = False
			try: del self.session.pip
			except Exception: pass

