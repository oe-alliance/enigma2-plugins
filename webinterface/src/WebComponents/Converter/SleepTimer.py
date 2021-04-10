from Components.Converter.Converter import Converter
from Components.Element import cached

class SleepTimer(Converter):
    ENABLED = 0
    TIME = 1
    ACTION = 2
    CONFIRMED = 3
    TEXT = 4
    
    def __init__(self, type):
        Converter.__init__(self, type)
        self.type = {"Enabled": self.ENABLED,
                      "Time": self.TIME,
                      "Action": self.ACTION,
                      "Text": self.TEXT,
                      "Confirmed": self.CONFIRMED,
                    }[type]

    @cached
    def getText(self):
        timer = self.source.timer
        
        if self.type is self.ENABLED:
            return str(timer[0])
        elif self.type is self.TIME:
            return str(timer[1])
        elif self.type is self.ACTION:
            return str(timer[2])
        elif self.type is self.CONFIRMED:
            return str(timer[3])
        elif self.type is self.TEXT:
            if not timer[4] is None:
                return str(timer[4])
            else:
                return "" 
        else:
            return "N/A"
        
    text = property(getText)
