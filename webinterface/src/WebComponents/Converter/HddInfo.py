from Components.Converter.Converter import Converter
from Components.Element import cached

class HddInfo(Converter, object):
    MODEL = 0
    SIZE = 1
    FREE = 2
    
    def __init_(self, type):
        Converter.__init__(self)
        
        self.type = {
                     "Model" : self.MODEL,
                     "Size" : self.SIZE,
                     "Free" : self.FREE,
                     }[type]
                     
    @cached
    def getText(self):
        hdd = self.source.hdd
        
        if self.type == self.MODEL:
            return hdd.model
        elif self.type == self.SIZE:
            return hdd.size
        elif self.type == self.FREE:
            return hdd.free
        
    text = property(getText)
    