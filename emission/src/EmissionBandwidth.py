# GUI (Screens)
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText

# Configuration
from Components.config import config, getConfigListEntry, \
	ConfigNumber, ConfigSelection, ConfigText, ConfigYesNo, NoSave

class EmissionBandwidth(Screen, ConfigListScreen):
	def __init__(self, session, val, isTorrent, rpc_version):
		Screen.__init__(self, session)
		self.skinName = ["EmissionBandwith", "Setup"]

		# Summary
		self.setup_title = _("Bandwidth settings")
		self.onChangedEntry = []

		ConfigListScreen.__init__(self, [], session=session, on_change=self.changed)

		self.isTorrent = isTorrent
		if isTorrent:
			if rpc_version < 5:
				downloadLimitMode = val.downloadLimitMode
				uploadLimitMode = val.uploadLimitMode
				modelist = [(0, _("Global Setting")), (2, _("Unlimited")), (1, _("Limit"))]
			else:
				downloadLimitMode = val.downloadLimited
				uploadLimitMode = val.uploadLimited
				modelist = [(0, _("Global Setting")), (1, _("Limit"))] # XXX: this is a pure guess...

			self.downloadLimitMode = NoSave(ConfigSelection(choices=modelist, default=downloadLimitMode))
			self.downloadLimit = NoSave(ConfigNumber(default=val.downloadLimit))
			self.uploadLimitMode = NoSave(ConfigSelection(choices=modelist, default=uploadLimitMode))
			self.uploadLimit = NoSave(ConfigNumber(default=val.uploadLimit))
			self.maxConnectedPeers = NoSave(ConfigNumber(default=val.maxConnectedPeers))
		else: #if not isTorrent:
			if rpc_version < 5:
				peerLimit = val.peer_limit
				port = val.port
				pex_allowed = val.pex_allowed
			else:
				peerLimit = val.peer_limit_global
				port = val.peer_port
				pex_allowed = val.pex_enabled

			self.downloadLimitMode = NoSave(ConfigSelection(choices=[(0, _("Unlimited")), (1, _("Limit"))], default=val.speed_limit_down_enabled))
			self.downloadLimit = NoSave(ConfigNumber(default=val.speed_limit_down))
			self.uploadLimitMode = NoSave(ConfigSelection(choices=[(0, _("Unlimited")), (1, _("Limit"))], default=val.speed_limit_up_enabled))
			self.uploadLimit = NoSave(ConfigNumber(default=val.speed_limit_up))
			self.maxConnectedPeers = NoSave(ConfigNumber(default=peerLimit))
			self.encryption = NoSave(ConfigSelection(choices=[('required', _("required")), ('preferred', _("preferred")), ('tolerated', _("tolerated"))], default=val.encryption))
			self.download_dir = NoSave(ConfigText(default=val.download_dir, fixed_size=False))
			self.pex_allowed = NoSave(ConfigYesNo(default=pex_allowed))
			self.port = NoSave(ConfigNumber(default=port))
			self.port_forwarding_enabled = NoSave(ConfigYesNo(default=val.port_forwarding_enabled))

		self.downloadLimitMode.addNotifier(self.updateList, initial_call=False)
		self.uploadLimitMode.addNotifier(self.updateList, initial_call=False)

		self.updateList()

		# Initialize widgets
		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))
		self.full_title = _("%s bandwidth settings") % (isTorrent and str(val.name) or "eMission")

		# Define Actions
		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.keySave,
			}
		)

		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.setCustomTitle)

	def updateList(self, *args):
		list = [
			getConfigListEntry(_("Download rate"), self.downloadLimitMode)
		]
		if self.downloadLimitMode.value == 1:
			list.append(getConfigListEntry(_("Limit"), self.downloadLimit))
		list.append(getConfigListEntry(_("Upload rate"), self.uploadLimitMode))
		if self.uploadLimitMode.value == 1:
			list.append(getConfigListEntry(_("Limit"), self.uploadLimit))
		list.append(getConfigListEntry(_("Maximum Connections"), self.maxConnectedPeers))
		if not self.isTorrent:
			list.extend((
				getConfigListEntry(_("Encryption"), self.encryption),
				getConfigListEntry(_("Download directory"), self.download_dir),
				getConfigListEntry(_("Allow PEX"), self.pex_allowed),
				getConfigListEntry(_("Port"), self.port),
				getConfigListEntry(_("Enable Port-Forwarding"), self.port_forwarding_enabled),
			))
		self["config"].setList(list)

	def setCustomTitle(self):
		self.setTitle(self.full_title)

	def changed(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def keySave(self):
		if self.downloadLimitMode.value == 2 or self.uploadLimitMode.value == 2:
			self.session.open(
					MessageBox,
					_("Setting \"Unlimited\" is not supported via RPC.\nEither abort or choose another limit to continue."),
					type=MessageBox.TYPE_ERROR
			)
		else:
			# NOTE: transmissionrpc will take care of translating the arguments
			dict = {
				'speed_limit_down_enabled': self.downloadLimitMode.value,
				'speed_limit_down': self.downloadLimit.value,
				'speed_limit_up_enabled': self.uploadLimitMode.value,
				'speed_limit_up': self.uploadLimit.value,
				'peer_limit': self.maxConnectedPeers.value,
			}
			if not self.isTorrent:
				dict.update({
					'encryption': self.encryption.value,
					'download_dir': self.download_dir.value,
					'pex_allowed': self.pex_allowed.value,
					'port': self.port.value,
					'port_forwarding_enabled': self.port_forwarding_enabled.value,
				})
			self.close(dict)

