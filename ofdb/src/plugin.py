# -*- coding: UTF-8 -*-
from __future__ import print_function
from Plugins.Plugin import PluginDescriptor
from twisted.web.client import downloadPage
from enigma import ePicLoad, eServiceReference
from Screens.Screen import Screen
from Screens.EpgSelection import EPGSelection
from Screens.ChannelSelection import SimpleChannelSelection
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Button import Button
from Components.AVSwitch import AVSwitch
from Components.MenuList import MenuList
from Components.Language import language
from Components.ProgressBar import ProgressBar
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
import re
from six.moves.urllib.parse import quote
import os
import gettext

import six
from six.moves import html_entities


PluginLanguageDomain = "OFDb"
PluginLanguagePath = "Extensions/OFDb/locale"

def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print("[" + PluginLanguageDomain + "] fallback to default translation for " + txt)
		return gettext.gettext(txt)

language.addCallback(localeInit())

class OFDBChannelSelection(SimpleChannelSelection):
	def __init__(self, session):
		SimpleChannelSelection.__init__(self, session, _("Channel Selection"))
		self.skinName = "SimpleChannelSelection"

		self["ChannelSelectEPGActions"] = ActionMap(["ChannelSelectEPGActions"],
			{
				"showEPGList": self.channelSelected
			}
		)

	def channelSelected(self):
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.enterPath(ref)
		elif not (ref.flags & eServiceReference.isMarker):
			self.session.openWithCallback(
				self.epgClosed,
				OFDBEPGSelection,
				ref,
				openPlugin=False
			)

	def epgClosed(self, ret=None):
		if ret:
			self.close(ret)

class OFDBEPGSelection(EPGSelection):
	def __init__(self, session, ref, openPlugin=True):
		EPGSelection.__init__(self, session, ref)
		self.skinName = "EPGSelection"
		self["key_green"].setText(_("Lookup"))
		self.openPlugin = openPlugin

	def infoKeyPressed(self):
		self.timerAdd()

	def timerAdd(self):
		cur = self["list"].getCurrent()
		evt = cur[0]
		sref = cur[1]
		if not evt:
			return

		if self.openPlugin:
			self.session.open(
				OFDB,
				evt.getEventName()
			)
		else:
			self.close(evt.getEventName())

	def onSelectionChanged(self):
		pass

