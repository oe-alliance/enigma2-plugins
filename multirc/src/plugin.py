from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.config import *
from os import path

CONFIGS = [("1", "layer 1"),
	   ("2", "layer 2"),
	   ("4", "layer 3"),
	   ("8", "layer 4"),
	   ("f", "any RC")]

config.plugins.MultiRC = ConfigSubsection()
config.plugins.MultiRC.mask = ConfigSelection(choices = CONFIGS, default = "f")

# config file for IR mask, default is DM7025 or later, fallback to DM500/600
MASK = "/proc/stb/ir/rc/mask0"
if not path.exists(MASK):
	MASK = "/proc/stb/ir/rc/mask"

class MultiRCSetup(ConfigListScreen, Screen):
	skin = """
		<screen position="170,150" size="420,280" title="Multi RemoteControl" >
		<widget name="config" position="10,10" size="400,40" scrollbarMode="showOnDemand" />
		<widget name="warning" position="10,50" size="400,220" font="Regular;20" halign="center"/>
		</screen>"""

	# most of the following is black magic copied from other plugins.
	# e2 devs should really make some best practices or wrapper for this!
	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		self.list = [getConfigListEntry("Listen on Remote Control", config.plugins.MultiRC.mask)]
		ConfigListScreen.__init__(self, self.list)
		self["warning"] = Label("""WARNING!
After changing this and pressing <Ok>, your Remote Control might stop working!

Information about re-configuring the RC is available at http://www.dream-multimedia-tv.de/board/thread.php?threadid=5613""")
		self["config"].list = self.list
		self["config"].setList(self.list)
		self["setupActions"] = ActionMap(["SetupActions"],
		{
			"save": self.ask_save,
			"cancel": self.cancel,
			"ok": self.ask_save,
		}, -2)

	def ask_save(self):
		set_mask()
		# mask value 0xf allows all RCs, no need to verify
		if config.plugins.MultiRC.mask.value == "f":
			self.confirm_save(True)
		else:
			self.session.openWithCallback(self.confirm_save, MessageBox,
				"Is the RC still working?", MessageBox.TYPE_YESNO,
				timeout = 20, default = False)

	def confirm_save(self, confirmed):
		if confirmed:
			for x in self["config"].list:
				x[1].save()
			set_mask()
			self.close()
		else:
			# input failed, reset to any RC
			set_mask("f")

	def cancel(self):
		for x in self["config"].list:
			x[1].cancel()
		set_mask()
		self.close()

def set_mask(mask=None):
	if not mask:
		mask = config.plugins.MultiRC.mask.value
	f = open(MASK, "w")
	f.write(mask)
	f.close()

def multirc_setup(session, **kwargs):
	session.open(MultiRCSetup)

def multirc_autostart(reason, **kwargs):
	# on startup, set correct remote mask
	if reason == 0:
		set_mask()
		pass

def Plugins(**kwargs):
	return [PluginDescriptor(name="Multi RemoteControl",
				description="Multi Dreambox RC layer setup",
				where=PluginDescriptor.WHERE_PLUGINMENU,
				fnc = multirc_setup),

		PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART,
				fnc = multirc_autostart)]


