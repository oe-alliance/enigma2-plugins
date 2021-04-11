# NaughtyAmerica plugin by AliAbdul
from Podcast import Podcast

##################################################


class NaughtyAmerica(Podcast):
	def __init__(self):
		Podcast.__init__(self, "Naughty America", "NaughtyAmerica.png", "http://www.naughtyamerica.com/one_minclip_archive.xml")

##################################################


def getPlugin():
	return NaughtyAmerica()
