from __future__ import absolute_import
from twisted.web import resource, static
from twisted.python import util

from Components.config import config

from .Screenpage import ScreenPage
from .FileStreamer import FileStreamer
from .Screengrab import GrabResource
from .IPKG import IPKGResource
from .PlayService import ServiceplayerResource
from .Uploader import UploadResource
from .ServiceListSave import ServiceList
from .RedirecToCurrentStream import RedirecToCurrentStreamResource
from Tools.Directories import resolveFilename, SCOPE_MEDIA

from .External.__init__ import importExternalModules
externalChildren = []

"""
	.htc Files for IE Fixes need a certain Content-Type
"""
import mimetypes
mimetypes.add_type('text/x-component', '.htc')
mimetypes.add_type('text/cache-manifest', '.appcache')
mimetypes.add_type('video/MP2T', '.ts')
static.File.contentTypes = static.loadMimeTypes()

if hasattr(static.File, 'render_GET'):
	class File(static.File):
		def render_POST(self, request):
			return self.render_GET(request)
else:
	File = static.File


def addExternalChild(child):
	externalChildren.append(child)


def getToplevel(session):
	root = File(util.sibpath(__file__, "../web-data/tpl/default"))

	root.putChild(b"web", ScreenPage(session, util.sibpath(__file__, "../web"), True))  # "/web/*"
	root.putChild(b"web-data", File(util.sibpath(__file__, "../web-data")))
	root.putChild(b"file", FileStreamer())
	root.putChild(b"grab", GrabResource())
	res = IPKGResource()
	root.putChild(b"opkg", res)
	root.putChild(b"ipkg", res)
	root.putChild(b"play", ServiceplayerResource(session))
	root.putChild(b"wap", RedirectorResource("/mobile/"))
	root.putChild(b"mobile", ScreenPage(session, util.sibpath(__file__, "../mobile"), True))
	root.putChild(b"m", ScreenPage(session, util.sibpath(__file__, "../m"), True))
	root.putChild(b"upload", UploadResource())
	root.putChild(b"servicelist", ServiceList(session))
	root.putChild(b"streamcurrent", RedirecToCurrentStreamResource(session))

	if config.plugins.Webinterface.includemedia.value is True:
		root.putChild(b"media", File(resolveFilename(SCOPE_MEDIA)))
		root.putChild(b"hdd", File(resolveFilename(SCOPE_MEDIA, "hdd")))

	importExternalModules()

	for child in externalChildren:
		if len(child) > 1:
			root.putChild(child[0].encode() if isinstance(child[0], str) else child[0], child[1])

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
