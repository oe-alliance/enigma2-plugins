from Components.SystemInfo import SystemInfo

# MessageBox
from Screens.MessageBox import MessageBox
from Tools import Notifications

# Config
from Components.config import config

class RecordAdapter:
	def __init__(self, session):
		if SystemInfo.get("NumVideoDecoders", 1) < 2:
			self.backgroundRefreshAvailable = False
			return
		if config.plugins.epgrefresh.enablemessage.value:
			Notifications.AddNotification(MessageBox, _("EPG refresh started in background."), type=MessageBox.TYPE_INFO, timeout=4)
		self.__service = None
		self.backgroundRefreshAvailable = True
		self.navcore = session.nav

	def play(self, service):
		print "[EPGRefresh.RecordAdapter.play]"
		if not self.backgroundRefreshAvailable: return False
		self.stopStreaming()
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
		print "[EPGRefresh.RecordAdapter.stop]"
		self.stopStreaming()

