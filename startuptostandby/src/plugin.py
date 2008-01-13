# -*- coding: iso-8859-1 -*-
from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigEnableDisable
from Screens.Standby import Standby
from StartupToStandbyConfiguration import StartupToStandbyConfiguration
from enigma import eTimer

config.plugins.startuptostandby = ConfigSubsection()
config.plugins.startuptostandby.enabled = ConfigEnableDisable(default = False)
timer = eTimer()
savedkwargs = {}

def main(session, **kwargs):
	print "[StartupToStandby] Open Config Screen"
	session.open(StartupToStandbyConfiguration)
	
# Autostart
def autostart(reason, **kwargs):
	global timer
	global savedkwargs

	print "[StartupToStandby] autostart"
	if config.plugins.startuptostandby.enabled.value and reason == 0 and kwargs.has_key("session"):
		session = kwargs["session"]
		savedkwargs = kwargs
		session.open(Standby)
		#wait 10 seconds before setting standby again - bad hack...
		print "[StartupToStandby] start timer..."
		timer.timeout.get().append(timeout)
		timer.startLongTimer(10)
		print "[StartupToStandby] ...ready"

def timeout():
	global savedkwargs
	print "[StartupToStandby] Timeout!"
	#standby-screen is open - close it
	print "[StartupToStandby] Close Standby Screen"
	savedkwargs["session"].open(Standby)
	#and open it again...
	print "[StartupToStandby] Open Standby Screen"
	savedkwargs["session"].open(Standby)
	
	
def Plugins(path, **kwargs):
	return [PluginDescriptor(name="StartupToStandby", description="Startup To Standby", where = PluginDescriptor.WHERE_PLUGINMENU,fnc = main),
			PluginDescriptor(name="StartupToStandby", description = "Startup To Standby", where = PluginDescriptor.WHERE_SESSIONSTART,fnc = autostart)]


