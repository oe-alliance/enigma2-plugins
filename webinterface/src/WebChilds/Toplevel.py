from twisted.web2 import resource, static, responsecode, http, http_headers
from twisted.python import util

from Components.config import config

from Plugins.Extensions import WebInterface
from Screenpage import ScreenPage
from MovieStreamer import MovieStreamer
from Screengrab import GrabResource

class Toplevel(resource.Resource):
    addSlash = True
    def __init__(self,session):
        self.session = session
        resource.Resource.__init__(self)
        
        self.putChild("web",ScreenPage(self.session,util.sibpath(WebInterface.__file__, "web"))) # "/web/*"
        self.putChild("webdata",static.File(util.sibpath(WebInterface.__file__, "web-data"))) # FIXME: web-data appears as webdata
        self.putChild("wap",static.File(util.sibpath(WebInterface.__file__, "wap"))) # static pages for wap
        self.putChild("movie",MovieStreamer())
        self.putChild("grab",GrabResource())
        
        if config.plugins.Webinterface.includehdd.value:
            self.putChild("hdd",static.File("/hdd"))
        
    def render(self, req):
        fp = open(util.sibpath(WebInterface.__file__, "web-data")+"/index.html")
        s = fp.read()
        fp.close()
        return http.Response(responsecode.OK, {'Content-type': http_headers.MimeType('text', 'html')},stream=s)
