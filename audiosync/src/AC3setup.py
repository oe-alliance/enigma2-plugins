# for localized messages
from . import _

from AC3utils import PLUGIN_BASE, PLUGIN_VERSION
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Sources.StaticText import StaticText
from Components.Sources.Boolean import Boolean
from Components.ConfigList import ConfigListScreen
from Components.Label import Label,MultiColorLabel
from Components.ProgressBar import ProgressBar
from Components.config import config, getConfigListEntry
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Components.Pixmap import Pixmap
from Screens.Screen import Screen

class AC3LipSyncSetup(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="560,400" title="AC3 Lip Sync Setup">
			<ePixmap pixmap="~/img/button-red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="~/img/button-green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#9f1313" transparent="1" shadowColor="#000000" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" shadowColor="#000000" shadowOffset="-1,-1" />
			<widget name="config" position="10,40" size="540,320" scrollbarMode="showOnDemand" />
			<widget name="PluginInfo" position="10,370" size="540,20" zPosition="4" font="Regular;18" foregroundColor="#cccccc" />
		</screen>"""

	def __init__(self, session, plugin_path):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("Audio Sync Setup"))
		self.skinName = ["Setup"]
		self["HelpWindow"] = Pixmap()
		self["HelpWindow"].hide()
		self["VKeyIcon"] = Boolean(False)
		self['footnote'] = Label("")
		self["status"] = StaticText(_("Plugin: %(plugin)s , Version: %(version)s") % dict(plugin=PLUGIN_BASE,version=PLUGIN_VERSION))

		# Lets get a list of elements for the config list
		self.list = [
			getConfigListEntry(_("Outer Bound (+/-)"), config.plugins.AC3LipSync.outerBounds),
			getConfigListEntry(_("Step in ms for arrow keys"), config.plugins.AC3LipSync.arrowStepSize),
			getConfigListEntry(_("Wait time in ms before activation:"), config.plugins.AC3LipSync.activationDelay),
			getConfigListEntry(_("Step in ms for keys '%s'") % ("1/3"), config.plugins.AC3LipSync.stepSize13),
			getConfigListEntry(_("Step in ms for keys '%s'") % ("4/6"), config.plugins.AC3LipSync.stepSize46),
			getConfigListEntry(_("Step in ms for keys '%s'") % ("7/9"), config.plugins.AC3LipSync.stepSize79),
			getConfigListEntry(_("Step in ms for key %i") % (2), config.plugins.AC3LipSync.absoluteStep2),
			getConfigListEntry(_("Step in ms for key %i") % (5), config.plugins.AC3LipSync.absoluteStep5),
			getConfigListEntry(_("Step in ms for key %i") % (8), config.plugins.AC3LipSync.absoluteStep8)
		]

		ConfigListScreen.__init__(self, self.list)
		self["config"].list = self.list
		self.skin_path = plugin_path

		#check for list.entries > 0 else self.close
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))

		self["setupActions"] = NumberActionMap(["SetupActions", "ColorActions"],
		{
			"save": self.save,
			"cancel": self.cancel,
			"green": self.save,
			"red": self.cancel,
			"ok": self.save,
		}, -2)

	def save(self):
		for x in self.list:
			x[1].save()
		self.close()

	def cancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()
