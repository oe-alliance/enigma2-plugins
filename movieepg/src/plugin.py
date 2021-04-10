from __future__ import absolute_import
# Plugin definition
from Plugins.Plugin import PluginDescriptor

from Components.PluginComponent import plugins
from Tools.BoundFunction import boundFunction
from Screens.InfoBarGenerics import InfoBarPlugins, InfoBarMoviePlayerSummarySupport, InfoBarChannelSelection
from Screens.ChannelSelection import ChannelSelection
from Screens.InfoBar import InfoBar, MoviePlayer
from Screens.MessageBox import MessageBox
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigYesNo
from operator import attrgetter
import inspect

config.plugins.movieepg = ConfigSubsection()
config.plugins.movieepg.show_epg_entry = ConfigSelection(choices=[
		("never", _("Never")),
		("movie", _("Movie Player")),
		("always", _("always")),
	], default = "movie"
)
config.plugins.movieepg.show_servicelist_plugins_in_movieplayer = ConfigYesNo(default = True)

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
	showSlistPlugins = (config.plugins.movieepg.show_servicelist_plugins_in_movieplayer.value and hasattr(self, 'servicelist')) or isinstance(self, InfoBarChannelSelection)
	for p in plugins.getPlugins(where = PluginDescriptor.WHERE_EXTENSIONSMENU):
		args = inspect.getargspec(p.__call__)[0]
		if len(args) == 1 or len(args) == 2 and showSlistPlugins:
			l.append(p)
	l.sort(key=attrgetter('weight', 'name')) # sort first by weight, then by name

	# "tranform" into weird internal format
	l = [((boundFunction(self.getPluginName, p.name), boundFunction(self.runPlugin, p), lambda: True), None, p.name) for p in l]

	# add fake plugin if show_epg_entry set to "always" or "movie" and this is the movie player
	show_epg_entry = config.plugins.movieepg.show_epg_entry.value
	if show_epg_entry == "always" or show_epg_entry == "movie" and isinstance(self, InfoBarMoviePlayerSummarySupport):
		l.append(((boundFunction(self.getPluginName, "EPG"), boundFunction(self.runPlugin, entry), lambda: True), None, "EPG"))

	return l
def InfoBarPlugins_runPlugin(self, plugin, *args, **kwargs):
	if hasattr(self, 'servicelist'):
		plugin(session = self.session, servicelist = self.servicelist)
	else:
		plugin(session = self.session)
InfoBarPlugins.getPluginList = InfoBarPlugins_getPluginList
InfoBarPlugins.runPlugin = InfoBarPlugins_runPlugin

# Step 2: Overwrite some ChannelSelection code to be able to interject channel selection
#
# Doing so should not affect behavior if plugin is disabled, though we still overwrite these functions to make things easier to manage internally.
def ChannelSelection_close(self, *args, **kwargs):
	if hasattr(self, 'secretMovieMode') and self.secretMovieMode != MODE_MOVIEPLAYER:
		# handles "plugin" close
		self.secretMovieMode = MODE_OFF
	baseChannelSelection_close(self, *args, **kwargs)
baseChannelSelection_close = ChannelSelection.close
ChannelSelection.close = ChannelSelection_close

def ChannelSelection_zap(self, *args, **kwargs):
	if hasattr(self, 'secretMovieMode') and self.secretMovieMode:
		if movieEpgMoviePlayerInstance is not None:
			movieEpgMoviePlayerInstance.lastservice = self.getCurrentSelection()
			movieEpgMoviePlayerInstance.leavePlayer()
		return
	baseChannelSelection_zap(self, *args, **kwargs)
baseChannelSelection_zap = ChannelSelection.zap
ChannelSelection.zap = ChannelSelection_zap

# Step 3: Plugin which allows access to service list from extension menu (and possibly later on from plugin menu)
# Absolutely no effect on its own.
def entry(session = None, servicelist = None):
	# XXX: session.current_dialog is the movie player (or infobar if ran from "regular" extension menu)
	if not session:
		return
	if not servicelist:
		if InfoBar.instance:
			servicelist = InfoBar.instance.servicelist
		else:
			session.open(MessageBox, _("Unable to access InfoBar!\nEPG not available."), MessageBox.TYPE_ERROR)
			return

	if hasattr(servicelist, 'secretMovieMode') and servicelist.secretMovieMode != MODE_MOVIEPLAYER:
		servicelist.secretMovieMode = MODE_ON
	session.execDialog(servicelist)

# Step 4: Modify standard movie player to keep a reference to the service list (taken from the info bar)
# We also save a reference to the movie list here which we use to provide the "standard" close dialog when trying to zap
#
# Basically no effect on its own.
movieEpgMoviePlayerInstance = None
def MoviePlayer___init__(self, *args, **kwargs):
	baseMoviePlayer___init__(self, *args, **kwargs)
	if InfoBar.instance:
		self.servicelist = InfoBar.instance.servicelist
		self.servicelist.secretMovieMode = MODE_MOVIEPLAYER
	global movieEpgMoviePlayerInstance
	movieEpgMoviePlayerInstance = self
baseMoviePlayer___init__ = MoviePlayer.__init__
MoviePlayer.__init__ = MoviePlayer___init__

def MoviePlayer_close(self, *args, **kwargs):
	global movieEpgMoviePlayerInstance
	movieEpgMoviePlayerInstance = None
	if hasattr(self, 'servicelist'):
		self.servicelist.secretMovieMode = MODE_OFF
	baseMoviePlayer_close(self, *args, **kwargs)
baseMoviePlayer_close = MoviePlayer.close
MoviePlayer.close = MoviePlayer_close

def main(session):
	from .MovieEpgSetup import MovieEpgSetup
	session.open(MovieEpgSetup)

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			name="Movie-EPG",
			description=_("Configure Movie-EPG Plugin"),
			where=PluginDescriptor.WHERE_PLUGINMENU,
			fnc=main,
			needsRestart=True, # XXX: force restart for now as I don't think it will work properly without doing so
		),
	]
