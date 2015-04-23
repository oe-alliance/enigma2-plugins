from __future__ import print_function

from Components.SystemInfo import SystemInfo
from enigma import pNavigation

# MessageBox
from Screens.MessageBox import MessageBox
from Tools import Notifications

# Config
from Components.config import config

from . import _, STARTNOTIFICATIONID, NOTIFICATIONDOMAIN

class RecordAdapter:
	backgroundCapable = True
	def __init__(self, session):
		if SystemInfo.get("NumVideoDecoders", 1) < 2:
			self.backgroundRefreshAvailable = False
			return

		self.backgroundRefreshAvailable = True
		self.__service = None
		self.navcore = session.nav

	def prepare(self):
		if not self.backgroundRefreshAvailable:
			return False
		if config.plugins.epgrefresh.enablemessage.value:
			Notifications.AddPopup(_("EPG refresh started in background."), MessageBox.TYPE_INFO, 4, STARTNOTIFICATIONID)

		return True

	def play(self, service):
		print("[EPGRefresh.RecordAdapter.play]")
		if not self.backgroundRefreshAvailable: return False
		self.stopStreaming()
		try:
			#not all images support recording type indicators
			self.__service = self.navcore.recordService(service,False,pNavigation.isPseudoRecording|pNavigation.isFromEPGrefresh)
		except:
			self.__service = self.navcore.recordService(service)
		if self.__service is not None:
			self.__service.prepareStreaming()
			self.__service.start()
			return True
		return False

	def stopStreaming(self):
		if self.__service is not None:
			self.navcore.stopRecordService(self.__service)
			self.__service = None

	def stop(self):
		print("[EPGRefresh.RecordAdapter.stop]")
		self.stopStreaming()

