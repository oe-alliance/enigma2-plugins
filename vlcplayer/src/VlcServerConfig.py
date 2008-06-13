# -*- coding: ISO-8859-1 -*-
#===============================================================================
# VLC Player Plugin by A. Lätsch 2007
#                   modified by Volker Christian 2008
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================


from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.config import config
from Components.config import ConfigElement
from Components.config import ConfigSubsection
from Components.config import ConfigSubList
from Components.config import ConfigInteger
from Components.config import ConfigText
from Components.config import ConfigIP
from Components.config import ConfigSelection
from Components.config import ConfigYesNo
from Components.config import configfile
from Components.config import getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.Button import Button

from VlcServer import VlcServer

import gettext


class ConfigMutable(ConfigElement):
	def __init__(self, configElementDict, defaultKey):
		ConfigElement.__init__(self)
		self.configElementDict = configElementDict
		self.currentConfig = self.configElementDict[defaultKey]
		self.currentKey = defaultKey
		self.defaultConfig = self.currentConfig
		self.defaultKey = self.currentKey

	def addConfigElement(self, key, configElement):
		self.elements[key] = configElement

	def setAsCurrent(self, key):
		if self.configElementDict.has_key(key):
			self.currentConfig = self.configElementDict[key]
			self.currentKey = key
			self.saved_value = self.currentConfig.saved_value
			
	def setValue(self, val):
		self.currentConfig.value = val
		self.changed()

	def set_Value(self, val):
		self.currentConfig._value = val
		self.changed()

	def getValue(self):
		return self.currentConfig.value
	
	def get_Value(self):
		return self.currentConfig._value

	_value = property(get_Value, set_Value)
	
	def fromstring(self, value):
		return self.currentConfig.fromstring(value)

	def load(self):
		self.currentConfig.saved_value = self.saved_value
		self.currentConfig.load()

	def tostring(self, value):
		return self.currentConfig.tostring(value)

	def save(self):
		self.currentConfig.save()
		self.defaultConfig = self.currentConfig
		self.saved_value = self.currentConfig.saved_value

	def cancel(self):
		self.currentConfig = self.defaultConfig
		self.currentKey = self.defaultKey
		self.load()
		
	def isChanged(self):
		return self.currentConfig.isChanged()

	def changed(self):
		for x in self.notifiers:
			x(self)
			
	def addNotifier(self, notifier, initial_call = True):
		assert callable(notifier), "notifiers must be callable"
		self.notifiers.append(notifier)
		if initial_call:
			notifier(self)

	def disableSave(self):
		self.currentConfig.disableSave()

	def __call__(self, selected):
		return self.currentConfig.getMulti(selected)

	def onSelect(self, session):
		self.currentConfig.onSelect(session)

	def onDeselect(self, session):
		self.currentConfig.onDeselect(session)

	def handleKey(self, key):
		self.currentConfig.handleKey(key)

	def getHTML(self, id):
		return self.currentConfig.getHTML(id)

	def genText(self):
		return self.currentConfig.genText()

	def getText(self):
		return self.currentConfig.getText()

	def getMulti(self, selected):
		return self.currentConfig.getMulti(selected)

	def onSelect(self, session):
		self.currentConfig.onSelect(session)

	def onDeselect(self, session):
		self.currentConfig.onDeselect(session)


class ConfigSelectionExtended(ConfigSelection):
	def __init__(self, choices, default = None):
		ConfigSelection.__init__(self, choices, default)

	def deleteNotifier(self, notifier):
		self.notifiers.remove(notifier)


def _(txt):
	t = gettext.dgettext("VlcPlayer", txt)
	if t == txt:
		print "[VLC] fallback to default translation for", txt
		t = gettext.gettext(txt)
	return t


class VlcPluginInfo():
	def __init__(self):
		pass

vlcPluginInfo = VlcPluginInfo()


