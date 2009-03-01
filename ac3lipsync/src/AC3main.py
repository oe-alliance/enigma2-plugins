from AC3utils import AC3, PCM, AC3PCM, lFileDelay, dec2hex, hex2dec
from AC3delay import AC3delay
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.Label import Label,MultiColorLabel
from Components.ProgressBar import ProgressBar
from Components.config import config
from enigma import eDVBDB
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.InfoBarGenerics import InfoBarAudioSelection
from ServiceReference import ServiceReference
from __init__ import _
import os

class AC3LipSync(Screen,InfoBarAudioSelection):
    skin = """
        <screen position="60,420" size="600,100" title="AC3 Lip Sync" zPosition="1" >
            <widget name="AC3DelayText" zPosition="2" position="5,0" size="180,21" font="Regular;21" foregroundColors="#ffffff,#ffa323" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/AC3LipSyncBarBG.png" zPosition="2" position="190,0" size="370,21" alphatest="on" transparent="1" />
            <widget name="AC3Slider" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/AC3LipSyncBar.png" zPosition="3" position="190,0" size="370,21" transparent="1" />
            <widget name="AC3SliderText" zPosition="4" position="190,0" size="370,21" font="Regular;18" halign="center" valign="center" transparent="1" />
            <widget name="PCMDelayText" zPosition="2" position="5,26" size="180,21" font="Regular;21" foregroundColors="#ffffff,#ffa323" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/AC3LipSyncBarBG.png" zPosition="2" position="190,26" size="370,21" alphatest="on" transparent="1" />
            <widget name="PCMSlider" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/AC3LipSyncBar.png" zPosition="3" position="190,26" size="370,21" transparent="1" />
            <widget name="PCMSliderText" zPosition="4" position="190,26" size="370,21" font="Regular;18" halign="center" valign="center" transparent="1" />
            <widget name="ServiceInfoText" zPosition="4" position="5,52" size="180,21" font="Regular;21" foregroundColor="#ffffff" />
            <widget name="ServiceInfo" zPosition="4" position="190,52" size="180,21" font="Regular;21" foregroundColor="#cccccc" />
            <widget name="AC3DelayInfoText" zPosition="4" position="380,52" size="40,21" font="Regular;21" foregroundColor="#ffffff" />
            <widget name="AC3DelayInfo" zPosition="4" position="430,52" size="50,21" font="Regular;21" foregroundColor="#cccccc" />
            <widget name="PCMDelayInfoText" zPosition="4" position="490,52" size="40,21" font="Regular;21" foregroundColor="#ffffff" />
            <widget name="PCMDelayInfo" zPosition="4" position="540,52" size="50,21" font="Regular;21" foregroundColor="#cccccc" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/key-red.png" position="5,78" zPosition="5" size="20,20" transparent="1" alphatest="on" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/key-green.png" position="150,78" zPosition="5" size="20,20" transparent="1" alphatest="on" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/key-yellow.png" position="295,78" zPosition="5" size="20,20" transparent="1" alphatest="on" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/key-blue.png" position="440,78" zPosition="5" size="20,20" transparent="1" alphatest="on" />
            <widget name="key_red" position="30,78" zPosition="1" size="115,21"
                font="Regular;16" valign="center" halign="left" transparent="1"
                shadowColor="#000000" shadowOffset="-1,-1" />
            <widget name="key_green" position="175,78" zPosition="1" size="115,21"
                font="Regular;16" valign="center" halign="left" transparent="1"
                shadowColor="#000000" shadowOffset="-1,-1" />
            <widget name="key_yellow" position="320,78" zPosition="1" size="115,21"
                font="Regular;16" valign="center" halign="left" transparent="1"
                shadowColor="#000000" shadowOffset="-1,-1" />
            <widget name="key_blue" position="465,78" zPosition="1" size="115,21"
                font="Regular;16" valign="center" halign="left" transparent="1"
            shadowColor="#000000" shadowOffset="-1,-1" />
        </screen>"""

    def __init__(self, session, args = None):
        Screen.__init__(self, session)
        self.onShow.append(self.__onShow)

        #Initialisiere Infobargenerics
        InfoBarAudioSelection.__init__(self)

        # Configuration values
        self.lowerBound = int(config.plugins.AC3LipSync.lowerBound.getValue())
        self.upperBound = int(config.plugins.AC3LipSync.upperBound.getValue())
        self.arrowStepSize = int(config.plugins.AC3LipSync.arrowStepSize.getValue())
        self.stepSize = int(config.plugins.AC3LipSync.stepSize.getValue())

        # AC3delay instance
        self.AC3delay = AC3delay(self.session)

        #Which Values do the number keys use
        self.whichKeys = "Computed" # Computed = computed Values of keys, User = User set values of keys
        self.whichKeyText = {}
        self.whichKeyText["Computed"] = _("Use user delays")
        self.whichKeyText["User"] = _("Use calc. delays")

        #Screen elements

        #Slider

        for sAudio in AC3PCM:
            self[sAudio+"Slider"] = ProgressBar()
            self[sAudio+"SliderText"] = Label(_("%i ms")%0)
            self[sAudio+"DelayText"] = MultiColorLabel( _("%s delay:")%sAudio)
            self[sAudio+"DelayInfoText"] = Label( _("%s:")%sAudio)
            self[sAudio+"DelayInfo"] = Label(_("%i ms")%0)

        #Service Information
        self["ServiceInfoText"] = Label(_("Channel audio:"))
        self["ServiceInfo"] = Label()
        self.setChannelInfoText()

        # Buttons
        if self.AC3delay.bIsRecording == True:
            self["key_red"] = Label(_(" "))
        else:
            self["key_red"] = Label(_("Save"))
        self["key_green"] = Label(_("Switch audio"))
        self["key_yellow"] = Label(_("Set user delay"))
        self["key_blue"] = Label(self.whichKeyText[self.whichKeys])

        # Last saved values
        self.savedValue = {}
        self.savedValue[AC3] = 0
        self.savedValue[PCM] = 0

        # Current Values
        self.currentValue = {}
        self.currentValue[AC3] = 0
        self.currentValue[PCM] = 0

        # Actions
        self["actions"] = NumberActionMap(["WizardActions", "NumberActions", "ColorActions"],
        {
            "ok": self.keyOk,
            "back": self.keyCancel,
            "left": self.keyLeft,
            "right": self.keyRight,
            "up": self.keyUp,
            "down": self.keyDown,
            "red": self.keySaveToLamedb,
            "green": self.keyAudioSelection,
            "yellow": self.keySaveDelayToKey,
            "blue": self.keySwitchKeyValues,
            "1": self.keyNumberGlobal,
            "2": self.keyNumberGlobal,
            "3": self.keyNumberGlobal,
            "4": self.keyNumberGlobal,
            "5": self.keyNumberGlobal,
            "6": self.keyNumberGlobal,
            "7": self.keyNumberGlobal,
            "8": self.keyNumberGlobal,
            "9": self.keyNumberGlobal,
            "0": self.keyNumberGlobal
        }, -1)

    def __onShow(self):
        for sAudio in lFileDelay.keys():
            iDelay = self.AC3delay.getFileDelay(sAudio)
            self[sAudio + "Slider"].setRange([(self.lowerBound), (self.upperBound)])
            self[sAudio + "Slider"].setValue(iDelay-self.lowerBound)
            self[sAudio + "SliderText"].setText(_("%i ms") %iDelay)
            self.savedValue[sAudio] = iDelay
            self.currentValue[sAudio] = iDelay
            if self.AC3delay.whichAudio == AC3:
                self["AC3DelayText"].setForegroundColorNum(1)
                self["PCMDelayText"].setForegroundColorNum(0)
            else:
                self["AC3DelayText"].setForegroundColorNum(0)
                self["PCMDelayText"].setForegroundColorNum(1)

    def keyUp(self):
        self.AC3delay.whichAudio = AC3
        self["AC3DelayText"].setForegroundColorNum(1)
        self["PCMDelayText"].setForegroundColorNum(0)

    def keyDown(self):
        self.AC3delay.whichAudio = PCM
        self["AC3DelayText"].setForegroundColorNum(0)
        self["PCMDelayText"].setForegroundColorNum(1)

    def keyLeft(self):
        sAudio = self.AC3delay.whichAudio
        iSliderValue = int(self[sAudio+"Slider"].getValue())
        iSliderValue -= self.arrowStepSize
        if iSliderValue < 0:
            iSliderValue = 0
        self.setSliderInfo(iSliderValue)
        self.AC3delay.setFileDelay(sAudio, self.currentValue[sAudio])

    def keyRight(self):
        sAudio = self.AC3delay.whichAudio
        iSliderValue = int(self[sAudio+"Slider"].getValue())
        if self.currentValue[sAudio] == 0:
            iSliderValue = 0
        iSliderValue += self.arrowStepSize
        if iSliderValue > self.upperBound:
            iSliderValue = self.upperBound
        self.setSliderInfo(iSliderValue)
        self.AC3delay.setFileDelay(sAudio, self.currentValue[sAudio])

    def keyNumberGlobal(self, number):
        sAudio = self.AC3delay.whichAudio
        iNumber = int(number)
        if iNumber == 0:
            iSliderValue = 0
            self.currentValue[sAudio] = 0
        else:
            if self.whichKeys == "Computed":
                iSliderValue = self.stepSize*iNumber
            else:
                iSliderValue = int(config.plugins.AC3LipSync.keySteps[iNumber].stepSize.getValue())-self.lowerBound
                if iSliderValue < 0:
                    iSliderValue = 0
        self.setSliderInfo(iSliderValue)
        self.AC3delay.setFileDelay(sAudio, self.currentValue[sAudio])

    def keyAudioSelection(self):
        self.audioSelection()

    def keyOk(self):
        self.close()

    def keyCancel(self):
        for sAudio in lFileDelay.keys():
            iSliderValue = self.currentValue[sAudio]
            if iSliderValue <> self.savedValue[sAudio]:
                self.whichAudio = sAudio
                self.AC3delay.setFileDelay(sAudio, self.savedValue[sAudio])
        self.close()

    def keySaveToLamedb(self):
        if self.AC3delay.bIsRecording == False:
            keyList = [
                (_("Save %s delay")%AC3,"1"),
                (_("Save %s delay")%PCM,"2"),
                (_("Save both delays"),"3")
            ]

            self.session.openWithCallback(self.DoSaveLamedb,ChoiceBox,_("Which delays do you want to set"),keyList)

    def DoSaveLamedb(self, answer):
        sNewLine = ""
        sResponse = ""
        bOk = True
        iType = MessageBox.TYPE_INFO
        aSetAudio = []
        if answer is not None:
            if answer[1] in ("1","2","3"):
                bSetAC3 = False
                bSetPCM = False
                self.AC3delay.initAudio()
                if self.AC3delay.iAudioDelay is not None:
                    if answer[1] in ("1","3"):
                        iDelay = int( self.AC3delay.getLamedbDelay(AC3) )
                        aSetAudio.append((AC3,iDelay))
                        bSetAC3 = True
                    if answer[1] in ("2","3"):
                        iDelay = int( self.AC3delay.getLamedbDelay(PCM) )
                        aSetAudio.append((PCM,iDelay))
                        bSetPCM = True
                    for vAudio in aSetAudio:
                        sAudio = vAudio[0]
                        iChannelDelay = int(vAudio[1])
                        iCurDelay = self.currentValue[sAudio]
                        iNewDelay = iCurDelay
                        if sAudio == AC3:
                            self.AC3delay.iAudioDelay.setAC3Delay(iNewDelay)
                        else:
                            self.AC3delay.iAudioDelay.setPCMDelay(iNewDelay)
                        self.AC3delay.lamedbDelay[sAudio] = iNewDelay
                        sResponse = sResponse + sNewLine + _("Saved %(audio)s value: %(delay)i ms") %dict(audio=sAudio,delay=iNewDelay)
                        sNewLine = "\n"
                self.AC3delay.deleteAudio()
            else:
                sResponse = _("Invalid selection")
                iType = MessageBox.TYPE_ERROR
            if bOk == True:
                self.session.open(MessageBox, sResponse , iType)
        self.setChannelInfoText()

    def setSliderInfo(self, iDelay):
        sAudio = self.AC3delay.whichAudio
        if iDelay == 0:
            if self.currentValue[sAudio] >= self.lowerBound:
                self.currentValue[sAudio] = self.lowerBound
            else:
                self.currentValue = 0
        else:
            self.currentValue[sAudio] = iDelay + self.lowerBound
        self[sAudio+"Slider"].setValue(iDelay)
        self[sAudio+"SliderText"].setText(_("%i ms")%self.currentValue[sAudio])

    def setChannelInfoText(self):
        sActiveAudio = str(self.AC3delay.selectedAudioInfo[0])
        sBitstreamDelay = _("%i ms") %self.AC3delay.lamedbDelay[AC3]
        sPCMDelay = ("%i ms") %self.AC3delay.lamedbDelay[PCM]

        self["ServiceInfo"].setText(sActiveAudio)
        self["AC3DelayInfo"].setText(sBitstreamDelay)
        self["PCMDelayInfo"].setText(sPCMDelay)

    def keySwitchKeyValues(self):
        if self.whichKeys == "Computed":
            self.whichKeys = "User"
        else:
            self.whichKeys = "Computed"
        self["key_blue"].setText(self.whichKeyText[self.whichKeys])

    def keySaveDelayToKey(self):
        sAudio = self.AC3delay.whichAudio
        iDelay = self[sAudio+"Slider"].getValue()+self.lowerBound
        AC3SetCustomValue(self.session,iDelay)

    def audioSelected(self, audio):
        InfoBarAudioSelection.audioSelected(self, audio)
        if audio is not None:
            self.AC3delay.getAudioInformation()
            self.setChannelInfoText()

class AC3SetCustomValue:
    def __init__(self, session, iDelay):
        self.session = session
        self.iDelay = iDelay
        self.session.openWithCallback(self.DoSetCustomValue,ChoiceBox,_("Select the key you want to set"),self.getKeyList())

    def getKeyList(self):
        keyList = []
        for i in range(1, 10):
            keyList.append((_("Key")+" "+str(i),str(i)))
        return keyList

    def DoSetCustomValue(self,answer):
        if answer is None:
            self.session.open(MessageBox,_("Setting key canceled"), MessageBox.TYPE_INFO)
        else:
            config.plugins.AC3LipSync.keySteps[int(answer[1])].stepSize.setValue(self.iDelay)
            config.plugins.AC3LipSync.keySteps.save()
            self.session.open(MessageBox,_("%(Key)s successfully set to %(delay)i ms") %dict(Key=answer[0],delay=self.iDelay), MessageBox.TYPE_INFO, 5)

