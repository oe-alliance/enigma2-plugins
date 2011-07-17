from twisted.web import resource, server
from ServiceReference import ServiceReference

class RedirecToCurrentStreamResource(resource.Resource):
	"""
		used to redirect the client to the streamproxy with the current service tuned on TV
	"""
	def __init__(self, session):
		resource.Resource.__init__(self)
		self.session = session

	def render(self, request):
		currentServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
		if currentServiceRef is not None:
			sref = currentServiceRef.toString()
		else:
			sref = "N/A"

		request.redirect("http://%s:8001/%s" % (request.getHost().host, sref))
		request.finish()
		return server.NOT_DONE_YET

