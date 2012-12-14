from __future__ import print_function

from Screens.PictureInPicture import PictureInPicture
from Components.SystemInfo import SystemInfo
from enigma import ePoint, eSize

# MessageBox
from Screens.MessageBox import MessageBox
from Tools import Notifications

# Config
from Components.config import config

from . import _, NOTIFICATIONID

class PipAdapter:
	backgroundCapable = False
	def __init__(self, session, hide=True):
		if SystemInfo.get("NumVideoDecoders", 1) < 2:
			self.pipAvail = False
			return

		self.hide = hide
		self.session = session
		self.pipAvail = True

	def prepare(self):
		if not self.pipAvail:
			return False

		if config.plugins.epgrefresh.enablemessage.value:
			Notifications.AddPopup(_("EPG refresh started in background.") + "\n" + _("Please don't use PiP meanwhile!"), MessageBox.TYPE_INFO, 4, NOTIFICATIONID)
		if hasattr(self.session, 'pipshown') and self.session.pipshown:
			# Hijack PiP
			self.wasShown = True
			self.previousService = self.session.pip.getCurrentService()
			self.previousPath = self.session.pip.servicePath
			del self.session.pip
		else:
			self.wasShown = False
		self.initPiP()
		return True

	def hidePiP(self):
		# set pip size to 1 pixel
		print("[EPGRefresh.PipAdapter.hidePiP]")
		x = y = 0
		w = h = 1
		self.session.pip.instance.move(ePoint(x, y))
		self.session.pip.instance.resize(eSize(w, y))
		self.session.pip["video"].instance.resize(eSize(w, y))

	def initPiP(self):
		# Instantiate PiP
		self.session.pip = self.session.instantiateDialog(PictureInPicture)
		self.session.pip.show()
		if self.hide: self.hidePiP()
		self.session.pipshown = True # Always pretends it's shown (since the ressources are present)
		newservice = self.session.nav.getCurrentlyPlayingServiceReference()
		if self.session.pip.playService(newservice):
			self.session.pip.servicePath = newservice.getPath()

	def play(self, service):
		print("[EPGRefresh.PipAdapter.play]")
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
			Notifications.AddPopup(_("EPG refresh finished.") + "\n" + _("PiP available now."), MessageBox.TYPE_INFO, 4, NOTIFICATIONID)

		# remove pip preemptively
		try: del self.session.pip
		except Exception: pass

		# reset pip and remove it if unable to play service
		if self.wasShown:
			self.session.pip = self.session.instantiateDialog(PictureInPicture)
			self.session.pip.show()
			self.session.pipshown = True
			if self.session.pip.playService(self.previousService):
				self.session.pip.servicePath = self.previousPath
			else:
				self.session.pipshown = False
				del self.session.pip
		else:
			self.session.pipshown = False