class VlcServerConfig():
	def __init__(self):
		self.serverlist = []
		config.plugins.vlcplayer = ConfigSubsection()
		config.plugins.vlcplayer.servercount = ConfigInteger(0)
		config.plugins.vlcplayer.servers = ConfigSubList()
		for servernum in range(0, config.plugins.vlcplayer.servercount.value):
			self.new()

	# Add a new server or load a configsection if existing
	def new(self):
		newServerConfigSubsection = ConfigSubsection()
		config.plugins.vlcplayer.servers.append(newServerConfigSubsection)
		newServerConfigSubsection.name = ConfigText("Server " + str(self.__getServerCount()), False)
		newServerConfigSubsection.addressType = ConfigSelectionExtended({"DNS": "FQDN", "IP": "IP-Address"}, "IP")
		newServerConfigSubsection.hostip = ConfigMutable({"IP": ConfigIP([192,168,1,1]), "DNS": ConfigText("dnsname", False)},
											newServerConfigSubsection.addressType.value)
		newServerConfigSubsection.httpport = ConfigInteger(8080, (0,65535))
		newServerConfigSubsection.basedir = ConfigText("/", False)
		newServerConfigSubsection.dvdPath = ConfigText("", False)
		newServerConfigSubsection.transcodeVideo = ConfigYesNo()
		newServerConfigSubsection.transcodeAudio = ConfigYesNo(True)
		newServerConfigSubsection.videocodec = ConfigSelection({"mp1v": "MPEG1", "mp2v": "MPEG2"}, "mp2v")
		newServerConfigSubsection.videobitrate = ConfigInteger(1000, (100, 9999))
		newServerConfigSubsection.audiocodec = ConfigSelection({"mpga":"MP1", "mp2a": "MP2", "mp3": "MP3"}, "mp2a")
		newServerConfigSubsection.audiobitrate = ConfigInteger(128, (64, 320))
		newServerConfigSubsection.samplerate = ConfigSelection({"0":"as Input", "44100": "44100", "48000": "48000"}, "0")
		newServerConfigSubsection.audiochannels = ConfigInteger(2, (1, 9))
		newServerConfigSubsection.videowidth = ConfigSelection(["352", "704", "720"])
		newServerConfigSubsection.videoheight = ConfigSelection(["288", "576"])
		newServerConfigSubsection.framespersecond = ConfigInteger(25, (1, 99))
		newServerConfigSubsection.aspectratio = ConfigSelection(["none", "16:9", "4:3"], "none")
		newServerConfigSubsection.soverlay = ConfigYesNo()
		newServer = VlcServer(newServerConfigSubsection)

		self.serverlist.append(newServer)

		return newServer

	# Add was canceled or existing server should be removed
	def delete(self, server):
		config.plugins.vlcplayer.servers.remove(server.getCfg())
		self.serverlist.remove(server)
		self.__save()

	# Edit or Add should complete
	def save(self, server):
		server.getCfg().save()
		self.__save()

	def getServerlist(self):
		return self.serverlist

	def __save(self):
		config.plugins.vlcplayer.servercount.value = self.__getServerCount()
		config.plugins.vlcplayer.servercount.save()
		configfile.save()

	def __getServerCount(self):
		return len(config.plugins.vlcplayer.servers)


class VlcServerConfigScreen(Screen, ConfigListScreen):
	skin = """
		<screen name="VLCServerConfigScreen" position="80,100" size="560,320" title="Edit VLC Server">
			<widget name="config" position="10,10" size="520,250" scrollbarMode="showOnDemand" />
			<ePixmap name="red"    position="0,280"   zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green"  position="140,280" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,280" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue"   position="420,280" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,280" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,280" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="280,280" zPosition="5" size="140,40" valign="center" halign="center"  font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="420,280" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, server):
		Screen.__init__(self, session)
		self.server = server
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"cancel": self.keyCancel
		}, -2)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")

		cfglist = []
		cfglist.append(getConfigListEntry(_("Symbolic Servername"), server.name()))
		cfglist.append(getConfigListEntry(_("Enter VLC-Server as FQDN or IP-Address"), server.addressType()))
		self.hostConfigListEntry = getConfigListEntry(_("Server Address"), server.host())
		cfglist.append(self.hostConfigListEntry)
		cfglist.append(getConfigListEntry(_("HTTP Port"), server.httpPort()))
		cfglist.append(getConfigListEntry(_("Movie Directory"), server.basedir()))
		cfglist.append(getConfigListEntry(_("DVD Device (leave empty for default)"), server.dvdPath()))

		cfglist.append(getConfigListEntry(_("Transcode MPEG/DVD Video"), server.transcodeVideo()))
		cfglist.append(getConfigListEntry(_("Video Codec"), server.videoCodec()))
		cfglist.append(getConfigListEntry(_("Video Bitrate"), server.videoBitrate()))
		cfglist.append(getConfigListEntry(_("Video Width"), server.videoWidth()))
		cfglist.append(getConfigListEntry(_("Video Height"), server.videoHeight()))
		#cfglist.append(getConfigListEntry(_("Frames per Second"), config.plugins.vlcplayer.fps))
		cfglist.append(getConfigListEntry(_("Correct aspect ratio to"), server.aspectRatio()))
		cfglist.append(getConfigListEntry(_("Subtitle overlay"), server.sOverlay()))

		cfglist.append(getConfigListEntry(_("Transcode MPEG/DVD Audio"), server.transcodeAudio()))
		cfglist.append(getConfigListEntry(_("Audio Codec"), server.audioCodec()))
		cfglist.append(getConfigListEntry(_("Audio Bitrate"), server.audioBitrate()))
		cfglist.append(getConfigListEntry(_("Audio Samplerate"), server.samplerate()))
		cfglist.append(getConfigListEntry(_("Audio Channels"), server.audioChannels()))

		ConfigListScreen.__init__(self, cfglist, session)

		server.addressType().addNotifier(self.switchAddressType, False)
		
		self.onClose.append(self.__onClose)
		
	def __onClose(self):
		self.server.addressType().deleteNotifier(self.switchAddressType)

	def switchAddressType(self, configElement):
		if configElement.value == "IP":
			self.server.host().setAsCurrent("IP")
		else:
			self.server.host().setAsCurrent("DNS")
		self["config"].invalidate(self.hostConfigListEntry)

	def keySave(self):
		self.close(True, self.server)

	def keyCancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close(False, self.server)
