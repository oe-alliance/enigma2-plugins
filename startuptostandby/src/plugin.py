from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigEnableDisable
from Tools import Notifications

from .StartupToStandbyConfiguration import StartupToStandbyConfiguration

if not hasattr(config.plugins, "startuptostandby"):
	config.plugins.startuptostandby = ConfigSubsection()
if not hasattr(config.plugins.startuptostandby, "enabled"):
	config.plugins.startuptostandby.enabled = ConfigEnableDisable(default=False)


def main(session, **kwargs):
	print("[StartupToStandby] Open Config Screen")
	session.open(StartupToStandbyConfiguration)


def sessionstart(reason, session=None, **kwargs):
	print("[StartupToStandby] autostart")
	if reason != 0:
		return
	from Screens.Standby import Standby, inStandby
	if config.plugins.startuptostandby.enabled.value and not inStandby and session is not None:
		Notifications.AddNotificationWithID("Standby", Standby)


def Plugins(path, **kwargs):
	return [
		PluginDescriptor(
			name="StartupToStandby",
			description="Startup To Standby",
			where=PluginDescriptor.WHERE_PLUGINMENU,
			fnc=main,
			needsRestart=False
		),
		PluginDescriptor(
			name="StartupToStandby",
			description="Startup To Standby",
			where=PluginDescriptor.WHERE_SESSIONSTART,
			fnc=sessionstart,
			needsRestart=False,
			weight=-1
		)
	]
