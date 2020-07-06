from __future__ import absolute_import
# for localized messages
from . import _

# Config
from Components.config import *

# Plugin
from Plugins.Plugin import PluginDescriptor

zapperInstance = None

# Config options
config.werbezapper          = ConfigSubsection()
config.werbezapper.duration = ConfigNumber(default = 5)


# Mainfunction
def main(session, servicelist, **kwargs):
	# Create Instance if none present
	global zapperInstance
	if zapperInstance is None:
		from .WerbeZapper import WerbeZapper
		zapperInstance = session.instantiateDialog( WerbeZapper, servicelist, cleanup )
	# Show dialog
	zapperInstance.showSelection()

# Instant start / stop monitoring
def startstop(session, servicelist, **kwargs):
	# Create Instance if none present
	global zapperInstance
	if zapperInstance is None:
		from .WerbeZapper import WerbeZapper
		zapperInstance = session.instantiateDialog( WerbeZapper, servicelist, cleanup )
	# Start or stop monitoring
	if not zapperInstance.monitor_timer.isActive():
		zapperInstance.startMonitoring()
	else:
		zapperInstance.stopMonitoring()

def cleanup():
	global zapperInstance
	if zapperInstance is not None:
		zapperInstance.shutdown()
		zapperInstance.doClose()
		zapperInstance = None

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			name = "Werbezapper",
			description = _("Automatically zaps back to current service after given Time"),
			where = PluginDescriptor.WHERE_EXTENSIONSMENU,
			fnc = main,
			needsRestart = False,
		),
		PluginDescriptor(
			name = "Werbezapper Start / Stop monitoring",
			description = _("Start / Stop monitoring instantly"),
			where = PluginDescriptor.WHERE_EXTENSIONSMENU,
			fnc = startstop,
			needsRestart = False,
		)
	]

