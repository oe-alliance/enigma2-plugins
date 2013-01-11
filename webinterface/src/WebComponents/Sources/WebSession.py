from Components.Sources.Source import Source
import uuid

class WebSession(Source):
	def __init__(self, request):
		Source.__init__(self)
		self.request = request

	def getText(self):
		return self.request.enigma2_session.id

	text = property(getText)

