# for localized messages
from . import _

from AC3utils import AC3, PCM, AC3GLOB, PCMGLOB, AC3PCM, SKIN
from AC3delay import AC3delay
from enigma import ePoint
from HelpableNumberActionMap import HelpableNumberActionMap
from Components.Label import Label,MultiColorLabel
from Components.Pixmap import MultiPixmap
from Components.ProgressBar import ProgressBar
from Components.config import config
from MovableScreen import MovableScreen
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from __init__ import _

class AC3LipSync(Screen, HelpableScreen, MovableScreen):

    def __init__(self, session, plugin_path):
        Screen.__init__(self, session)
        self.onShow.append(self.__onShow)
        self.skin = SKIN
        self.skin_path = plugin_path

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

        # Last saved values
        self.savedValue = {}
        # Current Values
        self.currentValue = {}
        
        #OptionFields
        self["ChannelImg"] = MultiPixmap()
        self["GlobalImg"] = MultiPixmap()
        
        self["ChannelLabel"] = MultiColorLabel(_("Service delay"))
        self["GlobalLabel"] = MultiColorLabel(_("Global delay"))

        # Slider
        self["AudioSliderBar"] = ProgressBar()
        self["AudioSlider"] = Label(_("%i ms")%self.AC3delay.systemDelay[self.AC3delay.whichAudio])
        
        #Service Information
        self["ServiceInfoLabel"] = Label(_("Channel audio:"))
        self["ServiceInfo"] = Label()
        self.setChannelInfoText()

        # Buttons
        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("OK"))
        self["key_blue"] = Label(_("Save to key"))

        # Actions
        self["actions"] = HelpableNumberActionMap(self, "PluginAudioSyncActions",
        {
            "menu":     (self.keyMenu,              _("Open plugin menu")),
            "ok":       (self.keyOk,                _("Save values and close plugin")),
            "cancel":   (self.keyCancel,            _("Discard changes and close plugin")),
            "left":     (self.keyLeft,              _("Change active delay")),
            "right":    (self.keyRight,             _("Change active delay")),
            "up":       (self.keyUp,                _("Increase delay")),
            "down":     (self.keyDown,              _("Decrease delay")),
            "red":      (self.keyCancel,            _("Discard changes and close plugin")),
            "green":    (self.keyOk,                _("Save values and close plugin")),
            "blue":     (self.menuSaveDelayToKey,    _("Save current delay to key")),
            "1":        (self.keyNumberRelative,    _("Decrease delay by %i ms (can be set)")%self.stepSize["1"]),
            "3":        (self.keyNumberRelative,    _("Increase delay by %i ms (can be set)")%self.stepSize["3"]),
            "4":        (self.keyNumberRelative,    _("Decrease delay by %i ms (can be set)")%self.stepSize["4"]),
            "6":        (self.keyNumberRelative,    _("Increase delay by %i ms (can be set)")%self.stepSize["6"]),
            "7":        (self.keyNumberRelative,    _("Decrease delay by %i ms (can be set)")%self.stepSize["7"]),
            "9":        (self.keyNumberRelative,    _("Increase delay by %i ms (can be set)")%self.stepSize["9"]),
            "0":        (self.keyNumberAbsolute,    _("Set delay to %i ms (can be set)")%self.keyStep["0"]),
            "2":        (self.keyNumberAbsolute,    _("Set delay to %i ms (can be set)")%self.keyStep["2"]),
            "5":        (self.keyNumberAbsolute,    _("Set delay to %i ms (can be set)")%self.keyStep["5"]),
            "8":        (self.keyNumberAbsolute,    _("Set delay to %i ms (can be set)")%self.keyStep["8"])
        }, -1)

        HelpableScreen.__init__(self)
        MovableScreen.__init__(self, config.plugins.AC3LipSync, [self["actions"]], 600, 460)
        
    def __onShow(self):
        for sAudio in AC3PCM:
            iDelay = self.AC3delay.getSystemDelay(sAudio)
            self.savedValue[sAudio] = iDelay
            self.currentValue[sAudio] = iDelay

        self["AudioSliderBar"].setRange([(self.lowerBound), (self.upperBound)])
        self.setActiveSlider()
        self.movePosition()

    def keyLeft(self):
        if self.AC3delay.whichAudio == PCMGLOB:
            self.AC3delay.whichAudio = PCM
        elif self.AC3delay.whichAudio == AC3GLOB:
            self.AC3delay.whichAudio = AC3
        
        self.setActiveSlider()

    def keyRight(self):
        if self.AC3delay.whichAudio == AC3:
            self.AC3delay.whichAudio = AC3GLOB
        elif self.AC3delay.whichAudio == PCM:
            self.AC3delay.whichAudio = PCMGLOB

        self.setActiveSlider()

    def setActiveSlider(self):
        # Reset colors of all tabs
        if self.AC3delay.whichAudio in (AC3,PCM):
            self["ChannelImg"].setPixmapNum(1)
            self["GlobalImg"].setPixmapNum(0)
            self["ChannelLabel"].setForegroundColorNum(1)
            self["GlobalLabel"].setForegroundColorNum(0)        
        else:    
            self["ChannelImg"].setPixmapNum(0)
            self["GlobalImg"].setPixmapNum(1)
            self["ChannelLabel"].setForegroundColorNum(0)
            self["GlobalLabel"].setForegroundColorNum(1)
        
        iCurDelay = self.currentValue[self.AC3delay.whichAudio]
        iDelay = iCurDelay - self.lowerBound
        self["AudioSliderBar"].setValue(iDelay)
        self["AudioSlider"].setText(_("%i ms")%iCurDelay)

    def keyDown(self):
        if self.AC3delay.whichAudio == AC3GLOB or self.AC3delay.whichAudio == PCMGLOB:
            iStep = -25
        else:
            iStep = -1 * self.arrowStepSize
        self.changeSliderValue(iStep)
        
    def keyUp(self):
        if self.AC3delay.whichAudio == AC3GLOB or self.AC3delay.whichAudio == PCMGLOB:
            iStep = 25
        else:
            iStep = self.arrowStepSize
        self.changeSliderValue(iStep)

    def keyNumberAbsolute(self, number):
        sAudio = self.AC3delay.whichAudio
        sNumber = str(number)
        if self.AC3delay.whichAudio == AC3GLOB or self.AC3delay.whichAudio == PCMGLOB:
            iStep = (self.keyStep[sNumber] // 25) * 25
        else:
            iStep = self.keyStep[sNumber]        
        iSliderValue = iStep-self.lowerBound
        self.setSliderInfo(iSliderValue)
        self.AC3delay.setSystemDelay(sAudio, self.currentValue[sAudio], True)

    def keyNumberRelative(self, number):
        sNumber = str(number)
        if self.AC3delay.whichAudio == AC3GLOB or self.AC3delay.whichAudio == PCMGLOB:
            iStep = (self.stepSize[sNumber] // 25) * 25
        else:
            iStep = self.stepSize[sNumber]

        self.changeSliderValue(iStep)

    def changeSliderValue(self,iValue):
        sAudio = self.AC3delay.whichAudio
        iSliderValue = int(self["AudioSliderBar"].getValue())
        iSliderValue += iValue
        if iSliderValue < 0:
            iSliderValue = 0
        elif iSliderValue > (self.upperBound - self.lowerBound):
            iSliderValue = (self.upperBound - self.lowerBound)
        self.setSliderInfo(iSliderValue)
        self.AC3delay.setSystemDelay(sAudio, self.currentValue[sAudio], True)        

    def keyOk(self):
        self.close()

    def keyCancel(self):
        for sAudio in AC3PCM:
            iSliderValue = self.currentValue[sAudio]
            if iSliderValue <> self.savedValue[sAudio]:
                self.AC3delay.whichAudio = sAudio
                self.AC3delay.setSystemDelay(sAudio, self.savedValue[sAudio], False)
        self.close()

    def keyMenu(self):
        sAudio = self.AC3delay.whichAudio
        iDelay = self["AudioSliderBar"].getValue()+self.lowerBound
        keyList = [
            (_("Move plugin screen"),"1")
        ]

        self.session.openWithCallback(self.DoShowMenu,ChoiceBox,_("Menu"),keyList)
    
    def DoShowMenu(self, answer):
        if answer is not None:
            if answer[1] == "1":
                self.startMoving()
            else:
                sResponse = _("Invalid selection")
                iType = MessageBox.TYPE_ERROR
                self.session.open(MessageBox, sResponse, iType)
                
    def menuSaveDelayToKey(self):
        sAudio = self.AC3delay.whichAudio
        iDelay = self["AudioSliderBar"].getValue()+self.lowerBound

        AC3SetCustomValue(self.session,iDelay,self.keyStep)
        
    def setSliderInfo(self, iDelay):
        sAudio = self.AC3delay.whichAudio
        self.currentValue[sAudio] = iDelay + self.lowerBound
        iCurDelay = self.currentValue[sAudio]
        self["AudioSliderBar"].setValue(iDelay)
        self["AudioSlider"].setText(_("%i ms")%iCurDelay)

    def setChannelInfoText(self):
        sActiveAudio = str(self.AC3delay.selectedAudioInfo[0])
        sBitstreamDelay = _("%i ms") %self.AC3delay.systemDelay[AC3]
        sPCMDelay = _("%i ms") %self.AC3delay.systemDelay[PCM]

        self["ServiceInfo"].setText(sActiveAudio)
            
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
        elif answer[1] in ("2", "5", "8"):
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
