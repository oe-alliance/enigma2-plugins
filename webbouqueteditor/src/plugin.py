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
from WebChilds.WebUploadResource import WebUploadResource
from enigma import eEnv

def autostart(reason, **kwargs):
	if "session" in kwargs:
		session = kwargs["session"]
		root = static.File(eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/WebBouquetEditor/web-data"))
		root.putChild("web", ScreenPage(session, util.sibpath(__file__, "web"), True) )
		root.putChild('tmp', static.File('/tmp'))
		root.putChild("uploadfile",WebUploadResource(session))
		addExternalChild( ("bouqueteditor", root) )

def Plugins(**kwargs):
	list = [PluginDescriptor(name="WebBouquetEditor", description=_("WebBouquetEditor"), where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart)]  
	return list
