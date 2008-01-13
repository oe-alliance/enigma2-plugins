# -*- coding: iso-8859-1 -*-
from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigEnableDisable
from Screens.Standby import Standby
from StartupToStandbyConfiguration import StartupToStandbyConfiguration
from enigma import eTimer

config.plugins.startuptostandby = ConfigSubsection()
config.plugins.startuptostandby.enabled = ConfigEnableDisable(default = False)


def __init__(self):
	self.timer = eTimer()
	self.session = {}	

def main(session, **kwargs):
	print "[StartupToStandby] Open Config Screen"
	session.open(StartupToStandbyConfiguration)
	
# Autostart
def autostart(reason, **kwargs):
	print "[StartupToStandby] autostart"
	if config.plugins.startuptostandby.enabled.value and reason == 0 and kwargs.has_key("session"):
		session = kwargs["session"]
		session.open(Standby)
		timer = eTimer()
		#wait 10 seconds before setting standby again - bad hack...
		print "[StartupToStandby] start timer..."
		timer.timeout.get().append(timeout)
		timer.start(10000)
		print "[StartupToStandby] ...ready"

def timeout():
	print "[StartupToStandby] Timeout!"
	#standby-screen is open - close it
	print "[StartupToStandby] Close Standby Screen"
	session.open(Standby)
	#and open it again...
	print "[StartupToStandby] Open Standby Screen"
	session.open(Standby)
	#end timer, since we only need to do this once.
	print "[StartupToStandby] Stop Timer"
	timer.stop()
		
def Plugins(path, **kwargs):
	return [PluginDescriptor(name="StartupToStandby", description="Startup To Standby", where = PluginDescriptor.WHERE_PLUGINMENU,fnc = main),
			PluginDescriptor(name="StartupToStandby", description = "Startup To Standby", where = PluginDescriptor.WHERE_SESSIONSTART,fnc = autostart)]


