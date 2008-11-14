##
## RS Downloader
## by AliAbdul
##
from Components.ActionMap import ActionMap
from Components.config import config, ConfigText, ConfigYesNo, ConfigClock, ConfigSubsection, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Screens.Screen import Screen
from time import time

##############################################################################

config.plugins.RSDownloader = ConfigSubsection()
config.plugins.RSDownloader.username = ConfigText(default="", fixed_size=False)
config.plugins.RSDownloader.password = ConfigText(default="", fixed_size=False)
config.plugins.RSDownloader.lists_directory = ConfigText(default="/media/cf/rs/lists/", fixed_size=False)
config.plugins.RSDownloader.downloads_directory = ConfigText(default="/media/cf/rs/downloads", fixed_size=False)
config.plugins.RSDownloader.start_time = ConfigClock(default = time())
config.plugins.RSDownloader.end_time = ConfigClock(default = time())
config.plugins.RSDownloader.write_log = ConfigYesNo(default = True)
config.plugins.RSDownloader.reconnect_fritz = ConfigYesNo(default = False)

##############################################################################

class RSConfig(ConfigListScreen, Screen):
	skin = """
		<screen position="80,170" size="560,270" title="RS Downloader">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="0,45" size="560,220" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		
		self["key_green"] = Label(_("Save"))
		
		list = []
		list.append(getConfigListEntry(_("Username:"), config.plugins.RSDownloader.username))
		list.append(getConfigListEntry(_("Password:"), config.plugins.RSDownloader.password))
		list.append(getConfigListEntry(_("Lists directory:"), config.plugins.RSDownloader.lists_directory))
		list.append(getConfigListEntry(_("Downloads directory:"), config.plugins.RSDownloader.downloads_directory))
		list.append(getConfigListEntry(_("Don't download before:"), config.plugins.RSDownloader.start_time))
		list.append(getConfigListEntry(_("Don't download after:"), config.plugins.RSDownloader.end_time))
		list.append(getConfigListEntry(_("Write log:"), config.plugins.RSDownloader.write_log))
		list.append(getConfigListEntry(_("Reconnect fritz.Box before downloading:"), config.plugins.RSDownloader.reconnect_fritz))
		ConfigListScreen.__init__(self, list)
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {"green": self.save, "cancel": self.exit}, -1)

	def save(self):
		for x in self["config"].list:
			x[1].save()
		self.close()

	def exit(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()
