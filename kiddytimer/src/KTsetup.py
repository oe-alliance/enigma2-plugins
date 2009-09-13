from Components.ActionMap import ActionMap, NumberActionMap
from Components.Button import Button
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.config import config, getConfigListEntry
from KTpositioner import KiddyTimerPositioner
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
    <screen position="75,90" size="560,380" title="%s Setup">
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
      <widget name="config" position="10,40" size="540,280" scrollbarMode="showOnDemand" />
      <widget name="LastDayStarted" position="10,320" size="540,20" zPosition="4" font="Regular;18" foregroundColor="#cccccc" />
      <widget name="RemainingTime" position="10,340" size="540,20" zPosition="4" font="Regular;18" foregroundColor="#cccccc" />
      <widget name="PluginInfo" position="10,360" size="540,20" zPosition="4" font="Regular;18" foregroundColor="#cccccc" />
    </screen>""") %KTglob.PLUGIN_BASE

    def __init__(self, session):
        self.session = session
        Screen.__init__(self, self.session)
        ProtectedScreen.__init__(self)

        # Lets get a list of elements for the config list
        self.list = [
            getConfigListEntry(_("Enabled"), config.plugins.KiddyTimer.enabled),
            getConfigListEntry(_("PIN"), config.plugins.KiddyTimer.pin),
            getConfigListEntry(_("Don't monitor TV started after"), config.plugins.KiddyTimer.monitorEndTime ), 
            getConfigListEntry(_("Style of timer"), config.plugins.KiddyTimer.timerStyle )
            ]
        for i in range(0,7):
            self.list.append(getConfigListEntry(KTglob.DAYNAMES[i], config.plugins.KiddyTimer.dayTimes[i].timeValue))                

        ConfigListScreen.__init__(self, self.list)

        self["config"].list = self.list

        self.skin_path = KTglob.plugin_path
        self.enabled_old = config.plugins.KiddyTimer.enabled.value

        # Temporarily stop timer as long as we are in the setup screen
        if KTglob.oKiddyTimer.dialog != None:
            KTglob.oKiddyTimer.setDialogStatus(False)

        # Plugin Information
        iRemainingTime = KTglob.oKiddyTimer.remainingTime
        sRemainingTime = KTglob.getTimeFromSeconds(KTglob.oKiddyTimer.remainingTime , True )

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
           
    def keyPositioner(self):
        self.session.open(KiddyTimerPositioner)

    def resetTimer(self):
        KTglob.oKiddyTimer.resetTimer()
        sRemainingTime = KTglob.getTimeFromSeconds(KTglob.oKiddyTimer.remainingTime , True )
        self["RemainingTime"].setText(_("Remaining time: %s") %sRemainingTime)

    def save(self):
        if KTglob.oKiddyTimer.remainingTime > KTglob.getSecondsFromClock( config.plugins.KiddyTimer.dayTimes[KTglob.oKiddyTimer.dayNr].timeValue.getValue()):
            self.resetTimer()
        for x in self["config"].list:
            x[1].save()
        
        KTglob.oKiddyTimer.currentDayTime = KTglob.getSecondsFromClock(config.plugins.KiddyTimer.dayTimes[KTglob.oKiddyTimer.dayNr].timeValue.getValue())
        if config.plugins.KiddyTimer.enabled.value:
            if self.enabled_old != config.plugins.KiddyTimer.enabled.value:
                KTglob.oKiddyTimer.gotSession(KTglob.oKiddyTimer.session)
            else:
                KTglob.oKiddyTimer.setDialogStatus(KTglob.oKiddyTimer.timerHasToRun())
                if KTglob.oKiddyTimer.dialogEnabled == True:
                    KTglob.oKiddyTimer.askForActivation()
        self.close()

    def cancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close()
        KTglob.oKiddyTimer.showHide()

    def protectedWithPin(self):
        return config.plugins.KiddyTimer.pin.getValue()
