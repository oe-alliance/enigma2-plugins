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
from Components.SystemInfo import SystemInfo

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
			getConfigListEntry(_("Refresh EPG automatically"), config.plugins.epgrefresh.enabled, _("Unless this is enabled, EPGRefresh won't automatically run but needs to be explicitly started by the yellow button in this menu.")),
			getConfigListEntry(_("Show popup when refresh starts and ends"), config.plugins.epgrefresh.enablemessage, _("This setting controls whether or not an informational message will be shown at start and completion of refresh.")),
			getConfigListEntry(_("Wake up from deep stand-by for EPG refresh"), config.plugins.epgrefresh.wakeup, _("If this is enabled, the plugin will wake up the receiver from deep stand-by if possible. Otherwise it needs to be switched on already.")),
			getConfigListEntry(_("Duration to stay on service-channels (minutes)"), config.plugins.epgrefresh.interval, _("This is the duration for each servive-channel to stay active during a refresh run.")),
			getConfigListEntry(_("EPG refresh auto-start earliest (hh:mm)"), config.plugins.epgrefresh.begin, _("An automated refresh will start after this time of day, but before the time specified in next setting.")),
			getConfigListEntry(_("EPG refresh auto-start latest (hh:mm)"), config.plugins.epgrefresh.end, _("An automated refresh will start before this time of day, but after the time specified in previous setting.")),
			getConfigListEntry(_("Delay if not in stand-by (minutes)"), config.plugins.epgrefresh.delay_standby, _("If the receiver currently isn't in stand-by, this is the duration which EPGRefresh will wait before retry.")),
			getConfigListEntry(_("Force scan even if receiver is in use"), config.plugins.epgrefresh.force, _("This setting controls whether or not the refresh will be initiated even though the receiver is active (either not in standby or currently recording).")),
			getConfigListEntry(_("Shutdown after EPG refresh"), config.plugins.epgrefresh.afterevent, _("This setting controls whether the receiver should be set to deep standby after refresh is completed.")),
                ]
		if SystemInfo.get("NumVideoDecoders", 1) > 1:
			self.list.insert(2, getConfigListEntry(_("Refresh hidden in background"), config.plugins.epgrefresh.background, _("Do you want to refresh EPG in background by using the Picture in Picture (PiP) feature?")))

		try:
			# try to import autotimer module to check for its existence
			from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer

			self.list.append(getConfigListEntry(_("Inherit Services from AutoTimer"), config.plugins.epgrefresh.inherit_autotimer, _("Extend the list of services to refresh by those your AutoTimers use?")))
			self.list.append(getConfigListEntry(_("Run AutoTimer after refresh"), config.plugins.epgrefresh.parse_autotimer, _("After a successful refresh the AutoTimer will automatically search for new matches if this is enabled.")))
		except ImportError, ie:
			print "[EPGRefresh] AutoTimer Plugin not installed:", e

		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)
		def selectionChanged():
			if self["config"].current:
				self["config"].current[1].onDeselect(self.session)
			self["config"].current = self["config"].getCurrent()
			if self["config"].current:
				self["config"].current[1].onSelect(self.session)
			for x in self["config"].onSelectionChanged:
				x()
		self["config"].selectionChanged = selectionChanged
		self["config"].onSelectionChanged.append(self.updateHelp)

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("Refresh now"))
		self["key_blue"] = StaticText(_("Edit Services"))

		self["help"] = StaticText()

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions", "ChannelSelectEPGActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
				"yellow": self.forceRefresh,
				"blue": self.editServices,
				"showEPGList": self.keyInfo,
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

	def keyInfo(self):
		from Screens.MessageBox import MessageBox

		lastscan = config.plugins.epgrefresh.lastscan.value
		if lastscan:
			from Tools.FuzzyDate import FuzzyTime
			scanDate = ', '.join(FuzzyTime(lastscan))
		else:
			scanDate = _("never")

		self.session.open(
				MessageBox,
				_("Last refresh was %s") % (scanDate,),
				type=MessageBox.TYPE_INFO
		)

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
