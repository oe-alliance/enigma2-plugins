# -*- coding: UTF-8 -*-
from __future__ import print_function
from re import compile, search, DOTALL
from gettext import bindtextdomain
import gettext
from Plugins.Plugin import PluginDescriptor
from requests import get, exceptions
from twisted.internet.reactor import callInThread
from six.moves.urllib.parse import quote
from enigma import ePicLoad, eServiceReference
from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Button import Button
from Components.MenuList import MenuList
from Components.Language import language
from Components.ProgressBar import ProgressBar
from Screens.Screen import Screen
from Screens.EpgSelection import EPGSelection
from Screens.ChannelSelection import SimpleChannelSelection
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

PluginLanguageDomain = "OFDb"
PluginLanguagePath = "Extensions/OFDb/locale"


def localeInit():
	bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


localeInit()
language.addCallback(localeInit)


def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print("[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt))
		return gettext.gettext(txt)


class OFDBChannelSelection(SimpleChannelSelection):
	def __init__(self, session):
		SimpleChannelSelection.__init__(self, session, _("Channel Selection"))
		self.skinName = "SimpleChannelSelection"
		self["ChannelSelectEPGActions"] = ActionMap(["ChannelSelectEPGActions"], {"showEPGList": self.channelSelected})

	def channelSelected(self):
		ref = self.getCurrentSelection()
		if (ref.flags & 7) == 7:
			self.enterPath(ref)
		elif not (ref.flags & eServiceReference.isMarker):
			self.session.openWithCallback(self.epgClosed, OFDBEPGSelection, ref, openPlugin=False)

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
			self.session.open(OFDB, evt.getEventName())
		else:
			self.close(evt.getEventName())

	def onSelectionChanged(self):
		pass


class OFDB(Screen):
	skin = """
		<screen name="OFDb" position="center,center" size="780,600" title="Online-Filmdatenbank Details Plugin" >
			<ePixmap pixmap="skin_default/buttons/red.png" position="20,0" zPosition="0" size="180,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="200,0" zPosition="0" size="180,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="380,0" zPosition="0" size="180,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="560,0" zPosition="0" size="180,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/key_menu.png" position="725,5" zPosition="0" size="55,55" alphatest="on" />
			<widget name="key_red" position="20,0" zPosition="1" size="140,40" font="Regular;22" valign="center" halign="center" backgroundColor="#9f1313" transparent="1" />
			<widget name="key_green" position="200,0" zPosition="1" size="140,40" font="Regular;22" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_yellow" position="380,0" zPosition="1" size="140,40" font="Regular;22" valign="center" halign="center" backgroundColor="#a08500" transparent="1" />
			<widget name="key_blue" position="560,0" zPosition="1" size="140,40" font="Regular;22" valign="center" halign="center" backgroundColor="#18188b" transparent="1" />
			<widget name="titellabel" position="10,55" size="400,60" valign="center" font="Regular;22"/>
			<widget name="detailslabel" position="10,130" size="660,140" font="Regular;20" />
			<widget name="castlabel" position="10,260" size="760,300" font="Regular;20" />
			<widget name="extralabel" position="10,40" size="760,350" font="Regular;20" />
			<widget name="ratinglabel" position="470,85" size="210,24" halign="center" font="Regular;20" foregroundColor="#f0b400"/>
			<widget name="statusbar" position="10,570" size="580,24" font="Regular;20" foregroundColor="#cccccc" />
			<widget name="poster" position="680,60" size="96,140" alphatest="on" />
			<widget name="menu" position="10,115" size="760,275" zPosition="3" scrollbarMode="showOnDemand" />
			<widget name="starsbg" position="460,60" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/OFDb/starsbar_empty.png" transparent="1" zPosition="0" alphatest="on" />
			<widget name="stars" position="460,60" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/OFDb/starsbar_filled.png" transparent="1" />
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
		self.Page = 0  # 0 = multiple query selection menu page, 1 = movie info page, 2 = extra infos page
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "MenuActions", "InfoActions"],
		{
			"ok": self.showDetails,
			"cancel": self.close,
			"down": self.pageDown,
			"up": self.pageUp,
			"red": self.close,
			"green": self.showMenu,
			"yellow": self.showDetails,
			"blue": self.showExtras,
			"menu": self.openChannelSelection,
			"info": self.showDetails
		}, -1)
		self.getOFDB()

	def dictionary_init(self):
		syslang = language.getLanguage()
		if "de" not in syslang:
			self.OFDBlanguage = ""  # set to empty ("") for english version
		else:
			self.OFDBlanguage = "german."  # it's a subdomain, so add a '.' at the end
		self.htmltags = compile('<.*?>')
		self.generalinfomask = compile(
		r'<title>OFDb - (?P<title>.*?)</title>.*?'
		r'(?P<g_original>Originaltitel):[\s\S]*?class=\"Daten\">(?P<original>.*?)</td>'
		r'(?:.*?(?P<g_country>Herstellungsland):[\s\S]*?class="Daten">(?P<country>.*?)(?:\.\.\.|</td>))*'
		r'(?:.*?(?P<g_year>Erscheinungsjahr):[\s\S]*?class="Daten">(?P<year>.*?)</td>)*'
		r'(?:.*?(?P<g_director>Regie):[\s\S]*?class="Daten">(?P<director>.*?)(?:\.\.\.|</td>))*', DOTALL)

	def resetLabels(self):
		self["detailslabel"].setText("")
		self["ratinglabel"].setText("")
		self["titellabel"].setText("")
		self["castlabel"].setText("")
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
		if (self.Page == 1 or self.Page == 2) and self.resultlist:
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
			print("[OFDb] downloading query %s to %s" % (fetchurl, localfile))
			callInThread(self.threadDownloadPage, fetchurl, localfile, self.OFDBquery2, self.fetchFailed)
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
		self.session.openWithCallback(self.channelSelectionClosed, OFDBChannelSelection)

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
			event = info and info.getEvent(0)  # 0 = now, 1 = next
			if event:
				self.eventName = event.getEventName()

		if self.eventName != "":
			try:
				pos = self.eventName.index(" (")
				self.eventName = self.eventName[0:pos]
			except ValueError:
				pass
			if self.eventName[-3:] == "...":
				self.eventName = self.eventName[:-3]
			for article in ["The", "Der", "Die", "Das"]:
				if self.eventName[:4].capitalize() == article + " ":
					self.eventName = "%s, %s" % (self.eventName[4:], article)
			self["statusbar"].setText(_("Query OFDb: %s...") % (self.eventName))
			try:
				self.eventName = quote(self.eventName)
			except:
				self.eventName = quote(self.eventName.decode('utf8').encode('ascii', 'ignore'))
			localfile = "/tmp/ofdbquery.html"
			fetchurl = "http://www.ofdb.de/view.php?page=suchergebnis&Kat=DTitel&SText=" + self.eventName
			print("[OFDb] Downloading Query %s to %s" % (fetchurl, localfile))
			callInThread(self.threadDownloadPage, fetchurl, localfile, self.OFDBquery, self.fetchFailed)
		else:
			self["statusbar"].setText(_("Could't get Eventname"))

	def fetchFailed(self, string):
		print("[OFDb] fetch failed %s" % string)
		self["statusbar"].setText(_("OFDb Download failed"))

	def OFDBquery(self, string):
		print("[OFDBquery]")
		self["statusbar"].setText(_("OFDb Download completed"))
		self.inhtml = open("/tmp/ofdbquery.html", "rb").read().decode('utf-8', 'ignore')
		self.generalinfos = self.generalinfomask.search(self.inhtml)
		if self.generalinfos:
			self.OFDBparse()
		else:
			if search("<title>OFDb - Suchergebnis</title>", self.inhtml):
				searchresultmask = compile(r"<br>(\d{1,3}\.) <a href=\"film/(.*?)\"(?:.*?)\)\">(.*?)</a>", DOTALL)
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
		self.inhtml = open("/tmp/ofdbquery2.html", "rb").read().decode('utf-8', 'ignore')
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
				Titeltext = "%s%s" % (Titeltext[0:54], "…")
			self["titellabel"].setText(Titeltext)
			Detailstext = ""
			genreblockmask = compile(r'Genre\(s\):(?:[\s\S]*?)class=\"Daten\">(.*?)</tr>', DOTALL)
			genreblock = genreblockmask.findall(self.inhtml)
			genremask = compile('\">(.*?)</a')
			if genreblock:
				genres = genremask.finditer(genreblock[0])
				if genres:
					Detailstext += "Genre: "
					for x in genres:
						Detailstext += self.htmltags.sub('', "%s " % x.group(1))
			for category in ("director", "year", "country", "original"):
				if self.generalinfos.group('g_%s' % category):
					Detailstext += "\n%s: %s" % (self.generalinfos.group('g_' + category).encode('latin-1').decode('utf-8'), self.htmltags.sub('', self.generalinfos.group(category).replace("<br>", ' ')))
				self["detailslabel"].setText(Detailstext)
			ratingmask = compile(r'<td>[\s\S]*notenskala.*(?P<g_rating>Note: )(?P<rating>\d.\d{2,2})[\s\S]*</td>', DOTALL)
			rating = ratingmask.search(self.inhtml)
			Ratingtext = _("no user rating yet")
			if rating:
				Ratingtext = "%s%s / 10" % (rating.group("g_rating"), rating.group("rating"))
				self.ratingstars = int(10 * round(float(rating.group("rating")), 1))
				self["stars"].show()
				self["stars"].setValue(self.ratingstars)
				self["starsbg"].show()
			self["ratinglabel"].setText(Ratingtext)
			castblockmask = compile(r'Darsteller:[\s\S]*?class=\"Daten\">(.*?)(?:\.\.\.|\xbb)', DOTALL)
			castblock = castblockmask.findall(self.inhtml)
			castmask = compile('\">(.*?)</a')
			Casttext = ""
			if castblock:
				cast = castmask.finditer(castblock[0])
				if cast:
					for x in cast:
						Casttext += "\n%s" % self.htmltags.sub('', x.group(1))
					if Casttext != "":
						Casttext = _("Cast: %s" % Casttext)
					else:
						Casttext = _("No cast list found in the database.")
					self["castlabel"].setText(Casttext)
			postermask = compile('<img src=\"(http://img.ofdb.de/film.*?)\" alt', DOTALL)
			posterurl = postermask.search(self.inhtml)
			if posterurl and posterurl.group(1).find("jpg") > 0:
				posterurl = posterurl.group(1)
				self["statusbar"].setText(_("Downloading Movie Poster: %s...") % (posterurl))
				localfile = "/tmp/poster.jpg"
				print("[OFDb] downloading poster %s to %s" % (posterurl, localfile))
				callInThread(self.threadDownloadPage, posterurl, localfile, self.OFDBPoster, self.fetchFailed)
			else:
				print("no jpg poster!")
				self.OFDBPoster(noPoster=True)
		self["detailslabel"].setText(Detailstext)

	def threadDownloadPage(self, link, file, success, fail=None):
		link = link.encode('ascii', 'xmlcharrefreplace').decode().replace(' ', '%20').replace('\n', '').encode('utf-8')
		try:
			response = get(link)
			response.raise_for_status()
			with open(file, "wb") as f:
				f.write(response.content)
			success(file)
		except exceptions.RequestException as error:
			if fail is not None:
				fail(error)

	def OFDBPoster(self, noPoster=False):
		self["statusbar"].setText(_("OFDb Details parsed"))
		filename = resolveFilename(SCOPE_PLUGINS, "Extensions/OFDb/no_poster.png") if noPoster else "/tmp/poster.jpg"
		self.picload.setPara((self["poster"].instance.size().width(), self["poster"].instance.size().height(), 1, 1, False, 1, "#00000000"))
		self.picload.startDecode(filename)

	def paintPosterPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr is not None:
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
			event = info.getEvent(0)  # 0 = now, 1 = next
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
		return PluginDescriptor(name="OFDb Details", description=_("Query details from the Online-Filmdatenbank"), icon="ofdb.png", where=wherelist, fnc=main)
