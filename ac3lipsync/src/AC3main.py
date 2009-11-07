from AC3utils import AC3, PCM, AC3PCM
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
        <screen position="center,472" size="600,74" title="AC3 Lip Sync" zPosition="1" >
            <widget name="AudioDelayText" zPosition="2" position="5,0" size="180,21" font="Regular;21" foregroundColors="#ffffff,#ffa323" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/AC3LipSyncBarBG.png" zPosition="2" position="190,0" size="370,21" alphatest="on" transparent="1" />
            <widget name="AudioSlider" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/AC3LipSyncBar.png" zPosition="3" position="190,0" size="370,21" transparent="1" />
            <widget name="AudioSliderText" zPosition="4" position="190,0" size="370,21" font="Regular;18" halign="center" valign="center" transparent="1" />
            <widget name="ServiceInfoText" zPosition="4" position="5,26" size="180,21" font="Regular;18" foregroundColor="#ffffff" />
            <widget name="ServiceInfo" zPosition="4" position="190,26" size="180,21" font="Regular;18" foregroundColor="#cccccc" />
            <widget name="AC3DelayInfoText" zPosition="4" position="380,26" size="48,21" font="Regular;18" foregroundColor="#ffffff" />
            <widget name="AC3DelayInfo" zPosition="4" position="430,26" size="50,21" font="Regular;18" foregroundColor="#cccccc" />
            <widget name="PCMDelayInfoText" zPosition="4" position="490,26" size="48,21" font="Regular;18" foregroundColor="#ffffff" />
            <widget name="PCMDelayInfo" zPosition="4" position="540,26" size="50,21" font="Regular;18" foregroundColor="#cccccc" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/key-red.png" position="5,52" zPosition="5" size="20,20" transparent="1" alphatest="on" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/key-green.png" position="150,52" zPosition="5" size="20,20" transparent="1" alphatest="on" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/key-yellow.png" position="295,52" zPosition="5" size="20,20" transparent="1" alphatest="on" />
            <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/AC3LipSync/img/key-blue.png" position="440,52" zPosition="5" size="20,20" transparent="1" alphatest="on" />
            <widget name="key_red" position="30,52" zPosition="1" size="115,21"
                font="Regular;16" valign="center" halign="left" transparent="1"
                shadowColor="#000000" shadowOffset="-1,-1" />
            <widget name="key_green" position="175,52" zPosition="1" size="115,21"
                font="Regular;16" valign="center" halign="left" transparent="1"
                shadowColor="#000000" shadowOffset="-1,-1" />
            <widget name="key_yellow" position="320,52" zPosition="1" size="115,21"
                font="Regular;16" valign="center" halign="left" transparent="1"
                shadowColor="#000000" shadowOffset="-1,-1" />
            <widget name="key_blue" position="465,52" zPosition="1" size="115,21"
                font="Regular;16" valign="center" halign="left" transparent="1"
            shadowColor="#000000" shadowOffset="-1,-1" />
        </screen>"""

    def __init__(self, session, args = None):
        Screen.__init__(self, session)
        self.onShow.append(self.__onShow)

        #Initialisiere Infobargenerics
        InfoBarAudioSelection.__init__(self)

        # Configuration values
        self.upperBound = int(config.plugins.AC3LipSync.outerBounds.getValue())
        self.lowerBound = -1 * self.upperBound
        self.arrowStepSize = int(config.plugins.AC3LipSync.arrowStepSize.getValue())
        self.stepSize = {}
        self.stepSize["3"] = int(config.plugins.AC3LipSync.stepSize13.getValue())
        self.stepSize["1"] = -1 * self.stepSize["3"]
        self.stepSize["6"] = int(config.plugins.AC3LipSync.stepSize46.getValue())
        self.stepSize["4"] = -1 * self.stepSize["6"]
        self.stepSize["9"] = int(config.plugins.AC3LipSync.stepSize79.getValue())
        self.stepSize["7"] = -1 * self.stepSize["9"]
        self.keyStep = {}
        self.keyStep["0"] = 0
        self.keyStep["2"] = int(config.plugins.AC3LipSync.absoluteStep2.getValue()) 
        self.keyStep["5"] = int(config.plugins.AC3LipSync.absoluteStep5.getValue()) 
        self.keyStep["8"] = int(config.plugins.AC3LipSync.absoluteStep8.getValue()) 

        # AC3delay instance
        self.AC3delay = AC3delay()

        #Screen elements

        #Slider

        for sAudio in AC3PCM:
            self[sAudio+"Slider"] = ProgressBar()
            self[sAudio+"SliderText"] = Label(_("%i ms")%0)
            self[sAudio+"DelayText"] = MultiColorLabel( _("%s delay:")%sAudio)
            self[sAudio+"DelayInfoText"] = Label( _("%s:")%sAudio)
            self[sAudio+"DelayInfo"] = Label(_("%i ms")%0)

        self["AudioSlider"] = ProgressBar()
        self["AudioSliderText"] = Label(_("%i ms")%0)
        self["AudioDelayText"] = MultiColorLabel( _("%s delay:")%self.AC3delay.whichAudio)
        
        #Service Information
        self["ServiceInfoText"] = Label(_("Channel audio:"))
        self["ServiceInfo"] = Label()
        self.setChannelInfoText()

        # Buttons
        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("OK"))
        self["key_yellow"] = Label(_("Switch audio"))
        self["key_blue"] = Label("")

        # Last saved values
        self.savedValue = {}
        self.savedValue[AC3] = 0
        self.savedValue[PCM] = 0

        # Current Values
        self.currentValue = {}
        self.currentValue[AC3] = 0
        self.currentValue[PCM] = 0

        # Actions
        self["actions"] = NumberActionMap(["WizardActions", "NumberActions", "ColorActions", "MenuActions"],
        {
            "menu": self.keyMenu,
            "ok": self.keyOk,
            "back": self.keyCancel,
            "left": self.keyLeft,
            "right": self.keyRight,
            "up": self.keyUp,
            "down": self.keyDown,
            "red": self.keyCancel,
            "green": self.keyOk,
            "yellow": self.keyAudioSelection,
            "1": self.keyNumberRelative,
            "3": self.keyNumberRelative,
            "4": self.keyNumberRelative,
            "6": self.keyNumberRelative,
            "7": self.keyNumberRelative,
            "9": self.keyNumberRelative,
            "0": self.keyNumberAbsolute,
            "2": self.keyNumberAbsolute,
            "5": self.keyNumberAbsolute,
            "8": self.keyNumberAbsolute
        }, -1)

    def __onShow(self):
        for sAudio in AC3PCM:
            iDelay = self.AC3delay.getLamedbDelay(sAudio)
            self[sAudio + "Slider"].setRange([(self.lowerBound), (self.upperBound)])
            self[sAudio + "Slider"].setValue(iDelay-self.lowerBound)
            self[sAudio + "SliderText"].setText(_("%i ms") %iDelay)
            self.savedValue[sAudio] = iDelay
            self.currentValue[sAudio] = iDelay
            if sAudio == self.AC3delay.whichAudio: 
                self["AudioSlider"].setRange([(self.lowerBound), (self.upperBound)])
                self["AudioSlider"].setValue(iDelay-self.lowerBound)
                self["AudioSliderText"].setText(_("%i ms")%iDelay)

    def keyUp(self):
        self.AC3delay.whichAudio = AC3
        self.setActiveSlider(AC3)

    def keyDown(self):
        self.AC3delay.whichAudio = PCM
        self.setActiveSlider(PCM)

    def setActiveSlider(self,sAudio):
        if self.AC3delay.whichAudio == AC3:
            self["AC3DelayText"].setForegroundColorNum(1)
            self["PCMDelayText"].setForegroundColorNum(0)
        else:
            self["AC3DelayText"].setForegroundColorNum(0)
            self["PCMDelayText"].setForegroundColorNum(1)                        
        iDelay = self[sAudio+"Slider"].getValue()
        iCurDelay = iDelay + self.lowerBound
        self["AudioSlider"].setValue(iDelay)
        self["AudioSliderText"].setText(_("%i ms")%iCurDelay)
        self["AudioDelayText"].setText(_("%s delay:")%sAudio)

    def keyLeft(self):
        self.changeSliderValue(-1 * self.arrowStepSize)
        
    def keyRight(self):
        self.changeSliderValue(self.arrowStepSize)

    def keyNumberAbsolute(self, number):
        sAudio = self.AC3delay.whichAudio
        sNumber = str(number)
        iSliderValue = self.keyStep[sNumber]-self.lowerBound
        self.setSliderInfo(iSliderValue)
        self.AC3delay.setLamedbDelay(sAudio, self.currentValue[sAudio], True)

    def keyNumberRelative(self, number):
        sNumber = str(number)
        self.changeSliderValue(self.stepSize[sNumber])

    def changeSliderValue(self,iValue):
        sAudio = self.AC3delay.whichAudio
        iSliderValue = int(self[sAudio+"Slider"].getValue())
        iSliderValue += iValue
        if iSliderValue < 0:
            iSliderValue = 0
        elif iSliderValue > (self.upperBound - self.lowerBound):
            iSliderValue = (self.upperBound - self.lowerBound)
        self.setSliderInfo(iSliderValue)
        self.AC3delay.setLamedbDelay(sAudio, self.currentValue[sAudio], True)        

    def keyAudioSelection(self):
        self.audioSelection()

    def keyOk(self):
        self.close()

    def keyCancel(self):
        for sAudio in AC3PCM:
            iSliderValue = self.currentValue[sAudio]
            if iSliderValue <> self.savedValue[sAudio]:
                self.AC3delay.whichAudio = sAudio
                self.AC3delay.setLamedbDelay(sAudio, self.savedValue[sAudio], False)
        self.close()

    def keyMenu(self):
        sAudio = self.AC3delay.whichAudio
        iDelay = self[sAudio+"Slider"].getValue()+self.lowerBound
        keyList = [
            (_("Save current %(audio)s delay of %(delay)i ms to key") %dict(audio=sAudio , delay=iDelay),"1")
        ]

        self.session.openWithCallback(self.DoShowMenu,ChoiceBox,_("Menu"),keyList)
    
    def DoShowMenu(self, answer):
        if answer is not None:
            if answer[1] == "1":
                self.menuSaveDelayToKey()
            else:
                sResponse = _("Invalid selection")
                iType = MessageBox.TYPE_ERROR
                self.session.open(MessageBox, sResponse , iType)
                
    def menuSaveDelayToKey(self):
        sAudio = self.AC3delay.whichAudio
        iDelay = self[sAudio+"Slider"].getValue()+self.lowerBound

        AC3SetCustomValue(self.session,iDelay,self.keyStep)

    def setSliderInfo(self, iDelay):
        sAudio = self.AC3delay.whichAudio
        self.currentValue[sAudio] = iDelay + self.lowerBound
        iCurDelay = self.currentValue[sAudio]
        self[sAudio+"Slider"].setValue(iDelay)
        self[sAudio+"SliderText"].setText(_("%i ms")%iCurDelay)
        self["AudioSlider"].setValue(iDelay)
        self["AudioSliderText"].setText(_("%i ms")%iCurDelay)

    def setChannelInfoText(self):
        sActiveAudio = str(self.AC3delay.selectedAudioInfo[0])
        sBitstreamDelay = _("%i ms") %self.AC3delay.lamedbDelay[AC3]
        sPCMDelay = _("%i ms") %self.AC3delay.lamedbDelay[PCM]

        self["ServiceInfo"].setText(sActiveAudio)
        self["AC3DelayInfo"].setText(sBitstreamDelay)
        self["PCMDelayInfo"].setText(sPCMDelay)

    def audioSelected(self, audio):
        InfoBarAudioSelection.audioSelected(self, audio)
        if audio is not None:
            self.AC3delay.getAudioInformation()
            self.setChannelInfoText()
            self.setActiveSlider(self.AC3delay.whichAudio)
            
class AC3SetCustomValue:
    def __init__(self, session, iDelay, keyStep):
        self.keyStep = keyStep
        self.session = session
        self.iDelay = iDelay
        self.session.openWithCallback(self.DoSetCustomValue,ChoiceBox,_("Select the key you want to set to %i ms") %(iDelay),self.getKeyList())

    def getKeyList(self):
        keyList = []
        for i,iValue in self.keyStep.iteritems():
            if i != "0":
                keyList.append((_("Key %(key)s (current value: %(value)i ms)") %dict(key=i, value=iValue),i))
        return keyList

    def DoSetCustomValue(self,answer):
        if answer is None:
            self.session.open(MessageBox,_("Setting key canceled"), MessageBox.TYPE_INFO)
        elif answer[1] in ("2" , "5" , "8"):
            if answer[1] == "2":
                config.plugins.AC3LipSync.absoluteStep2.setValue(self.iDelay)
                config.plugins.AC3LipSync.absoluteStep2.save()
            elif  answer[1] == "5":
                config.plugins.AC3LipSync.absoluteStep5.setValue(self.iDelay)
                config.plugins.AC3LipSync.absoluteStep5.save()
            elif  answer[1] == "8":
                config.plugins.AC3LipSync.absoluteStep8.setValue(self.iDelay)
                config.plugins.AC3LipSync.absoluteStep8.save()
            self.keyStep[answer[1]] = self.iDelay
            self.session.open(MessageBox,_("Key %(Key)s successfully set to %(delay)i ms") %dict(Key=answer[1],delay=self.iDelay), MessageBox.TYPE_INFO, 5)
        else:
            self.session.open(MessageBox,_("Invalid selection"), MessageBox.TYPE_ERROR, 5)
