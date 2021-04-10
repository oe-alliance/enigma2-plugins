from __future__ import absolute_import
# Pornabees plugin by AliAbdul
from .Podcast import Podcast

##################################################


class Pornabees(Podcast):
	def __init__(self):
		Podcast.__init__(self, "Pornabees", "Pornabees.png", "http://feeds.feedburner.com/PornabeesPodPorn")

##################################################


def getPlugin():
	return Pornabees()
