from Components.ActionMap import ActionMap, NumberActionMap
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.config import config, configfile, getConfigListEntry
from KTmain import kiddyTimer
from KTMultiPixmap import KTmultiPixmap
from MovableScreen import MovableScreen
from Screens.InputBox import PinInput
from Screens.MessageBox import MessageBox
from Screens.ParentalControlSetup import ProtectedScreen
from Screens.Screen import Screen
from Tools import Notifications
from __init__ import _
import KTglob
import time

class KiddyTimerSetup(ConfigListScreen, Screen, ProtectedScreen):
    skin = ("""
    <screen position="center,center" size="560,440" title="%s Setup">
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
      <widget name="config" position="10,40" size="540,330" scrollbarMode="showOnDemand" />
      <widget name="LastDayStarted" position="10,380" size="540,20" zPosition="4" font="Regular;18" foregroundColor="#cccccc" />
      <widget name="RemainingTime" position="10,400" size="540,20" zPosition="4" font="Regular;18" foregroundColor="#cccccc" />
      <widget name="PluginInfo" position="10,420" size="540,20" zPosition="4" font="Regular;18" foregroundColor="#cccccc" />
    </screen>""") %KTglob.PLUGIN_BASE

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, self.session)
        ProtectedScreen.__init__(self)

        # Lets get a list of elements for the config list
        self.list = [
            getConfigListEntry(_("Enabled"), config.plugins.KiddyTimer.enabled),
            getConfigListEntry(_("PIN"), config.plugins.KiddyTimer.pin),
            getConfigListEntry(_("Don't monitor TV started before"), config.plugins.KiddyTimer.monitorStartTime), 
            getConfigListEntry(_("Don't monitor TV started after"), config.plugins.KiddyTimer.monitorEndTime), 
            getConfigListEntry(_("Style of timer"), config.plugins.KiddyTimer.timerStyle),
            getConfigListEntry(_("Timeout for activation dialog"), config.plugins.KiddyTimer.activationDialogTimeout)
            ]
        for i in range(0,7):
            self.list.append(getConfigListEntry(KTglob.DAYNAMES[i], config.plugins.KiddyTimer.dayTimes[i].timeValue))                

        ConfigListScreen.__init__(self, self.list)

        self["config"].list = self.list

        self.skin_path = KTglob.plugin_path
        self.kiddyTimerStopped = False
        
        # Plugin Information
        self.remainingTime = config.plugins.KiddyTimer.remainingTime.value
        sRemainingTime = KTglob.getTimeFromSeconds(self.remainingTime, True)

        self["PluginInfo"] = Label(_("Plugin: %(plugin)s , Version: %(version)s") %dict(plugin=KTglob.PLUGIN_BASE,version=KTglob.PLUGIN_VERSION))
        self["RemainingTime"] = Label(_("Remaining time: %s") %sRemainingTime)
        self["LastDayStarted"] = Label(_("Last day started: %s") % config.plugins.KiddyTimer.lastStartDay.getValue())
        
        # BUTTONS
        self["key_red"] = Button(_("Cancel"))
        self["key_green"] = Button(_("Save"))
        self["key_yellow"] = Button(_("Reset clock"))
        self["key_blue"] = Button(_("Move clock"))

        self["setupActions"] = NumberActionMap(["SetupActions", "ColorActions"],
        {
            "save": self.save,
            "cancel": self.cancel,
            "green": self.save,
            "red": self.cancel,
            "ok": self.save,
            "blue": self.keyPositioner,
            "yellow": self.resetTimer
        }, -2)

    def pinEntered(self, result):
        if result is None:
            self.cancel()
        elif not result:
            self.session.openWithCallback(self.pinCancel, MessageBox, _("The pin code you entered is wrong."), MessageBox.TYPE_ERROR)
        else:
            self.checkStopTimer()

    def pinCancel(self, result):
        self.cancel()
               
    def keyPositioner(self):
        self.session.open(KiddyTimerPositioner)

    def checkStopTimer(self):
        # Temporarily stop timer as long as we are in the setup screen
        if kiddyTimer.active:
            self.kiddyTimerStopped = True
            kiddyTimer.stopTimer()

    def resetTimer(self):
        self.remainingTime = KTglob.getTodaysTimeInSeconds()
        config.plugins.KiddyTimer.remainingTime.value = int(self.remainingTime)
        config.plugins.KiddyTimer.remainingTime.save()

        sRemainingTime = KTglob.getTimeFromSeconds(self.remainingTime, True)
        self["RemainingTime"].setText(_("Remaining time: %s") %sRemainingTime)

    def save(self):
        if self.remainingTime > KTglob.getTodaysTimeInSeconds():
            self.resetTimer()
        for x in self["config"].list:
            x[1].save()
        configfile.save() 
            
        if config.plugins.KiddyTimer.enabled.value:
            kiddyTimer.startTimer()
        self.close()

    def cancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close()
        if self.kiddyTimerStopped:
            kiddyTimer.startTimer()
        
    def protectedWithPin(self):
        return config.plugins.KiddyTimer.pin.getValue()

class KiddyTimerPositioner(Screen, MovableScreen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.skin = KTglob.SKIN

        self.skin_path = KTglob.plugin_path

        self["TimerGraph"] = KTmultiPixmap()
        self["TimerText"] = Label(_("01:00"))
        self["TimerSlider"] = ProgressBar()
        self["TimerSliderText"] = Label(_("01:00"))
        self["TimerTransparent"] = Pixmap()
        self["TimerTransparentText"] = Label(_("01:00"))
        
        if config.plugins.KiddyTimer.timerStyle.value == "clock":
            self["TimerGraph"].show()
            self["TimerText"].show()
            self["TimerSlider"].hide()    
            self["TimerSliderText"].hide()
            self["TimerTransparent"].hide()
            self["TimerTransparentText"].hide()
        elif config.plugins.KiddyTimer.timerStyle.value == "smiley":
            self["TimerGraph"].hide()
            self["TimerText"].hide()
            self["TimerSlider"].show()
            self["TimerSliderText"].show()
            self["TimerTransparent"].hide()
            self["TimerTransparentText"].hide()
        else:
            self["TimerGraph"].hide()
            self["TimerText"].hide()
            self["TimerSlider"].hide()
            self["TimerSliderText"].hide()
            self["TimerTransparent"].show()
            self["TimerTransparentText"].show()

        self["actions"] = ActionMap(["OkCancelActions"], 
        {
         "ok":      self.keyOK,
         "cancel":  self.keyCancel
        }, -1)

        MovableScreen.__init__(self, config.plugins.KiddyTimer, [], 82, 82)
        self.startMoving()
        
    def keyOK(self):
        self.close()
    
    def keyCancel(self):
        self.close()
