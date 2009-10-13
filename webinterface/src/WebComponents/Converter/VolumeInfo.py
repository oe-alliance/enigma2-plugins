from Components.Converter.Converter import Converter
from Components.Element import cached

class VolumeInfo(Converter):
	RESULT = 0
	RESULTTEXT = 1
	VOLUME = 2
	ISMUTED = 3
	
	def __init__(self, type):
		Converter.__init__(self, type)
		self.type = { "Result" : self.RESULT,
					  "ResultText" : self.RESULTTEXT,
					  "Volume" : self.VOLUME,
					  "IsMuted" : self.ISMUTED
					}[type]

	@cached
	def getText(self):
		volume = self.source.volume
		
		if self.type is self.RESULT:
			return str(volume[0])
		elif self.type is self.RESULTTEXT:
			return str(volume[1])
		elif self.type is self.VOLUME:
			return str(volume[2])
		elif self.type is self.ISMUTED:
			return str(volume[3])
		else:
			return "N/A"
		
	text = property(getText)
