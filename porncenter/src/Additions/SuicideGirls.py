# SuicideGirls plugin by AliAbdul
from Podcast import Podcast

##################################################


class SuicideGirls(Podcast):
	def __init__(self):
		Podcast.__init__(self, "Suicide Girls", "SuicideGirls.png", "http://suicidegirls.com/rss/video")

##################################################


def getPlugin():
	return SuicideGirls()
