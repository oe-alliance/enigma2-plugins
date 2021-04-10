from Components.Label import Label
from Components.ProgressBar import ProgressBar
from KTMultiPixmap import KTmultiPixmap
from Components.config import config, configfile
from Components.Pixmap import Pixmap
from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import PinInput
from Screens.MessageBox import MessageBox
from Screens.MinuteInput import MinuteInput
from Screens.Screen import Screen
from Screens import Standby
from Tools.BoundFunction import boundFunction
from Tools import Notifications
from Tools.Directories import resolveFilename, SCOPE_CONFIG
from enigma import ePoint, eTimer, eDVBLocalTimeHandler

from __init__ import _
import KTglob
import NavigationInstance
import time

PARAM_NONE = -1
PARAM_STOPTIMER = 1
PARAM_STARTTIMER = 2
PARAM_DISABLETIMER = 3
PARAM_ENABLETIMER = 4
PARAM_INCREASETIMER = 5
PARAM_DECREASETIMER = 6
PARAM_SETTIMER = 7
PARAM_ENABLETIMERONCE = 8
PARAM_RESETTIMER = 9

class KiddyTimerScreen(Screen):    

    def __init__(self, session):
        Screen.__init__(self, session)
        self.skin = KTglob.SKIN
        self.onShow.append(self.movePosition)
        
        self.skin_path = KTglob.plugin_path
        
        self["TimerGraph"] = KTmultiPixmap()
        self["TimerText"] = Label(_("??:??"))
        self["TimerSlider"] = ProgressBar()
        self["TimerSliderText"] = Label(_("??:??"))
        self["TimerTransparent"] = Pixmap()
        self["TimerTransparentText"] = Label(_("01:00"))

    def renderScreen(self):
        self["TimerSlider"].setValue(int(kiddyTimer.remainingPercentage*100)) 
        self["TimerGraph"].setPixmapNum(kiddyTimer.curImg)
        self.sTimeLeft = KTglob.getTimeFromSeconds( (kiddyTimer.remainingTime + 59) , False ) # Add 59 Seconds to show one minute if less than 1 minute left...
        self["TimerText"].setText(self.sTimeLeft)
        self["TimerSliderText"].setText(self.sTimeLeft)
        self["TimerTransparentText"].setText(self.sTimeLeft)

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

    def movePosition(self):
        if self.instance:
            self.getPixmapList()
            self.instance.move(ePoint(config.plugins.KiddyTimer.position_x.value, config.plugins.KiddyTimer.position_y.value))

    def getPixmapList(self):
        self.percentageList = []
        for sPixmap in self["TimerGraph"].pixmapFiles:
            i = int(sPixmap[-8:-4])
            self.percentageList.append(i)
      
##############################################################################

