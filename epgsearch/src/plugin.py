# for localized messages  	 
from . import _

from enigma import eServiceCenter

# Config
from Components.config import config, ConfigSet, ConfigSubsection, ConfigText

config.plugins.epgsearch = ConfigSubsection()
config.plugins.epgsearch.history = ConfigSet(choices = [])
# XXX: configtext is more flexible but we cannot use this for a (not yet created) gui config
config.plugins.epgsearch.encoding = ConfigText(default = 'ISO8859-15', fixed_size = False)

# Plugin
from EPGSearch import EPGSearch, EPGSearchEPGSelection, EPGSelectionInit

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# Autostart
def autostart(reason, **kwargs):
	if "session" in kwargs:
		try:
			# for blue key activating in EPGSelection
			EPGSelectionInit()
		except:
			pass

# Mainfunction
def main(session, *args, **kwargs):
	s = session.nav.getCurrentService()
	info = s.info()
	event = info.getEvent(0) # 0 = now, 1 = next
	name = event and event.getEventName() or ''
	session.open(EPGSearch, name, False)

# Event Info
def eventinfo(session, *args, **kwargs):
	ref = session.nav.getCurrentlyPlayingServiceReference()
	session.open(EPGSearchEPGSelection, ref, True)

# Movielist
def movielist(session, service, **kwargs):
	serviceHandler = eServiceCenter.getInstance()
	info = serviceHandler.info(service)
	name = info and info.getName(service) or ''

	session.open(EPGSearch, name)

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			where = PluginDescriptor.WHERE_SESSIONSTART,
			fnc = autostart,
		),
		PluginDescriptor(
			name = "EPGSearch",
			description = _("Search EPG"),
			where = PluginDescriptor.WHERE_PLUGINMENU,
			fnc = main,
		),
		PluginDescriptor(
			name = _("Search EPG..."),
			where = PluginDescriptor.WHERE_EVENTINFO,
			fnc = eventinfo,
		),
		PluginDescriptor(
			name = "EPGSearch",
			description = _("Search EPG..."),
			where = PluginDescriptor.WHERE_MOVIELIST,
			fnc = movielist,
		),
	]
