# for localized messages
from . import _

from enigma import eServiceCenter

# Configuration
from Components.config import config

# Plugin
from EPGSearch import EPGSearch, EPGSearchEPGSelection

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# Mainfunction
def main(session, *args, **kwargs):
	s = session.nav.getCurrentService()
	if s:
		info = s.info()
		event = info.getEvent(0) # 0 = now, 1 = next
		name = event and event.getEventName() or ''
	else:
		name = self.session.nav.getCurrentlyPlayingServiceReference().toString()
		name = name.split('/')
		name = name[-1]
		name = name.replace('.',' ')
		name = name.split('-')
		name = name[0]
		if name.endswith(' '):
			name = name[:-1]
	if name:
		session.open(EPGSearch, name, False)
	else:
		session.open(EPGSearch)

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

pluginlist = PluginDescriptor(name = _("EPGSearch"), description = _("Search EPG"), where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main, needsRestart = False)

def Plugins(**kwargs):
	l = [
		PluginDescriptor(
			# TRANSLATORS: EPGSearch title in EventInfo dialog (requires the user to select an event to search for)
			name = _("search EPG..."),
			where = PluginDescriptor.WHERE_EVENTINFO,
			fnc = main,
			needsRestart = False,
		),
		PluginDescriptor(
			# TRANSLATORS: EPGSearch title in MovieList (does not require further user interaction)
			description = _("search EPG"),
			where = PluginDescriptor.WHERE_MOVIELIST,
			fnc = movielist,
			needsRestart = False,
		),
	]

	if config.plugins.epgsearch.showinplugins.value:
		l.append(pluginlist)

	return l
