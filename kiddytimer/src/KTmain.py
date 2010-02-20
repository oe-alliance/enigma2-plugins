from Components.Label import Label
from Components.ProgressBar import ProgressBar
from KTMultiPixmap import KTmultiPixmap
from Components.config import config
from Screens.ChoiceBox import ChoiceBox
from Screens.InputBox import PinInput
from Screens.MessageBox import MessageBox
from Screens.MinuteInput import MinuteInput
from Screens.Screen import Screen
from Screens import Standby
from Tools.BoundFunction import boundFunction
from Tools import Notifications
from enigma import ePoint, eTimer
import KTglob
import NavigationInstance
import time

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
        
    def renderScreen(self):
        self["TimerSlider"].setValue(int(oKiddyTimer.remainingPercentage*100)) 
        self["TimerGraph"].setPixmapNum(oKiddyTimer.curImg)
        self.sTimeLeft = KTglob.getTimeFromSeconds( (oKiddyTimer.remainingTime + 59) , False ) # Add 59 Seconds to show one minute if less than 1 minute left...
        self["TimerText"].setText(self.sTimeLeft)
        self["TimerSliderText"].setText(self.sTimeLeft)

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
        self.dialogEnabled = False

        self.iServiceReference = None
        self.curImg = 0
                    
        self.loopTimerStep = 10000
        self.loopTimer = eTimer()
        self.loopTimer.callback.append(self.calculateTimer)

        config.misc.standbyCounter.addNotifier(self.enterStandby, initial_call = False)
    
    def gotSession(self, session):
        self.session = session
        self.enabled = config.plugins.KiddyTimer.enabled.value
        # Start- Time of the plugin, used for calculating the remaining time
        self.pluginStartTime = time.localtime()            
        # Number of the current day
        self.dayNr = int(time.strftime("%w" , self.pluginStartTime ))
        # Current Day to compare with the last saved day. If different -> Reset counter
        # Number of seconds for the current day
        iDayTime = KTglob.getSecondsFromClock( config.plugins.KiddyTimer.dayTimes[self.dayNr].timeValue.getValue() )
        self.currentDayTime = iDayTime
        self.currentDay = time.strftime("%d.%m.%Y" , self.pluginStartTime)
        self.lastSavedRemainingTime = config.plugins.KiddyTimer.remainingTime.getValue()
        self.remainingTime = self.lastSavedRemainingTime
        if self.enabled == True:            
            if self.currentDay != config.plugins.KiddyTimer.lastStartDay.getValue():
                #Reset all Timers
                self.resetTimer()
            
            if self.dialog == None:
                self.dialog = self.session.instantiateDialog(KiddyTimerScreen)
                self.dialog.hide()
                
            self.setDialogStatus(self.timerHasToRun())
            if self.dialogEnabled == True:
                self.askForActivation()
            else:
                self.calculateTimer()
    
    def askForActivation(self):
        iTimeOut = config.plugins.KiddyTimer.activationDialogTimeout.getValue()
        Notifications.AddNotificationWithCallback(self.activationCallback, MessageBox, _("Do you want to start the kiddytimer- plugin now."), MessageBox.TYPE_YESNO, iTimeOut)

    def activationCallback(self, value):
        self.setDialogStatus(self.timerHasToRun())

        if value:
            self.setDialogStatus( True )
            if self.dialog == None:
                self.dialog = self.session.instantiateDialog(KiddyTimerScreen)
                self.dialog.hide()
        else:
            self.askForPassword(self.pinEnteredDialog)
                                       
        self.calculateTimer()

    def askForPassword(self,callbackFunction):
        self.session.openWithCallback( callbackFunction, PinInput, pinList = [config.plugins.KiddyTimer.pin.getValue()], triesEntry = self.getTriesEntry(), title = _("Please enter the correct pin code"), windowTitle = _("Enter pin code"))
    
    def getTriesEntry(self):
        return config.ParentalControl.retries.setuppin
        
    def pinEnteredDialog(self, result):
        if result is None:
            pass
        elif not result:
            pass
        else:
            self.setDialogStatus( False )        
    
    def pinEnteredDesactivation(self, result):
        if result is None:
            pass
        elif not result:
            pass
        else:
            config.plugins.KiddyTimer.enabled.value = False
            config.plugins.KiddyTimer.enabled.save()
            self.stopMe()
    
    def pinEnteredIncreaseRemainingTime(self, result):
        if result is None:
            pass
        elif not result:
            pass
        else:
            self.session.openWithCallback(self.increaseRemainingCallback, MinuteInput)

    def increaseRemainingCallback(self, iMinutes):
        iSeconds = iMinutes * 60
        self.lastSavedRemainingTime += iSeconds
        if self.lastSavedRemainingTime > self.currentDayTime:
            self.lastSavedRemainingTime = self.currentDayTime
        self.calculateTimer()

    def decreaseRemainingCallback(self, iMinutes):
        iSeconds = iMinutes * 60
        self.lastSavedRemainingTime -= iSeconds
        if self.lastSavedRemainingTime < 0:
            self.lastSavedRemainingTime = 0
        self.calculateTimer()

    def startLoop(self):
        self.loopTimer.start(self.loopTimerStep,1)
    
    def stopLoop(self):
        self.loopTimer.stop()
    
    def resetTimer(self):
        iDayTime = KTglob.getSecondsFromClock( config.plugins.KiddyTimer.dayTimes[self.dayNr].timeValue.getValue() )
        self.currentDayTime = iDayTime
        
        self.lastSavedRemainingTime = self.currentDayTime
        self.remainingTime = self.currentDayTime
                
        config.plugins.KiddyTimer.lastStartDay.setValue(self.currentDay)
        self.remainingPercentage = self.remainingTime / self.currentDayTime
        self.pluginStartTime = time.localtime()
        
        self.saveValues()
    
    def timerHasToRun(self):
        iPluginStart = KTglob.getSecondsFromClock( [self.pluginStartTime[3],self.pluginStartTime[4]] )
        iMonitorEnd = KTglob.getSecondsFromClock(config.plugins.KiddyTimer.monitorEndTime.getValue())  
        return iPluginStart < iMonitorEnd 
    
    def setDialogStatus(self , bStatus):
        if bStatus == True:
            self.dialogEnabled = True
            if self.dialog != None:
                self.dialog.show()
        else:
            self.dialogEnabled = False
            if self.dialog != None:
                self.dialog.hide()

    def calculateTimer(self):
        self.stopLoop()
        if self.dialogEnabled == True:
            odtEnd = time.mktime(time.localtime())
            iDiff = odtEnd - time.mktime(self.pluginStartTime)
            iRemaining = self.lastSavedRemainingTime - iDiff
            if iRemaining < 0:
                iRemaining = 0
            self.remainingTime = iRemaining
            self.remainingPercentage = iRemaining / self.currentDayTime
            self.saveValues()
            
            self.setImageNumber()
            
            if self.remainingTime == 0:
                self.iServiceReference = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
                NavigationInstance.instance.stopService()
            self.dialog.renderScreen()
        self.startLoop()

    def enterStandby(self,configElement):
        Standby.inStandby.onClose.append(self.endStandby)
        self.stopMe()            
        
    def showHide(self):
        if config.plugins.KiddyTimer.enabled.value and self.timerHasToRun():
            self.setDialogStatus(True)
        else:
            self.setDialogStatus(False)
        
    def endStandby(self):
        self.gotSession(self.session)

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

    def stopMe(self):
        self.saveValues()
        if self.dialog != None:
            self.stopLoop()
            self.dialog.hide()
        self.iServiceReference = None
        self.dialog = None
        
    def saveValues(self):
        config.plugins.KiddyTimer.lastStartDay.save()
        config.plugins.KiddyTimer.remainingTime.setValue(int(self.remainingTime))
        config.plugins.KiddyTimer.remainingTime.save()

    def showExtensionsMenu(self):
        self.session.openWithCallback(self.DoSelectionExtensionsMenu,ChoiceBox,_("Please select your KiddyTimer- option"),self.getOptionList())

    def getOptionList(self):
        keyList = []
        if config.plugins.KiddyTimer.enabled.value:
            if self.dialogEnabled:
                keyList.append((_("Stop KiddyTimer (this session only)"),1))
                keyList.append((_("Increase remaining time"),5))
                keyList.append((_("Decrease remaining time"),6))
            else:
                keyList.append((_("Start KiddyTimer"),2))
            keyList.append((_("Disable KiddyTimer"),3))
        else:
            keyList.append((_("Enable KiddyTimer"),4))
        return keyList
    
    def DoSelectionExtensionsMenu(self,answer):
        if answer is None:
            pass
        elif answer[1] == 3:
            self.askForPassword(self.pinEnteredDesactivation)
        elif  answer[1] == 1:
            self.activationCallback(False)
        elif  answer[1] == 2:
            self.activationCallback(True)
        elif  answer[1] == 4:
            config.plugins.KiddyTimer.enabled.value = True
            config.plugins.KiddyTimer.enabled.save()
            self.gotSession(self.session)
        elif answer[1] ==5:
            self.askForPassword(self.pinEnteredIncreaseRemainingTime)
        elif answer[1] ==6:
            self.session.openWithCallback(self.decreaseRemainingCallback, MinuteInput)
        else:
            self.session.open(MessageBox,_("Invalid selection"), MessageBox.TYPE_ERROR, 5)

# Assign global variable oKiddyTimer
oKiddyTimer = KiddyTimer()