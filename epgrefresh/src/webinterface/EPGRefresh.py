from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
from Plugins.Extensions.EPGRefresh.EPGRefreshResource import \
		EPGRefreshStartRefreshResource, \
		EPGRefreshAddRemoveServiceResource, \
		EPGRefreshListServicesResource

root = EPGRefreshListServicesResource()
root.putChild("refresh", EPGRefreshStartRefreshResource())
root.putChild("add", EPGRefreshAddRemoveServiceResource(EPGRefreshAddRemoveServiceResource.TYPE_ADD))
root.putChild("del", EPGRefreshAddRemoveServiceResource(EPGRefreshAddRemoveServiceResource.TYPE_DEL))
addExternalChild( ("epgrefresh", root) )

