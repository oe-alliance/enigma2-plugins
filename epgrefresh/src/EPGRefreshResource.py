from twisted.web import http, resource
from EPGRefresh import epgrefresh

# pretty basic resource which is just present to have a way to start a
# forced refresh through the webif
class EPGRefreshResource(resource.Resource):
	def __init__(self):
		resource.Resource.__init__(self)

	def render(self, req):
		res = False
		if req.args.has_key("refresh"):
			if epgrefresh.forceRefresh():
				output = "initiated refresh"
				res = True
			else:
				output = "could not initiate refresh"
		else:
			output = "unknown command"

		result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
			<e2simplexmlresult>
				<e2state>%s</e2state>
				<e2statetext>%s</e2statetext>
			</e2simplexmlresult>
			""" % ('true' if res else 'false', output)

		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application; xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		
		return result
