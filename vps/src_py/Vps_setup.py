# -*- coding: utf-8 -*-

from . import _
from Screens.Screen import Screen
from Components.ScrollLabel import ScrollLabel
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.config import config, getConfigListEntry

class VPS_Setup(Screen, ConfigListScreen):

	skin = """<screen name="vpsConfiguration" title="VPS-Plugin" position="center,center" size="565,370">
		<ePixmap position="0,5" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,5" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,5" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,5" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget source="key_red" render="Label" position="0,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_green" render="Label" position="140,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_blue" render="Label" position="420,5" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="config" position="5,50" size="555,200" scrollbarMode="showOnDemand" />
		<ePixmap pixmap="skin_default/div-h.png" position="0,251" zPosition="1" size="565,2" />
		<widget source="help" render="Label" position="5,255" size="555,113" font="Regular;21" />
	</screen>"""
	
	def __init__(self, session):
		Screen.__init__(self, session)
		
		self.setup_title = "VPS-Plugin Einstellungen"
		
		self.vps_enabled = getConfigListEntry(_("Enable VPS-Plugin"), config.plugins.vps.enabled)
		self.vps_initial_time = getConfigListEntry(_("Starting time"), config.plugins.vps.initial_time)
		self.vps_allow_overwrite = getConfigListEntry(_("Recordings can be controlled by channel"), config.plugins.vps.allow_overwrite)
		self.vps_allow_wakeup = getConfigListEntry(_("Wakeup from Deep-Standby is allowed"), config.plugins.vps.allow_wakeup)
		self.vps_default = getConfigListEntry(_("VPS enabled by default"), config.plugins.vps.default_vps)
		self.vps_default_overwrite = getConfigListEntry(_("Recordings are controlled by channel by default"), config.plugins.vps.default_overwrite)
		
		self.list = []
		self.list.append(self.vps_enabled)
		self.list.append(self.vps_initial_time)
		self.list.append(self.vps_allow_overwrite)
		self.list.append(self.vps_allow_wakeup)
		self.list.append(self.vps_default)
		self.list.append(self.vps_default_overwrite)

		ConfigListScreen.__init__(self, self.list, session = session)
		self["config"].onSelectionChanged.append(self.updateHelp)

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_blue"] = StaticText(_("Information"))

		self["help"] = StaticText()

		# Define Actions
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
				"blue": self.show_info,
			}
		)
	
	def updateHelp(self):
		cur = self["config"].getCurrent()
		if cur == self.vps_enabled:
			self["help"].text = _("This plugin can determine whether a programme begins earlier or lasts longer. The channel has to provide reliable data.")
		elif cur == self.vps_initial_time:
			self["help"].text = _("If possible, x minutes before a timer starts VPS-Plugin will control whether the programme begins earlier. (0 disables feature)")
		elif cur == self.vps_allow_overwrite:
			self["help"].text = _("If enabled, you can decide whether a timer should be controlled by channel (Running-Status). Programmed start and end time will be ignored.")
		elif cur == self.vps_default:
			self["help"].text = _("Enable VPS by default (new timers)")
		elif cur == self.vps_default_overwrite:
			self["help"].text = _("Enable \"Recording controlled by channel\" by default (new timers)")
		elif cur == self.vps_allow_wakeup:
			self["help"].text = _("If enabled and necessary, the plugin will wake up the Dreambox from Deep-Standby for the defined starting time to control whether the programme begins earlier.")

	def show_info(self):
		VPS_show_info(self.session)
	
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
		for x in self["config"].list:
			x[1].save()

		self.close(self.session)



class VPS_Screen_Info(Screen):
	skin = """<screen name="vpsInfo" position="center,center" size="550,400" title="VPS-Plugin Information">
		<widget name="text" position="10,10" size="540,390" font="Regular;22" />
	</screen>"""
	
	def __init__(self, session):
		Screen.__init__(self, session)
		
		self["text"] = ScrollLabel(_("The VPS-Plugin can react on delays arising in the startTime or endTime of a programme. VPS is only supported by certain channels!\n\nIf you enable VPS, the recording is definitely starting at the latest at the startTime. The recording may start earlier or lasts longer.\n\nIf you also enable \"Recording controlled by channel\", the recording will only start, when the channel flags the programme as running.\n\n\nSupported channels\n\nGermany:\n ARD, ZDF, Sky and DMAX\n\nAustria:\n ORF and Servus TV\n\nCzech Republic:\n CT\n\nIf a timer is programmed manually (not via EPG), it is necessary to set a VPS-Time to enable VPS. VPS-Time (also known as PDC) is the first published start time, e.g. given in magazines. If you set a VPS-Time, you have to leave timer name empty."))
		
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"], 
			{
				"cancel": self.close,
				"ok": self.close,
				"up": self["text"].pageUp,
				"down": self["text"].pageDown,
			}, -1)
		
	
def VPS_show_info(session):
	session.open(VPS_Screen_Info)
	