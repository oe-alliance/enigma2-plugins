from Components.Converter.Converter import Converter
from Components.Element import cached

class SimpleResult(Converter, object):
	RESULT = 0
	RESULTTEXT = 1
	
	def __init__(self, type):
		Convert.__init__(self, type)
		self.type = { "result" : self.RESULT,
					  "resulttext" : self.RESULTTEXT
					}[type]

	@cached
	def getText(self):
		result = self.source.result
		
		if self.type is self.RESULT:
			return result.result
		elif self.type is self.RESULTTEXT:
			return result.resulttext
		else:
			return _("N/A")
		
	text = property(getText)