# for localized messages
from . import _

# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from EPGRefreshChannelEditor import EPGRefreshServiceEditor

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

# Configuration
from Components.config import config, getConfigListEntry

from EPGRefresh import epgrefresh

class EPGRefreshConfiguration(Screen, ConfigListScreen):
	"""Configuration of EPGRefresh"""

	skin = """<screen name="EPGRefreshConfiguration" title="Configure EPGRefresh" position="center,center" size="565,370">
		<ePixmap position="0,5" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,5" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,5" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,5" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget source="key_red" render="Label" position="0,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_green" render="Label" position="140,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_yellow" render="Label" position="280,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_blue" render="Label" position="420,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="config" position="5,50" size="555,250" scrollbarMode="showOnDemand" />
		<ePixmap pixmap="skin_default/div-h.png" position="0,301" zPosition="1" size="565,2" />
		<widget source="help" render="Label" position="5,305" size="555,63" font="Regular;21" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Summary
		self.setup_title = _("EPGRefresh Configuration")
		self.onChangedEntry = []

		# Although EPGRefresh keeps services in a Set we prefer a list
		self.services = (
			[x for x in epgrefresh.services[0]],
			[x for x in epgrefresh.services[1]]
		)

		self.list = [
			getConfigListEntry(_("Refresh automatically"), config.plugins.epgrefresh.enabled, _("Unless this is enabled EPGRefresh won't automatically run but has to be explicitely started through the yellow button from this menu.")),
			getConfigListEntry(_("Wakeup from Deep-Standby to refresh EPG"), config.plugins.epgrefresh.wakeup, _("If this is enabled, the plugin will wake the receiver up from deep-standby if possible. Otherwise it has to be turned on already.")),
			getConfigListEntry(_("Time to stay on service (in m)"), config.plugins.epgrefresh.interval, _("This is the ammount of time a channel will be active during a refresh.")),
			getConfigListEntry(_("Refresh EPG after"), config.plugins.epgrefresh.begin, _("An automated refresh will happen after this time of day, but before the next setting.")),
			getConfigListEntry(_("Refresh EPG before"), config.plugins.epgrefresh.end, _("An automated refresh will happen before this time of day, but after the previous setting.")),
			getConfigListEntry(_("Delay when not in Standby (in m)"), config.plugins.epgrefresh.delay_standby, _("If the receiver is currently not in standby this is the amount of time EPGRefresh will wait before trying again.")),
			getConfigListEntry(_("Force scan even if receiver is in use"), config.plugins.epgrefresh.force, _("This setting controls whether or not the refresh will also be initiated when the receiver is being used (namely not in standby or currently recording).")),
			getConfigListEntry(_("Inherit Services from AutoTimer if available"), config.plugins.epgrefresh.inherit_autotimer, _("If you're also using the AutoTimer plugin this allows to extend the list of services to refresh by the services your AutoTimers are restricted to.")),
			getConfigListEntry(_("Make AutoTimer parse EPG if available"), config.plugins.epgrefresh.parse_autotimer, _("If you're also using the AutoTimer plugin this will initiate a scan of the EPG after a completed refresh.")),
			getConfigListEntry(_("Shutdown after refresh"), config.plugins.epgrefresh.afterevent, _("This setting controls if the receiver should be sent to deep-standby after a completed refresh.")),
		]

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)
		self["config"].onSelectionChanged.append(self.updateHelp)

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("Refresh now"))
		self["key_blue"] = StaticText(_("Edit Services"))

		self["help"] = StaticText()

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

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Configure EPGRefresh"))

	def updateHelp(self):
		cur = self["config"].getCurrent()
		if cur:
			self["help"].text = cur[2]

	def forceRefresh(self):
		epgrefresh.services = (set(self.services[0]), set(self.services[1]))
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
			except Exception:
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
		epgrefresh.services = (set(self.services[0]), set(self.services[1]))
		epgrefresh.saveConfiguration()

		for x in self["config"].list:
			x[1].save()

		self.close(self.session)
