from Components.Sources.Source import Source

class CurrentService(Source):
	def __init__(self, session):
		Source.__init__(self)
		self.session = session

	def command(self):
		currentServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
		if currentServiceRef is not None:
			text = currentServiceRef.toString()
		else:
			text = "N/A"

		return text

	text = property(command)