class OFDB(Screen):
	skin = """
		<screen name="OFDb" position="center,center" size="600,420" title="Online-Filmdatenbank Details Plugin" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" zPosition="0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/key_menu.png" position="565,5" zPosition="0" size="35,25" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#9f1313" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#a08500" transparent="1" />
			<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#18188b" transparent="1" />
			<widget name="titellabel" position="10,40" size="330,45" valign="center" font="Regular;22"/>
			<widget name="detailslabel" position="105,90" size="485,140" font="Regular;18" />
			<widget name="castlabel" position="10,235" size="580,155" font="Regular;18" />
			<widget name="extralabel" position="10,40" size="580,350" font="Regular;18" />
			<widget name="ratinglabel" position="340,62" size="250,20" halign="center" font="Regular;18" foregroundColor="#f0b400"/>
			<widget name="statusbar" position="10,404" size="580,16" font="Regular;16" foregroundColor="#cccccc" />
			<widget name="poster" position="4,90" size="96,140" alphatest="on" />
			<widget name="menu" position="10,115" size="580,275" zPosition="3" scrollbarMode="showOnDemand" />
			<widget name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/OFDb/starsbar_empty.png" position="340,40" zPosition="0" size="250,21" transparent="1" alphatest="on" />
			<widget name="stars" position="340,40" size="250,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/OFDb/starsbar_filled.png" transparent="1" />
		</screen>"""

	def __init__(self, session, eventName, args=None):
		self.skin = OFDB.skin
		Screen.__init__(self, session)
		self.eventName = eventName
		self.dictionary_init()
		self["poster"] = Pixmap()
		self.picload = ePicLoad()
		self.picload.PictureData.get().append(self.paintPosterPixmapCB)

		self["stars"] = ProgressBar()
		self["starsbg"] = Pixmap()
		self["stars"].hide()
		self["starsbg"].hide()
		self.ratingstars = -1
		self["titellabel"] = Label(_("The Online-Filmdatenbank"))
		self["detailslabel"] = ScrollLabel("")
		self["castlabel"] = ScrollLabel("")
		self["extralabel"] = ScrollLabel("")
		self["statusbar"] = Label("")
		self["ratinglabel"] = Label("")
		self.resultlist = []
		self["menu"] = MenuList(self.resultlist)
		self["menu"].hide()
		self["key_red"] = Button(_("Exit"))
		self["key_green"] = Button("")
		self["key_yellow"] = Button("")
		self["key_blue"] = Button("")
		# 0 = multiple query selection menu page
		# 1 = movie info page
		# 2 = extra infos page
		self.Page = 0

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "MovieSelectionActions", "DirectionActions"],
		{
			"ok": self.showDetails,
			"cancel": self.close,
			"down": self.pageDown,
			"up": self.pageUp,
			"red": self.close,
			"green": self.showMenu,
			"yellow": self.showDetails,
			"blue": self.showExtras,
			"contextMenu": self.openChannelSelection,
			"showEventInfo": self.showDetails
		}, -1)

		self.getOFDB()

	def dictionary_init(self):
		syslang = language.getLanguage()
		if "de" not in syslang:
			self.OFDBlanguage = ""  # set to empty ("") for english version
		else:
			self.OFDBlanguage = "german." # it's a subdomain, so add a '.' at the end

		self.htmltags = re.compile('<.*?>')

		self.generalinfomask = re.compile(
		'<title>OFDb - (?P<title>.*?)</title>.*?'
		'(?P<g_original>Originaltitel):[\s\S]*?class=\"Daten\">(?P<original>.*?)</td>'
		'(?:.*?(?P<g_country>Herstellungsland):[\s\S]*?class="Daten">(?P<country>.*?)(?:\.\.\.|</td>))*'
		'(?:.*?(?P<g_year>Erscheinungsjahr):[\s\S]*?class="Daten">(?P<year>.*?)</td>)*'
		'(?:.*?(?P<g_director>Regie):[\s\S]*?class="Daten">(?P<director>.*?)(?:\.\.\.|</td>))*'
		, re.DOTALL)

	def resetLabels(self):
		self["detailslabel"].setText("")
		self["ratinglabel"].setText("")
		self["titellabel"].setText("")
		self["castlabel"].setText("")
		self["titellabel"].setText("")
		self["extralabel"].setText("")
		self.ratingstars = -1

	def pageUp(self):
		if self.Page == 0:
			self["menu"].instance.moveSelection(self["menu"].instance.moveUp)
		if self.Page == 1:
			self["castlabel"].pageUp()
			self["detailslabel"].pageUp()
		if self.Page == 2:
			self["extralabel"].pageUp()

	def pageDown(self):
		if self.Page == 0:
			self["menu"].instance.moveSelection(self["menu"].instance.moveDown)
		if self.Page == 1:
			self["castlabel"].pageDown()
			self["detailslabel"].pageDown()
		if self.Page == 2:
			self["extralabel"].pageDown()

	def showMenu(self):
		if ( self.Page == 1 or self.Page == 2 ) and self.resultlist:
			self["menu"].show()
			self["stars"].hide()
			self["starsbg"].hide()
			self["ratinglabel"].hide()
			self["castlabel"].hide()
			self["poster"].hide()
			self["extralabel"].hide()
			self["titellabel"].setText(_("Ambiguous results"))
			self["detailslabel"].setText(_("Please select the matching entry"))
			self["detailslabel"].show()
			self["key_blue"].setText("")
			self["key_green"].setText(_("Title Menu"))
			self["key_yellow"].setText(_("Details"))
			self.Page = 0

	def showDetails(self):
		self["ratinglabel"].show()
		self["castlabel"].show()
		self["detailslabel"].show()

		if self.resultlist and self.Page == 0:
			link = self["menu"].getCurrent()[1]
			title = self["menu"].getCurrent()[0]
			self["statusbar"].setText(_("Re-Query OFDb: %s...") % (title))
			localfile = "/tmp/ofdbquery2.html"
			fetchurl = "http://www.ofdb.de/film/" + link
			print("[OFDb] downloading query " + fetchurl + " to " + localfile)
			downloadPage(six.ensure_binary(fetchurl), localfile).addCallback(self.OFDBquery2).addErrback(self.fetchFailed)
			self["menu"].hide()
			self.resetLabels()
			self.Page = 1

		if self.Page == 2:
			self["extralabel"].hide()
			self["poster"].show()
			if self.ratingstars > 0:
				self["starsbg"].show()
				self["stars"].show()
				self["stars"].setValue(self.ratingstars)

			self.Page = 1

	def showExtras(self):
		if self.Page == 1:
			self["extralabel"].show()
			self["detailslabel"].hide()
			self["castlabel"].hide()
			self["poster"].hide()
			self["stars"].hide()
			self["starsbg"].hide()
			self["ratinglabel"].hide()
			self.Page = 2

	def openChannelSelection(self):
		self.session.openWithCallback(
			self.channelSelectionClosed,
			OFDBChannelSelection
		)

	def channelSelectionClosed(self, ret=None):
		if ret:
			self.eventName = ret
			self.Page = 0
			self.resultlist = []
			self["menu"].hide()
			self["ratinglabel"].show()
			self["castlabel"].show()
			self["detailslabel"].show()
			self["poster"].hide()
			self["stars"].hide()
			self["starsbg"].hide()
			self.getOFDB()

	def getOFDB(self):
		self.resetLabels()
		if self.eventName == "":
			s = self.session.nav.getCurrentService()
			info = s and s.info()
			event = info and info.getEvent(0) # 0 = now, 1 = next
			if event:
				self.eventName = event.getEventName()

		if self.eventName != "":
			try:
				pos = self.eventName.index(" (")
				self.eventName=self.eventName[0:pos]
			except ValueError:
				pass
			if self.eventName[-3:] == "...":
				self.eventName = self.eventName[:-3]
			for article in ["The", "Der", "Die", "Das"]:
				if self.eventName[:4].capitalize() == article + " ":
					self.eventName = self.eventName[4:] + ", " + article

			self["statusbar"].setText(_("Query OFDb: %s...") % (self.eventName))
			try:
				self.eventName = quote(self.eventName)
			except:
				self.eventName = quote(self.eventName.decode('utf8').encode('ascii', 'ignore'))
			localfile = "/tmp/ofdbquery.html"
			fetchurl = "http://www.ofdb.de/view.php?page=suchergebnis&Kat=DTitel&SText=" + self.eventName
			print("[OFDb] Downloading Query " + fetchurl + " to " + localfile)
			downloadPage(six.ensure_binary(fetchurl), localfile).addCallback(self.OFDBquery).addErrback(self.fetchFailed)
		else:
			self["statusbar"].setText(_("Could't get Eventname"))

	def fetchFailed(self, string):
		print("[OFDb] fetch failed " + string)
		self["statusbar"].setText(_("OFDb Download failed"))

	def html2utf8(self, in_html):
		htmlentitynumbermask = re.compile('(&#(\d{1,5}?);)')
		htmlentitynamemask = re.compile('(&(\D{1,5}?);)')

		entities = htmlentitynamemask.finditer(in_html)
		entitydict = {}

		for x in entities:
			entitydict[x.group(1)] = x.group(2)

		for key, name in list(entitydict.items()):
			entitydict[key] = html_entities.name2codepoint[name]

		entities = htmlentitynumbermask.finditer(in_html)

		for x in entities:
			entitydict[x.group(1)] = x.group(2)

		for key, codepoint in list(entitydict.items()):
			in_html = in_html.replace(key, (six.unichr(int(codepoint)).encode('utf8')))

		self.inhtml = in_html

	def OFDBquery(self, string):
		print("[OFDBquery]")
		self["statusbar"].setText(_("OFDb Download completed"))

		self.html2utf8(open("/tmp/ofdbquery.html", "r").read())

		self.generalinfos = self.generalinfomask.search(self.inhtml)

		if self.generalinfos:
			self.OFDBparse()
		else:
			if re.search("<title>OFDb - Suchergebnis</title>", self.inhtml):
				searchresultmask = re.compile("<br>(\d{1,3}\.) <a href=\"film/(.*?)\"(?:.*?)\)\">(.*?)</a>", re.DOTALL)
				searchresults = searchresultmask.finditer(self.inhtml)
				self.resultlist = [(self.htmltags.sub('', x.group(3)), x.group(2)) for x in searchresults]
				self["menu"].l.setList(self.resultlist)
				if len(self.resultlist) == 1:
					self.Page = 0
					self["extralabel"].hide()
					self.showDetails()
				elif len(self.resultlist) > 1:
					self.Page = 1
					self.showMenu()
				else:
					self["detailslabel"].setText(_("No OFDb match."))
					self["statusbar"].setText(_("No OFDb match."))
			else:
				self["detailslabel"].setText(_("OFDb query failed!"))

	def OFDBquery2(self, string):
		self["statusbar"].setText(_("OFDb Re-Download completed"))
		self.html2utf8(open("/tmp/ofdbquery2.html", "r").read())
		self.generalinfos = self.generalinfomask.search(self.inhtml)
		self.OFDBparse()

	def OFDBparse(self):
		print("[OFDBparse]")
		self.Page = 1
		Detailstext = _("No details found.")
		if self.generalinfos:
			self["key_yellow"].setText(_("Details"))
			self["statusbar"].setText(_("OFDb Details parsed"))

			Titeltext = self.generalinfos.group("title")
			if len(Titeltext) > 57:
				Titeltext = Titeltext[0:54] + "..."
			self["titellabel"].setText(Titeltext)

			Detailstext = ""

			genreblockmask = re.compile('Genre\(s\):(?:[\s\S]*?)class=\"Daten\">(.*?)</tr>', re.DOTALL)
			genreblock = genreblockmask.findall(self.inhtml)
			genremask = re.compile('\">(.*?)</a')
			if genreblock:
				genres = genremask.finditer(genreblock[0])
				if genres:
					Detailstext += "Genre: "
					for x in genres:
						Detailstext += self.htmltags.sub('', x.group(1)) + " "

			for category in ("director", "year", "country", "original"):
				if self.generalinfos.group('g_'+category):
					Detailstext += "\n" + self.generalinfos.group('g_'+category) + ": " + self.htmltags.sub('', self.generalinfos.group(category).replace("<br>", ' '))

			self["detailslabel"].setText(Detailstext)

			#if self.generalinfos.group("alternativ"):
				#Detailstext += "\n" + self.generalinfos.group("g_alternativ") + ": " + self.htmltags.sub('',(self.generalinfos.group("alternativ").replace('\n','').replace("<br>",'\n').replace("	 ",' ')))

			ratingmask = re.compile('<td>[\s\S]*notenskala.*(?P<g_rating>Note: )(?P<rating>\d.\d{2,2})[\s\S]*</td>', re.DOTALL)
			rating = ratingmask.search(self.inhtml)
			Ratingtext = _("no user rating yet")
			if rating:
				Ratingtext = rating.group("g_rating") + rating.group("rating") + " / 10"
				self.ratingstars = int(10*round(float(rating.group("rating")), 1))
				self["stars"].show()
				self["stars"].setValue(self.ratingstars)
				self["starsbg"].show()
			self["ratinglabel"].setText(Ratingtext)

			castblockmask = re.compile('Darsteller:[\s\S]*?class=\"Daten\">(.*?)(?:\.\.\.|\xbb)', re.DOTALL)
			castblock = castblockmask.findall(self.inhtml)
			castmask = re.compile('\">(.*?)</a')
			Casttext = ""
			if castblock:
				cast = castmask.finditer(castblock[0])
				if cast:
					for x in cast:
						Casttext += "\n" + self.htmltags.sub('', x.group(1))
					if Casttext != "":
						Casttext = _("Cast: ") + Casttext
					else:
						Casttext = _("No cast list found in the database.")
					self["castlabel"].setText(Casttext)

			postermask = re.compile('<img src=\"(http://img.ofdb.de/film.*?)\" alt', re.DOTALL)
			posterurl = postermask.search(self.inhtml)
			if posterurl and posterurl.group(1).find("jpg") > 0:
				posterurl = posterurl.group(1)
				self["statusbar"].setText(_("Downloading Movie Poster: %s...") % (posterurl))
				localfile = "/tmp/poster.jpg"
				print("[OFDb] downloading poster " + posterurl + " to " + localfile)
				downloadPage(six.ensure_binary(posterurl), localfile).addCallback(self.OFDBPoster).addErrback(self.fetchFailed)
			else:
				print("no jpg poster!")
				self.OFDBPoster(noPoster=True)

		self["detailslabel"].setText(Detailstext)

	def OFDBPoster(self, noPoster=False):
		self["statusbar"].setText(_("OFDb Details parsed"))
		if not noPoster:
			filename = "/tmp/poster.jpg"
		else:
			filename = resolveFilename(SCOPE_PLUGINS, "Extensions/OFDb/no_poster.png")
		sc = AVSwitch().getFramebufferScale()
		self.picload.setPara((self["poster"].instance.size().width(), self["poster"].instance.size().height(), sc[0], sc[1], False, 1, "#00000000"))
		self.picload.startDecode(filename)

	def paintPosterPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr != None:
			self["poster"].instance.setPixmap(ptr)
			self["poster"].show()

	def createSummary(self):
		return OFDbLCDScreen

