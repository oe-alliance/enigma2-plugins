from twisted.web import resource, http, server, static

from Plugins.Extensions.WebInterface import webif
import six

from os import path as os_path

"""
	define all files in /web to send no XML-HTTP-Headers here
	all files listed here will get an Content-Type: application/xhtml+xml charset: UTF-8
"""
AppTextHeaderFiles = frozenset(('stream.m3u.xml', 'ts.m3u.xml', 'streamcurrent.m3u.xml', 'movielist.m3u.xml', 'services.m3u.xml', ))

"""
Actualy, the TextHtmlHeaderFiles should contain the updates.html.xml, but the IE then
has problems with six.text_type-characters
"""
TextHtmlHeaderFiles = frozenset(('wapremote.xml', 'stream.xml', ))

"""
	define all files in /web to send no XML-HTTP-Headers here
	all files listed here will get an Content-Type: text/html charset: UTF-8
"""
NoExplicitHeaderFiles = frozenset(('getpid.xml', 'tvbrowser.xml', ))

"""
	define all files in /web with a text/javascript header
"""
TextJavascriptHeaderFiles = frozenset(('strings.js.xml', ))

class ScreenPage(resource.Resource):
	def __init__(self, session, path, addSlash=False):
		resource.Resource.__init__(self)

		self.session = session
		self.path = path
		self.addSlash = addSlash

	def render(self, request):
		path = self.path
		if os_path.isfile(path):
			lastComponent = path.split('/')[-1]

			# Set the Header according to what's requested
			if lastComponent in AppTextHeaderFiles:
				request.setHeader('Content-Type', 'application/text')
			elif lastComponent in TextHtmlHeaderFiles or (path.endswith(".html.xml") and lastComponent != "updates.html.xml"):
				request.setHeader('Content-Type', 'text/html; charset=UTF-8')
			elif lastComponent in TextJavascriptHeaderFiles:
				request.setHeader('Content-Type', 'text/javascript; charset=UTF-8')
			elif lastComponent not in NoExplicitHeaderFiles:
				request.setHeader('Content-Type', 'application/xhtml+xml; charset=UTF-8')
			# now go and write the Output
			# request.finish() is called inside webif.py (requestFinish() which is called via renderPage())
			webif.renderPage(request, path, self.session) # login?
			request.setResponseCode(http.OK)

		elif os_path.isdir(path) and self.addSlash is True:
			uri = "%s/" % (request.path)
			request.redirect(uri)
			return ""

		else:
			return resource.ErrorPage(http.NOT_FOUND, "Error 404 - Page not found", "The requested resource is not available").render(request)

		return server.NOT_DONE_YET

	def getChild(self, path, request):
		path = "%s/%s" % (self.path, path)

		if path[-1] == "/":
			path += "index.html"

		path += ".xml"
		return ScreenPage(self.session, path)

