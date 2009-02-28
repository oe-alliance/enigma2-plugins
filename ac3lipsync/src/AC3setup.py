from AC3main import AC3LipSync
from AC3utils import dec2hex, hex2dec
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.Label import Label,MultiColorLabel
from Components.ProgressBar import ProgressBar
from Components.config import config, getConfigListEntry
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from __init__ import _
import os

class AC3LipSyncSetup(ConfigListScreen, Screen):
    skin = """
    <screen position="75,90" size="560,400" title="AC3 Lip Sync Setup">
      <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/button-red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
      <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/button-green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
      <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/button-yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
      <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/button-blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
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
    </screen>"""

    def __init__(self, session, args = None):
        Screen.__init__(self, session)
                
        # nun erzeugen wir eine liste von elementen fuer die menu liste.
        self.list = [ ]
        self.list.append(getConfigListEntry(_("Minimum delay"), config.plugins.AC3LipSync.lowerBound))
        self.list.append(getConfigListEntry(_("Maximum delay"), config.plugins.AC3LipSync.upperBound))
        self.list.append(getConfigListEntry(_("Step in ms for arrow keys"), config.plugins.AC3LipSync.arrowStepSize))
        for i in range(1 , 10):
            self.list.append(getConfigListEntry(_("Step in ms for key %i" %i), config.plugins.AC3LipSync.keySteps[i].stepSize))
            
        ConfigListScreen.__init__(self, self.list)

        self["config"].list = self.list

        # DO NOT ASK.
        self["key_red"] = Button(_("Cancel"))
        self["key_green"] = Button(_("Save"))
        self["key_yellow"] = Button(_("Recalculate..."))
        self["key_blue"] = Button(_(" "))        

        self["setupActions"] = NumberActionMap(["SetupActions", "ColorActions"],
        {
            "save": self.save,
            "cancel": self.cancel,
            "green": self.save,
            "red": self.cancel,
            "yellow": self.recalculateKeys,
            "ok": self.save,
        }, -2)

    def recalculateKeys(self):
        iLowerBound = int(config.plugins.AC3LipSync.lowerBound.getValue())
        iUpperBound = int(config.plugins.AC3LipSync.upperBound.getValue())
        iStepSize = (iUpperBound - iLowerBound)/9
        for i in range(1 , 10):
            config.plugins.AC3LipSync.keySteps[i].stepSize.setValue(i*iStepSize)
        self["config"].setList(self.list)
        
    def save(self):
        iLowerBound = int(config.plugins.AC3LipSync.lowerBound.getValue())
        iUpperBound = int(config.plugins.AC3LipSync.upperBound.getValue())
        iStepSize = (iUpperBound - iLowerBound)/9
        config.plugins.AC3LipSync.stepSize.setValue(iStepSize)
        config.plugins.AC3LipSync.stepSize.save()
        iUpperBound = iLowerBound + (iStepSize*9)
        config.plugins.AC3LipSync.upperBound.setValue(iUpperBound)
        for x in self.list:
            x[1].save()
        self.close()

    def cancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close()

    def startPlugin(self):
        self.save
        AC3LipSync(self.session)
        self.close()