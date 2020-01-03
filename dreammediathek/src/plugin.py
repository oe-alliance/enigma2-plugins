# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor
from Tools.BoundFunction import boundFunction
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List
from Components.AVSwitch import AVSwitch
from Components.config import config, Config, ConfigSelection, ConfigSubsection, ConfigText, getConfigListEntry, ConfigYesNo, ConfigIP, ConfigNumber,ConfigLocations
from Components.config import KEY_DELETE, KEY_BACKSPACE, KEY_LEFT, KEY_RIGHT, KEY_HOME, KEY_END, KEY_TOGGLEOW, KEY_ASCII, KEY_TIMEOUT
from Components.ConfigList import ConfigListScreen
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase

from Tools.Directories import pathExists, fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE, SCOPE_HDD, SCOPE_CURRENT_PLUGIN, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
from enigma import eTimer, quitMainloop,eListbox,ePoint, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER, eListboxPythonMultiContent, eListbox, gFont, getDesktop, ePicLoad, eServiceCenter, iServiceInformation, eServiceReference,iSeekableService,iServiceInformation, iPlayableService, iPlayableServicePtr
from os import path as os_path, system as os_system, unlink, stat, mkdir, popen, makedirs, listdir, access, rename, remove, W_OK, R_OK, F_OK
from twisted.web import client
from twisted.internet import reactor
from time import time

from Screens.InfoBarGenerics import InfoBarShowHide, InfoBarSeek, InfoBarNotifications, InfoBarServiceNotifications

from ServiceXML import iWebTVStations
from MoviePlayer import dreamMediathekPlayer

config.plugins.dreamMediathek = ConfigSubsection()
config.plugins.dreamMediathek.general = ConfigSubsection()
config.plugins.dreamMediathek.general.on_movie_stop = ConfigSelection(default = "ask", choices = [
	("ask", _("Ask user")), ("quit", _("Return to movie list")), ("playnext", _("Play next video")), ("playagain", _("Play video again")) ])
config.plugins.dreamMediathek.general.on_exit = ConfigSelection(default = "ask", choices = [
	("ask", _("Ask user")), ("quit", _("Return to movie list"))])


