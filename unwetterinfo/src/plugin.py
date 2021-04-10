# -*- coding: utf-8 -*-
#
# Wetter Infos von
# www.unwetterzentrale.de und www.uwz.at
#
# Author: barabas
#

import xml.sax.saxutils as util

from Plugins.Plugin import PluginDescriptor
from twisted.web.client import getPage
from twisted.internet import reactor
from Screens.Screen import Screen
from Screens.Console import Console
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.AVSwitch import AVSwitch
from Components.Pixmap import Pixmap
from enigma import eTimer, ePicLoad
from re import sub, search, findall
from os import unlink

###############################################################################

class PictureView(Screen):
	skin = """
		<screen position="center,center" size="720,576" flags="wfNoBorder" title="UWZ" >
			<eLabel position="0,0" zPosition="1" size="720,576" backgroundColor="black" />
			<ePixmap position="655,540" zPosition="2" size="36,20" pixmap="skin_default/buttons/key_info.png" alphatest="on" />
			<widget name="picture" position="80,10" zPosition="2" size="550,550" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self.picfile = "/tmp/uwz.png"

		self["picture"] = Pixmap()

		self["actions"] = ActionMap(["OkCancelActions", "MovieSelectionActions"],
		{
			"cancel": self.exit,
			"ok": self.exit,
			"showEventInfo": self.HelpView,
		}, -1)

		self.picload = ePicLoad()
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((550, 550, sc[0], sc[1], 0, 0, '#ff000000'))
		self.picload.PictureData.get().append(self.gotPic)
		self.onLayoutFinish.append(self.getPic)

	def getPic(self):
		self.picload.startDecode(self.picfile)

	def gotPic(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr:
			self["picture"].instance.setPixmap(ptr)

	def HelpView(self):
		self.session.openWithCallback(self.getPic, HelpPictureView)

	def exit(self):
		self.close()

class HelpPictureView(Screen):
	skin = """
		<screen position="center,center" size="700,320" title="Warnstufen" >
			<eLabel position="0,0" zPosition="1" size="700,320" backgroundColor="black" />
			<ePixmap position="80,270" zPosition="2" size="45,45" pixmap="skin_default/vkey_left.png" alphatest="on" />
			<ePixmap position="328,270" zPosition="2" size="45,45" pixmap="skin_default/vkey_esc.png" alphatest="on" />
			<ePixmap position="575,270" zPosition="2" size="45,45" pixmap="skin_default/vkey_right.png" alphatest="on" />
			<widget name="picture" position="5,20" zPosition="2" size="690,225" />
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self["picture"] = Pixmap()

		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"],
		{
			"cancel": self.exit,
			"ok": self.exit,
			"left": self.prevPic,
			"right": self.nextPic
		}, -1)

		self.list = (
			pluginpath + "/W_gruen.gif",
			pluginpath + "/W_gelb.gif",
			pluginpath + "/W_orange.gif",
			pluginpath + "/W_rot.gif",
			pluginpath + "/W_violett.gif"
		)
		self.index = 0

		self.picload = ePicLoad()
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((690, 225, sc[0], sc[1], 0, 0, '#ff000000'))
		self.picload.PictureData.get().append(self.gotPic)

		self.onShown.append(self.getPic)

	def getPic(self):
		self.picload.startDecode(self.list[self.index])

	def gotPic(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr:
			self["picture"].instance.setPixmap(ptr)

	def nextPic(self):
		self.index += 1
		if self.index > 4:
			self.index = 0
		self.getPic()

	def prevPic(self):
		self.index -= 1
		if self.index < 0:
			self.index = 4
		self.getPic()

	def exit(self):
		self.close()

class UnwetterMain(Screen):
	skin = """
		<screen position="center,center" size="530,430" title="Unwetterzentrale" >
			<widget name="hmenu" position="5,0" zPosition="1" size="530,220" scrollbarMode="showOnDemand" />
			<widget name="thumbnail" position="185,250" zPosition="2" size="140,150" />
			<widget name="thumbland" position="435,390" zPosition="2" size="90,40" />
			<ePixmap position="20,380" zPosition="2" size="36,20" pixmap="skin_default/buttons/key_menu.png" alphatest="on" />
			<widget name="statuslabel" position="5,410" zPosition="2" size="530,20" font="Regular;16" halign="left"/>
		</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		self["statuslabel"] = Label()
		self["thumbland"] = Pixmap()
		self["thumbnail"] = Pixmap()
		self["hmenu"] = MenuList([])
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "MovieSelectionActions"],
		{
			"ok": self.ok,
			"up": self.up,
			"right": self.rightDown,
			"left": self.leftUp,
			"down": self.down,
			"cancel": self.exit,
			"contextMenu": self.switchDeA,
		}, -1)

		self.loadinginprogress = False
		self.picfile = "/tmp/uwz.png"
		self.picweatherfile = pluginpath + "/wetterreport.jpg"
		self.reportfile = "/tmp/uwz.report"

		self.picload = ePicLoad()

#		self.onLayoutFinish.append(self.go)

		self.ThumbTimer = eTimer()
		self.ThumbTimer.callback.append(self.showThumb)

		self.switchDeA(load=True)

	def hauptmenu(self, output):
		self.loadinginprogress = False
		trans = {'&szlig;': 'ß', '&auml;': 'ä', '&ouml;': 'ö', '&uuml;': 'ü', '&Auml;': 'Ä', '&Ouml;': 'Ö', '&Uuml;': 'Ü'}
		output = util.unescape(output, trans)

		if self.land == "de":
			startpos = output.find('<div id="navigation">')
			endpos = output.find('<a class="section-link" title="FAQ"', startpos)
			bereich = output[startpos:endpos]
			a = findall(r'href=(?P<text>.*?)</a>', bereich)
			for x in a:
				x = x.replace('">', "#").replace('"', "").split('#')
				if not len(x) > 1:
					break
				if x[0] == "index.html":
					continue
				name = x[1]
				link = self.baseurl + x[0]
				self.menueintrag.append(name)
				self.link.append(link)
		else:
			self.menueintrag.append("Lagebericht")
			self.link.append(self.weatherreporturl)

			startpos = output.find('<div id="select_dropdownprovinces"')
			endpos = output.find('</div>', startpos)
			bereich = output[startpos:endpos]
			a = findall(r'<a href=(?P<text>.*?)</a>', bereich)
			for x in a[1:13]:
				x = x.replace('">', "#").replace('"', "")
				if x != '#&nbsp;':
						x = x.split('#')
						if not len(x) > 1:
							break
						name = x[1]
						link = x[0]
						self.menueintrag.append(name)
						self.link.append(link)

		self["statuslabel"].setText("")
		self["hmenu"].l.setList(self.menueintrag)
		self["hmenu"].instance.moveSelectionTo(0)
		self.showThumbLand()

	def ok(self):
		self.go()
		c = self["hmenu"].getCurrent()
		if c is not None:
			x = self.menueintrag.index(c)
			if x != 0:
				self.session.open(PictureView)
			else:
				self.downloadWeatherReport()

	def go(self):
		c = self["hmenu"].getCurrent()
		if c is not None:
			x = self.menueintrag.index(c)
			# Wetterlagebericht ist Index 0
			if x != 0:
				url = self.link[x]
				self["statuslabel"].setText("Loading Data")
				self.downloadPicUrl(url)
			self.ThumbTimer.start(1500, True)

	def up(self):
		self["hmenu"].up()
		self.go()

	def down(self):
		self["hmenu"].down()
		self.go()

	def leftUp(self):
		self["hmenu"].pageUp()
		self.go()

	def rightDown(self):
		self["hmenu"].pageDown()
		self.go()

	def showThumbLand(self):
		picture = ""
		if self.land == "de":
			picture = pluginpath + "/uwz.png"
		else:
			picture = pluginpath + "/uwzat.png"
		picload = self.picload
		sc = AVSwitch().getFramebufferScale()
		picload.setPara((90, 40, sc[0], sc[1], 0, 0, '#ff000000'))
		l = picload.PictureData.get()
		del l[:]
		l.append(self.gotThumbLand)
		picload.startDecode(picture)

	def gotThumbLand(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr:
			self["thumbland"].instance.setPixmap(ptr)

	def showThumb(self):
		picture = ""
		if self.land == "de":
			width = 142
			height = 150
		else:
			width = 142
			height = 135
		c = self["hmenu"].getCurrent()
		if c is not None:
			x = self.menueintrag.index(c)
			if x != 0:
				picture = self.picfile
			else:
				picture = self.picweatherfile
				height = 150

			picload = self.picload
			sc = AVSwitch().getFramebufferScale()
			picload.setPara((width, height, sc[0], sc[1], 0, 0, '#ff000000'))
			l = picload.PictureData.get()
			del l[:]
			l.append(self.gotThumb)
			picload.startDecode(picture)

	def gotThumb(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr:
			self["statuslabel"].setText("")
			self["thumbnail"].show()
			self["thumbnail"].instance.setPixmap(ptr)
		else:
			self["thumbnail"].hide()

	def getPicUrl(self, output):
		self.loadinginprogress = False
		if self.land == "de":
			startpos = output.find('<!-- Anfang msg_Box Content -->')
			endpos = output.find('<!-- Ende msg_Box Content -->', startpos)
			bereich = output[startpos:endpos]
			picurl = search(r'<img src="(?P<text>.*?)" width=', bereich)
			picurl = self.baseurl + picurl.group(1)
		else:
			picurl = search(r'<img class="map mapper" src="(?P<url>.*?)" lang=', output)
			picurl = self.baseurl + picurl.group(1).replace('&amp;', '&')
		self.downloadPic(picurl)

	def getPic(self, output):
		self.loadinginprogress = False
		f = open(self.picfile, "wb")
		f.write(output)
		f.close()

	def getWeatherReport(self, output):
		self.loadinginprogress = False
		trans = {'&szlig;': 'ß', '&auml;': 'ä', '&ouml;': 'ö', '&uuml;': 'ü', '&Auml;': 'Ä', '&Ouml;': 'Ö', '&Uuml;': 'Ü'}
		output = util.unescape(output, trans)
		if self.land == "de":
			startpos = output.find('<!-- Anfang msg_Box Content -->')
			endpos = output.find('<!-- Ende msg_Box Content -->')
			bereich = output[startpos:endpos]
			bereich = bereich.replace('<strong>', '\n')
		else:
			startpos = output.find('<div class="content"')
			endpos = output.find('</div>', startpos)
			bereich = output[startpos:endpos]

		bereich = sub('<br\s*/?>', "\n", bereich)
		bereich = sub('<[^>]*>', "", bereich)
		bereich = sub('Fronten- und Isobarenkarte.*', "", bereich)
		bereich = bereich.strip()
		bereich = sub("\n[\s\n]+", "\n\n", bereich)

		f = open(self.reportfile, "w")
		f.write("%s" % bereich)
		f.close()
		self.session.open(Console, _("Warnlagebericht"), ["cat %s" % self.reportfile])

	def downloadError(self, output):
		self.loadinginprogress = False
		self["statuslabel"].setText("Fehler beim Download")

	def downloadMenu(self):
		self.loadinginprogress = True
		getPage(self.menuurl).addCallback(self.hauptmenu).addErrback(self.downloadError)

	def downloadPicUrl(self, url):
		self.loadinginprogress = True
		getPage(url).addCallback(self.getPicUrl).addErrback(self.downloadError)

	def downloadPic(self, picurl):
		headers = {}
		self.loadinginprogress = True
#		self["statuslabel"].setText("Lade Bild: %s" % picurl)
		if self.land == "a":
			c = self["hmenu"].getCurrent()
			x = self.menueintrag.index(c)
			headers["Referer"] = self.link[x]
		getPage(picurl, headers=headers).addCallback(self.getPic).addErrback(self.downloadError)

	def downloadWeatherReport(self):
		self.loadinginprogress = True
#		self["statuslabel"].setText("Lade Report: %s" % self.weatherreporturl)
		getPage(self.weatherreporturl).addCallback(self.getWeatherReport).addErrback(self.downloadError)

	def switchDeA(self, load=False):
		if load:
			try:
				f = open(pluginpath + "/last.cfg", "r")
				self.land = f.read()
				f.close
			except:
				self.land = "a"

		self.menueintrag = []
		self.link = []

		if self.land == "de":
			self.land = "a"
			self.baseurl = "http://www.uwz.at/"
			self.menuurl = self.baseurl + "karte/alle_warnungen"
			self.weatherreporturl = self.baseurl + "at/de/lagebericht/aktuelle-wetterlage"
		else:
			self.land = "de"
			self.baseurl = "http://www.unwetterzentrale.de/uwz/"
			self.menuurl = self.baseurl + "index.html"
			self.weatherreporturl = self.baseurl + "lagebericht.html"

		if not load:
			f = open(pluginpath + "/last.cfg", "w")
			f.write(self.land)
			f.close

		self.downloadMenu()
		self.ThumbTimer.start(1500, True)

	def exit(self):
		if self.loadinginprogress:
			reactor.callLater(1, self.exit)
		else:
			try:
				unlink(self.picfile)
				unlink(self.reportfile)
			except OSError:
				pass
			self.close()

#############################

def main(session, **kwargs):
	session.open(UnwetterMain)

def Plugins(path, **kwargs):
	global pluginpath
	pluginpath = path
 	return PluginDescriptor(
		name="Unwetterzentrale",
		description="www.unwetterzentrale.de und www.uwz.at",
		icon="uwz.png",
		where=PluginDescriptor.WHERE_PLUGINMENU,
		fnc=main)
