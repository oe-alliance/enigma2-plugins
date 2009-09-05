from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import config, ConfigInteger, ConfigSubsection, ConfigSelection, \
    ConfigSubList, ConfigText, ConfigYesNo, ConfigDateTime, ConfigClock, ConfigPIN
from KTmain import KiddyTimer
from KTsetup import KiddyTimerSetup
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from __init__ import _
import KTglob
import time

config.plugins.KiddyTimer = ConfigSubsection()
config.plugins.KiddyTimer.enabled = ConfigYesNo(default=False)
config.plugins.KiddyTimer.position_x = ConfigInteger(default=590)
config.plugins.KiddyTimer.position_y = ConfigInteger(default=35)
config.plugins.KiddyTimer.timerStyle = ConfigSelection(choices = [("clock", _("Clock")), ("smiley", _("Smiley"))])
config.plugins.KiddyTimer.lastStartDay = ConfigText(default="")
config.plugins.KiddyTimer.monitorEndTime = ConfigClock(default=KTglob.EIGHTOCLOCKNOON)
config.plugins.KiddyTimer.pin = ConfigPIN(default = 1111 , censor = "*")
config.plugins.KiddyTimer.remainingTime = ConfigInteger(default=int(KTglob.ONEHOUR), limits = (0,86400) )

config.plugins.KiddyTimer.dayTimes = ConfigSubList()
for i in range(0, 7):
    s = ConfigSubsection()
    s.timeValue = ConfigClock(default=KTglob.ONEOCLOCK)
    config.plugins.KiddyTimer.dayTimes.append(s)
    del s

# Assign global variable oKiddyTimer
KTglob.oKiddyTimer = KiddyTimer()

def setup(session, **kwargs):
    session.open(KiddyTimerSetup)

def sessionstart(reason, **kwargs):
    if reason == 0:
        KTglob.oKiddyTimer.gotSession(kwargs["session"])

def autostart(reason, **kwargs):
    if reason == 1:
        KTglob.oKiddyTimer.stopMe()
        KTglob.oKiddyTimer = None
        
def Plugins(path,**kwargs):
    # Assign global variable plugin_path
    KTglob.plugin_path = path
    return [
            PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart),
            PluginDescriptor(where=PluginDescriptor.WHERE_AUTOSTART, fnc=autostart),
            PluginDescriptor(name=_("KiddyTimer"), description=_("Allows to controls your kids' daily TV usage"), icon = "KiddyTimer.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=setup)]