class OFDbLCDScreen(Screen):
	skin = """
	<screen position="0,0" size="132,64" title="OFDb Plugin">
		<widget name="headline" position="4,0" size="128,22" font="Regular;20"/>
		<widget source="session.Event_Now" render="Label" position="6,26" size="120,34" font="Regular;14" >
			<convert type="EventName">Name</convert>
		</widget>
	</screen>"""

	def __init__(self, session, parent):
		Screen.__init__(self, session)
		self["headline"] = Label(_("OFDb Plugin"))

def eventinfo(session, eventName="", **kwargs):
	if not eventName:
		s = session.nav.getCurrentService()
		if s:
			info = s.info()
			event = info.getEvent(0) # 0 = now, 1 = next
			eventName = event and event.getEventName() or ''
	session.open(OFDB, eventName)

def main(session, eventName="", **kwargs):
	session.open(OFDB, eventName)

def Plugins(**kwargs):
	try:
		return [PluginDescriptor(name="OFDb Details",
				description=_("Query details from the Online-Filmdatenbank"),
				icon="ofdb.png",
				where=PluginDescriptor.WHERE_PLUGINMENU,
				fnc=main),
				PluginDescriptor(name="OFDb Details",
				description=_("Query details from the Online-Filmdatenbank"),
				where=PluginDescriptor.WHERE_EVENTINFO,
				fnc=eventinfo)
				]
	except AttributeError:
		wherelist = [PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU]
		return PluginDescriptor(name="OFDb Details",
				description=_("Query details from the Online-Filmdatenbank"),
				icon="ofdb.png",
				where=wherelist,
				fnc=main)
