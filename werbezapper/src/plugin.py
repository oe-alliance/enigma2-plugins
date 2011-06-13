# for localized messages
from . import _

# Plugin
from Plugins.Plugin import PluginDescriptor

zapperInstance = None

# Mainfunction
def main(session, servicelist, **kwargs):
	# Create Instance if none present, show Dialog afterwards
	global zapperInstance
	if zapperInstance is None:
		from WerbeZapper import WerbeZapper
		zapperInstance = WerbeZapper(session, servicelist, cleanup)
	zapperInstance.showSelection()

def cleanup():
	global zapperInstance
	if zapperInstance is not None:
		zapperInstance.shutdown()
		zapperInstance = None

def Plugins(**kwargs):
 	return [
		PluginDescriptor(
			name = "Werbezapper",
			description = _("Automatically zaps back to current service after given Time"),
			where = PluginDescriptor.WHERE_EXTENSIONSMENU,
			fnc = main,
			needsRestart = False,
		)
	]

