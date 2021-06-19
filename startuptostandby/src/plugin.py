# -*- coding: iso-8859-1 -*-
from __future__ import print_function
from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigEnableDisable
from Screens.Standby import Standby, inStandby
from StartupToStandbyConfiguration import StartupToStandbyConfiguration
from Tools import Notifications

config.plugins.startuptostandby = ConfigSubsection()
config.plugins.startuptostandby.enabled = ConfigEnableDisable(default=False)


def main(session, **kwargs):
	print("[StartupToStandby] Open Config Screen")
	session.open(StartupToStandbyConfiguration)

# sessionstart


def sessionstart(reason, session=None):
	print("[StartupToStandby] autostart")
	if config.plugins.startuptostandby.enabled.value and reason == 0 and not inStandby:
		Notifications.AddNotificationWithID("Standby", Standby)


def Plugins(path, **kwargs):
	return [PluginDescriptor(name="StartupToStandby", description="Startup To Standby", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main, needsRestart=False),
			PluginDescriptor(name="StartupToStandby", description="Startup To Standby", where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart, needsRestart=False, weight=-1)]
