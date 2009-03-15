from twisted.web2 import resource, responsecode, http
from EPGRefresh import epgrefresh

# pretty basic resource which is just present to have a way to start a
# forced refresh through the webif
class EPGRefreshResource(resource.Resource):
	def __init__(self):
		resource.Resource.__init__(self)

	def render(self, req):
		if req.args.has_key("refresh"):
			# XXX: we assume we already know the session
			epgrefresh.forceRefresh()
			output = "initiated refresh"
		else:
			output = "unknown command"
		return http.Response(responsecode.OK ,stream = output)

