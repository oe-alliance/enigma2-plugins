from twisted.web2 import resource, static, responsecode, http, http_headers
from twisted.python import util

from Components.config import config

from Plugins.Extensions import WebInterface
from Screenpage import ScreenPage
from MovieStreamer import MovieStreamer
from Screengrab import GrabResource
from IPKG import IPKGResource
from PlayService import ServiceplayerResource

class Toplevel(resource.Resource):
    addSlash = True
    def __init__(self,session):
        self.session = session
        resource.Resource.__init__(self)
        
        self.putChild("web",ScreenPage(self.session,util.sibpath(WebInterface.__file__, "web"))) # "/web/*"
        self.putChild("webdata",static.File(util.sibpath(WebInterface.__file__, "web-data"))) # FIXME: web-data appears as webdata
        self.putChild("movie",MovieStreamer())
        self.putChild("grab",GrabResource())
        self.putChild("ipkg",IPKGResource())
        self.putChild("play",ServiceplayerResource(self.session))
        self.putChild("wap",RedirectorResource("/web/wap/"))# shorten and simplify url to wap-pages
        
        if config.plugins.Webinterface.includehdd.value:
            self.putChild("hdd",static.File("/hdd"))
        
    def render(self, req):
        fp = open(util.sibpath(WebInterface.__file__, "web-data")+"/index.html")
        s = fp.read()
        fp.close()
        return http.Response(responsecode.OK, {'Content-type': http_headers.MimeType('text', 'html')},stream=s)

    def locateChild(self, request, segments):
        print "[WebIf]",request.remoteAddr.host,request.method,request.path,request.args
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

