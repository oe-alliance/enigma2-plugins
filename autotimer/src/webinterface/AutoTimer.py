from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
from Plugins.Extensions.AutoTimer.AutoTimerResource import AutoTimerDoParseResource, \
	AutoTimerListAutoTimerResource

root = AutoTimerListAutoTimerResource()
root.putChild('parse', AutoTimerDoParseResource())
addExternalChild( ("autotimer", root ) )

