from __future__ import absolute_import
# Plugin
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor
# Webinterface
from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
from Plugins.Extensions.WebInterface.WebChilds.Screenpage import ScreenPage
# Twisted
from twisted.web import static
from twisted.python import util
#
from . import _
from .WebChilds.WebUploadResource import WebUploadResource
from .WebScreens.BouquetEditorWebScreens import BouquetEditorWebScreen
from .WebScreens.AdditionalWebScreens import AdditionalWebScreen
from enigma import eEnv

if hasattr(static.File, 'render_GET'):
	class File(static.File):
		def render_POST(self, request):
			return self.render_GET(request)
else:
	File = static.File


def autostart(reason, **kwargs):
	if "session" in kwargs:
		session = kwargs["session"]
		from Plugins.Extensions.WebInterface import webif
		webif.BouquetEditorWebScreen = BouquetEditorWebScreen
		webif.AdditionalWebScreen = AdditionalWebScreen
		root = File(eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/WebBouquetEditor/web-data"))
		root.putChild(b"web", ScreenPage(session, util.sibpath(__file__, "web"), True))
		root.putChild(b'tmp', File('/tmp'))
		root.putChild(b"uploadfile", WebUploadResource(session))
		addExternalChild(("bouqueteditor", root, "BouquetEditor", 1, True))


def Plugins(**kwargs):
	list = [PluginDescriptor(name="WebBouquetEditor", description=_("WebBouquetEditor"), where=PluginDescriptor.WHERE_SESSIONSTART, fnc=autostart)]
	return list
