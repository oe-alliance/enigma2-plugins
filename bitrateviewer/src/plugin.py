from __future__ import absolute_import
#
#  BitrateViewer E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2010
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from enigma import iServiceInformation, getDesktop
from .bitratecalc import eBitrateCalculator

class BitrateCalculator(Screen):
	sz_w = getDesktop(0).size().width()
	if sz_w == 1280:
		left = 1000
	elif sz_w == 1024:
		left = 774
	else:
		left = 470
	skin = """
		<screen position="%d,40" size="235,68" flags="wfNoBorder" title="BitrateViewer">
			<widget render="Label" source="video_caption" position="10,10" zPosition="1" size="70,23" font="Regular;22" transparent="1"/>
			<widget render="Label" source="audio_caption" position="10,35" zPosition="1" size="70,23" font="Regular;22" transparent="1"/>
			<widget render="Label" source="video" position="75,10" zPosition="1" size="150,23" font="Regular;22" halign="right" transparent="1"/>
			<widget render="Label" source="audio" position="75,35" zPosition="1" size="150,23" font="Regular;22" halign="right" transparent="1"/>
		</screen>""" % left

	def __init__(self, session, args = None):
		Screen.__init__(self, session)
		self["video_caption"] = StaticText("Video:")
		self["audio_caption"] = StaticText("Audio:")
		self["video"] = StaticText()
		self["audio"] = StaticText()
		self["actions"] = ActionMap(["WizardActions"],
		{
			"back": self.close,
			"ok": self.close,
			"right": self.close,
			"left": self.close,
			"down": self.close,
			"up": self.close,

		}, -1)
		ref = session.nav.getCurrentlyPlayingServiceReference()
		vpid = apid = dvbnamespace = tsid = onid = -1
		service = session.nav.getCurrentService()
		if service:
			serviceInfo = service.info()
			vpid = serviceInfo.getInfo(iServiceInformation.sVideoPID)
			apid = serviceInfo.getInfo(iServiceInformation.sAudioPID)
		if not ref.getPath():
			tsid = ref.getData(2)
			onid = ref.getData(3)
			dvbnamespace = ref.getData(4)
		if vpid:
			self.videoBitrate = eBitrateCalculator(vpid, dvbnamespace, tsid, onid, 1000, 1024*1024) # pid, dvbnamespace, tsid, onid, refresh intervall, buffer size
			self.videoBitrate.callback.append(self.getVideoBitrateData)
		if apid:
			self.audioBitrate = eBitrateCalculator(apid, dvbnamespace, tsid, onid, 1000, 64*1024)
			self.audioBitrate.callback.append(self.getAudioBitrateData)

	def getVideoBitrateData(self, value, status): # value = rate in kbit/s, status ( 1  = ok || 0 = nok (zapped?))
		if status:
			self["video"].text = "%d kbit/s" % value
		else:
			self.videoBitrate = None

	def getAudioBitrateData(self, value, status): 
		if status:
			self["audio"].text = "%d kbit/s" % value
		else:
			self.audioBitrate = None


def main(session,**kwargs):
	session.open(BitrateCalculator)

def Plugins(**kwargs):
	list = [PluginDescriptor(name="BitrateViewer", description=_("BitrateViewer"), 
		where = [PluginDescriptor.WHERE_EXTENSIONSMENU ], fnc=main)]
	return list
