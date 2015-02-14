from __future__ import print_function

# Plugin definition
from Plugins.Plugin import PluginDescriptor

from Components.ActionMap import HelpableActionMap
from Components.ChoiceList import ChoiceEntryComponent
from Components.config import config, ConfigSubsection, ConfigEnableDisable
from Components.SystemInfo import SystemInfo
from Components.ParentalControl import parentalControl
from enigma import ePoint, eServiceReference, getDesktop
from Screens.ChannelSelection import ChannelContextMenu, ChannelSelection, ChannelSelectionBase
from Screens.InfoBar import InfoBar, MoviePlayer
from Screens.InfoBarGenerics import InfoBarNumberZap, InfoBarEPG, InfoBarChannelSelection, InfoBarPiP, InfoBarShowMovies, InfoBarTimeshift, InfoBarSeek, InfoBarPlugins
from Screens.PictureInPicture import PictureInPicture
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from PipzapSetup import PipzapSetup
from Components.PluginComponent import plugins

class baseMethods:
	pass

#pragma mark -
#pragma mark ChannelSelection
#pragma mark -

# ChannelContextMenu: switch "Activate Picture in Picture" for pip/mainpicture
def ChannelContextMenu___init__(self, session, csel, *args, **kwargs):
	baseMethods.ChannelContextMenu__init__(self, session, csel, *args, **kwargs)

	if self.pipAvailable:
		list = self["menu"].list
		x = 0
		# TRANSLATORS: Do NOT translate this! This is not a string in our plugin but one from e2 core which we try to find, so a custom translation will probably disallow us to do so.
		searchText = _("Activate Picture in Picture")
		for entry in list:
			if entry[0][0] == searchText:
				if csel.dopipzap:
					entry = ChoiceEntryComponent("", (_("play in mainwindow"), self.playMain))
				else:
					entry = ChoiceEntryComponent("blue", (_("play as picture in picture"), self.showServiceInPiP))
				list[x] = entry
				break
			x += 1
		self["menu"].setList(list)

def ChannelContextMenu_playMain(self):
	# XXX: we want to keep the current selection
	sel = self.csel.getCurrentSelection()
	self.csel.zap()
	self.csel.setCurrentSelection(sel)
	self.close()

# do not hide existing pip
def ChannelContextMenu_showServiceInPiP(self):
	if not self.pipAvailable:
		return

	if not self.session.pipshown:
		self.session.pip = self.session.instantiateDialog(PictureInPicture)
		self.session.pip.show()

	newservice = self.csel.servicelist.getCurrent()
	if self.session.pip.playService(newservice):
		self.session.pipshown = True
		self.session.pip.servicePath = self.csel.getCurrentServicePath()
		self.close(True)
	else:
		self.session.pipshown = False
		del self.session.pip
		self.session.openWithCallback(self.close, MessageBox, _("Could not open Picture in Picture"), MessageBox.TYPE_ERROR)

def ChannelSelectionBase__init__(self, *args, **kwargs):
	baseMethods.ChannelSelectionBase__init__(self, *args, **kwargs)
	self.dopipzap = False
	self.enable_pipzap = False

def ChannelSelectionBase_setCurrentSelection(self, service, *args, **kwargs):
	if service:
		baseMethods.ChannelSelectionBase_setCurrentSelection(self, service, *args, **kwargs)

def ChannelSelection_channelSelected(self, *args, **kwargs):
	self.enable_pipzap = True
	baseMethods.ChannelSelection_channelSelected(self, *args, **kwargs)

def ChannelSelection_togglePipzap(self):
	assert(self.session.pip)
	title = self.instance.getTitle()
	pos = title.find(" (")
	if pos != -1:
		title = title[:pos]
	if self.dopipzap:
		# Mark PiP as inactive and effectively deactivate pipzap
		self.session.pip.inactive()
		self.dopipzap = False

		# Disable PiP if not playing a service
		if self.session.pip.pipservice is None:
			self.session.pipshown = False
			del self.session.pip

		# Move to playing service
		lastservice = eServiceReference(self.lastservice.value)
		if lastservice.valid() and self.getCurrentSelection() != lastservice:
			self.setCurrentSelection(lastservice)

		title += " (TV)"
	else:
		# Mark PiP as active and effectively active pipzap
		self.session.pip.active()
		self.dopipzap = True

		# Move to service playing in pip (will not work with subservices)
		self.setCurrentSelection(self.session.pip.getCurrentService())

		title += " (PiP)"
	self.setTitle(title)
	self.buildTitleString()

