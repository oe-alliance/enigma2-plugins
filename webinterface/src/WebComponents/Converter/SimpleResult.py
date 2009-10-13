from Components.Converter.Converter import Converter
from Components.Element import cached

class SimpleResult(Converter):
	RESULT = 0
	RESULTTEXT = 1
	
	def __init__(self, type):
		Converter.__init__(self, type)
		self.type = { "Result" : self.RESULT,
					  "ResultText" : self.RESULTTEXT
					}[type]

	@cached
	def getText(self):
		result = self.source.result
		
		if self.type is self.RESULT:
			return str(result[0])
		elif self.type is self.RESULTTEXT:
			return str(result[1])
		else:
			return "N/A"
		
	text = property(getText)
