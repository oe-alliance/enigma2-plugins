from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
from Plugins.Extensions.AutoTimer.AutoTimerResource import AutoTimerDoParseResource, \
	AutoTimerListAutoTimerResource, AutoTimerAddOrEditAutoTimerResource, \
	AutoTimerRemoveAutoTimerResource

root = AutoTimerListAutoTimerResource()
root.putChild('parse', AutoTimerDoParseResource())
root.putChild('remove', AutoTimerRemoveAutoTimerResource())
root.putChild('edit', AutoTimerAddOrEditAutoTimerResource())
addExternalChild( ("autotimer", root ) )

