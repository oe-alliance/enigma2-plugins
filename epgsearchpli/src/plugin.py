# for localized messages  
from . import _
from enigma import eServiceCenter
from Screens.EpgSelection import EPGSelection
from Components.EpgList import EPG_TYPE_SINGLE, EPG_TYPE_MULTI
from Components.ActionMap import ActionMap
from EPGSearch import EPGSearch, EPGSearchEPGSelection
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Components.config import config

# Overwrite EPGSelection.__init__ with our modified one
baseEPGSelection__init__ = None
def EPGSelectionInit():
	global baseEPGSelection__init__
	if baseEPGSelection__init__ is None:
		baseEPGSelection__init__ = EPGSelection.__init__
	EPGSelection.__init__ = EPGSearchSelection__init__
	EPGSelection.CallbackChoiceAction = CallbackChoiceAction

# Modified EPGSelection __init__
def EPGSearchSelection__init__(self, session, service, zapFunc=None, eventid=None, bouquetChangeCB=None, serviceChangeCB=None, parent=None):
	baseEPGSelection__init__(self, session, service, zapFunc, eventid, bouquetChangeCB, serviceChangeCB, parent)
	if self.type != EPG_TYPE_MULTI and config.plugins.epgsearch.add_search_to_epg.value:
		def bluePressed():
			if config.plugins.epgsearch.type_button_blue.value == "0":
				cur = self["list"].getCurrent()
				if cur[0] is not None:
					name = cur[0].getEventName()
				else:
					name = ''
				self.session.open(EPGSearch, name, False)
			elif config.plugins.epgsearch.type_button_blue.value == "1":
				list = [
				(_("Search"), "search"),
				(_("Select channel"), "standard"),
				]
				dlg = self.session.openWithCallback(self.CallbackChoiceAction, ChoiceBox, title= _("Select action:"), list = list)
				dlg.setTitle(_("Choice list EPGSearch"))
		self["epgsearch_actions"] = ActionMap(["EPGSelectActions"],
				{
					"blue": bluePressed,
				})
		if config.plugins.epgsearch.type_button_blue.value == "0":
			self["key_blue"].text = _("Search")
		elif config.plugins.epgsearch.type_button_blue.value == "1":
			self["key_blue"].text = _("Choice list")

def CallbackChoiceAction(self, ret):
	ret = ret and ret[1]
	if ret:
		if ret == "search":
			try:
				cur = self["list"].getCurrent()
				if cur[0] is not None:
					name = cur[0].getEventName()
				else:
					name = ''
				self.session.open(EPGSearch, name, False)
			except:
				pass
		elif ret == "standard":
			try:
				self.blueButtonPressed()
			except:
				pass

# Autostart
def autostart(reason, **kwargs):
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
		event = info and info.getEvent(0) # 0 = now, 1 = next
		name = event and event.getEventName() or ''
		session.open(EPGSearch, name, False)
	else:
		session.open(EPGSearch)

# Channel context menu
def channelscontext(session, service=None, **kwargs):
	serviceHandler = eServiceCenter.getInstance()
	info = serviceHandler.info(service)
	event = info.getEvent(service)
	if event:
		name = info and event.getEventName() or ''
		session.open(EPGSearch, name)

# Event Info
def eventinfo(session, eventName="", **kwargs):
	if eventName != "":
		session.open(EPGSearch, eventName, False)
	else:
		ref = session.nav.getCurrentlyPlayingServiceReference()
		if ref:
			session.open(EPGSearchEPGSelection, ref, True)

# EPG Further Options
def epgfurther(session, selectedevent, **kwargs):
	session.open(EPGSearch, selectedevent[0].getEventName())

# Movielist
def movielist(session, service, **kwargs):
	serviceHandler = eServiceCenter.getInstance()
	info = serviceHandler.info(service)
	name = info and info.getName(service) or ''
	name = name.split(".")[0].strip()
	session.open(EPGSearch, name)

def Plugins(**kwargs):
	path = [
		PluginDescriptor(
			where = [PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART],
			fnc = autostart,
		),
		PluginDescriptor(
			name = _("EPGSearch"),
			description = _("Search EPG by title event"),
			where = PluginDescriptor.WHERE_PLUGINMENU,
			fnc = main,
			icon = "epg.png",
			needsRestart = False,
		),
		PluginDescriptor(
			name = _("search EPG..."),
			where = PluginDescriptor.WHERE_EVENTINFO,
			fnc = eventinfo,
			needsRestart = False,
		),
		PluginDescriptor(
			description = _("search EPG"),
			where = PluginDescriptor.WHERE_MOVIELIST,
			fnc = movielist,
			needsRestart = False,
		),
	]
	if config.plugins.epgsearch.search_in_channelmenu.value:
		path.append(PluginDescriptor(name = _("Search event in EPG"), where=PluginDescriptor.WHERE_CHANNEL_CONTEXT_MENU, needsRestart = False, fnc=channelscontext))
	if config.plugins.epgsearch.show_in_furtheroptionsmenu.value:
		path.append(PluginDescriptor(name = _("Search event in EPG"), where = PluginDescriptor.WHERE_EVENTINFO, fnc = epgfurther, needsRestart = False))
	return path
