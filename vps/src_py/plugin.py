from Plugins.Plugin import PluginDescriptor
from os import stat
from Vps import vps_timers
from Vps_setup import VPS_Setup
from Modifications import register_vps

# Config
from Components.config import config, ConfigYesNo, ConfigSubsection, ConfigInteger

config.plugins.vps = ConfigSubsection()
config.plugins.vps.enabled = ConfigYesNo(default = True)
config.plugins.vps.initial_time = ConfigInteger(default=10, limits=(0, 120))
config.plugins.vps.allow_overwrite = ConfigYesNo(default = False)
config.plugins.vps.allow_wakeup = ConfigYesNo(default = False)
config.plugins.vps.default_vps = ConfigYesNo(default = False)
config.plugins.vps.default_overwrite = ConfigYesNo(default = False)
config.plugins.vps.infotext = ConfigInteger(default = 0)


def autostart(reason, **kwargs):
	if reason == 0:
		if kwargs.has_key("session"):
			session = kwargs["session"]
			vps_timers.session = session
			vps_timers.checkTimer()
		
		register_vps()
	
	elif reason == 1:
		vps_timers.shutdown()
		

def setup(session, **kwargs):
	session.openWithCallback(doneConfig, VPS_Setup)

def doneConfig(session, **kwargs):
	vps_timers.checkTimer()

def startSetup(menuid):
	if menuid != "system":
		return []
	return [("VPS-Plugin", setup, "vps", 50)]

def getNextWakeup():
	return vps_timers.NextWakeup()
	
	

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			name = "VPS",
			where = [
				PluginDescriptor.WHERE_AUTOSTART,
				PluginDescriptor.WHERE_SESSIONSTART
			],
			fnc = autostart,
			wakeupfnc = getNextWakeup
		),
		PluginDescriptor(
			name = "VPS-Plugin",
			where = PluginDescriptor.WHERE_MENU,
			fnc = startSetup
		),
	]
