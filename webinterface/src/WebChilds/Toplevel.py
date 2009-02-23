from twisted.web2 import resource, static, responsecode, http, http_headers
from twisted.python import util

from Components.config import config

from Plugins.Extensions import WebInterface
from Screenpage import ScreenPage
from FileStreamer import FileStreamer
from Screengrab import GrabResource
from IPKG import IPKGResource
from PlayService import ServiceplayerResource
from Uploader import UploadResource
from ServiceListSave import ServiceList
from RedirecToCurrentStream import RedirecToCurrentStreamResource

from External.__init__ import importExternalModules
externalChildren = []

def addExternalChild(child):
	externalChildren.append(child)

class Toplevel(resource.Resource):
	addSlash = True
	def __init__(self,session):
		self.session = session
		resource.Resource.__init__(self)

		self.putChild("web", ScreenPage(self.session,util.sibpath(WebInterface.__file__, "web"))) # "/web/*"
		self.putChild("web-data", static.File(util.sibpath(WebInterface.__file__, "web-data")))
		self.putChild("file", FileStreamer())
		self.putChild("grab", GrabResource())
		self.putChild("ipkg", IPKGResource())
		self.putChild("play", ServiceplayerResource(self.session))
		self.putChild("wap", RedirectorResource("/web/wap/"))# shorten and simplify url to wap-pages
		self.putChild("upload", UploadResource())
		self.putChild("servicelist", ServiceList(self.session))
		self.putChild("streamcurrent", RedirecToCurrentStreamResource(session))
			
		if config.plugins.Webinterface.includemedia.value is True:
			self.putChild("media", static.File("/media"))
			self.putChild("hdd", static.File("/media/hdd"))
			
		
		importExternalModules()

		for child in externalChildren:
			if len(child) == 2:
				self.putChild(child[0], child[1])


	def render(self, req):
		fp = open(util.sibpath(WebInterface.__file__, "web-data/tpl/default")+"/index.html")
		s = fp.read()
		fp.close()
		return http.Response(responsecode.OK, {'Content-type': http_headers.MimeType('text', 'html')},stream=s)

	def locateChild(self, request, segments):
		print "[WebIf]", request.remoteAddr.host,request.method,request.path,request.args
		return resource.Resource.locateChild(self, request, segments)

class RedirectorResource(resource.Resource):
	"""
		this class can be used to redirect a request to a specified uri
	"""
	def __init__(self,uri):
		self.uri = uri
		resource.Resource.__init__(self)
	def render(self, req):
		return http.RedirectResponse(self.uri)

