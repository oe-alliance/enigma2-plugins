from Components.config import config, ConfigSubsection, ConfigInteger, ConfigSubList, ConfigBoolean
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from AC3main import AC3LipSync, audioTools
import AC3setup

config.plugins.AC3LipSync = ConfigSubsection()
config.plugins.AC3LipSync.outerBounds = ConfigInteger(default = 1000, limits = (-10000,10000))
config.plugins.AC3LipSync.arrowStepSize = ConfigInteger(default = 5, limits = (-10000,10000))
config.plugins.AC3LipSync.activationDelay = ConfigInteger(default = 800, limits = (-10000,10000))
config.plugins.AC3LipSync.stepSize13 = ConfigInteger(default = 50, limits = (-10000,10000))
config.plugins.AC3LipSync.stepSize46 = ConfigInteger(default = 200, limits = (-10000,10000))
config.plugins.AC3LipSync.stepSize79 = ConfigInteger(default = 500, limits = (-10000,10000))
config.plugins.AC3LipSync.absoluteStep2 = ConfigInteger(default = 0, limits = (-10000,10000))
config.plugins.AC3LipSync.absoluteStep5 = ConfigInteger(default = 0, limits = (-10000,10000))
config.plugins.AC3LipSync.absoluteStep8 = ConfigInteger(default = 0, limits = (-10000,10000))
config.plugins.AC3LipSync.position_x = ConfigInteger(default=0)
config.plugins.AC3LipSync.position_y = ConfigInteger(default=0)
config.plugins.AC3LipSync.restartAudioOnEnigma2Start = ConfigBoolean(default=False)
config.plugins.AC3LipSync.restartAudioDelay = ConfigInteger(default = 5, limits = (0,30))

def main(session, **kwargs):
#    reload(AC3main)
    session.open(AC3LipSync, plugin_path)

def setup(session, **kwargs):
#    reload(AC3setup)
    session.open(AC3setup.AC3LipSyncSetup, plugin_path)

def audioMenu(session, **kwargs):
#    reload(AC3setup)
    session.open(AC3LipSync, plugin_path)

def sessionstart(reason, **kwargs):
    if reason == 0:
        audioTools.audioRestart()
        
def Plugins(path,**kwargs):
    global plugin_path
    plugin_path = path
    pluginList = [ PluginDescriptor(name=_("Audio Sync Setup"), description=_("Setup for the Audio Sync Plugin"), icon = "AudioSync.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=setup),
        PluginDescriptor(name=_("Audio Sync"), description=_("sets the Audio Delay (LipSync)"), where = PluginDescriptor.WHERE_AUDIOMENU, fnc=audioMenu)]
    if config.plugins.AC3LipSync.restartAudioOnEnigma2Start.value:
        pluginAutoStart = PluginDescriptor(name="Audio restart", description = _("Restart audio"), where=PluginDescriptor.WHERE_SESSIONSTART, fnc = sessionstart)
        pluginList.append(pluginAutoStart)
    return pluginList