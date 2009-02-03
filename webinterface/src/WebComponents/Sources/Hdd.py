from Components.Sources.Source import Source
from Components.Harddisk import harddiskmanager

class Hdd(Source):
    def __init__(self, devicecount = 0):
        Source.__init__(self)
        self.devicecount = devicecount
    
    def getHddData(self):
        if len(harddiskmanager.hdd) > 0:
            return harddiskmanager.hdd[0] # TODO, list more than the first harddisc if there are more than one. but this requires many changes in the way the webif generates the responses
        else:
            return None
        
    
            
    hdd = property(getHddData)
    
    def destroy(self):
        Source.destroy(self)