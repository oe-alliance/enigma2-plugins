from AC3utils import AC3, PCM, AC3PCM, lFileDelay, dec2hex, hex2dec
from Components.config import config
from enigma import eTimer
from Tools.ISO639 import LanguageCodes
import os
import NavigationInstance

class AC3delay:
    def __init__(self, session):
        self.iService = None
        self.iServiceReference = None
        self.iAudioDelay = None
        self.channelAudio = AC3
        self.whichAudio = AC3
        self.bIsRecording = False

        # Current audio- delay
        self.lamedbDelay = {}

        self.getAudioInformation()

        self.activateTimer = eTimer()
        self.activateTimer.callback.append(self.activateDelay)
        self.activateWait = config.plugins.AC3LipSync.activationDelay.getValue()
        
        # Current value for movie start behaviour
        self.movieStart = config.usage.on_movie_start.getValue()

    def initAudio(self):
        self.iService = NavigationInstance.instance.getCurrentService()
        self.iServiceReference = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
        self.iAudioDelay = self.iService and self.iService.audioDelay()
        self.iSeek = self.iService and self.iService.seek()

    def deleteAudio(self):
        self.iService = None
        self.iAudioDelay = None
        self.iSeek = None

    def setChannelAudio(self, sAudio):
        self.channelAudio = sAudio

    def delayedActivateDelay(self):
        if self.activateTimer.isActive:
            self.activateTimer.stop()
        self.activateTimer.start(self.activateWait, False)

    def activateDelay(self):
        if self.activateTimer.isActive:
            self.activateTimer.stop()
        bInitialized = False
        if self.iService == None:
            self.initAudio()
            bInitialized = True
        if self.iServiceReference is not None:
            lCurPosition = self.cueGetCurrentPosition()
            self.deleteAudio()
            if self.whichAudio == self.channelAudio:
                config.usage.on_movie_start.setValue("beginning")
                NavigationInstance.instance.stopService()
                NavigationInstance.instance.playService(self.iServiceReference)
                config.usage.on_movie_start.setValue(self.movieStart)
                if lCurPosition is not None:
                    self.lCurPosition = lCurPosition
                    self.timer = eTimer()
                    self.timer.callback.append(self.seekAfterWait)
                    self.timer.start(200, False)
        else:
            self.deleteAudio()
        
    def seekAfterWait(self):
        self.timer.stop()
        self.initAudio()
        if self.iSeek is not None:
            self.iSeek.seekTo(self.lCurPosition)
        self.deleteAudio()

    def cueGetCurrentPosition(self):
        if self.iSeek is None:
            return None
        r = self.iSeek.getPlayPosition()
        if r[0]:
            return None
        return long(r[1])

    def getLamedbDelay(self, sAudio):
        bInitialized = False
        if self.iService == None:
            self.initAudio()
            bInitialized = True
        iDelay = 0
        if self.iAudioDelay is not None:
            if sAudio == AC3:
                iDelay = self.iAudioDelay.getAC3Delay()
            else:
                iDelay = self.iAudioDelay.getPCMDelay()
            if iDelay == -1:
                iDelay = 0
        if bInitialized == True:
            self.deleteAudio()
        return iDelay

    def getFileDelay(self, sAudio):
        sFileName = lFileDelay[sAudio]
        if os.path.exists(sFileName) == True:
            delayfile = open(sFileName,"r")
            delay = 0
            delay = delayfile.readline()
            delayfile.close()
            iDelay = hex2dec(delay)/90
        else:
            iDelay = 0
        return int(iDelay)

    def setLamedbDelay(self, sAudio, iDelay):
        self.initAudio()
        if self.iAudioDelay is not None:
            if iDelay == 0:
                iDelay = -1
            if sAudio == AC3:
                self.iAudioDelay.setAC3Delay(iDelay)
            else:
                self.iAudioDelay.setPCMDelay(iDelay)

    def setFileDelay(self, sAudio, iDelay, bDelayStart):
        hDelay = dec2hex(iDelay*90)
        sFileName = lFileDelay[sAudio]
        if os.path.exists(sFileName) == True:
            delayfile = open(lFileDelay[sAudio],"w")
            delayfile.write("%s\0" % hDelay)
            delayfile.close()
            if bDelayStart == True:
                self.delayedActivateDelay()
            else:
                self.activateDelay()

    def getAudioInformation(self):
        bInitialized = False
        if self.iService == None:
            self.initAudio()
            bInitialized = True
        self.initAudio()
        lCurPosition = self.cueGetCurrentPosition()
        if lCurPosition is not None:
            self.bIsRecording = True
        oAudioTracks = self.iService and self.iService.audioTracks()
        n = oAudioTracks and oAudioTracks.getNumberOfTracks() or 0
        tlist = []
        self.selectedAudioIndex = oAudioTracks.getCurrentTrack()
        if n >= 0:
            for x in range(n):
                i = oAudioTracks.getTrackInfo(x)
                language = i.getLanguage()
                description = i.getDescription()
                if LanguageCodes.has_key(language):
                    language = LanguageCodes[language][0]
                if len(description):
                    description += " (" + language + ")"
                else:
                    description = language

                tlist.append((description, x))
                if x == self.selectedAudioIndex:
                    if description.find("AC3") != -1 or description.find("DTS") != -1:
                        self.whichAudio = AC3
                        self.channelAudio = AC3
                    else:
                        self.whichAudio = PCM
                        self.channelAudio = PCM
                    self.selectedAudioInfo = (description, x)
            tlist.sort(key=lambda x: x[0])

            self.audioTrackList = tlist
        for sAudio in AC3PCM:
            self.lamedbDelay[sAudio]=self.getLamedbDelay(sAudio)
        del oAudioTracks
        if bInitialized == True:
            self.deleteAudio()

