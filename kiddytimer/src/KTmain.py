from Components.Label import Label
from KTMultiPixmap import KTmultiPixmap
from Components.config import config
from Screens.Screen import Screen
from Screens import Standby
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
        
    def renderScreen(self):
        self["TimerGraph"].setPixmapNum(KTglob.oKiddyTimer.curImg)
        self["TimerGraph"].show()
        self.sTimeLeft = KTglob.getTimeFromSeconds( (KTglob.oKiddyTimer.remainingTime + 59) , False ) # Add 59 Seconds to show one minute if less than 1 minute left...
        self["TimerText"].setText(self.sTimeLeft)

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
                    
        self.loopTimerStep = 1000
        self.loopTimer = eTimer()
        self.loopTimer.callback.append(self.calculateTimer)
    
    def gotSession(self, session):
        self.session = session
        self.initVars()
    
    def initVars(self):
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
        if Standby.inStandby != None:
            Standby.inStandby.onClose.append(self.endStandby)
            self.stopMe()            
        else:
            if self.dialogEnabled == True:
                odtEnd = time.mktime(time.localtime())
                iDiff = odtEnd - time.mktime(self.pluginStartTime)
                iRemaining = self.lastSavedRemainingTime - iDiff
                if iRemaining < 0:
                    iRemaining = 0
                self.remainingTime = iRemaining
                self.remainingPercentage = iRemaining / KTglob.oKiddyTimer.currentDayTime
                self.saveValues()
                
                self.setImageNumber()
                
                if self.remainingTime == 0:
                    self.iServiceReference = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
                    NavigationInstance.instance.stopService()
                self.dialog.renderScreen()
            self.startLoop()

    def showHide(self):
        if config.plugins.KiddyTimer.enabled.value:
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
        