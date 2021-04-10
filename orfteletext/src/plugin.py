#######################################################################
#
#    ORFteletext for Dreambox-Enigma2
#    Coded by Vali (c)2010
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#  To view a copy of this license, visit http://creativecommons.org/licenses/by-nc-sa/3.0/
#  or send a letter to Creative Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#
#######################################################################


from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import NumberActionMap
from Components.AVSwitch import AVSwitch
from Components.Pixmap import Pixmap
from Components.MenuList import MenuList
from Components.Label import Label
from Tools.Directories import fileExists
from enigma import ePicLoad, getDesktop, eEnv
from os import system as os_system
from Components.config import config, ConfigSubsection, ConfigText, ConfigInteger


config.plugins.ORFteletext = ConfigSubsection()
config.plugins.ORFteletext.startHZ = ConfigInteger(default=100)
config.plugins.ORFteletext.startNZ = ConfigInteger(default=1)
config.plugins.ORFteletext.adr = ConfigText(default="ORF")


def Plugins(**kwargs):
	return [PluginDescriptor(name="ORF-Teletext", description=_("ORF-Teletext"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main), ]


def main(session, **kwargs):
	session.open(ORFteletextScreen)


class ORFteletextScreen(Screen):
	if (getDesktop(0).size().width()) == 1280:
		skin = """
			<screen flags="wfNoBorder" position="0,0" size="1280,720" title="ORF-Teletext" backgroundColor="#00121214">
				<widget backgroundColor="#ffffffff" position="30,163" render="Pig" size="700,394" source="session.VideoPicture" zPosition="1"/>
				<widget name="Picture" position="740,192" size="480,336" zPosition="1"/>
				<widget name="seite" position="770,93" size="200,24" font="Regular;22" transparent="1"/>
				<widget name="wohin" position="770,123" size="200,24" font="Regular;22" foregroundColor="#ff4a3c" transparent="1"/>
				<eLabel font="Regular;20" foregroundColor="#00ff4A3C" position="320,620" size="120,26" transparent="1" text="NEWS"/>
				<eLabel font="Regular;20" foregroundColor="#0056C856" position="320,650" size="120,26" transparent="1" text="WEATHER"/>
				<eLabel font="Regular;20" foregroundColor="#00ffc000" position="760,620" size="120,26" transparent="1" text="SPORT"/>
				<eLabel font="Regular;20" foregroundColor="#00879ce1" position="760,650" size="120,26" transparent="1" text="INDEX"/>
			</screen>"""
	elif (getDesktop(0).size().width()) == 1024:
		skin = """
			<screen flags="wfNoBorder" position="0,0" size="1024,576" title="ORF-Teletext" backgroundColor="#00121214">
				<widget backgroundColor="#ffffffff" position="30,156" render="Pig" size="470,264" source="session.VideoPicture" zPosition="1"/>
				<widget name="Picture" position="504,120" size="480,336" zPosition="1"/>
				<widget name="seite" position="504,50" size="200,24" font="Regular;22" transparent="1"/>
				<widget name="wohin" position="504,75" size="200,24" font="Regular;22" foregroundColor="#ff4a3c" transparent="1"/>
				<eLabel font="Regular;20" foregroundColor="#00ff4A3C" position="220,480" size="120,26" transparent="1" text="NEWS"/>
				<eLabel font="Regular;20" foregroundColor="#0056C856" position="220,510" size="120,26" transparent="1" text="WEATHER"/>
				<eLabel font="Regular;20" foregroundColor="#00ffc000" position="504,480" size="120,26" transparent="1" text="SPORT"/>
				<eLabel font="Regular;20" foregroundColor="#00879ce1" position="504,510" size="120,26" transparent="1" text="INDEX"/>
			</screen>"""
	else:
		skin = """
			<screen flags="wfNoBorder" position="0,0" size="720,576" title="ORF-Teletext" backgroundColor="#00121214">
				<widget name="seite" position="250,50" size="200,24" font="Regular;22" transparent="1"/>
				<widget name="wohin" position="250,75" size="200,24" font="Regular;22" foregroundColor="#ff4a3c" transparent="1"/>
				<widget backgroundColor="#ffffffff" position="60,156" render="Pig" size="160,120" source="session.VideoPicture" zPosition="1"/>
				<widget name="Picture" position="250,120" size="480,336" zPosition="1"/>
				<eLabel font="Regular;20" foregroundColor="#00ff4A3C" position="120,480" size="120,26" transparent="1" text="NEWS"/>
				<eLabel font="Regular;20" foregroundColor="#0056C856" position="120,510" size="120,26" transparent="1" text="WEATHER"/>
				<eLabel font="Regular;20" foregroundColor="#00ffc000" position="504,480" size="120,26" transparent="1" text="SPORT"/>
				<eLabel font="Regular;20" foregroundColor="#00879ce1" position="504,510" size="120,26" transparent="1" text="INDEX"/>
			</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["seite"] = Label("100")
		self["wohin"] = Label("")
		self.seite = config.plugins.ORFteletext.startHZ.value
		self.strseite = ""
		self.subseite = config.plugins.ORFteletext.startNZ.value
		self.EXscale = (AVSwitch().getFramebufferScale())
		self.EXpicload = ePicLoad()
		self["Picture"] = Pixmap()
		self["actions"] = NumberActionMap(["DirectionActions", "ColorActions", "OkCancelActions", "NumberActions", "EPGSelectActions"],
		{
			"ok": self.showMe,
			"cancel": self.raus,
			"left": self.seiteMinus,
			"right": self.seitePlus,
			"up": self.vor,
			"down": self.zurueck,
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
			"0": self.keyNumberGlobal,
			"red": self.rot,
			"green": self.gruen,
			"yellow": self.gelb,
			"blue": self.blau,
			"info": self.Info
		}, -1)
		if fileExists("/tmp/bild"):
			self.whatPic = "/tmp/bild"
		else:
			self.whatPic = eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/ORFteletext/nodata.png")
		self.EXpicload.PictureData.get().append(self.DecodeAction)
		self.onLayoutFinish.append(self.firstStart)

	def firstStart(self):
		self.lade2(self.seite, self.subseite)

	def Show_Picture(self):
		if self.whatPic is not None:
			self.EXpicload.setPara([self["Picture"].instance.size().width(), self["Picture"].instance.size().height(), self.EXscale[0], self.EXscale[1], 0, 1, "#121214"])
			self.EXpicload.startDecode(self.whatPic)

	def DecodeAction(self, pictureInfo=" "):
		if self.whatPic is not None:
			ptr = self.EXpicload.getData()
			self["Picture"].instance.setPixmap(ptr)

	def raus(self):
		os_system("rm -f /tmp/bild")
		config.plugins.ORFteletext.startHZ.value = self.seite
		config.plugins.ORFteletext.startNZ.value = self.subseite
		config.plugins.ORFteletext.adr.save()
		config.plugins.ORFteletext.startHZ.save()
		config.plugins.ORFteletext.startNZ.save()
		self.close()

	def lade2(self, hs, ns):
		os_system("rm -f /tmp/bild")
		hz = str(hs)
		lz = hz[0]
		nz = str(ns)
		if config.plugins.ORFteletext.adr.value == "ORF":
			adr = "http://teletext.orf.at/" + lz + "00/" + hz + "_000" + nz + ".png"
		elif config.plugins.ORFteletext.adr.value == "SAT1":
			adr = "http://www.sat1.at/service/teletext/cache_de/" + hz + "_0" + nz + ".png" 
		neu = "wget -O /tmp/bild " + adr
		self["seite"].setText(hz + "-" + nz + " at " + config.plugins.ORFteletext.adr.value)
		os_system(neu)
		if fileExists("/tmp/bild"):
			self.whatPic = "/tmp/bild"
		else:
			self.whatPic = eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/ORFteletext/nodata.png")
		self.Show_Picture()

	def showMe(self):
		self.lade2(self.seite, self.subseite)

	def seitePlus(self):
		if self.subseite < 9:
			self.subseite = self.subseite + 1
		else:
			self.subseite = 1
		self.lade2(self.seite, self.subseite)

	def seiteMinus(self):
		if self.subseite > 1:
			self.subseite = self.subseite - 1
		else:
			self.subseite = 1
		self.lade2(self.seite, self.subseite)

	def keyNumberGlobal(self, number):
		if len(self.strseite) < 3:
			self.strseite = self.strseite + str(number)
			self["wohin"].setText(self.strseite)
		if len(self.strseite) == 3:
			self.seite = int(self.strseite)
			self.subseite = 1
			self.lade2(self.seite, self.subseite)
			self.strseite = ""
			self["wohin"].setText(self.strseite)
		if len(self.strseite) > 3:
			self.strseite = ""
			self["wohin"].setText(self.strseite)

	def vor(self):
		if self.seite < 900:
			self.seite = self.seite + 1
		else:
			self.seite = 100
		self.subseite = 1
		self.lade2(self.seite, self.subseite)

	def zurueck(self):
		if self.seite > 100:
			self.seite = self.seite - 1
		else:
			self.seite = 100
		self.subseite = 1
		self.lade2(self.seite, self.subseite)	

	def rot(self):
		self.seite = 111
		self.subseite = 1
		self.lade2(self.seite, self.subseite)

	def gruen(self):
		if config.plugins.ORFteletext.adr.value == "ORF":
			self.seite = 600
		elif config.plugins.ORFteletext.adr.value == "SAT1":
			self.seite = 150
		self.subseite = 1
		self.lade2(self.seite, self.subseite)

	def gelb(self):
		self.seite = 200
		self.subseite = 1
		self.lade2(self.seite, self.subseite)

	def blau(self):
		if config.plugins.ORFteletext.adr.value == "ORF":
			self.seite = 890
		elif config.plugins.ORFteletext.adr.value == "SAT1":
			self.seite = 104
		self.subseite = 1
		self.lade2(self.seite, self.subseite)
			
	def Info(self):
		if config.plugins.ORFteletext.adr.value == "ORF":
			config.plugins.ORFteletext.adr.value = "SAT1"
			config.plugins.ORFteletext.adr.save()
		else:
			config.plugins.ORFteletext.adr.value = "ORF"
			config.plugins.ORFteletext.adr.save()
		self.seite = 100
		self.subseite = 1
		self.showMe()




