from twisted.web import resource, http, server, static

from Plugins.Extensions.WebInterface import webif

import os

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
	def __init__(self, session, path):		
		resource.Resource.__init__(self)
		
		self.session = session
		self.path = path

	def render(self, request):	
		if os.path.isfile(self.path):	
			
# Set the Header according to what's requested								
			if self.path.split("/")[-1] in AppTextHeaderFiles:				
				request.setResponseCode(http.OK)
				request.setHeader('Content-Type', 'application/text')
				
			elif self.path.split("/")[-1] in TextHtmlHeaderFiles or (self.path.endswith(".html.xml") and self.path.split("/")[-1] != "updates.html.xml"):
				request.setResponseCode(http.OK)
				request.setHeader('Content-Type', 'text/html; charset=UTF-8')				
																					
			elif self.path.split("/")[-1] in NoExplicitHeaderFiles:
				request.setResponseCode(http.OK)				
				
			else:
				request.setResponseCode(http.OK)				
				request.setHeader('Content-Type', 'application/xhtml+xml; charset=UTF-8')	

			# now go and write the Output
			# request.finish() is called inside webif.py (requestFinish() which is called via renderPage())			
			webif.renderPage(request, self.path, self.session) # login?		
		
		elif os.path.isdir(self.path):			
			return self.getChild("/", request).render(request)
			
		else:
			request.setResponseCode(http.NOT_FOUND)
			request.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n')
			request.write("<html><head><title>Enigma2 WebControl</title></head><body><h1>404 - Page not found</h1></body></html>")
			request.finish()
				
		return server.NOT_DONE_YET
				

	def getChild(self, path, request):	
		path = "%s/%s" %(self.path, path)
		
		if path[-1:] == "/":
			path += "index.html"
			
		path += ".xml"
		return ScreenPage(self.session, path)

