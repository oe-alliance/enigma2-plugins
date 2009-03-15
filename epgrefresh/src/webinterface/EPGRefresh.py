from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
from Plugins.Extensions.EPGRefresh.EPGRefreshResource import EPGRefreshResource

addExternalChild( ("epgrefresh", EPGRefreshResource()) )

