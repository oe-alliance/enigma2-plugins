from Components.Converter.Converter import Converter
from Components.Element import cached

class TPMChallenge(Converter):
    L2C = 0
    L3C = 1
    VALUE = 2
    RESULT = 3
    TEXT = 4
    
    def __init__(self, type):
        Converter.__init__(self, type)
        self.type = {"Level2Cert": self.L2C,
                      "Level3Cert": self.L3C,
                      "Value": self.VALUE,
                      "Result": self.RESULT,
                      "Text": self.TEXT
                    }[type]

    @cached
    def getText(self):
        res = self.source.tpm_result
        
        if self.type is self.L2C:
            return str(res[0])
        elif self.type is self.L3C:
            return str(res[1])
        elif self.type is self.VALUE:
            return str(res[2])
        elif self.type is self.RESULT:
            return str(res[3])
        elif self.type is self.TEXT:
            return str(res[4]) 
        else:
            return "N/A"
        
    text = property(getText)