def ChannelSelection_zap(self, *args, **kwargs):
	if self.enable_pipzap and self.dopipzap:
		if not self.session.pipshown:
			self.session.pip = self.session.instantiateDialog(PictureInPicture)
			self.session.pip.show()
			self.session.pipshown = True
		self.revertMode=None
		ref = self.session.pip.getCurrentService()
		nref = self.getCurrentSelection()
		if ref is None or ref != nref:
			if not config.ParentalControl.servicepinactive.value or parentalControl.getProtectionLevel(nref.toCompareString()) == -1:
				if not self.session.pip.playService(nref):
					# XXX: Make sure we set an invalid ref
					self.session.pip.playService(None)
	else:
		baseMethods.ChannelSelection_zap(self, *args, **kwargs)

		# Yes, we might double-check this, but we need to re-select pipservice if pipzap is active
		# and we just wanted to zap in mainwindow once
		# XXX: do we really want this? this also resets the service when zapping from context menu
		#      which is irritating
		if self.dopipzap:
			# This unfortunately won't work with subservices
			self.setCurrentSelection(self.session.pip.getCurrentService())
	self.enable_pipzap = False

def ChannelSelection_setHistoryPath(self, *args, **kwargs):
	baseMethods.ChannelSelection_setHistoryPath(self, *args, **kwargs)
	if self.dopipzap:
		self.setCurrentSelection(self.session.pip.getCurrentService())

def ChannelSelection_cancel(self, *args, **kwargs):
	if self.revertMode is None and self.dopipzap:
		# This unfortunately won't work with subservices
		self.setCurrentSelection(self.session.pip.getCurrentService())
		self.revertMode = 1337 # not in (None, MODE_TV, MODE_RADIO)
	baseMethods.ChannelSelection_cancel(self, *args, **kwargs)

#pragma mark -
#pragma mark MoviePlayer
#pragma mark -

def MoviePlayer__init__(self, *args, **kwargs):
	baseMethods.MoviePlayer__init__(self, *args, **kwargs)
	self.servicelist = InfoBar.instance and InfoBar.instance.servicelist

	self["DirectionActions"] = HelpableActionMap(self, "DirectionActions",
		{
			"left": self.left,
			"right": self.right
		}, prio = -2)

def MoviePlayer_up(self):
	slist = self.servicelist
	if slist and slist.dopipzap:
		slist.moveUp()
		self.session.execDialog(slist)
	else:
		self.showMovies()

def MoviePlayer_down(self):
	slist = self.servicelist
	if slist and slist.dopipzap:
		slist.moveDown()
		self.session.execDialog(slist)
	else:
		self.showMovies()

def MoviePlayer_right(self):
	# XXX: gross hack, we do not really seek if changing channel in pip :-)
	slist = self.servicelist
	if slist and slist.dopipzap:
		# XXX: We replicate InfoBarChannelSelection.zapDown here - we shouldn't do that
		if slist.inBouquet():
			prev = slist.getCurrentSelection()
			if prev:
				prev = prev.toString()
				while True:
					if config.usage.quickzap_bouquet_change.value and slist.atEnd():
						slist.nextBouquet()
					else:
						slist.moveDown()
					cur = slist.getCurrentSelection()
					if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
						break
		else:
			slist.moveDown()
		slist.enable_pipzap = True
		slist.zap()
	else:
		InfoBarSeek.seekFwd(self)

def MoviePlayer_left(self):
	slist = self.servicelist
	if slist and slist.dopipzap:
		# XXX: We replicate InfoBarChannelSelection.zapUp here - we shouldn't do that
		if slist.inBouquet():
			prev = slist.getCurrentSelection()
			if prev:
				prev = prev.toString()
				while True:
					if config.usage.quickzap_bouquet_change.value:
						if slist.atBegin():
							slist.prevBouquet()
					slist.moveUp()
					cur = slist.getCurrentSelection()
					if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
						break
		else:
			slist.moveUp()
		slist.enable_pipzap = True
		slist.zap()
	else:
		InfoBarSeek.seekBack(self)

def MoviePlayer_swapPiP(self):
	pass

#pragma mark -
#pragma mark InfoBarGenerics
#pragma mark -

def InfoBarNumberZap_zapToNumber(self, *args, **kwargs):
	try:
		self.servicelist.enable_pipzap = True
	except AttributeError as ae:
		pass
	baseMethods.InfoBarNumberZap_zapToNumber(self, *args, **kwargs)

def InfoBarChannelSelection_zapUp(self, *args, **kwargs):
	self.servicelist.enable_pipzap = True
	baseMethods.InfoBarChannelSelection_zapUp(self, *args, **kwargs)

