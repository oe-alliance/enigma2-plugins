from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
from Plugins.Extensions.EPGRefresh.EPGRefreshResource import \
		EPGRefreshStartRefreshResource, \
		EPGRefreshAddRemoveServiceResource, \
		EPGRefreshListServicesResource, \
		EPGRefreshChangeSettingsResource, \
		EPGRefreshSettingsResource, \
		EPGRefreshPreviewServicesResource, \
		API_VERSION

root = EPGRefreshListServicesResource()
root.putChild("refresh", EPGRefreshStartRefreshResource())
root.putChild("add", EPGRefreshAddRemoveServiceResource(EPGRefreshAddRemoveServiceResource.TYPE_ADD))
root.putChild("del", EPGRefreshAddRemoveServiceResource(EPGRefreshAddRemoveServiceResource.TYPE_DEL))
root.putChild("set", EPGRefreshChangeSettingsResource())
root.putChild("get", EPGRefreshSettingsResource())
root.putChild("preview", EPGRefreshPreviewServicesResource())
addExternalChild( ("epgrefresh", root, "EPGRefresh-Plugin", API_VERSION) )