class dreamMediathekStationsScreen(Screen):
	Details = {}
	skin = """
		<screen name="dreamMediathekStationsScreen" position="center,center" size="560,440" title="dreamMediathekStationsScreen" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
			<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
			<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />
			<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
			<widget source="streamlist" render="Listbox" position="5,50" size="550,280" zPosition="1" scrollbarMode="showOnDemand" transparent="1" >
				<convert type="TemplatedMultiContent">
				{"templates":
					{"default": (55,[
							MultiContentEntryText(pos = (5, 1), size = (540, 28), font=2, flags = RT_HALIGN_LEFT | RT_VALIGN_TOP| RT_WRAP, text = 1), # provider, title, streamurl
							MultiContentEntryText(pos = (5, 28), size = (540, 18), font=3, flags = RT_HALIGN_LEFT | RT_VALIGN_TOP| RT_WRAP, text = 0), # provider, title, streamurl
						]),
					"state": (55,[
							MultiContentEntryText(pos = (10, 1), size = (560, 28), font=2, flags = RT_HALIGN_LEFT | RT_VALIGN_TOP| RT_WRAP, text = 0), # index 0 is the name
							MultiContentEntryText(pos = (10, 22), size = (560, 46), font=3, flags = RT_HALIGN_LEFT | RT_VALIGN_TOP| RT_WRAP, text = 1), # index 2 is the description
						])
					},
					"fonts": [gFont("Regular", 22),gFont("Regular", 18),gFont("Regular", 26),gFont("Regular", 20)],
					"itemHeight": 55
				}
				</convert>
			</widget>
		</screen>"""
		
	def __init__(self, session, skin_path = None):
		Screen.__init__(self, session)
		self.session = session
		self.skin_path = skin_path
		if self.skin_path == None:
			self.skin_path = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/dreamMediathek")

		self.lastservice = session.nav.getCurrentlyPlayingServiceReference()
		self.streamlist = []
		self.currentList = "streamlist"
		self.oldList = None
		self.tvstations = None

		self["streamlist"] = List(self.streamlist)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText()
		self["key_blue"] = StaticText()	

		self["FredMainActions"] = ActionMap(["ShortcutActions", "WizardActions"],
		{
			"ok": self.keyOK,
			"back": self.leavePlayer,
			"red": self.leavePlayer,
		}, -1)

		#self["videoactions"].setEnabled(True)
		self.onLayoutFinish.append(self.layoutFinished)
		self.onShown.append(self.setWindowTitle)
		self.onClose.append(self.__onClose)
		
	def __onClose(self):
		self.Details = {}
		self.session.nav.playService(self.lastservice)
		
	def layoutFinished(self):
		self.currentList = "streamlist"
		self.getStationsList()
		#self["videoactions"].setEnabled(False)
		
	def setWindowTitle(self):
		self.setTitle(_("dreamMediathek TV Stations"))

	def handleLeave(self, how):
		self.is_closing = True
		if how == "ask":
			list = (
				(_("Yes"), "quit"),
				(_("No"), "continue")
			)					
			self.session.openWithCallback(self.leavePlayerConfirmed, ChoiceBox, title=_("Really quit dreamMediathek ?"), list = list)
		else:
			self.leavePlayerConfirmed([True, how])

	def leavePlayer(self):
		print "leavePlayer"
		self.handleLeave(config.plugins.dreamMediathek.general.on_exit.value)

	def leavePlayerConfirmed(self, answer):
		answer = answer and answer[1]
		if answer == "quit":
			self.doQuit()
		else:
			return

	def doQuit(self):
		config.plugins.dreamMediathek.general.save()
		config.plugins.dreamMediathek.save()
		self.close()
			
	def keyOK(self):
		print "self.currentList im KeyOK",self.currentList
		if self.currentList == "streamlist":
			current = self["streamlist"].getCurrent()
			if current:
				print current
				url = current[2]
				title = current[1]
				myreference = eServiceReference(4097,0,url)
				myreference.setName(title)
				#self.session.open(dreamMediathekPlayer, myreference, self.lastservice, infoCallback = self.showVideoInfo, nextCallback = self.getNextEntry, prevCallback = self.getPrevEntry )
				self.session.open(dreamMediathekPlayer, myreference, self.lastservice)

	def getStationsList(self):
		print "getStationsList"
		iWebTVStations.getWebTVStations()
		self.buildStationsList()

	def buildStationsComponent(self, station):
		provider = None
		title = None
		streamurl = None
		if iWebTVStations.webtv_stations[station].has_key("provider"):
			provider = iWebTVStations.webtv_stations[station]["provider"]
		if iWebTVStations.webtv_stations[station].has_key("title"):
			title = iWebTVStations.webtv_stations[station]["title"]
		if iWebTVStations.webtv_stations[station].has_key("streamurl"):
			streamurl = iWebTVStations.webtv_stations[station]["streamurl"]			
		return((provider, title, streamurl ))	

	def buildStationsList(self):
		self.tvstations = None
		self.tvstations = iWebTVStations.getWebTVStationsList()
		if self.tvstations and len(self.tvstations):
			self.streamlist = []
			for station in self.tvstations:
				print "GOT station:",station
				self.streamlist.append(self.buildStationsComponent(station))
			if len(self.streamlist):
				self["streamlist"].setList(self.streamlist)
				self["streamlist"].style = "default"

def dreamMediathekMain(session, **kwargs):
	session.open(dreamMediathekStationsScreen)


def Plugins(path, **kwargs):
	global plugin_path
	plugin_path = path
	return PluginDescriptor(
		name=_("DreamMediathek"),
		description=_("Play Web and ipTV streams"),
		where = [ PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU ],
		fnc = dreamMediathekMain)
