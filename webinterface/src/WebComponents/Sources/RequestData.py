from Components.Sources.Source import Source

class RequestData(Source):
	"""
		a source for requestinformations like the adress that the client requested to reache the box
	"""
	HOST = 0
	PORT = 1
	METHOD = 2
	PATH = 3
	REMOTEADRESS = 4
	REMOTEPORT = 5
	REMOTETYPE = 6
	URI = 7

	def __init__(self, request, what=None):
		Source.__init__(self)
		self.request = request
		self.what = what

	def handleCommand(self, cmd):
		pass

	def getHTML(self, id):
		if self.what is self.HOST:
			return self.request.getRequestHostname()
		elif self.what is self.PORT:
			return str(self.request.host.port)
		elif self.what is self.METHOD:
			return self.request.method
		elif self.what is self.PATH:
			return self.request.path
		elif self.what is self.REMOTEADRESS:
			return self.request.client.ip
		elif self.what is self.REMOTEPORT:
			return str(self.request.client.port)
		elif self.what is self.REMOTETYPE:
			return self.request.client.type
		elif self.what is self.URI:
			return self.request.uri
		else:
			return "N/A"
