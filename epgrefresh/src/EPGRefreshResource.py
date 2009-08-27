from twisted.web2 import http, http_headers, resource, responsecode
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

		result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n
			<e2simplexmlresult>\n
				<e2state>%s</e2state>\n
				<e2statetext>%s</e2statetext>\n
			</e2simplexmlresult>
			""" % ('true' if res else 'false', output)

		XML_HEADER = {'Content-type': http_headers.MimeType('application', 'xhtml+xml', (('charset', 'UTF-8'),))}
		return http.Response(responsecode.OK, XML_HEADER, stream = result)

