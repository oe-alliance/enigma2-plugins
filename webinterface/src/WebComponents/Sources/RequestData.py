from Components.Sources.Source import Source

class RequestData(Source):
	"""
		a source for requestinformations like the adress that the client requested to reache the box
	"""
	HOST = 0
	PORT = 1
	METHOD = 2
	PATH = 3
	PROTOCOL = 4
	REMOTEADRESS = 5
	REMOTEPORT = 6
	REMOTETYPE = 7
	URI = 8

	def __init__(self, request, what=None):
		Source.__init__(self)
		self.request = request
		self.what = what

	def handleCommand(self, cmd):
		pass

	def getHTML(self, id):
		if self.what is self.HOST:
			host = self.request.getHeader('host')
			if host:
				if host[0]=='[':
					return host.split(']',1)[0] + "]"
				return host.split(':', 1)[0].encode('ascii')
			return self.request.getHost().host.encode('ascii')
		elif self.what is self.PORT:
			return str(self.request.host.port)
		elif self.what is self.METHOD:
			return self.request.method
		elif self.what is self.PATH:
			return self.request.path
		elif self.what is self.PROTOCOL:
			return "https" if self.request.isSecure() else "http"
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
