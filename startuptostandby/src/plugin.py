# -*- coding: iso-8859-1 -*-
from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigEnableDisable
from Screens.Standby import Standby
from StartupToStandbyConfiguration import StartupToStandbyConfiguration
from enigma import eTimer

config.plugins.startuptostandby = ConfigSubsection()
config.plugins.startuptostandby.enabled = ConfigEnableDisable(default = False)

my_global_session = None

def timeout():
	print "[StartupToStandby] Timeout, Open Standby Screen"
	my_global_session.open(Standby)

timer = eTimer()
timer.callback.append(timeout)

def main(session, **kwargs):
	print "[StartupToStandby] Open Config Screen"
	session.open(StartupToStandbyConfiguration)

# sessionstart
def sessionstart(reason, session = None):
	print "[StartupToStandby] autostart"
	if config.plugins.startuptostandby.enabled.value and reason == 0:
		global my_global_session
		my_global_session = session
		my_global_session.open(Standby)
		# wait 10 seconds before setting standby again -
		# bad hack so we do not only have a blank screen but are actually in standby...
		print "[StartupToStandby] start timer..."
		timer.startLongTimer(10)

def Plugins(path, **kwargs):
	return [PluginDescriptor(name="StartupToStandby", description="Startup To Standby", where = PluginDescriptor.WHERE_PLUGINMENU,fnc = main),
			PluginDescriptor(name="StartupToStandby", description = "Startup To Standby", where = PluginDescriptor.WHERE_SESSIONSTART,fnc = sessionstart)]

