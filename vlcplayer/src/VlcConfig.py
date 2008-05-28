# -*- coding: ISO-8859-1 -*-
#===============================================================================
# VLC Player Plugin by A. Lätsch 2007
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

from Screens.Screen import Screen
from Components.config import config
from Components.config import getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.config import configfile
from Components.Button import Button
from Plugins.Extensions.VlcPlayer import addVlcServerConfig
from Screens.MessageBox import MessageBox

class VLCSettings(Screen, ConfigListScreen):
	skin = """
		<screen name="VLCSettings" position="80,140" size="560,330" title="VLC Settings">
			<widget name="config" position="10,10" size="540,250" scrollbarMode="showOnDemand" />
			<ePixmap name="red"    position="0,280"   zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green"  position="140,280" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,280" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue"   position="420,280" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,280" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,280" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="280,280" zPosition="5" size="140,40" valign="center" halign="center"  font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="420,280" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""
	
	def __init__(self, session):
		Screen.__init__(self, session)
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
		cfglist.append(getConfigListEntry(_("Video Codec"), config.plugins.vlcplayer.vcodec))
		cfglist.append(getConfigListEntry(_("Video Bitrate"), config.plugins.vlcplayer.vb))
		cfglist.append(getConfigListEntry(_("Video Width"), config.plugins.vlcplayer.width))
		cfglist.append(getConfigListEntry(_("Video Height"), config.plugins.vlcplayer.height))
		#cfglist.append(getConfigListEntry(_("Frames per Second"), config.plugins.vlcplayer.fps))
		cfglist.append(getConfigListEntry(_("Correct aspect ratio to"), config.plugins.vlcplayer.aspect))
		cfglist.append(getConfigListEntry(_("Subtitle overlay"), config.plugins.vlcplayer.soverlay))
		cfglist.append(getConfigListEntry(_("Audio Codec"), config.plugins.vlcplayer.acodec))
		cfglist.append(getConfigListEntry(_("Audio Bitrate"), config.plugins.vlcplayer.ab))
		cfglist.append(getConfigListEntry(_("Audio Samplerate"), config.plugins.vlcplayer.samplerate))
		cfglist.append(getConfigListEntry(_("Audio Channels"), config.plugins.vlcplayer.channels))
		ConfigListScreen.__init__(self, cfglist, session)

	def keySave(self):
		ConfigListScreen.keySave(self)
		configfile.save()


class VLCServerConfig(Screen, ConfigListScreen):
	skin = """
		<screen name="VLCServerConfig" position="80,148" size="560,280" title="Edit VLC Server">
			<widget name="config" position="10,10" size="520,210" scrollbarMode="showOnDemand" />
			<ePixmap name="red"    position="0,240"   zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap name="green"  position="140,240" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap name="yellow" position="280,240" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap name="blue"   position="420,240" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,240" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="140,240" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="280,240" zPosition="5" size="140,40" valign="center" halign="center"  font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="420,240" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""
	
	def __init__(self, session, servernum):
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.keySave,
			"red": self.keyCancel,
			"blue": self.keyDelete,
			"cancel": self.keyCancel
		}, -2)

		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button("")
		self["key_blue"] = Button(_("Delete"))

		if servernum is None:
			i = addVlcServerConfig()
		else:
			i = servernum
		cfglist = []
		cfglist.append(getConfigListEntry(_("Hostname or IP"), config.plugins.vlcplayer.servers[i].host))
		cfglist.append(getConfigListEntry(_("HTTP Port"), config.plugins.vlcplayer.servers[i].httpport))
		cfglist.append(getConfigListEntry(_("Movie Directory"), config.plugins.vlcplayer.servers[i].basedir))
		#cfglist.append(getConfigListEntry(_("Method"), config.plugins.vlcplayer.servers[i].method))
		#cfglist.append(getConfigListEntry(_("Admin (telnet) Port"), config.plugins.vlcplayer.servers[i].adminport))
		#cfglist.append(getConfigListEntry(_("Admin Password"), config.plugins.vlcplayer.servers[i].adminpwd))
		ConfigListScreen.__init__(self, cfglist, session)
		self.servernum = i

	def keySave(self):
		config.plugins.vlcplayer.servercount.save()
		for x in self["config"].list:
			if isinstance(x[1].value, str):
				x[1].value = x[1].value.strip()
			x[1].save()
		self.close()
		configfile.save()

	def cancelConfirm(self, result):
		if result:
			config.plugins.vlcplayer.servercount.cancel()
		self.callback = None
		ConfigListScreen.cancelConfirm(self, result)

	def keyDelete(self):
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this Server config?"))

	def deleteConfirm(self, result):
		if not result:
			return
		del(config.plugins.vlcplayer.servers[self.servernum])
		config.plugins.vlcplayer.servers.save()
		config.plugins.vlcplayer.servercount.value = config.plugins.vlcplayer.servercount.value - 1;
		config.plugins.vlcplayer.servercount.save()
		configfile.save()
		self.close()
