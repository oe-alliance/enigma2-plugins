from Components.Sources.Source import Source
from Components.PluginComponent import plugins
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

class ReadPluginList(Source):
	def __init__(self, session):
		Source.__init__(self)
		self.session = session

	def command(self):
		print "[WebComponents.ReadPluginList] readPluginList"

		plugins.readPluginList(resolveFilename(SCOPE_PLUGINS))
		return ( True, "List of Plugins has been read" )

	result = property(command)
