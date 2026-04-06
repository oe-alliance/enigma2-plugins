# for localized messages
from . import _

# Config
from Components.config import ConfigNumber, ConfigSubsection, config

# Plugin
from Plugins.Plugin import PluginDescriptor

zapperInstance = None

# Config options
config.werbezapper = ConfigSubsection()
config.werbezapper.duration = ConfigNumber(default=5)


def getWerbeZapper(session, servicelist):
    global zapperInstance
    if zapperInstance is None:
        from .WerbeZapper import WerbeZapper

        zapperInstance = session.instantiateDialog(WerbeZapper, servicelist, cleanup)
    return zapperInstance


# Main function
def main(session, servicelist, **kwargs):
    getWerbeZapper(session, servicelist).showSelection()


# Instant start / stop monitoring
def startstop(session, servicelist, **kwargs):
    instance = getWerbeZapper(session, servicelist)
    if not instance.monitor_timer.isActive():
        instance.startMonitoring()
    else:
        instance.stopMonitoring()


def cleanup():
    global zapperInstance
    if zapperInstance is not None:
        zapperInstance.shutdown()
        zapperInstance.doClose()
        zapperInstance = None


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="WerbeZapper",
            description=_("Automatically zaps back to current service after given Time"),
            where=PluginDescriptor.WHERE_EXTENSIONSMENU,
            fnc=main,
            needsRestart=False,
        ),
        PluginDescriptor(
            name="WerbeZapper Start / Stop monitoring",
            description=_("Start / Stop monitoring instantly"),
            where=PluginDescriptor.WHERE_EXTENSIONSMENU,
            fnc=startstop,
            needsRestart=False,
        ),
    ]
