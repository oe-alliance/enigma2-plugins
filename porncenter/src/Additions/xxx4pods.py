from __future__ import absolute_import
# xxx4pods plugin by AliAbdul
from .Podcast import Podcast

##################################################

class xxx4pods(Podcast):
	def __init__(self):
		Podcast.__init__(self, "xxx4pods", "xxx4pods.png", "http://xxx4pods.com/podcasts/podcast.xml")

##################################################

def getPlugin():
	return xxx4pods()
