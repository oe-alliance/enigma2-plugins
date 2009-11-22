from AC3utils import AC3, PCM, AC3GLOB, PCMGLOB, AC3PCM, SKIN
from AC3delay import AC3delay
from AC3Positioner import AC3Positioner
from enigma import ePoint
from HelpableNumberActionMap import HelpableNumberActionMap
from Components.Label import Label,MultiColorLabel
from Components.Pixmap import MultiPixmap
from Components.ProgressBar import ProgressBar
from Components.config import config
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.InfoBarGenerics import InfoBarAudioSelection
from __init__ import _

class AC3LipSync(Screen, HelpableScreen, InfoBarAudioSelection):

    def __init__(self, session, plugin_path):
        Screen.__init__(self, session)
        self.onShow.append(self.__onShow)
        self.skin = SKIN
        self.skin_path = plugin_path

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

        # Last saved values
        self.savedValue = {}
        # Current Values
        self.currentValue = {}
        
        #Delay information
        for sAudio in AC3PCM:
            self[sAudio+"DelayInfoLabel"] = Label( _("%s:")%sAudio)
            self[sAudio+"DelayInfo"] = Label(_("%i ms")%self.AC3delay.systemDelay[sAudio])

        #Tabbed table labels
        self["AC3TableTab"] = MultiPixmap()
        self["AC3GLOBTableTab"] = MultiPixmap()
        self["PCMTableTab"] = MultiPixmap()
        self["PCMGLOBTableTab"] = MultiPixmap()
        
        self["AC3TableTabLabel"] = MultiColorLabel( _("Passthrough"))
        self["AC3GLOBTableTabLabel"] = MultiColorLabel( _("Global Passthr."))
        self["PCMTableTabLabel"] = MultiColorLabel( _("PCM"))
        self["PCMGLOBTableTabLabel"] = MultiColorLabel( _("Global PCM"))

        # Slider
        self["AudioSliderBar"] = ProgressBar()
        self["AudioSlider"] = Label(_("%i ms")%self.AC3delay.systemDelay[self.AC3delay.whichAudio])
        self["AudioSliderLabel"] = Label( _("Delay:"))
        
        #Service Information
        self["ServiceInfoLabel"] = Label(_("Channel audio:"))
        self["ServiceInfo"] = Label()
        self.setChannelInfoText()

        # Buttons
        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("OK"))
        self["key_yellow"] = Label(_("Switch audio"))
        self["key_blue"] = Label("Save to key")

        # Actions
        self["actions"] = HelpableNumberActionMap(self, "PluginAudioSyncActions",
        {
            "menu":     (self.keyMenu,              _("Open plugin menu")),
            "ok":       (self.keyOk,                _("Save values and close plugin")),
            "cancel":   (self.keyCancel,            _("Discard changes and close plugin")),
            "left":     (self.keyLeft,              _("Decrease delay")),
            "right":    (self.keyRight,             _("Increase delay")),
            "up":       (self.keyUp,                _("Change active delay")),
            "down":     (self.keyDown,              _("Change active delay")),
            "red":      (self.keyCancel,            _("Discard changes and close plugin")),
            "green":    (self.keyOk,                _("Save values and close plugin")),
            "yellow":   (self.keyAudioSelection,    _("Select channel audio")),
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
        
    def __onShow(self):
        for sAudio in AC3PCM:
            iDelay = self.AC3delay.getSystemDelay(sAudio)
            self.savedValue[sAudio] = iDelay
            self.currentValue[sAudio] = iDelay
            if sAudio == self.AC3delay.whichAudio: 
                self["AudioSliderBar"].setRange([(self.lowerBound), (self.upperBound)])
                self["AudioSliderBar"].setValue(iDelay-self.lowerBound)
                self["AudioSlider"].setText(_("%i ms")%iDelay)
                iNum = 1
            else:
                iNum = 0
            self[ sAudio + "TableTabLabel"].setForegroundColorNum(iNum)
            self[ sAudio + "TableTab"].setPixmapNum(iNum)
            
        self.movePosition()

    def movePosition(self):
        if config.plugins.AC3LipSync.position_x.value != 0 or config.plugins.AC3LipSync.position_y.value != 0:
            self.instance.move(ePoint(config.plugins.AC3LipSync.position_x.value, config.plugins.AC3LipSync.position_y.value))


    def keyUp(self):
        if self.AC3delay.whichAudio == PCMGLOB:
            self.AC3delay.whichAudio = PCM
        elif self.AC3delay.whichAudio == PCM:
            self.AC3delay.whichAudio = AC3GLOB
        elif self.AC3delay.whichAudio == AC3GLOB:
            self.AC3delay.whichAudio = AC3
        else:
            self.AC3delay.whichAudio = PCMGLOB
        
        self.setActiveSlider()

    def keyDown(self):
        if self.AC3delay.whichAudio == AC3:
            self.AC3delay.whichAudio = AC3GLOB
        elif self.AC3delay.whichAudio == AC3GLOB:
            self.AC3delay.whichAudio = PCM
        elif self.AC3delay.whichAudio == PCM:
            self.AC3delay.whichAudio = PCMGLOB
        else:
            self.AC3delay.whichAudio = AC3

        self.setActiveSlider()

    def setActiveSlider(self):
        # Reset colors of all tabs
        for sAudio in AC3PCM:
            if sAudio == self.AC3delay.whichAudio:
                iNum = 1
            else: 
                iNum = 0
            self[ sAudio + "TableTabLabel"].setForegroundColorNum(iNum)
            self[ sAudio + "TableTab"].setPixmapNum(iNum)
        iCurDelay = self.currentValue[self.AC3delay.whichAudio]
        iDelay = iCurDelay - self.lowerBound
        self["AudioSliderBar"].setValue(iDelay)
        self["AudioSlider"].setText(_("%i ms")%iCurDelay)

    def keyLeft(self):
        if self.AC3delay.whichAudio == AC3GLOB or self.AC3delay.whichAudio == PCMGLOB:
            iStep = -25
        else:
            iStep = -1 * self.arrowStepSize
        self.changeSliderValue(iStep)
        
    def keyRight(self):
        if self.AC3delay.whichAudio == AC3GLOB or self.AC3delay.whichAudio == PCMGLOB:
            iStep = 25
        else:
            iStep = self.arrowStepSize
        self.changeSliderValue(iStep)

    def keyNumberAbsolute(self, number):
        sAudio = self.AC3delay.whichAudio
        sNumber = str(number)
        if self.AC3delay.whichAudio == AC3GLOB or self.AC3delay.whichAudio == PCMGLOB:
            iStep = ( self.keyStep[sNumber] // 25 ) * 25
        else:
            iStep = self.keyStep[sNumber]        
        iSliderValue = iStep-self.lowerBound
        self.setSliderInfo(iSliderValue)
        self.AC3delay.setSystemDelay(sAudio, self.currentValue[sAudio], True)

    def keyNumberRelative(self, number):
        sNumber = str(number)
        if self.AC3delay.whichAudio == AC3GLOB or self.AC3delay.whichAudio == PCMGLOB:
            iStep = ( self.stepSize[sNumber] // 25 ) * 25
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

    def keyAudioSelection(self):
        self.audioSelection()

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
                self.session.openWithCallback(self.positionerCallback,AC3Positioner,self.skin_path)    
            else:
                sResponse = _("Invalid selection")
                iType = MessageBox.TYPE_ERROR
                self.session.open(MessageBox, sResponse , iType)
                
    def menuSaveDelayToKey(self):
        sAudio = self.AC3delay.whichAudio
        iDelay = self["AudioSliderBar"].getValue()+self.lowerBound

        AC3SetCustomValue(self.session,iDelay,self.keyStep)
    
    def positionerCallback(self):
        self.movePosition()
    
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
        self["AC3DelayInfo"].setText(sBitstreamDelay)
        self["PCMDelayInfo"].setText(sPCMDelay)

    def audioSelected(self, audio):
        InfoBarAudioSelection.audioSelected(self, audio)
        if audio is not None:
            self.AC3delay.getAudioInformation()
            self.setChannelInfoText()
            self.setActiveSlider()
            
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
