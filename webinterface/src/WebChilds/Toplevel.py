from twisted.web import resource, static
from twisted.python import util

from Components.config import config

from Plugins.Extensions.WebInterface import __file__ 
from Screenpage import ScreenPage
from FileStreamer import FileStreamer
from Screengrab import GrabResource
from IPKG import IPKGResource
from PlayService import ServiceplayerResource
#from Uploader import UploadResource
from ServiceListSave import ServiceList
from RedirecToCurrentStream import RedirecToCurrentStreamResource

from External.__init__ import importExternalModules
externalChildren = []

def addExternalChild(child):
	externalChildren.append(child)

def getToplevel(session):
	root = static.File(util.sibpath(__file__, "web-data/tpl/default"))
	
	root.putChild("web", ScreenPage(session, util.sibpath(__file__, "web"), True) ) # "/web/*"
	root.putChild("web-data", static.File(util.sibpath(__file__, "web-data")))
	root.putChild("file", FileStreamer())
	root.putChild("grab", GrabResource())
	root.putChild("ipkg", IPKGResource())
	root.putChild("play", ServiceplayerResource(session))
	root.putChild("wap", RedirectorResource("/mobile/"))
	root.putChild("mobile", ScreenPage(session, util.sibpath(__file__, "mobile"), True) )
	#root.putChild("upload", UploadResource())
	root.putChild("servicelist", ServiceList(session))
	root.putChild("streamcurrent", RedirecToCurrentStreamResource(session))
		
	if config.plugins.Webinterface.includemedia.value is True:
		root.putChild("media", static.File("/media"))
		root.putChild("hdd", static.File("/media/hdd"))
		
	
	importExternalModules()

	for child in externalChildren:
		if len(child) == 2:
			root.putChild(child[0], child[1])
	
	return root
		
class RedirectorResource(resource.Resource):
	"""
		this class can be used to redirect a request to a specified uri
	"""
	def __init__(self, uri):
		self.uri = uri
		resource.Resource.__init__(self)
	
	def render(self, request):
		request.redirect(self.uri)
		request.finish()