def InfoBarChannelSelection_zapDown(self, *args, **kwargs):
	self.servicelist.enable_pipzap = True
	baseMethods.InfoBarChannelSelection_zapDown(self, *args, **kwargs)

def InfoBarEPG_zapToService(self, *args, **kwargs):
	try:
		self.servicelist.enable_pipzap = True
	except AttributeError as ae:
		pass
	baseMethods.InfoBarEPG_zapToService(self, *args, **kwargs)

def InfoBarShowMovies__init__(self):
	baseMethods.InfoBarShowMovies__init__(self)
	self["MovieListActions"] = HelpableActionMap(self, "InfobarMovieListActions",
		{
			"movieList": (self.showMovies, _("movie list")),
			"up": (self.up, _("movie list")),
			"down": (self.down, _("movie list"))
		})

def InfoBarPiP__init__(self):
	baseMethods.InfoBarPiP__init__(self)
	if SystemInfo.get("NumVideoDecoders", 1) > 1 and self.allowPiP:
		self.addExtension((self.getTogglePipzapName, self.togglePipzap, self.pipzapAvailable), "red")
		if config.plugins.pipzap.enable_hotkey.value:
			self["pipzapActions"] = HelpableActionMap(self, "pipzapActions",
				{
					"switchPiP": (self.togglePipzap, _("zap in pip window...")),
				})

def InfoBarPiP_pipzapAvailable(self):
	try:
		return True if self.servicelist and self.session.pipshown else False
	except AttributeError as ae:
		return False

def InfoBarPiP_getTogglePipzapName(self):
	slist = self.servicelist
	if slist and slist.dopipzap:
		return _("Zap focus to main screen")
	return _("Zap focus to Picture in Picture")

def InfoBarPiP_togglePipzap(self):
	# supposed to fix some problems with permanent timeshift patch
	if isinstance(self, InfoBarTimeshift) and isinstance(self, InfoBarSeek) and \
		self.timeshift_enabled and self.isSeekable():
			return 0

	if not self.session.pipshown:
		self.showPiP()
	slist = self.servicelist
	if slist:
		slist.togglePipzap()

def InfoBarPiP_togglePipzapHelpable(self):
	"""Stupid helper for InfoBarPiP_togglePipzap to optimize away the check if help should be shown if it already was."""
	InfoBarPiP.togglePipzap = InfoBarPiP_togglePipzap

	if config.plugins.pipzap.show_help.value and pipzapHelp:
		pipzapHelp.open(self.session)
		config.plugins.pipzap.show_help.value = False
		config.plugins.pipzap.save()

	self.togglePipzap()

def InfoBarPiP_showPiP(self, *args, **kwargs):
	try:
		slist = self.servicelist
	except AttributeError as ae:
		slist = None

	if self.session.pipshown and slist and slist.dopipzap:
		slist.togglePipzap()
	elif not self.session.pipshown and isinstance(self, InfoBarShowMovies):
		self.session.pip = self.session.instantiateDialog(PictureInPicture)
		self.session.pip.show()
		self.session.pipshown = True
		if slist:
			self.session.pip.playService(slist.getCurrentSelection())
		return
	baseMethods.InfoBarPiP_showPiP(self, *args, **kwargs)

# Using the base implementation would cause nasty bugs, so ignore it here
def InfoBarPiP_swapPiP(self):
	swapservice = self.session.nav.getCurrentlyPlayingServiceReference()
	pipref = self.session.pip.getCurrentService()
	if pipref and swapservice and pipref.toString() != swapservice.toString():
			self.session.pip.playService(swapservice)

			try:
				slist = self.servicelist
			except AttributeError as ae:
				slist = None
			if slist:
				# TODO: this behaves real bad on subservices
				if slist.dopipzap:
					slist.servicelist.setCurrent(swapservice)
				else:
					slist.servicelist.setCurrent(pipref)

				slist.addToHistory(pipref) # add service to history
				slist.lastservice.value = pipref.toString() # save service as last playing one
			self.session.nav.stopService() # stop portal
			self.session.nav.playService(pipref) # start subservice

#pragma mark -
#pragma mark Picture in Picture
#pragma mark -

class PictureInPictureZapping(Screen):
	skin = """<screen name="PictureInPictureZapping" flags="wfNoBorder" position="50,50" size="90,26" title="PiPZap" zPosition="-1">
		<eLabel text="PiP-Zap" position="0,0" size="90,26" foregroundColor="#00ff66" font="Regular;26" />
	</screen>"""
	def refreshPosition(self):
		x = config.av.pip.value[0]
		y = config.av.pip.value[1]
		width = getDesktop(0).size().width()
		height = getDesktop(0).size().height()
		if x > width / 2:
			x = 40
		else:
			x = width - 120
		if y > height / 2:
			y = 40
		else:
			y = height - 55
		self.instance.move(ePoint(x, y))

