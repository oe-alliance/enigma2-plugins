from __future__ import print_function
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.config import *
from os import path

CONFIGS = [("1", _("layer 1")),
	   ("2", _("layer 2")),
	   ("4", _("layer 3")),
	   ("8", _("layer 4")),
	   ("f", _("any RC"))]

CONFIGS1 = [("100", _("DM8000-RC layer 1")),
	     ("200", _("DM8000-RC layer 2")),
	     ("400", _("DM8000-RC layer 3")),
	     ("800", _("DM8000-RC layer 4"))]

CONFIGS2 = [("10000", _("Illuminated RC layer 1")),
	    ("20000", _("Illuminated RC layer 2")),
	    ("40000", _("Illuminated RC layer 3")),
	    ("80000", _("Illuminated RC layer 4"))]

# config file for IR mask, default is DM7025 or later, fallback to DM500/600
# new-gen boxes also support DM8000 RCs via mask1
MASK = "/proc/stb/ir/rc/mask0"
if path.exists(MASK):
	MASK1 = "/proc/stb/ir/rc/mask1"
	CONFIGS += CONFIGS1
	MASK2 = "/proc/stb/ir/rc/mask2"
	# check for mask2 (RCU, only on newer kernels)
	if path.exists(MASK2):
		CONFIGS += CONFIGS2
	else:
		MASK2 = None
else:
	MASK = "/proc/stb/ir/rc/mask"

config.plugins.MultiRC = ConfigSubsection()
config.plugins.MultiRC.mask = ConfigSelection(choices = CONFIGS, default = "f")

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
		self.list = [getConfigListEntry(_("Listen on Remote Control"), config.plugins.MultiRC.mask)]
		ConfigListScreen.__init__(self, self.list)
		self["warning"] = Label(_("""WARNING!
After changing this and pressing <Ok>, your Remote Control might stop working!

Information about re-configuring the RC is available at http://www.dream-multimedia-tv.de/board/thread.php?threadid=5613"""))
		self["config"].list = self.list
		self["config"].setList(self.list)
		self["setupActions"] = ActionMap(["SetupActions"],
		{
			"save": self.ask_save,
			"cancel": self.cancel,
			"ok": self.ask_save,
		}, -2)

	def ask_save(self):
		if not set_mask():
			self.session.open(MessageBox, text = _("Error writing to %s!") % MASK,
				type = MessageBox.TYPE_WARNING)
			return
		# mask value 0xf allows all RCs, no need to verify
		if config.plugins.MultiRC.mask.value == "f":
			self.confirm_save(True)
		else:
			self.session.openWithCallback(self.confirm_save, MessageBox,
				_("Is the RC still working?"), MessageBox.TYPE_YESNO,
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

def write_mask(fname, value):
	print("MultiRC:", fname, value)
	f = open(fname, "w")
	f.write(value)
	f.close()

def set_mask(mask=None):
	if not mask:
		mask = config.plugins.MultiRC.mask.value
	try:
		# we have to separate old-rc values (1..8) to mask0,
		# DM8000-RC values (100..800) to mask1 and Illuminated RC
		# values (10000..80000) to mask2. The special
		# case "any RC" (f) must be set to all three.
		if mask == "f":
			mask = "0f0f0f"
		v = "000000" + mask
		mask0 = v[-2:]		# last two digits
		mask1 = v[-4:-2] + "00"	# four digits (WTF?)
		mask2 = v[-6:-4]	# first two, if available

		write_mask(MASK, mask0)
		if MASK1:
			write_mask(MASK1, mask1)
		if MASK2:
			write_mask(MASK2, mask2)

	except Exception as e:
		print("MultiRC failed:", e)
		return False
	return True

def multirc_setup(session, **kwargs):
	session.open(MultiRCSetup)

def multirc_autostart(reason, **kwargs):
	# on startup, set correct remote mask
	if reason == 0:
		set_mask()
		pass

def Plugins(**kwargs):
	return [PluginDescriptor(name="Multi RemoteControl",
				description=_("Multi Receiver RC layer setup"),
				where=PluginDescriptor.WHERE_PLUGINMENU,
				fnc = multirc_setup),

		PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART,
				fnc = multirc_autostart)]


