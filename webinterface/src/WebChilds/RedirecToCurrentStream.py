from twisted.web2 import resource
from ServiceReference import ServiceReference

class RedirecToCurrentStreamResource(resource.Resource):
	"""
		used to redirect the client to the streamproxy with the current service tuned on TV
	"""
	def __init__(self,session):
		self.session = session
		resource.Resource.__init__(self)

	def render(self, req):
		currentServiceRef = self.session.nav.getCurrentlyPlayingServiceReference()
		if currentServiceRef is not None:
			sref = currentServiceRef.toString()
		else:
			sref = "N/A"
		return http.RedirectResponse("http://%s:8001/%s"%(req.host,sref))

