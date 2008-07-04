# Code for the AutoTimerPlugin
#from enigma import eServiceReference, iServiceInformation, eServiceCenter
from Components.Sources.Source import Source
#from ServiceReference import ServiceReference
#from Components.FileList import FileList
#from os import path as os_path

class AT( Source ):
    LIST = 0
    WRITE = 1
    
    def __init__(self, session,func = LIST):
        print "AutoTimer: init: ", func
        Source.__init__(self)
        self.func = func
        self.session = session
        error = "unknown command (%s)" % func
        self.result = [[error,error,error]]
    
    def handleCommand(self,cmd):
        print "AutoTimer: handleCommand: ", cmd    
        self.cmd = cmd
        if self.func is self.LIST:
            self.result = self.timerList(cmd)
        elif self.func is self.WRITE:
            self.result = self.writeTimer(cmd)
        
    def timerList(self,param):
        print "timerList:",param
        
        returnList = []
        
        from Components.PluginComponent import plugins
        from Plugins.Plugin import PluginDescriptor#, PluginEntryComponent
        pluginlist = plugins.getPlugins(PluginDescriptor.WHERE_PLUGINMENU)
        autoTimerAvailable = False
        for plugin in pluginlist:
            if plugin.name == "AutoTimer":
                #if PluginEntryComponent(plugin).name == "AutoTimer":
                autoTimerAvailable = True
        
        if autoTimerAvailable:
            print "AutoTimer vorhanden"
            from Plugins.Extensions.AutoTimer.plugin import autotimer
            
            if autotimer is None:
                from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
                autotimer = AutoTimer()
            #timers = autotimer.getTimerList
            #AutoTimerComponent
            from Plugins.Extensions.AutoTimer.AutoTimerComponent import AutoTimerComponent
            for timer in autotimer.getTimerList():
                print "TIMER: ", timer
                innerList = []
                innerList.append(timer.getName())
                innerList.append(timer.getMatch())
                
                if timer.hasAfterEvent():
                    innerList.append(timer.getAfterEvent()) # 2
                else:
                    innerList.append("") # 2
                                
                #excludes
                innerList.append(timer.getExcludedTitle())
                innerList.append(timer.getExcludedShort())
                innerList.append(timer.getExcludedDescription())
                innerList.append(timer.getExcludedDays())
                
                #inclides
                innerList.append(timer.getIncludedTitle())
                innerList.append(timer.getIncludedShort())
                innerList.append(timer.getIncludedDescription())
                innerList.append(timer.getIncludedDays())
                
                # filterSET
                self.excludes = (
                                 timer.getExcludedTitle(),
                                 timer.getExcludedShort(),
                                 timer.getExcludedDescription(),
                                 timer.getExcludedDays()
                )
                self.includes = (
                                 timer.getIncludedTitle(),
                                 timer.getIncludedShort(),
                                 timer.getIncludedDescription(),
                                 timer.getIncludedDays()
                )
                innerList.append(timer.getServices()) # 11
                innerList.append(timer.getBouquets()) # 12
                if timer.hasTimespan():
                    innerList.append(timer.getTimespanBegin()) # 13
                    innerList.append(timer.getTimespanEnd()) # 14
                else:
                    innerList.append("") # 13
                    innerList.append("") # 14
                
                if timer.hasDuration():
                    innerList.append(timer.getDuration()) # 15
                else:
                    innerList.append("") # 15
                
                if timer.hasCounter():
                    innerList.append(timer.getCounter()) # 16
                    innerList.append(timer.getCounterLeft()) # 17
                else:
                    innerList.append(0) # 16
                    innerList.append(0) # 17
                
                innerList.append(timer.getCounterLimit()) # 18
                
                if timer.hasDestination():
                    innerList.append(timer.getDestination()) # 19
                else:
                    innerList.append("/hdd/movie/") # 19
                    
                if timer.hasCounterFormatString():
                    innerList.append(timer.getCounterFormatString()) # 20
                else:
                    innerList.append("") # 20
                
                innerList.append(timer.getLastBegin()) # 21
                innerList.append(timer.getJustplay()) # 22
                innerList.append(timer.getAvoidDuplicateDescription()) # 23
                
                if timer.hasTags():
                    innerList.append(timer.getTags()) # 24
                else:
                    innerList.append("") # 24
                
                print "Enabled", timer.getEnabled()
                innerList.append(timer.getEnabled())  # 25
                innerList.append("off")  # 26

                returnList.append(innerList)
        
        return returnList

        
    def writeTimer(self,param):
        print "writeTimer: ",param
        # TODO: fix error handling

        return
        
    def command(self,param):
        print "command: ",param
        return

        param = int(param)
        
        # TODO: fix error handling
    
    def getList(self):
        return self.result
    
    list = property(getList)
    lut = {"Name": 0
           ,"Match": 1
           ,"AfterEvent": 2
           ,"ExcludedTitle": 3
           ,"ExcludedShort": 4
           ,"ExcludedDescription": 5
           ,"ExcludedDays": 6
           ,"IncludedTitle": 7
           ,"IncludedShort": 8
           ,"IncludedDescription": 9
           ,"IncludedDays": 10
           ,"Services": 11
           ,"Bouquets": 12
           ,"TimespanBegin": 13
           ,"TimespanEnd": 14
           ,"Duration": 15
           ,"Counter": 16
           ,"CounterLeft": 17
           ,"CounterLimit": 18
           ,"Destination": 19
           ,"CounterFormatString": 20
           ,"LastBegin": 21
           ,"Justplay": 22
           ,"AvoidDuplicateDescription": 23
           ,"Tags": 24
           ,"Enabled": 25
           ,"toggleDisabledIMG": 26
           }
