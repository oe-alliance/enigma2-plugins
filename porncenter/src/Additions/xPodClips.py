# xPodClips plugin by AliAbdul
from Podcast import Podcast

##################################################


class xPodClips(Podcast):
	def __init__(self):
		Podcast.__init__(self, "xPod Clips", "xPodClips.png", "http://feeds.feedburner.com/XpodClips")

##################################################


def getPlugin():
	return xPodClips()
