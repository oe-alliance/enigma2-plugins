from twisted.web2 import http, http_headers, resource, responsecode
from AutoTimer import AutoTimer
from . import _

# pretty basic resource which is just present to have a way to start a
# forced run through the webif
class AutoTimerResource(resource.Resource):
	def __init__(self):
		resource.Resource.__init__(self)

	def render(self, req):
		from plugin import autotimer

		remove = False
		res = False
		if autotimer is None:
			autotimer = AutoTimer()
			remove = True

		if req.args.has_key("parse"):
			ret = autotimer.parseEPG()
			output = _("Found a total of %d matching Events.\n%d Timer were added and %d modified.") % (ret[0], ret[1], ret[2])
			res = True
		else:
			output = "unknown command"

		if remove:
			autotimer.writeXml()
			autotimer = None

		result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n
			<e2simplexmlresult>\n
				<e2state>%s</e2state>\n
				<e2statetext>%s</e2statetext>\n
			</e2simplexmlresult>
			""" % ('true' if res else 'false', output)

		XML_HEADER = {'Content-type': http_headers.MimeType('application', 'xhtml+xml', (('charset', 'UTF-8'),))}
		return http.Response(responsecode.OK, XML_HEADER, stream = result)

