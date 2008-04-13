# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from EPGRefreshChannelEditor import EPGRefreshServiceEditor

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Button import Button

# Configuration
from Components.config import config, getConfigListEntry

from EPGRefresh import epgrefresh

from sets import Set

class EPGRefreshConfiguration(Screen, ConfigListScreen):
	"""Configuration of EPGRefresh"""

	skin = """<screen name="EPGRefreshConfiguration" title="Configure EPGRefresh" position="75,155" size="565,280">
		<widget name="config" position="5,5" size="555,225" scrollbarMode="showOnDemand" />
		<ePixmap position="0,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,235" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="140,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="280,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="420,235" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = "EPGRefresh Configuration"
		self.onChangedEntry = []

		# Although EPGRefresh keeps services in a Set we prefer a list
		self.services = (
			[x for x in epgrefresh.services[0]],
			[x for x in epgrefresh.services[1]]
		)

		self.list = [
			getConfigListEntry(_("Refresh automatically"), config.plugins.epgrefresh.enabled),
			getConfigListEntry(_("Time to stay on service (in m)"), config.plugins.epgrefresh.interval),
			getConfigListEntry(_("Refresh EPG after"), config.plugins.epgrefresh.begin),
			getConfigListEntry(_("Refresh EPG before"), config.plugins.epgrefresh.end),
			getConfigListEntry(_("Delay when not in Standby (in m)"), config.plugins.epgrefresh.delay_standby),
			getConfigListEntry(_("Force scan even if not in Standby or Recording"), config.plugins.epgrefresh.force),
			getConfigListEntry(_("Inherit Services from AutoTimer if available"), config.plugins.epgrefresh.inherit_autotimer),
			getConfigListEntry(_("Shutdown after refresh"), config.plugins.epgrefresh.afterevent),
		]

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button(_("Refresh now"))
		self["key_blue"] = Button(_("Edit Services"))

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
				"yellow": self.forceRefresh,
				"blue": self.editServices
			}
		)

		# Trigger change
		self.changed()

	def forceRefresh(self):
		epgrefresh.services = (Set(self.services[0]), Set(self.services[1]))
		epgrefresh.forceRefresh(self.session)

	def editServices(self):
		self.session.openWithCallback(
			self.editServicesCallback,
			EPGRefreshServiceEditor,
			self.services
		)

	def editServicesCallback(self, ret):
		if ret:
			self.services = ret

	def changed(self):
		for x in self.onChangedEntry:
			try:
				x()
			except:
				pass

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def cancelConfirm(self, result):
		if not result:
			return

		for x in self["config"].list:
			x[1].cancel()

		self.close(self.session)

	def keyCancel(self):
		if self["config"].isChanged():
			from Screens.MessageBox import MessageBox

			self.session.openWithCallback(
				self.cancelConfirm,
				MessageBox,
				_("Really close without saving settings?")
			)
		else:
			self.close(self.session)

	def keySave(self):
		epgrefresh.services = (Set(self.services[0]), Set(self.services[1]))
		epgrefresh.saveConfiguration()
		
		for x in self["config"].list:
			x[1].save()

		self.close(self.session)
