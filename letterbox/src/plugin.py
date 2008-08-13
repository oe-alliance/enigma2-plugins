from Plugins.Plugin import PluginDescriptor
from Components.ServiceEventTracker import ServiceEventTracker
from Screens.Screen import Screen
from enigma import iPlayableService

# config file to read/write state
POLICY = "/proc/stb/video/policy"

# list of mode choices to cycle through
MODE_CHOICES = ["letterbox", "panscan"]

def get_mode():
	f = open(POLICY, "r")
	mode = f.read().strip("\n")
	f.close()
	return mode

def set_mode(mode):
	f = open(POLICY, "w")
	f.write(mode + "\n")
	f.close()


class LetterBox(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.default = None
		self.tracker = ServiceEventTracker(screen=self, eventmap=
				{ iPlayableService.evStart: self.reset, })
		self.used = False

	def reset(self):
		if self.used:
			set_mode(self.default)
			self.used = False
		else:
			self.default = get_mode()

	def toggle(self):
		mode = get_mode()
		if not mode in MODE_CHOICES:
			MODE_CHOICES.append(mode)
		modeidx = MODE_CHOICES.index(mode)
		modeidx = (modeidx + 1) % len(MODE_CHOICES)
		set_mode(MODE_CHOICES[modeidx])
		self.used = True

letterbox = None

def zoom_init(reason, **kwargs):
	global letterbox
	letterbox = LetterBox(kwargs["session"])

def zoom_toggle(session, **kwargs):
	global letterbox
	letterbox.toggle()

def Plugins(**kwargs):
	plname = "LetterBox Zoom"
	return [PluginDescriptor(name=plname,
			description="Zoom into letterboxed movies",
			where=PluginDescriptor.WHERE_EXTENSIONSMENU,
			fnc=zoom_toggle),
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART,
			fnc=zoom_init)]

