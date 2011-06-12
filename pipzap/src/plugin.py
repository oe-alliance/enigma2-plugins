# Plugin definition
from Plugins.Plugin import PluginDescriptor

from Components.ActionMap import HelpableActionMap
from Components.ChoiceList import ChoiceEntryComponent
from Components.config import config, ConfigSubsection, ConfigEnableDisable
from Components.SystemInfo import SystemInfo
from Components.ParentalControl import parentalControl
from enigma import eServiceReference
from Screens.ChannelSelection import ChannelContextMenu, ChannelSelection, ChannelSelectionBase
from Screens.InfoBar import InfoBar, MoviePlayer
from Screens.InfoBarGenerics import InfoBarNumberZap, InfoBarEPG, InfoBarChannelSelection, InfoBarPiP, InfoBarShowMovies, InfoBarTimeshift, InfoBarSeek, InfoBarPlugins
from Screens.PictureInPicture import PictureInPicture
from Screens.Screen import Screen

#pragma mark -
#pragma mark ChannelSelection
#pragma mark -

# ChannelContextMenu: switch "Activate Picture in Picture" for pip/mainpicture
def ChannelContextMenu___init__(self, session, csel, *args, **kwargs):
	ChannelContextMenu.baseInit(self, session, csel, *args, **kwargs)

	list = self["menu"].list
	x = 0
	for entry in list:
		if entry[0][0] == _("Activate Picture in Picture"):
			if csel.dopipzap:
				entry = ChoiceEntryComponent("", (_("play in mainwindow"), self.playMain))
			else:
				entry = ChoiceEntryComponent("blue", (_("play as picture in picture"), self.showServiceInPiP))
			list[x] = entry
			break
		x += 1
	self["menu"].setList(list)
ChannelContextMenu.baseInit = ChannelContextMenu.__init__
ChannelContextMenu.__init__ = ChannelContextMenu___init__

def ChannelContextMenu_playMain(self):
	# XXX: we want to keep the current selection
	sel = self.csel.getCurrentSelection()
	self.csel.zap()
	self.csel.setCurrentSelection(sel)
	self.close()
ChannelContextMenu.playMain = ChannelContextMenu_playMain

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
ChannelContextMenu.showServiceInPiP = ChannelContextMenu_showServiceInPiP

def ChannelSelectionBase__init__(self, *args, **kwargs):
	ChannelSelectionBase.baseInit(self, *args, **kwargs)
	self.dopipzap = False
	self.enable_pipzap = False
ChannelSelectionBase.baseInit = ChannelSelectionBase.__init__
ChannelSelectionBase.__init__ = ChannelSelectionBase__init__

def ChannelSelectionBase_setCurrentSelection(self, service, *args, **kwargs):
	if service:
		ChannelSelectionBase.baseSetCurrentSelection(self, service, *args, **kwargs)
ChannelSelectionBase.baseSetCurrentSelection = ChannelSelectionBase.setCurrentSelection
ChannelSelectionBase.setCurrentSelection = ChannelSelectionBase_setCurrentSelection

def ChannelSelection_channelSelected(self, *args, **kwargs):
	self.enable_pipzap = True
	ChannelSelection.baseChannelSelected(self, *args, **kwargs)
	self.enable_pipzap = False
ChannelSelection.baseChannelSelected = ChannelSelection.channelSelected
ChannelSelection.channelSelected = ChannelSelection_channelSelected

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
ChannelSelection.togglePipzap = ChannelSelection_togglePipzap 

def ChannelSelection_zap(self, *args, **kwargs):
	if self.enable_pipzap and self.dopipzap:
		self.revertMode=None
		ref = self.session.pip.getCurrentService()
		nref = self.getCurrentSelection()
		if ref is None or ref != nref:
			if not config.ParentalControl.configured.value or parentalControl.getProtectionLevel(nref.toCompareString()) == -1:
				if not self.session.pip.playService(nref):
					# XXX: Make sure we set an invalid ref
					self.session.pip.playService(None)
	else:
		ChannelSelection.baseZap(self, *args, **kwargs)

		# Yes, we might double-check this, but we need to re-select pipservice if pipzap is active
		# and we just wanted to zap in mainwindow once
		# XXX: do we really want this? this also resets the service when zapping from context menu
		#      which is irritating
		if self.dopipzap:
			# This unfortunately won't work with subservices
			self.setCurrentSelection(self.session.pip.getCurrentService())
ChannelSelection.baseZap = ChannelSelection.zap
ChannelSelection.zap = ChannelSelection_zap

