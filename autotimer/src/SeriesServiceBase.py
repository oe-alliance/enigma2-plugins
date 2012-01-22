# by betonme @2012

class SeriesServiceBase():
	def __init__(self):
		pass

	def getName(self):
		# Return a presentable name
		return "Not used"

	def getId(self):
		# Return a unique id
		return "None"


	# Attention: Both functions has to be blocking!

	def getSeriesList(self, name):
		# On Success: Return a series list of id, name tuples
		# On Failure: Return a empty list or None
		return None
		
	def getEpisodeId(self, id, begin, end, channel):
		# On Success: Return a single season, episode, title tuple
		# On Failure: Return a empty list or None
		return None
