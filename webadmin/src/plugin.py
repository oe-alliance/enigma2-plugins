# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor
from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
from Plugins.Extensions.WebInterface.WebChilds.Screenpage import ScreenPage
from WebChilds.UploadPkg import UploadPkgResource
from WebChilds.UploadText import UploadTextResource
from WebChilds.PKG import PKGResource
from WebChilds.Script import Script
from twisted.web import static
from twisted.python import util
from enigma import eEnv

if hasattr(static.File, 'render_GET'):
	class File(static.File):
		def render_POST(self, request):
			return self.render_GET(request)
else:
	File = static.File


def autostart(reason, **kwargs):
	if reason == 0 and "session" in kwargs:
		session = kwargs["session"]
		root = File(eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/WebAdmin/web-data"))
		root.putChild("web", ScreenPage(session, util.sibpath(__file__, "web"), True))
		root.putChild("mobile", ScreenPage(session, util.sibpath(__file__, "mobile"), True))
		root.putChild('tmp', File('/tmp'))
		root.putChild("uploadtext", UploadTextResource())
		root.putChild("uploadpkg", UploadPkgResource())
		root.putChild("pkg", PKGResource())
		root.putChild("script", Script())
		addExternalChild(("webadmin", root, "WebAdmin", 1, True, "_self"))
			

def Plugins(**kwargs):
	return [PluginDescriptor(name="WebAdmin",
			where=PluginDescriptor.WHERE_SESSIONSTART,
			fnc=autostart)]
