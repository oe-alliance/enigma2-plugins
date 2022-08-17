from Screens.Setup import Setup
from Components.config import config, getConfigListEntry


class StartupToStandbyConfiguration(Setup):
	def __init__(self, session):
		Setup.__init__(self, session=session, setup=None)
		self.title = _("StartupToStandby Configuration")
		self.skinName = ["StartupToStandbyConfiguration", "Setup"]

	def createSetup(self):
		if not self.list:  # only load once as is a single item
			self.list = [getConfigListEntry(_("Enable"), config.plugins.startuptostandby.enabled)]
			self["config"].list = self.list
