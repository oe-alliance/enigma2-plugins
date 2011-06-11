# Plugin definition
from Plugins.Plugin import PluginDescriptor

from Components.PluginComponent import plugins
from Tools.BoundFunction import boundFunction
from Screens.InfoBarGenerics import InfoBarPlugins, InfoBarMoviePlayerSummarySupport
from Screens.ChannelSelection import ChannelSelection
from Screens.InfoBar import InfoBar, MoviePlayer
import inspect

MODE_OFF = False
MODE_ON = True
MODE_MOVIEPLAYER = 2

# This plugin consists of 4 "steps" which serve their own purpose and if combined allow access to both the service list and plugins requiring the service list from within the movie player.
# Each of these steps are enclosed in their own sections and their purpose is explained.

# Step 1: change way used to determine if plugins requiring service list should be shown
# Base implementation uses isinstance(self, InfoBarChannelSelection) which we do not want (to implement) for various reasons.
# Instead we we check for the instance variable "servicelist".
#
# Additionally, we inject our "fake" plugin only if the (original?) movie player is running.
#
# Doing so should not affect behavior if plugin is disabled, though we still overwrite these functions to make things easier to manage internally.
def InfoBarPlugins_getPluginList(self, *args, **kwargs):
	l = []
	showSlistPlugins = hasattr(self, 'servicelist')
	for p in plugins.getPlugins(where = PluginDescriptor.WHERE_EXTENSIONSMENU):
		args = inspect.getargspec(p.__call__)[0]
		if len(args) == 1 or len(args) == 2 and showSlistPlugins:
			l.append(((boundFunction(self.getPluginName, p.name), boundFunction(self.runPlugin, p), lambda: True), None, p.name))
	# this is the/a movie player, add our fake plugin
	if isinstance(self, InfoBarMoviePlayerSummarySupport):
		l.append(((boundFunction(self.getPluginName, "EPG"), boundFunction(self.runPlugin, entry), lambda: True), None, "EPG"))
	l.sort(key = lambda e: e[2]) # sort by name
	return l
def InfoBarPlugins_runPlugin(self, plugin, *args, **kwargs):
	if hasattr(self, 'servicelist'):
		plugin(session = self.session, servicelist = self.servicelist)
	else:
		plugin(session = self.session)
InfoBarPlugins.getPluginList = InfoBarPlugins_getPluginList
InfoBarPlugins.runPlugin = InfoBarPlugins_runPlugin

# Step 2: Overwrite some ChannelSelection code to be able to interject channel selection
# TODO: right now we only block channel selection, this can be improved by allowing to switch channels
#
# Doing so should not affect behavior if plugin is disabled, though we still overwrite these functions to make things easier to manage internally.
baseChannelSelection_channelSelected = None
def ChannelSelection_channelSelected(self, *args, **kwargs):
	if hasattr(self, 'secretMovieMode') and self.secretMovieMode:
		# XXX: better would be to invoke the movie player quit handler and eventually (if not canceled) zap
		return
	baseChannelSelection_channelSelected(self, *args, **kwargs)
baseChannelSelection_channelSelected = ChannelSelection.channelSelected
ChannelSelection.channelSelected = ChannelSelection_channelSelected

baseChannelSelection_close = None
def ChannelSelection_close(self, *args, **kwargs):
	if hasattr(self, 'secretMovieMode') and self.secretMovieMode != MODE_MOVIEPLAYER:
		self.secretMovieMode = MODE_OFF
	baseChannelSelection_close(self, *args, **kwargs)
baseChannelSelection_close = ChannelSelection.close
ChannelSelection.close = ChannelSelection_close

baseChannelSelection_zap = None
def ChannelSelection_zap(self, *args, **kwargs):
	if hasattr(self, 'secretMovieMode') and self.secretMovieMode:
		# XXX: better would be to invoke the movie player quit handler and eventually (if not canceled) zap
		return
	baseChannelSelection_zap(self, *args, **kwargs)
baseChannelSelection_zap = ChannelSelection.zap
ChannelSelection.zap = ChannelSelection_zap

# Step 3: Plugin which allows access to service list from extension menu (and possibly later on from plugin menu)
# Absolutely no effect on its own.
def entry(session = None, servicelist = None):
	# XXX: session.current_dialog is the movie player (or infobar if ran from "regular" extension menu)
	if not session: return
	if not servicelist:
		servicelist = InfoBar.instance.servicelist
	if hasattr(servicelist, 'secretMovieMode') and servicelist.secretMovieMode != MODE_MOVIEPLAYER:
		servicelist.secretMovieMode = MODE_ON
	session.execDialog(servicelist)

# Step 4: Modify standard movie player to keep a reference to the service list (taken from the info bar)
# Basically no effect on its own.
baseMoviePlayer___init__ = None
def MoviePlayer___init__(self, *args, **kwargs):
	baseMoviePlayer___init__(self, *args, **kwargs)
	self.servicelist = InfoBar.instance.servicelist
	self.servicelist.secretMovieMode = MODE_MOVIEPLAYER
baseMoviePlayer___init__ = MoviePlayer.__init__
MoviePlayer.__init__ = MoviePlayer___init__

baseMoviePlayer_close = None
def MoviePlayer_close(self, *args, **kwargs):
	self.servicelist.secretMovieMode = MODE_OFF
	baseMoviePlayer_close(self, *args, **kwargs)
baseMoviePlayer_close = MoviePlayer.close
MoviePlayer.close = MoviePlayer_close

# Autostart
def autostart(reason, **kwargs):
	if reason == 0:
		pass # TODO: anything to do here?

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			where = PluginDescriptor.WHERE_AUTOSTART,
			fnc = autostart,
			needsRestart = True,
		),
	]