class KiddyTimer():

    def __init__(self):
        self.session = None 
        self.dialog = None
        self.active = False

        self.iServiceReference = None
        self.curImg = 0

        self.sessionStartTime = None

        self.loopTimerStep = 1000
        self.loopTimer = eTimer()
        self.loopTimer.callback.append(self.calculateTimes)

        self.observeTimerStep = 60000 # Check every minute, if the time to acitivate the timer has come
        self.observeTimer = eTimer()
        self.observeTimer.callback.append(self.observeTime)

        config.misc.standbyCounter.addNotifier(self.enterStandby, initial_call=False)

    def gotSession(self, session):
        self.session = session
        self.startTimer()   
         
    def enterStandby(self,configElement):
        Standby.inStandby.onClose.append(self.endStandby)
        self.stopTimer()    
      
    def endStandby(self):
        self.sessionStartTime = None
        self.startTimer()
        
    def startTimer(self,bForceStart=False,iRemainingSeconds=0):
        curStartYear = time.localtime().tm_year 
        if curStartYear < 2011: 
            # Time has not yet been set from transponder, wait until it has been set
            eDVBLocalTimeHandler.getInstance().m_timeUpdated.get().append(self.gotTime)
        else:
            bDoStandardInit = True
            if bForceStart:
                self.enabled = True
            else:
                self.enabled = config.plugins.KiddyTimer.enabled.value
            if (self.enabled == True and self.timerHasToRun()) or bForceStart:   
                # This command may be double, just made to be sure, the observer is stopped when the real timer starts
                self.stopObserve()
                # Date of the current day
                self.currentDay = time.strftime("%d.%m.%Y" , time.localtime())
                # First check for Cheat- attempts by kids
                if self.detectCheatAttempt():
                    config.plugins.KiddyTimer.remainingTime.value = 0
                    configfile.save()
                    bForceStart = True
                elif iRemainingSeconds > 0:
                    self.resetTimer(setTime=iRemainingSeconds)
                    bDoStandardInit = False
                elif self.currentDay != config.plugins.KiddyTimer.lastStartDay.getValue():
                    self.resetTimer()
                    bDoStandardInit = False
                if bDoStandardInit:             
                    self.setCurrentDayTime()
                    self.setSessionTime(config.plugins.KiddyTimer.remainingTime.getValue())
                    self.setRemainingTime(self.sessionTime)
                    self.setSessionStartTime()
    
                self.setPluginStatus("RUNNING")
                self.toggleActiveState(True)
                if not bForceStart:
                    self.askForActivation()
                else:
                    self.startLoop()
            else:
                if (self.enabled == True):
                    self.startObserve()

    def gotTime(self):
        eDVBLocalTimeHandler.getInstance().m_timeUpdated.get().remove(self.gotTime)
        self.startTimer()
    
    def stopTimer(self):
        if self.active:
            self.saveValues()
        self.toggleActiveState(False)
        self.stopLoop()
        self.stopObserve()
        self.setPluginStatus("SHUTDOWN")
        self.iServiceReference = None
        self.dialog = None
                
    def resetTimer(self,**kwargs):
        if "setTime" in kwargs.keys():
            self.setCurrentDayTime(kwargs["setTime"])
        else:            
            self.setCurrentDayTime()
        
        self.setSessionTime(self.currentDayTime)
        self.setRemainingTime(self.currentDayTime)
        self.setSessionStartTime()

    def timerHasToRun(self):
        curStartTime = time.localtime()
        iPluginStart = KTglob.getSecondsFromClock( [curStartTime[3],curStartTime[4]] )
        iMonitorEnd = KTglob.getSecondsFromClock(config.plugins.KiddyTimer.monitorEndTime.getValue())  
        iMonitorStart = KTglob.getSecondsFromClock(config.plugins.KiddyTimer.monitorStartTime.getValue())  
        return (iPluginStart < iMonitorEnd) & (iPluginStart >= iMonitorStart)

    def startLoop(self):
        self.loopTimer.start(self.loopTimerStep,1)
    
    def stopLoop(self):
        self.loopTimer.stop()
    
    def startObserve(self):
        curStartTime = time.localtime()
        iPluginStart = KTglob.getSecondsFromClock( [curStartTime[3],curStartTime[4]] )
        iMonitorStart = KTglob.getSecondsFromClock(config.plugins.KiddyTimer.monitorStartTime.getValue())  

        # If we are after Pluginstart, then sleep until next day
        if (iPluginStart > iMonitorStart):
            iMonitorStart += 86400

        iObserveTimerStep = (iMonitorStart - iPluginStart)*1000 + 1000
        print "[KiddyTimer] setting plugin idle for ms=", iObserveTimerStep
        self.observeTimer.start(iObserveTimerStep, False)
        
    def stopObserve(self):
        self.observeTimer.stop()
    
    def observeTime(self):
        print "[KiddyTimer] Observer checking if plugin has to run"
        if (self.timerHasToRun()):
            self.stopObserve()
            self.startTimer()
    
    def detectCheatAttempt(self):
        sLastStatus = config.plugins.KiddyTimer.lastStatus.value
        if (sLastStatus == "RUNNING"):
            # cheat detected: RUNNING is NEVER a valid entry when checking.
            Notifications.AddNotification(MessageBox, _("Cheat attempt detected. \nBox has not been shudown correctly. \nRemaining time was set to 0."), MessageBox.TYPE_WARNING, 0)
            return True
        else:
            return False

    def setPluginStatus(self,sStatus):
        # Set values for detection of cheat attempts
        config.plugins.KiddyTimer.lastStatus.value = sStatus
        config.plugins.KiddyTimer.lastStatus.save()
        configfile.save()

    def askForActivation(self):
        iTimeOut = config.plugins.KiddyTimer.activationDialogTimeout.getValue()
        Notifications.AddNotificationWithCallback(self.callbackAskForActivation, MessageBox, _("Do you want to start the kiddytimer- plugin now."), MessageBox.TYPE_YESNO, iTimeOut)

    def callbackAskForActivation(self, value):
        if not value:
            self.callbackParameter = PARAM_STOPTIMER
            self.askForPIN()

        self.startLoop()

    def askForPIN(self):
        self.session.openWithCallback( self.pinEntered, PinInput, pinList=[config.plugins.KiddyTimer.pin.getValue()], triesEntry=self.getTriesEntry(), title=_("Please enter the correct pin code"), windowTitle=_("Enter pin code"))
    
    def getTriesEntry(self):
        return config.ParentalControl.retries.setuppin

    def pinEntered(self, result):
        if not result:
            pass
        else:
            if self.callbackParameter == PARAM_STOPTIMER:
                self.stopTimer()      
            elif self.callbackParameter == PARAM_DISABLETIMER:
                self.toggleEnabledState(False)
            elif self.callbackParameter == PARAM_INCREASETIMER:
                self.session.openWithCallback(self.modifySessionTime, MinuteInput)
            elif self.callbackParameter == PARAM_SETTIMER:
                self.session.openWithCallback(self.callbackSetTimer, MinuteInput)
            elif self.callbackParameter == PARAM_RESETTIMER:
                self.resetTimer()
            elif self.callbackParameter == PARAM_ENABLETIMERONCE:
                self.session.openWithCallback(self.callbackEnableTimerOnce, MinuteInput)

    def setCurrentDayTime(self,iDayTime=PARAM_NONE):
        if iDayTime == PARAM_NONE:
            iDayTime = KTglob.getTodaysTimeInSeconds()
        self.currentDayTime = iDayTime

    def setSessionStartTime(self):
        self.sessionStartTime = time.localtime()
                
    def modifySessionTime(self, iMinutes):
        iSeconds = iMinutes * 60
        if self.callbackParameter == PARAM_INCREASETIMER:
            iSeconds += self.sessionTime
        else:
            iSeconds = self.sessionTime - iSeconds 
        self.setSessionTime(iSeconds)
        

    def setSessionTime(self, iSeconds):
        self.sessionTime = iSeconds
        if self.sessionTime > self.currentDayTime:
            self.setCurrentDayTime(self.sessionTime)
        if self.sessionTime < 0:
            self.sessionTime = 0

    def setRemainingTime(self,iRemaining):
        if iRemaining < 0:
            iRemaining = 0
        self.remainingTime = iRemaining
        if self.currentDayTime > 0:
            self.remainingPercentage = iRemaining / self.currentDayTime
        else:
            self.remainingPercentage = 0

    def callbackSetTimer(self, iMinutes):
        iSeconds = iMinutes * 60
        self.resetTimer(setTime=iSeconds)
                
    def callbackEnableTimerOnce(self, iMinutes):
        iSeconds = iMinutes * 60
        if iSeconds > 0:
            #If timer is active: stop it first to prohibit conflicts
            if self.active:
                self.stopTimer()
            self.startTimer(True, iSeconds)
    
    def toggleActiveState(self , bStatus):
        # Initialize dialog
        if self.dialog == None and bStatus:
            self.dialog = self.session.instantiateDialog(KiddyTimerScreen)
        self.active = bStatus
        if bStatus == True:
            self.dialog.show()
        else:
            if self.dialog != None:
                self.dialog.hide()

    def toggleEnabledState(self, bStatus):
        config.plugins.KiddyTimer.enabled.value = bStatus
        self.enabled = bStatus
        config.plugins.KiddyTimer.enabled.save()
        configfile.save()
        if self.enabled:
            self.startTimer()
        else:
            self.stopTimer()

    def calculateTimes(self):
        self.stopLoop()
        if self.active == True and self.timerHasToRun():
            odtEnd = time.mktime(time.localtime())
            iDiff = odtEnd - time.mktime(self.sessionStartTime)
            iRemaining = self.sessionTime - iDiff
            if iRemaining < 0:
                iRemaining = 0
            self.remainingTime = iRemaining
            if self.currentDayTime > 0:
                self.remainingPercentage = iRemaining / self.currentDayTime
            else:
                self.remainingPercentage = 0

            self.setImageNumber()
            
            if self.remainingTime == 0:
                self.iServiceReference = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
                NavigationInstance.instance.stopService()
            self.dialog.renderScreen()
            self.startLoop()
        else:
            self.stopTimer()

    def setImageNumber(self):
        iCurPercent = int( self.remainingPercentage * 1000 )
        iCount = 0
        for iPercent in self.dialog.percentageList:
           if iCurPercent <= iPercent:
               iCount = iCount + 1
        iCount = iCount - 1
        if iCount < 0:
            iCount = 0
        self.curImg = iCount
        
    def saveValues(self):
        if hasattr(self,"currentDay"):
            config.plugins.KiddyTimer.lastStartDay.value = self.currentDay
            config.plugins.KiddyTimer.lastStartDay.save()
        if hasattr(self,"remainingTime"):
            config.plugins.KiddyTimer.remainingTime.value = int(self.remainingTime)
            config.plugins.KiddyTimer.remainingTime.save()

    def showExtensionsMenu(self):
        keyList = []
        if self.enabled:
            if self.active:
                keyList.append((_("Stop KiddyTimer (this session only)"),PARAM_STOPTIMER))
                keyList.append((_("Increase remaining time"),PARAM_INCREASETIMER))
                keyList.append((_("Decrease remaining time"),PARAM_DECREASETIMER))
                keyList.append((_("Set remaining time"),PARAM_SETTIMER))
                keyList.append((_("Reset todays remaining time"),PARAM_RESETTIMER))
            else:
                keyList.append((_("Start KiddyTimer"),PARAM_STARTTIMER))
            keyList.append((_("Enable KiddyTimer for x minutes"),PARAM_ENABLETIMERONCE))
            keyList.append((_("Disable KiddyTimer"),PARAM_DISABLETIMER))
        else:
            keyList.append((_("Enable KiddyTimer"),PARAM_ENABLETIMER))
            keyList.append((_("Enable KiddyTimer for x minutes"),PARAM_ENABLETIMERONCE))
        self.session.openWithCallback(self.DoSelectionExtensionsMenu,ChoiceBox,_("Please select your KiddyTimer- option"),keyList)
        
    def DoSelectionExtensionsMenu(self,answer):
        self.callbackParameter = PARAM_NONE
        if answer is None:
            pass
        elif answer[1] in [PARAM_DISABLETIMER,PARAM_STOPTIMER,PARAM_INCREASETIMER,PARAM_SETTIMER,PARAM_ENABLETIMERONCE,PARAM_RESETTIMER]:
            self.callbackParameter = answer[1]
            self.askForPIN()
        elif  answer[1] == PARAM_STARTTIMER:
            self.startTimer()
        elif  answer[1] == PARAM_ENABLETIMER: 
            self.toggleEnabledState(True)
        elif answer[1] == PARAM_DECREASETIMER:
            self.session.openWithCallback(self.modifySessionTime, MinuteInput)
        else:
            self.session.open(MessageBox,_("Invalid selection"), MessageBox.TYPE_ERROR, 5)

# Assign global variable kiddyTimer
kiddyTimer = KiddyTimer()
