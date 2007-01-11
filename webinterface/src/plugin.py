from Plugins.Plugin import PluginDescriptor

sessions = [ ]

def startWebserver():
	from twisted.internet import reactor
	from twisted.web2 import server, channel, static, resource, stream, http_headers, responsecode, http
	from twisted.python import util
	import webif

	class ScreenPage(resource.Resource):
		def __init__(self, path):
			self.path = path
			
		def render(self, req):
			global sessions
			if sessions == [ ]:
				return http.Response(200, stream="please wait until enigma has booted")

			class myProducerStream(stream.ProducerStream):
				closed_callback = None

				def close(self):
					if self.closed_callback:
						self.closed_callback()
					stream.ProducerStream.close(self)

			s = myProducerStream()
			webif.renderPage(s, self.path, req, sessions[0])  # login?

			return http.Response(stream=s)

		def locateChild(self, request, segments):
			path = '/'.join(["web"] + segments)
			if path[-1:] == "/":
				path += "index.html"

			path += ".xml"
			return ScreenPage(path), ()

	class Toplevel(resource.Resource):
		addSlash = True

		def render(self, req):
			return http.Response(responsecode.OK, {'Content-type': http_headers.MimeType('text', 'html')},
				stream='Hello! You want go to <a href="/web/">OSD</a> instead.')

		child_web = ScreenPage("/") # "/web"
		child_hdd = static.File("/hdd")
		child_webdata = static.File(util.sibpath(__file__, "web-data")) # FIXME: web-data appears as webdata

	site = server.Site(Toplevel())

	reactor.listenTCP(80, channel.HTTPFactory(site))

def autostart(reason, **kwargs):
	if "session" in kwargs:
		global sessions
		sessions.append(kwargs["session"])
		return

	if reason == 0:
		try:
			startWebserver()
		except ImportError:
			print "twisted not available, not starting web services"

def Plugins(**kwargs):
	return PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart)