def ChannelSelection_setHistoryPath(self, *args, **kwargs):
	ChannelSelection.baseSetHistoryPath(self, *args, **kwargs)
	if self.dopipzap:
		self.setCurrentSelection(self.session.pip.getCurrentService())
ChannelSelection.baseSetHistoryPath = ChannelSelection.setHistoryPath
ChannelSelection.setHistoryPath = ChannelSelection_setHistoryPath

def ChannelSelection_cancel(self, *args, **kwargs):
	if self.revertMode is None and self.dopipzap:
		# This unfortunately won't work with subservices
		self.setCurrentSelection(self.session.pip.getCurrentService())
		self.revertMode = 1337 # not in (None, MODE_TV, MODE_RADIO)
	ChannelSelection.baseCancel(self, *args, **kwargs)
ChannelSelection.baseCancel = ChannelSelection.cancel
ChannelSelection.cancel = ChannelSelection_cancel

#pragma mark -
#pragma mark MoviePlayer
#pragma mark -

def MoviePlayer__init__(self, *args, **kwargs):
	MoviePlayer.baseInit(self, *args, **kwargs)
	self.servicelist = InfoBar.instance.servicelist

	# WARNING: GROSS HACK INBOUND
	del self.list[:]
	self.allowPiP = True
	InfoBarPlugins.__init__(self)
	InfoBarPiP.__init__(self)

	self["DirectionActions"] = HelpableActionMap(self, "DirectionActions",
		{
			"left": self.left,
			"right": self.right
		}, prio = -2)
MoviePlayer.baseInit = MoviePlayer.__init__
MoviePlayer.__init__ = MoviePlayer__init__

def MoviePlayer_up(self):
	slist = self.servicelist
	if slist and slist.dopipzap:
		slist.moveUp()
		self.session.execDialog(slist)
	else:
		self.showMovies()
MoviePlayer.up = MoviePlayer_up

def MoviePlayer_down(self):
	slist = self.servicelist
	if slist and slist.dopipzap:
		slist.moveDown()
		self.session.execDialog(slist)
	else:
		self.showMovies()
MoviePlayer.down = MoviePlayer_down

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
		slist.enable_pipzap = False
	else:
		InfoBarSeek.seekFwd(self)
MoviePlayer.right = MoviePlayer_right

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
		slist.enable_pipzap = False
	else:
		InfoBarSeek.seekBack(self)
MoviePlayer.left = MoviePlayer_left

def MoviePlayer_showPiP(self):
	slist = self.servicelist
	if self.session.pipshown:
		if slist and slist.dopipzap:
			slist.togglePipzap()
		del self.session.pip
		self.session.pipshown = False
	else:
		from Screens.PictureInPicture import PictureInPicture
		self.session.pip = self.session.instantiateDialog(PictureInPicture)
		self.session.pip.show()
		self.session.pipshown = True
		self.session.pip.playService(slist.getCurrentSelection())
MoviePlayer.showPiP = MoviePlayer_showPiP

def MoviePlayer_swapPiP(self):
	pass
MoviePlayer.swapPiP = MoviePlayer_swapPiP

#pragma mark -
#pragma mark InfoBarGenerics
#pragma mark -

def InfoBarNumberZap_zapToNumber(self, *args, **kwargs):
	self.servicelist.enable_pipzap = True
	InfoBarNumberZap.baseZapToNumber(self, args, **kwargs)
	self.servicelist.enable_pipzap = False
InfoBarNumberZap.baseZapToNumber = InfoBarNumberZap.zapToNumber
InfoBarNumberZap.zapToNumber = InfoBarNumberZap_zapToNumber

def InfoBarChannelSelection_zapUp(self, *args, **kwargs):
	self.servicelist.enable_pipzap = True
	InfoBarChannelSelection.baseZapUp(self, *args, **kwargs)
	self.servicelist.enable_pipzap = False
InfoBarChannelSelection.baseZapUp = InfoBarChannelSelection.zapUp
InfoBarChannelSelection.zapUp = InfoBarChannelSelection_zapUp

def InfoBarChannelSelection_zapDown(self, *args, **kwargs):
	self.servicelist.enable_pipzap = True
	InfoBarChannelSelection.baseZapDown(self, *args, **kwargs)
	self.servicelist.enable_pipzap = False
InfoBarChannelSelection.baseZapDown = InfoBarChannelSelection.zapDown
InfoBarChannelSelection.zapDown = InfoBarChannelSelection_zapDown

def InfoBarEPG_zapToService(self, *args, **kwargs):
	self.servicelist.enable_pipzap = True
	InfoBarEPG.baseZapToService(self, *args, **kwargs)
	self.servicelist.enable_pipzap = False
