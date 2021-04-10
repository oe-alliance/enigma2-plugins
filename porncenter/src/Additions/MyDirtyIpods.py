from __future__ import absolute_import
# MyDirtyIpods plugin by AliAbdul
from .Podcast import Podcast

##################################################


class MyDirtyIpods(Podcast):
	def __init__(self):
		Podcast.__init__(self, "My Dirty Ipods", "MyDirtyIpods.png", "http://www.mydirtyipods.com/Ipod/IpodClips.xml")

##################################################


def getPlugin():
	return MyDirtyIpods()
