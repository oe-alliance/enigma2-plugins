from Components.config import config, ConfigSubsection, ConfigInteger, ConfigSubList
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
import AC3main
import AC3setup

config.plugins.AC3LipSync = ConfigSubsection()
config.plugins.AC3LipSync.lowerBound = ConfigInteger(default = 0, limits = (0,10000))
config.plugins.AC3LipSync.upperBound = ConfigInteger(default = 405, limits = (0,10000))
config.plugins.AC3LipSync.arrowStepSize = ConfigInteger(default = 5, limits = (0,10000))
config.plugins.AC3LipSync.stepSize = ConfigInteger(default = 45, limits = (0,10000))
config.plugins.AC3LipSync.keySteps = ConfigSubList()
for i in range(0, 10):
    s = ConfigSubsection() 
    s.stepSize = ConfigInteger(default = i*45, limits = (0,10000))
    config.plugins.AC3LipSync.keySteps.append(s)
    del s
            
def main(session, **kwargs):
#    reload(AC3main)
    session.open(AC3main.AC3LipSync)
    
def setup(session, **kwargs):
#    reload(AC3setup)
    session.open(AC3setup.AC3LipSyncSetup)

def mainSetup(menuid, **kwargs):
    if menuid == "setup": 
        return [(_("AC3 Lip Sync"), main, "ac3_lipsync", 99)]
    return [ ]

def Plugins(**kwargs):
    return [ PluginDescriptor(name=_("AC3 Lip Sync"), description=_("sets the AC3 audio Delay (LipSync)"), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main), 
        PluginDescriptor(name=_("AC3 Lip Sync Setup"), description=_("Setup for the AC3 Lip Sync Plugin"), icon = "AC3LipSync.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=setup),
        PluginDescriptor(name=_("AC3 Lip Sync"), description=_("sets the AC3 audio Delay (LipSync)"), where = PluginDescriptor.WHERE_MENU, fnc=mainSetup)]