def PictureInPicture__init__(self, session, *args, **kwargs):
	baseMethods.PictureInPicture__init__(self, session, *args, **kwargs)
	self.pipActive = session.instantiateDialog(PictureInPictureZapping)

def PictureInPicture_active(self):
	if config.plugins.pipzap.show_label.value:
		self.pipActive.show()

def PictureInPicture_inactive(self):
	self.pipActive.hide()

def PictureInPicture_move(self, *args, **kwargs):
	baseMethods.PictureInPicture_move(self, *args, **kwargs)
	self.pipActive.refreshPosition()

#pragma mark -
#pragma mark - Help
#pragma mark -

try:
	if SystemInfo.get("NumVideoDecoders", 1) > 1:
		from Plugins.SystemPlugins.MPHelp import registerHelp, XMLHelpReader
		from Tools.Directories import resolveFilename, SCOPE_PLUGINS
		file = open(resolveFilename(SCOPE_PLUGINS, "Extensions/pipzap/mphelp.xml"), 'r')
		reader = XMLHelpReader(file)
		file.close()
		pipzapHelp = registerHelp(*reader)
except Exception as e:
	print("[pipzap] Unable to initialize MPHelp:", e,"- Help not available!")
	pipzapHelp = None

#pragma mark -
#pragma mark Plugin
#pragma mark -

def overwriteFunctions():
	"""Overwrite existing functions here to increase system stability a bit."""
	try:
		baseMethods.ChannelContextMenu__init__
	except AttributeError as ae:
		pass
	else:
		print("[pipzap] already initialized, aborting.")
		return

	global ChannelContextMenu, ChannelSelection, ChannelSelectionBase
	try:
		from Plugins.Extensions.AdvancedChannelSelection import plugin
	except ImportError as ie:
		pass
	else:
		if config.plugins.AdvancedChannelSelection.enabled.value:
			print("[pipzap] ACS is installed and activated, ugly just invited scary to the party xD")
			from Plugins.Extensions.AdvancedChannelSelection.ChannelSelection import ChannelContextMenu, ChannelSelection, ChannelSelectionBase

	baseMethods.ChannelContextMenu__init__ = ChannelContextMenu.__init__
	ChannelContextMenu.__init__ = ChannelContextMenu___init__

	ChannelContextMenu.playMain = ChannelContextMenu_playMain
	ChannelContextMenu.showServiceInPiP = ChannelContextMenu_showServiceInPiP

	baseMethods.ChannelSelectionBase__init__ = ChannelSelectionBase.__init__
	ChannelSelectionBase.__init__ = ChannelSelectionBase__init__

	baseMethods.ChannelSelectionBase_setCurrentSelection = ChannelSelectionBase.setCurrentSelection
	ChannelSelectionBase.setCurrentSelection = ChannelSelectionBase_setCurrentSelection

	baseMethods.ChannelSelection_channelSelected = ChannelSelection.channelSelected
	ChannelSelection.channelSelected = ChannelSelection_channelSelected

	ChannelSelection.togglePipzap = ChannelSelection_togglePipzap 

	baseMethods.ChannelSelection_zap = ChannelSelection.zap
	ChannelSelection.zap = ChannelSelection_zap

	baseMethods.ChannelSelection_setHistoryPath = ChannelSelection.setHistoryPath
	ChannelSelection.setHistoryPath = ChannelSelection_setHistoryPath

	baseMethods.ChannelSelection_cancel = ChannelSelection.cancel
	ChannelSelection.cancel = ChannelSelection_cancel

	baseMethods.MoviePlayer__init__ = MoviePlayer.__init__
	MoviePlayer.__init__ = MoviePlayer__init__

	MoviePlayer.allowPiP = property(lambda *x: True, lambda *x: None)

	MoviePlayer.up = MoviePlayer_up
	MoviePlayer.down = MoviePlayer_down
	MoviePlayer.right = MoviePlayer_right
	MoviePlayer.left = MoviePlayer_left
	MoviePlayer.swapPiP = MoviePlayer_swapPiP

	baseMethods.InfoBarNumberZap_zapToNumber = InfoBarNumberZap.zapToNumber
	InfoBarNumberZap.zapToNumber = InfoBarNumberZap_zapToNumber

	baseMethods.InfoBarChannelSelection_zapUp = InfoBarChannelSelection.zapUp
	InfoBarChannelSelection.zapUp = InfoBarChannelSelection_zapUp

	baseMethods.InfoBarChannelSelection_zapDown = InfoBarChannelSelection.zapDown
	InfoBarChannelSelection.zapDown = InfoBarChannelSelection_zapDown

	baseMethods.InfoBarEPG_zapToService = InfoBarEPG.zapToService
	InfoBarEPG.zapToService = InfoBarEPG_zapToService

	baseMethods.InfoBarShowMovies__init__ = InfoBarShowMovies.__init__
	InfoBarShowMovies.__init__ = InfoBarShowMovies__init__

	baseMethods.InfoBarPiP__init__ = InfoBarPiP.__init__
	InfoBarPiP.__init__ = InfoBarPiP__init__

	InfoBarPiP.pipzapAvailable = InfoBarPiP_pipzapAvailable
	InfoBarPiP.getTogglePipzapName = InfoBarPiP_getTogglePipzapName
	InfoBarPiP.swapPiP = InfoBarPiP_swapPiP

	if config.plugins.pipzap.show_help.value and pipzapHelp:
		InfoBarPiP.togglePipzap = InfoBarPiP_togglePipzapHelpable
	else:
		InfoBarPiP.togglePipzap = InfoBarPiP_togglePipzap

	baseMethods.InfoBarPiP_showPiP = InfoBarPiP.showPiP
	InfoBarPiP.showPiP = InfoBarPiP_showPiP

	baseMethods.PictureInPicture__init__ = PictureInPicture.__init__
	PictureInPicture.__init__ = PictureInPicture__init__

	PictureInPicture.active = PictureInPicture_active
	PictureInPicture.inactive = PictureInPicture_inactive

	baseMethods.PictureInPicture_move = PictureInPicture.move
	PictureInPicture.move = PictureInPicture_move

