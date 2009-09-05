from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from KTMultiPixmap import KTmultiPixmap
from Components.config import config
from Screens.Screen import Screen
from __init__ import _
from enigma import ePoint, eTimer, getDesktop
import KTglob

class KiddyTimerPositioner(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.skin = KTglob.SKIN

        self.skin_path = KTglob.plugin_path

        self["TimerGraph"] = KTmultiPixmap()
        self["TimerText"] = Label(_("01:00"))
        self["TimerSlider"] = ProgressBar()
        self["TimerSliderText"] = Label(_("01:00"))
        
        if config.plugins.KiddyTimer.timerStyle.value == "clock":
            self["TimerGraph"].show()
            self["TimerText"].show()
            self["TimerSlider"].hide()    
            self["TimerSliderText"].hide()
        else:
            self["TimerGraph"].hide()
            self["TimerText"].hide()
            self["TimerSlider"].show()
            self["TimerSliderText"].show()
        
        self["actions"] = ActionMap(["WizardActions"],
        {
            "left": self.left,
            "up": self.up,
            "right": self.right,
            "down": self.down,
            "ok": self.ok,
            "back": self.exit
        }, -1)
        
        desktop = getDesktop(0)
        self.desktopWidth = desktop.size().width()
        self.desktopHeight = desktop.size().height()
        
        self.moveTimer = eTimer()
        self.moveTimer.callback.append(self.movePosition)
        self.moveTimer.start(50, 1)

    def movePosition(self):
        self.instance.move(ePoint(config.plugins.KiddyTimer.position_x.value, config.plugins.KiddyTimer.position_y.value))
        self.moveTimer.start(50, 1)

    def left(self):
        value = config.plugins.KiddyTimer.position_x.value
        value -= KTglob.MOVEPOSITIONSTEP
        if value < 0:
            value = 0
        config.plugins.KiddyTimer.position_x.value = value

    def up(self):
        value = config.plugins.KiddyTimer.position_y.value
        value -= KTglob.MOVEPOSITIONSTEP
        if value < 0:
            value = 0
        config.plugins.KiddyTimer.position_y.value = value

    def right(self):
        value = config.plugins.KiddyTimer.position_x.value
        value += KTglob.MOVEPOSITIONSTEP
        if value > self.desktopWidth:
            value = self.desktopWidth
        config.plugins.KiddyTimer.position_x.value = value

    def down(self):
        value = config.plugins.KiddyTimer.position_y.value
        value += KTglob.MOVEPOSITIONSTEP
        if value > self.desktopHeight:
            value = self.desktopHeight
        config.plugins.KiddyTimer.position_y.value = value

    def ok(self):
        config.plugins.KiddyTimer.position_x.save()
        config.plugins.KiddyTimer.position_y.save()
        self.close()

    def exit(self):
        config.plugins.KiddyTimer.position_x.cancel()
        config.plugins.KiddyTimer.position_y.cancel()
        self.close()
