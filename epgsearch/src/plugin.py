# Config
from Components.config import config, ConfigSet, ConfigSubsection, ConfigText

config.plugins.epgsearch = ConfigSubsection()
config.plugins.epgsearch.history = ConfigSet(choices = [])
# XXX: configtext is more flexible but we cannot use this for a (not yet created) gui config
config.plugins.epgsearch.history = ConfigText(default = 'ISO8859-15', fixed_size = False)

# Plugin
from EPGSearch import EPGSearch

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# Mainfunction
def main(session, *args, **kwargs):
	session.open(EPGSearch)

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			name="EPGSearch",
			description = _("Search the EPG"),
			where = PluginDescriptor.WHERE_PLUGINMENU,
			fnc = main,
		),
		PluginDescriptor(
			name="EPGSearch",
			description = _("Search the EPG"),
			where = PluginDescriptor.WHERE_EVENTINFO,
			fnc = main,
		),
	]
