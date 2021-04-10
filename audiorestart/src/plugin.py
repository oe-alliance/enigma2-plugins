from Components.config import config, ConfigSubsection, ConfigInteger, ConfigSelection, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import NumberActionMap
from Components.Button import Button
from Components.Label import Label,MultiColorLabel
from Components.SystemInfo import SystemInfo
from enigma import eTimer
from Plugins.Plugin import PluginDescriptor
from Screens import Standby
from Screens.Screen import Screen
from __init__ import _
import NavigationInstance

config.plugins.AudioRestart = ConfigSubsection()
config.plugins.AudioRestart.restartSelection = ConfigSelection(default="disabled", choices=[("disabled", _("disabled")), ("restart", _("after restart")), ("standby", _("after standby")), ("both", _("after restart/standby"))])
config.plugins.AudioRestart.restartDelay = ConfigInteger(default=5, limits=(0,30))

PLUGIN_BASE = "AudioRestart"
PLUGIN_VERSION = "0.1"

class AudioRestart():
    def __init__(self):
        self.activateTimer = eTimer()
        self.activateTimer.callback.append(self.restartAudio)
        if config.plugins.AudioRestart.restartSelection.value in ["standby", "both"]:
            config.misc.standbyCounter.addNotifier(self.enterStandby, initial_call=False)
        if config.plugins.AudioRestart.restartSelection.value in ["restart", "both"]:
            self.startTimer()
        
    def enterStandby(self,configElement):
        Standby.inStandby.onClose.append(self.endStandby)
      
    def endStandby(self):
        self.startTimer()

    def startTimer(self):
        self.intDelay = config.plugins.AudioRestart.restartDelay.value * 1000
        print "[AudioSync] audio restart in ",self.intDelay
        self.activateTimer.start(self.intDelay, True)

    def restartAudio(self):
        self.activateTimer.stop()
        if self.audioIsAC3() and SystemInfo["CanDownmixAC3"] and (config.av.downmix_ac3.value == False):
            config.av.downmix_ac3.value = True
            config.av.downmix_ac3.save()
            config.av.downmix_ac3.value = False
            config.av.downmix_ac3.save()
            print "[AudioSync] audio restarted"

    def audioIsAC3(self):
        service = NavigationInstance.instance.getCurrentService()
        audioTracks = service and service.audioTracks()
        blnReturn = False
        if audioTracks is not None:
            n = audioTracks and audioTracks.getNumberOfTracks() or 0
            if n >= 0:
                selectedAudioIndex = audioTracks.getCurrentTrack()
                if selectedAudioIndex <= n:
                    trackInfo = audioTracks.getTrackInfo(selectedAudioIndex)
                    description = trackInfo.getDescription()
                    if (description.find("AC3") != -1 or description.find("AC-3") != -1) or description.find("DTS") != -1:
                        blnReturn = True
        return blnReturn
    
class AudioRestartSetup(ConfigListScreen, Screen):
    skin = """
    <screen position="center,center" size="560,400" title="Audio Restart Setup">
      <ePixmap pixmap="~/img/button-red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
      <ePixmap pixmap="~/img/button-green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
      <ePixmap pixmap="~/img/button-yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
      <ePixmap pixmap="~/img/button-blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
      <widget name="key_red" position="0,0" zPosition="1" size="140,40"
        font="Regular;20" valign="center" halign="center" backgroundColor="#9f1313" transparent="1"
        shadowColor="#000000" shadowOffset="-1,-1" />
      <widget name="key_green" position="140,0" zPosition="1" size="140,40"
        font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1"
        shadowColor="#000000" shadowOffset="-1,-1" />
      <widget name="key_yellow" position="280,0" zPosition="1" size="140,40"
        font="Regular;20" valign="center" halign="center" backgroundColor="#a08500" transparent="1"
        shadowColor="#000000" shadowOffset="-1,-1" />
      <widget name="key_blue" position="420,0" zPosition="1" size="140,40"
        font="Regular;20" valign="center" halign="center" backgroundColor="#18188b" transparent="1"
        shadowColor="#000000" shadowOffset="-1,-1" />
      <widget name="config" position="10,40" size="540,320" scrollbarMode="showOnDemand" />
      <widget name="PluginInfo" position="10,370" size="540,20" zPosition="4" font="Regular;18" foregroundColor="#cccccc" />
    </screen>"""

    def __init__(self, session, plugin_path):
        Screen.__init__(self, session)

        # Lets get a list of elements for the config list
        self.list = [
            getConfigListEntry(_("Restart audio"), config.plugins.AudioRestart.restartSelection),
            getConfigListEntry(_("Restart audio delay (in sec)"), config.plugins.AudioRestart.restartDelay)
        ]
        
        ConfigListScreen.__init__(self, self.list)

        self["config"].list = self.list

        self.skin_path = plugin_path

        # Plugin Information
        self["PluginInfo"] = Label(_("Plugin: %(plugin)s , Version: %(version)s") % dict(plugin=PLUGIN_BASE,version=PLUGIN_VERSION))

        # BUTTONS
        self["key_red"] = Button(_("Cancel"))
        self["key_green"] = Button(_("Save"))
        self["key_yellow"] = Button(_(" "))
        self["key_blue"] = Button(" ")

        self["setupActions"] = NumberActionMap(["SetupActions", "ColorActions"],
        {
            "save": self.save,
            "cancel": self.cancel,
            "green": self.save,
            "red": self.cancel,
            "ok": self.save,
        }, -2)

    def save(self):
        for x in self.list:
            x[1].save()
        self.close()

    def cancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close()

def sessionstart(reason, **kwargs):
    if reason == 0:
        AudioRestart()

def setup(session, **kwargs):
#    reload(AC3setup)
    session.open(AudioRestartSetup, plugin_path)
        
def Plugins(path,**kwargs):
    global plugin_path
    plugin_path = path
    pluginList = [PluginDescriptor(name=_("Audio restart Setup"), description=_("Setup for the AudioRestart Plugin"), icon="AudioRestart.png", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=setup)]
    if config.plugins.AudioRestart.restartSelection.value <> "disabled":
        pluginAutoStart = PluginDescriptor(name="Audio restart", description=_("Restart audio"), where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart)
        pluginList.append(pluginAutoStart)
    return pluginList
