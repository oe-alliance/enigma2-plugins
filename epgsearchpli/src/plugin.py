# for localized messages  	 
from . import _

from enigma import eServiceCenter
from Components.config import config

# Plugin
from EPGSearch import EPGSearch, EPGSearchEPGSelection, EPGSelectionInit

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# Autostart
def autostart(reason, **kwargs):
	if reason == 0:
		try:
			# for blue key activating in EPGSelection
			EPGSelectionInit()
		except Exception:
			pass

# Mainfunction
def main(session, *args, **kwargs):
	s = session.nav.getCurrentService()
	if s:
		info = s.info()
		event = info.getEvent(0) # 0 = now, 1 = next
		name = event and event.getEventName() or ''
		session.open(EPGSearch, name, False)
	else:
		session.open(EPGSearch)

# Event Info
def eventinfo(session, *args, **kwargs):
	ref = session.nav.getCurrentlyPlayingServiceReference()
	session.open(EPGSearchEPGSelection, ref, True)

# EPG Further Options
def epgfurther(session, selectedevent, **kwargs):
	session.open(EPGSearch, selectedevent[0].getEventName())

# Movielist
def movielist(session, service, **kwargs):
	serviceHandler = eServiceCenter.getInstance()
	info = serviceHandler.info(service)
	name = info and info.getName(service) or ''

	session.open(EPGSearch, name)

def Plugins(**kwargs):
	path = [
		PluginDescriptor(
			where = PluginDescriptor.WHERE_AUTOSTART,
			fnc = autostart,
			needsRestart = False,
		),
		PluginDescriptor(
			name = "EPGSearch",
			# TRANSLATORS: description of EPGSearch in PluginBrowser
			description = _("Search EPG"),
			where = PluginDescriptor.WHERE_PLUGINMENU,
			fnc = main,
			needsRestart = False,
		),
		PluginDescriptor(
			# TRANSLATORS: EPGSearch title in EventInfo dialog (requires the user to select an event to search for)
			name = _("search EPG..."),
			where = PluginDescriptor.WHERE_EVENTINFO,
			fnc = eventinfo,
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
	if config.plugins.epgsearch.show_in_furtheroptionsmenu.value:
		path.append(PluginDescriptor( name = _("Search event in EPG"), where = PluginDescriptor.WHERE_EVENTINFO, fnc = epgfurther,needsRestart = False,))
	return path
