from AC3utils import AC3, PCM, AC3GLOB, PCMGLOB, AC3PCM, SKIN, MOVEPOSITIONSTEP
from HelpableNumberActionMap import HelpableNumberActionMap
from Components.Label import Label,MultiColorLabel
from Components.Pixmap import MultiPixmap
from Components.ProgressBar import ProgressBar
from Components.config import config
from Screens.HelpMenu import HelpableScreen
from Screens.Screen import Screen
from __init__ import _
from enigma import ePoint, eTimer, getDesktop

class AC3Positioner(Screen, HelpableScreen):
    def __init__(self, session, plugin_path):
        Screen.__init__(self, session)
        self.skin = SKIN

        self.skin_path = plugin_path

        self.screenSize_x = 600
        self.screenSize_y = 100
        self.minMargin = 30

        #Delay information
        for sAudio in AC3PCM:
            self[sAudio+"DelayInfoLabel"] = Label( _("%s:")%sAudio)
            self[sAudio+"DelayInfo"] = Label(_("%i ms")%0)

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
        self["AudioSlider"] = Label(_("%i ms")%0)
        self["AudioSliderLabel"] = MultiColorLabel( _("Delay:"))
        
        #Service Information
        self["ServiceInfoLabel"] = Label(_("Channel audio:"))
        self["ServiceInfo"] = Label()

        # Buttons
        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("OK"))
        self["key_yellow"] = Label(_("Switch audio"))
        self["key_blue"] = Label("Save to key")

        self["actions"] = HelpableNumberActionMap(self, "PluginAudioSyncActions",
        {
            "ok":       (self.keyOk,                   _("Save values and close screen")),
            "cancel":   (self.keyCancel,            _("Discard changes and close screen")),
            "left":     (self.keyLeft,              _("Move screen to the left")),
            "right":    (self.keyRight,             _("Move screen to the right")),
            "up":       (self.keyUp,                _("Move screen up")),
            "down":     (self.keyDown,              _("Move screen down")),
            "red":      (self.keyCancel,            _("Discard changes and close screen")),
            "green":    (self.keyOk,                _("Save values and close screen")),
            "1":        (self.keyNumber,            _("Move screen to the upper left corner")),
            "2":        (self.keyNumber,            _("Center screen at the upper border")),
            "3":        (self.keyNumber,            _("Move screen to the upper right corner")),
            "4":        (self.keyNumber,            _("Move screen to the middle of the left border")),
            "5":        (self.keyNumber,            _("Move screen to the center of your TV")),
            "6":        (self.keyNumber,            _("Move screen to the middle of the right border")),
            "7":        (self.keyNumber,            _("Move screen to the lower left corner")),
            "8":        (self.keyNumber,            _("Center screen at the lower border")),
            "9":        (self.keyNumber,            _("Move screen to the lower right corner")),
            "0":        (self.keyNumber,            _("Reset saved position"))
        }, -1)
        
        HelpableScreen.__init__(self)
        
        desktop = getDesktop(0)
        self.desktopWidth = desktop.size().width()
        self.desktopHeight = desktop.size().height()
        
        self.moveTimer = eTimer()
        self.moveTimer.callback.append(self.movePosition)
        self.moveTimer.start(50, 1)

    def movePosition(self):
        if config.plugins.AC3LipSync.position_x.value == 0 and config.plugins.AC3LipSync.position_y.value == 0:
            config.plugins.AC3LipSync.position_x.value = (self.desktopWidth - self.screenSize_x)/2
            config.plugins.AC3LipSync.position_y.value = self.minMargin
        self.instance.move(ePoint(config.plugins.AC3LipSync.position_x.value, config.plugins.AC3LipSync.position_y.value))
            
        self.moveTimer.start(50, 1)

    def keyLeft(self):
        value = config.plugins.AC3LipSync.position_x.value
        value -= MOVEPOSITIONSTEP
        if value < 0:
            value = 0
        config.plugins.AC3LipSync.position_x.value = value

    def keyUp(self):
        value = config.plugins.AC3LipSync.position_y.value
        value -= MOVEPOSITIONSTEP
        if value < 0:
            value = 0
        config.plugins.AC3LipSync.position_y.value = value

    def keyRight(self):
        value = config.plugins.AC3LipSync.position_x.value
        value += MOVEPOSITIONSTEP
        if value > self.desktopWidth:
            value = self.desktopWidth
        config.plugins.AC3LipSync.position_x.value = value

    def keyDown(self):
        value = config.plugins.AC3LipSync.position_y.value
        value += MOVEPOSITIONSTEP
        if value > self.desktopHeight:
            value = self.desktopHeight
        config.plugins.AC3LipSync.position_y.value = value

    def keyNumber(self, number):
        #x- Positioning
        if number in (1,4,7):
            iPosX = self.minMargin
        elif number in (2,5,8,0):
            iPosX = (self.desktopWidth - self.screenSize_x)/2
        else:
            iPosX = self.desktopWidth - self.minMargin - self.screenSize_x
        
        config.plugins.AC3LipSync.position_x.value = iPosX

        #y- positioning
        if number in (0,1,2,3):
            iPosY = self.minMargin
        elif number in (4,5,6):
            iPosY = (self.desktopHeight - self.screenSize_y)/2
        elif number in (7,8,9):    
            iPosY = self.desktopHeight - self.minMargin - self.screenSize_y
            
        config.plugins.AC3LipSync.position_y.value = iPosY
            
    def keyOk(self):
        config.plugins.AC3LipSync.position_x.save()
        config.plugins.AC3LipSync.position_y.save()
        self.close()

    def keyCancel(self):
        config.plugins.AC3LipSync.position_x.cancel()
        config.plugins.AC3LipSync.position_y.cancel()
        self.close()
