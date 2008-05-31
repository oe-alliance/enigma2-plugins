from enigma import eDVBDB
from Components.Sources.Source import Source

class ServiceListReload( Source):
    BOTH = 0
    LAMEDB = 1
    USERBOUQUETS = 2
    
    def __init__(self, session):
        Source.__init__(self)
        self.session = session
        self.eDVBDB = eDVBDB.getInstance()
    
    def handleCommand(self,cmd):       
        try:
            self.cmd = int(cmd)
            if self.cmd is self.BOTH:
                self.reloadLameDB()
                self.reloadUserBouquets()
                self.result = [['true','reloaded both']]
            elif self.cmd is self.LAMEDB:
                self.result = self.reloadLameDB()
                self.result = [['true','reloaded lamedb']]
            elif self.cmd is self.USERBOUQUETS:
                self.result = self.reloadUserBouquets()
                self.result = [['true','reloaded bouquets']]
            else:
                self.result = False # results in message generated in getList
        except Exception,e:
            self.result = False # results in message generated in getList

    def reloadLameDB(self):
        print "[WebInterface] reloading lamedb"
        self.eDVBDB.reloadServicelist()
        
    def reloadUserBouquets(self):
        print "[WebInterface] reloading userbouquets"
        self.eDVBDB.reloadBouquets()
    
    def getList(self):
        try:
            if self.result:
                return self.result
            else:
                raise AttributeError
        except AttributeError:
            return [['false',"missing or wrong parameter mode [%i=both, %i=lamedb only, %i=userbouqets only]"%(self.BOTH,self.LAMEDB,self.USERBOUQUETS) ]]
    
    list = property(getList)
    lut = {"result": 0
           ,"mode": 1
           }
