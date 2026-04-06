from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigText
from Screens.ChannelSelection import ChannelContextMenu
from Screens.ChoiceBox import ChoiceBox
from enigma import eServiceReference
from Components.ChoiceList import ChoiceEntryComponent
from Screens.MessageBox import MessageBox
from Tools.BoundFunction import boundFunction

from . import _


config.startupservice = ConfigSubsection()
config.startupservice.lastservice = ConfigText(default="")
config.startupservice.lastroot = ConfigText(default="")
config.startupservice.lastmode = ConfigText(default="tv")

config.startupserviceleavingstandbymode = ConfigSubsection()
config.startupserviceleavingstandbymode.lastservice = ConfigText(default="")
config.startupserviceleavingstandbymode.lastroot = ConfigText(default="")
config.startupserviceleavingstandbymode.lastmode = ConfigText(default="tv")


baseChannelContextMenu__init__ = None
_notifier_registered = False


def _has_startup_config(config_element):
    return bool(config_element.lastservice.value and config_element.lastroot.value)


def _target_mode_config(mode):
    return config.tv if mode == "tv" else config.radio


def _copy_startup_to_lastservice(config_element):
    if not _has_startup_config(config_element):
        return

    if not hasattr(config, "servicelist"):
        config.servicelist = ConfigSubsection()
    if not hasattr(config.servicelist, "lastmode"):
        config.servicelist.lastmode = ConfigText(default="tv")
    config.servicelist.lastmode.value = config_element.lastmode.value
    config.servicelist.lastmode.save()

    target = _target_mode_config(config_element.lastmode.value)
    if not hasattr(target, "lastservice"):
        target.lastservice = ConfigText(default="")
    if not hasattr(target, "lastroot"):
        target.lastroot = ConfigText(default="")
    target.lastservice.value = config_element.lastservice.value
    target.lastroot.value = config_element.lastroot.value
    target.save()


def leaveStandby():
    if not _has_startup_config(config.startupserviceleavingstandbymode):
        return

    from Screens.InfoBar import InfoBar
    infobar = getattr(InfoBar, "instance", None)
    if not infobar or not hasattr(infobar, "servicelist"):
        return

    if config.startupserviceleavingstandbymode.lastmode.value == "tv":
        infobar.servicelist.setModeTv()
    else:
        infobar.servicelist.setModeRadio()


def standbyCounterChanged(configElement):
    if not _has_startup_config(config.startupserviceleavingstandbymode):
        return

    from Screens.Standby import inStandby

    if not inStandby or not getattr(inStandby, "prev_running_service", None):
        return

    path = inStandby.prev_running_service.getPath()
    if path and path.startswith("/"):
        return

    startup_cfg = config.startupserviceleavingstandbymode
    inStandby.prev_running_service = eServiceReference(startup_cfg.lastservice.value)

    target = _target_mode_config(startup_cfg.lastmode.value)
    if not hasattr(target, "lastservice"):
        target.lastservice = ConfigText(default="")
    if not hasattr(target, "lastroot"):
        target.lastroot = ConfigText(default="")
    target.lastservice.value = startup_cfg.lastservice.value
    target.lastroot.value = startup_cfg.lastroot.value
    target.save()

    if leaveStandby not in inStandby.onClose:
        inStandby.onClose.append(leaveStandby)


def main(session, **kwargs):
    global _notifier_registered

    _copy_startup_to_lastservice(config.startupservice)

    try:
        startUpServiceInit()
    except Exception as err:
        print("[StartUpService] init failed:", err)

    if not _notifier_registered:
        config.misc.standbyCounter.addNotifier(standbyCounterChanged, initial_call=False)
        _notifier_registered = True


def startUpServiceInit():
    global baseChannelContextMenu__init__

    if baseChannelContextMenu__init__ is None:
        baseChannelContextMenu__init__ = ChannelContextMenu.__init__

    ChannelContextMenu.__init__ = startUpService__init__
    ChannelContextMenu.startUpServiceContextMenuCallback = startUpServiceContextMenuCallback
    ChannelContextMenu.startUpServiceMenuCallback = startUpServiceMenuCallback
    ChannelContextMenu.setStartUpService = setStartUpService
    ChannelContextMenu.resetStartUpService = resetStartUpService


def startUpService__init__(self, session, csel):
    baseChannelContextMenu__init__(self, session, csel)

    current = csel.getCurrentSelection()
    current_root = csel.getRoot()
    root_path = current_root and current_root.getPath() or ""
    inBouquetRootList = 'FROM BOUQUET "bouquets.' in root_path

    if not current:
        return

    if csel.bouquet_mark_edit == 0 and not csel.movemode and not inBouquetRootList:
        if not (current.flags & (eServiceReference.isMarker | eServiceReference.isDirectory)):
            self["menu"].list.insert(1, ChoiceEntryComponent(text=((_("set as startup service"), boundFunction(self.startUpServiceContextMenuCallback, True)))))
            self["menu"].list.insert(2, ChoiceEntryComponent(text=((_("reset startup service"), boundFunction(self.startUpServiceContextMenuCallback, False)))))


def startUpServiceContextMenuCallback(self, add):
    if add:
        options = [
            (_("set as startup service after booting..."), boundFunction(self.setStartUpService, config.startupservice)),
            (_("set as startup service after leaving standby mode..."), boundFunction(self.setStartUpService, config.startupserviceleavingstandbymode)),
        ]
    else:
        options = [
            (_("reset startup service for booting..."), boundFunction(self.resetStartUpService, config.startupservice)),
            (_("reset startup service for leaving standby mode..."), boundFunction(self.resetStartUpService, config.startupserviceleavingstandbymode)),
        ]
    self.session.openWithCallback(self.startUpServiceMenuCallback, ChoiceBox, list=options)


def startUpServiceMenuCallback(self, ret):
    if ret:
        ret[1]()


def setStartUpService(self, configElement):
    current = self.csel.getCurrentSelection()
    if not current:
        self.close()
        return

    path = ";".join(service.toString() for service in self.csel.servicePath)
    if path:
        configElement.lastroot.value = "%s;" % path
        if current.type == eServiceReference.idDVB and current.getData(0) in (2, 10):
            configElement.lastmode.value = "radio"
        else:
            configElement.lastmode.value = "tv"
        configElement.lastservice.value = current.toString()
        configElement.save()
        self.close()
    else:
        self.session.openWithCallback(
            self.close,
            MessageBox,
            _("If you see this message, please switch to the service you want to mark as startservice and try again."),
            MessageBox.TYPE_ERROR,
        )


def resetStartUpService(self, configElement):
    configElement.lastroot.value = ""
    configElement.lastmode.value = "tv"
    configElement.lastservice.value = ""
    configElement.save()
    self.close()


def Plugins(**kwargs):
    return [PluginDescriptor(name="StartUpService", description="set startup service", where=PluginDescriptor.WHERE_SESSIONSTART, fnc=main)]
