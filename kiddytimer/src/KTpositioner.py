from Components.ActionMap import ActionMap
from Components.config import config
from Components.Label import Label
from Components.ProgressBar import ProgressBar
from KTMultiPixmap import KTmultiPixmap
from MovableScreen import MovableScreen
from Screens.Screen import Screen
from __init__ import _
import KTglob


class KiddyTimerPositioner(Screen, MovableScreen):
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

        self["actions"] = ActionMap(["OkCancelActions"],
        {
         "ok": self.keyOK,
         "cancel": self.keyCancel
        }, -1)

        MovableScreen.__init__(self, config.plugins.KiddyTimer, [], 82, 82)
        self.startMoving()

    def keyOK(self):
        self.close()

    def keyCancel(self):
        self.close()
