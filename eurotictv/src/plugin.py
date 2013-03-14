from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarCueSheetSupport
from Screens.HelpMenu import HelpableScreen
from Components.Sources.StaticText import StaticText
from Components.Sources.Boolean import Boolean
from Components.ActionMap import HelpableActionMap, ActionMap
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.VideoWindow import VideoWindow
from Components.Label import Label, MultiColorLabel
from Components.Pixmap import Pixmap
from Components.GUIComponent import GUIComponent
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigPassword, ConfigYesNo, ConfigText
from enigma import eListboxPythonMultiContent, eServiceReference, getDesktop, iPlayableService, eSize, ePicLoad, iServiceInformation
from ServiceReference import ServiceReference
from Tools.Directories import SCOPE_PLUGINS, resolveFilename
from __init__ import __

class EuroticTVPlayer(Screen, InfoBarBase, InfoBarSeek, HelpableScreen):
	STATE_DISCONNECTED, STATE_CONNECTING, STATE_PLAYING, STATE_PAUSED, STATE_FAILURE = range(5)
	STATE_NAMES = [__("disconnected"), __("connecting..."), __("LIVE"), __("pause"), __("No Connection")]
	STREAM_DIM = (768, 576)
	PIP_DIM = (432, 324)
	STREAM_URI = "http://174.121.228.234/hls-live/livepkgr/_definst_/liveevent/etv-livestream_2.m3u86"
	CENTER_POS = ((560-PIP_DIM[0])/2)

	skin = """
	<screen position="center,center" size="560,470" title="eUroticTV" flags="wfNoBorder">
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
		<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;19" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
		<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;19" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;19" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
		<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;19" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />

		<widget source="pig_mode" render="Pig" position="%i,60" size="%i,%i" zPosition="0" backgroundColor="transparent">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget name="poster" position="%i,60" size="%i,%i" alphatest="on" zPosition="2" />
		<widget name="connection_label" position="85,422" size="384,48" font="Regular;24" valign="center" halign="center" foregroundColors="#000000,#FFFF00,#00FF00,#AAAAAA,#FF0000" />
		<widget source="do_blink" render="FixedLabel" text=" " position="85,434" zPosition="1" size="384,24">
			<convert type="ConditionalShowHide">Blink</convert>
		</widget>
	</screen>""" % (CENTER_POS, PIP_DIM[0], PIP_DIM[1], CENTER_POS, PIP_DIM[0], PIP_DIM[1])

	def __init__(self, session):
		Screen.__init__(self, session)
		InfoBarBase.__init__(self, steal_current_service = True)
		InfoBarSeek.__init__(self, actionmap = "CutlistSeekActions")
		HelpableScreen.__init__(self)
		self.old_service = session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.stopService()

		self["key_red"] = StaticText(__("Exit"))
		self["key_green"] = StaticText(__("Play"))
		self["key_yellow"] = StaticText((""))
		self["key_blue"] = StaticText(__("Fullscreen"))
		self["connection_label"] = MultiColorLabel()
		self["do_blink"] = Boolean(False)
		self["pig_mode"] = Boolean(True)

		self["poster"] = Pixmap()
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.paintPosterPixmapCB)

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "InfobarSeekActions", "MediaPlayerActions"],
		{
				"ok": self.keyOK,
				"cancel": self.exit,
				"stop": self.disconnect,
				"playpauseService": self.playpauseService,
				"red": self.exit,
				"green": self.keyOK,
				"blue": self.keyBlue,
				"yellow": self.keyYellow,
				"seekFwd": self.keyPass
			}, -4)

		self.__event_tracker = ServiceEventTracker(screen = self, eventmap =
			{
				iPlayableService.evStart: self.__serviceStarted,
				iPlayableService.evUpdatedEventInfo: self.__streamStarted,
				iPlayableService.evTuneFailed: self.__streamFailed,
				iPlayableService.evEOF: self.__evEOF,
				iPlayableService.evUser+15: self.__streamFailed
			})	

		self.onClose.append(self.__onClose)
		self.onExecBegin.append(self.__onExecBegin)
		
		self.setState(self.STATE_DISCONNECTED)

	def __onExecBegin(self):
		from Components.AVSwitch import AVSwitch
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((self["poster"].instance.size().width(), self["poster"].instance.size().height(), self.PIP_DIM[0], self.PIP_DIM[1], False, 1, "#00000000"))
		self.picload.startDecode(resolveFilename(SCOPE_PLUGINS)+"Extensions/eUroticTV/"+"eurotic.jpg")

	def setState(self, state):
		if state <= self.STATE_FAILURE:
			self.state = state

		self["connection_label"].setForegroundColorNum(self.state)
		self["connection_label"].setText(self.STATE_NAMES[self.state])
		
		if self.state in (self.STATE_CONNECTING, self.STATE_PAUSED):
			self["do_blink"].setBoolean(True)
		else:
			self["do_blink"].setBoolean(False)

		if self.state in (self.STATE_DISCONNECTED, self.STATE_CONNECTING, self.STATE_FAILURE):
			self.togglePIG(fullscreen=False)
		
		if self.state in (self.STATE_PLAYING, self.STATE_PAUSED):
			self["poster"].hide()
			self["pig_mode"].setBoolean(True)
		else: 
			self["poster"].show()
			self["pig_mode"].setBoolean(False)

	def paintPosterPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr != None:
			self["poster"].instance.setPixmap(ptr)
			self["poster"].show()

	def __streamStarted(self):
		print "__streamStarted"
		if self.state != self.STATE_PAUSED:
			self.setState(self.STATE_PLAYING)

	def __serviceStarted(self):
		print "__streamStarted"
		self.setState(self.STATE_CONNECTING)

	def __streamFailed(self):
		print "__streamFailed"
		currPlay = self.session.nav.getCurrentService()
		message = currPlay.info().getInfoString(iServiceInformation.sUser+12)
		self.setState(self.STATE_FAILURE)
		self["connection_label"].setText(_("Streaming error: %s") % message)

	def __evEOF(self):
		print "__evEOF"
		if self.state != self.STATE_FAILURE:
			self.setState(self.STATE_DISCONNECTED)

	def keyPass(self):
		print "keyPass"

	def keyOK(self):
		if self.state in (self.STATE_DISCONNECTED, self.STATE_FAILURE):
			self.start()
		elif self.state == self.STATE_PAUSED:
			self.playpauseService()

	def keyYellow(self):
		if self.state in (self.STATE_PLAYING, self.STATE_PAUSED):
			self.playpauseService()

	def togglePIG(self, fullscreen=False):
		if fullscreen == True:
			self.hide()
		else:
			self.show()
		self["pig_mode"].setBoolean(not fullscreen)

	def keyBlue(self):
		if self["pig_mode"].getBoolean() == True:
			self.togglePIG(True)
		else:
			self.togglePIG(fullscreen=False)

	def playpauseService(self):
		if self.seekstate == self.SEEK_STATE_PLAY:
			self.setState(self.STATE_PAUSED)
			self.pauseService()
		elif self.seekstate == self.SEEK_STATE_PAUSE:
			self.setState(self.STATE_PLAYING)
			self.unPauseService()

	def checkSkipShowHideLock(self):
		pass

	def start(self):
		sref = eServiceReference(4097,0,self.STREAM_URI)
		sref.setName("eUroticTV Live Stream")
		self.session.nav.playService(sref)

	def disconnect(self):
		self.session.nav.stopService()
		self.setState(self.STATE_DISCONNECTED)

	def __onClose(self):
		self.session.nav.playService(self.old_service, forceRestart=True)

	def exit(self):
		self.close()

def main(session, **kwargs):
	session.open(EuroticTVPlayer)

def Plugins(**kwargs):
 	return PluginDescriptor(name="eUroticTV", description=__("Watch eUroticTV via HTTP Live Streaming"), where = PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", needsRestart = True, fnc=main)
