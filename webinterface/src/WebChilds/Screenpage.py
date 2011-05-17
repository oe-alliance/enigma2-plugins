from twisted.web import resource, http, server, static

from Plugins.Extensions.WebInterface import webif

from os import path as os_path

"""
	define all files in /web to send no XML-HTTP-Headers here
	all files listed here will get an Content-Type: application/xhtml+xml charset: UTF-8
"""
AppTextHeaderFiles = ['stream.m3u.xml', 'ts.m3u.xml', 'streamcurrent.m3u.xml', 'movielist.m3u.xml', 'services.m3u.xml', ]

"""
 Actualy, the TextHtmlHeaderFiles should contain the updates.html.xml, but the IE then
 has problems with unicode-characters
"""
TextHtmlHeaderFiles = ['wapremote.xml', 'stream.xml', ]

"""
	define all files in /web to send no XML-HTTP-Headers here
	all files listed here will get an Content-Type: text/html charset: UTF-8
"""
NoExplicitHeaderFiles = ['getpid.xml', 'tvbrowser.xml', ]

class ScreenPage(resource.Resource):
	def __init__(self, session, path, addSlash = False):
		resource.Resource.__init__(self)

		self.session = session
		self.path = path
		self.addSlash = addSlash

	def render(self, request):
		path = self.path
		if os_path.isfile(path):
			lastComponent = path.split('/')[-1]

			# Set the Header according to what's requested
			request.setResponseCode(http.OK)
			if lastComponent in AppTextHeaderFiles:
				request.setHeader('Content-Type', 'application/text')
			elif lastComponent in TextHtmlHeaderFiles or (path.endswith(".html.xml") and lastComponent != "updates.html.xml"):
				request.setHeader('Content-Type', 'text/html; charset=UTF-8')
			elif lastComponent not in NoExplicitHeaderFiles:
				request.setHeader('Content-Type', 'application/xhtml+xml; charset=UTF-8')

			# now go and write the Output
			# request.finish() is called inside webif.py (requestFinish() which is called via renderPage())
			webif.renderPage(request, path, self.session) # login?

		elif os_path.isdir(path) and self.addSlash is True:
			return self.getChild("/", request).render(request)

		else:
			request.setResponseCode(http.NOT_FOUND)
			request.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n')
			request.write("<html><head><title>Enigma2 WebControl</title></head><body><h1>404 - Page not found</h1></body></html>")
			request.finish()

		return server.NOT_DONE_YET

	def getChild(self, path, request):
		path = "%s/%s" % (self.path, path)

		if path[-1] == "/":
			path += "index.html"

		path += ".xml"
		return ScreenPage(self.session, path)

