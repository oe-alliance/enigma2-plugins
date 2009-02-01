from Components.Sources.Source import Source
from Components.Harddisk import HarddiskManager
from Components.Element import cached

class Hdd(Source):
    def __init__(self, devicecount = 0):
        Source.__init__(self)
        self.devicecount = devicecount
        
        self.model = _("N/A")
        self.capacity = _("N/A")
        self.free = _("N/A")

    @cached
    def getHddData(self):
        hddmgr = HarddiskManager()
        
        if len(hddmgr.hdd) <= self.devicecount:
            hdd = hddmgr.hdd[self.devicecount] # TODO, list more than the first harddisc if there are more than one. but this requires many changes in the way the webif generates the responses
            
            self.model = hdd.model()
            self.capacity = hdd.capacity()
            self.free = hdd.free()
            
    hdd = property(getHddData)
    
    def destroy(self):
        Source.destroy(self)