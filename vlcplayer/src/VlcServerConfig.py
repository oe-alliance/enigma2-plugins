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
		newServerConfigSubsection.hostip = ConfigIP([0,0,0,0])
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

	# Edit was canceled
	def cancel(self, server):
		server.getCfg().load()

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
		cfglist.append(getConfigListEntry(_("Server IP"), server.host()))
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

	def keySave(self):
		for x in self["config"].list:
			if isinstance(x[1].value, str):
				x[1].value = x[1].value.strip()
		result = [ True, self.server ]
		self.close(True, self.server)

	def keyCancel(self):
		result = [ False, self.server ]
		self.close(False, self.server)