config.plugins.pipzap = ConfigSubsection()
config.plugins.pipzap.enable_hotkey = ConfigEnableDisable(default = True)
config.plugins.pipzap.show_in_plugins = ConfigEnableDisable(default = False)
config.plugins.pipzap.show_label = ConfigEnableDisable(default = True)
config.plugins.pipzap.show_help = ConfigEnableDisable(default = True)

def autostart(reason, **kwargs):
	if reason == 0:
		overwriteFunctions()

def activate(session, *args, **kwargs):
	infobar = InfoBar.instance
	if not infobar:
		session.open(MessageBox, _("Unable to access InfoBar.\npipzap not available."), MessageBox.TYPE_ERROR)
	elif hasattr(infobar, 'togglePipzap'): # check if plugin is already hooked into enigma2
		infobar.togglePipzap()
	else:
		session.open(MessageBox, _("pipzap not properly installed.\nPlease restart Enigma2."), MessageBox.TYPE_ERROR)

def main(session, *args, **kwargs):
	session.open(PipzapSetup)

def menu(menuid):
	if menuid != "system":
		return []
	return [(_("pipzap"), main, "pipzap_setup", None)]

def housekeepingPluginmenu(el):
	if el.value:
		plugins.addPlugin(activateDescriptor)
	else:
		plugins.removePlugin(activateDescriptor)

config.plugins.pipzap.show_in_plugins.addNotifier(housekeepingPluginmenu, initial_call=False, immediate_feedback=True)
activateDescriptor = PluginDescriptor(name="pipzap", description=_("Toggle pipzap status"), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=activate, needsRestart=False)

def showHideNotifier(el):
	infobar = InfoBar.instance
	if not infobar:
		return
	session = infobar.session
	slist = infobar.servicelist
	if slist and hasattr(slist, 'dopipzap'): # check if plugin is already hooked into enigma2
		if session.pipshown:
			if el.value and slist.dopipzap:
				session.pip.active()
			else:
				session.pip.inactive()

config.plugins.pipzap.show_label.addNotifier(showHideNotifier, initial_call=False, immediate_feedback=True)

def Plugins(**kwargs):
	# do not add any entry if only one (or less :P) video decoders present
	if SystemInfo.get("NumVideoDecoders", 1) < 2:
		return []

	l = [
		PluginDescriptor(
			where=PluginDescriptor.WHERE_AUTOSTART,
			fnc=autostart,
			needsRestart=True, # XXX: force restart for now as I don't think the plugin will work properly without one
		),
		PluginDescriptor(
			where=PluginDescriptor.WHERE_MENU,
			fnc=menu,
			needsRestart=False,
		),
	]
	if config.plugins.pipzap.show_in_plugins.value:
		l.append(activateDescriptor)
	return l
