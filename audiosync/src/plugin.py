from __future__ import absolute_import
# for localized messages
from . import _

from Components.config import config, ConfigSubsection, ConfigInteger, ConfigSubList
from boxbranding import getImageDistro
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from . import AC3main
from . import AC3setup

from six.moves import reload_module


config.plugins.AC3LipSync = ConfigSubsection()
config.plugins.AC3LipSync.outerBounds = ConfigInteger(default = 1000, limits = (-10000, 10000))
config.plugins.AC3LipSync.arrowStepSize = ConfigInteger(default = 5, limits = (-10000, 10000))
config.plugins.AC3LipSync.activationDelay = ConfigInteger(default = 800, limits = (-10000, 10000))
config.plugins.AC3LipSync.stepSize13 = ConfigInteger(default = 50, limits = (-10000, 10000))
config.plugins.AC3LipSync.stepSize46 = ConfigInteger(default = 200, limits = (-10000, 10000))
config.plugins.AC3LipSync.stepSize79 = ConfigInteger(default = 500, limits = (-10000, 10000))
config.plugins.AC3LipSync.absoluteStep2 = ConfigInteger(default = 0, limits = (-10000, 10000))
config.plugins.AC3LipSync.absoluteStep5 = ConfigInteger(default = 0, limits = (-10000, 10000))
config.plugins.AC3LipSync.absoluteStep8 = ConfigInteger(default = 0, limits = (-10000, 10000))
config.plugins.AC3LipSync.position_x = ConfigInteger(default=0)
config.plugins.AC3LipSync.position_y = ConfigInteger(default=0)

def main(session, **kwargs):
#	 reload_module(AC3main)
	session.open(AC3main.AC3LipSync, plugin_path)

def startSetup(menuid, **kwargs):
	if getImageDistro() == "ventonsupport":
		if menuid == "expert":
			return [(_("Audio Sync Setup"), setup, "audiosync_setup", 41)]
		else:
			return []
	elif getImageDistro() in ("openatv", "openhdf"):
		if menuid == "audio_menu":
			return [(_("Audio Sync Setup"), setup, "audiosync_setup", 41)]
		else:
			return []
	else:
		if menuid == "system":
			return [(_("Audio Sync Setup"), setup, "audiosync_setup", 41)]
		else:
			return []

def setup(session, **kwargs):
#	 reload_module(AC3setup)
	session.open(AC3setup.AC3LipSyncSetup, plugin_path)

def audioMenu(session, **kwargs):
#	 reload_module(AC3setup)
	session.open(AC3main.AC3LipSync, plugin_path)

def Plugins(path,**kwargs):
	global plugin_path
	plugin_path = path
	return [ PluginDescriptor(name=_("Audio Sync Setup"), description=_("Setup for the Audio Sync Plugin"), where = PluginDescriptor.WHERE_MENU, fnc=startSetup),
		PluginDescriptor(name=_("Audio Sync"), description=_("sets the Audio Delay (LipSync)"), where = PluginDescriptor.WHERE_AUDIOMENU, fnc=audioMenu)]