InfoBarEPG.baseZapToService = InfoBarEPG.zapToService
InfoBarEPG.zapToService = InfoBarEPG_zapToService

def InfoBarShowMovies__init__(self):
	InfoBarShowMovies.baseInit(self)
	self["MovieListActions"] = HelpableActionMap(self, "InfobarMovieListActions",
		{
			"movieList": (self.showMovies, _("movie list")),
			"up": (self.up, _("movie list")),
			"down": (self.down, _("movie list"))
		})
InfoBarShowMovies.baseInit = InfoBarShowMovies.__init__
InfoBarShowMovies.__init__ = InfoBarShowMovies__init__

def InfoBarPiP__init__(self):
	InfoBarPiP.baseInit(self)
	if SystemInfo.get("NumVideoDecoders", 1) > 1 and self.allowPiP:
		self.addExtension((self.getTogglePipzapName, self.togglePipzap, self.pipShown), "red")
		if config.plugins.pipzap.enable_hotkey.value:
			self["pipzapActions"] = HelpableActionMap(self, "pipzapActions",
				{
					"switchPiP": (self.togglePipzap, _("zap in pip window...")),
				})
InfoBarPiP.baseInit = InfoBarPiP.__init__
InfoBarPiP.__init__ = InfoBarPiP__init__

def InfoBarPiP_getTogglePipzapName(self):
	slist = self.servicelist
	if slist and slist.dopipzap:
		return _("Zap focus to main screen")
	return _("Zap focus to Picture in Picture")
InfoBarPiP.getTogglePipzapName = InfoBarPiP_getTogglePipzapName

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
InfoBarPiP.togglePipzap = InfoBarPiP_togglePipzap

# Using the base implementation would cause nasty bugs, so ignore it here
def InfoBarPiP_showPiP(self):
	if self.session.pipshown:
		slist = self.servicelist
		if slist and slist.dopipzap:
			slist.togglePipzap()
		del self.session.pip
		self.session.pipshown = False
	else:
		self.session.pip = self.session.instantiateDialog(PictureInPicture)
		self.session.pip.show()
		newservice = self.session.nav.getCurrentlyPlayingServiceReference()
		if self.session.pip.playService(newservice):
			self.session.pipshown = True
			self.session.pip.servicePath = self.servicelist.getCurrentServicePath()
		else:
			self.session.pipshown = False
			del self.session.pip
InfoBarPiP.showPiP = InfoBarPiP_showPiP

# Using the base implementation would cause nasty bugs, so ignore it here
def InfoBarPiP_swapPiP(self):
	swapservice = self.session.nav.getCurrentlyPlayingServiceReference()
	pipref = self.session.pip.getCurrentService()
	if pipref and swapservice and pipref.toString() != swapservice.toString():
			self.session.pip.playService(swapservice)

			slist = self.servicelist
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
InfoBarPiP.swapPiP = InfoBarPiP_swapPiP

#pragma mark -
#pragma mark Picture in Picture
#pragma mark -

class PictureInPictureZapping(Screen):
	skin = """<screen name="PictureInPictureZapping" flags="wfNoBorder" position="50,50" size="90,26" title="PiPZap" zPosition="-1">
		<eLabel text="PiP-Zap" position="0,0" size="90,26" foregroundColor="#00ff66" font="Regular;26" />
	</screen>"""

def PictureInPicture__init__(self, session, *args, **kwargs):
	PictureInPicture.baseInit(self, session, *args, **kwargs)
	self.pipActive = session.instantiateDialog(PictureInPictureZapping)
PictureInPicture.baseInit = PictureInPicture.__init__
PictureInPicture.__init__ = PictureInPicture__init__

def PictureInPicture_active(self):
	self.pipActive.show()
PictureInPicture.active = PictureInPicture_active

def PictureInPicture_inactive(self):
	self.pipActive.hide()
PictureInPicture.inactive = PictureInPicture_inactive

#pragma mark -
#pragma mark Plugin
#pragma mark -

from PipzapSetup import PipzapSetup

# XXX: disabling more than the hotkey does not make much sense, because then you could just remove the plugin
config.plugins.pipzap = ConfigSubsection()
config.plugins.pipzap.enable_hotkey = ConfigEnableDisable(default = True)

def main(session):
	session.open(PipzapSetup)

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			name="pipzap",
			description=_("Configure pipzap Plugin"),
			where=PluginDescriptor.WHERE_PLUGINMENU,
			fnc=main,
			needsRestart=True, # XXX: force restart for now as I don't think the plugin will work properly without one
		),
	]
