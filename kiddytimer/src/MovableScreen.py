from __future__ import absolute_import
from .HelpableNumberActionMap import HelpableNumberActionMap
from Components.config import config
from .__init__ import _
from enigma import ePoint, eTimer, getDesktop

class MovableScreen():
    def __init__(self, configRoot, disableKeymaps, screenSize_x, screenSize_y, moveMinMargin=30, moveStepSize=10):
        self.configRoot = configRoot
        self.disableKeymaps = disableKeymaps
        self.screenSize_x = screenSize_x
        self.screenSize_y = screenSize_y
        self.moveMinMargin = moveMinMargin
        self.moveStepSize = moveStepSize

        self["MovableScreenActions"] = HelpableNumberActionMap(self, "MovableScreenActions",
        {
            "ok":       (self.moveKeyOk,                   _("Save values and close screen")),
            "cancel":   (self.moveKeyCancel,            _("Discard changes and close screen")),
            "left":     (self.moveKeyLeft,              _("Move screen to the left")),
            "right":    (self.moveKeyRight,             _("Move screen to the right")),
            "up":       (self.moveKeyUp,                _("Move screen up")),
            "down":     (self.moveKeyDown,              _("Move screen down")),
            "red":      (self.moveKeyCancel,            _("Discard changes and close screen")),
            "green":    (self.moveKeyOk,                _("Save values and close screen")),
            "1":        (self.moveKeyNumber,            _("Move screen to the upper left corner")),
            "2":        (self.moveKeyNumber,            _("Center screen at the upper border")),
            "3":        (self.moveKeyNumber,            _("Move screen to the upper right corner")),
            "4":        (self.moveKeyNumber,            _("Move screen to the middle of the left border")),
            "5":        (self.moveKeyNumber,            _("Move screen to the center of your TV")),
            "6":        (self.moveKeyNumber,            _("Move screen to the middle of the right border")),
            "7":        (self.moveKeyNumber,            _("Move screen to the lower left corner")),
            "8":        (self.moveKeyNumber,            _("Center screen at the lower border")),
            "9":        (self.moveKeyNumber,            _("Move screen to the lower right corner")),
            "0":        (self.moveKeyNumber,            _("Reset saved position"))
        }, -1)
             
        self["MovableScreenActions"].setEnabled(False)
      
        desktop = getDesktop(0)
        self.desktopWidth = desktop.size().width()
        self.desktopHeight = desktop.size().height()
        

    def startMoving(self):
        self.setEnableMoveKeymap(True)

        self.moveTimer = eTimer()
        self.moveTimer.callback.append(self.movePositionTimer)
        self.moveTimer.start(50, 1)

    def movePositionTimer(self):
        if self.configRoot.position_x.value == 0 and self.configRoot.position_y.value == 0:
            self.configRoot.position_x.value = (self.desktopWidth - self.screenSize_x)/2
            self.configRoot.position_y.value = self.moveMinMargin
        self.instance.move(ePoint(self.configRoot.position_x.value, self.configRoot.position_y.value))
            
        self.moveTimer.start(50, 1)

    def movePosition(self):
        if self.configRoot.position_x.value != 0 or self.configRoot.position_y.value != 0:
            self.instance.move(ePoint(self.configRoot.position_x.value, self.configRoot.position_y.value))
            
    def moveKeyLeft(self):
        value = self.configRoot.position_x.value
        value -= self.moveStepSize
        if value < 0:
            value = 0
        self.configRoot.position_x.value = value

    def moveKeyUp(self):
        value = self.configRoot.position_y.value
        value -= self.moveStepSize
        if value < 0:
            value = 0
        self.configRoot.position_y.value = value

    def moveKeyRight(self):
        value = self.configRoot.position_x.value
        value += self.moveStepSize
        if value > self.desktopWidth:
            value = self.desktopWidth
        self.configRoot.position_x.value = value

    def moveKeyDown(self):
        value = self.configRoot.position_y.value
        value += self.moveStepSize
        if value > self.desktopHeight:
            value = self.desktopHeight
        self.configRoot.position_y.value = value

    def moveKeyNumber(self, number):
        #x- Positioning
        if number in (1, 4, 7):
            iPosX = self.moveMinMargin
        elif number in (2, 5, 8, 0):
            iPosX = (self.desktopWidth - self.screenSize_x)/2
        else:
            iPosX = self.desktopWidth - self.moveMinMargin - self.screenSize_x
        
        self.configRoot.position_x.value = iPosX

        #y- positioning
        if number in (0, 1, 2, 3):
            iPosY = self.moveMinMargin
        elif number in (4, 5, 6):
            iPosY = (self.desktopHeight - self.screenSize_y)/2
        elif number in (7, 8, 9):    
            iPosY = self.desktopHeight - self.moveMinMargin - self.screenSize_y
            
        self.configRoot.position_y.value = iPosY
            
    def moveKeyOk(self):
        self.configRoot.position_x.save()
        self.configRoot.position_y.save()
        self.setEnableMoveKeymap(False)

    def moveKeyCancel(self):
        self.configRoot.position_x.cancel()
        self.configRoot.position_y.cancel()
        self.setEnableMoveKeymap(False)

    def setEnableMoveKeymap(self, enabled):
        self["MovableScreenActions"].setEnabled(enabled)
        for keymap in self.disableKeymaps:
            keymap.setEnabled(not(enabled))
